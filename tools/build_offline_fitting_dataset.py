#!/usr/bin/env python3
"""Build allocation decision-context rows for offline fitting.

This command reads an experiment-corpus registry and emits row-level allocation
decision contexts for candidate replay. When registry entries include a
committed or local ``sourceLogPath``, the tool parses AllocationLog rows
directly so private raw logs do not need to be re-read by later replay phases.
Summary-only corpus entries are reported as evidence-limited and do not invent
row detail.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import shutil
from typing import Any

from import_player_log_experiments import LOG_RE, parse_pairs
from summarize_experiment_corpus import load_json_file, load_registry, repo_root, resolve_repo_path


DEFAULT_REGISTRY = Path("artifacts/experiments/registry.jsonl")
DEFAULT_OUTPUT = Path("artifacts/offline-fitting/dataset")
SCHEMA_VERSION = 1

RESULT_RECORD_TYPES = {
    "appliedDecision",
    "skippedDecision",
    "failedDecision",
    "fleetWideBoundedLiveResult",
}
CANDIDATE_RECORD_TYPES = {
    "dryRunCommandCandidate",
    "fleetWideBoundedLiveCandidate",
    "fleetWideCommandAuthorityCandidate",
}
DECISION_RECORD_TYPES = RESULT_RECORD_TYPES | CANDIDATE_RECORD_TYPES
NUMERIC_INT_FIELDS = {
    "assignedShots",
    "ammoGateBudgetShots",
    "pdScore",
    "saturationSize",
    "killSize",
    "selectedTargetRank",
    "selectedTargetRankTieCount",
    "targetAlternativeDenominator",
    "targetAlternativeCountTruncated",
    "targetAlternativeFeatureCount",
    "targetAlternativeFeatureMissingCount",
    "selectedTargetPriorControlledShots",
    "selectedTargetPriorMissileInFlightEstimate",
    "selectedTargetPriorMissileInFlightObserved",
    "selectedTargetPriorMissileInFlightUnknownTargetCount",
    "selectedTargetNewAssignedShots",
    "selectedTargetCumulativeAssignedShots",
    "selectedTargetSaturationSize",
    "selectedTargetKillSize",
    "globalCapRemaining",
    "perShipCapRemaining",
    "perTargetCapRemaining",
    "boundedLivePressureThreshold",
    "boundedLiveDecisionPressure",
    "boundedLiveDecisionPriorControlledShots",
    "boundedLiveDecisionExactInFlightShots",
    "boundedLiveDecisionLowerBoundInFlightShots",
    "boundedLiveDecisionTargetAlternativeDenominator",
    "appliedCommands",
    "failedCommands",
    "totalAppliedCommands",
    "globalCap",
    "perShipCap",
    "perTargetCap",
    "selectedShipCount",
    "visibleHostileTargets",
    "visibleTargetSourceCount",
}
NUMERIC_FLOAT_FIELDS = {
    "launchWindowScore",
    "scorePerShot",
    "selectedTargetScore",
    "targetValue",
    "boundedLiveSelectedTargetScore",
    "boundedLiveRetargetedTargetScore",
    "selectedTargetOverSaturationRatio",
    "selectedTargetKillOvercommitRatio",
}


def optional_int(value: Any) -> int | None:
    """Return an int for concrete values, otherwise None."""
    if value in (None, "", "unknown", "none"):
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def optional_float(value: Any) -> float | None:
    """Return a float for concrete values, otherwise None."""
    if value in (None, "", "unknown", "none"):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def typed_value(key: str, value: Any) -> Any:
    """Coerce known scalar diagnostic fields while preserving unknown text."""
    if key in NUMERIC_INT_FIELDS:
        parsed = optional_int(value)
        return parsed if parsed is not None else value
    if key in NUMERIC_FLOAT_FIELDS:
        parsed = optional_float(value)
        return parsed if parsed is not None else value
    if value in ("True", "False"):
        return value == "True"
    return value


def split_pipe(value: Any) -> list[str]:
    """Split pipe-delimited diagnostic list fields."""
    if value in (None, "", "unknown", "none"):
        return []
    return [part.strip() for part in str(value).split("|")]


def pipe_value(values: list[str], index: int) -> str | None:
    """Return an aligned pipe-list value if present."""
    return values[index] if index < len(values) and values[index] else None


def typed_pipe_value(values: list[str], index: int, kind: str) -> Any:
    """Return an aligned pipe-list value coerced to the requested type."""
    value = pipe_value(values, index)
    if kind == "int":
        return optional_int(value)
    if kind == "float":
        return optional_float(value)
    return value


def pressure_evidence_state(pairs: dict[str, Any]) -> str:
    """Classify pressure evidence quality."""
    if pairs.get("boundedLivePressureDecision") is None:
        return "not-applicable"
    bound = str(pairs.get("selectedTargetPriorMissileInFlightEstimateBound", "unknown"))
    quality = str(pairs.get("boundedLiveDecisionInFlightEvidenceQuality", "unknown"))
    if bound == "exact" and quality == "exact":
        return "exact"
    if bound == "lowerBound" or quality == "lowerBound":
        return "lower-bound"
    if bound == "exact" and quality == "unknown":
        return "inferred"
    return "unknown"


def list_warnings_for_alternatives(pairs: dict[str, Any], lengths: dict[str, int]) -> list[str]:
    """Return explicit warnings for malformed alternative pipe lists."""
    warnings: list[str] = []
    denominator = optional_int(pairs.get("targetAlternativeDenominator"))
    if denominator is not None:
        for name, length in lengths.items():
            if length not in (0, denominator):
                warnings.append(
                    f"{name} has {length} value(s), expected {denominator} from targetAlternativeDenominator"
                )
    return warnings


def target_alternatives(pairs: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Build normalized target alternatives from pipe-delimited diagnostics."""
    ids = split_pipe(pairs.get("targetAlternativeIds"))
    names = split_pipe(pairs.get("targetAlternativeNames"))
    teams = split_pipe(pairs.get("targetAlternativeTeams"))
    values = split_pipe(pairs.get("targetAlternativeValues"))
    pd_scores = split_pipe(pairs.get("targetAlternativePdScores"))
    saturation_sizes = split_pipe(pairs.get("targetAlternativeSaturationSizes"))
    kill_sizes = split_pipe(pairs.get("targetAlternativeKillSizes"))
    launch_scores = split_pipe(pairs.get("targetAlternativeLaunchWindowScores"))
    scores = split_pipe(pairs.get("targetAlternativeScores"))
    lengths = {
        "targetAlternativeIds": len(ids),
        "targetAlternativeNames": len(names),
        "targetAlternativeTeams": len(teams),
        "targetAlternativeValues": len(values),
        "targetAlternativePdScores": len(pd_scores),
        "targetAlternativeSaturationSizes": len(saturation_sizes),
        "targetAlternativeKillSizes": len(kill_sizes),
        "targetAlternativeLaunchWindowScores": len(launch_scores),
        "targetAlternativeScores": len(scores),
    }
    count = max([*lengths.values(), optional_int(pairs.get("targetAlternativeDenominator")) or 0])
    selected_id = pairs.get("targetId")
    pressure_target_id = pairs.get("boundedLiveOriginalTargetId") or selected_id
    threshold = optional_int(pairs.get("boundedLivePressureThreshold"))
    selected_pressure = optional_int(pairs.get("boundedLiveDecisionPressure"))
    row_pressure_state = pressure_evidence_state(pairs)
    alternatives: list[dict[str, Any]] = []
    for index in range(count):
        alternative_id = pipe_value(ids, index)
        is_selected = bool(alternative_id and selected_id and alternative_id == selected_id)
        is_pressure_target = bool(
            alternative_id and pressure_target_id and alternative_id == pressure_target_id
        )
        pressure = selected_pressure if is_pressure_target else None
        pressure_state = (
            row_pressure_state
            if is_pressure_target
            else "not-applicable"
            if pairs.get("boundedLivePressureDecision") is not None
            else "unknown"
        )
        pressure_reason = (
            "selected-pressure-target"
            if is_pressure_target
            else "not-pressure-target"
            if pairs.get("boundedLivePressureDecision") is not None
            else "pressure-decision-missing"
        )
        alternatives.append(
            {
                "targetId": alternative_id,
                "target": pipe_value(names, index),
                "targetTeam": pipe_value(teams, index),
                "isSelectedTarget": is_selected,
                "isPressureTarget": is_pressure_target,
                "targetValue": typed_pipe_value(values, index, "float"),
                "pdScore": typed_pipe_value(pd_scores, index, "int"),
                "saturationSize": typed_pipe_value(saturation_sizes, index, "int"),
                "killSize": typed_pipe_value(kill_sizes, index, "int"),
                "launchWindowScore": typed_pipe_value(launch_scores, index, "float"),
                "score": typed_pipe_value(scores, index, "float"),
                "scoreBasis": pairs.get("targetAlternativeScoreBasis"),
                "scoreSpace": pairs.get("targetAlternativeScoreSpace"),
                "pressure": pressure,
                "pressureEvidenceState": pressure_state,
                "pressureEvidenceReason": pressure_reason,
                "pressureThreshold": threshold,
                "underPressureThreshold": pressure < threshold if pressure is not None and threshold is not None else None,
                "evidenceState": {
                    "pressure": pressure_state,
                },
                "eligibilityReason": pairs.get("targetAlternativeEvidence", "unknown"),
            }
        )
    return alternatives, list_warnings_for_alternatives(pairs, lengths)


def normalized_raw_fields(pairs: dict[str, str]) -> dict[str, Any]:
    """Return raw diagnostic fields with conservative scalar coercion."""
    return {key: typed_value(key, value) for key, value in sorted(pairs.items())}


def known_missing_evidence(metadata: dict[str, Any]) -> list[str]:
    """Extract missing-evidence text from metadata without flattening proof modes."""
    values: list[str] = []
    raw = metadata.get("knownMissingEvidence")
    if isinstance(raw, list):
        values.extend(str(item) for item in raw)
    evidence_summary = metadata.get("evidenceSummary")
    if isinstance(evidence_summary, dict):
        missing = evidence_summary.get("missing_evidence_counts")
        if isinstance(missing, dict):
            values.extend(f"{key}: {value}" for key, value in sorted(missing.items()))
    return values


def parser_warning_fields(pairs: dict[str, Any], alternative_warnings: list[str]) -> list[str]:
    """Represent row-local uncertainty instead of silently discarding it."""
    warnings = list(alternative_warnings)
    if pairs.get("targetAlternativeDenominator") in (None, "unknown"):
        warnings.append("targetAlternativeDenominator missing or unknown")
    if pairs.get("selectedTargetPriorMissileInFlightEstimateBound") == "lowerBound":
        warnings.append("selected target prior missile pressure is lower-bound")
    if pairs.get("selectedTargetPriorMissileInFlightUnknownTargetCount") not in (None, "0", 0, "unknown"):
        warnings.append("observed live missiles include unknown target attribution")
    if pairs.get("controlledCommandCorrelation") in (None, "pendingRuntimeContext", "unknown"):
        warnings.append("direct runtime command correlation not confirmed on allocation row")
    return warnings


def pressure_audit(pairs: dict[str, Any], alternatives: list[dict[str, Any]]) -> dict[str, Any]:
    """Return pressure fields needed by replay and later conservative scoring."""
    threshold = optional_int(pairs.get("boundedLivePressureThreshold"))
    pressure = optional_int(pairs.get("boundedLiveDecisionPressure"))
    at_or_above = pairs.get("boundedLiveDecisionPressureAtOrAboveThreshold")
    if isinstance(at_or_above, str):
        at_or_above = at_or_above.lower() == "true"
    under_threshold_known = [
        alt for alt in alternatives if alt.get("underPressureThreshold") is True
    ]
    retained_above_threshold = (
        pairs.get("boundedLivePressureDecision") == "retained" and at_or_above is True
    )
    return {
        "decision": pairs.get("boundedLivePressureDecision", "unknown"),
        "decisionReason": pairs.get("boundedLivePressureDecisionReason", "unknown"),
        "reference": pairs.get("boundedLivePressureReference", "unknown"),
        "decisionPressure": pressure,
        "threshold": threshold,
        "atOrAboveThreshold": at_or_above,
        "priorControlledShots": optional_int(pairs.get("boundedLiveDecisionPriorControlledShots")),
        "exactInFlightShots": optional_int(pairs.get("boundedLiveDecisionExactInFlightShots")),
        "lowerBoundInFlightShots": optional_int(pairs.get("boundedLiveDecisionLowerBoundInFlightShots")),
        "inFlightEvidenceQuality": pairs.get("boundedLiveDecisionInFlightEvidenceQuality", "unknown"),
        "selectedTargetPriorEstimateBound": pairs.get(
            "selectedTargetPriorMissileInFlightEstimateBound", "unknown"
        ),
        "selectedTargetPriorTargetAttribution": pairs.get(
            "selectedTargetPriorMissileInFlightTargetAttribution", "unknown"
        ),
        "retainedAboveThreshold": retained_above_threshold,
        "underThresholdAlternativeCount": len(under_threshold_known),
        "noUnderThresholdAlternativeEvidence": (
            "noneFound"
            if retained_above_threshold and alternatives and not under_threshold_known
            else "hasUnderThresholdAlternative"
            if retained_above_threshold and under_threshold_known
            else "notApplicable"
        ),
    }


def alternative_evidence_state(pairs: dict[str, Any], alternatives: list[dict[str, Any]]) -> str:
    """Classify target-alternative evidence quality."""
    denominator = optional_int(pairs.get("targetAlternativeDenominator"))
    if denominator is None:
        return "unknown"
    if denominator == 0:
        return "not-applicable"
    if optional_int(pairs.get("targetAlternativeCountTruncated")) not in (None, 0):
        return "lower-bound"
    if not alternatives or len(alternatives) != denominator:
        return "unknown"
    if any(
        alternative.get("targetId") is None
        or alternative.get("targetTeam") is None
        or alternative.get("score") is None
        for alternative in alternatives
    ):
        return "unknown"
    feature_evidence = str(pairs.get("targetAlternativeFeatureEvidence", "unknown"))
    missing_count = optional_int(pairs.get("targetAlternativeFeatureMissingCount")) or 0
    if feature_evidence == "allocatorComparableFeatures" and missing_count == 0:
        return "exact"
    if feature_evidence in {"unknown", "none"}:
        return "unknown"
    return "inferred"


def score_rank_evidence_state(pairs: dict[str, Any]) -> str:
    """Classify score/rank comparison evidence quality."""
    if pairs.get("selectedTargetScore") is None and pairs.get("selectedTargetRank") is None:
        return "not-applicable"
    rank_confidence = str(pairs.get("selectedTargetRankConfidence", "unknown"))
    rank_space = str(pairs.get("selectedTargetRankComparisonSpace", "unknown"))
    rank_level = str(pairs.get("selectedTargetRankLevel", "unknown"))
    score_space = str(pairs.get("targetAlternativeScoreSpace", "unknown"))
    has_scores = pairs.get("targetAlternativeScores") not in (None, "unknown", "none", "")
    if (
        rank_confidence in {"exact", "tied"}
        and rank_space == "targetAlternativeScores"
        and rank_level == "target-level"
        and score_space != "unknown"
        and has_scores
    ):
        return "exact"
    if rank_confidence in {"partialAlternativeFeatures", "ambiguous"}:
        return "inferred"
    return "unknown"


def command_correlation_evidence_state(pairs: dict[str, Any], direct_launch_rows: int) -> str:
    """Classify direct command-result-to-launch evidence quality."""
    if direct_launch_rows > 0 or pairs.get("controlledCommandCorrelation") == "directRuntimeContext":
        return "exact"
    if pairs.get("controlledCommandCorrelation") in {"pendingRuntimeContext", "none"}:
        return "unknown"
    return "not-applicable"


def outcome_evidence_state(pairs: dict[str, Any]) -> str:
    """Classify outcome evidence quality for offline fitting."""
    attribution = str(pairs.get("targetOutcomeAttribution", "unknown"))
    confidence = str(pairs.get("attributionConfidence", "unknown"))
    if attribution == "evidenceLimited" or confidence == "outcomeCorrelationPending":
        return "inferred"
    if attribution in {"unknown", "none"}:
        return "not-applicable"
    return "inferred"


def overall_evidence_state(states: dict[str, str]) -> str:
    """Return the strongest conservative evidence-state label for a row."""
    relevant = [value for value in states.values() if value != "not-applicable"]
    if not relevant:
        return "not-applicable"
    for state in ("unknown", "lower-bound", "inferred"):
        if state in relevant:
            return state
    return "exact"


def evidence_state(
    pairs: dict[str, Any],
    alternatives: list[dict[str, Any]],
    direct_launch_rows: int,
) -> dict[str, str]:
    """Return explicit evidence states for replay and reporting."""
    states = {
        "targetAlternatives": alternative_evidence_state(pairs, alternatives),
        "pressure": pressure_evidence_state(pairs),
        "scoreRank": score_rank_evidence_state(pairs),
        "commandCorrelation": command_correlation_evidence_state(pairs, direct_launch_rows),
        "outcome": outcome_evidence_state(pairs),
    }
    states["overall"] = overall_evidence_state(states)
    return states


def build_decision_context(
    *,
    entry: dict[str, Any],
    metadata: dict[str, Any],
    pairs: dict[str, str],
    source_log: str,
    source_line: int,
    source_record_types: list[str],
    direct_launch_rows: int,
) -> dict[str, Any]:
    """Build one allocation decision-context row."""
    raw_fields = normalized_raw_fields(pairs)
    alternatives, alternative_warnings = target_alternatives(raw_fields)
    warnings = parser_warning_fields(raw_fields, alternative_warnings)
    missing = known_missing_evidence(metadata)
    states = evidence_state(raw_fields, alternatives, direct_launch_rows)
    command_result_id = raw_fields.get("commandResultId") or f"line-{source_line}"
    row_id = f"{entry.get('experimentId', 'unknown')}:{command_result_id}"
    return {
        "schemaVersion": SCHEMA_VERSION,
        "rowType": "allocationDecisionContext",
        "rowId": row_id,
        "source": {
            "registryExperimentId": entry.get("experimentId"),
            "sourceExperimentId": raw_fields.get("experimentId"),
            "sourceLogPath": source_log,
            "sourceLine": source_line,
            "sourceRecordTypes": source_record_types,
        },
        "run": {
            "runMode": entry.get("runMode"),
            "heuristicCandidateId": entry.get("heuristicCandidateId"),
            "modCommit": entry.get("modCommit"),
            "parameterSnapshotHash": entry.get("parameterSnapshotHash"),
            "scenarioTags": entry.get("scenarioTags", []),
            "registryVerdict": entry.get("verdict"),
            "selectedMode": metadata.get("selectedMode", "unknown"),
        },
        "launcher": {
            "launcherId": raw_fields.get("launcherId") or raw_fields.get("allocatorLauncherId"),
            "launcher": raw_fields.get("launcher") or raw_fields.get("allocatorLauncher"),
            "launcherTeam": raw_fields.get("launcherTeam") or raw_fields.get("allocatorLauncherTeam"),
            "launcherSelectionRelation": raw_fields.get("launcherSelectionRelation", "unknown"),
            "selectionEvidenceLimit": raw_fields.get("selectionEvidenceLimit", "unknown"),
            "selectedScopeSource": raw_fields.get("selectedScopeSource", "unknown"),
            "selectedShipCount": raw_fields.get("selectedShipCount", "unknown"),
            "ammoGateBudgetShots": raw_fields.get("ammoGateBudgetShots"),
        },
        "selectedTarget": {
            "targetId": raw_fields.get("targetId"),
            "target": raw_fields.get("target"),
            "targetTeam": raw_fields.get("targetTeam"),
            "assignedShots": raw_fields.get("assignedShots"),
            "targetValue": raw_fields.get("targetValue"),
            "pdScore": raw_fields.get("pdScore"),
            "saturationSize": raw_fields.get("saturationSize"),
            "killSize": raw_fields.get("killSize"),
            "launchWindowScore": raw_fields.get("launchWindowScore"),
            "score": (
                raw_fields.get("selectedTargetScore")
                if raw_fields.get("selectedTargetScore") is not None
                else raw_fields.get("scorePerShot")
            ),
            "scoreBasis": raw_fields.get("selectedTargetScoreBasis"),
            "scoreSpace": raw_fields.get("selectedTargetScoreSpace"),
            "rank": raw_fields.get("selectedTargetRank"),
            "rankBasis": raw_fields.get("selectedTargetRankBasis"),
            "rankComparisonSpace": raw_fields.get("selectedTargetRankComparisonSpace"),
            "rankLevel": raw_fields.get("selectedTargetRankLevel"),
            "rankConfidence": raw_fields.get("selectedTargetRankConfidence"),
            "rankTieCount": raw_fields.get("selectedTargetRankTieCount"),
            "originalTargetId": raw_fields.get("boundedLiveOriginalTargetId"),
            "originalTarget": raw_fields.get("boundedLiveOriginalTarget"),
            "retargetedToTargetId": raw_fields.get("boundedLiveRetargetedToTargetId"),
            "retargetedToTarget": raw_fields.get("boundedLiveRetargetedToTarget"),
        },
        "targetAlternatives": alternatives,
        "pressure": pressure_audit(raw_fields, alternatives),
        "evidenceState": states,
        "command": {
            "commandResultId": raw_fields.get("commandResultId"),
            "candidateId": raw_fields.get("candidateId"),
            "candidateSource": raw_fields.get("candidateSource", "unknown"),
            "result": raw_fields.get("result") or raw_fields.get("classification", "unknown"),
            "reason": raw_fields.get("reason", "unknown"),
            "exceptionType": raw_fields.get("exceptionType", "none"),
            "capReason": raw_fields.get("capReason", "unknown"),
            "controlledCommandCorrelation": raw_fields.get("controlledCommandCorrelation", "unknown"),
            "directRuntimeContextLaunchRows": direct_launch_rows,
            "appliedCommands": raw_fields.get("appliedCommands"),
            "failedCommands": raw_fields.get("failedCommands"),
            "globalCap": raw_fields.get("globalCap"),
            "perShipCap": raw_fields.get("perShipCap"),
            "perTargetCap": raw_fields.get("perTargetCap"),
            "globalCapRemaining": raw_fields.get("globalCapRemaining"),
            "perShipCapRemaining": raw_fields.get("perShipCapRemaining"),
            "perTargetCapRemaining": raw_fields.get("perTargetCapRemaining"),
            "preLauncherPrimaryTargetId": raw_fields.get("preLauncherPrimaryTargetId"),
            "postLauncherPrimaryTargetId": raw_fields.get("postLauncherPrimaryTargetId"),
            "postState": raw_fields.get("postState"),
        },
        "uncertainty": {
            "parserWarnings": warnings,
            "knownMissingEvidence": missing,
            "targetOutcomeAttribution": raw_fields.get("targetOutcomeAttribution", "unknown"),
            "attributionConfidence": raw_fields.get("attributionConfidence", "unknown"),
            "spilloverClassification": "notJoined",
            "lowerBoundPressure": raw_fields.get("selectedTargetPriorMissileInFlightEstimateBound")
            == "lowerBound",
            "missingAlternatives": not alternatives,
        },
        "replayReadiness": {
            "hasSelectedTarget": bool(raw_fields.get("targetId")),
            "hasTargetAlternatives": bool(alternatives),
            "hasSelectedTargetScoreRank": raw_fields.get("selectedTargetRank") is not None
            and raw_fields.get("selectedTargetScore") is not None,
            "hasPressureDecision": raw_fields.get("boundedLivePressureDecision") is not None,
            "hasExactPressure": states["pressure"] == "exact",
            "hasLowerBoundPressure": raw_fields.get("selectedTargetPriorMissileInFlightEstimateBound")
            == "lowerBound",
            "hasExactTargetAlternatives": states["targetAlternatives"] == "exact",
            "hasExactScoreRank": states["scoreRank"] == "exact",
            "hasCommandResult": raw_fields.get("result") is not None
            or raw_fields.get("classification") is not None,
        },
        "rawFields": raw_fields,
    }


def parse_source_log(
    *,
    entry: dict[str, Any],
    metadata: dict[str, Any],
    source_path: Path,
    source_log_text: str,
    warnings: list[str],
) -> list[dict[str, Any]]:
    """Parse one source log into decision-context rows."""
    groups: dict[str, list[tuple[int, str, dict[str, str]]]] = defaultdict(list)
    launch_counts: Counter[str] = Counter()
    with source_path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            match = LOG_RE.search(line)
            if not match:
                continue
            pairs = parse_pairs(match.group("pairs"))
            kind = match.group("kind")
            if kind == "LaunchLog":
                command_result_id = pairs.get("commandResultId")
                if command_result_id and pairs.get("controlledCommandCorrelation") == "directRuntimeContext":
                    launch_counts[command_result_id] += 1
                continue
            record_type = pairs.get("recordType")
            if record_type not in DECISION_RECORD_TYPES:
                continue
            command_result_id = pairs.get("commandResultId") or f"line-{line_number}"
            groups[command_result_id].append((line_number, record_type, pairs))

    contexts: list[dict[str, Any]] = []
    for command_result_id, records in sorted(groups.items()):
        merged: dict[str, str] = {}
        selected_line = records[-1][0]
        selected_record_types: list[str] = []
        for line_number, record_type, pairs in records:
            selected_record_types.append(record_type)
            merged.update(pairs)
            if record_type in RESULT_RECORD_TYPES:
                selected_line = line_number
        contexts.append(
            build_decision_context(
                entry=entry,
                metadata=metadata,
                pairs=merged,
                source_log=source_log_text,
                source_line=selected_line,
                source_record_types=selected_record_types,
                direct_launch_rows=launch_counts[command_result_id],
            )
        )
    if not contexts:
        warnings.append(f"{entry.get('experimentId')}: no decision-context AllocationLog rows in {source_log_text}")
    return contexts


def build_dataset(registry_path: Path) -> tuple[list[dict[str, Any]], list[str], Counter[str], Counter[str]]:
    """Build all context rows from a registry."""
    entries, warnings = load_registry(registry_path)
    rows: list[dict[str, Any]] = []
    run_mode_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    for entry in entries:
        run_mode_counts[str(entry.get("runMode", "unknown"))] += 1
        metadata = load_json_file(
            entry.get("metadataPath"),
            warnings,
            f"{entry.get('experimentId', 'unknown')}: metadataPath",
        )
        source_log = entry.get("sourceLogPath")
        if not source_log:
            source_counts["summaryOnlyEntries"] += 1
            warnings.append(
                f"{entry.get('experimentId', 'unknown')}: sourceLogPath omitted; row-level contexts unavailable"
            )
            continue
        source_path = resolve_repo_path(str(source_log))
        if source_path is None or not source_path.exists():
            source_counts["missingSourceLogs"] += 1
            warnings.append(f"{entry.get('experimentId', 'unknown')}: source log not found: {source_log}")
            continue
        source_counts["sourceLogsRead"] += 1
        rows.extend(
            parse_source_log(
                entry=entry,
                metadata=metadata,
                source_path=source_path,
                source_log_text=str(source_log),
                warnings=warnings,
            )
        )
    return rows, warnings, run_mode_counts, source_counts


def summarize_rows(
    rows: list[dict[str, Any]],
    warnings: list[str],
    run_mode_counts: Counter[str],
    source_counts: Counter[str],
) -> dict[str, Any]:
    """Build a deterministic dataset health summary."""
    record_types: Counter[str] = Counter()
    command_results: Counter[str] = Counter()
    pressure_decisions: Counter[str] = Counter()
    evidence_states: dict[str, Counter[str]] = defaultdict(Counter)
    alternative_pressure_states: Counter[str] = Counter()
    for row in rows:
        for record_type in row["source"]["sourceRecordTypes"]:
            record_types[record_type] += 1
        command_results[str(row["command"].get("result", "unknown"))] += 1
        pressure_decisions[str(row["pressure"].get("decision", "unknown"))] += 1
        for key, value in row.get("evidenceState", {}).items():
            evidence_states[key][str(value)] += 1
        for alternative in row.get("targetAlternatives", []):
            alternative_pressure_states[str(alternative.get("pressureEvidenceState", "unknown"))] += 1
    return {
        "schemaVersion": SCHEMA_VERSION,
        "datasetKind": "allocation-decision-context",
        "rowCount": len(rows),
        "registryRunModeCounts": dict(sorted(run_mode_counts.items())),
        "sourceCounts": dict(sorted(source_counts.items())),
        "sourceRecordTypeCounts": dict(sorted(record_types.items())),
        "commandResultCounts": dict(sorted(command_results.items())),
        "pressureDecisionCounts": dict(sorted(pressure_decisions.items())),
        "rowsWithTargetAlternatives": sum(1 for row in rows if row["replayReadiness"]["hasTargetAlternatives"]),
        "rowsWithPressureDecision": sum(1 for row in rows if row["replayReadiness"]["hasPressureDecision"]),
        "rowsWithExactPressure": sum(1 for row in rows if row["replayReadiness"]["hasExactPressure"]),
        "rowsWithLowerBoundPressure": sum(1 for row in rows if row["replayReadiness"]["hasLowerBoundPressure"]),
        "rowsWithCommandResult": sum(1 for row in rows if row["replayReadiness"]["hasCommandResult"]),
        "rowsWithParserWarnings": sum(1 for row in rows if row["uncertainty"]["parserWarnings"]),
        "evidenceStateCounts": {
            key: dict(sorted(counter.items())) for key, counter in sorted(evidence_states.items())
        },
        "targetAlternativePressureEvidenceStateCounts": dict(sorted(alternative_pressure_states.items())),
        "warnings": warnings,
    }


def ensure_safe_output(output_path: Path, *, force: bool) -> None:
    """Prepare an output directory without deleting arbitrary repo paths."""
    resolved = output_path.resolve()
    if resolved.exists():
        if not resolved.is_dir():
            raise SystemExit(f"Output path exists and is not a directory: {output_path}")
        if not force:
            raise SystemExit(f"Output already exists: {output_path} (use --force)")
        artifacts_root = (repo_root() / "artifacts").resolve()
        try:
            resolved.relative_to(artifacts_root)
        except ValueError as exc:
            raise SystemExit(
                f"Refusing to clear output directory outside {artifacts_root}: {output_path}"
            ) from exc
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], output_path: Path) -> None:
    """Write JSONL, JSON, and summary artifacts."""
    (output_path / "decision-contexts.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    (output_path / "decision-contexts.json").write_text(
        json.dumps(
            {
                "schemaVersion": SCHEMA_VERSION,
                "datasetKind": "allocation-decision-context",
                "rows": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_path / "dataset-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def enforce_fixture_gate(summary: dict[str, Any]) -> None:
    """Fail validation when committed fixtures do not exercise required evidence."""
    failures: list[str] = []
    if summary["rowCount"] <= 0:
        failures.append("no decision-context rows emitted")
    if summary["rowsWithTargetAlternatives"] <= 0:
        failures.append("no rows preserve target alternatives")
    if summary["rowsWithPressureDecision"] <= 0:
        failures.append("no rows preserve bounded-live pressure decisions")
    if summary["rowsWithLowerBoundPressure"] <= 0:
        failures.append("no rows preserve lower-bound pressure uncertainty")
    if summary["rowsWithCommandResult"] <= 0:
        failures.append("no rows preserve command results")
    if not summary.get("targetAlternativePressureEvidenceStateCounts"):
        failures.append("no per-target-alternative pressure evidence states emitted")
    if failures:
        raise SystemExit("Dataset fixture gate failed: " + "; ".join(failures))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true", help="overwrite an existing artifacts output directory")
    parser.add_argument(
        "--require-row-evidence",
        action="store_true",
        help="fail if fixture rows do not include alternatives, pressure, uncertainty, and command results",
    )
    return parser.parse_args()


def main() -> None:
    """Command entry point."""
    args = parse_args()
    rows, warnings, run_mode_counts, source_counts = build_dataset(args.registry)
    summary = summarize_rows(rows, warnings, run_mode_counts, source_counts)
    if args.require_row_evidence:
        enforce_fixture_gate(summary)
    ensure_safe_output(args.output, force=args.force)
    write_outputs(rows, summary, args.output)
    print(f"Loaded registry: {args.registry}")
    print(f"Decision-context rows: {summary['rowCount']}")
    print(f"Rows with alternatives: {summary['rowsWithTargetAlternatives']}")
    print(f"Rows with lower-bound pressure: {summary['rowsWithLowerBoundPressure']}")
    print(f"Wrote dataset to {args.output}")


if __name__ == "__main__":
    main()
