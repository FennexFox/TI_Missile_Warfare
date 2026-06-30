#!/usr/bin/env python3
"""Replay offline-fitting candidate policies over decision-context rows."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import shutil
from typing import Any


DEFAULT_DATASET = Path("artifacts/offline-fitting/dataset/decision-contexts.jsonl")
DEFAULT_OUTPUT = Path("artifacts/offline-fitting/replay")
SCHEMA_VERSION = 1
CURRENT_POLICY_ID = "pressure-aware-bounded-live-v1"
REPORT_ONLY_POLICY_ID = "report-only-pressure-relief-v1"


def load_contexts(path: Path) -> list[dict[str, Any]]:
    """Load allocation decision-context rows."""
    if not path.exists():
        raise SystemExit(f"Dataset not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
            if not isinstance(value, dict):
                raise SystemExit(f"{path}:{line_number}: row is not a JSON object")
            rows.append(value)
    return rows


def numeric(value: Any) -> float | None:
    """Return a float for numeric JSON values."""
    if isinstance(value, bool) or value in (None, "unknown", "none", ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None


def selected_target(row: dict[str, Any]) -> dict[str, Any]:
    """Return the observed selected target as a candidate-like object."""
    target = row.get("selectedTarget", {})
    return {
        "targetId": target.get("targetId"),
        "target": target.get("target"),
        "targetTeam": target.get("targetTeam"),
        "score": target.get("score"),
        "isSelectedTarget": True,
        "isPressureTarget": target.get("targetId")
        == (target.get("originalTargetId") or target.get("targetId")),
    }


def alternative_by_id(row: dict[str, Any], target_id: Any) -> dict[str, Any] | None:
    """Find a normalized target alternative by id."""
    for alternative in row.get("targetAlternatives", []):
        if alternative.get("targetId") == target_id:
            return alternative
    return None


def exact_pressure_ready(row: dict[str, Any]) -> bool:
    """Return whether pressure evidence is exact enough for a favorable retarget."""
    return (
        row.get("replayReadiness", {}).get("hasExactPressure") is True
        and row.get("uncertainty", {}).get("lowerBoundPressure") is False
    )


def best_report_only_alternative(row: dict[str, Any]) -> dict[str, Any] | None:
    """Pick the highest-score non-pressure target when exact over-pressure exists."""
    pressure = row.get("pressure", {})
    if pressure.get("atOrAboveThreshold") is not True or not exact_pressure_ready(row):
        return None
    alternatives = [
        alternative
        for alternative in row.get("targetAlternatives", [])
        if alternative.get("isPressureTarget") is not True
        and alternative.get("targetId")
        and numeric(alternative.get("score")) is not None
    ]
    if not alternatives:
        return None
    return sorted(
        alternatives,
        key=lambda item: (
            numeric(item.get("score")) or float("-inf"),
            numeric(item.get("targetValue")) or float("-inf"),
        ),
        reverse=True,
    )[0]


def choose_target(row: dict[str, Any], policy_id: str) -> tuple[dict[str, Any], str]:
    """Replay one policy and return its selected target plus decision reason."""
    if policy_id == CURRENT_POLICY_ID:
        return selected_target(row), "observed-current-policy"
    alternative = best_report_only_alternative(row)
    if alternative is None:
        return selected_target(row), "blocked-or-no-exact-pressure-relief"
    return alternative, "exact-pressure-report-only-relief"


def retained_above_threshold_classification(row: dict[str, Any]) -> str:
    """Classify retained above-threshold rows without overclaiming weak evidence."""
    pressure = row.get("pressure", {})
    if pressure.get("retainedAboveThreshold") is not True:
        return "not-applicable"
    if row.get("uncertainty", {}).get("lowerBoundPressure") or row.get("uncertainty", {}).get(
        "missingAlternatives"
    ):
        return "inconclusive"
    if not exact_pressure_ready(row):
        return "inconclusive"
    alternatives = row.get("targetAlternatives", [])
    if any(
        alternative.get("isPressureTarget") is not True
        and numeric(alternative.get("score")) is not None
        for alternative in alternatives
    ):
        return "avoidable"
    return "unavoidable"


def guardrail_failures(row: dict[str, Any], chosen: dict[str, Any]) -> list[str]:
    """Return hard guardrail failures separately from objective penalties."""
    failures: list[str] = []
    command = row.get("command", {})
    launcher = row.get("launcher", {})
    chosen_team = chosen.get("targetTeam")
    if chosen_team and launcher.get("launcherTeam") and chosen_team == launcher.get("launcherTeam"):
        failures.append("friendly-target")
    if row.get("rawFields", {}).get("scopeViolation") is True:
        failures.append("scope-violation")
    if command.get("result") in {"wouldFail", "failed"}:
        failures.append(f"command-result-{command.get('result')}")
    if command.get("capReason") not in (None, "none", "unknown"):
        failures.append(f"command-cap-{command.get('capReason')}")
    if row.get("uncertainty", {}).get("spilloverClassification") not in (None, "notJoined"):
        failures.append("spillover-ambiguous")
    return failures


def target_score(row: dict[str, Any], target_id: Any) -> float | None:
    """Return comparable target-level score when available."""
    alternative = alternative_by_id(row, target_id)
    if alternative:
        return numeric(alternative.get("score"))
    return numeric(row.get("selectedTarget", {}).get("score"))


def objective_metrics(row: dict[str, Any], chosen: dict[str, Any]) -> dict[str, Any]:
    """Score soft surrogate objectives separately from hard guardrails."""
    pressure = row.get("pressure", {})
    selected = row.get("selectedTarget", {})
    chosen_id = chosen.get("targetId")
    chosen_alternative = alternative_by_id(row, chosen_id) or chosen
    chose_pressure_target = chosen_alternative.get("isPressureTarget") is True
    exact_at_or_above = pressure.get("atOrAboveThreshold") is True and exact_pressure_ready(row)
    selected_score = numeric(selected.get("score"))
    chosen_score = target_score(row, chosen_id)
    score_drop = (
        max(0.0, selected_score - chosen_score)
        if selected_score is not None and chosen_score is not None
        else 0.0
    )
    parser_warning_count = len(row.get("uncertainty", {}).get("parserWarnings", []))
    lower_bound = row.get("uncertainty", {}).get("lowerBoundPressure") is True
    missing_alternatives = row.get("uncertainty", {}).get("missingAlternatives") is True
    metrics = {
        "avoidableSelectedTargetOverPressurePenalty": 1 if exact_at_or_above and chose_pressure_target else 0,
        "pressureImbalancePenalty": 1 if exact_at_or_above and chose_pressure_target and row.get("targetAlternatives") else 0,
        "highScoreCoveragePenalty": round(score_drop, 6),
        "churnPenalty": 1 if chosen_id and chosen_id != selected.get("targetId") else 0,
        "evidenceWeakRetargetPenalty": 1 if chosen_id != selected.get("targetId") and (lower_bound or missing_alternatives) else 0,
        "uncertaintyPenalty": parser_warning_count + (1 if lower_bound else 0) + (1 if missing_alternatives else 0),
    }
    metrics["softPenaltyTotal"] = round(
        float(metrics["avoidableSelectedTargetOverPressurePenalty"])
        + float(metrics["pressureImbalancePenalty"])
        + float(metrics["highScoreCoveragePenalty"])
        + float(metrics["churnPenalty"])
        + float(metrics["evidenceWeakRetargetPenalty"])
        + float(metrics["uncertaintyPenalty"]),
        6,
    )
    return metrics


def replay_policy(row: dict[str, Any], policy_id: str) -> dict[str, Any]:
    """Replay one policy against one decision context."""
    chosen, reason = choose_target(row, policy_id)
    guardrails = guardrail_failures(row, chosen)
    metrics = objective_metrics(row, chosen)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "rowId": row.get("rowId"),
        "policyId": policy_id,
        "policyMode": "current-measurement" if policy_id == CURRENT_POLICY_ID else "report-only",
        "runMode": row.get("run", {}).get("runMode"),
        "parameterSnapshotHash": row.get("run", {}).get("parameterSnapshotHash"),
        "selectedTargetId": row.get("selectedTarget", {}).get("targetId"),
        "chosenTargetId": chosen.get("targetId"),
        "chosenTarget": chosen.get("target"),
        "decisionReason": reason,
        "retainedAboveThresholdClassification": retained_above_threshold_classification(row),
        "objectiveMetrics": metrics,
        "hardGuardrailFailures": guardrails,
        "hardGuardrailFailureCount": len(guardrails),
        "uncertainty": row.get("uncertainty", {}),
    }


def replay(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Replay all supported policies."""
    records: list[dict[str, Any]] = []
    for row in rows:
        for policy_id in (CURRENT_POLICY_ID, REPORT_ONLY_POLICY_ID):
            records.append(replay_policy(row, policy_id))
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate machine-readable candidate scores."""
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_policy[record["policyId"]].append(record)
    policies: list[dict[str, Any]] = []
    for policy_id, policy_records in sorted(by_policy.items()):
        classifications = Counter(
            str(record.get("retainedAboveThresholdClassification", "unknown"))
            for record in policy_records
        )
        guardrails = Counter(
            failure
            for record in policy_records
            for failure in record.get("hardGuardrailFailures", [])
        )
        policies.append(
            {
                "policyId": policy_id,
                "policyMode": policy_records[0]["policyMode"],
                "rowCount": len(policy_records),
                "softPenaltyTotal": round(
                    sum(record["objectiveMetrics"]["softPenaltyTotal"] for record in policy_records),
                    6,
                ),
                "hardGuardrailFailureCount": sum(
                    record["hardGuardrailFailureCount"] for record in policy_records
                ),
                "classificationCounts": dict(sorted(classifications.items())),
                "hardGuardrailFailures": dict(sorted(guardrails.items())),
            }
        )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "resultKind": "offline-fitting-candidate-replay",
        "recordCount": len(records),
        "policies": sorted(
            policies,
            key=lambda item: (
                item["hardGuardrailFailureCount"],
                item["softPenaltyTotal"],
                item["policyId"],
            ),
        ),
    }


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


def write_outputs(records: list[dict[str, Any]], summary: dict[str, Any], output_path: Path) -> None:
    """Write replay artifacts."""
    (output_path / "replay-results.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    (output_path / "replay-results.json").write_text(
        json.dumps(
            {
                "schemaVersion": SCHEMA_VERSION,
                "resultKind": "offline-fitting-candidate-replay",
                "records": records,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_path / "candidate-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def enforce_fixture_gate(summary: dict[str, Any]) -> None:
    """Fail if committed fixtures do not exercise both policies."""
    failures: list[str] = []
    policies = {policy["policyId"]: policy for policy in summary.get("policies", [])}
    if CURRENT_POLICY_ID not in policies:
        failures.append("current policy replay missing")
    if REPORT_ONLY_POLICY_ID not in policies:
        failures.append("report-only policy replay missing")
    if summary.get("recordCount", 0) <= 0:
        failures.append("no replay records emitted")
    if failures:
        raise SystemExit("Replay fixture gate failed: " + "; ".join(failures))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true", help="overwrite an existing artifacts output directory")
    parser.add_argument("--require-replay-evidence", action="store_true", help="fail if fixture replay is incomplete")
    return parser.parse_args()


def main() -> None:
    """Command entry point."""
    args = parse_args()
    rows = load_contexts(args.dataset)
    records = replay(rows)
    summary = summarize(records)
    if args.require_replay_evidence:
        enforce_fixture_gate(summary)
    ensure_safe_output(args.output, force=args.force)
    write_outputs(records, summary, args.output)
    print(f"Loaded decision contexts: {len(rows)}")
    print(f"Replay records: {summary['recordCount']}")
    print(f"Policies: {', '.join(policy['policyId'] for policy in summary['policies'])}")
    print(f"Wrote replay to {args.output}")


if __name__ == "__main__":
    main()
