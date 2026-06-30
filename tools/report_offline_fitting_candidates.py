#!/usr/bin/env python3
"""Generate ranked candidate reports from offline-fitting replay artifacts."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import shutil
from typing import Any


DEFAULT_REPLAY = Path("artifacts/offline-fitting/replay/replay-results.jsonl")
DEFAULT_SUMMARY = Path("artifacts/offline-fitting/replay/candidate-summary.json")
DEFAULT_OUTPUT = Path("artifacts/offline-fitting/report")
SCHEMA_VERSION = 1


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object."""
    if not path.exists():
        raise SystemExit(f"Required artifact not found: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Artifact is not a JSON object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL replay records."""
    if not path.exists():
        raise SystemExit(f"Required artifact not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise SystemExit(f"{path}:{line_number}: row is not a JSON object")
            rows.append(value)
    return rows


def policy_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group replay records by policy id."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record.get("policyId", "unknown"))].append(record)
    return grouped


def evidence_blocker_counts(records: list[dict[str, Any]]) -> Counter[str]:
    """Count uncertainty blockers that should downgrade candidate verdicts."""
    counts: Counter[str] = Counter()
    for record in records:
        uncertainty = record.get("uncertainty", {})
        if uncertainty.get("lowerBoundPressure") is True:
            counts["lower-bound-pressure"] += 1
        if uncertainty.get("missingAlternatives") is True:
            counts["missing-alternatives"] += 1
        if uncertainty.get("spilloverClassification") not in (None, "notJoined"):
            counts["spillover-ambiguity"] += 1
        parser_warnings = uncertainty.get("parserWarnings", [])
        if parser_warnings:
            counts["parser-warnings"] += len(parser_warnings)
    return counts


def verdict_for_policy(policy: dict[str, Any], records: list[dict[str, Any]]) -> tuple[str, str]:
    """Return a conservative machine-readable verdict and reason."""
    hard_failures = int(policy.get("hardGuardrailFailureCount", 0))
    classifications = policy.get("classificationCounts", {})
    blockers = evidence_blocker_counts(records)
    if hard_failures:
        return "blocked", "hard guardrail failures are present"
    if blockers:
        return "inconclusive", "evidence blockers or parser warnings are present"
    if int(classifications.get("avoidable", 0)) > 0:
        if policy.get("policyMode") == "report-only":
            return "needs-live-validation", "report-only candidate found avoidable retained over-pressure"
        return "candidate-filtered", "current policy measurement has avoidable retained over-pressure evidence"
    return "inconclusive", "no retained above-threshold candidate shortlist is justified"


def build_verdicts(summary: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Build candidate verdict JSON."""
    grouped = policy_records(records)
    verdicts: list[dict[str, Any]] = []
    for policy in summary.get("policies", []):
        policy_id = str(policy.get("policyId", "unknown"))
        policy_rows = grouped.get(policy_id, [])
        verdict, reason = verdict_for_policy(policy, policy_rows)
        verdicts.append(
            {
                "policyId": policy_id,
                "policyMode": policy.get("policyMode"),
                "verdict": verdict,
                "reason": reason,
                "rowCount": policy.get("rowCount", 0),
                "softPenaltyTotal": policy.get("softPenaltyTotal", 0),
                "hardGuardrailFailureCount": policy.get("hardGuardrailFailureCount", 0),
                "hardGuardrailFailures": policy.get("hardGuardrailFailures", {}),
                "classificationCounts": policy.get("classificationCounts", {}),
                "evidenceBlockerCounts": dict(sorted(evidence_blocker_counts(policy_rows).items())),
                "requiresLiveValidationBeforeBehaviorChange": verdict
                in {"candidate-filtered", "needs-live-validation"},
            }
        )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "resultKind": "offline-fitting-candidate-verdicts",
        "verdictVocabulary": [
            "candidate-filtered",
            "needs-live-validation",
            "inconclusive",
            "blocked",
        ],
        "verdicts": sorted(
            verdicts,
            key=lambda item: (
                item["verdict"] == "blocked",
                item["hardGuardrailFailureCount"],
                item["softPenaltyTotal"],
                item["policyId"],
            ),
        ),
        "liveValidationBoundary": (
            "Offline replay is a candidate filter only. Behavior-changing candidates still require "
            "controlled-live or fleet-wide-controlled validation."
        ),
    }


def markdown_cell(value: Any) -> str:
    """Format a markdown table cell."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def format_counts(values: dict[str, Any]) -> str:
    """Format compact sorted counts."""
    if not values:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(values.items()))


def ranked_candidates_markdown(verdicts: dict[str, Any]) -> str:
    """Render the ranked candidates report."""
    lines = [
        "# Ranked offline-fitting candidates",
        "",
        "Offline replay is a candidate filter only. It is not causal proof of live combat improvement.",
        "Any behavior-changing candidate still needs controlled-live or fleet-wide-controlled validation.",
        "",
        "| Rank | Policy | Mode | Verdict | Soft penalty | Hard failures | Classifications | Evidence blockers |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for index, verdict in enumerate(verdicts["verdicts"], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    markdown_cell(verdict["policyId"]),
                    markdown_cell(verdict.get("policyMode", "unknown")),
                    markdown_cell(verdict["verdict"]),
                    markdown_cell(verdict["softPenaltyTotal"]),
                    markdown_cell(verdict["hardGuardrailFailureCount"]),
                    markdown_cell(format_counts(verdict.get("classificationCounts", {}))),
                    markdown_cell(format_counts(verdict.get("evidenceBlockerCounts", {}))),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `candidate-filtered` and `needs-live-validation` are not live behavior approval.",
            "- `blocked` means hard guardrail failures are present in the replayed evidence.",
            "- `inconclusive` means evidence quality prevents a favorable candidate verdict.",
            "- Outcome rows are not used as rewards or kill proof in this report.",
        ]
    )
    return "\n".join(lines) + "\n"


def guardrail_markdown(verdicts: dict[str, Any]) -> str:
    """Render hard guardrail and evidence blocker report."""
    lines = [
        "# Offline-fitting guardrail report",
        "",
        "Hard guardrails are reported separately from soft surrogate objective scores.",
        "",
        "| Policy | Hard guardrail failures | Evidence blockers | Verdict impact |",
        "| --- | --- | --- | --- |",
    ]
    for verdict in verdicts["verdicts"]:
        impact = verdict["reason"]
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(verdict["policyId"]),
                    markdown_cell(format_counts(verdict.get("hardGuardrailFailures", {}))),
                    markdown_cell(format_counts(verdict.get("evidenceBlockerCounts", {}))),
                    markdown_cell(impact),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Rows with parser warnings, lower-bound pressure, missing alternatives, spillover ambiguity,",
            "or command-safety failures must not receive overconfident favorable verdicts.",
        ]
    )
    return "\n".join(lines) + "\n"


def ensure_safe_output(output_path: Path, *, force: bool) -> None:
    """Prepare an artifacts output directory."""
    resolved = output_path.resolve()
    if resolved.exists():
        if not force:
            raise SystemExit(f"Output already exists: {output_path} (use --force)")
        if "artifacts" not in resolved.parts:
            raise SystemExit(f"Refusing to clear non-artifacts output path: {output_path}")
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def write_outputs(verdicts: dict[str, Any], output_path: Path) -> None:
    """Write report artifacts."""
    (output_path / "candidate-verdicts.json").write_text(
        json.dumps(verdicts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_path / "ranked-candidates.md").write_text(
        ranked_candidates_markdown(verdicts),
        encoding="utf-8",
    )
    (output_path / "guardrail-report.md").write_text(
        guardrail_markdown(verdicts),
        encoding="utf-8",
    )


def enforce_fixture_gate(verdicts: dict[str, Any], output_path: Path) -> None:
    """Validate required report artifacts and verdict vocabulary."""
    failures: list[str] = []
    verdict_values = {item.get("verdict") for item in verdicts.get("verdicts", [])}
    if not (output_path / "ranked-candidates.md").exists():
        failures.append("ranked-candidates.md missing")
    if not (output_path / "candidate-verdicts.json").exists():
        failures.append("candidate-verdicts.json missing")
    if not (output_path / "guardrail-report.md").exists():
        failures.append("guardrail-report.md missing")
    if not verdict_values:
        failures.append("no candidate verdicts emitted")
    allowed = set(verdicts.get("verdictVocabulary", []))
    if not verdict_values <= allowed:
        failures.append("unknown verdict value emitted")
    if failures:
        raise SystemExit("Report fixture gate failed: " + "; ".join(failures))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, default=DEFAULT_REPLAY)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true", help="overwrite an existing artifacts output directory")
    parser.add_argument("--require-report-evidence", action="store_true", help="fail if required report outputs are missing")
    return parser.parse_args()


def main() -> None:
    """Command entry point."""
    args = parse_args()
    summary = load_json(args.summary)
    records = load_jsonl(args.replay)
    verdicts = build_verdicts(summary, records)
    ensure_safe_output(args.output, force=args.force)
    write_outputs(verdicts, args.output)
    if args.require_report_evidence:
        enforce_fixture_gate(verdicts, args.output)
    print(f"Loaded replay records: {len(records)}")
    print(f"Candidate verdicts: {len(verdicts['verdicts'])}")
    print(f"Wrote report to {args.output}")


if __name__ == "__main__":
    main()
