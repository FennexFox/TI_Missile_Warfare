#!/usr/bin/env python3
"""Import Player.log diagnostics into experiment-corpus artifact drafts.

This tool groups AllocationLog/LaunchLog rows by experimentId and writes one
corpus artifact directory per experiment. It also performs best-effort battle
segmentation before any same-cycle context attachment, so cycle ids can later be
interpreted in a battle-local namespace instead of as Player.log-global ids.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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
BOUNDED_LIVE_APPLIED_FIELD_KEYS = (
    "experimentId",
    "battleSegmentId",
    "cycleId",
    "commandResultId",
    "candidateId",
    "launcherId",
    "launcher",
    "launcherTeam",
    "allocatorLauncherId",
    "allocatorLauncher",
    "allocatorLauncherTeam",
    "targetId",
    "target",
    "targetTeam",
    "assignedShots",
    "ammoGateBudgetShots",
    "targetValue",
    "pdScore",
    "saturationSize",
    "killSize",
    "launchWindowScore",
    "selectedTargetScore",
    "selectedTargetScoreBasis",
    "selectedTargetScoreSpace",
    "selectedTargetRank",
    "selectedTargetRankBasis",
    "selectedTargetRankComparisonSpace",
    "selectedTargetRankLevel",
    "selectedTargetRankConfidence",
    "selectedTargetRankTieCount",
    "candidateSource",
    "allocatorEvidence",
    "visibleTargetSource",
    "visibleTargetConfidence",
    "visibleTargetSourceCount",
    "visibleHostileTargets",
    "targetAlternativeDenominator",
    "targetAlternativeEvidence",
    "targetAlternativeIds",
    "targetAlternativeNames",
    "targetAlternativeTeams",
    "targetAlternativeCountTruncated",
    "targetAlternativeFeatureEvidence",
    "targetAlternativeFeatureCount",
    "targetAlternativeFeatureMissingCount",
    "targetAlternativeValues",
    "targetAlternativePdScores",
    "targetAlternativeSaturationSizes",
    "targetAlternativeKillSizes",
    "targetAlternativeLaunchWindowScores",
    "targetAlternativeScores",
    "targetAlternativeScoreBasis",
    "targetAlternativeScoreSpace",
    "selectedTargetPriorControlledShots",
    "selectedTargetPriorAllocatorShots",
    "selectedTargetPriorVanillaShotsKnown",
    "selectedTargetPriorVanillaShotsNearWindow",
    "selectedTargetPriorMissileInFlightEstimate",
    "selectedTargetPriorMissileInFlightEstimateSource",
    "selectedTargetPriorMissileInFlightEstimateConfidence",
    "selectedTargetPriorMissileInFlightEstimateBound",
    "selectedTargetPriorMissileInFlightTargetAttribution",
    "selectedTargetPriorMissileInFlightObserved",
    "selectedTargetPriorMissileInFlightUnknownTargetCount",
    "selectedTargetPriorKnownShotPressure",
    "selectedTargetNewAssignedShots",
    "selectedTargetCumulativeAssignedShots",
    "selectedTargetSaturationSize",
    "selectedTargetKillSize",
    "selectedTargetOverSaturationRatio",
    "selectedTargetKillOvercommitRatio",
    "targetSurvivedAfterControlledWindow",
    "targetDestroyedAfterControlledWindow",
    "timeToImpactWindowKnown",
    "targetOutcomeAttribution",
    "attributionConfidence",
    "globalCapRemaining",
    "perShipCapRemaining",
    "perTargetCapRemaining",
    "blockedCandidateLauncherId",
    "blockedCandidateTargetId",
    "blockedCandidateScore",
    "appliedCandidateScore",
    "wouldHaveAppliedRankWithoutCap",
    "blockedCandidateWasBetterThanApplied",
    "boundedLivePressureDecision",
    "boundedLivePressureDecisionReason",
    "boundedLivePressureReference",
    "boundedLivePressureThreshold",
    "boundedLiveDecisionPressure",
    "boundedLiveDecisionPressureAtOrAboveThreshold",
    "boundedLiveDecisionPriorControlledShots",
    "boundedLiveDecisionExactInFlightShots",
    "boundedLiveDecisionLowerBoundInFlightShots",
    "boundedLiveDecisionInFlightEvidenceQuality",
    "boundedLiveOriginalTargetId",
    "boundedLiveOriginalTarget",
    "boundedLiveRetargetedToTargetId",
    "boundedLiveRetargetedToTarget",
    "boundedLiveSelectedTargetScore",
    "boundedLiveRetargetedTargetScore",
    "boundedLiveDecisionTargetAlternativeDenominator",
)
BOUNDED_LIVE_TUNING_READINESS_COUNTER_KEYS = (
    "boundedLiveAppliedResults",
    "boundedLiveAppliedWithTargetAlternativeDenominator",
    "boundedLiveAppliedWithTargetAlternativeDenominatorGtOne",
    "boundedLiveAppliedWithUnknownTargetAlternativeDenominator",
    "boundedLiveAppliedWithComparableAlternativeFeatures",
    "boundedLiveAppliedWithPartialAlternativeFeatures",
    "boundedLiveAppliedWithSelectedTargetRank",
    "boundedLiveAppliedWithPriorInFlightEstimate",
    "boundedLiveAppliedWithFullyComparableScoreRankEvidence",
    "boundedLiveAppliedWithPartialOrAmbiguousScoreSpaceEvidence",
    "boundedLiveAppliedWithKnownPriorInFlightPressure",
    "boundedLiveAppliedWithLowerBoundPriorInFlightPressure",
    "sameTargetPackagesWithDenominatorOne",
    "sameTargetPackagesWithDenominatorGtOne",
    "sameTargetPackagesWithUnknownDenominator",
    "boundedLiveRetainedSelectedTargetDecisionsAboveThreshold",
    "boundedLiveRetargetedDecisionsAboveThreshold",
    "boundedLivePressureDecisionExactInFlightRows",
    "boundedLivePressureDecisionLowerBoundInFlightRows",
    "boundedLivePressureDecisionUnknownInFlightRows",
    "boundedLiveLowerBoundPressureDiagnosticOnlyRows",
    "potentialOverConcentrationCandidates",
    "potentialUnderSaturationCandidates",
    "potentialCapMisallocationCandidates",
    "targetValueMismatchCandidates",
    "evidenceLimitedResults",
    "hardMeasurementBlockedResults",
    "externalOutcomeBlockedResults",
)


@dataclass
class BattleSegment:
    """Best-effort Player.log combat/battle segment."""

    battle_id: str
    start_line: int
    last_observed_line: int
    boundary_source: str
    first_ship_create_line: int | None = None
    end_trigger_line: int | None = None
    combat_will_end_line: int | None = None
    label: str | None = None

    def contains(self, line_number: int) -> bool:
        """Return whether a source line is inside this segment."""
        return self.start_line <= line_number <= self.last_observed_line

    def to_json(self) -> dict[str, Any]:
        """Return JSON metadata for this segment."""
        return {
            "sourceBattleId": self.battle_id,
            "battleStartLine": self.start_line,
            "battleFirstShipCreateLine": self.first_ship_create_line,
            "battleEndTriggerLine": self.end_trigger_line,
            "battleCombatWillEndLine": self.combat_will_end_line,
            "battleLastObservedLine": self.last_observed_line,
            "battleBoundarySource": self.boundary_source,
            "battleLabel": self.label,
        }


@dataclass
class LogRow:
    """One parsed diagnostics row from a Player.log file."""

    line_number: int
    kind: str
    pairs: dict[str, str]
    battle_segment_id: str | None = None


@dataclass
class ExperimentGroup:
    """Rows that belong to one diagnostics experiment id."""

    source_experiment_id: str
    rows: list[LogRow] = field(default_factory=list)
    battle_segment: BattleSegment | None = None
    battle_segment_ids: set[str] = field(default_factory=set)
    battle_segments_by_id: dict[str, BattleSegment] = field(default_factory=dict)
    nearby_cycle_context_rows: list[LogRow] = field(default_factory=list)

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


def concrete_experiment_id(experiment_id: str | None) -> str | None:
    """Return a concrete experiment id, excluding placeholder values."""
    if not experiment_id:
        return None
    experiment_id = experiment_id.strip()
    if experiment_id in {"", "none", "unknown"}:
        return None
    return experiment_id


def is_battle_start_marker(line: str) -> bool:
    """Return whether a raw Player.log line looks like combat setup started."""
    return (
        "Init Canvas SpaceCombatCanvas" in line
        or "Adding ship to CombatManager as ActiveShip(CreateShip)" in line
        or "MaxShipsInCombat" in line
    )


def is_ship_create_marker(line: str) -> bool:
    """Return whether a raw Player.log line adds an active ship to combat."""
    return "Adding ship to CombatManager as ActiveShip(CreateShip)" in line


def is_battle_end_marker(line: str) -> bool:
    """Return whether a raw Player.log line looks like combat end scheduling."""
    return "FLTS: Combat End Triggered" in line or "Combat Will End" in line


def finalized_segment(segment: BattleSegment, last_line: int) -> BattleSegment:
    """Return a segment with a nonzero last observed line."""
    if segment.last_observed_line < segment.start_line:
        segment.last_observed_line = last_line
    return segment


def detect_vanilla_battle_segments(path: Path) -> tuple[list[BattleSegment], int]:
    """Detect battle segments from vanilla combat lifecycle markers."""
    segments: list[BattleSegment] = []
    current: BattleSegment | None = None
    last_line = 0
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            last_line = line_number
            if is_battle_start_marker(line):
                if current is None:
                    current = BattleSegment(
                        battle_id=f"BATTLE-{len(segments) + 1:04d}",
                        start_line=line_number,
                        last_observed_line=line_number,
                        boundary_source="vanilla-combat-manager-log",
                    )
                elif current.end_trigger_line is not None and line_number > current.last_observed_line:
                    segments.append(finalized_segment(current, line_number - 1))
                    current = BattleSegment(
                        battle_id=f"BATTLE-{len(segments) + 1:04d}",
                        start_line=line_number,
                        last_observed_line=line_number,
                        boundary_source="vanilla-combat-manager-log",
                    )
                current.last_observed_line = line_number
                if is_ship_create_marker(line) and current.first_ship_create_line is None:
                    current.first_ship_create_line = line_number
                continue

            if current is not None:
                current.last_observed_line = line_number
                if is_ship_create_marker(line) and current.first_ship_create_line is None:
                    current.first_ship_create_line = line_number
                if "FLTS: Combat End Triggered" in line and current.end_trigger_line is None:
                    current.end_trigger_line = line_number
                if "Combat Will End" in line:
                    current.combat_will_end_line = line_number

    if current is not None:
        segments.append(finalized_segment(current, last_line))
    return segments, last_line


def detect_cycle_battle_field_segments(path: Path, last_line: int) -> list[BattleSegment]:
    """Fallback segments from AllocationLog cycle rows with a battle field."""
    markers: list[tuple[int, str]] = []
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            match = LOG_RE.search(line)
            if not match or match.group("kind") != "AllocationLog":
                continue
            pairs = parse_pairs(match.group("pairs"))
            if pairs.get("recordType") != "cycle":
                continue
            battle_label = pairs.get("battle")
            if battle_label and battle_label not in {"none", "unknown"}:
                if not markers or markers[-1][1] != battle_label:
                    markers.append((line_number, battle_label))

    if not markers:
        return []

    segments: list[BattleSegment] = []
    for index, (line_number, label) in enumerate(markers):
        next_line = markers[index + 1][0] if index + 1 < len(markers) else last_line + 1
        segments.append(
            BattleSegment(
                battle_id=f"BATTLE-{index + 1:04d}",
                start_line=line_number,
                last_observed_line=max(line_number, next_line - 1),
                boundary_source="allocation-cycle-battle-field",
                label=label,
            )
        )
    return segments


def detect_battle_segments(path: Path) -> list[BattleSegment]:
    """Detect battle segments with conservative fallback markers."""
    vanilla_segments, last_line = detect_vanilla_battle_segments(path)
    if vanilla_segments:
        return vanilla_segments
    return detect_cycle_battle_field_segments(path, last_line)


def battle_for_line(segments: list[BattleSegment], line_number: int) -> BattleSegment | None:
    """Return the detected battle segment containing a source line."""
    for segment in segments:
        if segment.contains(line_number):
            return segment
    return None


def row_battle_segment_ids(rows: list[LogRow]) -> list[str]:
    """Return sorted concrete battle segment ids for rows."""
    return sorted({row.battle_segment_id for row in rows if row.battle_segment_id})


def primary_battle_segment_id(group: ExperimentGroup) -> str | None:
    """Return the primary battle segment id for a group, preferring allocation rows."""
    allocation_counter = Counter(
        row.battle_segment_id for row in group.allocation_rows if row.battle_segment_id
    )
    if allocation_counter:
        return allocation_counter.most_common(1)[0][0]
    row_counter = Counter(row.battle_segment_id for row in group.rows if row.battle_segment_id)
    if row_counter:
        return row_counter.most_common(1)[0][0]
    return None


def battle_context_for_group(group: ExperimentGroup) -> dict[str, Any]:
    """Return battle context metadata for one experiment group."""
    segment_ids = sorted(group.battle_segment_ids)
    primary_segment_id = primary_battle_segment_id(group)
    primary_segment = (
        group.battle_segments_by_id.get(primary_segment_id) if primary_segment_id else None
    ) or group.battle_segment
    if primary_segment is None:
        return {
            "sourceBattleId": "unknown",
            "primaryBattleSegmentId": "unknown",
            "allocationBattleSegmentIds": row_battle_segment_ids(group.allocation_rows),
            "launchBattleSegmentIds": row_battle_segment_ids(group.launch_rows),
            "battleSegmentIds": segment_ids,
            "battleSegmentConfidence": "not-detected",
            "battleBoundarySource": "not-detected",
        }
    context = primary_segment.to_json()
    context["primaryBattleSegmentId"] = primary_segment.battle_id
    context["allocationBattleSegmentIds"] = row_battle_segment_ids(group.allocation_rows)
    context["launchBattleSegmentIds"] = row_battle_segment_ids(group.launch_rows)
    context["battleSegmentIds"] = segment_ids
    context["battleSegmentConfidence"] = (
        "single-detected-segment" if len(segment_ids) <= 1 else "multiple-detected-segments"
    )
    return context


def battle_missing_evidence(group: ExperimentGroup) -> list[str]:
    """Return battle-boundary evidence limitations for one experiment group."""
    allocation_ids = row_battle_segment_ids(group.allocation_rows)
    launch_ids = row_battle_segment_ids(group.launch_rows)
    if not allocation_ids and not launch_ids:
        return ["battle boundary not detected by Player.log importer"]
    missing: list[str] = []
    if len(allocation_ids) > 1:
        missing.append("allocation rows span multiple detected battle segments")
    if len(launch_ids) > 1:
        missing.append("launch runtime context spans multiple detected battle segments")
    return missing


def unique_preserving_order(values: list[str]) -> list[str]:
    """Return unique values while preserving first-seen order."""
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def parse_log_groups(
    path: Path,
    filters: set[str] | None = None,
    battle_segments: list[BattleSegment] | None = None,
) -> dict[str, ExperimentGroup]:
    """Parse a Player.log and group AllocationLog/LaunchLog rows by experiment id."""
    segments = battle_segments or []
    groups: dict[str, ExperimentGroup] = {}
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            match = LOG_RE.search(line)
            if not match:
                continue
            pairs = parse_pairs(match.group("pairs"))
            experiment_id = concrete_experiment_id(pairs.get("experimentId"))
            if not experiment_id and match.group("kind") == "LaunchLog":
                experiment_id = concrete_experiment_id(
                    experiment_from_command_result(pairs.get("commandResultId"))
                )
            if not experiment_id:
                continue
            if filters and experiment_id not in filters:
                continue
            segment = battle_for_line(segments, line_number)
            group = groups.setdefault(experiment_id, ExperimentGroup(experiment_id))
            group.rows.append(
                LogRow(
                    line_number,
                    match.group("kind"),
                    pairs,
                    segment.battle_id if segment is not None else None,
                )
            )
            if segment is not None:
                group.battle_segment_ids.add(segment.battle_id)
                group.battle_segments_by_id[segment.battle_id] = segment
                if group.battle_segment is None:
                    group.battle_segment = segment
    return groups


def collect_cycle_context_rows(
    path: Path,
    battle_segments: list[BattleSegment],
) -> dict[tuple[str, str], list[LogRow]]:
    """Collect AllocationLog cycle context rows by (battle id, cycle id)."""
    cycle_rows: dict[tuple[str, str], list[LogRow]] = {}
    if not battle_segments:
        return cycle_rows
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            match = LOG_RE.search(line)
            if not match or match.group("kind") != "AllocationLog":
                continue
            pairs = parse_pairs(match.group("pairs"))
            if pairs.get("recordType") != "cycle":
                continue
            cycle_id = pairs.get("cycleId")
            if not cycle_id or cycle_id in {"none", "unknown"}:
                continue
            segment = battle_for_line(battle_segments, line_number)
            if segment is None:
                continue
            cycle_rows.setdefault((segment.battle_id, cycle_id), []).append(
                LogRow(line_number, match.group("kind"), pairs, segment.battle_id)
            )
    return cycle_rows


def line_distance_to_group(row: LogRow, group: ExperimentGroup) -> int:
    """Return line distance from a context row to an experiment group span."""
    line_numbers = [experiment_row.line_number for experiment_row in group.rows]
    if not line_numbers:
        return 0
    first_line = min(line_numbers)
    last_line = max(line_numbers)
    if first_line <= row.line_number <= last_line:
        return 0
    return min(abs(row.line_number - first_line), abs(row.line_number - last_line))


def attach_cycle_context_rows(
    groups: dict[str, ExperimentGroup],
    cycle_context_rows: dict[tuple[str, str], list[LogRow]],
    *,
    line_window: int,
) -> None:
    """Attach same-battle same-cycle context rows to experiment groups."""
    for group in groups.values():
        attached: dict[int, LogRow] = {}
        for experiment_row in group.allocation_rows:
            battle_id = experiment_row.battle_segment_id
            cycle_id = experiment_row.pairs.get("cycleId")
            if not battle_id or not cycle_id or cycle_id in {"none", "unknown"}:
                continue
            for row in cycle_context_rows.get((battle_id, cycle_id), []):
                if line_distance_to_group(row, group) <= line_window:
                    attached[row.line_number] = row
        group.nearby_cycle_context_rows = [attached[key] for key in sorted(attached)]


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


def optional_int(value: Any) -> int | None:
    """Parse an integer diagnostics value, preserving unknown as None."""
    try:
        if value in (None, "", "none", "unknown"):
            return None
        return int(str(value))
    except ValueError:
        return None


def optional_float(value: Any) -> float | None:
    """Parse a float diagnostics value, preserving unknown as None."""
    try:
        if value in (None, "", "none", "unknown"):
            return None
        return float(str(value))
    except ValueError:
        return None


def has_concrete_value(value: Any) -> bool:
    """Return whether a diagnostics value is present and not an explicit unknown."""
    return value not in (None, "", "none", "unknown")


def has_cap_blocked_vs_applied_comparison(pairs: dict[str, str]) -> bool:
    """Return whether a cap-skipped bounded-live row has comparison evidence."""
    return (
        has_concrete_value(pairs.get("blockedCandidateScore"))
        and has_concrete_value(pairs.get("appliedCandidateScore"))
        and pairs.get("blockedCandidateWasBetterThanApplied") in {"True", "False"}
    )


def first_non_empty(values: list[str | None], default: str = "unknown") -> str:
    """Return the first concrete diagnostics value."""
    for value in values:
        if value and value not in {"none", "unknown"}:
            return value
    return default


def pd_category_for_group(group: ExperimentGroup) -> tuple[str, str]:
    """Return PD evidence category and provenance for an experiment group."""
    direct_category = first_non_empty(
        [row.pairs.get("pdEvidenceQuality") for row in group.allocation_rows]
        + [row.pairs.get("pdEvidenceCategory") for row in group.allocation_rows],
        default="unknown",
    )
    if direct_category != "unknown":
        return direct_category, "experiment-row"

    cycle_category = first_non_empty(
        [row.pairs.get("pdEvidenceQuality") for row in group.nearby_cycle_context_rows]
        + [row.pairs.get("pdEvidenceCategory") for row in group.nearby_cycle_context_rows],
        default="unknown",
    )
    if cycle_category != "unknown":
        return cycle_category, "same-battle-same-cycle-context"
    return "unknown", "not-attached"


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
        cap_skip_rows = [
            row for row in result_rows
            if row.pairs.get("result") == "skipped"
            and "CapBlocked" in row.pairs.get("reason", "")
        ]
        cap_skip_with_comparison = sum(
            1 for row in cap_skip_rows
            if has_cap_blocked_vs_applied_comparison(row.pairs)
        )
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
                "fleet_wide_bounded_live_cap_skip_records": len(cap_skip_rows),
                "fleet_wide_bounded_live_cap_skip_with_blocked_applied_comparison": cap_skip_with_comparison,
                "fleet_wide_bounded_live_cap_skip_missing_blocked_applied_comparison": (
                    len(cap_skip_rows) - cap_skip_with_comparison
                ),
                "fleet_wide_bounded_live_pressure_decision_counts": counter_dict(
                    Counter(row.pairs.get("boundedLivePressureDecision", "unknown") for row in bounded_rows)
                ),
                "fleet_wide_bounded_live_pressure_decision_reason_counts": counter_dict(
                    Counter(row.pairs.get("boundedLivePressureDecisionReason", "unknown") for row in bounded_rows)
                ),
                "fleet_wide_bounded_live_pressure_evidence_counts": counter_dict(
                    Counter(row.pairs.get("boundedLiveDecisionInFlightEvidenceQuality", "unknown") for row in bounded_rows)
                ),
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
        command = {
            "cycleId": int_value(row.pairs.get("cycleId"), default=-1),
            "battleSegmentId": row.battle_segment_id or "unknown",
            "launcher": row.pairs.get("launcher", "unknown"),
            "launcherId": row.pairs.get("launcherId", "unknown"),
            "target": row.pairs.get("target", "unknown"),
            "targetId": row.pairs.get("targetId", "unknown"),
            "assignedShots": int_value(row.pairs.get("assignedShots")),
            "commandResultId": command_result_id,
            "directRuntimeContextRows": direct_by_command.get(command_result_id, 0),
        }
        if record_type == "fleetWideBoundedLiveResult":
            for key in BOUNDED_LIVE_APPLIED_FIELD_KEYS:
                if key == "battleSegmentId":
                    command[key] = row.battle_segment_id or "unknown"
                elif key == "cycleId":
                    command[key] = int_value(row.pairs.get(key), default=-1)
                elif key in {"assignedShots", "ammoGateBudgetShots", "targetAlternativeDenominator", "visibleHostileTargets", "visibleTargetSourceCount", "targetAlternativeCountTruncated", "targetAlternativeFeatureCount", "targetAlternativeFeatureMissingCount", "selectedTargetRank", "selectedTargetRankTieCount", "selectedTargetPriorControlledShots", "selectedTargetPriorVanillaShotsNearWindow", "selectedTargetPriorMissileInFlightEstimate", "selectedTargetPriorMissileInFlightObserved", "selectedTargetPriorMissileInFlightUnknownTargetCount", "selectedTargetPriorKnownShotPressure", "selectedTargetNewAssignedShots", "selectedTargetCumulativeAssignedShots", "selectedTargetSaturationSize", "selectedTargetKillSize", "globalCapRemaining", "perShipCapRemaining", "perTargetCapRemaining", "boundedLivePressureThreshold", "boundedLiveDecisionPressure", "boundedLiveDecisionPriorControlledShots", "boundedLiveDecisionExactInFlightShots", "boundedLiveDecisionLowerBoundInFlightShots", "boundedLiveDecisionTargetAlternativeDenominator"}:
                    value = optional_int(row.pairs.get(key))
                    command[key] = value if value is not None else "unknown"
                else:
                    command[key] = row.pairs.get(key, "unknown")
            add_bounded_live_launch_pressure(command, row, group.launch_rows)
        commands.append(command)
    return commands


def launch_target_matches(row: LogRow, target_id: Any) -> bool:
    """Return whether a launch row references a target id/state id."""
    if not has_concrete_value(target_id):
        return False
    target_text = str(target_id)
    return target_text in {
        row.pairs.get("targetId"),
        row.pairs.get("targetStateId"),
    }


def add_bounded_live_launch_pressure(
    command: dict[str, Any],
    result_row: LogRow,
    launch_rows: list[LogRow],
) -> None:
    """Add best-effort launch pressure fields from imported launch rows."""
    target_id = command.get("targetId")
    same_segment_launch_rows = [
        row for row in launch_rows
        if row.battle_segment_id == result_row.battle_segment_id
    ]
    non_correlated_same_target = [
        row for row in same_segment_launch_rows
        if row.pairs.get("controlledCommandCorrelation", "missing") in {"none", "missing"}
        and launch_target_matches(row, target_id)
    ]
    prior_non_correlated = [
        row for row in non_correlated_same_target
        if row.line_number < result_row.line_number
    ]
    direct_rows = int_value(command.get("directRuntimeContextRows"))
    assigned = int_value(command.get("assignedShots"))
    prior_controlled = int_value(command.get("selectedTargetPriorControlledShots"))
    command["actualLaunchRows"] = direct_rows
    command["missileSpendConfirmed"] = "True" if assigned > 0 and direct_rows == assigned else "False"
    command["nonCorrelatedLaunchRowsNearWindow"] = len(non_correlated_same_target)
    command["vanillaSpilloverRowsNearTarget"] = len(non_correlated_same_target)
    if same_segment_launch_rows:
        command["selectedTargetPriorVanillaShotsKnown"] = "True"
        command["selectedTargetPriorVanillaShotsNearWindow"] = len(prior_non_correlated)
        command["selectedTargetPriorKnownShotPressure"] = prior_controlled + len(prior_non_correlated)
    else:
        command.setdefault("selectedTargetPriorVanillaShotsKnown", "unknown")
        command.setdefault("selectedTargetPriorVanillaShotsNearWindow", "unknown")
        if not has_concrete_value(command.get("selectedTargetPriorKnownShotPressure")):
            command["selectedTargetPriorKnownShotPressure"] = "unknown"
    if not has_concrete_value(command.get("selectedTargetPriorMissileInFlightEstimate")):
        command["selectedTargetPriorMissileInFlightEstimate"] = "unknown"


def denominator_bucket(command: dict[str, Any]) -> str:
    """Return denominator quality bucket for a bounded-live applied command."""
    value = command.get("targetAlternativeDenominator")
    denominator = value if isinstance(value, int) else optional_int(value)
    if denominator is None:
        return "unknown"
    if denominator > 1:
        return "gtOne"
    return "one"


def score_rank_evidence_bucket(command: dict[str, Any]) -> str:
    """Classify whether score/rank evidence has an unambiguous comparison space."""
    feature_evidence = str(command.get("targetAlternativeFeatureEvidence", "unknown"))
    rank_confidence = str(command.get("selectedTargetRankConfidence", "unknown"))
    selected_space = str(command.get("selectedTargetScoreSpace", "unknown"))
    alternative_space = str(command.get("targetAlternativeScoreSpace", "unknown"))
    rank_space = str(command.get("selectedTargetRankComparisonSpace", "unknown"))
    rank_level = str(command.get("selectedTargetRankLevel", "unknown"))

    if not has_concrete_value(command.get("selectedTargetScore")):
        return "unavailable"
    if not has_concrete_value(command.get("targetAlternativeScores")):
        return "unavailable"
    if not has_concrete_value(command.get("selectedTargetRank")):
        return "unavailable"
    if "unknown" in {selected_space, alternative_space, rank_space, rank_level}:
        return "ambiguousScoreSpace"
    if feature_evidence != "allocatorComparableFeatures":
        return "partialAlternativeFeatures"
    if rank_confidence != "exact":
        return "ambiguousRank"
    if rank_space != "targetAlternativeScores" or rank_level != "target-level":
        return "ambiguousScoreSpace"
    return "fullyComparable"


def in_flight_pressure_bucket(command: dict[str, Any]) -> str:
    """Classify pre-command in-flight pressure as exact, lower-bound, or unavailable."""
    if not has_concrete_value(command.get("selectedTargetPriorMissileInFlightEstimate")):
        return "unavailable"

    bound = str(command.get("selectedTargetPriorMissileInFlightEstimateBound", "unknown"))
    if bound == "exact":
        return "fullyKnown"
    if bound == "lowerBound":
        return "lowerBound"

    confidence = str(
        command.get("selectedTargetPriorMissileInFlightEstimateConfidence", "unknown")
    )
    observed = optional_int(command.get("selectedTargetPriorMissileInFlightObserved")) or 0
    unknown_targets = optional_int(
        command.get("selectedTargetPriorMissileInFlightUnknownTargetCount")
    ) or 0
    if observed > 0 and unknown_targets > 0:
        return "lowerBound"
    if unknown_targets == 0 and confidence in {
        "noLiveMissilesObserved",
        "targetIdsRecoveredFromLiveMissiles",
    }:
        return "fullyKnown"
    if confidence == "partialTargetIdsRecoveredFromLiveMissiles":
        return "lowerBound"
    return "unavailable"


def bounded_live_tuning_readiness(
    commands: list[dict[str, Any]],
    allocation_summary: dict[str, Any],
) -> dict[str, Any]:
    """Return conservative #43.4 readiness counters from applied bounded-live commands."""
    bounded = [
        command for command in commands
        if str(command.get("commandResultId", "")).startswith("fleetwide-bounded-live-")
    ]
    counters: Counter[str] = Counter()
    for key in BOUNDED_LIVE_TUNING_READINESS_COUNTER_KEYS:
        counters[key] = 0
    hard_blockers: Counter[str] = Counter()
    external_blockers: Counter[str] = Counter()
    evidence_limited_commands = 0
    hard_blocked_commands = 0
    external_blocked_commands = 0
    target_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    counters["boundedLiveAppliedResults"] = len(bounded)
    for command in bounded:
        command_hard_blocked = False
        command_external_blocked = False
        target_groups[str(command.get("targetId", "unknown"))].append(command)
        denominator = optional_int(command.get("targetAlternativeDenominator"))
        if denominator is None:
            counters["boundedLiveAppliedWithUnknownTargetAlternativeDenominator"] += 1
            hard_blockers["missing targetAlternativeDenominator"] += 1
            command_hard_blocked = True
        else:
            counters["boundedLiveAppliedWithTargetAlternativeDenominator"] += 1
            if denominator > 1:
                counters["boundedLiveAppliedWithTargetAlternativeDenominatorGtOne"] += 1

        feature_evidence = str(command.get("targetAlternativeFeatureEvidence", "unknown"))
        if feature_evidence == "allocatorComparableFeatures":
            counters["boundedLiveAppliedWithComparableAlternativeFeatures"] += 1
        elif feature_evidence == "partialAllocatorComparableFeatures":
            counters["boundedLiveAppliedWithPartialAlternativeFeatures"] += 1

        if has_concrete_value(command.get("selectedTargetRank")):
            counters["boundedLiveAppliedWithSelectedTargetRank"] += 1

        score_rank_bucket = score_rank_evidence_bucket(command)
        if score_rank_bucket == "fullyComparable":
            counters["boundedLiveAppliedWithFullyComparableScoreRankEvidence"] += 1
        elif score_rank_bucket != "unavailable":
            counters["boundedLiveAppliedWithPartialOrAmbiguousScoreSpaceEvidence"] += 1

        in_flight_bucket = in_flight_pressure_bucket(command)
        if in_flight_bucket in {"fullyKnown", "lowerBound"}:
            counters["boundedLiveAppliedWithPriorInFlightEstimate"] += 1
        if in_flight_bucket == "fullyKnown":
            counters["boundedLiveAppliedWithKnownPriorInFlightPressure"] += 1
        elif in_flight_bucket == "lowerBound":
            counters["boundedLiveAppliedWithLowerBoundPriorInFlightPressure"] += 1

        pressure_decision = str(command.get("boundedLivePressureDecision", "unknown"))
        pressure_above_threshold = (
            str(command.get("boundedLiveDecisionPressureAtOrAboveThreshold", "unknown")).lower()
            == "true"
        )
        if pressure_above_threshold:
            if pressure_decision == "retargeted":
                counters["boundedLiveRetargetedDecisionsAboveThreshold"] += 1
            elif pressure_decision == "retained":
                counters["boundedLiveRetainedSelectedTargetDecisionsAboveThreshold"] += 1

        decision_in_flight_quality = str(
            command.get("boundedLiveDecisionInFlightEvidenceQuality", "unknown")
        )
        if decision_in_flight_quality == "exact":
            counters["boundedLivePressureDecisionExactInFlightRows"] += 1
        elif decision_in_flight_quality == "lowerBound":
            counters["boundedLivePressureDecisionLowerBoundInFlightRows"] += 1
            counters["boundedLiveLowerBoundPressureDiagnosticOnlyRows"] += 1
        else:
            counters["boundedLivePressureDecisionUnknownInFlightRows"] += 1

        for required in (
            "experimentId",
            "battleSegmentId",
            "cycleId",
            "commandResultId",
            "launcherId",
            "targetId",
            "assignedShots",
            "directRuntimeContextRows",
        ):
            if not has_concrete_value(command.get(required)):
                hard_blockers[f"missing {required}"] += 1
                command_hard_blocked = True

        if not has_concrete_value(command.get("visibleHostileTargets")):
            hard_blockers["missing visibleHostileTargets"] += 1
            command_hard_blocked = True
        if not has_concrete_value(command.get("targetValue")):
            hard_blockers["missing targetValue"] += 1
            command_hard_blocked = True
        if not has_concrete_value(command.get("pdScore")):
            hard_blockers["missing pdScore"] += 1
            command_hard_blocked = True
        if not has_concrete_value(command.get("selectedTargetScore")):
            hard_blockers["selected target score unavailable"] += 1
            command_hard_blocked = True
        elif score_rank_bucket == "ambiguousScoreSpace":
            hard_blockers["score/rank comparison-space semantics ambiguous"] += 1
            command_hard_blocked = True
        if not has_concrete_value(command.get("selectedTargetRank")):
            hard_blockers["selected target rank unavailable because scores are unavailable"] += 1
            command_hard_blocked = True
        elif command.get("selectedTargetRankConfidence") == "tied":
            hard_blockers["selected target rank unavailable because of ties"] += 1
            command_hard_blocked = True
        elif command.get("selectedTargetRankConfidence") == "partialAlternativeFeatures":
            hard_blockers["selected target rank based on partial alternative features"] += 1
            command_hard_blocked = True
        if not has_concrete_value(command.get("saturationSize")) and not has_concrete_value(command.get("killSize")):
            hard_blockers["saturation/kill-size evidence unknown"] += 1
            command_hard_blocked = True
        if command.get("targetAlternativeCountTruncated") == "unknown":
            hard_blockers["target identity comparison evidence-limited"] += 1
            command_hard_blocked = True
        if optional_int(command.get("targetAlternativeCountTruncated")) not in (None, 0):
            hard_blockers["target alternative identity list truncated"] += 1
            command_hard_blocked = True
        if feature_evidence == "partialAllocatorComparableFeatures":
            hard_blockers["alternative target comparable features partially available"] += 1
            command_hard_blocked = True
        elif feature_evidence != "allocatorComparableFeatures":
            hard_blockers["alternative target comparable score/features unavailable"] += 1
            command_hard_blocked = True
        if command.get("selectedTargetPriorVanillaShotsKnown") != "True":
            hard_blockers["prior vanilla/none-correlated shot pressure unknown"] += 1
            command_hard_blocked = True
        if not has_concrete_value(command.get("selectedTargetPriorKnownShotPressure")):
            hard_blockers["prior known target shot pressure unavailable"] += 1
            command_hard_blocked = True
        if in_flight_bucket == "unavailable":
            hard_blockers[
                "prior in-flight estimate unavailable because target ownership/source cannot be recovered"
            ] += 1
            command_hard_blocked = True
        elif in_flight_bucket == "lowerBound":
            observed = optional_int(command.get("selectedTargetPriorMissileInFlightObserved")) or 0
            unknown_targets = optional_int(
                command.get("selectedTargetPriorMissileInFlightUnknownTargetCount")
            ) or 0
            if observed > 0 and unknown_targets >= observed:
                hard_blockers[
                    "prior in-flight target attribution unavailable for observed live missiles"
                ] += 1
            else:
                hard_blockers[
                    "prior in-flight estimate lower-bound because some live missile targets are unknown"
                ] += 1
            command_hard_blocked = True
        if command.get("targetOutcomeAttribution") in {None, "", "unknown", "evidenceLimited"}:
            external_blockers["exact outcome attribution pending #47"] += 1
            command_external_blocked = True
        if optional_int(command.get("vanillaSpilloverRowsNearTarget")) not in (None, 0):
            external_blockers["vanilla spillover / selected-ship distribution pending #48"] += 1
            command_external_blocked = True
        if command_hard_blocked or command_external_blocked:
            evidence_limited_commands += 1
        if command_hard_blocked:
            hard_blocked_commands += 1
        if command_external_blocked:
            external_blocked_commands += 1

    for target_commands in target_groups.values():
        if len(target_commands) < 2:
            continue
        buckets = {denominator_bucket(command) for command in target_commands}
        if "gtOne" in buckets:
            counters["sameTargetPackagesWithDenominatorGtOne"] += 1
        elif "unknown" in buckets:
            counters["sameTargetPackagesWithUnknownDenominator"] += 1
        else:
            counters["sameTargetPackagesWithDenominatorOne"] += 1

        if "gtOne" in buckets:
            over_ratio = max(
                (optional_float(command.get("selectedTargetOverSaturationRatio")) or 0.0)
                for command in target_commands
            )
            kill_ratio = max(
                (optional_float(command.get("selectedTargetKillOvercommitRatio")) or 0.0)
                for command in target_commands
            )
            if over_ratio > 1.0 or kill_ratio > 1.0:
                counters["potentialOverConcentrationCandidates"] += 1

    counters["potentialUnderSaturationCandidates"] = 0
    counters["potentialCapMisallocationCandidates"] = 0
    counters["targetValueMismatchCandidates"] = 0
    counters["evidenceLimitedResults"] = evidence_limited_commands
    counters["hardMeasurementBlockedResults"] = hard_blocked_commands
    counters["externalOutcomeBlockedResults"] = external_blocked_commands

    bounded_reasons = allocation_summary.get("fleet_wide_bounded_live_reason_counts")
    if isinstance(bounded_reasons, dict):
        cap_skip_count = sum(
            value for reason, value in bounded_reasons.items()
            if isinstance(value, int) and "CapBlocked" in str(reason)
        )
        missing_cap_comparison = allocation_summary.get(
            "fleet_wide_bounded_live_cap_skip_missing_blocked_applied_comparison"
        )
        if not isinstance(missing_cap_comparison, int):
            missing_cap_comparison = cap_skip_count
        if missing_cap_comparison:
            hard_blockers[
                "cap blocked-vs-applied comparison required for cap skips"
            ] += missing_cap_comparison

    return {
        "counters": counter_dict(counters),
        "hardMeasurementBlockers": counter_dict(hard_blockers),
        "externalOutcomeBlockers": counter_dict(external_blockers),
        "blockers": counter_dict(hard_blockers + external_blockers),
        "interpretation": "measurement-only; hard blockers must be resolved inside #43.4 before closing, while external blockers may hand off to #47/#48",
    }


def cycle_context_to_json(row: LogRow) -> dict[str, Any]:
    """Return a compact JSON representation of an attached cycle context row."""
    keys = (
        "cycleId",
        "battle",
        "sourceHook",
        "friendlyLaunchers",
        "targetCount",
        "totalAmmoGateBudgetShots",
        "pdWeight",
        "pdEvidenceQuality",
        "pdEvidenceCategory",
        "pdCapabilityEvidenceSource",
        "pdCapabilityWeaponCount",
        "pdCapabilityRangeKm",
        "pdCapabilityCooldownSeconds",
        "pdCapabilityObservedFields",
        "pdCapabilityMissingReason",
        "pdCapabilityLimitations",
        "missingInputs",
    )
    result: dict[str, Any] = {
        "lineNumber": row.line_number,
        "battleSegmentId": row.battle_segment_id,
        "attachmentConfidence": "same-battle-same-cycle",
    }
    for key in keys:
        value = row.pairs.get(key)
        if value and value not in {"none", "unknown"}:
            result[key] = value
    return result


def nearby_context_for_group(group: ExperimentGroup) -> dict[str, Any]:
    """Return attached nearby context rows for an experiment group."""
    if not group.nearby_cycle_context_rows:
        return {}
    return {
        "allocationCycleRows": [
            cycle_context_to_json(row) for row in group.nearby_cycle_context_rows
        ]
    }


def row_segment_id(row: LogRow) -> str:
    """Return a stable segment id bucket for one row."""
    return row.battle_segment_id or "unassigned"


def segment_count_dict(counter: Counter[str]) -> dict[str, int]:
    """Return deterministic segment count mapping."""
    return dict(sorted(counter.items(), key=lambda item: (item[0] == "unassigned", item[0])))


def nested_segment_counter_dict(counters: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    """Return deterministic nested counters keyed by battle segment id."""
    return {segment: counter_dict(counters[segment]) for segment in sorted(counters)}


def battle_segment_breakdown_for_group(group: ExperimentGroup) -> dict[str, Any]:
    """Return row-kind and allocation-record breakdowns by detected battle segment."""
    row_counts: dict[str, Counter[str]] = defaultdict(Counter)
    allocation_counts: Counter[str] = Counter()
    launch_counts: Counter[str] = Counter()
    allocation_record_counts: dict[str, Counter[str]] = defaultdict(Counter)
    allocation_result_counts: dict[str, Counter[str]] = defaultdict(Counter)
    allocation_reason_counts: dict[str, Counter[str]] = defaultdict(Counter)
    applied_command_counts: Counter[str] = Counter()
    skipped_command_counts: dict[str, Counter[str]] = defaultdict(Counter)
    line_ranges: dict[str, dict[str, int]] = {}

    for row in group.rows:
        segment = row_segment_id(row)
        row_counts[segment][row.kind] += 1
        if segment not in line_ranges:
            line_ranges[segment] = {"firstLine": row.line_number, "lastLine": row.line_number}
        else:
            line_ranges[segment]["firstLine"] = min(
                line_ranges[segment]["firstLine"], row.line_number
            )
            line_ranges[segment]["lastLine"] = max(
                line_ranges[segment]["lastLine"], row.line_number
            )

        if row.kind == "AllocationLog":
            allocation_counts[segment] += 1
            record_type = row.pairs.get("recordType", "unknown")
            allocation_record_counts[segment][record_type] += 1
            result = row.pairs.get("result")
            if result and result not in {"none", "unknown"}:
                allocation_result_counts[segment][result] += 1
                if result == "applied":
                    applied_command_counts[segment] += 1
                if result == "skipped":
                    reason = row.pairs.get("reason", "unknown")
                    skipped_command_counts[segment][reason] += 1
            reason = row.pairs.get("reason")
            if reason and reason not in {"none", "unknown"}:
                allocation_reason_counts[segment][reason] += 1
        elif row.kind == "LaunchLog":
            launch_counts[segment] += 1

    return {
        "rowCountsByBattleSegment": nested_segment_counter_dict(row_counts),
        "allocationRowsByBattleSegment": segment_count_dict(allocation_counts),
        "launchRowsByBattleSegment": segment_count_dict(launch_counts),
        "allocationRecordTypeCountsByBattleSegment": nested_segment_counter_dict(
            allocation_record_counts
        ),
        "allocationResultCountsByBattleSegment": nested_segment_counter_dict(
            allocation_result_counts
        ),
        "allocationReasonCountsByBattleSegment": nested_segment_counter_dict(
            allocation_reason_counts
        ),
        "appliedCommandCountsByBattleSegment": segment_count_dict(applied_command_counts),
        "skippedCommandReasonCountsByBattleSegment": nested_segment_counter_dict(
            skipped_command_counts
        ),
        "lineRangesByBattleSegment": dict(sorted(line_ranges.items())),
    }


def build_summary(group: ExperimentGroup, log_path: Path, *, fixture: bool, include_source: bool) -> dict[str, Any]:
    """Build parsed summary artifact for one experiment group."""
    allocation_summary = summarize_allocation(group)
    launch_summary, direct_by_command, none_or_missing_by_target = summarize_launches(group)
    command_summary = applied_commands(group, direct_by_command)
    readiness_summary = bounded_live_tuning_readiness(command_summary, allocation_summary)
    direct_launches = launch_summary.get("directRuntimeContext", 0)
    limitation_counts: dict[str, int] = {}
    if not include_source:
        limitation_counts["source Player.log path omitted from registry"] = 1
    if direct_launches == 0 and group.launch_rows:
        limitation_counts["direct runtime launch correlation not observed"] = 1
    for missing in battle_missing_evidence(group):
        limitation_counts[missing] = 1

    row_summary: dict[str, Any] = {
        "source_experiment_id": group.source_experiment_id,
        "source_line_first": min((row.line_number for row in group.rows), default=None),
        "source_line_last": max((row.line_number for row in group.rows), default=None),
        "allocation_rows": len(group.allocation_rows),
        "launch_rows": len(group.launch_rows),
        "battle_context": battle_context_for_group(group),
        "battle_segment_breakdown": battle_segment_breakdown_for_group(group),
        "nearby_context": nearby_context_for_group(group),
        "parser_summary": {"allocation_summary": allocation_summary},
        "controlled_launch_correlation_summary": launch_summary,
        "applied_commands": command_summary,
        "bounded_live_tuning_readiness": readiness_summary,
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
    missing_counts = Counter(evidence["missing_evidence_counts"])
    if pd_category == "unknown":
        missing_counts["pd evidence context not attached by experimentId importer"] += 1
    evidence["missing_evidence_counts"] = counter_dict(missing_counts)
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
    selected_mode = infer_selected_mode(group, run_mode)
    selected_count = max((int_value(row.pairs.get("selectedShipCount")) for row in allocation_rows), default=0)
    launcher_ids = unique_values(all_rows, "launcherId", "allocatorLauncherId")
    target_ids = unique_values(all_rows, "targetId", "targetStateId")
    pd_category, pd_category_source = pd_category_for_group(group)
    known_missing = [
        "imported by experimentId; review metadata and verdict before tuning",
    ]
    if summary.get("limitation_counts"):
        known_missing.extend(summary["limitation_counts"].keys())
    if pd_category == "unknown":
        known_missing.append("pd evidence context not attached by experimentId importer")
    known_missing.extend(battle_missing_evidence(group))
    known_missing = unique_preserving_order(known_missing)

    allocation_summary = summary["logs"][0]["parser_summary"]["allocation_summary"]
    direct_summary = summary["logs"][0]["controlled_launch_correlation_summary"]
    metadata = {
        "schemaVersion": 1,
        "experimentId": corpus_id,
        "sourceExperimentId": group.source_experiment_id,
        **battle_context_for_group(group),
        "runMode": run_mode,
        "selectedMode": selected_mode,
        "selectedShipCount": selected_count,
        "friendlyMissileShipCount": len(launcher_ids),
        "enemyShipCount": len(target_ids),
        "launcherWeaponCount": len(launcher_ids),
        "missileFamily": missile_family,
        "targetIds": target_ids,
        "pdEvidenceCategory": pd_category,
        "pdEvidenceCategorySource": pd_category_source,
        "battleSegmentBreakdown": battle_segment_breakdown_for_group(group),
        "nearbyContext": nearby_context_for_group(group),
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

    return metadata


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
    parser.add_argument("--context-line-window", type=int, default=200, help="max line distance for same-battle same-cycle context attachment; default: 200")
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
    battle_segments = detect_battle_segments(args.log)
    groups = parse_log_groups(args.log, filters=filters, battle_segments=battle_segments)
    cycle_context_rows = collect_cycle_context_rows(args.log, battle_segments)
    attach_cycle_context_rows(
        groups,
        cycle_context_rows,
        line_window=args.context_line_window,
    )
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
