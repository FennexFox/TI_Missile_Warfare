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
        and row.get("evidenceState", {}).get("pressure") == "exact"
    )


def auditable_alternatives_ready(row: dict[str, Any]) -> bool:
    """Return whether target-alternative and score/rank evidence is auditable."""
    evidence = row.get("evidenceState", {})
    return evidence.get("targetAlternatives") == "exact" and evidence.get("scoreRank") == "exact"


def is_known_friendly_alternative(row: dict[str, Any], alternative: dict[str, Any]) -> bool:
    """Return whether a target alternative is known friendly to the launcher."""
    launcher_team = row.get("launcher", {}).get("launcherTeam")
    target_team = alternative.get("targetTeam")
    return bool(launcher_team and target_team and launcher_team == target_team)


def best_report_only_alternative(row: dict[str, Any]) -> dict[str, Any] | None:
    """Pick the highest-score safe non-pressure target when exact over-pressure exists."""
    pressure = row.get("pressure", {})
    if (
        pressure.get("atOrAboveThreshold") is not True
        or not exact_pressure_ready(row)
        or not auditable_alternatives_ready(row)
    ):
        return None
    alternatives = [
        alternative
        for alternative in row.get("targetAlternatives", [])
        if alternative.get("isPressureTarget") is not True
        and alternative.get("targetId")
        and numeric(alternative.get("score")) is not None
        and not is_known_friendly_alternative(row, alternative)
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
    if not exact_pressure_ready(row) or not auditable_alternatives_ready(row):
        return "inconclusive"
    alternatives = row.get("targetAlternatives", [])
    non_pressure = [alternative for alternative in alternatives if alternative.get("isPressureTarget") is not True]
    if not non_pressure:
        return "unavoidable"
    if any(
        numeric(alternative.get("score")) is not None
        and alternative.get("targetTeam") != row.get("launcher", {}).get("launcherTeam")
        for alternative in non_pressure
    ):
        return "avoidable"
    return "inconclusive"


def observed_row_failures(row: dict[str, Any]) -> list[str]:
    """Return hard failures in the observed source row."""
    failures: list[str] = []
    command = row.get("command", {})
    launcher = row.get("launcher", {})
    selected = row.get("selectedTarget", {})
    selected_team = selected.get("targetTeam")
    if selected_team and launcher.get("launcherTeam") and selected_team == launcher.get("launcherTeam"):
        failures.append("observed-friendly-target")
    if row.get("rawFields", {}).get("scopeViolation") is True:
        failures.append("observed-scope-violation")
    if command.get("result") in {"wouldFail", "failed"}:
        failures.append(f"observed-command-result-{command.get('result')}")
    if command.get("capReason") not in (None, "none", "unknown"):
        failures.append(f"observed-command-cap-{command.get('capReason')}")
    if row.get("uncertainty", {}).get("spilloverClassification") not in (None, "notJoined"):
        failures.append("observed-spillover-ambiguous")
    return failures


def candidate_guardrail_failures(row: dict[str, Any], chosen: dict[str, Any]) -> list[str]:
    """Return hard failures introduced by a replayed candidate choice."""
    failures: list[str] = []
    launcher = row.get("launcher", {})
    chosen_team = chosen.get("targetTeam")
    selected_id = row.get("selectedTarget", {}).get("targetId")
    if (
        chosen.get("targetId") != selected_id
        and chosen_team
        and launcher.get("launcherTeam")
        and chosen_team == launcher.get("launcherTeam")
    ):
        failures.append("candidate-friendly-target")
    return failures


def guardrail_failures(row: dict[str, Any], chosen: dict[str, Any]) -> list[str]:
    """Return all hard guardrail failures for backward-compatible output."""
    return observed_row_failures(row) + candidate_guardrail_failures(row, chosen)


def evidence_blockers(row: dict[str, Any]) -> list[str]:
    """Return row-level evidence blockers for favorable classification."""
    blockers: list[str] = []
    pressure = row.get("pressure", {})
    evidence = row.get("evidenceState", {})
    pressure_relevant = pressure.get("retainedAboveThreshold") is True or pressure.get("atOrAboveThreshold") is True
    if pressure_relevant and evidence.get("pressure") != "exact":
        blockers.append(f"pressure-{evidence.get('pressure', 'unknown')}")
    if pressure.get("retainedAboveThreshold") is True:
        if evidence.get("targetAlternatives") != "exact":
            blockers.append(f"target-alternatives-{evidence.get('targetAlternatives', 'unknown')}")
        if evidence.get("scoreRank") != "exact":
            blockers.append(f"score-rank-{evidence.get('scoreRank', 'unknown')}")
    if row.get("uncertainty", {}).get("missingAlternatives") is True and pressure_relevant:
        blockers.append("missing-alternatives")
    return sorted(set(blockers))


def diagnostic_warnings(row: dict[str, Any]) -> list[str]:
    """Return non-blocking diagnostic warnings preserved for reporting."""
    return list(row.get("uncertainty", {}).get("parserWarnings", []))


def score_value_and_space(row: dict[str, Any], target_id: Any) -> tuple[float | None, str | None]:
    """Return a score value with its comparison space."""
    alternative = alternative_by_id(row, target_id)
    if alternative:
        return numeric(alternative.get("score")), alternative.get("scoreSpace")
    selected = row.get("selectedTarget", {})
    if target_id == selected.get("targetId"):
        return numeric(selected.get("score")), selected.get("scoreSpace")
    return None, None


def score_delta_evaluation(row: dict[str, Any], chosen: dict[str, Any]) -> dict[str, Any]:
    """Return a score delta only when selected and chosen scores are comparable."""
    selected = row.get("selectedTarget", {})
    selected_id = selected.get("targetId")
    chosen_id = chosen.get("targetId")
    target_changed = bool(chosen_id and chosen_id != selected_id)
    if not target_changed:
        score, space = score_value_and_space(row, selected_id)
        return {
            "scoreDelta": 0.0 if score is not None else None,
            "scoreDeltaKind": "no-target-change",
            "scoreDeltaScoreSpace": space,
            "scoreDeltaReason": "selected-target-retained",
        }

    selected_score, selected_space = score_value_and_space(row, selected_id)
    chosen_score, chosen_space = score_value_and_space(row, chosen_id)
    if selected_score is None or chosen_score is None:
        return {
            "scoreDelta": None,
            "scoreDeltaKind": "not-comparable",
            "scoreDeltaScoreSpace": None,
            "scoreDeltaReason": "missing-score",
        }
    if selected_space != chosen_space:
        return {
            "scoreDelta": None,
            "scoreDeltaKind": "not-comparable",
            "scoreDeltaScoreSpace": None,
            "scoreDeltaReason": f"score-space-mismatch:{selected_space}->{chosen_space}",
        }
    return {
        "scoreDelta": round(chosen_score - selected_score, 6),
        "scoreDeltaKind": "changed-target-comparable",
        "scoreDeltaScoreSpace": selected_space,
        "scoreDeltaReason": "target-alternative-score-space",
    }


def objective_metrics(row: dict[str, Any], chosen: dict[str, Any]) -> dict[str, Any]:
    """Score soft surrogate objectives separately from hard guardrails."""
    pressure = row.get("pressure", {})
    selected = row.get("selectedTarget", {})
    chosen_id = chosen.get("targetId")
    chosen_alternative = alternative_by_id(row, chosen_id) or chosen
    chose_pressure_target = chosen_alternative.get("isPressureTarget") is True
    exact_at_or_above = pressure.get("atOrAboveThreshold") is True and exact_pressure_ready(row)
    target_changed = bool(chosen_id and chosen_id != selected.get("targetId"))
    score_delta = score_delta_evaluation(row, chosen)
    comparable_delta = numeric(score_delta.get("scoreDelta"))
    score_drop = (
        max(0.0, -comparable_delta)
        if target_changed and comparable_delta is not None
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


def row_evaluation(row: dict[str, Any], chosen: dict[str, Any], policy_id: str) -> dict[str, Any]:
    """Separate row-level exclusion, blocker, and favorable-signal state."""
    observed_failures = observed_row_failures(row)
    candidate_failures = candidate_guardrail_failures(row, chosen)
    blockers = evidence_blockers(row)
    warnings = diagnostic_warnings(row)
    selected = row.get("selectedTarget", {})
    target_changed = bool(chosen.get("targetId") and chosen.get("targetId") != selected.get("targetId"))
    score_delta = score_delta_evaluation(row, chosen)
    classification = retained_above_threshold_classification(row)
    exclusion_reasons = observed_failures + candidate_failures + blockers
    is_diagnostic_signal = (
        not exclusion_reasons
        and policy_id == CURRENT_POLICY_ID
        and classification == "avoidable"
    )
    is_candidate_improvement = (
        not exclusion_reasons
        and policy_id == REPORT_ONLY_POLICY_ID
        and target_changed
        and chosen.get("isPressureTarget") is not True
    )
    return {
        "rowEligibility": "excluded" if exclusion_reasons else "eligible",
        "rowExclusionReasons": exclusion_reasons,
        "observedRowFailures": observed_failures,
        "candidateGuardrailFailures": candidate_failures,
        "evidenceBlockers": blockers,
        "diagnosticWarnings": warnings,
        "diagnosticWarningCount": len(warnings),
        "targetChanged": target_changed,
        **score_delta,
        "isDiagnosticSignal": is_diagnostic_signal,
        "isCandidateImprovementSignal": is_candidate_improvement,
    }


def replay_policy(row: dict[str, Any], policy_id: str) -> dict[str, Any]:
    """Replay one policy against one decision context."""
    chosen, reason = choose_target(row, policy_id)
    evaluation = row_evaluation(row, chosen, policy_id)
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
        "rowEvaluation": evaluation,
        "evidenceState": row.get("evidenceState", {}),
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
        row_evaluations = [record.get("rowEvaluation", {}) for record in policy_records]
        eligibility = Counter(str(evaluation.get("rowEligibility", "unknown")) for evaluation in row_evaluations)
        observed_failures = Counter(
            failure for evaluation in row_evaluations for failure in evaluation.get("observedRowFailures", [])
        )
        candidate_failures = Counter(
            failure for evaluation in row_evaluations for failure in evaluation.get("candidateGuardrailFailures", [])
        )
        blockers = Counter(
            blocker for evaluation in row_evaluations for blocker in evaluation.get("evidenceBlockers", [])
        )
        eligible_score_deltas = [
            evaluation.get("scoreDelta")
            for evaluation in row_evaluations
            if evaluation.get("rowEligibility") == "eligible" and evaluation.get("scoreDelta") is not None
        ]
        eligible_changed_score_deltas = [
            evaluation.get("scoreDelta")
            for evaluation in row_evaluations
            if evaluation.get("rowEligibility") == "eligible"
            and evaluation.get("targetChanged") is True
            and evaluation.get("scoreDelta") is not None
        ]
        score_delta_kinds = Counter(
            str(evaluation.get("scoreDeltaKind", "unknown"))
            for evaluation in row_evaluations
            if evaluation.get("rowEligibility") == "eligible"
        )
        changed_eligible = sum(
            1
            for evaluation in row_evaluations
            if evaluation.get("rowEligibility") == "eligible" and evaluation.get("targetChanged") is True
        )
        diagnostic_signals = sum(
            1 for evaluation in row_evaluations if evaluation.get("isDiagnosticSignal") is True
        )
        candidate_improvements = sum(
            1 for evaluation in row_evaluations if evaluation.get("isCandidateImprovementSignal") is True
        )
        policies.append(
            {
                "policyId": policy_id,
                "policyMode": policy_records[0]["policyMode"],
                "rowCount": len(policy_records),
                "eligibleRowCount": eligibility.get("eligible", 0),
                "excludedRowCount": eligibility.get("excluded", 0),
                "badObservedRowCount": sum(observed_failures.values()),
                "badCandidateRowCount": sum(candidate_failures.values()),
                "evidenceBlockedRowCount": sum(1 for evaluation in row_evaluations if evaluation.get("evidenceBlockers")),
                "diagnosticSignalRowCount": diagnostic_signals,
                "candidateImprovementRowCount": candidate_improvements,
                "targetChangeCount": changed_eligible,
                "scoreDeltaTotalEligible": round(sum(eligible_score_deltas), 6),
                "scoreDeltaAverageEligible": round(sum(eligible_score_deltas) / len(eligible_score_deltas), 6)
                if eligible_score_deltas
                else None,
                "changedScoreDeltaTotalEligible": round(sum(eligible_changed_score_deltas), 6),
                "changedScoreDeltaAverageEligible": round(
                    sum(eligible_changed_score_deltas) / len(eligible_changed_score_deltas), 6
                )
                if eligible_changed_score_deltas
                else None,
                "scoreDeltaKindCounts": dict(sorted(score_delta_kinds.items())),
                "rowEligibilityCounts": dict(sorted(eligibility.items())),
                "observedRowFailures": dict(sorted(observed_failures.items())),
                "candidateGuardrailFailures": dict(sorted(candidate_failures.items())),
                "evidenceBlockers": dict(sorted(blockers.items())),
                "diagnosticWarningCount": sum(
                    int(evaluation.get("diagnosticWarningCount", 0)) for evaluation in row_evaluations
                ),
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
