#!/usr/bin/env python3
"""Regression tests for offline-fitting evidence and report semantics."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_offline_fitting_dataset as dataset
import replay_offline_fitting_candidates as replay
import report_offline_fitting_candidates as report


REPO_ROOT = TOOLS_DIR.parent
FIXTURE_REGISTRY = REPO_ROOT / "tools" / "fixtures" / "offline_fitting" / "registry.jsonl"


def exact_retained_row() -> dict:
    """Return a minimal exact retained above-threshold row."""
    return {
        "run": {"runMode": "fixture"},
        "launcher": {"launcherTeam": "player"},
        "selectedTarget": {"targetId": "red", "targetTeam": "enemy", "score": 3.0},
        "targetAlternatives": [
            {
                "targetId": "red",
                "target": "Red",
                "targetTeam": "enemy",
                "isPressureTarget": True,
                "score": 3.0,
                "targetValue": 10,
                "pressureEvidenceState": "exact",
                "evidenceState": {"pressure": "exact"},
            },
            {
                "targetId": "blue",
                "target": "Blue",
                "targetTeam": "enemy",
                "isPressureTarget": False,
                "score": 2.0,
                "targetValue": 8,
                "pressureEvidenceState": "not-applicable",
                "evidenceState": {"pressure": "not-applicable"},
            },
        ],
        "pressure": {"retainedAboveThreshold": True, "atOrAboveThreshold": True},
        "replayReadiness": {"hasExactPressure": True},
        "uncertainty": {"lowerBoundPressure": False, "missingAlternatives": False, "parserWarnings": []},
        "evidenceState": {"pressure": "exact", "targetAlternatives": "exact", "scoreRank": "exact"},
        "command": {"result": "applied", "capReason": "none"},
        "rawFields": {},
    }


class EvidenceStateTests(unittest.TestCase):
    def test_pipe_alternatives_and_evidence_states_are_explicit(self) -> None:
        pairs = dataset.normalized_raw_fields(
            {
                "targetId": "red",
                "boundedLiveOriginalTargetId": "red",
                "boundedLivePressureDecision": "retained",
                "boundedLivePressureThreshold": "4",
                "boundedLiveDecisionPressure": "4",
                "boundedLiveDecisionInFlightEvidenceQuality": "exact",
                "selectedTargetPriorMissileInFlightEstimateBound": "exact",
                "selectedTargetScore": "3.0",
                "selectedTargetRank": "1",
                "selectedTargetRankComparisonSpace": "targetAlternativeScores",
                "selectedTargetRankLevel": "target-level",
                "selectedTargetRankConfidence": "exact",
                "targetAlternativeDenominator": "2",
                "targetAlternativeIds": "red|blue",
                "targetAlternativeNames": "Red|Blue",
                "targetAlternativeTeams": "enemy|enemy",
                "targetAlternativeScores": "3.0|2.0",
                "targetAlternativeValues": "10|8",
                "targetAlternativeCountTruncated": "0",
                "targetAlternativeFeatureEvidence": "allocatorComparableFeatures",
                "targetAlternativeFeatureMissingCount": "0",
                "targetAlternativeScoreSpace": "diagnosticTargetAlternativeRecomputed",
                "targetOutcomeAttribution": "evidenceLimited",
                "attributionConfidence": "outcomeCorrelationPending",
            }
        )
        alternatives, warnings = dataset.target_alternatives(pairs)
        states = dataset.evidence_state(pairs, alternatives, direct_launch_rows=1)

        self.assertEqual([], warnings)
        self.assertEqual(2, len(alternatives))
        self.assertEqual(2.0, alternatives[1]["score"])
        self.assertEqual("exact", alternatives[0]["pressureEvidenceState"])
        self.assertEqual("not-applicable", alternatives[1]["pressureEvidenceState"])
        self.assertEqual({"pressure": "not-applicable"}, alternatives[1]["evidenceState"])
        self.assertEqual("exact", states["targetAlternatives"])
        self.assertEqual("exact", states["pressure"])
        self.assertEqual("exact", states["scoreRank"])
        self.assertEqual("exact", states["commandCorrelation"])
        self.assertEqual("inferred", states["outcome"])
        self.assertEqual("inferred", states["overall"])

    def test_weak_alternative_evidence_is_not_exact(self) -> None:
        pairs = dataset.normalized_raw_fields(
            {
                "targetAlternativeDenominator": "2",
                "targetAlternativeIds": "red|blue",
                "targetAlternativeFeatureEvidence": "allocatorComparableFeatures",
                "targetAlternativeFeatureMissingCount": "1",
                "targetAlternativeCountTruncated": "0",
            }
        )
        alternatives, _ = dataset.target_alternatives(pairs)

        self.assertEqual("inferred", dataset.alternative_evidence_state(pairs, alternatives))
        pairs["targetAlternativeCountTruncated"] = 1
        self.assertEqual("lower-bound", dataset.alternative_evidence_state(pairs, alternatives))

    def test_pressure_exact_requires_exact_bound_and_quality(self) -> None:
        pairs = {
            "boundedLivePressureDecision": "retained",
            "selectedTargetPriorMissileInFlightEstimateBound": "exact",
            "boundedLiveDecisionInFlightEvidenceQuality": "unknown",
        }

        self.assertEqual("inferred", dataset.pressure_evidence_state(pairs))
        pairs["boundedLiveDecisionInFlightEvidenceQuality"] = "exact"
        self.assertEqual("exact", dataset.pressure_evidence_state(pairs))


class ReplayClassificationTests(unittest.TestCase):
    def test_retained_above_threshold_classification_uses_exact_evidence(self) -> None:
        row = exact_retained_row()
        self.assertEqual("avoidable", replay.retained_above_threshold_classification(row))

        unavoidable = exact_retained_row()
        unavoidable["targetAlternatives"] = [unavoidable["targetAlternatives"][0]]
        self.assertEqual("unavoidable", replay.retained_above_threshold_classification(unavoidable))

        lower_bound = exact_retained_row()
        lower_bound["replayReadiness"]["hasExactPressure"] = False
        lower_bound["uncertainty"]["lowerBoundPressure"] = True
        lower_bound["evidenceState"]["pressure"] = "lower-bound"
        self.assertEqual("inconclusive", replay.retained_above_threshold_classification(lower_bound))

        unknown_alternatives = exact_retained_row()
        unknown_alternatives["evidenceState"]["targetAlternatives"] = "unknown"
        self.assertEqual("inconclusive", replay.retained_above_threshold_classification(unknown_alternatives))

    def test_report_only_policy_skips_known_friendly_alternatives(self) -> None:
        row = exact_retained_row()
        row["targetAlternatives"][1]["targetTeam"] = "player"
        row["targetAlternatives"][1]["score"] = 4.0

        current = replay.replay_policy(row, replay.CURRENT_POLICY_ID)
        candidate = replay.replay_policy(row, replay.REPORT_ONLY_POLICY_ID)
        summary = replay.summarize([current, candidate])
        policies = {policy["policyId"]: policy for policy in summary["policies"]}

        self.assertEqual([], current["rowEvaluation"]["candidateGuardrailFailures"])
        self.assertEqual([], candidate["rowEvaluation"]["candidateGuardrailFailures"])
        self.assertEqual("red", candidate["chosenTargetId"])
        self.assertEqual(0, policies[replay.CURRENT_POLICY_ID]["badCandidateRowCount"])
        self.assertEqual(0, policies[replay.REPORT_ONLY_POLICY_ID]["badCandidateRowCount"])

        unsafe_choice = row["targetAlternatives"][1]
        self.assertEqual(["candidate-friendly-target"], replay.candidate_guardrail_failures(row, unsafe_choice))

        bad_observed = exact_retained_row()
        bad_observed["command"]["result"] = "wouldFail"
        observed = replay.replay_policy(bad_observed, replay.CURRENT_POLICY_ID)
        self.assertEqual(["observed-command-result-wouldFail"], observed["rowEvaluation"]["observedRowFailures"])


class ReportVerdictTests(unittest.TestCase):
    def test_report_verdicts_preserve_row_counts_and_downgrades(self) -> None:
        row = exact_retained_row()
        records = [
            replay.replay_policy(row, replay.CURRENT_POLICY_ID),
            replay.replay_policy(row, replay.REPORT_ONLY_POLICY_ID),
        ]
        summary = replay.summarize(records)

        verdicts = report.build_verdicts(summary, records)
        by_policy = {item["policyId"]: item for item in verdicts["verdicts"]}
        report_only = by_policy[replay.REPORT_ONLY_POLICY_ID]

        self.assertEqual("inconclusive", report_only["verdict"])
        self.assertEqual(0, report_only["badCandidateRowCount"])
        self.assertEqual(1, report_only["candidateImprovementRowCount"])
        self.assertIn("fixture evidence only", report_only["downgradeReasons"])
        self.assertIn("Eligible", report.ranked_candidates_markdown(verdicts))
        self.assertIn("Bad observed rows", report.guardrail_markdown(verdicts))

    def test_fixture_pipeline_summaries_keep_expected_quality_counts(self) -> None:
        rows, warnings, run_modes, source_counts = dataset.build_dataset(FIXTURE_REGISTRY)
        dataset_summary = dataset.summarize_rows(rows, warnings, run_modes, source_counts)
        records = replay.replay(rows)
        replay_summary = replay.summarize(records)
        verdicts = report.build_verdicts(replay_summary, records)
        policies = {policy["policyId"]: policy for policy in replay_summary["policies"]}
        verdict_by_policy = {item["policyId"]: item for item in verdicts["verdicts"]}

        self.assertEqual(10, dataset_summary["rowCount"])
        self.assertEqual({"exact": 5, "lower-bound": 2, "not-applicable": 2, "unknown": 1}, dataset_summary["evidenceStateCounts"]["pressure"])
        self.assertEqual({"exact": 5, "lower-bound": 2, "not-applicable": 8, "unknown": 2}, dataset_summary["targetAlternativePressureEvidenceStateCounts"])
        self.assertEqual(20, replay_summary["recordCount"])
        self.assertEqual(0, policies[replay.REPORT_ONLY_POLICY_ID]["badCandidateRowCount"])
        self.assertEqual(1, policies[replay.REPORT_ONLY_POLICY_ID]["candidateImprovementRowCount"])
        self.assertEqual(0, policies[replay.REPORT_ONLY_POLICY_ID]["diagnosticSignalRowCount"])
        self.assertEqual(1, policies[replay.CURRENT_POLICY_ID]["diagnosticSignalRowCount"])
        self.assertEqual("inconclusive", verdict_by_policy[replay.CURRENT_POLICY_ID]["verdict"])
        self.assertEqual("inconclusive", verdict_by_policy[replay.REPORT_ONLY_POLICY_ID]["verdict"])


if __name__ == "__main__":
    unittest.main()
