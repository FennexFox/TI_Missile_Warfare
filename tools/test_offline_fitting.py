#!/usr/bin/env python3
"""Regression tests for offline-fitting evidence and report semantics."""
from __future__ import annotations

import sys
import tempfile
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
                "targetAlternativeTeams": "enemy|enemy",
                "targetAlternativeScores": "3.0|2.0",
                "targetAlternativeFeatureEvidence": "allocatorComparableFeatures",
                "targetAlternativeFeatureMissingCount": "1",
                "targetAlternativeCountTruncated": "0",
            }
        )
        alternatives, _ = dataset.target_alternatives(pairs)

        self.assertEqual("inferred", dataset.alternative_evidence_state(pairs, alternatives))
        pairs["targetAlternativeCountTruncated"] = 1
        self.assertEqual("lower-bound", dataset.alternative_evidence_state(pairs, alternatives))

    def test_malformed_alternative_rows_are_not_exact_evidence(self) -> None:
        pairs = dataset.normalized_raw_fields(
            {
                "targetAlternativeDenominator": "2",
                "targetAlternativeIds": "red|blue",
                "targetAlternativeTeams": "enemy|enemy",
                "targetAlternativeScores": "3.0",
                "targetAlternativeFeatureEvidence": "allocatorComparableFeatures",
                "targetAlternativeFeatureMissingCount": "0",
                "targetAlternativeCountTruncated": "0",
            }
        )
        alternatives, _ = dataset.target_alternatives(pairs)

        self.assertIsNone(alternatives[1]["score"])
        self.assertEqual("unknown", dataset.alternative_evidence_state(pairs, alternatives))

    def test_selected_target_score_preserves_explicit_zero(self) -> None:
        row = dataset.build_decision_context(
            entry={"experimentId": "EXP-ZERO-SCORE"},
            metadata={},
            pairs={
                "commandResultId": "cmd-zero",
                "targetId": "red",
                "target": "Red",
                "targetTeam": "enemy",
                "selectedTargetScore": "0.0",
                "scorePerShot": "9.0",
            },
            source_log="fixture.txt",
            source_line=1,
            source_record_types=["fleetWideBoundedLiveCandidate"],
            direct_launch_rows=0,
        )

        self.assertEqual(0.0, row["selectedTarget"]["score"])

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

    def test_current_policy_no_change_score_delta_is_zero_across_score_spaces(self) -> None:
        row = exact_retained_row()
        row["selectedTarget"]["score"] = 3.0
        row["selectedTarget"]["scoreSpace"] = "launcherCandidateAllocation"
        row["targetAlternatives"][0]["score"] = 1.0
        row["targetAlternatives"][0]["scoreSpace"] = "diagnosticTargetAlternativeRecomputed"
        row["targetAlternatives"][1]["score"] = 2.0
        row["targetAlternatives"][1]["scoreSpace"] = "diagnosticTargetAlternativeRecomputed"

        current = replay.replay_policy(row, replay.CURRENT_POLICY_ID)
        report_only = replay.replay_policy(row, replay.REPORT_ONLY_POLICY_ID)
        summary = replay.summarize([current, report_only])
        policies = {policy["policyId"]: policy for policy in summary["policies"]}

        self.assertFalse(current["rowEvaluation"]["targetChanged"])
        self.assertEqual(0.0, current["rowEvaluation"]["scoreDelta"])
        self.assertEqual("no-target-change", current["rowEvaluation"]["scoreDeltaKind"])
        self.assertEqual(0.0, current["objectiveMetrics"]["highScoreCoveragePenalty"])
        self.assertEqual(0.0, policies[replay.CURRENT_POLICY_ID]["scoreDeltaTotalEligible"])
        self.assertIsNone(policies[replay.CURRENT_POLICY_ID]["changedScoreDeltaAverageEligible"])

        self.assertTrue(report_only["rowEvaluation"]["targetChanged"])
        self.assertEqual(1.0, report_only["rowEvaluation"]["scoreDelta"])
        self.assertEqual("changed-target-comparable", report_only["rowEvaluation"]["scoreDeltaKind"])
        self.assertEqual(
            "diagnosticTargetAlternativeRecomputed",
            report_only["rowEvaluation"]["scoreDeltaScoreSpace"],
        )
        self.assertEqual(1.0, policies[replay.REPORT_ONLY_POLICY_ID]["changedScoreDeltaTotalEligible"])

    def test_report_only_changed_target_mismatched_score_space_is_not_comparable(self) -> None:
        row = exact_retained_row()
        row["targetAlternatives"][0]["score"] = 1.0
        row["targetAlternatives"][0]["scoreSpace"] = "diagnosticTargetAlternativeRecomputed"
        row["targetAlternatives"][1]["score"] = 2.0
        row["targetAlternatives"][1]["scoreSpace"] = "someOtherSpace"

        report_only = replay.replay_policy(row, replay.REPORT_ONLY_POLICY_ID)
        evaluation = report_only["rowEvaluation"]

        self.assertTrue(evaluation["targetChanged"])
        self.assertIsNone(evaluation["scoreDelta"])
        self.assertEqual("not-comparable", evaluation["scoreDeltaKind"])
        self.assertTrue(evaluation["scoreDeltaReason"].startswith("score-space-mismatch"))
        self.assertEqual(0.0, report_only["objectiveMetrics"]["highScoreCoveragePenalty"])

    def test_bad_row_counts_count_rows_not_failure_instances(self) -> None:
        row = exact_retained_row()
        row["selectedTarget"]["targetTeam"] = "player"
        row["command"]["result"] = "wouldFail"

        current = replay.replay_policy(row, replay.CURRENT_POLICY_ID)
        summary = replay.summarize([current])
        policy = summary["policies"][0]

        self.assertEqual(["observed-friendly-target", "observed-command-result-wouldFail"], current["hardGuardrailFailures"])
        self.assertEqual(1, policy["badObservedRowCount"])
        self.assertEqual(2, policy["hardGuardrailFailureCount"])


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
        self.assertEqual("n/a", report.markdown_cell(None))

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


class ToolHardeningTests(unittest.TestCase):
    def test_parse_source_log_tolerates_invalid_utf8_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Player.log"
            source.write_bytes(
                b'\xff[MissileWarfare] [MFC] [AllocationLog] recordType="fleetWideBoundedLiveCandidate" '
                b'commandResultId="cmd-invalid-utf8" targetId="red" target="Red"\n'
            )
            warnings: list[str] = []

            rows = dataset.parse_source_log(
                entry={"experimentId": "EXP-INVALID-UTF8"},
                metadata={},
                source_path=source,
                source_log_text="Player.log",
                warnings=warnings,
            )

            self.assertEqual(1, len(rows))
            self.assertEqual([], warnings)

    def test_ensure_safe_output_refuses_non_directories_and_external_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_file = root / "output-file"
            output_file.write_text("not a directory", encoding="utf-8")
            external_dir = root / "artifacts" / "outside"
            external_dir.mkdir(parents=True)

            for module in (dataset, replay, report):
                with self.assertRaises(SystemExit):
                    module.ensure_safe_output(output_file, force=True)
                with self.assertRaises(SystemExit):
                    module.ensure_safe_output(external_dir, force=True)

            self.assertTrue(output_file.exists())
            self.assertTrue(external_dir.exists())

    def test_report_loaders_emit_clear_json_parse_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_json = root / "bad.json"
            bad_json.write_text("{not-json", encoding="utf-8")
            bad_jsonl = root / "bad.jsonl"
            bad_jsonl.write_text('{"ok": true}\n{not-json}\n', encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "invalid JSON"):
                report.load_json(bad_json)
            with self.assertRaisesRegex(SystemExit, r"bad\.jsonl:2: invalid JSONL row"):
                report.load_jsonl(bad_jsonl)


if __name__ == "__main__":
    unittest.main()
