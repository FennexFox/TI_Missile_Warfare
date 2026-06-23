#!/usr/bin/env python3
"""Summarize a JSONL experiment corpus registry."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any


DEFAULT_REGISTRY = Path("artifacts/experiments/registry.jsonl")
DEFAULT_OUTPUT = Path("artifacts/fitting/corpus-summary")
KNOWN_RUN_MODES = {
    "fixture",
    "shadow-replay",
    "controlled-live",
    "fleet-wide-controlled",
}
KNOWN_VERDICTS = {
    "good",
    "bad",
    "ambiguous",
    "safety-blocked",
    "evidence-limited",
    "needs-live-validation",
    "regression-suspected",
    "fixture-only",
}
REQUIRED_FIELDS = (
    "schemaVersion",
    "experimentId",
    "timestampUtc",
    "runMode",
    "heuristicCandidateId",
    "parametersPath",
    "parameterSnapshotHash",
    "metadataPath",
    "verdictPath",
    "scenarioTags",
)
COUNT_FIELDS = (
    "missing_evidence_counts",
    "skipped_command_counts",
    "failed_command_counts",
    "overkill_counts",
    "under_saturation_counts",
    "target_mismatch_counts",
    "regression_counts",
    "vanilla_spillover_counts",
)


def load_registry(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Load registry JSONL entries and return non-fatal parse warnings."""
    warnings: list[str] = []
    entries: list[dict[str, Any]] = []
    if not path.exists():
        raise SystemExit(f"Registry not found: {path}")

    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                warnings.append(f"{path}:{line_number}: invalid JSONL row: {exc}")
                continue
            if not isinstance(value, dict):
                warnings.append(f"{path}:{line_number}: row is not a JSON object")
                continue
            value["_registryLine"] = line_number
            entries.append(value)
    return entries, warnings


def repo_root() -> Path:
    """Return the repository root from this tool location."""
    return Path(__file__).resolve().parents[1]


def resolve_repo_path(path_text: str | None) -> Path | None:
    """Resolve a repo-relative or absolute artifact path."""
    if not path_text:
        return None
    path = Path(path_text)
    return path if path.is_absolute() else repo_root() / path


def load_json_file(path_text: str | None, warnings: list[str], label: str) -> dict[str, Any]:
    """Load a JSON object if the path exists, otherwise add a warning."""
    path = resolve_repo_path(path_text)
    if path is None:
        warnings.append(f"{label}: path is missing")
        return {}
    if not path.exists():
        warnings.append(f"{label}: missing artifact {path_text}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{label}: invalid JSON artifact {path_text}: {exc}")
        return {}
    if not isinstance(value, dict):
        warnings.append(f"{label}: artifact is not a JSON object {path_text}")
        return {}
    return value


def sha256_file(path: Path) -> str:
    """Return the sha256 hash for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def validate_entry(
    entry: dict[str, Any],
    metadata: dict[str, Any],
    parameters_path: Path | None,
    verdict: dict[str, Any],
) -> list[str]:
    """Return validation warnings for one registry entry."""
    experiment_id = str(entry.get("experimentId", f"line-{entry.get('_registryLine', '?')}"))
    warnings: list[str] = []
    for field_name in REQUIRED_FIELDS:
        if field_name not in entry:
            warnings.append(f"{experiment_id}: missing required registry field {field_name}")

    run_mode = entry.get("runMode")
    if run_mode not in KNOWN_RUN_MODES:
        warnings.append(f"{experiment_id}: unknown runMode {run_mode!r}")

    tags = entry.get("scenarioTags")
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        warnings.append(f"{experiment_id}: scenarioTags must be a string list")

    registry_verdict = entry.get("verdict")
    verdict_value = verdict.get("verdict", registry_verdict)
    if verdict_value not in KNOWN_VERDICTS:
        warnings.append(f"{experiment_id}: unknown or missing verdict {verdict_value!r}")

    if registry_verdict and verdict_value and registry_verdict != verdict_value:
        warnings.append(
            f"{experiment_id}: registry verdict {registry_verdict!r} differs from verdict file {verdict_value!r}"
        )

    if metadata:
        metadata_mode = metadata.get("runMode")
        if metadata_mode and metadata_mode != run_mode:
            warnings.append(
                f"{experiment_id}: metadata runMode {metadata_mode!r} differs from registry {run_mode!r}"
            )

    expected_hash = entry.get("parameterSnapshotHash")
    if parameters_path and parameters_path.exists() and isinstance(expected_hash, str):
        actual_hash = sha256_file(parameters_path)
        if expected_hash != actual_hash:
            warnings.append(
                f"{experiment_id}: parameterSnapshotHash mismatch; expected {expected_hash}, actual {actual_hash}"
            )

    return warnings


def add_counts(counter: Counter[str], values: Any) -> None:
    """Add a mapping of count-like values to a counter."""
    if not isinstance(values, dict):
        return
    for key, value in values.items():
        if isinstance(value, int) and value > 0:
            counter[str(key)] += value


def nested_get(value: dict[str, Any], *keys: str) -> Any:
    """Safely retrieve a nested dictionary value."""
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def summarize_parsed_artifact(parsed: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Extract corpus-level counts from existing fitting summary artifacts."""
    counts: dict[str, Counter[str]] = {field: Counter() for field in COUNT_FIELDS}

    add_counts(counts["missing_evidence_counts"], parsed.get("limitation_counts"))
    classification_counts = parsed.get("classification_counts")
    if isinstance(classification_counts, dict):
        for key in ("missing-evidence-limited", "command-safety no-op"):
            value = classification_counts.get(key)
            if isinstance(value, int) and value:
                counts["missing_evidence_counts"][key] += value
        overkill = classification_counts.get("overkill")
        if isinstance(overkill, int) and overkill:
            counts["overkill_counts"]["classification:overkill"] += overkill
        underkill = classification_counts.get("underkill")
        if isinstance(underkill, int) and underkill:
            counts["under_saturation_counts"]["classification:underkill"] += underkill
        partial = classification_counts.get("partial saturation")
        if isinstance(partial, int) and partial:
            counts["under_saturation_counts"]["classification:partial saturation"] += partial
        target_mismatch = classification_counts.get("target-value mismatch")
        if isinstance(target_mismatch, int) and target_mismatch:
            counts["target_mismatch_counts"]["classification:target-value mismatch"] += target_mismatch

    for log in parsed.get("logs", []):
        if not isinstance(log, dict):
            continue
        parser_summary = log.get("parser_summary")
        allocation_summary = (
            parser_summary.get("allocation_summary")
            if isinstance(parser_summary, dict)
            else {}
        )
        if isinstance(allocation_summary, dict):
            add_counts(
                counts["missing_evidence_counts"],
                allocation_summary.get("missing_input_counts"),
            )
            dry_run_skipped = allocation_summary.get("controlled_dry_run_skipped_commands")
            if isinstance(dry_run_skipped, int) and dry_run_skipped:
                counts["skipped_command_counts"]["controlled dry-run skipped"] += dry_run_skipped
            dry_run_safety_blocked = allocation_summary.get(
                "controlled_dry_run_safety_gate_blocked_commands"
            )
            if isinstance(dry_run_safety_blocked, int) and dry_run_safety_blocked:
                counts["skipped_command_counts"][
                    "controlled dry-run safety-gate blocked"
                ] += dry_run_safety_blocked
            dry_run_scope_violations = allocation_summary.get(
                "controlled_dry_run_scope_violations"
            )
            if isinstance(dry_run_scope_violations, int) and dry_run_scope_violations:
                counts["skipped_command_counts"][
                    "controlled dry-run scope violation"
                ] += dry_run_scope_violations
            dry_run_failed = allocation_summary.get("controlled_dry_run_failed_commands")
            if isinstance(dry_run_failed, int) and dry_run_failed:
                counts["failed_command_counts"]["controlled dry-run failed"] += dry_run_failed
            add_counts(
                counts["skipped_command_counts"],
                allocation_summary.get("controlled_dry_run_safety_gate_reason_counts"),
            )
            dry_run_candidate_reasons = allocation_summary.get(
                "controlled_dry_run_candidate_reason_counts"
            )
            if isinstance(dry_run_candidate_reasons, dict):
                add_counts(
                    counts["skipped_command_counts"],
                    {
                        key: value
                        for key, value in dry_run_candidate_reasons.items()
                        if key != "none"
                    },
                )
            live_apply_reasons = allocation_summary.get("controlled_live_apply_reason_counts")
            if isinstance(live_apply_reasons, dict):
                add_counts(
                    counts["skipped_command_counts"],
                    {
                        key: value
                        for key, value in live_apply_reasons.items()
                        if key != "none"
                    },
                )
            skipped = allocation_summary.get("controlled_live_apply_skipped")
            if isinstance(skipped, int) and skipped:
                counts["skipped_command_counts"]["controlled live skipped"] += skipped
            failed = allocation_summary.get("controlled_live_apply_failed")
            if isinstance(failed, int) and failed:
                counts["failed_command_counts"]["controlled live failed"] += failed
            add_counts(
                counts["target_mismatch_counts"],
                allocation_summary.get("controlled_live_apply_mismatch_counts"),
            )
            same_team = allocation_summary.get("same_team_missile_target_snapshots")
            if isinstance(same_team, int) and same_team:
                counts["regression_counts"]["same-team missile target snapshots"] += same_team
            for pattern in allocation_summary.get("suspicious_patterns", []):
                if pattern != "none":
                    counts["regression_counts"][str(pattern)] += 1

        spillover_rows = log.get("controlled_cap_spillover_diagnostics")
        if isinstance(spillover_rows, list) and spillover_rows:
            counts["vanilla_spillover_counts"]["controlled cap skipped-launcher spillover"] += len(
                spillover_rows
            )
        post_budget_rows = log.get("applied_launcher_post_budget_spillover_diagnostics")
        if isinstance(post_budget_rows, list) and post_budget_rows:
            counts["vanilla_spillover_counts"]["applied-launcher post-budget spillover"] += len(
                post_budget_rows
            )

    return {key: dict(sorted(counter.items())) for key, counter in counts.items()}


def summarize_entry(
    entry: dict[str, Any],
    metadata: dict[str, Any],
    verdict: dict[str, Any],
    parsed: dict[str, Any],
) -> dict[str, Any]:
    """Return one normalized experiment summary row."""
    evidence_counts = summarize_parsed_artifact(parsed) if parsed else {
        field: {} for field in COUNT_FIELDS
    }
    if metadata:
        for field_name in COUNT_FIELDS:
            merged = Counter(evidence_counts[field_name])
            add_counts(merged, nested_get(metadata, "evidenceSummary", field_name))
            evidence_counts[field_name] = dict(sorted(merged.items()))

    return {
        "experimentId": entry.get("experimentId"),
        "timestampUtc": entry.get("timestampUtc"),
        "runMode": entry.get("runMode"),
        "heuristicCandidateId": entry.get("heuristicCandidateId"),
        "scenarioTags": entry.get("scenarioTags", []),
        "verdict": verdict.get("verdict", entry.get("verdict", "unknown")),
        "gameVersion": entry.get("gameVersion"),
        "modCommit": entry.get("modCommit"),
        "parameterSnapshotHash": entry.get("parameterSnapshotHash"),
        "selectedMode": metadata.get("selectedMode"),
        "pdEvidenceCategory": metadata.get("pdEvidenceCategory"),
        "knownMissingEvidence": metadata.get("knownMissingEvidence", []),
        "evidenceCounts": evidence_counts,
    }


def sorted_counter(counter: Counter[str]) -> dict[str, int]:
    """Return a deterministic count mapping."""
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def build_summary(
    registry_path: Path,
    entries: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, Any]:
    """Build the corpus summary JSON object."""
    experiments: list[dict[str, Any]] = []
    mode_counts: Counter[str] = Counter()
    verdict_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    candidate_counts: Counter[str] = Counter()
    counts_by_mode: dict[str, dict[str, Counter[str]]] = defaultdict(
        lambda: {field: Counter() for field in COUNT_FIELDS}
    )
    candidate_mode_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for entry in entries:
        experiment_id = str(entry.get("experimentId", f"line-{entry.get('_registryLine', '?')}"))
        metadata = load_json_file(entry.get("metadataPath"), warnings, f"{experiment_id} metadata")
        verdict = load_json_file(entry.get("verdictPath"), warnings, f"{experiment_id} verdict")
        parsed = load_json_file(entry.get("parsedPath"), warnings, f"{experiment_id} parsed") if entry.get("parsedPath") else {}
        parameters_path = resolve_repo_path(entry.get("parametersPath"))
        warnings.extend(validate_entry(entry, metadata, parameters_path, verdict))

        for path_field in ("reportPath", "sourceLogPath"):
            path_text = entry.get(path_field)
            if path_text and not (resolve_repo_path(path_text) or Path()).exists():
                artifact_path = resolve_repo_path(path_text)
                if artifact_path and not artifact_path.exists():
                    warnings.append(f"{experiment_id} {path_field}: missing artifact {path_text}")

        row = summarize_entry(entry, metadata, verdict, parsed)
        experiments.append(row)

        run_mode = str(row["runMode"])
        candidate = str(row["heuristicCandidateId"])
        mode_counts[run_mode] += 1
        verdict_counts[str(row["verdict"])] += 1
        candidate_counts[candidate] += 1
        candidate_mode_counts[candidate][run_mode] += 1
        for tag in row.get("scenarioTags", []):
            tag_counts[str(tag)] += 1
        for field_name, values in row["evidenceCounts"].items():
            add_counts(counts_by_mode[run_mode][field_name], values)

    return {
        "schemaVersion": 1,
        "registryPath": str(registry_path),
        "experimentCount": len(experiments),
        "runModeCounts": sorted_counter(mode_counts),
        "verdictCounts": sorted_counter(verdict_counts),
        "scenarioTagCounts": sorted_counter(tag_counts),
        "heuristicCandidateCounts": sorted_counter(candidate_counts),
        "heuristicCandidateRunModeCounts": {
            key: sorted_counter(value) for key, value in sorted(candidate_mode_counts.items())
        },
        "evidenceCountsByRunMode": {
            mode: {
                field_name: sorted_counter(counter)
                for field_name, counter in fields.items()
            }
            for mode, fields in sorted(counts_by_mode.items())
        },
        "warnings": sorted(set(warnings)),
        "experiments": sorted(experiments, key=lambda item: str(item["experimentId"])),
    }


def ensure_safe_output(output_path: Path) -> None:
    """Clear only known corpus-summary output directories."""
    if not output_path.exists():
        return
    if not output_path.is_dir():
        raise SystemExit(f"Output path exists and is not a directory: {output_path}")
    if not any(output_path.iterdir()):
        return
    sentinels = {
        "corpus-summary.json",
        "candidate-comparison.csv",
        "scenario-breakdown.md",
    }
    if not any((output_path / sentinel).exists() for sentinel in sentinels):
        artifacts_root = (repo_root() / "artifacts/fitting").resolve()
        resolved_output = output_path.resolve()
        try:
            resolved_output.relative_to(artifacts_root)
        except ValueError as exc:
            raise SystemExit(
                "Refusing to overwrite non-empty directory without corpus summary "
                f"sentinel outside {artifacts_root}: {output_path}"
            ) from exc
    shutil.rmtree(output_path)


def write_candidate_csv(summary: dict[str, Any], output_path: Path) -> None:
    """Write candidate comparison CSV split by run mode."""
    with (output_path / "candidate-comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "heuristicCandidateId",
                "runMode",
                "experimentCount",
                "verdicts",
                "scenarioTags",
            ),
        )
        writer.writeheader()
        grouped: dict[tuple[str, str], dict[str, Counter[str]]] = defaultdict(
            lambda: {"verdicts": Counter(), "tags": Counter(), "count": Counter()}
        )
        for row in summary["experiments"]:
            key = (str(row["heuristicCandidateId"]), str(row["runMode"]))
            grouped[key]["count"]["experiments"] += 1
            grouped[key]["verdicts"][str(row["verdict"])] += 1
            for tag in row.get("scenarioTags", []):
                grouped[key]["tags"][str(tag)] += 1

        for (candidate, run_mode), values in sorted(grouped.items()):
            writer.writerow(
                {
                    "heuristicCandidateId": candidate,
                    "runMode": run_mode,
                    "experimentCount": values["count"]["experiments"],
                    "verdicts": compact_counts(values["verdicts"]),
                    "scenarioTags": compact_counts(values["tags"]),
                }
            )


def compact_counts(counter: Counter[str]) -> str:
    """Return stable semicolon-separated count text."""
    return "; ".join(f"{key}={value}" for key, value in sorted(counter.items()))


def format_markdown_summary(summary: dict[str, Any]) -> str:
    """Return a human-readable Markdown scenario breakdown."""
    lines = [
        "# Experiment corpus summary",
        "",
        f"- registry: `{summary['registryPath']}`",
        f"- experiments: {summary['experimentCount']}",
        "- evidence interpretation: shadow replay is a candidate filter/regression check; controlled live is causal command-behavior evidence.",
        "",
        "## Run modes",
        "",
    ]
    for mode, count in summary["runModeCounts"].items():
        lines.append(f"- `{mode}`: {count}")

    lines.extend(["", "## Verdicts", ""])
    for verdict, count in summary["verdictCounts"].items():
        lines.append(f"- `{verdict}`: {count}")

    lines.extend(["", "## Scenario tags", ""])
    if summary["scenarioTagCounts"]:
        for tag, count in summary["scenarioTagCounts"].items():
            lines.append(f"- `{tag}`: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Evidence by mode", ""])
    for mode, field_counts in summary["evidenceCountsByRunMode"].items():
        lines.append(f"### {mode}")
        for field_name, values in field_counts.items():
            if not values:
                continue
            lines.append(f"- {field_name}: {compact_plain_counts(values)}")
        if not any(field_counts.values()):
            lines.append("- no summarized evidence counters")
        lines.append("")

    lines.extend(["## Experiments", ""])
    lines.extend(
        [
            "| experiment | mode | candidate | verdict | selected mode | tags |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in summary["experiments"]:
        lines.append(
            "| {experiment} | {mode} | {candidate} | {verdict} | {selected} | {tags} |".format(
                experiment=markdown_cell(str(row["experimentId"])),
                mode=markdown_cell(str(row["runMode"])),
                candidate=markdown_cell(str(row["heuristicCandidateId"])),
                verdict=markdown_cell(str(row["verdict"])),
                selected=markdown_cell(str(row.get("selectedMode") or "unknown")),
                tags=markdown_cell(", ".join(row.get("scenarioTags", []))),
            )
        )

    if summary["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for warning in summary["warnings"]:
            lines.append(f"- {warning}")

    return "\n".join(lines) + "\n"


def compact_plain_counts(values: dict[str, int]) -> str:
    """Return deterministic inline count text for Markdown."""
    return ", ".join(f"{key}: {value}" for key, value in sorted(values.items()))


def markdown_cell(text: str) -> str:
    """Escape text for a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def write_outputs(summary: dict[str, Any], output_path: Path) -> None:
    """Write summary JSON, CSV, and Markdown outputs."""
    ensure_safe_output(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "corpus-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_candidate_csv(summary, output_path)
    (output_path / "scenario-breakdown.md").write_text(
        format_markdown_summary(summary),
        encoding="utf-8",
    )


def main() -> None:
    """Parse arguments and summarize the experiment corpus."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help=f"default: {DEFAULT_REGISTRY}")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"default: {DEFAULT_OUTPUT}")
    args = parser.parse_args()

    entries, warnings = load_registry(args.registry)
    summary = build_summary(args.registry, entries, warnings)
    write_outputs(summary, args.output)

    print(f"Loaded {summary['experimentCount']} experiment(s) from {args.registry}.")
    print(f"Wrote corpus summary to {args.output}.")
    print("Run modes: " + compact_plain_counts(summary["runModeCounts"]))
    if summary["warnings"]:
        print(f"Warnings: {len(summary['warnings'])}")

    raise SystemExit(0)


if __name__ == "__main__":
    main()
