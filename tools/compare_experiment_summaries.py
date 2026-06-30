#!/usr/bin/env python3
"""Compare two experiment corpus summaries for bounded-live tuning review."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


DEFAULT_MODE = "fleet-wide-controlled"
OBJECTIVE_METRICS = (
    "boundedLiveAppliedResults",
    "boundedLiveAppliedWithTargetAlternativeDenominatorGtOne",
    "boundedLiveAppliedWithComparableAlternativeFeatures",
    "boundedLiveAppliedWithFullyComparableScoreRankEvidence",
    "boundedLiveAppliedWithKnownPriorInFlightPressure",
    "boundedLiveAppliedWithLowerBoundPriorInFlightPressure",
    "boundedLiveRetainedSelectedTargetDecisionsAboveThreshold",
    "boundedLiveRetargetedDecisionsAboveThreshold",
    "boundedLiveLowerBoundPressureDiagnosticOnlyRows",
    "potentialOverConcentrationCandidates",
    "potentialCapMisallocationCandidates",
)
GUARDRAIL_COUNT_FIELDS = (
    "failed_command_counts",
    "regression_counts",
    "target_mismatch_counts",
    "vanilla_spillover_counts",
)
BLOCKER_FIELDS = (
    "bounded_live_hard_measurement_blocker_counts",
    "bounded_live_external_outcome_blocker_counts",
    "bounded_live_tuning_readiness_blocker_counts",
)


@dataclass(frozen=True)
class CorpusView:
    """Relevant bounded-live counters from one corpus summary."""

    path: Path
    experiment_count: int
    run_mode_counts: dict[str, int]
    verdict_counts: dict[str, int]
    scenario_tag_counts: dict[str, int]
    candidate_counts: dict[str, int]
    mode_counts: dict[str, dict[str, int]]


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise SystemExit(f"Summary not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON summary {path}: {exc}") from None
    if not isinstance(value, dict):
        raise SystemExit(f"Summary must be a JSON object: {path}")
    return value


def int_dict(value: Any) -> dict[str, int]:
    """Return a string->int dictionary, ignoring non-integer values."""
    if not isinstance(value, dict):
        return {}
    return {str(key): count for key, count in value.items() if isinstance(count, int)}


def mode_bucket(summary: dict[str, Any], mode: str) -> dict[str, Any]:
    """Return the evidence bucket for a run mode."""
    buckets = summary.get("evidenceCountsByRunMode")
    if not isinstance(buckets, dict):
        return {}
    bucket = buckets.get(mode)
    return bucket if isinstance(bucket, dict) else {}


def load_corpus_view(path: Path, mode: str) -> CorpusView:
    """Load a corpus summary and keep only the counters needed for comparison."""
    summary = load_json(path)
    buckets = summary.get("evidenceCountsByRunMode")
    if not isinstance(buckets, dict) or not isinstance(buckets.get(mode), dict):
        raise SystemExit(f"Run mode '{mode}' not found in summary: {path}")
    bucket = buckets[mode]
    mode_counts: dict[str, dict[str, int]] = {}
    for key in (
        "direct_command_spend_counts",
        "skipped_command_counts",
        *GUARDRAIL_COUNT_FIELDS,
        "bounded_live_tuning_readiness_counts",
        *BLOCKER_FIELDS,
    ):
        mode_counts[key] = int_dict(bucket.get(key))

    return CorpusView(
        path=path,
        experiment_count=int(summary.get("experimentCount", 0)),
        run_mode_counts=int_dict(summary.get("runModeCounts")),
        verdict_counts=int_dict(summary.get("verdictCounts")),
        scenario_tag_counts=int_dict(summary.get("scenarioTagCounts")),
        candidate_counts=int_dict(summary.get("heuristicCandidateCounts")),
        mode_counts=mode_counts,
    )


def count(view: CorpusView, group: str, key: str) -> int:
    """Return a named counter from a corpus view."""
    return view.mode_counts.get(group, {}).get(key, 0)


def sum_group(view: CorpusView, group: str) -> int:
    """Return the sum of all counters in a group."""
    return sum(view.mode_counts.get(group, {}).values())


def format_counts(values: dict[str, int]) -> str:
    """Format a counter mapping for Markdown."""
    if not values:
        return "none"
    return ", ".join(f"{key}: {value}" for key, value in sorted(values.items()))


def metric_delta(baseline: CorpusView, followup: CorpusView, metric: str) -> tuple[int, int, int]:
    """Return baseline, follow-up, and delta for one readiness metric."""
    before = count(baseline, "bounded_live_tuning_readiness_counts", metric)
    after = count(followup, "bounded_live_tuning_readiness_counts", metric)
    return before, after, after - before


def guardrail_failures(baseline: CorpusView, followup: CorpusView) -> list[str]:
    """Return hard guardrail failures visible in the summaries."""
    failures: list[str] = []
    for group in GUARDRAIL_COUNT_FIELDS:
        value = sum_group(followup, group)
        if value:
            failures.append(f"{group} has {value} follow-up count(s)")

    failed_commands = sum_group(followup, "failed_command_counts")
    if failed_commands:
        failures.append(f"failed command counts are nonzero ({failed_commands})")

    baseline_modes = set(baseline.run_mode_counts)
    followup_modes = set(followup.run_mode_counts)
    if baseline_modes != followup_modes:
        failures.append(
            "run mode sets differ: "
            f"baseline={sorted(baseline_modes)}, follow-up={sorted(followup_modes)}"
        )
    return failures


def blocker_regressions(baseline: CorpusView, followup: CorpusView) -> list[str]:
    """Return blocker groups that got worse in the follow-up summary."""
    regressions: list[str] = []
    for group in BLOCKER_FIELDS:
        before = sum_group(baseline, group)
        after = sum_group(followup, group)
        if after > before:
            regressions.append(f"{group} increased from {before} to {after}")
    return regressions


def choose_verdict(baseline: CorpusView, followup: CorpusView) -> tuple[str, str, str]:
    """Choose a conservative verdict from summary counters."""
    failures = guardrail_failures(baseline, followup)
    if failures:
        return "contradictory", "high", "; ".join(failures)

    if baseline.experiment_count != followup.experiment_count:
        return (
            "inconclusive",
            "medium",
            f"experiment counts differ: baseline={baseline.experiment_count}, follow-up={followup.experiment_count}",
        )
    if baseline.run_mode_counts != followup.run_mode_counts:
        return (
            "inconclusive",
            "medium",
            "run mode distributions differ: "
            f"baseline={format_counts(baseline.run_mode_counts)}, "
            f"follow-up={format_counts(followup.run_mode_counts)}",
        )
    if baseline.scenario_tag_counts != followup.scenario_tag_counts:
        return (
            "inconclusive",
            "medium",
            "scenario tag distributions differ: "
            f"baseline={format_counts(baseline.scenario_tag_counts)}, "
            f"follow-up={format_counts(followup.scenario_tag_counts)}",
        )

    blocker_regression_reasons = blocker_regressions(baseline, followup)
    if blocker_regression_reasons:
        return "inconclusive", "medium", "; ".join(blocker_regression_reasons)

    applied_before, applied_after, _ = metric_delta(baseline, followup, "boundedLiveAppliedResults")
    retained_before, retained_after, retained_delta = metric_delta(
        baseline, followup, "boundedLiveRetainedSelectedTargetDecisionsAboveThreshold"
    )
    retargeted_before, retargeted_after, retargeted_delta = metric_delta(
        baseline, followup, "boundedLiveRetargetedDecisionsAboveThreshold"
    )

    sparse = applied_before < 5 or applied_after < 5
    retained_clean = retained_after == 0 or retained_delta < 0
    retarget_preserved = retargeted_after > 0 and retargeted_delta >= 0

    if sparse:
        return (
            "inconclusive",
            "medium",
            "guardrails held, but bounded-live applied evidence is sparse",
        )
    if retained_clean and retarget_preserved:
        return (
            "supportive",
            "medium",
            "objective pressure counters were preserved or improved with clean guardrails",
        )
    if retained_after == retained_before and retargeted_after == retargeted_before:
        return "no material change", "medium", "objective counters did not materially move"
    return "inconclusive", "low", "mixed objective movement requires human review"


def render_markdown(
    baseline: CorpusView,
    followup: CorpusView,
    mode: str,
    comparison_id: str,
) -> tuple[str, dict[str, Any]]:
    """Render a Markdown comparison and return machine-readable verdict data."""
    verdict, confidence, primary_reason = choose_verdict(baseline, followup)
    failures = guardrail_failures(baseline, followup)

    lines = [
        "# Candidate Comparison",
        "",
        "## Run identity",
        "",
        f"- comparisonId: `{comparison_id}`",
        f"- baselineSummary: `{baseline.path}`",
        f"- followupSummary: `{followup.path}`",
        f"- runMode: `{mode}`",
        f"- baselineCandidates: {format_counts(baseline.candidate_counts)}",
        f"- followupCandidates: {format_counts(followup.candidate_counts)}",
        "",
        "## Comparability checklist",
        "",
        "| Check | Status | Notes |",
        "| --- | --- | --- |",
        f"| Same run mode | {'same' if set(baseline.run_mode_counts) == set(followup.run_mode_counts) else 'different'} | baseline={format_counts(baseline.run_mode_counts)}; follow-up={format_counts(followup.run_mode_counts)} |",
        "| Same command caps unless intentionally changed | unknown | Summaries do not encode full runtime settings; verify parameter snapshots. |",
        "| Same diagnostics toggles | unknown | Parser/log health must be checked separately. |",
        "| Raw logs private and not committed | same | Imports omit source Player.log path from registry. |",
        "| Outcome hooks used only as validation context | same | Summary comparison does not consume OutcomeLog rows. |",
        "",
        "## Objective metrics",
        "",
        "| Metric | Baseline | Follow-up | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for metric in OBJECTIVE_METRICS:
        before, after, delta = metric_delta(baseline, followup, metric)
        lines.append(f"| {metric} | {before} | {after} | {delta:+d} |")

    lines.extend(
        [
            "",
            "## Guardrail checks",
            "",
            "| Guardrail | Baseline | Follow-up | Pass/Fail |",
            "| --- | --- | --- | --- |",
        ]
    )
    for group in GUARDRAIL_COUNT_FIELDS:
        before = format_counts(baseline.mode_counts.get(group, {}))
        after = format_counts(followup.mode_counts.get(group, {}))
        status = "fail" if sum_group(followup, group) else "pass"
        lines.append(f"| {group} | {before} | {after} | {status} |")

    lines.extend(
        [
            "",
            "## Blocker deltas",
            "",
            "| Blocker group | Baseline | Follow-up |",
            "| --- | --- | --- |",
        ]
    )
    for group in BLOCKER_FIELDS:
        before = format_counts(baseline.mode_counts.get(group, {}))
        after = format_counts(followup.mode_counts.get(group, {}))
        lines.append(f"| {group} | {before} | {after} |")

    regressions = "none" if not failures else "; ".join(failures)
    next_action = (
        "Candidate B may proceed only as a conservative report-only or diagnostics-only step."
        if verdict in {"inconclusive", "no material change"}
        else "Do not proceed to Candidate B without human review."
        if verdict == "contradictory"
        else "Candidate B is not required by this comparison; preserve current behavior unless more evidence is needed."
    )
    lines.extend(
        [
            "",
            "## Verdict recommendation",
            "",
            "```text",
            f"verdict: {verdict}",
            f"confidence: {confidence}",
            f"primaryReason: {primary_reason}",
            "secondaryReasons: evidence remains local/private and corpus size is limited",
            f"regressions: {regressions}",
            f"nextAction: {next_action}",
            "```",
            "",
            "## Human review notes",
            "",
            "- This helper compares corpus summaries only; it does not inspect raw combat video or join OutcomeLog rows to AllocationLog rows.",
            "- Treat `evidence-limited` experiment verdicts as a reason to prefer report-only Candidate B work before combat-behavior changes.",
        ]
    )

    data = {
        "comparisonId": comparison_id,
        "baselineSummary": str(baseline.path),
        "followupSummary": str(followup.path),
        "runMode": mode,
        "verdict": verdict,
        "confidence": confidence,
        "primaryReason": primary_reason,
        "guardrailFailures": failures,
        "objectiveMetrics": {
            metric: {
                "baseline": metric_delta(baseline, followup, metric)[0],
                "followup": metric_delta(baseline, followup, metric)[1],
                "delta": metric_delta(baseline, followup, metric)[2],
            }
            for metric in OBJECTIVE_METRICS
        },
    }
    return "\n".join(lines) + "\n", data


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-summary", required=True, type=Path)
    parser.add_argument("--followup-summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--run-mode", default=DEFAULT_MODE)
    parser.add_argument("--comparison-id", default="candidate-comparison")
    return parser.parse_args()


def main() -> None:
    """Compare two corpus summaries and write the result."""
    args = parse_args()
    baseline = load_corpus_view(args.baseline_summary, args.run_mode)
    followup = load_corpus_view(args.followup_summary, args.run_mode)
    markdown, data = render_markdown(baseline, followup, args.run_mode, args.comparison_id)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote comparison to {args.output}")
    if args.json_output:
        print(f"Wrote comparison JSON to {args.json_output}")
    print(f"Verdict: {data['verdict']} ({data['confidence']})")


if __name__ == "__main__":
    main()
