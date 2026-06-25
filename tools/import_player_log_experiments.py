#!/usr/bin/env python3
"""Import Player.log diagnostics into experiment-corpus artifact drafts.

This tool groups AllocationLog/LaunchLog rows by experimentId and writes one
corpus artifact directory per experiment. It is intentionally experimentId-based;
it does not try to infer full Terra Invicta battle boundaries yet.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any


DEFAULT_OUTPUT = Path("artifacts/experiments/imported")
DEFAULT_REGISTRY_NAME = "registry.jsonl"
COUNT_FIELDS = (
    "direct_command_spend_counts",
    "missing_evidence_counts",
    "skipped_command_counts",
    "failed_command_counts",
    "overkill_counts",
    "under_saturation_counts",
    "target_mismatch_counts",
    "regression_counts",
    "vanilla_spillover_counts",
)
KNOWN_RUN_MODES = {
    "fixture",
    "shadow-replay",
    "controlled-live",
    "fleet-wide-controlled",
}
LOG_RE = re.compile(r"\[(?P<kind>AllocationLog|LaunchLog)\]\s*(?P<pairs>.*)$")
PAIR_RE = re.compile(r'(?P<key>[A-Za-z][A-Za-z0-9_]*)="(?P<value>[^"]*)"')
EXPERIMENT_TIMESTAMP_RE = re.compile(
    r"(?P<date>20\d{6})T(?P<hms>\d{6})(?P<millis>\d{3})?Z"
)
FLEET_WIDE_BOUNDED_LIVE_RECORDS = {
    "fleetWideBoundedLiveCandidate",
    "fleetWideBoundedLivePreState",
    "fleetWideBoundedLiveResult",
    "fleetWideBoundedLivePostState",
}
FLEET_WIDE_COMMAND_AUTHORITY_RECORDS = {
    "fleetWideCommandAuthorityCandidate",
    "fleetWideCommandAuthorityPreState",
    "fleetWideCommandAuthorityResult",
    "fleetWideCommandAuthorityPostState",
}
CONTROLLED_LIVE_RESULT_RECORDS = {
    "appliedDecision",
    "skippedDecision",
    "failedDecision",
}


@dataclass
class LogRow:
    """One parsed diagnostics row from a Player.log file."""

    line_number: int
    kind: str
    pairs: dict[str, str]


@dataclass
class ExperimentGroup:
    """Rows that belong to one diagnostics experiment id."""

    source_experiment_id: str
    rows: list[LogRow] = field(default_factory=list)

    @property
    def allocation_rows(self) -> list[LogRow]:
        return [row for row in self.rows if row.kind == "AllocationLog"]

    @property
    def launch_rows(self) -> list[LogRow]:
        return [row for row in self.rows if row.kind == "LaunchLog"]


def repo_root() -> Path:
    """Return the repository root from this script location."""
    return Path(__file__).resolve().parents[1]


def repo_relative(path: Path) -> str:
    """Return a repo-relative path when possible."""
    try:
        return path.resolve().relative_to(repo_root()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    """Return sha256:<hex> for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def parse_pairs(text: str) -> dict[str, str]:
    """Parse key="value" diagnostics pairs."""
    return {match.group("key"): match.group("value") for match in PAIR_RE.finditer(text)}


def experiment_from_command_result(command_result_id: str | None) -> str | None:
    """Extract experiment id from commandResultId when it uses experiment:command form."""
    if not command_result_id or command_result_id == "none":
        return None
    if ":" not in command_result_id:
        return None
    prefix = command_result_id.split(":", 1)[0]
    return prefix or None


def parse_log_groups(path: Path, filters: set[str] | None = None) -> dict[str, ExperimentGroup]:
    """Parse a Player.log and group AllocationLog/LaunchLog rows by experiment id."""
    groups: dict[str, ExperimentGroup] = {}
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            match = LOG_RE.search(line)
            if not match:
                continue
            pairs = parse_pairs(match.group("pairs"))
            experiment_id = pairs.get("experimentId")
            if not experiment_id and match.group("kind") == "LaunchLog":
                experiment_id = experiment_from_command_result(pairs.get("commandResultId"))
            if not experiment_id:
                continue
            if filters and experiment_id not in filters:
                continue
            group = groups.setdefault(experiment_id, ExperimentGroup(experiment_id))
            group.rows.append(LogRow(line_number, match.group("kind"), pairs))
    return groups


def counter_dict(counter: Counter[str]) -> dict[str, int]:
    """Return deterministic count mapping."""
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def int_value(value: Any, default: int = 0) -> int:
    """Parse an integer-ish diagnostics value."""
    try:
        if value in (None, "", "none", "unknown"):
            return default
        return int(str(value))
    except ValueError:
        return default


def first_non_empty(values: list[str | None], default: str = "unknown") -> str:
    """Return the first concrete diagnostics value."""
    for value in values:
        if value and value not in {"none", "unknown"}:
            return value
    return default


def unique_values(rows: list[LogRow], *keys: str) -> list[str]:
    """Return sorted unique non-empty values from rows across several keys."""
    values: set[str] = set()
    for row in rows:
        for key in keys:
            value = row.pairs.get(key)
            if value and value not in {"none", "unknown"}:
                values.add(value)
    return sorted(values)


def count_same_team_markers(rows: list[LogRow]) -> int:
    """Count rows where launcher/team and target/team are both visible and equal."""
    count = 0
    for row in rows:
        launcher_team = row.pairs.get("launcherTeam") or row.pairs.get("allocatorLauncherTeam")
        target_team = row.pairs.get("targetTeam")
        if (
            launcher_team
            and target_team
            and launcher_team not in {"none", "unknown"}
            and target_team not in {"none", "unknown"}
            and launcher_team == target_team
        ):
            count += 1
    return count


def infer_run_mode(group: ExperimentGroup) -> str:
    """Infer corpus runMode from row runMode fields and record families."""
    declared = Counter(
        row.pairs.get("runMode")
        for row in group.allocation_rows
        if row.pairs.get("runMode") in KNOWN_RUN_MODES
    )
    if declared:
        return declared.most_common(1)[0][0]

    record_types = {row.pairs.get("recordType", "") for row in group.allocation_rows}
    if record_types & FLEET_WIDE_BOUNDED_LIVE_RECORDS:
        return "fleet-wide-controlled"
    if record_types & FLEET_WIDE_COMMAND_AUTHORITY_RECORDS:
        return "fleet-wide-controlled"
    if any(record_type.startswith("fleetWide") for record_type in record_types):
        return "fleet-wide-controlled"
    if record_types & CONTROLLED_LIVE_RESULT_RECORDS:
        return "controlled-live"
    if any(record_type.startswith("dryRun") for record_type in record_types):
        return "shadow-replay"
    return "shadow-replay"


def infer_selected_mode(group: ExperimentGroup, run_mode: str) -> str:
    """Infer selectedMode for metadata."""
    if run_mode == "fleet-wide-controlled" or any(
        row.pairs.get("recordType", "").startswith("fleetWide") for row in group.allocation_rows
    ):
        return "fleet-wide"
    selected_counts = [int_value(row.pairs.get("selectedShipCount")) for row in group.allocation_rows]
    max_selected = max(selected_counts, default=0)
    if max_selected > 1:
        return "selected-group"
    if max_selected == 1:
        return "selected-single-ship"
    return "shadow-only"


def infer_timestamp(source_experiment_id: str, launch_rows: list[LogRow]) -> str:
    """Infer ISO UTC timestamp from experiment id or launch rows."""
    match = EXPERIMENT_TIMESTAMP_RE.search(source_experiment_id)
    if match:
        date_text = match.group("date")
        hms_text = match.group("hms")
        millis_text = match.group("millis") or "000"
        return (
            f"{date_text[0:4]}-{date_text[4:6]}-{date_text[6:8]}"
            f"T{hms_text[0:2]}:{hms_text[2:4]}:{hms_text[4:6]}.{millis_text}Z"
        )
    for row in launch_rows:
        utc = row.pairs.get("utc")
        if utc and utc not in {"none", "unknown"}:
            return utc
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_slug(value: str, *, upper: bool = False, max_len: int = 96) -> str:
    """Return a filesystem-safe slug."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("._-")
    slug = re.sub(r"[-_.]{2,}", "-", slug)
    if not slug:
        slug = "experiment"
    slug = slug[:max_len].strip("._-") or "experiment"
    return slug.upper() if upper else slug.lower()


def corpus_experiment_id(source_experiment_id: str, prefix: str) -> str:
    """Return a durable corpus experiment id for registry/metadata."""
    if source_experiment_id.startswith("EXP-"):
        return safe_slug(source_experiment_id, upper=True, max_len=120)
    return f"{prefix}-{safe_slug(source_experiment_id, upper=True, max_len=100)}"


def summarize_allocation(group: ExperimentGroup) -> dict[str, Any]:
    """Build parser-summary allocation counters for one experiment group."""
    rows = group.allocation_rows
    record_counts = Counter(row.pairs.get("recordType", "unknown") for row in rows)
    summary: dict[str, Any] = {
        "source_experiment_id": group.source_experiment_id,
        "allocation_rows": len(rows),
        "allocation_record_type_counts": counter_dict(record_counts),
        "source_line_first": min((row.line_number for row in group.rows), default=None),
        "source_line_last": max((row.line_number for row in group.rows), default=None),
        "same_team_missile_target_snapshots": count_same_team_markers(rows),
        "suspicious_patterns": ["none"],
    }

    bounded_rows = [
        row for row in rows if row.pairs.get("recordType") in FLEET_WIDE_BOUNDED_LIVE_RECORDS
    ]
    if bounded_rows:
        result_rows = [
            row for row in bounded_rows if row.pairs.get("recordType") == "fleetWideBoundedLiveResult"
        ]
        result_counts = Counter(row.pairs.get("result", "unknown") for row in result_rows)
        reason_counts = Counter(row.pairs.get("reason", "unknown") for row in result_rows)
        summary.update(
            {
                "fleet_wide_bounded_live_experiment_ids": [group.source_experiment_id],
                "fleet_wide_bounded_live_candidate_records": record_counts.get(
                    "fleetWideBoundedLiveCandidate", 0
                ),
                "fleet_wide_bounded_live_pre_state_records": record_counts.get(
                    "fleetWideBoundedLivePreState", 0
                ),
                "fleet_wide_bounded_live_result_records": record_counts.get(
                    "fleetWideBoundedLiveResult", 0
                ),
                "fleet_wide_bounded_live_post_state_records": record_counts.get(
                    "fleetWideBoundedLivePostState", 0
                ),
                "fleet_wide_bounded_live_applied_commands": result_counts.get("applied", 0),
                "fleet_wide_bounded_live_failed_commands": result_counts.get("failed", 0)
                + sum(int_value(row.pairs.get("failedCommands")) for row in result_rows),
                "fleet_wide_bounded_live_scope_mode_counts": counter_dict(
                    Counter(row.pairs.get("scopeMode", "unknown") for row in bounded_rows)
                ),
                "fleet_wide_bounded_live_result_counts": counter_dict(result_counts),
                "fleet_wide_bounded_live_reason_counts": counter_dict(reason_counts),
                "fleet_wide_bounded_live_selection_relation_counts": counter_dict(
                    Counter(
                        row.pairs.get("launcherSelectionRelation", "unknown")
                        for row in bounded_rows
                    )
                ),
                "fleet_wide_bounded_live_correlation_counts": counter_dict(
                    Counter(row.pairs.get("controlledCommandCorrelation", "unknown") for row in result_rows)
                ),
            }
        )

    live_rows = [row for row in rows if row.pairs.get("recordType") in CONTROLLED_LIVE_RESULT_RECORDS]
    if live_rows:
        result_counts = Counter(row.pairs.get("result", "unknown") for row in live_rows)
        reason_counts = Counter(row.pairs.get("reason", "unknown") for row in live_rows)
        summary.update(
            {
                "controlled_live_apply_applied": result_counts.get("applied", 0),
                "controlled_live_apply_skipped": result_counts.get("skipped", 0),
                "controlled_live_apply_failed": result_counts.get("failed", 0),
                "controlled_live_apply_reason_counts": counter_dict(reason_counts),
                "controlled_live_apply_mismatch_counts": {},
            }
        )

    missing_inputs = Counter()
    for row in rows:
        missing = row.pairs.get("missingInputs") or row.pairs.get("missing")
        if missing and missing not in {"none", "unknown"}:
            for item in missing.split(","):
                item = item.strip()
                if item:
                    missing_inputs[item] += 1
    if missing_inputs:
        summary["missing_input_counts"] = counter_dict(missing_inputs)

    return summary


def summarize_launches(group: ExperimentGroup) -> tuple[dict[str, int], Counter[str], Counter[str]]:
    """Return launch correlation summary and useful launch counters."""
    correlation_counts: Counter[str] = Counter()
    direct_by_command: Counter[str] = Counter()
    none_or_missing_by_target: Counter[str] = Counter()
    for row in group.launch_rows:
        correlation = row.pairs.get("controlledCommandCorrelation", "missing")
        correlation_counts[correlation] += 1
        if correlation == "directRuntimeContext":
            direct_by_command[row.pairs.get("commandResultId", "unknown")] += 1
        elif correlation in {"none", "missing"}:
            target = row.pairs.get("targetStateId") or row.pairs.get("targetId") or "unknown"
            none_or_missing_by_target[target] += 1
    return counter_dict(correlation_counts), direct_by_command, none_or_missing_by_target


def applied_commands(group: ExperimentGroup, direct_by_command: Counter[str]) -> list[dict[str, Any]]:
    """Return applied command summaries when result rows are available."""
    commands: list[dict[str, Any]] = []
    for row in group.allocation_rows:
        record_type = row.pairs.get("recordType")
        if record_type not in {"fleetWideBoundedLiveResult", "appliedDecision"}:
            continue
        if row.pairs.get("result") != "applied":
            continue
        command_result_id = row.pairs.get("commandResultId", "none")
        commands.append(
            {
                "cycleId": int_value(row.pairs.get("cycleId"), default=-1),
                "launcher": row.pairs.get("launcher", "unknown"),
                "launcherId": row.pairs.get("launcherId", "unknown"),
                "target": row.pairs.get("target", "unknown"),
                "targetId": row.pairs.get("targetId", "unknown"),
                "assignedShots": int_value(row.pairs.get("assignedShots")),
                "commandResultId": command_result_id,
                "directRuntimeContextRows": direct_by_command.get(command_result_id, 0),
            }
        )
    return commands


def build_summary(group: ExperimentGroup, log_path: Path, *, fixture: bool, include_source: bool) -> dict[str, Any]:
    """Build parsed summary artifact for one experiment group."""
    allocation_summary = summarize_allocation(group)
    launch_summary, direct_by_command, none_or_missing_by_target = summarize_launches(group)
    direct_launches = launch_summary.get("directRuntimeContext", 0)
    limitation_counts: dict[str, int] = {}
    if not include_source:
        limitation_counts["source Player.log path omitted from registry"] = 1
    if direct_launches == 0 and group.launch_rows:
        limitation_counts["direct runtime launch correlation not observed"] = 1

    row_summary: dict[str, Any] = {
        "source_experiment_id": group.source_experiment_id,
        "source_line_first": min((row.line_number for row in group.rows), default=None),
        "source_line_last": max((row.line_number for row in group.rows), default=None),
        "allocation_rows": len(group.allocation_rows),
        "launch_rows": len(group.launch_rows),
        "parser_summary": {"allocation_summary": allocation_summary},
        "controlled_launch_correlation_summary": launch_summary,
        "applied_commands": applied_commands(group, direct_by_command),
    }
    if none_or_missing_by_target:
        row_summary["none_or_missing_correlated_launches_by_target"] = counter_dict(
            none_or_missing_by_target
        )

    return {
        "input": log_path.name,
        "sourceExperimentId": group.source_experiment_id,
        "log_count": 1,
        "evidence_log_count": 1,
        "real_evidence_log_count": 0 if fixture else 1,
        "synthetic_fixture_count": 1 if fixture else 0,
        "parser_failures": 0,
        "classification_counts": {
            "plausible": 1,
            "partial saturation": 0,
            "overkill": 0,
            "underkill": 0,
            "target-value mismatch": 0,
            "missing-evidence-limited": len(limitation_counts),
            "command-safety no-op": 0,
        },
        "limitation_counts": limitation_counts,
        "logs": [row_summary],
    }


def evidence_summary_from_group(
    group: ExperimentGroup,
    summary: dict[str, Any],
    *,
    pd_category: str,
) -> dict[str, dict[str, int]]:
    """Build metadata evidenceSummary additions not already represented by parsed summary."""
    launch_summary = summary["logs"][0]["controlled_launch_correlation_summary"]
    direct_rows = launch_summary.get("directRuntimeContext", 0)
    none_rows = launch_summary.get("none", 0) + launch_summary.get("missing", 0)
    evidence: dict[str, dict[str, int]] = {field: {} for field in COUNT_FIELDS}
    if direct_rows:
        evidence["direct_command_spend_counts"] = {"directRuntimeContext launch rows": direct_rows}
    if none_rows:
        evidence["vanilla_spillover_counts"] = {
            "none-or-missing correlated launch rows with experiment id": none_rows
        }
    same_team = summary["logs"][0]["parser_summary"]["allocation_summary"].get(
        "same_team_missile_target_snapshots", 0
    )
    if same_team:
        evidence["regression_counts"] = {"same-team missile target snapshots": same_team}
    if pd_category == "unknown":
        evidence["missing_evidence_counts"] = {
            "pd evidence context not attached by experimentId importer": 1
        }
    return evidence


def build_metadata(
    group: ExperimentGroup,
    corpus_id: str,
    run_mode: str,
    summary: dict[str, Any],
    *,
    missile_family: str,
    reviewer_notes: str,
) -> dict[str, Any]:
    """Build scenario metadata artifact."""
    all_rows = group.rows
    allocation_rows = group.allocation_rows
    launch_rows = group.launch_rows
    selected_mode = infer_selected_mode(group, run_mode)
    selected_count = max((int_value(row.pairs.get("selectedShipCount")) for row in allocation_rows), default=0)
    launcher_ids = unique_values(all_rows, "launcherId", "allocatorLauncherId")
    target_ids = unique_values(all_rows, "targetId", "targetStateId")
    pd_category = first_non_empty(
        [row.pairs.get("pdEvidenceQuality") for row in allocation_rows]
        + [row.pairs.get("pdEvidenceCategory") for row in allocation_rows],
        default="unknown",
    )
    known_missing = [
        "imported by experimentId; review metadata and verdict before tuning",
    ]
    if summary.get("limitation_counts"):
        known_missing.extend(summary["limitation_counts"].keys())
    if pd_category == "unknown":
        known_missing.append("pd evidence context not attached by experimentId importer")

    allocation_summary = summary["logs"][0]["parser_summary"]["allocation_summary"]
    direct_summary = summary["logs"][0]["controlled_launch_correlation_summary"]
    return {
        "schemaVersion": 1,
        "experimentId": corpus_id,
        "sourceExperimentId": group.source_experiment_id,
        "runMode": run_mode,
        "selectedMode": selected_mode,
        "selectedShipCount": selected_count,
        "friendlyMissileShipCount": len(launcher_ids),
        "enemyShipCount": len(target_ids),
        "launcherWeaponCount": len(launcher_ids),
        "missileFamily": missile_family,
        "targetIds": target_ids,
        "pdEvidenceCategory": pd_category,
        "rangeBand": "imported",
        "closingSpeedBand": "imported",
        "knownMissingEvidence": known_missing,
        "directCommandSpendSummary": {
            "appliedCommands": allocation_summary.get("fleet_wide_bounded_live_applied_commands", 0)
            or allocation_summary.get("controlled_live_apply_applied", 0),
            "failedCommands": allocation_summary.get("fleet_wide_bounded_live_failed_commands", 0)
            or allocation_summary.get("controlled_live_apply_failed", 0),
            "directRuntimeContextRows": direct_summary.get("directRuntimeContext", 0),
            "sameTeamMarkers": allocation_summary.get("same_team_missile_target_snapshots", 0),
            "scopeViolationMarkers": allocation_summary.get("controlled_dry_run_scope_violations", 0),
        },
        "evidenceSummary": evidence_summary_from_group(
            group,
            summary,
            pd_category=pd_category,
        ),
        "reviewerNotes": reviewer_notes,
    }


def build_verdict(
    corpus_id: str,
    source_experiment_id: str,
    run_mode: str,
    reviewed_at_utc: str,
    reviewer: str,
    verdict: str,
) -> dict[str, Any]:
    """Build manual-verdict draft."""
    return {
        "schemaVersion": 1,
        "verdict": verdict,
        "reviewer": reviewer,
        "reviewedAtUtc": reviewed_at_utc,
        "summary": (
            f"Imported {run_mode} experiment {source_experiment_id} into corpus artifact "
            f"{corpus_id}. Review before using for tuning."
        ),
        "evidenceGaps": [
            "manual review required",
            "cross-scenario comparison required before tuning",
            "exact outcome / kill attribution may be unavailable",
        ],
        "nextAction": "Review generated metadata/summary and then summarize the corpus registry.",
    }


def build_registry_entry(
    corpus_id: str,
    group: ExperimentGroup,
    run_mode: str,
    timestamp_utc: str,
    artifact_dir: Path,
    parameters_path: Path,
    parameter_hash: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Build one registry JSONL object."""
    entry: dict[str, Any] = {
        "schemaVersion": 1,
        "experimentId": corpus_id,
        "timestampUtc": timestamp_utc,
        "runMode": run_mode,
        "parsedPath": repo_relative(artifact_dir / "summary.json"),
        "metadataPath": repo_relative(artifact_dir / "metadata.json"),
        "parametersPath": repo_relative(parameters_path),
        "verdictPath": repo_relative(artifact_dir / "verdict.json"),
        "gameVersion": args.game_version,
        "modCommit": args.mod_commit,
        "heuristicCandidateId": args.heuristic_candidate_id,
        "parameterSnapshotHash": parameter_hash,
        "scenarioTags": sorted(set([run_mode, "imported", *args.scenario_tag])),
        "verdict": args.verdict,
        "notes": f"Imported from Player.log experimentId {group.source_experiment_id}; raw log not committed by default.",
    }
    if args.include_source_log_path:
        entry["sourceLogPath"] = repo_relative(args.log)
    return entry


def write_json(path: Path, value: dict[str, Any], *, force: bool) -> None:
    """Write a JSON object with overwrite protection."""
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_artifacts(
    groups: dict[str, ExperimentGroup],
    args: argparse.Namespace,
    parameter_hash: str,
) -> list[dict[str, Any]]:
    """Write artifact directories and return registry entries."""
    entries: list[dict[str, Any]] = []
    for source_experiment_id, group in sorted(groups.items()):
        run_mode = args.run_mode if args.run_mode != "auto" else infer_run_mode(group)
        if run_mode not in KNOWN_RUN_MODES:
            raise SystemExit(f"Unsupported runMode {run_mode!r} for {source_experiment_id}")
        corpus_id = corpus_experiment_id(source_experiment_id, args.corpus_id_prefix)
        timestamp_utc = args.timestamp_utc or infer_timestamp(source_experiment_id, group.launch_rows)
        artifact_dir = args.output / safe_slug(source_experiment_id)
        if not args.dry_run and artifact_dir.exists() and not args.force:
            raise SystemExit(f"Refusing to overwrite existing artifact directory without --force: {artifact_dir}")

        summary = build_summary(
            group,
            args.log,
            fixture=args.fixture,
            include_source=args.include_source_log_path,
        )
        metadata = build_metadata(
            group,
            corpus_id,
            run_mode,
            summary,
            missile_family=args.missile_family,
            reviewer_notes=args.reviewer_notes,
        )
        verdict = build_verdict(
            corpus_id,
            source_experiment_id,
            run_mode,
            args.reviewed_at_utc,
            args.reviewer,
            args.verdict,
        )

        if not args.dry_run:
            write_json(artifact_dir / "summary.json", summary, force=args.force)
            write_json(artifact_dir / "metadata.json", metadata, force=args.force)
            write_json(artifact_dir / "verdict.json", verdict, force=args.force)

        entries.append(
            build_registry_entry(
                corpus_id,
                group,
                run_mode,
                timestamp_utc,
                artifact_dir,
                args.parameters,
                parameter_hash,
                args,
            )
        )
    return entries


def write_registry(path: Path, entries: list[dict[str, Any]], *, append: bool, force: bool) -> None:
    """Write or append registry JSONL entries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not append and not force:
        raise SystemExit(f"Refusing to overwrite existing registry without --force or --append-registry: {path}")
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True, help="Player.log or fixture log to import")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"default: {DEFAULT_OUTPUT}")
    parser.add_argument("--registry", type=Path, help="default: <output>/registry.jsonl")
    parser.add_argument("--parameters", type=Path, required=True, help="parameter snapshot JSON for registry provenance")
    parser.add_argument("--parameter-snapshot-hash", help="override sha256 hash for --parameters")
    parser.add_argument("--heuristic-candidate-id", required=True)
    parser.add_argument("--run-mode", default="auto", choices=["auto", *sorted(KNOWN_RUN_MODES)])
    parser.add_argument("--experiment-id", action="append", default=[], help="only import this source experimentId; repeatable")
    parser.add_argument("--corpus-id-prefix", default="EXP-IMPORTED")
    parser.add_argument("--scenario-tag", action="append", default=[])
    parser.add_argument("--verdict", default="evidence-limited")
    parser.add_argument("--reviewer", default="FennexFox")
    parser.add_argument("--reviewed-at-utc", default=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    parser.add_argument("--timestamp-utc", help="override registry timestamp for every imported experiment")
    parser.add_argument("--game-version", default=None)
    parser.add_argument("--mod-commit", default=None)
    parser.add_argument("--missile-family", default="imported")
    parser.add_argument("--reviewer-notes", default="Generated by import_player_log_experiments.py; review before tuning.")
    parser.add_argument("--fixture", action="store_true", help="mark outputs as synthetic fixture evidence")
    parser.add_argument("--include-source-log-path", action="store_true", help="include sourceLogPath in registry; omit for private raw logs")
    parser.add_argument("--append-registry", action="store_true", help="append to registry instead of overwriting")
    parser.add_argument("--force", action="store_true", help="overwrite artifact files/registry when safe")
    parser.add_argument("--dry-run", action="store_true", help="print planned registry entries without writing files")
    args = parser.parse_args()
    if args.registry is None:
        args.registry = args.output / DEFAULT_REGISTRY_NAME
    return args


def main() -> None:
    """Import Player.log experiments."""
    args = parse_args()
    if not args.log.exists():
        raise SystemExit(f"Log file not found: {args.log}")
    if not args.parameters.exists():
        raise SystemExit(f"Parameter snapshot not found: {args.parameters}")
    parameter_hash = args.parameter_snapshot_hash or sha256_file(args.parameters)
    filters = set(args.experiment_id) if args.experiment_id else None
    groups = parse_log_groups(args.log, filters=filters)
    if not groups:
        raise SystemExit("No experimentId-tagged AllocationLog/LaunchLog rows found.")

    entries = write_artifacts(groups, args, parameter_hash)
    if args.dry_run:
        print(json.dumps({"registryEntries": entries}, indent=2, ensure_ascii=False))
        return
    write_registry(args.registry, entries, append=args.append_registry, force=args.force)
    print(f"Imported {len(entries)} experiment(s) from {args.log}.")
    print(f"Wrote artifacts under {args.output}.")
    print(f"Wrote registry entries to {args.registry}.")


if __name__ == "__main__":
    main()
