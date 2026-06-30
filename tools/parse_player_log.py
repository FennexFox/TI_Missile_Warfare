#!/usr/bin/env python3
"""Summarize MissileWarfare markers in a Terra Invicta Player.log."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import statistics


DEFAULT_LOG = Path.home() / "AppData" / "LocalLow" / "Pavonis Interactive" / "TerraInvicta" / "Player.log"
MOD_PREFIX = "[MissileWarfare]"

VERSION_RE = re.compile(r"^\[MissileWarfare\] Version '(?P<version>[^']+)'\. Loading\.")
PATCH_RE = re.compile(r"^\[MissileWarfare\] \[MFC\] Patched (?P<description>.*?): (?P<target>.+)$")
BOOTSTRAP_RE = re.compile(
    r"^\[MissileWarfare\] \[MFC\] Combat launch diagnostics patch bootstrap complete\. "
    r"patched=(?P<patched>\d+), skipped=(?P<skipped>\d+)"
)
LAUNCH_RE = re.compile(r"^\[MissileWarfare\] \[MFC\] \[LaunchLog\] (?P<pairs>.*)$")
SNAPSHOT_RE = re.compile(r"^\[MissileWarfare\] \[MFC\] \[SnapshotLog\] (?P<pairs>.*)$")
ALLOCATION_RE = re.compile(r"^\[MissileWarfare\] \[MFC\] \[AllocationLog\] (?P<pairs>.*)$")
OUTCOME_RE = re.compile(r"^\[MissileWarfare\] \[MFC\] \[OutcomeLog\] (?P<pairs>.*)$")
PAIR_RE = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9_]*)=\"(?P<value>[^\"]*)\"")
REQUIRED_PATCH_DESCRIPTIONS = {
    "primary ship fire hook",
    "secondary missile try-fire hook",
    "secondary missile projectile fire hook",
}
OUTCOME_PATCH_DESCRIPTIONS = {
    "outcome missile damage hook",
    "outcome missile lifecycle hook",
    "outcome ship damage hook",
    "outcome ship destruction hook",
}

APPLIED_ALLOCATION_RECORD_TYPES = {"applied", "appliedDecision", "applied-decision", "commandApplied"}
SKIPPED_ALLOCATION_RECORD_TYPES = {"skipped", "skippedDecision", "skipped-decision"}
FAILED_ALLOCATION_RECORD_TYPES = {"failed", "failedCommand", "commandFailed", "command-failed"}
SHADOW_ALLOCATION_RECORD_TYPES = {"cycle", "allocation", "rejection", "noOp"}
CONTROLLED_DRY_RUN_ALLOCATION_RECORD_TYPES = {
    "dryRunExperiment",
    "dryRunIntent",
    "dryRunCommandCandidate",
    "dryRunApplyGate",
    "dryRunResult",
}
FLEET_WIDE_REPORT_ONLY_ALLOCATION_RECORD_TYPES = {
    "fleetWideDryRunExperiment",
    "fleetWideLauncher",
    "fleetWideTarget",
    "fleetWideCommandCandidate",
    "fleetWideCapState",
    "fleetWideResult",
}
FLEET_WIDE_LIVE_ALLOCATION_RECORD_TYPES = {
    "fleetWideLiveCommandPathStatus",
    "fleetWideLiveApplyDecision",
    "fleetWideLiveResult",
}
FLEET_WIDE_COMMAND_AUTHORITY_ALLOCATION_RECORD_TYPES = {
    "fleetWideCommandAuthorityCandidate",
    "fleetWideCommandAuthorityPreState",
    "fleetWideCommandAuthorityResult",
    "fleetWideCommandAuthorityPostState",
}
FLEET_WIDE_BOUNDED_LIVE_ALLOCATION_RECORD_TYPES = {
    "fleetWideBoundedLiveCandidate",
    "fleetWideBoundedLivePreState",
    "fleetWideBoundedLiveResult",
    "fleetWideBoundedLivePostState",
}
KNOWN_ALLOCATION_RECORD_TYPES = (
    SHADOW_ALLOCATION_RECORD_TYPES
    | CONTROLLED_DRY_RUN_ALLOCATION_RECORD_TYPES
    | FLEET_WIDE_REPORT_ONLY_ALLOCATION_RECORD_TYPES
    | FLEET_WIDE_LIVE_ALLOCATION_RECORD_TYPES
    | FLEET_WIDE_COMMAND_AUTHORITY_ALLOCATION_RECORD_TYPES
    | FLEET_WIDE_BOUNDED_LIVE_ALLOCATION_RECORD_TYPES
    | APPLIED_ALLOCATION_RECORD_TYPES
    | SKIPPED_ALLOCATION_RECORD_TYPES
    | FAILED_ALLOCATION_RECORD_TYPES
)
CRITICAL_ALLOCATION_INPUTS = (
    "ammoGateBudgetShots",
    "targetIdentity",
    "targetVelocity",
    "missileProfileData",
    "pdWeightsDefaulted",
)
ALLOCATION_REJECTION_WINDOW_MARKERS = ("launch window", "range", "receding", "outside threshold", "outside")


@dataclass
class LineHit:
    line: int
    text: str


@dataclass
class PatchHit:
    line: int
    description: str
    target: str


@dataclass
class NumericFieldSummary:
    count: int = 0
    average: float | None = None
    median: float | None = None


@dataclass
class AllocationBattleSummary:
    shadow_cycles: int = 0
    shadow_evaluated_cycles: int = 0
    shadow_skipped_cycles: int = 0
    applied_decisions: int = 0
    skipped_decisions: int = 0
    failed_command_applications: int = 0
    controlled_dry_run_experiments: int = 0
    controlled_dry_run_intents: int = 0
    controlled_dry_run_command_candidates: int = 0
    controlled_dry_run_apply_gate_records: int = 0
    controlled_dry_run_results: int = 0
    controlled_dry_run_experiment_ids: list[str] = field(default_factory=list)
    controlled_dry_run_intended_commands: int = 0
    controlled_dry_run_skipped_commands: int = 0
    controlled_dry_run_applied_commands: int = 0
    controlled_dry_run_failed_commands: int = 0
    controlled_dry_run_safety_gate_blocked_commands: int = 0
    controlled_dry_run_candidate_classification_counts: dict[str, int] = field(default_factory=dict)
    controlled_dry_run_candidate_reason_counts: dict[str, int] = field(default_factory=dict)
    controlled_dry_run_candidate_source_counts: dict[str, int] = field(default_factory=dict)
    controlled_dry_run_apply_gate_result_counts: dict[str, int] = field(default_factory=dict)
    controlled_dry_run_safety_gate_reason_counts: dict[str, int] = field(default_factory=dict)
    controlled_dry_run_command_scope_source_counts: dict[str, int] = field(default_factory=dict)
    controlled_dry_run_command_scope_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    controlled_dry_run_scope_violations: int = 0
    controlled_dry_run_selected_ship_counts: dict[str, int] = field(default_factory=dict)
    controlled_dry_run_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_experiments: int = 0
    fleet_wide_report_only_launchers: int = 0
    fleet_wide_report_only_targets: int = 0
    fleet_wide_report_only_command_candidates: int = 0
    fleet_wide_report_only_cap_state_records: int = 0
    fleet_wide_report_only_results: int = 0
    fleet_wide_report_only_experiment_ids: list[str] = field(default_factory=list)
    fleet_wide_report_only_eligible_launchers: int = 0
    fleet_wide_report_only_excluded_launchers: int = 0
    fleet_wide_report_only_visible_hostile_targets: int = 0
    fleet_wide_report_only_candidate_rows: int = 0
    fleet_wide_report_only_emitted_candidate_rows: int = 0
    fleet_wide_report_only_eligible_candidate_rows: int = 0
    fleet_wide_report_only_cap_would_block_candidates: int = 0
    fleet_wide_report_only_missing_evidence_candidates: int = 0
    fleet_wide_report_only_applied_commands: int = 0
    fleet_wide_report_only_launcher_classification_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_launcher_reason_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_target_classification_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_target_reason_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_candidate_classification_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_candidate_reason_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_candidate_source_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_scope_mode_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_source_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_report_only_target_source_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_live_path_status_records: int = 0
    fleet_wide_live_decision_records: int = 0
    fleet_wide_live_result_records: int = 0
    fleet_wide_live_experiment_ids: list[str] = field(default_factory=list)
    fleet_wide_live_scope_mode_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_live_command_path_status_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_live_re_gate_status_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_live_decision_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_live_reason_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_live_candidate_source_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_live_candidate_rows: int = 0
    fleet_wide_live_emitted_decision_rows: int = 0
    fleet_wide_live_allocator_evidence_candidates: int = 0
    fleet_wide_live_cap_blocked_candidates: int = 0
    fleet_wide_live_missing_evidence_candidates: int = 0
    fleet_wide_live_re_blocked_candidates: int = 0
    fleet_wide_live_applied_commands: int = 0
    fleet_wide_live_failed_commands: int = 0
    fleet_wide_command_authority_candidate_records: int = 0
    fleet_wide_command_authority_pre_state_records: int = 0
    fleet_wide_command_authority_result_records: int = 0
    fleet_wide_command_authority_post_state_records: int = 0
    fleet_wide_command_authority_experiment_ids: list[str] = field(default_factory=list)
    fleet_wide_command_authority_scope_mode_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_command_authority_result_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_command_authority_reason_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_command_authority_selection_relation_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_command_authority_correlation_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_command_authority_applied_commands: int = 0
    fleet_wide_command_authority_failed_commands: int = 0
    fleet_wide_bounded_live_candidate_records: int = 0
    fleet_wide_bounded_live_pre_state_records: int = 0
    fleet_wide_bounded_live_result_records: int = 0
    fleet_wide_bounded_live_post_state_records: int = 0
    fleet_wide_bounded_live_experiment_ids: list[str] = field(default_factory=list)
    fleet_wide_bounded_live_scope_mode_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_result_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_reason_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_selection_relation_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_correlation_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_target_alternative_denominator_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_target_alternative_evidence_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_target_alternative_feature_evidence_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_selected_target_score_space_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_target_alternative_score_space_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_selected_target_rank_comparison_space_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_selected_target_rank_level_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_selected_target_rank_confidence_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_prior_in_flight_confidence_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_prior_in_flight_bound_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_prior_in_flight_target_attribution_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_pressure_decision_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_pressure_decision_reason_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_pressure_evidence_counts: dict[str, int] = field(default_factory=dict)
    fleet_wide_bounded_live_retained_above_threshold: int = 0
    fleet_wide_bounded_live_retargeted_above_threshold: int = 0
    fleet_wide_bounded_live_target_alternative_truncated_records: int = 0
    fleet_wide_bounded_live_applied_with_target_alternative_denominator: int = 0
    fleet_wide_bounded_live_applied_with_target_alternative_denominator_gt_one: int = 0
    fleet_wide_bounded_live_applied_with_unknown_target_alternative_denominator: int = 0
    fleet_wide_bounded_live_applied_commands: int = 0
    fleet_wide_bounded_live_failed_commands: int = 0
    controlled_live_apply_attempts: int = 0
    controlled_live_apply_applied: int = 0
    controlled_live_apply_skipped: int = 0
    controlled_live_apply_failed: int = 0
    controlled_live_apply_reason_counts: dict[str, int] = field(default_factory=dict)
    controlled_live_apply_path_counts: dict[str, int] = field(default_factory=dict)
    controlled_live_apply_candidate_source_counts: dict[str, int] = field(default_factory=dict)
    controlled_selected_group_members_by_experiment: dict[str, str] = field(default_factory=dict)
    controlled_live_apply_counts_by_experiment: dict[str, dict[str, int]] = field(default_factory=dict)
    controlled_live_apply_counts_by_ship: dict[str, dict[str, int]] = field(default_factory=dict)
    controlled_live_apply_assigned_shots_by_ship: dict[str, int] = field(default_factory=dict)
    controlled_live_apply_spent_shots_by_ship: dict[str, int] = field(default_factory=dict)
    controlled_live_apply_spent_unknown_by_ship: dict[str, int] = field(default_factory=dict)
    controlled_live_apply_mismatch_counts: dict[str, int] = field(default_factory=dict)
    unknown_record_type_counts: dict[str, int] = field(default_factory=dict)
    max_target_count_observed: int | None = None
    target_observations: int = 0
    ammo_gate_budget_shots_numeric_cycles: int = 0
    ammo_gate_budget_shots_unknown_cycles: int = 0
    total_ammo_gate_budget_shots: int | None = None
    assigned_shots: int = 0
    assigned_shots_numeric_cycles: int = 0
    assigned_shots_unknown_cycles: int = 0
    total_assigned_shots: int | None = None
    unassigned_shots_numeric_cycles: int = 0
    unassigned_shots_unknown_cycles: int = 0
    total_unassigned_shots: int | None = None
    allocations: int = 0
    rejections: int = 0
    no_op_decisions: int = 0
    top_rejection_reason: str | None = None
    top_rejection_reason_count: int = 0
    top_no_op_reason: str | None = None
    top_no_op_reason_count: int = 0
    no_op_reason_counts: dict[str, int] = field(default_factory=dict)
    kill_size: NumericFieldSummary = field(default_factory=NumericFieldSummary)
    saturation_size: NumericFieldSummary = field(default_factory=NumericFieldSummary)
    launch_window_score: NumericFieldSummary = field(default_factory=NumericFieldSummary)
    score_per_shot: NumericFieldSummary = field(default_factory=NumericFieldSummary)
    missing_input_counts: dict[str, int] = field(default_factory=dict)
    ammo_gate_budget_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    ammo_gate_budget_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    ammo_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    ammo_only_budget_cycles: int = 0
    missing_ammo_gate_budget_evidence_cycles: int = 0
    target_velocity_evidence_cycles: int = 0
    relative_velocity_evidence_cycles: int = 0
    target_velocity_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    target_velocity_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    relative_velocity_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    relative_velocity_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    pd_weight_observed_cycles: int = 0
    pd_weight_defaulted_cycles: int = 0
    pd_weight_unknown_cycles: int = 0
    pd_weight_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    pd_weight_default_reason_counts: dict[str, int] = field(default_factory=dict)
    pd_weight_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    pd_evidence_quality_counts: dict[str, int] = field(default_factory=dict)
    pd_capability_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    pd_capability_observed_field_counts: dict[str, int] = field(default_factory=dict)
    pd_capability_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    pd_capability_limitation_counts: dict[str, int] = field(default_factory=dict)
    same_team_missile_target_snapshots: int = 0
    suspicious_patterns: list[str] = field(default_factory=list)


@dataclass
class LogSummary:
    path: str
    exists: bool
    size_bytes: int = 0
    line_count: int = 0
    version: str | None = None
    version_line: int | None = None
    loaded_line: int | None = None
    enabled_line: int | None = None
    active_line: int | None = None
    bootstrap_line: int | None = None
    bootstrap_patched: int | None = None
    bootstrap_skipped: int | None = None
    patched_hooks: list[PatchHit] = field(default_factory=list)
    launch_log_count: int = 0
    hook_counts: dict[str, int] = field(default_factory=dict)
    first_launch_line: int | None = None
    first_launch_utc: str | None = None
    last_launch_line: int | None = None
    last_launch_utc: str | None = None
    first_seq: int | None = None
    last_seq: int | None = None
    sequence_gaps: list[str] = field(default_factory=list)
    duplicate_sequences: list[int] = field(default_factory=list)
    missile_try_fire_count: int = 0
    missile_try_fire_pre_fire_field_counts: dict[str, int] = field(default_factory=dict)
    missile_try_fire_pre_fire_ammo_source_counts: dict[str, int] = field(default_factory=dict)
    missile_try_fire_pre_post_ammo_delta_counts: dict[str, int] = field(default_factory=dict)
    missile_try_fire_pre_post_ammo_numeric_count: int = 0
    controlled_command_launch_context_rows: int = 0
    controlled_command_launch_correlation_counts: dict[str, int] = field(default_factory=dict)
    controlled_command_launch_observed_spent_numeric_count: int = 0
    snapshot_log_count: int = 0
    snapshot_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_missing_counts: dict[str, int] = field(default_factory=dict)
    snapshot_ammo_gate_budget_shots_counts: dict[str, int] = field(default_factory=dict)
    snapshot_ammo_gate_budget_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_ammo_gate_budget_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    snapshot_ammo_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_live_weapon_state_counts: dict[str, int] = field(default_factory=dict)
    snapshot_known_target_count: int = 0
    snapshot_target_identity_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_target_velocity_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_target_velocity_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    snapshot_relative_velocity_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_relative_velocity_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    snapshot_pd_weight_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_pd_weight_default_reason_counts: dict[str, int] = field(default_factory=dict)
    snapshot_pd_weight_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    snapshot_pd_evidence_quality_counts: dict[str, int] = field(default_factory=dict)
    snapshot_pd_capability_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_pd_capability_observed_field_counts: dict[str, int] = field(default_factory=dict)
    snapshot_pd_capability_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    snapshot_pd_capability_limitation_counts: dict[str, int] = field(default_factory=dict)
    snapshot_target_counts: dict[str, int] = field(default_factory=dict)
    snapshot_target_team_counts: dict[str, int] = field(default_factory=dict)
    snapshot_same_team_target_count: int = 0
    first_snapshot_line: int | None = None
    last_snapshot_line: int | None = None
    outcome_log_count: int = 0
    outcome_record_type_counts: dict[str, int] = field(default_factory=dict)
    outcome_event_level_counts: dict[str, int] = field(default_factory=dict)
    outcome_attribution_level_counts: dict[str, int] = field(default_factory=dict)
    outcome_identity_bridge_counts: dict[str, int] = field(default_factory=dict)
    outcome_source_hook_counts: dict[str, int] = field(default_factory=dict)
    first_outcome_line: int | None = None
    last_outcome_line: int | None = None
    allocation_log_count: int = 0
    allocation_record_type_counts: dict[str, int] = field(default_factory=dict)
    allocation_status_counts: dict[str, int] = field(default_factory=dict)
    allocation_missing_input_counts: dict[str, int] = field(default_factory=dict)
    allocation_ammo_gate_budget_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    allocation_ammo_gate_budget_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    allocation_ammo_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    allocation_target_velocity_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    allocation_target_velocity_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    allocation_relative_velocity_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    allocation_relative_velocity_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    allocation_pd_weight_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    allocation_pd_weight_default_reason_counts: dict[str, int] = field(default_factory=dict)
    allocation_pd_weight_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    allocation_pd_evidence_quality_counts: dict[str, int] = field(default_factory=dict)
    allocation_pd_capability_evidence_source_counts: dict[str, int] = field(default_factory=dict)
    allocation_pd_capability_observed_field_counts: dict[str, int] = field(default_factory=dict)
    allocation_pd_capability_missing_reason_counts: dict[str, int] = field(default_factory=dict)
    allocation_pd_capability_limitation_counts: dict[str, int] = field(default_factory=dict)
    allocation_rejection_reason_counts: dict[str, int] = field(default_factory=dict)
    allocation_no_op_reason_counts: dict[str, int] = field(default_factory=dict)
    allocation_assigned_shots_counts: dict[str, int] = field(default_factory=dict)
    allocation_summary: AllocationBattleSummary = field(default_factory=AllocationBattleSummary)
    first_allocation_line: int | None = None
    last_allocation_line: int | None = None
    issues: list[LineHit] = field(default_factory=list)


def parse_pairs(text: str) -> dict[str, str]:
    """Parse quoted key/value pairs from a LaunchLog payload."""
    return {match.group("key"): match.group("value") for match in PAIR_RE.finditer(text)}


def is_issue_line(line: str) -> bool:
    """Return whether a MissileWarfare log line represents a warning or error."""
    if not line.startswith(MOD_PREFIX):
        return False

    lowered = line.lower()
    markers = ("[error]", "[exception]", "[warning]", " skipped ", " failed", "not loaded")
    return any(marker in lowered for marker in markers)


def try_parse_int(text: str | None) -> int | None:
    """Parse a diagnostic integer value, returning None for unknown fields."""
    if text is None:
        return None

    try:
        return int(text)
    except ValueError:
        return None


def first_parse_int(*texts: str | None) -> int | None:
    """Return the first successfully parsed integer from a list of fields."""
    for text in texts:
        value = try_parse_int(text)
        if value is not None:
            return value
    return None


def try_parse_float(text: str | None) -> float | None:
    """Parse a diagnostic floating-point value, returning None for unknown fields."""
    if text is None or text.strip() in {"", "unknown", "n/a", "null"}:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def sort_numeric_text_count(item: tuple[str, int]) -> tuple[int, int | str]:
    """Sort numeric histogram keys by numeric value, then non-numeric keys alphabetically."""
    key, _count = item
    return (0, int(key)) if key.isdigit() else (1, key)


def sorted_count_dict(counter: Counter[str], limit: int | None = None) -> dict[str, int]:
    """Return a deterministic count dictionary sorted by count descending, then key."""
    items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    if limit is not None:
        items = items[:limit]
    return dict(items)


def sorted_nested_count_dict(values: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    """Return deterministic nested counter dictionaries."""
    return {key: dict(sorted(counter.items())) for key, counter in sorted(values.items())}


def summarize_numeric(values: list[float]) -> NumericFieldSummary:
    """Return compact average/median stats for present numeric values."""
    if not values:
        return NumericFieldSummary()

    return NumericFieldSummary(
        count=len(values),
        average=statistics.fmean(values),
        median=statistics.median(values),
    )


def split_csv_field(text: str | None) -> list[str]:
    """Split a comma-separated diagnostic field into non-empty values."""
    if not text or text == "none":
        return []

    return [value.strip() for value in text.split(",") if value.strip()]


def ship_key_from_parts(ship_id: str | None, name: str | None, team: str | None) -> str:
    """Return a compact stable display key for ship-scoped report rows."""
    clean_id = ship_id or "unknown"
    clean_name = name or "unknown"
    clean_team = team or "unknown"
    return f"{clean_name}#{clean_id}[team={clean_team}]"


def ship_key_from_pairs(pairs: dict[str, str]) -> str:
    """Return the selected command ship key from an allocation record."""
    return ship_key_from_parts(pairs.get("launcherId"), pairs.get("launcher"), pairs.get("launcherTeam"))


def format_group_members(ids_text: str | None, names_text: str | None, teams_text: str | None) -> str:
    """Format selected-group ids, names, and teams from comma-separated fields."""
    ids = split_csv_field(ids_text)
    names = split_csv_field(names_text)
    teams = split_csv_field(teams_text)
    members: list[str] = []
    for index, ship_id in enumerate(ids):
        name = names[index] if index < len(names) else "unknown"
        team = teams[index] if index < len(teams) else "unknown"
        members.append(ship_key_from_parts(ship_id, name, team))
    return ", ".join(members) if members else "none"


def split_observed_capability_fields(text: str | None) -> list[str]:
    """Split PD capability observed fields, preserving explicitly emitted none."""
    if text is None or text == "":
        return []
    if text == "none":
        return ["none"]
    return [value.strip() for value in text.split(",") if value.strip()]


def is_ammo_only_budget_reason(text: str | None) -> bool:
    """Return whether an ammo/gate budget missing reason is explicitly ammo-only evidence."""
    if not text:
        return False

    return text.strip().lower() in {
        "ammo-only projectile snapshot evidence",
        "missing live weapon correlation",
        "missing module-keyed ammo evidence",
    }


def top_count(counter: Counter[str]) -> tuple[str | None, int]:
    """Return a deterministic top key and count."""
    if not counter:
        return None, 0

    reason, count = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0]
    return reason, count


def build_allocation_battle_summary(
    record_type_counts: Counter[str],
    status_counts: Counter[str],
    rejection_reason_counts: Counter[str],
    no_op_reason_counts: Counter[str],
    cycle_missing_input_counts: Counter[str],
    cycle_target_counts: list[int],
    ammo_gate_budget_values: list[int | None],
    assigned_shot_values: list[int | None],
    unassigned_shot_values: list[int | None],
    kill_size_values: list[float],
    saturation_size_values: list[float],
    launch_window_score_values: list[float],
    score_per_shot_values: list[float],
    allocation_partial_saturation_count: int,
    allocation_overkill_count: int,
    cycle_allocated_target_values: dict[str, list[float]],
    cycle_rejected_target_values: dict[str, list[float]],
    cycle_ammo_gate_budget_evidence_source_counts: Counter[str],
    cycle_ammo_gate_budget_missing_reason_counts: Counter[str],
    cycle_ammo_evidence_source_counts: Counter[str],
    cycle_ammo_only_budget_count: int,
    cycle_missing_ammo_gate_budget_evidence_count: int,
    cycle_target_velocity_evidence_source_counts: Counter[str],
    cycle_target_velocity_missing_reason_counts: Counter[str],
    cycle_relative_velocity_evidence_source_counts: Counter[str],
    cycle_relative_velocity_missing_reason_counts: Counter[str],
    cycle_pd_weight_evidence_source_counts: Counter[str],
    cycle_pd_weight_default_reason_counts: Counter[str],
    cycle_pd_weight_missing_reason_counts: Counter[str],
    cycle_pd_weight_defaulted_counts: Counter[str],
    cycle_pd_evidence_quality_counts: Counter[str],
    cycle_pd_capability_evidence_source_counts: Counter[str],
    cycle_pd_capability_observed_field_counts: Counter[str],
    cycle_pd_capability_missing_reason_counts: Counter[str],
    cycle_pd_capability_limitation_counts: Counter[str],
) -> AllocationBattleSummary:
    """Build a compact battle-level allocation summary from parsed records."""
    summary = AllocationBattleSummary()
    summary.shadow_cycles = record_type_counts.get("cycle", 0)
    summary.shadow_evaluated_cycles = status_counts.get("evaluated", 0)
    summary.shadow_skipped_cycles = status_counts.get("skipped", 0)
    summary.applied_decisions = sum(record_type_counts[record_type] for record_type in APPLIED_ALLOCATION_RECORD_TYPES)
    summary.skipped_decisions = sum(record_type_counts[record_type] for record_type in SKIPPED_ALLOCATION_RECORD_TYPES)
    summary.failed_command_applications = sum(
        record_type_counts[record_type] for record_type in FAILED_ALLOCATION_RECORD_TYPES
    )
    summary.unknown_record_type_counts = dict(
        sorted(
            (record_type, count)
            for record_type, count in record_type_counts.items()
            if record_type not in KNOWN_ALLOCATION_RECORD_TYPES
        )
    )
    summary.max_target_count_observed = max(cycle_target_counts) if cycle_target_counts else None
    summary.target_observations = sum(cycle_target_counts)

    numeric_ammo_gate_budget_shots = [value for value in ammo_gate_budget_values if value is not None]
    summary.ammo_gate_budget_shots_numeric_cycles = len(numeric_ammo_gate_budget_shots)
    summary.ammo_gate_budget_shots_unknown_cycles = len(ammo_gate_budget_values) - len(numeric_ammo_gate_budget_shots)
    summary.total_ammo_gate_budget_shots = sum(numeric_ammo_gate_budget_shots) if summary.ammo_gate_budget_shots_unknown_cycles == 0 else None

    numeric_assigned_shots = [value for value in assigned_shot_values if value is not None]
    summary.assigned_shots_numeric_cycles = len(numeric_assigned_shots)
    summary.assigned_shots_unknown_cycles = len(assigned_shot_values) - len(numeric_assigned_shots)
    summary.assigned_shots = sum(numeric_assigned_shots)
    summary.total_assigned_shots = sum(numeric_assigned_shots) if summary.assigned_shots_unknown_cycles == 0 else None

    numeric_unassigned_shots = [value for value in unassigned_shot_values if value is not None]
    summary.unassigned_shots_numeric_cycles = len(numeric_unassigned_shots)
    summary.unassigned_shots_unknown_cycles = len(unassigned_shot_values) - len(numeric_unassigned_shots)
    summary.total_unassigned_shots = (
        sum(numeric_unassigned_shots) if summary.unassigned_shots_unknown_cycles == 0 else None
    )

    summary.allocations = record_type_counts.get("allocation", 0)
    summary.rejections = record_type_counts.get("rejection", 0)
    summary.no_op_decisions = record_type_counts.get("noOp", 0)
    summary.top_rejection_reason, summary.top_rejection_reason_count = top_count(rejection_reason_counts)
    summary.top_no_op_reason, summary.top_no_op_reason_count = top_count(no_op_reason_counts)
    summary.no_op_reason_counts = sorted_count_dict(no_op_reason_counts, limit=12)
    summary.kill_size = summarize_numeric(kill_size_values)
    summary.saturation_size = summarize_numeric(saturation_size_values)
    summary.launch_window_score = summarize_numeric(launch_window_score_values)
    summary.score_per_shot = summarize_numeric(score_per_shot_values)
    summary.missing_input_counts = {field_name: cycle_missing_input_counts.get(field_name, 0) for field_name in CRITICAL_ALLOCATION_INPUTS}
    summary.ammo_gate_budget_evidence_source_counts = dict(sorted(cycle_ammo_gate_budget_evidence_source_counts.items()))
    summary.ammo_gate_budget_missing_reason_counts = dict(sorted(cycle_ammo_gate_budget_missing_reason_counts.items()))
    summary.ammo_evidence_source_counts = dict(sorted(cycle_ammo_evidence_source_counts.items()))
    summary.ammo_only_budget_cycles = cycle_ammo_only_budget_count
    summary.missing_ammo_gate_budget_evidence_cycles = cycle_missing_ammo_gate_budget_evidence_count
    summary.target_velocity_evidence_source_counts = dict(sorted(cycle_target_velocity_evidence_source_counts.items()))
    summary.target_velocity_missing_reason_counts = dict(sorted(cycle_target_velocity_missing_reason_counts.items()))
    summary.relative_velocity_evidence_source_counts = dict(sorted(cycle_relative_velocity_evidence_source_counts.items()))
    summary.relative_velocity_missing_reason_counts = dict(sorted(cycle_relative_velocity_missing_reason_counts.items()))
    summary.target_velocity_evidence_cycles = sum(
        count for source, count in cycle_target_velocity_evidence_source_counts.items() if source not in {"unknown", "none"}
    )
    summary.relative_velocity_evidence_cycles = sum(
        count for source, count in cycle_relative_velocity_evidence_source_counts.items() if source not in {"unknown", "none"}
    )
    summary.pd_weight_evidence_source_counts = dict(sorted(cycle_pd_weight_evidence_source_counts.items()))
    summary.pd_weight_default_reason_counts = dict(sorted(cycle_pd_weight_default_reason_counts.items()))
    summary.pd_weight_missing_reason_counts = dict(sorted(cycle_pd_weight_missing_reason_counts.items()))
    summary.pd_evidence_quality_counts = dict(sorted(cycle_pd_evidence_quality_counts.items()))
    summary.pd_capability_evidence_source_counts = dict(sorted(cycle_pd_capability_evidence_source_counts.items()))
    summary.pd_capability_observed_field_counts = dict(sorted(cycle_pd_capability_observed_field_counts.items()))
    summary.pd_capability_missing_reason_counts = dict(sorted(cycle_pd_capability_missing_reason_counts.items()))
    summary.pd_capability_limitation_counts = dict(sorted(cycle_pd_capability_limitation_counts.items()))
    summary.pd_weight_defaulted_cycles = cycle_pd_weight_defaulted_counts.get("true", 0)
    summary.pd_weight_observed_cycles = cycle_pd_weight_defaulted_counts.get("false", 0)
    summary.pd_weight_unknown_cycles = cycle_pd_weight_defaulted_counts.get("unknown", 0)
    summary.suspicious_patterns = allocation_suspicious_patterns(
        summary,
        rejection_reason_counts,
        allocation_partial_saturation_count,
        allocation_overkill_count,
        cycle_allocated_target_values,
        cycle_rejected_target_values,
    )
    return summary


def allocation_suspicious_patterns(
    summary: AllocationBattleSummary,
    rejection_reason_counts: Counter[str],
    allocation_partial_saturation_count: int,
    allocation_overkill_count: int,
    cycle_allocated_target_values: dict[str, list[float]],
    cycle_rejected_target_values: dict[str, list[float]],
) -> list[str]:
    """Return conservative allocation tuning hints from observable log fields."""
    patterns: list[str] = []
    shadow_cycles = summary.shadow_cycles

    if shadow_cycles and summary.missing_input_counts.get("ammoGateBudgetShots", 0) == shadow_cycles:
        patterns.append("all shadow cycles missing ammoGateBudgetShots")

    if shadow_cycles and summary.ammo_only_budget_cycles == shadow_cycles:
        patterns.append("all shadow cycles have ammo-only budget evidence")

    if shadow_cycles and summary.missing_ammo_gate_budget_evidence_cycles == shadow_cycles:
        patterns.append("all shadow cycles blocked by missing ammo/gate budget evidence")

    if summary.same_team_missile_target_snapshots:
        patterns.append(f"same-team missile target snapshots: {summary.same_team_missile_target_snapshots}")

    if (
        summary.ammo_gate_budget_shots_numeric_cycles
        and summary.total_ammo_gate_budget_shots is not None
        and summary.total_ammo_gate_budget_shots > 0
        and summary.total_assigned_shots == 0
    ):
        patterns.append("all numeric ammo/gate budget shots left unassigned")

    launch_window_rejects = sum(
        count
        for reason, count in rejection_reason_counts.items()
        if any(marker in reason.lower() for marker in ALLOCATION_REJECTION_WINDOW_MARKERS)
    )
    if summary.rejections and launch_window_rejects / summary.rejections >= 0.5:
        patterns.append("too many launch-window rejects")

    if allocation_partial_saturation_count >= 2:
        patterns.append("repeated partial saturation")

    if allocation_overkill_count >= 2:
        patterns.append("possible overkill")

    for cycle_id, rejected_values in cycle_rejected_target_values.items():
        allocated_values = cycle_allocated_target_values.get(cycle_id, [])
        if allocated_values and rejected_values and max(rejected_values) > max(allocated_values):
            patterns.append("higher-value rejected target present")
            break

    high_missing_inputs = [
        field_name
        for field_name, count in summary.missing_input_counts.items()
        if shadow_cycles and count / shadow_cycles >= 0.8
    ]
    if high_missing_inputs:
        patterns.append("allocation report limited by missing runtime inputs")

    if not any(
        field_summary.count
        for field_summary in (
            summary.kill_size,
            summary.saturation_size,
            summary.launch_window_score,
            summary.score_per_shot,
        )
    ):
        patterns.append("insufficient numeric allocation data")

    return patterns or ["none"]


def parse_log(path: Path, max_issues: int) -> LogSummary:
    """Scan a Player.log file and collect MissileWarfare diagnostics markers."""
    summary = LogSummary(path=str(path), exists=path.exists())
    if not path.exists():
        return summary

    summary.size_bytes = path.stat().st_size
    sequences: list[int] = []
    seen_sequences: set[int] = set()
    duplicate_sequences: set[int] = set()
    hook_counts: Counter[str] = Counter()
    missile_try_fire_pre_fire_field_counts: Counter[str] = Counter()
    missile_try_fire_pre_fire_ammo_source_counts: Counter[str] = Counter()
    missile_try_fire_pre_post_ammo_delta_counts: Counter[str] = Counter()
    controlled_command_launch_correlation_counts: Counter[str] = Counter()
    controlled_command_launch_context_rows = 0
    controlled_command_launch_observed_spent_numeric_count = 0
    snapshot_source_counts: Counter[str] = Counter()
    snapshot_missing_counts: Counter[str] = Counter()
    snapshot_ammo_gate_budget_shots_counts: Counter[str] = Counter()
    snapshot_ammo_gate_budget_evidence_source_counts: Counter[str] = Counter()
    snapshot_ammo_gate_budget_missing_reason_counts: Counter[str] = Counter()
    snapshot_ammo_evidence_source_counts: Counter[str] = Counter()
    snapshot_live_weapon_state_counts: Counter[str] = Counter()
    snapshot_target_identity_source_counts: Counter[str] = Counter()
    snapshot_target_velocity_evidence_source_counts: Counter[str] = Counter()
    snapshot_target_velocity_missing_reason_counts: Counter[str] = Counter()
    snapshot_relative_velocity_evidence_source_counts: Counter[str] = Counter()
    snapshot_relative_velocity_missing_reason_counts: Counter[str] = Counter()
    snapshot_pd_weight_evidence_source_counts: Counter[str] = Counter()
    snapshot_pd_weight_default_reason_counts: Counter[str] = Counter()
    snapshot_pd_weight_missing_reason_counts: Counter[str] = Counter()
    snapshot_pd_evidence_quality_counts: Counter[str] = Counter()
    snapshot_pd_capability_evidence_source_counts: Counter[str] = Counter()
    snapshot_pd_capability_observed_field_counts: Counter[str] = Counter()
    snapshot_pd_capability_missing_reason_counts: Counter[str] = Counter()
    snapshot_pd_capability_limitation_counts: Counter[str] = Counter()
    snapshot_target_counts: Counter[str] = Counter()
    snapshot_target_team_counts: Counter[str] = Counter()
    snapshot_same_team_target_count = 0
    outcome_record_type_counts: Counter[str] = Counter()
    outcome_event_level_counts: Counter[str] = Counter()
    outcome_attribution_level_counts: Counter[str] = Counter()
    outcome_identity_bridge_counts: Counter[str] = Counter()
    outcome_source_hook_counts: Counter[str] = Counter()
    allocation_record_type_counts: Counter[str] = Counter()
    allocation_status_counts: Counter[str] = Counter()
    allocation_missing_input_counts: Counter[str] = Counter()
    allocation_ammo_gate_budget_evidence_source_counts: Counter[str] = Counter()
    allocation_ammo_gate_budget_missing_reason_counts: Counter[str] = Counter()
    allocation_ammo_evidence_source_counts: Counter[str] = Counter()
    allocation_target_velocity_evidence_source_counts: Counter[str] = Counter()
    allocation_target_velocity_missing_reason_counts: Counter[str] = Counter()
    allocation_relative_velocity_evidence_source_counts: Counter[str] = Counter()
    allocation_relative_velocity_missing_reason_counts: Counter[str] = Counter()
    allocation_pd_weight_evidence_source_counts: Counter[str] = Counter()
    allocation_pd_weight_default_reason_counts: Counter[str] = Counter()
    allocation_pd_weight_missing_reason_counts: Counter[str] = Counter()
    allocation_pd_evidence_quality_counts: Counter[str] = Counter()
    allocation_pd_capability_evidence_source_counts: Counter[str] = Counter()
    allocation_pd_capability_observed_field_counts: Counter[str] = Counter()
    allocation_pd_capability_missing_reason_counts: Counter[str] = Counter()
    allocation_pd_capability_limitation_counts: Counter[str] = Counter()
    allocation_rejection_reason_counts: Counter[str] = Counter()
    allocation_no_op_reason_counts: Counter[str] = Counter()
    allocation_assigned_shots_counts: Counter[str] = Counter()
    controlled_dry_run_experiment_ids: set[str] = set()
    controlled_dry_run_selected_ship_counts: Counter[str] = Counter()
    controlled_dry_run_missing_reason_counts: Counter[str] = Counter()
    controlled_dry_run_candidate_classification_counts: Counter[str] = Counter()
    controlled_dry_run_candidate_reason_counts: Counter[str] = Counter()
    controlled_dry_run_candidate_source_counts: Counter[str] = Counter()
    controlled_dry_run_apply_gate_result_counts: Counter[str] = Counter()
    controlled_dry_run_safety_gate_reason_counts: Counter[str] = Counter()
    controlled_dry_run_command_scope_source_counts: Counter[str] = Counter()
    controlled_dry_run_command_scope_missing_reason_counts: Counter[str] = Counter()
    controlled_live_apply_reason_counts: Counter[str] = Counter()
    controlled_live_apply_path_counts: Counter[str] = Counter()
    controlled_live_apply_candidate_source_counts: Counter[str] = Counter()
    controlled_selected_group_members_by_experiment: dict[str, str] = {}
    controlled_live_apply_counts_by_experiment: dict[str, Counter[str]] = defaultdict(Counter)
    controlled_live_apply_counts_by_ship: dict[str, Counter[str]] = defaultdict(Counter)
    controlled_live_apply_assigned_shots_by_ship: Counter[str] = Counter()
    controlled_live_apply_spent_shots_by_ship: Counter[str] = Counter()
    controlled_live_apply_spent_unknown_by_ship: Counter[str] = Counter()
    controlled_live_apply_mismatch_counts: Counter[str] = Counter()
    fleet_wide_report_only_experiment_ids: set[str] = set()
    fleet_wide_report_only_launcher_classification_counts: Counter[str] = Counter()
    fleet_wide_report_only_launcher_reason_counts: Counter[str] = Counter()
    fleet_wide_report_only_target_classification_counts: Counter[str] = Counter()
    fleet_wide_report_only_target_reason_counts: Counter[str] = Counter()
    fleet_wide_report_only_candidate_classification_counts: Counter[str] = Counter()
    fleet_wide_report_only_candidate_reason_counts: Counter[str] = Counter()
    fleet_wide_report_only_candidate_source_counts: Counter[str] = Counter()
    fleet_wide_report_only_scope_mode_counts: Counter[str] = Counter()
    fleet_wide_report_only_source_counts: Counter[str] = Counter()
    fleet_wide_report_only_target_source_counts: Counter[str] = Counter()
    fleet_wide_live_experiment_ids: set[str] = set()
    fleet_wide_live_scope_mode_counts: Counter[str] = Counter()
    fleet_wide_live_command_path_status_counts: Counter[str] = Counter()
    fleet_wide_live_re_gate_status_counts: Counter[str] = Counter()
    fleet_wide_live_decision_counts: Counter[str] = Counter()
    fleet_wide_live_reason_counts: Counter[str] = Counter()
    fleet_wide_live_candidate_source_counts: Counter[str] = Counter()
    fleet_wide_command_authority_experiment_ids: set[str] = set()
    fleet_wide_command_authority_scope_mode_counts: Counter[str] = Counter()
    fleet_wide_command_authority_result_counts: Counter[str] = Counter()
    fleet_wide_command_authority_reason_counts: Counter[str] = Counter()
    fleet_wide_command_authority_selection_relation_counts: Counter[str] = Counter()
    fleet_wide_command_authority_correlation_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_experiment_ids: set[str] = set()
    fleet_wide_bounded_live_scope_mode_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_result_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_reason_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_selection_relation_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_correlation_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_target_alternative_denominator_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_target_alternative_evidence_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_target_alternative_feature_evidence_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_selected_target_score_space_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_target_alternative_score_space_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_selected_target_rank_comparison_space_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_selected_target_rank_level_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_selected_target_rank_confidence_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_prior_in_flight_confidence_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_prior_in_flight_bound_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_prior_in_flight_target_attribution_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_pressure_decision_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_pressure_decision_reason_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_pressure_evidence_counts: Counter[str] = Counter()
    fleet_wide_bounded_live_retained_above_threshold = 0
    fleet_wide_bounded_live_retargeted_above_threshold = 0
    fleet_wide_bounded_live_target_alternative_truncated_records = 0
    fleet_wide_bounded_live_applied_with_target_alternative_denominator = 0
    fleet_wide_bounded_live_applied_with_target_alternative_denominator_gt_one = 0
    fleet_wide_bounded_live_applied_with_unknown_target_alternative_denominator = 0
    controlled_dry_run_scope_violations = 0
    controlled_live_apply_attempts = 0
    controlled_live_apply_applied = 0
    controlled_live_apply_skipped = 0
    controlled_live_apply_failed = 0
    fleet_wide_report_only_eligible_launchers = 0
    fleet_wide_report_only_excluded_launchers = 0
    fleet_wide_report_only_visible_hostile_targets = 0
    fleet_wide_report_only_candidate_rows = 0
    fleet_wide_report_only_emitted_candidate_rows = 0
    fleet_wide_report_only_eligible_candidate_rows = 0
    fleet_wide_report_only_cap_would_block_candidates = 0
    fleet_wide_report_only_missing_evidence_candidates = 0
    fleet_wide_report_only_applied_commands = 0
    fleet_wide_live_candidate_rows = 0
    fleet_wide_live_emitted_decision_rows = 0
    fleet_wide_live_allocator_evidence_candidates = 0
    fleet_wide_live_cap_blocked_candidates = 0
    fleet_wide_live_missing_evidence_candidates = 0
    fleet_wide_live_re_blocked_candidates = 0
    fleet_wide_live_applied_commands = 0
    fleet_wide_live_failed_commands = 0
    fleet_wide_command_authority_applied_commands = 0
    fleet_wide_command_authority_failed_commands = 0
    fleet_wide_bounded_live_applied_commands = 0
    fleet_wide_bounded_live_failed_commands = 0
    controlled_dry_run_intended_commands = 0
    controlled_dry_run_skipped_commands = 0
    controlled_dry_run_applied_commands = 0
    controlled_dry_run_failed_commands = 0
    controlled_dry_run_safety_gate_blocked_commands = 0
    controlled_dry_run_result_safety_gate_blocked_commands = 0
    cycle_missing_input_counts: Counter[str] = Counter()
    cycle_target_counts: list[int] = []
    ammo_gate_budget_values: list[int | None] = []
    assigned_shot_values: list[int | None] = []
    unassigned_shot_values: list[int | None] = []
    kill_size_values: list[float] = []
    saturation_size_values: list[float] = []
    launch_window_score_values: list[float] = []
    score_per_shot_values: list[float] = []
    allocation_partial_saturation_count = 0
    allocation_overkill_count = 0
    cycle_ammo_gate_budget_evidence_source_counts: Counter[str] = Counter()
    cycle_ammo_gate_budget_missing_reason_counts: Counter[str] = Counter()
    cycle_ammo_evidence_source_counts: Counter[str] = Counter()
    cycle_target_velocity_evidence_source_counts: Counter[str] = Counter()
    cycle_target_velocity_missing_reason_counts: Counter[str] = Counter()
    cycle_relative_velocity_evidence_source_counts: Counter[str] = Counter()
    cycle_relative_velocity_missing_reason_counts: Counter[str] = Counter()
    cycle_pd_weight_evidence_source_counts: Counter[str] = Counter()
    cycle_pd_weight_default_reason_counts: Counter[str] = Counter()
    cycle_pd_weight_missing_reason_counts: Counter[str] = Counter()
    cycle_pd_weight_defaulted_counts: Counter[str] = Counter()
    cycle_pd_evidence_quality_counts: Counter[str] = Counter()
    cycle_pd_capability_evidence_source_counts: Counter[str] = Counter()
    cycle_pd_capability_observed_field_counts: Counter[str] = Counter()
    cycle_pd_capability_missing_reason_counts: Counter[str] = Counter()
    cycle_pd_capability_limitation_counts: Counter[str] = Counter()
    cycle_ammo_only_budget_count = 0
    cycle_missing_ammo_gate_budget_evidence_count = 0
    cycle_allocated_target_values: dict[str, list[float]] = {}
    cycle_rejected_target_values: dict[str, list[float]] = {}
    pre_fire_fields = (
        "preFireAmmoEvidenceSource",
        "preFireRemaining",
        "preFireWeaponHasAmmo",
        "preFireWeaponCanFire",
        "preFireOnCooldown",
        "preFireSalvoShotsFired",
        "preFireSalvoShots",
    )

    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            summary.line_count = line_number
            line = raw_line.rstrip("\r\n")

            version = VERSION_RE.match(line)
            if version:
                summary.version = version.group("version")
                summary.version_line = line_number
                continue

            patch = PATCH_RE.match(line)
            if patch:
                summary.patched_hooks.append(
                    PatchHit(
                        line=line_number,
                        description=patch.group("description"),
                        target=patch.group("target"),
                    )
                )
                continue

            bootstrap = BOOTSTRAP_RE.match(line)
            if bootstrap:
                summary.bootstrap_line = line_number
                summary.bootstrap_patched = int(bootstrap.group("patched"))
                summary.bootstrap_skipped = int(bootstrap.group("skipped"))
                continue

            if line == "[MissileWarfare] [MFC] MissileWarfare loaded. Current build is scaffold/logging-first only.":
                summary.loaded_line = line_number
                continue

            if line == "[MissileWarfare] [MFC] MissileWarfare enabled.":
                summary.enabled_line = line_number
                continue

            if line == "[MissileWarfare] Active.":
                summary.active_line = line_number
                continue

            launch = LAUNCH_RE.match(line)
            if launch:
                pairs = parse_pairs(launch.group("pairs"))
                summary.launch_log_count += 1

                hook = pairs.get("hook", "unknown")
                hook_counts[hook] += 1
                if hook == "MissileWeapon.TryFire":
                    summary.missile_try_fire_count += 1
                    for field_name in pre_fire_fields:
                        if field_name in pairs:
                            missile_try_fire_pre_fire_field_counts[field_name] += 1
                    if "preFireAmmoEvidenceSource" in pairs:
                        missile_try_fire_pre_fire_ammo_source_counts[pairs["preFireAmmoEvidenceSource"]] += 1

                    pre_fire_remaining = try_parse_int(pairs.get("preFireRemaining"))
                    post_fire_remaining = try_parse_int(pairs.get("postFireRemaining"))
                    if pre_fire_remaining is not None and post_fire_remaining is not None:
                        summary.missile_try_fire_pre_post_ammo_numeric_count += 1
                        delta = pre_fire_remaining - post_fire_remaining
                        missile_try_fire_pre_post_ammo_delta_counts[str(delta)] += 1
                    controlled_correlation = pairs.get("controlledCommandCorrelation")
                    command_result_id = pairs.get("commandResultId")
                    if controlled_correlation or command_result_id:
                        controlled_command_launch_correlation_counts[
                            controlled_correlation or "unknown"
                        ] += 1
                    if command_result_id and command_result_id not in {"none", "unknown"}:
                        controlled_command_launch_context_rows += 1
                    if try_parse_int(pairs.get("controlledCommandObservedSpentShots")) is not None:
                        controlled_command_launch_observed_spent_numeric_count += 1

                if summary.first_launch_line is None:
                    summary.first_launch_line = line_number
                    summary.first_launch_utc = pairs.get("utc")
                summary.last_launch_line = line_number
                summary.last_launch_utc = pairs.get("utc")

                seq_text = pairs.get("seq")
                if seq_text is not None:
                    try:
                        seq = int(seq_text)
                    except ValueError:
                        pass
                    else:
                        sequences.append(seq)
                        if seq in seen_sequences:
                            duplicate_sequences.add(seq)
                        seen_sequences.add(seq)
                continue

            snapshot = SNAPSHOT_RE.match(line)
            if snapshot:
                pairs = parse_pairs(snapshot.group("pairs"))
                summary.snapshot_log_count += 1

                source = pairs.get("source", "unknown")
                snapshot_source_counts[source] += 1
                snapshot_ammo_gate_budget_shots_counts[pairs.get("ammoGateBudgetShots", "unknown")] += 1
                ammo_gate_budget_evidence_source = pairs.get("ammoGateBudgetEvidenceSource")
                if ammo_gate_budget_evidence_source:
                    snapshot_ammo_gate_budget_evidence_source_counts[ammo_gate_budget_evidence_source] += 1
                ammo_gate_budget_missing_reason = pairs.get("ammoGateBudgetMissingReason")
                if ammo_gate_budget_missing_reason:
                    snapshot_ammo_gate_budget_missing_reason_counts[ammo_gate_budget_missing_reason] += 1
                ammo_evidence_source = pairs.get("ammoEvidenceSource")
                if ammo_evidence_source:
                    snapshot_ammo_evidence_source_counts[ammo_evidence_source] += 1
                live_weapon_state = pairs.get("liveWeaponState")
                if live_weapon_state:
                    snapshot_live_weapon_state_counts[live_weapon_state] += 1

                target_id = pairs.get("targetId", "unknown")
                target_name = pairs.get("target", "unknown")
                if target_id and target_id != "unknown":
                    summary.snapshot_known_target_count += 1
                    snapshot_target_counts[f"{target_name}#{target_id}"] += 1

                target_identity_source = pairs.get("targetIdentitySource")
                if target_identity_source:
                    snapshot_target_identity_source_counts[target_identity_source] += 1

                target_velocity_evidence_source = pairs.get("targetVelocityEvidenceSource")
                if target_velocity_evidence_source:
                    snapshot_target_velocity_evidence_source_counts[target_velocity_evidence_source] += 1
                target_velocity_missing_reason = pairs.get("targetVelocityMissingReason")
                if target_velocity_missing_reason:
                    snapshot_target_velocity_missing_reason_counts[target_velocity_missing_reason] += 1
                relative_velocity_evidence_source = pairs.get("relativeVelocityEvidenceSource")
                if relative_velocity_evidence_source:
                    snapshot_relative_velocity_evidence_source_counts[relative_velocity_evidence_source] += 1
                relative_velocity_missing_reason = pairs.get("relativeVelocityMissingReason")
                if relative_velocity_missing_reason:
                    snapshot_relative_velocity_missing_reason_counts[relative_velocity_missing_reason] += 1
                pd_weight_evidence_source = pairs.get("pdWeightEvidenceSource")
                if pd_weight_evidence_source:
                    snapshot_pd_weight_evidence_source_counts[pd_weight_evidence_source] += 1
                pd_weight_default_reason = pairs.get("pdWeightDefaultReason")
                if pd_weight_default_reason:
                    snapshot_pd_weight_default_reason_counts[pd_weight_default_reason] += 1
                pd_weight_missing_reason = pairs.get("pdWeightMissingReason")
                if pd_weight_missing_reason:
                    snapshot_pd_weight_missing_reason_counts[pd_weight_missing_reason] += 1
                pd_evidence_quality = pairs.get("pdEvidenceQuality")
                if pd_evidence_quality:
                    snapshot_pd_evidence_quality_counts[pd_evidence_quality] += 1
                pd_capability_evidence_source = pairs.get("pdCapabilityEvidenceSource")
                if pd_capability_evidence_source:
                    snapshot_pd_capability_evidence_source_counts[pd_capability_evidence_source] += 1
                for field_name in split_observed_capability_fields(pairs.get("pdCapabilityObservedFields")):
                    snapshot_pd_capability_observed_field_counts[field_name] += 1
                pd_capability_missing_reason = pairs.get("pdCapabilityMissingReason")
                if pd_capability_missing_reason:
                    snapshot_pd_capability_missing_reason_counts[pd_capability_missing_reason] += 1
                for limitation in split_csv_field(pairs.get("pdCapabilityLimitations")):
                    snapshot_pd_capability_limitation_counts[limitation] += 1

                target_team = pairs.get("targetTeam")
                if target_team:
                    snapshot_target_team_counts[target_team] += 1
                launcher_team = pairs.get("launcherTeam")
                if (
                    launcher_team
                    and target_team
                    and launcher_team not in {"unknown", "none"}
                    and target_team not in {"unknown", "none"}
                    and launcher_team == target_team
                ):
                    snapshot_same_team_target_count += 1

                missing = pairs.get("missing", "unknown")
                if missing and missing != "none":
                    for field_name in missing.split(","):
                        field_name = field_name.strip()
                        if field_name:
                            snapshot_missing_counts[field_name] += 1

                if summary.first_snapshot_line is None:
                    summary.first_snapshot_line = line_number
                summary.last_snapshot_line = line_number
                continue

            outcome = OUTCOME_RE.match(line)
            if outcome:
                pairs = parse_pairs(outcome.group("pairs"))
                summary.outcome_log_count += 1
                outcome_record_type_counts[pairs.get("recordType", "unknown")] += 1
                outcome_event_level_counts[pairs.get("eventLevel", "unknown")] += 1
                outcome_attribution_level_counts[pairs.get("attributionLevel", "unknown")] += 1
                outcome_identity_bridge_counts[pairs.get("identityBridge", "unknown")] += 1
                outcome_source_hook_counts[pairs.get("sourceHook", "unknown")] += 1
                if summary.first_outcome_line is None:
                    summary.first_outcome_line = line_number
                summary.last_outcome_line = line_number
                continue

            allocation = ALLOCATION_RE.match(line)
            if allocation:
                pairs = parse_pairs(allocation.group("pairs"))
                summary.allocation_log_count += 1

                record_type = pairs.get("recordType", "unknown")
                allocation_record_type_counts[record_type] += 1

                if record_type in CONTROLLED_DRY_RUN_ALLOCATION_RECORD_TYPES:
                    experiment_id = pairs.get("experimentId")
                    if experiment_id:
                        controlled_dry_run_experiment_ids.add(experiment_id)

                if record_type in FLEET_WIDE_REPORT_ONLY_ALLOCATION_RECORD_TYPES:
                    experiment_id = pairs.get("experimentId")
                    if experiment_id:
                        fleet_wide_report_only_experiment_ids.add(experiment_id)
                    fleet_wide_report_only_scope_mode_counts[pairs.get("scopeMode", "unknown")] += 1

                if record_type in FLEET_WIDE_LIVE_ALLOCATION_RECORD_TYPES:
                    experiment_id = pairs.get("experimentId")
                    if experiment_id:
                        fleet_wide_live_experiment_ids.add(experiment_id)
                    fleet_wide_live_scope_mode_counts[pairs.get("scopeMode", "unknown")] += 1

                if record_type in FLEET_WIDE_COMMAND_AUTHORITY_ALLOCATION_RECORD_TYPES:
                    experiment_id = pairs.get("experimentId")
                    if experiment_id:
                        fleet_wide_command_authority_experiment_ids.add(experiment_id)
                    fleet_wide_command_authority_scope_mode_counts[pairs.get("scopeMode", "unknown")] += 1

                if record_type in FLEET_WIDE_BOUNDED_LIVE_ALLOCATION_RECORD_TYPES:
                    experiment_id = pairs.get("experimentId")
                    if experiment_id:
                        fleet_wide_bounded_live_experiment_ids.add(experiment_id)
                    fleet_wide_bounded_live_scope_mode_counts[pairs.get("scopeMode", "unknown")] += 1

                if record_type == "dryRunExperiment":
                    experiment_id = pairs.get("experimentId")
                    if experiment_id:
                        controlled_selected_group_members_by_experiment[experiment_id] = format_group_members(
                            pairs.get("selectedShipIds"),
                            pairs.get("selectedShipNames"),
                            pairs.get("selectedShipTeams"),
                        )
                    controlled_dry_run_selected_ship_counts[pairs.get("selectedShipCount", "unknown")] += 1
                    controlled_dry_run_missing_reason_counts[
                        pairs.get("selectedScopeMissingReason", "unknown")
                    ] += 1
                    selected_count = try_parse_int(pairs.get("selectedShipCount"))
                    command_scope_count = try_parse_int(pairs.get("commandScopeShipCount"))
                    command_scope_source = pairs.get("commandScopeSource", "")
                    selected_scope_source_visible = (
                        "selectedFriendlyShip" in command_scope_source
                        or "groupSelectedFriendlyShips" in command_scope_source
                    )
                    if (
                        selected_count is not None
                        and command_scope_count is not None
                        and selected_count != command_scope_count
                        and selected_scope_source_visible
                    ):
                        controlled_live_apply_mismatch_counts["selectedScopeCommandScopeCountMismatch"] += 1

                if record_type == "dryRunCommandCandidate":
                    controlled_dry_run_candidate_classification_counts[
                        pairs.get("classification", "unknown")
                    ] += 1
                    controlled_dry_run_candidate_reason_counts[pairs.get("reason", "unknown")] += 1
                    candidate_source = pairs.get("candidateSource")
                    if candidate_source:
                        controlled_dry_run_candidate_source_counts[candidate_source] += 1
                    controlled_dry_run_command_scope_source_counts[
                        pairs.get("commandScopeSource", "unknown")
                    ] += 1
                    controlled_dry_run_command_scope_missing_reason_counts[
                        pairs.get("commandScopeMissingReason", "unknown")
                    ] += 1
                    if pairs.get("scopeViolation", "False").lower() == "true":
                        controlled_dry_run_scope_violations += 1

                if record_type == "dryRunApplyGate":
                    gate_result = pairs.get("gateResult", "unknown")
                    controlled_dry_run_apply_gate_result_counts[gate_result] += 1
                    block_reason = pairs.get("blockReason", "unknown")
                    if gate_result == "blocked":
                        controlled_dry_run_safety_gate_blocked_commands += 1
                        controlled_dry_run_safety_gate_reason_counts[block_reason] += 1

                if record_type == "dryRunResult":
                    controlled_dry_run_intended_commands += try_parse_int(pairs.get("intendedCommands")) or 0
                    controlled_dry_run_skipped_commands += try_parse_int(pairs.get("skippedCommands")) or 0
                    controlled_dry_run_applied_commands += try_parse_int(pairs.get("appliedCommands")) or 0
                    controlled_dry_run_failed_commands += try_parse_int(pairs.get("failedCommands")) or 0
                    controlled_dry_run_result_safety_gate_blocked_commands += (
                        try_parse_int(pairs.get("safetyGateBlockedCommands")) or 0
                    )

                if record_type == "fleetWideDryRunExperiment":
                    fleet_wide_report_only_eligible_launchers += try_parse_int(pairs.get("eligibleLaunchers")) or 0
                    fleet_wide_report_only_excluded_launchers += try_parse_int(pairs.get("excludedLaunchers")) or 0
                    fleet_wide_report_only_visible_hostile_targets += (
                        try_parse_int(pairs.get("visibleHostileTargets")) or 0
                    )
                    fleet_wide_report_only_candidate_rows += try_parse_int(pairs.get("candidateRows")) or 0
                    fleet_wide_report_only_emitted_candidate_rows += (
                        try_parse_int(pairs.get("emittedCandidateRows")) or 0
                    )
                    fleet_wide_report_only_eligible_candidate_rows += (
                        try_parse_int(pairs.get("eligibleCandidateRows")) or 0
                    )
                    fleet_wide_report_only_cap_would_block_candidates += (
                        try_parse_int(pairs.get("capWouldBlockCandidates")) or 0
                    )
                    fleet_wide_report_only_missing_evidence_candidates += (
                        try_parse_int(pairs.get("missingAllocatorEvidenceCandidates")) or 0
                    )
                    fleet_wide_report_only_applied_commands += try_parse_int(pairs.get("appliedCommands")) or 0
                    source = pairs.get("fleetEligibilitySource")
                    if source:
                        fleet_wide_report_only_source_counts[source] += 1
                    target_source = pairs.get("visibleTargetSource")
                    if target_source:
                        fleet_wide_report_only_target_source_counts[target_source] += 1

                if record_type == "fleetWideLauncher":
                    fleet_wide_report_only_launcher_classification_counts[
                        pairs.get("classification", "unknown")
                    ] += 1
                    fleet_wide_report_only_launcher_reason_counts[pairs.get("reason", "unknown")] += 1

                if record_type == "fleetWideTarget":
                    fleet_wide_report_only_target_classification_counts[
                        pairs.get("classification", "unknown")
                    ] += 1
                    fleet_wide_report_only_target_reason_counts[pairs.get("reason", "unknown")] += 1

                if record_type == "fleetWideCommandCandidate":
                    fleet_wide_report_only_candidate_classification_counts[
                        pairs.get("classification", "unknown")
                    ] += 1
                    fleet_wide_report_only_candidate_reason_counts[pairs.get("reason", "unknown")] += 1
                    candidate_source = pairs.get("candidateSource")
                    if candidate_source:
                        fleet_wide_report_only_candidate_source_counts[candidate_source] += 1

                if record_type == "fleetWideResult":
                    fleet_wide_report_only_applied_commands += try_parse_int(pairs.get("appliedCommands")) or 0

                if record_type == "fleetWideLiveCommandPathStatus":
                    fleet_wide_live_command_path_status_counts[
                        pairs.get("fleetWideLiveCommandPathStatus", "unknown")
                    ] += 1
                    fleet_wide_live_re_gate_status_counts[pairs.get("reGateStatus", "unknown")] += 1
                    fleet_wide_live_applied_commands += try_parse_int(pairs.get("appliedCommands")) or 0

                if record_type == "fleetWideLiveApplyDecision":
                    fleet_wide_live_decision_counts[pairs.get("decision", pairs.get("result", "unknown"))] += 1
                    fleet_wide_live_reason_counts[pairs.get("reason", "unknown")] += 1
                    candidate_source = pairs.get("candidateSource")
                    if candidate_source:
                        fleet_wide_live_candidate_source_counts[candidate_source] += 1
                    fleet_wide_live_applied_commands += try_parse_int(pairs.get("appliedCommands")) or 0
                    fleet_wide_live_failed_commands += try_parse_int(pairs.get("failedCommands")) or 0

                if record_type == "fleetWideLiveResult":
                    fleet_wide_live_candidate_rows += try_parse_int(pairs.get("candidateRows")) or 0
                    fleet_wide_live_emitted_decision_rows += (
                        try_parse_int(pairs.get("emittedDecisionRows")) or 0
                    )
                    fleet_wide_live_allocator_evidence_candidates += (
                        try_parse_int(pairs.get("allocatorEvidenceCandidates")) or 0
                    )
                    fleet_wide_live_cap_blocked_candidates += (
                        try_parse_int(pairs.get("capBlockedCandidates")) or 0
                    )
                    fleet_wide_live_missing_evidence_candidates += (
                        try_parse_int(pairs.get("missingEvidenceCandidates")) or 0
                    )
                    fleet_wide_live_re_blocked_candidates += (
                        try_parse_int(pairs.get("reBlockedCandidates")) or 0
                    )
                    fleet_wide_live_reason_counts[pairs.get("resultReason", "unknown")] += 1
                    fleet_wide_live_applied_commands += try_parse_int(pairs.get("appliedCommands")) or 0
                    fleet_wide_live_failed_commands += try_parse_int(pairs.get("failedCommands")) or 0

                if record_type in FLEET_WIDE_COMMAND_AUTHORITY_ALLOCATION_RECORD_TYPES:
                    relation = pairs.get("launcherSelectionRelation")
                    if relation:
                        fleet_wide_command_authority_selection_relation_counts[relation] += 1
                    correlation = pairs.get("controlledCommandCorrelation")
                    if correlation:
                        fleet_wide_command_authority_correlation_counts[correlation] += 1

                if record_type == "fleetWideCommandAuthorityResult":
                    fleet_wide_command_authority_result_counts[pairs.get("result", "unknown")] += 1
                    fleet_wide_command_authority_reason_counts[pairs.get("reason", "unknown")] += 1
                    fleet_wide_command_authority_applied_commands += (
                        try_parse_int(pairs.get("appliedCommands")) or 0
                    )
                    fleet_wide_command_authority_failed_commands += (
                        try_parse_int(pairs.get("failedCommands")) or 0
                    )

                if record_type in FLEET_WIDE_BOUNDED_LIVE_ALLOCATION_RECORD_TYPES:
                    relation = pairs.get("launcherSelectionRelation")
                    if relation:
                        fleet_wide_bounded_live_selection_relation_counts[relation] += 1
                    correlation = pairs.get("controlledCommandCorrelation")
                    if correlation:
                        fleet_wide_bounded_live_correlation_counts[correlation] += 1
                    denominator_text = pairs.get("targetAlternativeDenominator")
                    if denominator_text:
                        fleet_wide_bounded_live_target_alternative_denominator_counts[
                            denominator_text
                        ] += 1
                    evidence = pairs.get("targetAlternativeEvidence")
                    if evidence:
                        fleet_wide_bounded_live_target_alternative_evidence_counts[evidence] += 1
                    feature_evidence = pairs.get("targetAlternativeFeatureEvidence")
                    if feature_evidence:
                        fleet_wide_bounded_live_target_alternative_feature_evidence_counts[
                            feature_evidence
                        ] += 1
                    selected_score_space = pairs.get("selectedTargetScoreSpace")
                    if selected_score_space:
                        fleet_wide_bounded_live_selected_target_score_space_counts[
                            selected_score_space
                        ] += 1
                    alternative_score_space = pairs.get("targetAlternativeScoreSpace")
                    if alternative_score_space:
                        fleet_wide_bounded_live_target_alternative_score_space_counts[
                            alternative_score_space
                        ] += 1
                    rank_space = pairs.get("selectedTargetRankComparisonSpace")
                    if rank_space:
                        fleet_wide_bounded_live_selected_target_rank_comparison_space_counts[
                            rank_space
                        ] += 1
                    rank_level = pairs.get("selectedTargetRankLevel")
                    if rank_level:
                        fleet_wide_bounded_live_selected_target_rank_level_counts[
                            rank_level
                        ] += 1
                    rank_confidence = pairs.get("selectedTargetRankConfidence")
                    if rank_confidence:
                        fleet_wide_bounded_live_selected_target_rank_confidence_counts[
                            rank_confidence
                        ] += 1
                    in_flight_confidence = pairs.get(
                        "selectedTargetPriorMissileInFlightEstimateConfidence"
                    )
                    if in_flight_confidence:
                        fleet_wide_bounded_live_prior_in_flight_confidence_counts[
                            in_flight_confidence
                        ] += 1
                    in_flight_bound = pairs.get("selectedTargetPriorMissileInFlightEstimateBound")
                    if in_flight_bound:
                        fleet_wide_bounded_live_prior_in_flight_bound_counts[
                            in_flight_bound
                        ] += 1
                    in_flight_attribution = pairs.get(
                        "selectedTargetPriorMissileInFlightTargetAttribution"
                    )
                    if in_flight_attribution:
                        fleet_wide_bounded_live_prior_in_flight_target_attribution_counts[
                            in_flight_attribution
                        ] += 1
                    pressure_decision = pairs.get("boundedLivePressureDecision")
                    if pressure_decision:
                        fleet_wide_bounded_live_pressure_decision_counts[
                            pressure_decision
                        ] += 1
                    pressure_reason = pairs.get("boundedLivePressureDecisionReason")
                    if pressure_reason:
                        fleet_wide_bounded_live_pressure_decision_reason_counts[
                            pressure_reason
                        ] += 1
                    pressure_evidence = pairs.get("boundedLiveDecisionInFlightEvidenceQuality")
                    if pressure_evidence:
                        fleet_wide_bounded_live_pressure_evidence_counts[
                            pressure_evidence
                        ] += 1
                    pressure_above_threshold = (
                        pairs.get("boundedLiveDecisionPressureAtOrAboveThreshold", "")
                        .strip()
                        .lower()
                    )
                    if pressure_above_threshold == "true":
                        if pressure_decision == "retargeted":
                            fleet_wide_bounded_live_retargeted_above_threshold += 1
                        elif pressure_decision == "retained":
                            fleet_wide_bounded_live_retained_above_threshold += 1
                    if (try_parse_int(pairs.get("targetAlternativeCountTruncated")) or 0) > 0:
                        fleet_wide_bounded_live_target_alternative_truncated_records += 1
                    fleet_wide_bounded_live_applied_commands += (
                        try_parse_int(pairs.get("appliedCommands")) or 0
                    )
                    fleet_wide_bounded_live_failed_commands += (
                        try_parse_int(pairs.get("failedCommands")) or 0
                    )

                if record_type == "fleetWideBoundedLiveResult":
                    fleet_wide_bounded_live_result_counts[pairs.get("result", "unknown")] += 1
                    fleet_wide_bounded_live_reason_counts[pairs.get("reason", "unknown")] += 1
                    if pairs.get("result") == "applied":
                        denominator = try_parse_int(pairs.get("targetAlternativeDenominator"))
                        if denominator is None:
                            fleet_wide_bounded_live_applied_with_unknown_target_alternative_denominator += 1
                        else:
                            fleet_wide_bounded_live_applied_with_target_alternative_denominator += 1
                            if denominator > 1:
                                fleet_wide_bounded_live_applied_with_target_alternative_denominator_gt_one += 1

                if record_type in (
                    APPLIED_ALLOCATION_RECORD_TYPES | SKIPPED_ALLOCATION_RECORD_TYPES | FAILED_ALLOCATION_RECORD_TYPES
                ) and pairs.get("experimentId"):
                    experiment_id = pairs["experimentId"]
                    ship_key = ship_key_from_pairs(pairs)
                    controlled_live_apply_attempts += 1
                    controlled_live_apply_reason_counts[pairs.get("reason", "unknown")] += 1
                    controlled_live_apply_path_counts[pairs.get("commandPath", "unknown")] += 1
                    candidate_source = pairs.get("candidateSource")
                    if candidate_source:
                        controlled_live_apply_candidate_source_counts[candidate_source] += 1
                    if record_type in APPLIED_ALLOCATION_RECORD_TYPES:
                        controlled_live_apply_applied += 1
                        controlled_live_apply_counts_by_experiment[experiment_id]["applied"] += 1
                        controlled_live_apply_counts_by_ship[ship_key]["applied"] += 1
                    elif record_type in SKIPPED_ALLOCATION_RECORD_TYPES:
                        controlled_live_apply_skipped += 1
                        controlled_live_apply_counts_by_experiment[experiment_id]["skipped"] += 1
                        controlled_live_apply_counts_by_ship[ship_key]["skipped"] += 1
                    else:
                        controlled_live_apply_failed += 1
                        controlled_live_apply_counts_by_experiment[experiment_id]["failed"] += 1
                        controlled_live_apply_counts_by_ship[ship_key]["failed"] += 1

                    assigned_shots = first_parse_int(pairs.get("missilesAssigned"), pairs.get("assignedShots"))
                    spent_shots = first_parse_int(pairs.get("missilesSpent"))
                    if assigned_shots is not None:
                        controlled_live_apply_assigned_shots_by_ship[ship_key] += assigned_shots
                    if spent_shots is None:
                        controlled_live_apply_spent_unknown_by_ship[ship_key] += 1
                    else:
                        controlled_live_apply_spent_shots_by_ship[ship_key] += spent_shots
                    if assigned_shots is not None and spent_shots is not None and assigned_shots != spent_shots:
                        controlled_live_apply_mismatch_counts["assignedShotsSpentShotsMismatch"] += 1

                status = pairs.get("status")
                if status and record_type == "cycle":
                    allocation_status_counts[status] += 1

                missing = pairs.get("missingInputs")
                missing_inputs = split_csv_field(missing)
                for field_name in missing_inputs:
                    allocation_missing_input_counts[field_name] += 1
                    if record_type == "cycle":
                        cycle_missing_input_counts[field_name] += 1

                ammo_gate_budget_evidence_source = pairs.get("ammoGateBudgetEvidenceSource")
                if ammo_gate_budget_evidence_source:
                    allocation_ammo_gate_budget_evidence_source_counts[ammo_gate_budget_evidence_source] += 1
                    if record_type == "cycle":
                        cycle_ammo_gate_budget_evidence_source_counts[ammo_gate_budget_evidence_source] += 1

                ammo_gate_budget_missing_reason = pairs.get("ammoGateBudgetMissingReason")
                if ammo_gate_budget_missing_reason:
                    allocation_ammo_gate_budget_missing_reason_counts[ammo_gate_budget_missing_reason] += 1
                    if record_type == "cycle":
                        cycle_ammo_gate_budget_missing_reason_counts[ammo_gate_budget_missing_reason] += 1

                ammo_evidence_source = pairs.get("ammoEvidenceSource")
                if ammo_evidence_source:
                    allocation_ammo_evidence_source_counts[ammo_evidence_source] += 1
                    if record_type == "cycle":
                        cycle_ammo_evidence_source_counts[ammo_evidence_source] += 1

                target_velocity_evidence_source = pairs.get("targetVelocityEvidenceSource")
                if target_velocity_evidence_source:
                    allocation_target_velocity_evidence_source_counts[target_velocity_evidence_source] += 1
                    if record_type == "cycle":
                        cycle_target_velocity_evidence_source_counts[target_velocity_evidence_source] += 1
                target_velocity_missing_reason = pairs.get("targetVelocityMissingReason")
                if target_velocity_missing_reason:
                    allocation_target_velocity_missing_reason_counts[target_velocity_missing_reason] += 1
                    if record_type == "cycle":
                        cycle_target_velocity_missing_reason_counts[target_velocity_missing_reason] += 1
                relative_velocity_evidence_source = pairs.get("relativeVelocityEvidenceSource")
                if relative_velocity_evidence_source:
                    allocation_relative_velocity_evidence_source_counts[relative_velocity_evidence_source] += 1
                    if record_type == "cycle":
                        cycle_relative_velocity_evidence_source_counts[relative_velocity_evidence_source] += 1
                relative_velocity_missing_reason = pairs.get("relativeVelocityMissingReason")
                if relative_velocity_missing_reason:
                    allocation_relative_velocity_missing_reason_counts[relative_velocity_missing_reason] += 1
                    if record_type == "cycle":
                        cycle_relative_velocity_missing_reason_counts[relative_velocity_missing_reason] += 1
                pd_weight_evidence_source = pairs.get("pdWeightEvidenceSource")
                if pd_weight_evidence_source:
                    allocation_pd_weight_evidence_source_counts[pd_weight_evidence_source] += 1
                    if record_type == "cycle":
                        cycle_pd_weight_evidence_source_counts[pd_weight_evidence_source] += 1
                pd_weight_default_reason = pairs.get("pdWeightDefaultReason")
                if pd_weight_default_reason:
                    allocation_pd_weight_default_reason_counts[pd_weight_default_reason] += 1
                    if record_type == "cycle":
                        cycle_pd_weight_default_reason_counts[pd_weight_default_reason] += 1
                pd_weight_missing_reason = pairs.get("pdWeightMissingReason")
                if pd_weight_missing_reason:
                    allocation_pd_weight_missing_reason_counts[pd_weight_missing_reason] += 1
                    if record_type == "cycle":
                        cycle_pd_weight_missing_reason_counts[pd_weight_missing_reason] += 1
                pd_evidence_quality = pairs.get("pdEvidenceQuality")
                if pd_evidence_quality:
                    allocation_pd_evidence_quality_counts[pd_evidence_quality] += 1
                    if record_type == "cycle":
                        cycle_pd_evidence_quality_counts[pd_evidence_quality] += 1
                pd_capability_evidence_source = pairs.get("pdCapabilityEvidenceSource")
                if pd_capability_evidence_source:
                    allocation_pd_capability_evidence_source_counts[pd_capability_evidence_source] += 1
                    if record_type == "cycle":
                        cycle_pd_capability_evidence_source_counts[pd_capability_evidence_source] += 1
                for field_name in split_observed_capability_fields(pairs.get("pdCapabilityObservedFields")):
                    allocation_pd_capability_observed_field_counts[field_name] += 1
                    if record_type == "cycle":
                        cycle_pd_capability_observed_field_counts[field_name] += 1
                pd_capability_missing_reason = pairs.get("pdCapabilityMissingReason")
                if pd_capability_missing_reason:
                    allocation_pd_capability_missing_reason_counts[pd_capability_missing_reason] += 1
                    if record_type == "cycle":
                        cycle_pd_capability_missing_reason_counts[pd_capability_missing_reason] += 1
                for limitation in split_csv_field(pairs.get("pdCapabilityLimitations")):
                    allocation_pd_capability_limitation_counts[limitation] += 1
                    if record_type == "cycle":
                        cycle_pd_capability_limitation_counts[limitation] += 1

                rejection_reason = pairs.get("rejectionReason")
                if rejection_reason:
                    allocation_rejection_reason_counts[rejection_reason] += 1
                no_op_reason = pairs.get("noOpReason")
                if no_op_reason:
                    allocation_no_op_reason_counts[no_op_reason] += 1

                assigned_shots = pairs.get("assignedShots")
                if assigned_shots:
                    allocation_assigned_shots_counts[assigned_shots] += 1

                if record_type == "cycle":
                    target_count = try_parse_int(pairs.get("targetCount"))
                    if target_count is not None:
                        cycle_target_counts.append(target_count)
                    ammo_gate_budget_shots = try_parse_int(pairs.get("totalAmmoGateBudgetShots"))
                    ammo_gate_budget_values.append(ammo_gate_budget_shots)
                    assigned_shot_values.append(try_parse_int(pairs.get("assignedShots")))
                    unassigned_shot_values.append(try_parse_int(pairs.get("unassignedShots")))
                    if ammo_gate_budget_shots is None and is_ammo_only_budget_reason(ammo_gate_budget_missing_reason):
                        cycle_ammo_only_budget_count += 1
                    if ammo_gate_budget_shots is None and (
                        "ammoGateBudgetShots" in missing_inputs or ammo_gate_budget_missing_reason is not None
                    ):
                        cycle_missing_ammo_gate_budget_evidence_count += 1
                    pd_weight_defaulted = pairs.get("pdWeightDefaulted", "unknown").strip().lower()
                    if pd_weight_defaulted not in {"true", "false"}:
                        pd_weight_defaulted = "unknown"
                    cycle_pd_weight_defaulted_counts[pd_weight_defaulted] += 1

                if record_type in {"allocation", "rejection", "noOp"}:
                    kill_size = try_parse_float(pairs.get("killSize"))
                    saturation_size = try_parse_float(pairs.get("saturationSize"))
                    launch_window_score = try_parse_float(pairs.get("launchWindowScore"))
                    score_per_shot = try_parse_float(pairs.get("scorePerShot"))
                    has_package_metric = record_type == "allocation" or any(
                        value is not None and value > 0 for value in (kill_size, saturation_size)
                    )
                    if has_package_metric and kill_size is not None:
                        kill_size_values.append(kill_size)
                    if has_package_metric and saturation_size is not None:
                        saturation_size_values.append(saturation_size)
                    if has_package_metric and launch_window_score is not None:
                        launch_window_score_values.append(launch_window_score)
                    if has_package_metric and score_per_shot is not None:
                        score_per_shot_values.append(score_per_shot)

                    target_value = try_parse_float(pairs.get("targetValue"))
                    cycle_id = pairs.get("cycleId", "unknown")
                    if target_value is not None:
                        if record_type == "allocation":
                            cycle_allocated_target_values.setdefault(cycle_id, []).append(target_value)
                        elif record_type == "rejection":
                            cycle_rejected_target_values.setdefault(cycle_id, []).append(target_value)

                if record_type == "allocation":
                    assigned = try_parse_int(pairs.get("assignedShots"))
                    saturation = try_parse_int(pairs.get("saturationSize"))
                    kill = try_parse_int(pairs.get("killSize"))
                    if assigned is not None and saturation is not None and 0 < assigned < saturation:
                        allocation_partial_saturation_count += 1
                    if assigned is not None and kill is not None and assigned > kill:
                        allocation_overkill_count += 1

                if summary.first_allocation_line is None:
                    summary.first_allocation_line = line_number
                summary.last_allocation_line = line_number
                continue

            if is_issue_line(line) and len(summary.issues) < max_issues:
                summary.issues.append(LineHit(line=line_number, text=line))

    summary.hook_counts = dict(sorted(hook_counts.items()))
    summary.missile_try_fire_pre_fire_field_counts = dict(sorted(missile_try_fire_pre_fire_field_counts.items()))
    summary.missile_try_fire_pre_fire_ammo_source_counts = dict(
        sorted(missile_try_fire_pre_fire_ammo_source_counts.items())
    )
    summary.missile_try_fire_pre_post_ammo_delta_counts = dict(
        sorted(missile_try_fire_pre_post_ammo_delta_counts.items(), key=lambda item: int(item[0]))
    )
    summary.controlled_command_launch_context_rows = controlled_command_launch_context_rows
    summary.controlled_command_launch_correlation_counts = dict(
        sorted(controlled_command_launch_correlation_counts.items())
    )
    summary.controlled_command_launch_observed_spent_numeric_count = (
        controlled_command_launch_observed_spent_numeric_count
    )
    summary.snapshot_source_counts = dict(sorted(snapshot_source_counts.items()))
    summary.snapshot_missing_counts = dict(sorted(snapshot_missing_counts.items()))
    summary.snapshot_ammo_gate_budget_shots_counts = dict(sorted(snapshot_ammo_gate_budget_shots_counts.items()))
    summary.snapshot_ammo_gate_budget_evidence_source_counts = dict(
        sorted(snapshot_ammo_gate_budget_evidence_source_counts.items())
    )
    summary.snapshot_ammo_gate_budget_missing_reason_counts = dict(sorted(snapshot_ammo_gate_budget_missing_reason_counts.items()))
    summary.snapshot_ammo_evidence_source_counts = dict(sorted(snapshot_ammo_evidence_source_counts.items()))
    summary.snapshot_live_weapon_state_counts = dict(sorted(snapshot_live_weapon_state_counts.items()))
    summary.snapshot_target_identity_source_counts = dict(sorted(snapshot_target_identity_source_counts.items()))
    summary.snapshot_target_velocity_evidence_source_counts = dict(
        sorted(snapshot_target_velocity_evidence_source_counts.items())
    )
    summary.snapshot_target_velocity_missing_reason_counts = dict(
        sorted(snapshot_target_velocity_missing_reason_counts.items())
    )
    summary.snapshot_relative_velocity_evidence_source_counts = dict(
        sorted(snapshot_relative_velocity_evidence_source_counts.items())
    )
    summary.snapshot_relative_velocity_missing_reason_counts = dict(
        sorted(snapshot_relative_velocity_missing_reason_counts.items())
    )
    summary.snapshot_pd_weight_evidence_source_counts = dict(sorted(snapshot_pd_weight_evidence_source_counts.items()))
    summary.snapshot_pd_weight_default_reason_counts = dict(sorted(snapshot_pd_weight_default_reason_counts.items()))
    summary.snapshot_pd_weight_missing_reason_counts = dict(sorted(snapshot_pd_weight_missing_reason_counts.items()))
    summary.snapshot_pd_evidence_quality_counts = dict(sorted(snapshot_pd_evidence_quality_counts.items()))
    summary.snapshot_pd_capability_evidence_source_counts = dict(
        sorted(snapshot_pd_capability_evidence_source_counts.items())
    )
    summary.snapshot_pd_capability_observed_field_counts = dict(
        sorted(snapshot_pd_capability_observed_field_counts.items())
    )
    summary.snapshot_pd_capability_missing_reason_counts = dict(
        sorted(snapshot_pd_capability_missing_reason_counts.items())
    )
    summary.snapshot_pd_capability_limitation_counts = dict(
        sorted(snapshot_pd_capability_limitation_counts.items())
    )
    summary.snapshot_target_counts = dict(snapshot_target_counts.most_common(12))
    summary.snapshot_target_team_counts = dict(sorted(snapshot_target_team_counts.items()))
    summary.snapshot_same_team_target_count = snapshot_same_team_target_count
    summary.outcome_record_type_counts = dict(sorted(outcome_record_type_counts.items()))
    summary.outcome_event_level_counts = dict(sorted(outcome_event_level_counts.items()))
    summary.outcome_attribution_level_counts = dict(sorted(outcome_attribution_level_counts.items()))
    summary.outcome_identity_bridge_counts = dict(sorted(outcome_identity_bridge_counts.items()))
    summary.outcome_source_hook_counts = dict(sorted(outcome_source_hook_counts.items()))
    summary.allocation_record_type_counts = dict(sorted(allocation_record_type_counts.items()))
    summary.allocation_status_counts = dict(sorted(allocation_status_counts.items()))
    summary.allocation_missing_input_counts = dict(sorted(allocation_missing_input_counts.items()))
    summary.allocation_ammo_gate_budget_evidence_source_counts = dict(
        sorted(allocation_ammo_gate_budget_evidence_source_counts.items())
    )
    summary.allocation_ammo_gate_budget_missing_reason_counts = dict(
        sorted(allocation_ammo_gate_budget_missing_reason_counts.items())
    )
    summary.allocation_ammo_evidence_source_counts = dict(sorted(allocation_ammo_evidence_source_counts.items()))
    summary.allocation_target_velocity_evidence_source_counts = dict(
        sorted(allocation_target_velocity_evidence_source_counts.items())
    )
    summary.allocation_target_velocity_missing_reason_counts = dict(
        sorted(allocation_target_velocity_missing_reason_counts.items())
    )
    summary.allocation_relative_velocity_evidence_source_counts = dict(
        sorted(allocation_relative_velocity_evidence_source_counts.items())
    )
    summary.allocation_relative_velocity_missing_reason_counts = dict(
        sorted(allocation_relative_velocity_missing_reason_counts.items())
    )
    summary.allocation_pd_weight_evidence_source_counts = dict(sorted(allocation_pd_weight_evidence_source_counts.items()))
    summary.allocation_pd_weight_default_reason_counts = dict(sorted(allocation_pd_weight_default_reason_counts.items()))
    summary.allocation_pd_weight_missing_reason_counts = dict(sorted(allocation_pd_weight_missing_reason_counts.items()))
    summary.allocation_pd_evidence_quality_counts = dict(sorted(allocation_pd_evidence_quality_counts.items()))
    summary.allocation_pd_capability_evidence_source_counts = dict(
        sorted(allocation_pd_capability_evidence_source_counts.items())
    )
    summary.allocation_pd_capability_observed_field_counts = dict(
        sorted(allocation_pd_capability_observed_field_counts.items())
    )
    summary.allocation_pd_capability_missing_reason_counts = dict(
        sorted(allocation_pd_capability_missing_reason_counts.items())
    )
    summary.allocation_pd_capability_limitation_counts = dict(
        sorted(allocation_pd_capability_limitation_counts.items())
    )
    summary.allocation_rejection_reason_counts = sorted_count_dict(allocation_rejection_reason_counts, limit=12)
    summary.allocation_no_op_reason_counts = sorted_count_dict(allocation_no_op_reason_counts, limit=12)
    summary.allocation_assigned_shots_counts = dict(
        sorted(allocation_assigned_shots_counts.items(), key=sort_numeric_text_count)
    )
    allocation_summary = build_allocation_battle_summary(
        allocation_record_type_counts,
        allocation_status_counts,
        allocation_rejection_reason_counts,
        allocation_no_op_reason_counts,
        cycle_missing_input_counts,
        cycle_target_counts,
        ammo_gate_budget_values,
        assigned_shot_values,
        unassigned_shot_values,
        kill_size_values,
        saturation_size_values,
        launch_window_score_values,
        score_per_shot_values,
        allocation_partial_saturation_count,
        allocation_overkill_count,
        cycle_allocated_target_values,
        cycle_rejected_target_values,
        cycle_ammo_gate_budget_evidence_source_counts,
        cycle_ammo_gate_budget_missing_reason_counts,
        cycle_ammo_evidence_source_counts,
        cycle_ammo_only_budget_count,
        cycle_missing_ammo_gate_budget_evidence_count,
        cycle_target_velocity_evidence_source_counts,
        cycle_target_velocity_missing_reason_counts,
        cycle_relative_velocity_evidence_source_counts,
        cycle_relative_velocity_missing_reason_counts,
        cycle_pd_weight_evidence_source_counts,
        cycle_pd_weight_default_reason_counts,
        cycle_pd_weight_missing_reason_counts,
        cycle_pd_weight_defaulted_counts,
        cycle_pd_evidence_quality_counts,
        cycle_pd_capability_evidence_source_counts,
        cycle_pd_capability_observed_field_counts,
        cycle_pd_capability_missing_reason_counts,
        cycle_pd_capability_limitation_counts,
    )
    allocation_summary.same_team_missile_target_snapshots = snapshot_same_team_target_count
    if snapshot_same_team_target_count:
        same_team_pattern = f"same-team missile target snapshots: {snapshot_same_team_target_count}"
        if allocation_summary.suspicious_patterns == ["none"]:
            allocation_summary.suspicious_patterns = [same_team_pattern]
        else:
            allocation_summary.suspicious_patterns.append(same_team_pattern)
    allocation_summary.controlled_dry_run_experiments = allocation_record_type_counts.get("dryRunExperiment", 0)
    allocation_summary.controlled_dry_run_intents = allocation_record_type_counts.get("dryRunIntent", 0)
    allocation_summary.controlled_dry_run_command_candidates = allocation_record_type_counts.get(
        "dryRunCommandCandidate",
        0,
    )
    allocation_summary.controlled_dry_run_apply_gate_records = allocation_record_type_counts.get(
        "dryRunApplyGate",
        0,
    )
    allocation_summary.controlled_dry_run_results = allocation_record_type_counts.get("dryRunResult", 0)
    allocation_summary.controlled_dry_run_experiment_ids = sorted(controlled_dry_run_experiment_ids)
    allocation_summary.controlled_dry_run_intended_commands = controlled_dry_run_intended_commands
    allocation_summary.controlled_dry_run_skipped_commands = controlled_dry_run_skipped_commands
    allocation_summary.controlled_dry_run_applied_commands = controlled_dry_run_applied_commands
    allocation_summary.controlled_dry_run_failed_commands = controlled_dry_run_failed_commands
    allocation_summary.controlled_dry_run_safety_gate_blocked_commands = (
        max(
            controlled_dry_run_safety_gate_blocked_commands,
            controlled_dry_run_result_safety_gate_blocked_commands,
        )
    )
    allocation_summary.controlled_dry_run_candidate_classification_counts = dict(
        sorted(controlled_dry_run_candidate_classification_counts.items())
    )
    allocation_summary.controlled_dry_run_candidate_reason_counts = dict(
        sorted(controlled_dry_run_candidate_reason_counts.items())
    )
    allocation_summary.controlled_dry_run_candidate_source_counts = dict(
        sorted(controlled_dry_run_candidate_source_counts.items())
    )
    allocation_summary.controlled_dry_run_apply_gate_result_counts = dict(
        sorted(controlled_dry_run_apply_gate_result_counts.items())
    )
    allocation_summary.controlled_dry_run_safety_gate_reason_counts = dict(
        sorted(controlled_dry_run_safety_gate_reason_counts.items())
    )
    allocation_summary.controlled_dry_run_command_scope_source_counts = dict(
        sorted(controlled_dry_run_command_scope_source_counts.items())
    )
    allocation_summary.controlled_dry_run_command_scope_missing_reason_counts = dict(
        sorted(controlled_dry_run_command_scope_missing_reason_counts.items())
    )
    allocation_summary.controlled_dry_run_scope_violations = controlled_dry_run_scope_violations
    allocation_summary.controlled_dry_run_selected_ship_counts = dict(
        sorted(controlled_dry_run_selected_ship_counts.items(), key=sort_numeric_text_count)
    )
    allocation_summary.controlled_dry_run_missing_reason_counts = dict(
        sorted(controlled_dry_run_missing_reason_counts.items())
    )
    allocation_summary.fleet_wide_report_only_experiments = allocation_record_type_counts.get(
        "fleetWideDryRunExperiment",
        0,
    )
    allocation_summary.fleet_wide_report_only_launchers = allocation_record_type_counts.get("fleetWideLauncher", 0)
    allocation_summary.fleet_wide_report_only_targets = allocation_record_type_counts.get("fleetWideTarget", 0)
    allocation_summary.fleet_wide_report_only_command_candidates = allocation_record_type_counts.get(
        "fleetWideCommandCandidate",
        0,
    )
    allocation_summary.fleet_wide_report_only_cap_state_records = allocation_record_type_counts.get(
        "fleetWideCapState",
        0,
    )
    allocation_summary.fleet_wide_report_only_results = allocation_record_type_counts.get("fleetWideResult", 0)
    allocation_summary.fleet_wide_report_only_experiment_ids = sorted(fleet_wide_report_only_experiment_ids)
    allocation_summary.fleet_wide_report_only_eligible_launchers = fleet_wide_report_only_eligible_launchers
    allocation_summary.fleet_wide_report_only_excluded_launchers = fleet_wide_report_only_excluded_launchers
    allocation_summary.fleet_wide_report_only_visible_hostile_targets = (
        fleet_wide_report_only_visible_hostile_targets
    )
    allocation_summary.fleet_wide_report_only_candidate_rows = fleet_wide_report_only_candidate_rows
    allocation_summary.fleet_wide_report_only_emitted_candidate_rows = (
        fleet_wide_report_only_emitted_candidate_rows
    )
    allocation_summary.fleet_wide_report_only_eligible_candidate_rows = (
        fleet_wide_report_only_eligible_candidate_rows
    )
    allocation_summary.fleet_wide_report_only_cap_would_block_candidates = (
        fleet_wide_report_only_cap_would_block_candidates
    )
    allocation_summary.fleet_wide_report_only_missing_evidence_candidates = (
        fleet_wide_report_only_missing_evidence_candidates
    )
    allocation_summary.fleet_wide_report_only_applied_commands = fleet_wide_report_only_applied_commands
    allocation_summary.fleet_wide_report_only_launcher_classification_counts = dict(
        sorted(fleet_wide_report_only_launcher_classification_counts.items())
    )
    allocation_summary.fleet_wide_report_only_launcher_reason_counts = dict(
        sorted(fleet_wide_report_only_launcher_reason_counts.items())
    )
    allocation_summary.fleet_wide_report_only_target_classification_counts = dict(
        sorted(fleet_wide_report_only_target_classification_counts.items())
    )
    allocation_summary.fleet_wide_report_only_target_reason_counts = dict(
        sorted(fleet_wide_report_only_target_reason_counts.items())
    )
    allocation_summary.fleet_wide_report_only_candidate_classification_counts = dict(
        sorted(fleet_wide_report_only_candidate_classification_counts.items())
    )
    allocation_summary.fleet_wide_report_only_candidate_reason_counts = dict(
        sorted(fleet_wide_report_only_candidate_reason_counts.items())
    )
    allocation_summary.fleet_wide_report_only_candidate_source_counts = dict(
        sorted(fleet_wide_report_only_candidate_source_counts.items())
    )
    allocation_summary.fleet_wide_report_only_scope_mode_counts = dict(
        sorted(fleet_wide_report_only_scope_mode_counts.items())
    )
    allocation_summary.fleet_wide_report_only_source_counts = dict(
        sorted(fleet_wide_report_only_source_counts.items())
    )
    allocation_summary.fleet_wide_report_only_target_source_counts = dict(
        sorted(fleet_wide_report_only_target_source_counts.items())
    )
    allocation_summary.fleet_wide_live_path_status_records = allocation_record_type_counts.get(
        "fleetWideLiveCommandPathStatus",
        0,
    )
    allocation_summary.fleet_wide_live_decision_records = allocation_record_type_counts.get(
        "fleetWideLiveApplyDecision",
        0,
    )
    allocation_summary.fleet_wide_live_result_records = allocation_record_type_counts.get(
        "fleetWideLiveResult",
        0,
    )
    allocation_summary.fleet_wide_live_experiment_ids = sorted(fleet_wide_live_experiment_ids)
    allocation_summary.fleet_wide_live_scope_mode_counts = dict(
        sorted(fleet_wide_live_scope_mode_counts.items())
    )
    allocation_summary.fleet_wide_live_command_path_status_counts = dict(
        sorted(fleet_wide_live_command_path_status_counts.items())
    )
    allocation_summary.fleet_wide_live_re_gate_status_counts = dict(
        sorted(fleet_wide_live_re_gate_status_counts.items())
    )
    allocation_summary.fleet_wide_live_decision_counts = dict(
        sorted(fleet_wide_live_decision_counts.items())
    )
    allocation_summary.fleet_wide_live_reason_counts = dict(
        sorted(fleet_wide_live_reason_counts.items())
    )
    allocation_summary.fleet_wide_live_candidate_source_counts = dict(
        sorted(fleet_wide_live_candidate_source_counts.items())
    )
    allocation_summary.fleet_wide_live_candidate_rows = fleet_wide_live_candidate_rows
    allocation_summary.fleet_wide_live_emitted_decision_rows = fleet_wide_live_emitted_decision_rows
    allocation_summary.fleet_wide_live_allocator_evidence_candidates = (
        fleet_wide_live_allocator_evidence_candidates
    )
    allocation_summary.fleet_wide_live_cap_blocked_candidates = fleet_wide_live_cap_blocked_candidates
    allocation_summary.fleet_wide_live_missing_evidence_candidates = (
        fleet_wide_live_missing_evidence_candidates
    )
    allocation_summary.fleet_wide_live_re_blocked_candidates = fleet_wide_live_re_blocked_candidates
    allocation_summary.fleet_wide_live_applied_commands = fleet_wide_live_applied_commands
    allocation_summary.fleet_wide_live_failed_commands = fleet_wide_live_failed_commands
    allocation_summary.fleet_wide_command_authority_candidate_records = allocation_record_type_counts.get(
        "fleetWideCommandAuthorityCandidate",
        0,
    )
    allocation_summary.fleet_wide_command_authority_pre_state_records = allocation_record_type_counts.get(
        "fleetWideCommandAuthorityPreState",
        0,
    )
    allocation_summary.fleet_wide_command_authority_result_records = allocation_record_type_counts.get(
        "fleetWideCommandAuthorityResult",
        0,
    )
    allocation_summary.fleet_wide_command_authority_post_state_records = allocation_record_type_counts.get(
        "fleetWideCommandAuthorityPostState",
        0,
    )
    allocation_summary.fleet_wide_command_authority_experiment_ids = sorted(
        fleet_wide_command_authority_experiment_ids
    )
    allocation_summary.fleet_wide_command_authority_scope_mode_counts = dict(
        sorted(fleet_wide_command_authority_scope_mode_counts.items())
    )
    allocation_summary.fleet_wide_command_authority_result_counts = dict(
        sorted(fleet_wide_command_authority_result_counts.items())
    )
    allocation_summary.fleet_wide_command_authority_reason_counts = dict(
        sorted(fleet_wide_command_authority_reason_counts.items())
    )
    allocation_summary.fleet_wide_command_authority_selection_relation_counts = dict(
        sorted(fleet_wide_command_authority_selection_relation_counts.items())
    )
    allocation_summary.fleet_wide_command_authority_correlation_counts = dict(
        sorted(fleet_wide_command_authority_correlation_counts.items())
    )
    allocation_summary.fleet_wide_command_authority_applied_commands = (
        fleet_wide_command_authority_applied_commands
    )
    allocation_summary.fleet_wide_command_authority_failed_commands = (
        fleet_wide_command_authority_failed_commands
    )
    allocation_summary.fleet_wide_bounded_live_candidate_records = allocation_record_type_counts.get(
        "fleetWideBoundedLiveCandidate",
        0,
    )
    allocation_summary.fleet_wide_bounded_live_pre_state_records = allocation_record_type_counts.get(
        "fleetWideBoundedLivePreState",
        0,
    )
    allocation_summary.fleet_wide_bounded_live_result_records = allocation_record_type_counts.get(
        "fleetWideBoundedLiveResult",
        0,
    )
    allocation_summary.fleet_wide_bounded_live_post_state_records = allocation_record_type_counts.get(
        "fleetWideBoundedLivePostState",
        0,
    )
    allocation_summary.fleet_wide_bounded_live_experiment_ids = sorted(
        fleet_wide_bounded_live_experiment_ids
    )
    allocation_summary.fleet_wide_bounded_live_scope_mode_counts = dict(
        sorted(fleet_wide_bounded_live_scope_mode_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_result_counts = dict(
        sorted(fleet_wide_bounded_live_result_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_reason_counts = dict(
        sorted(fleet_wide_bounded_live_reason_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_selection_relation_counts = dict(
        sorted(fleet_wide_bounded_live_selection_relation_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_correlation_counts = dict(
        sorted(fleet_wide_bounded_live_correlation_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_target_alternative_denominator_counts = dict(
        sorted(fleet_wide_bounded_live_target_alternative_denominator_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_target_alternative_evidence_counts = dict(
        sorted(fleet_wide_bounded_live_target_alternative_evidence_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_target_alternative_feature_evidence_counts = dict(
        sorted(fleet_wide_bounded_live_target_alternative_feature_evidence_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_selected_target_score_space_counts = dict(
        sorted(fleet_wide_bounded_live_selected_target_score_space_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_target_alternative_score_space_counts = dict(
        sorted(fleet_wide_bounded_live_target_alternative_score_space_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_selected_target_rank_comparison_space_counts = dict(
        sorted(fleet_wide_bounded_live_selected_target_rank_comparison_space_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_selected_target_rank_level_counts = dict(
        sorted(fleet_wide_bounded_live_selected_target_rank_level_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_selected_target_rank_confidence_counts = dict(
        sorted(fleet_wide_bounded_live_selected_target_rank_confidence_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_prior_in_flight_confidence_counts = dict(
        sorted(fleet_wide_bounded_live_prior_in_flight_confidence_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_prior_in_flight_bound_counts = dict(
        sorted(fleet_wide_bounded_live_prior_in_flight_bound_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_prior_in_flight_target_attribution_counts = dict(
        sorted(fleet_wide_bounded_live_prior_in_flight_target_attribution_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_pressure_decision_counts = dict(
        sorted(fleet_wide_bounded_live_pressure_decision_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_pressure_decision_reason_counts = dict(
        sorted(fleet_wide_bounded_live_pressure_decision_reason_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_pressure_evidence_counts = dict(
        sorted(fleet_wide_bounded_live_pressure_evidence_counts.items())
    )
    allocation_summary.fleet_wide_bounded_live_retained_above_threshold = (
        fleet_wide_bounded_live_retained_above_threshold
    )
    allocation_summary.fleet_wide_bounded_live_retargeted_above_threshold = (
        fleet_wide_bounded_live_retargeted_above_threshold
    )
    allocation_summary.fleet_wide_bounded_live_target_alternative_truncated_records = (
        fleet_wide_bounded_live_target_alternative_truncated_records
    )
    allocation_summary.fleet_wide_bounded_live_applied_with_target_alternative_denominator = (
        fleet_wide_bounded_live_applied_with_target_alternative_denominator
    )
    allocation_summary.fleet_wide_bounded_live_applied_with_target_alternative_denominator_gt_one = (
        fleet_wide_bounded_live_applied_with_target_alternative_denominator_gt_one
    )
    allocation_summary.fleet_wide_bounded_live_applied_with_unknown_target_alternative_denominator = (
        fleet_wide_bounded_live_applied_with_unknown_target_alternative_denominator
    )
    allocation_summary.fleet_wide_bounded_live_applied_commands = (
        fleet_wide_bounded_live_applied_commands
    )
    allocation_summary.fleet_wide_bounded_live_failed_commands = (
        fleet_wide_bounded_live_failed_commands
    )
    allocation_summary.controlled_live_apply_attempts = controlled_live_apply_attempts
    allocation_summary.controlled_live_apply_applied = controlled_live_apply_applied
    allocation_summary.controlled_live_apply_skipped = controlled_live_apply_skipped
    allocation_summary.controlled_live_apply_failed = controlled_live_apply_failed
    allocation_summary.controlled_live_apply_reason_counts = dict(sorted(controlled_live_apply_reason_counts.items()))
    allocation_summary.controlled_live_apply_path_counts = dict(sorted(controlled_live_apply_path_counts.items()))
    allocation_summary.controlled_live_apply_candidate_source_counts = dict(
        sorted(controlled_live_apply_candidate_source_counts.items())
    )
    allocation_summary.controlled_selected_group_members_by_experiment = dict(
        sorted(controlled_selected_group_members_by_experiment.items())
    )
    allocation_summary.controlled_live_apply_counts_by_experiment = sorted_nested_count_dict(
        controlled_live_apply_counts_by_experiment
    )
    allocation_summary.controlled_live_apply_counts_by_ship = sorted_nested_count_dict(
        controlled_live_apply_counts_by_ship
    )
    allocation_summary.controlled_live_apply_assigned_shots_by_ship = dict(
        sorted(controlled_live_apply_assigned_shots_by_ship.items())
    )
    allocation_summary.controlled_live_apply_spent_shots_by_ship = dict(
        sorted(controlled_live_apply_spent_shots_by_ship.items())
    )
    allocation_summary.controlled_live_apply_spent_unknown_by_ship = dict(
        sorted(controlled_live_apply_spent_unknown_by_ship.items())
    )
    allocation_summary.controlled_live_apply_mismatch_counts = dict(
        sorted(controlled_live_apply_mismatch_counts.items())
    )
    summary.allocation_summary = allocation_summary
    if sequences:
        ordered = sorted(sequences)
        summary.first_seq = ordered[0]
        summary.last_seq = ordered[-1]
        summary.duplicate_sequences = sorted(duplicate_sequences)
        gaps: list[str] = []
        previous = ordered[0]
        for current in ordered[1:]:
            if current > previous + 1:
                missing_start = previous + 1
                missing_end = current - 1
                gaps.append(str(missing_start) if missing_start == missing_end else f"{missing_start}-{missing_end}")
            previous = current
        summary.sequence_gaps = gaps

    return summary


def logger_verdict(summary: LogSummary, require_launchlogs: bool, require_snapshots: bool) -> tuple[str, list[str]]:
    """Evaluate whether parsed markers show a healthy logger installation."""
    reasons: list[str] = []

    if not summary.exists:
        return "FAIL", ["Player.log was not found."]

    startup_markers_present = (
        summary.version is not None
        and summary.loaded_line is not None
        and summary.enabled_line is not None
        and summary.active_line is not None
    )

    if summary.version is None:
        reasons.append("MissileWarfare load marker was not found.")
    if summary.loaded_line is None:
        reasons.append("MFC loaded marker was not found.")
    if summary.enabled_line is None:
        reasons.append("MFC enabled marker was not found.")
    if summary.active_line is None:
        reasons.append("Unity Mod Manager Active marker was not found.")
    patched_descriptions = {hook.description for hook in summary.patched_hooks}
    outcome_patch_descriptions = patched_descriptions & OUTCOME_PATCH_DESCRIPTIONS
    outcome_validation_visible = (
        summary.outcome_log_count > 0
        or bool(outcome_patch_descriptions)
        or (
            summary.bootstrap_patched is not None
            and summary.bootstrap_patched > len(REQUIRED_PATCH_DESCRIPTIONS)
        )
    )
    required_patch_count = len(REQUIRED_PATCH_DESCRIPTIONS) + (
        len(OUTCOME_PATCH_DESCRIPTIONS) if outcome_validation_visible else 0
    )

    if summary.bootstrap_skipped != 0 or summary.bootstrap_patched is None or summary.bootstrap_patched < required_patch_count:
        reasons.append(
            f"Expected diagnostics bootstrap patched>={required_patch_count} and skipped=0; "
            f"got patched={summary.bootstrap_patched}, skipped={summary.bootstrap_skipped}."
        )
    missing_required_hooks = sorted(REQUIRED_PATCH_DESCRIPTIONS - patched_descriptions)
    if missing_required_hooks:
        reasons.append("Missing required launch hook patches: " + ", ".join(missing_required_hooks))
    if outcome_validation_visible:
        missing_outcome_hooks = sorted(OUTCOME_PATCH_DESCRIPTIONS - patched_descriptions)
        if missing_outcome_hooks:
            reasons.append("Missing required outcome hook patches: " + ", ".join(missing_outcome_hooks))
    if require_launchlogs and startup_markers_present and summary.launch_log_count == 0:
        reasons.append("No LaunchLog entries were found.")
    if require_snapshots and startup_markers_present and summary.snapshot_log_count == 0:
        reasons.append("No SnapshotLog entries were found.")
    if summary.sequence_gaps:
        reasons.append("LaunchLog sequence gaps found: " + ", ".join(summary.sequence_gaps[:8]))
    if summary.duplicate_sequences:
        reasons.append("Duplicate LaunchLog sequences found: " + ", ".join(map(str, summary.duplicate_sequences[:8])))
    if summary.allocation_summary.same_team_missile_target_snapshots:
        reasons.append(
            "Same-team missile target snapshots found: "
            + str(summary.allocation_summary.same_team_missile_target_snapshots)
        )

    return ("FAIL" if reasons else "OK"), reasons


def format_optional_total(value: int | None) -> str:
    """Format an optional integer total for compact human output."""
    return str(value) if value is not None else "unknown"


def format_metric(value: float | None) -> str:
    """Format a float without noisy trailing zeroes."""
    if value is None:
        return "n/a"

    return f"{value:.3f}".rstrip("0").rstrip(".")


def format_average_median(summary: NumericFieldSummary) -> str:
    """Format average and median fields for a numeric allocation metric."""
    return f"{format_metric(summary.average)} / {format_metric(summary.median)}"


def format_missing_rate(field_name: str, count: int, denominator: int) -> str:
    """Format a missing-input count and percent."""
    if denominator == 0:
        return f"{field_name} {count}/0 (n/a)"

    return f"{field_name} {count}/{denominator} ({(count / denominator) * 100.0:.1f}%)"


def format_count_dict(values: dict[str, int]) -> str:
    """Format a compact deterministic histogram."""
    return ", ".join(f"{key}: {count}" for key, count in values.items()) if values else "none"


def print_allocation_battle_summary(summary: AllocationBattleSummary) -> None:
    """Print compact battle-level allocation diagnostics."""
    print("Allocation summary")
    print(f"- shadow cycles: {summary.shadow_cycles}")
    print(f"- shadow evaluated cycles: {summary.shadow_evaluated_cycles}")
    print(f"- shadow skipped cycles: {summary.shadow_skipped_cycles}")
    print(f"- applied decisions: {summary.applied_decisions}")
    print(f"- skipped decisions: {summary.skipped_decisions}")
    print(f"- failed command applications: {summary.failed_command_applications}")
    if (
        summary.controlled_dry_run_experiments
        or summary.controlled_dry_run_intents
        or summary.controlled_dry_run_command_candidates
        or summary.controlled_dry_run_apply_gate_records
        or summary.controlled_dry_run_results
    ):
        print(f"- controlled dry-run experiments: {summary.controlled_dry_run_experiments}")
        print(f"- controlled dry-run intents: {summary.controlled_dry_run_intents}")
        print(f"- controlled dry-run command candidates: {summary.controlled_dry_run_command_candidates}")
        print(f"- controlled dry-run apply-gate records: {summary.controlled_dry_run_apply_gate_records}")
        print(f"- controlled dry-run results: {summary.controlled_dry_run_results}")
        print(
            "- controlled dry-run experiment ids: "
            + (", ".join(summary.controlled_dry_run_experiment_ids) or "none")
        )
        print(f"- controlled dry-run intended commands: {summary.controlled_dry_run_intended_commands}")
        print(f"- controlled dry-run skipped commands: {summary.controlled_dry_run_skipped_commands}")
        print(f"- controlled dry-run applied commands: {summary.controlled_dry_run_applied_commands}")
        print(f"- controlled dry-run failed commands: {summary.controlled_dry_run_failed_commands}")
        print(
            "- controlled dry-run safety-gate blocked commands: "
            f"{summary.controlled_dry_run_safety_gate_blocked_commands}"
        )
        if summary.controlled_dry_run_candidate_classification_counts:
            print(
                "- controlled dry-run command classifications: "
                + format_count_dict(summary.controlled_dry_run_candidate_classification_counts)
            )
        if summary.controlled_dry_run_candidate_reason_counts:
            print(
                "- controlled dry-run command reasons: "
                + format_count_dict(summary.controlled_dry_run_candidate_reason_counts)
            )
        if summary.controlled_dry_run_candidate_source_counts:
            print(
                "- controlled dry-run candidate sources: "
                + format_count_dict(summary.controlled_dry_run_candidate_source_counts)
            )
        if summary.controlled_dry_run_apply_gate_result_counts:
            print(
                "- controlled dry-run apply-gate results: "
                + format_count_dict(summary.controlled_dry_run_apply_gate_result_counts)
            )
        if summary.controlled_dry_run_safety_gate_reason_counts:
            print(
                "- controlled dry-run safety-gate reasons: "
                + format_count_dict(summary.controlled_dry_run_safety_gate_reason_counts)
            )
        if summary.controlled_dry_run_command_scope_source_counts:
            print(
                "- controlled dry-run command scope sources: "
                + format_count_dict(summary.controlled_dry_run_command_scope_source_counts)
            )
        if summary.controlled_dry_run_command_scope_missing_reason_counts:
            print(
                "- controlled dry-run command scope missing reasons: "
                + format_count_dict(summary.controlled_dry_run_command_scope_missing_reason_counts)
            )
        print(f"- controlled dry-run scope violations: {summary.controlled_dry_run_scope_violations}")
        if summary.controlled_dry_run_selected_ship_counts:
            print(
                "- controlled dry-run selected ship counts: "
                + format_count_dict(summary.controlled_dry_run_selected_ship_counts)
            )
        if summary.controlled_dry_run_missing_reason_counts:
            print(
                "- controlled dry-run selected-scope reasons: "
                + format_count_dict(summary.controlled_dry_run_missing_reason_counts)
            )
        if summary.controlled_selected_group_members_by_experiment:
            print("- controlled selected groups:")
            for experiment_id, members in summary.controlled_selected_group_members_by_experiment.items():
                print(f"  {experiment_id}: {members}")
    if (
        summary.fleet_wide_report_only_experiments
        or summary.fleet_wide_report_only_launchers
        or summary.fleet_wide_report_only_targets
        or summary.fleet_wide_report_only_command_candidates
        or summary.fleet_wide_report_only_cap_state_records
        or summary.fleet_wide_report_only_results
    ):
        print(f"- fleet-wide report-only experiments: {summary.fleet_wide_report_only_experiments}")
        print(
            "- fleet-wide report-only experiment ids: "
            + (", ".join(summary.fleet_wide_report_only_experiment_ids) or "none")
        )
        print(
            "- fleet-wide report-only scope modes: "
            + format_count_dict(summary.fleet_wide_report_only_scope_mode_counts)
        )
        print(
            "- fleet-wide report-only launchers: "
            f"{summary.fleet_wide_report_only_launchers} rows, "
            f"{summary.fleet_wide_report_only_eligible_launchers} eligible, "
            f"{summary.fleet_wide_report_only_excluded_launchers} excluded"
        )
        print(
            "- fleet-wide report-only visible hostile targets: "
            f"{summary.fleet_wide_report_only_visible_hostile_targets} "
            f"({summary.fleet_wide_report_only_targets} target rows)"
        )
        print(
            "- fleet-wide report-only command candidates: "
            f"{summary.fleet_wide_report_only_command_candidates} rows, "
            f"{summary.fleet_wide_report_only_candidate_rows} possible, "
            f"{summary.fleet_wide_report_only_emitted_candidate_rows} emitted, "
            f"{summary.fleet_wide_report_only_eligible_candidate_rows} eligible"
        )
        print(
            "- fleet-wide report-only cap would-block candidates: "
            f"{summary.fleet_wide_report_only_cap_would_block_candidates}"
        )
        print(
            "- fleet-wide report-only missing-evidence candidates: "
            f"{summary.fleet_wide_report_only_missing_evidence_candidates}"
        )
        print(f"- fleet-wide report-only applied commands: {summary.fleet_wide_report_only_applied_commands}")
        if summary.fleet_wide_report_only_launcher_classification_counts:
            print(
                "- fleet-wide report-only launcher classifications: "
                + format_count_dict(summary.fleet_wide_report_only_launcher_classification_counts)
            )
        if summary.fleet_wide_report_only_launcher_reason_counts:
            print(
                "- fleet-wide report-only launcher reasons: "
                + format_count_dict(summary.fleet_wide_report_only_launcher_reason_counts)
            )
        if summary.fleet_wide_report_only_target_classification_counts:
            print(
                "- fleet-wide report-only target classifications: "
                + format_count_dict(summary.fleet_wide_report_only_target_classification_counts)
            )
        if summary.fleet_wide_report_only_target_reason_counts:
            print(
                "- fleet-wide report-only target reasons: "
                + format_count_dict(summary.fleet_wide_report_only_target_reason_counts)
            )
        if summary.fleet_wide_report_only_candidate_classification_counts:
            print(
                "- fleet-wide report-only candidate classifications: "
                + format_count_dict(summary.fleet_wide_report_only_candidate_classification_counts)
            )
        if summary.fleet_wide_report_only_candidate_reason_counts:
            print(
                "- fleet-wide report-only candidate reasons: "
                + format_count_dict(summary.fleet_wide_report_only_candidate_reason_counts)
            )
        if summary.fleet_wide_report_only_candidate_source_counts:
            print(
                "- fleet-wide report-only candidate sources: "
                + format_count_dict(summary.fleet_wide_report_only_candidate_source_counts)
            )
        if summary.fleet_wide_report_only_source_counts:
            print(
                "- fleet-wide report-only eligibility sources: "
                + format_count_dict(summary.fleet_wide_report_only_source_counts)
            )
        if summary.fleet_wide_report_only_target_source_counts:
            print(
                "- fleet-wide report-only visible-target sources: "
                + format_count_dict(summary.fleet_wide_report_only_target_source_counts)
            )
        print(f"- fleet-wide report-only cap-state records: {summary.fleet_wide_report_only_cap_state_records}")
        print(f"- fleet-wide report-only results: {summary.fleet_wide_report_only_results}")
    if (
        summary.fleet_wide_live_path_status_records
        or summary.fleet_wide_live_decision_records
        or summary.fleet_wide_live_result_records
    ):
        print(f"- fleet-wide live command-path status records: {summary.fleet_wide_live_path_status_records}")
        print(
            "- fleet-wide live experiment ids: "
            + (", ".join(summary.fleet_wide_live_experiment_ids) or "none")
        )
        print(
            "- fleet-wide live scope modes: "
            + format_count_dict(summary.fleet_wide_live_scope_mode_counts)
        )
        print(
            "- fleet-wide live command-path statuses: "
            + format_count_dict(summary.fleet_wide_live_command_path_status_counts)
        )
        print(
            "- fleet-wide live RE gate statuses: "
            + format_count_dict(summary.fleet_wide_live_re_gate_status_counts)
        )
        print(f"- fleet-wide live decisions: {summary.fleet_wide_live_decision_records}")
        if summary.fleet_wide_live_decision_counts:
            print(
                "- fleet-wide live decision counts: "
                + format_count_dict(summary.fleet_wide_live_decision_counts)
            )
        if summary.fleet_wide_live_reason_counts:
            print(
                "- fleet-wide live reasons: "
                + format_count_dict(summary.fleet_wide_live_reason_counts)
            )
        if summary.fleet_wide_live_candidate_source_counts:
            print(
                "- fleet-wide live candidate sources: "
                + format_count_dict(summary.fleet_wide_live_candidate_source_counts)
            )
        print(
            "- fleet-wide live candidates: "
            f"{summary.fleet_wide_live_candidate_rows} possible, "
            f"{summary.fleet_wide_live_emitted_decision_rows} emitted, "
            f"{summary.fleet_wide_live_allocator_evidence_candidates} allocator-evidence, "
            f"{summary.fleet_wide_live_missing_evidence_candidates} missing-evidence, "
            f"{summary.fleet_wide_live_cap_blocked_candidates} cap-blocked, "
            f"{summary.fleet_wide_live_re_blocked_candidates} RE-blocked"
        )
        print(f"- fleet-wide live applied commands: {summary.fleet_wide_live_applied_commands}")
        print(f"- fleet-wide live failed commands: {summary.fleet_wide_live_failed_commands}")
        print(f"- fleet-wide live result records: {summary.fleet_wide_live_result_records}")
    if (
        summary.fleet_wide_command_authority_candidate_records
        or summary.fleet_wide_command_authority_pre_state_records
        or summary.fleet_wide_command_authority_result_records
        or summary.fleet_wide_command_authority_post_state_records
    ):
        print(
            "- fleet-wide command-authority experiment ids: "
            + (", ".join(summary.fleet_wide_command_authority_experiment_ids) or "none")
        )
        print(
            "- fleet-wide command-authority records: "
            f"{summary.fleet_wide_command_authority_candidate_records} candidate, "
            f"{summary.fleet_wide_command_authority_pre_state_records} pre-state, "
            f"{summary.fleet_wide_command_authority_result_records} result, "
            f"{summary.fleet_wide_command_authority_post_state_records} post-state"
        )
        print(
            "- fleet-wide command-authority scope modes: "
            + format_count_dict(summary.fleet_wide_command_authority_scope_mode_counts)
        )
        if summary.fleet_wide_command_authority_result_counts:
            print(
                "- fleet-wide command-authority results: "
                + format_count_dict(summary.fleet_wide_command_authority_result_counts)
            )
        if summary.fleet_wide_command_authority_reason_counts:
            print(
                "- fleet-wide command-authority reasons: "
                + format_count_dict(summary.fleet_wide_command_authority_reason_counts)
            )
        if summary.fleet_wide_command_authority_selection_relation_counts:
            print(
                "- fleet-wide command-authority selection relation: "
                + format_count_dict(summary.fleet_wide_command_authority_selection_relation_counts)
            )
        if summary.fleet_wide_command_authority_correlation_counts:
            print(
                "- fleet-wide command-authority correlations: "
                + format_count_dict(summary.fleet_wide_command_authority_correlation_counts)
            )
        print(
            "- fleet-wide command-authority applied/failed commands: "
            f"{summary.fleet_wide_command_authority_applied_commands}/"
            f"{summary.fleet_wide_command_authority_failed_commands}"
        )
    if (
        summary.fleet_wide_bounded_live_candidate_records
        or summary.fleet_wide_bounded_live_pre_state_records
        or summary.fleet_wide_bounded_live_result_records
        or summary.fleet_wide_bounded_live_post_state_records
    ):
        print(
            "- bounded fleet-wide live experiment ids: "
            + (", ".join(summary.fleet_wide_bounded_live_experiment_ids) or "none")
        )
        print(
            "- bounded fleet-wide live records: "
            f"{summary.fleet_wide_bounded_live_candidate_records} candidate, "
            f"{summary.fleet_wide_bounded_live_pre_state_records} pre-state, "
            f"{summary.fleet_wide_bounded_live_result_records} result, "
            f"{summary.fleet_wide_bounded_live_post_state_records} post-state"
        )
        print(
            "- bounded fleet-wide live scope modes: "
            + format_count_dict(summary.fleet_wide_bounded_live_scope_mode_counts)
        )
        if summary.fleet_wide_bounded_live_result_counts:
            print(
                "- bounded fleet-wide live results: "
                + format_count_dict(summary.fleet_wide_bounded_live_result_counts)
            )
        if summary.fleet_wide_bounded_live_reason_counts:
            print(
                "- bounded fleet-wide live reasons: "
                + format_count_dict(summary.fleet_wide_bounded_live_reason_counts)
            )
        if summary.fleet_wide_bounded_live_selection_relation_counts:
            print(
                "- bounded fleet-wide live selection relation: "
                + format_count_dict(summary.fleet_wide_bounded_live_selection_relation_counts)
            )
        if summary.fleet_wide_bounded_live_correlation_counts:
            print(
                "- bounded fleet-wide live correlations: "
                + format_count_dict(summary.fleet_wide_bounded_live_correlation_counts)
            )
        if summary.fleet_wide_bounded_live_target_alternative_denominator_counts:
            print(
                "- bounded fleet-wide live target alternative denominators: "
                + format_count_dict(summary.fleet_wide_bounded_live_target_alternative_denominator_counts)
            )
        if summary.fleet_wide_bounded_live_target_alternative_evidence_counts:
            print(
                "- bounded fleet-wide live target alternative evidence: "
                + format_count_dict(summary.fleet_wide_bounded_live_target_alternative_evidence_counts)
            )
        if summary.fleet_wide_bounded_live_target_alternative_feature_evidence_counts:
            print(
                "- bounded fleet-wide live target alternative feature evidence: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_target_alternative_feature_evidence_counts
                )
            )
        if summary.fleet_wide_bounded_live_selected_target_score_space_counts:
            print(
                "- bounded fleet-wide live selected score space: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_selected_target_score_space_counts
                )
            )
        if summary.fleet_wide_bounded_live_target_alternative_score_space_counts:
            print(
                "- bounded fleet-wide live alternative score space: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_target_alternative_score_space_counts
                )
            )
        if summary.fleet_wide_bounded_live_selected_target_rank_comparison_space_counts:
            print(
                "- bounded fleet-wide live rank comparison space: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_selected_target_rank_comparison_space_counts
                )
            )
        if summary.fleet_wide_bounded_live_selected_target_rank_level_counts:
            print(
                "- bounded fleet-wide live rank level: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_selected_target_rank_level_counts
                )
            )
        if summary.fleet_wide_bounded_live_selected_target_rank_confidence_counts:
            print(
                "- bounded fleet-wide live selected target rank confidence: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_selected_target_rank_confidence_counts
                )
            )
        if summary.fleet_wide_bounded_live_prior_in_flight_confidence_counts:
            print(
                "- bounded fleet-wide live prior in-flight confidence: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_prior_in_flight_confidence_counts
                )
            )
        if summary.fleet_wide_bounded_live_prior_in_flight_bound_counts:
            print(
                "- bounded fleet-wide live prior in-flight estimate bound: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_prior_in_flight_bound_counts
                )
            )
        if summary.fleet_wide_bounded_live_prior_in_flight_target_attribution_counts:
            print(
                "- bounded fleet-wide live prior in-flight target attribution: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_prior_in_flight_target_attribution_counts
                )
            )
        if summary.fleet_wide_bounded_live_pressure_decision_counts:
            print(
                "- bounded fleet-wide live pressure decisions: "
                + format_count_dict(summary.fleet_wide_bounded_live_pressure_decision_counts)
            )
        if summary.fleet_wide_bounded_live_pressure_decision_reason_counts:
            print(
                "- bounded fleet-wide live pressure decision reasons: "
                + format_count_dict(
                    summary.fleet_wide_bounded_live_pressure_decision_reason_counts
                )
            )
        if summary.fleet_wide_bounded_live_pressure_evidence_counts:
            print(
                "- bounded fleet-wide live pressure evidence: "
                + format_count_dict(summary.fleet_wide_bounded_live_pressure_evidence_counts)
            )
        if (
            summary.fleet_wide_bounded_live_retained_above_threshold
            or summary.fleet_wide_bounded_live_retargeted_above_threshold
        ):
            print(
                "- bounded fleet-wide live pressure decisions above threshold: "
                f"{summary.fleet_wide_bounded_live_retained_above_threshold} retained, "
                f"{summary.fleet_wide_bounded_live_retargeted_above_threshold} retargeted"
            )
        if summary.fleet_wide_bounded_live_target_alternative_truncated_records:
            print(
                "- bounded fleet-wide live truncated target alternative records: "
                f"{summary.fleet_wide_bounded_live_target_alternative_truncated_records}"
            )
        print(
            "- bounded fleet-wide live applied/failed commands: "
            f"{summary.fleet_wide_bounded_live_applied_commands}/"
            f"{summary.fleet_wide_bounded_live_failed_commands}"
        )
        print(
            "- bounded fleet-wide live applied denominator coverage: "
            f"{summary.fleet_wide_bounded_live_applied_with_target_alternative_denominator} known, "
            f"{summary.fleet_wide_bounded_live_applied_with_target_alternative_denominator_gt_one} >1, "
            f"{summary.fleet_wide_bounded_live_applied_with_unknown_target_alternative_denominator} unknown"
        )
    if summary.controlled_live_apply_attempts:
        print(f"- controlled live apply attempts: {summary.controlled_live_apply_attempts}")
        print(f"- controlled live apply applied: {summary.controlled_live_apply_applied}")
        print(f"- controlled live apply skipped: {summary.controlled_live_apply_skipped}")
        print(f"- controlled live apply failed: {summary.controlled_live_apply_failed}")
        if summary.controlled_live_apply_reason_counts:
            print(
                "- controlled live apply reasons: "
                + format_count_dict(summary.controlled_live_apply_reason_counts)
            )
        if summary.controlled_live_apply_path_counts:
            print(
                "- controlled live apply paths: "
                + format_count_dict(summary.controlled_live_apply_path_counts)
            )
        if summary.controlled_live_apply_candidate_source_counts:
            print(
                "- controlled live apply candidate sources: "
                + format_count_dict(summary.controlled_live_apply_candidate_source_counts)
            )
        if summary.controlled_live_apply_counts_by_experiment:
            print("- controlled live apply by experiment:")
            for experiment_id, counts in summary.controlled_live_apply_counts_by_experiment.items():
                print(f"  {experiment_id}: {format_count_dict(counts)}")
        if summary.controlled_live_apply_counts_by_ship:
            print("- controlled live apply by ship:")
            for ship, counts in summary.controlled_live_apply_counts_by_ship.items():
                assigned = summary.controlled_live_apply_assigned_shots_by_ship.get(ship)
                spent = summary.controlled_live_apply_spent_shots_by_ship.get(ship)
                spent_unknown = summary.controlled_live_apply_spent_unknown_by_ship.get(ship, 0)
                assigned_text = "unknown" if assigned is None else str(assigned)
                spent_text = "unknown" if spent is None else str(spent)
                if spent_unknown:
                    spent_text += f" ({spent_unknown} unknown rows)"
                print(
                    f"  {ship}: {format_count_dict(counts)}; "
                    f"assignedShots={assigned_text}; spentShots={spent_text}"
                )
        if summary.controlled_live_apply_mismatch_counts:
            print(
                "- controlled live apply mismatch evidence: "
                + format_count_dict(summary.controlled_live_apply_mismatch_counts)
            )
    if summary.unknown_record_type_counts:
        print(f"- unknown record types: {format_count_dict(summary.unknown_record_type_counts)}")
    print(
        "- max target count observed: "
        f"{summary.max_target_count_observed if summary.max_target_count_observed is not None else 'unknown'}"
    )
    print(f"- target observations: {summary.target_observations}")
    print(
        "- ammo/gate budget shots observed: "
        f"{summary.ammo_gate_budget_shots_numeric_cycles} numeric cycles, "
        f"{summary.ammo_gate_budget_shots_unknown_cycles} unknown cycles, "
        f"total {format_optional_total(summary.total_ammo_gate_budget_shots)}"
    )
    print(f"- ammo-only budget cycles: {summary.ammo_only_budget_cycles}")
    print(f"- missing ammo/gate budget evidence cycles: {summary.missing_ammo_gate_budget_evidence_cycles}")
    if summary.ammo_gate_budget_evidence_source_counts:
        print("- ammo/gate budget evidence sources: " + format_count_dict(summary.ammo_gate_budget_evidence_source_counts))
    if summary.ammo_gate_budget_missing_reason_counts:
        print("- ammo/gate budget missing reasons: " + format_count_dict(summary.ammo_gate_budget_missing_reason_counts))
    if summary.ammo_evidence_source_counts:
        print("- ammo evidence sources: " + format_count_dict(summary.ammo_evidence_source_counts))
    print(
        "- target velocity evidence: "
        f"{summary.target_velocity_evidence_cycles}/{summary.shadow_cycles} cycles"
    )
    if summary.target_velocity_evidence_source_counts:
        print("- target velocity evidence sources: " + format_count_dict(summary.target_velocity_evidence_source_counts))
    if summary.target_velocity_missing_reason_counts:
        print("- target velocity missing reasons: " + format_count_dict(summary.target_velocity_missing_reason_counts))
    print(
        "- relative velocity evidence: "
        f"{summary.relative_velocity_evidence_cycles}/{summary.shadow_cycles} cycles"
    )
    if summary.relative_velocity_evidence_source_counts:
        print("- relative velocity evidence sources: " + format_count_dict(summary.relative_velocity_evidence_source_counts))
    if summary.relative_velocity_missing_reason_counts:
        print("- relative velocity missing reasons: " + format_count_dict(summary.relative_velocity_missing_reason_counts))
    print(
        "- PD weight inputs: "
        f"{summary.pd_weight_observed_cycles} observed cycles, "
        f"{summary.pd_weight_defaulted_cycles} defaulted cycles, "
        f"{summary.pd_weight_unknown_cycles} unknown cycles"
    )
    if summary.pd_weight_evidence_source_counts:
        print("- PD weight evidence sources: " + format_count_dict(summary.pd_weight_evidence_source_counts))
    if summary.pd_weight_default_reason_counts:
        print("- PD weight default reasons: " + format_count_dict(summary.pd_weight_default_reason_counts))
    if summary.pd_weight_missing_reason_counts:
        print("- PD weight missing reasons: " + format_count_dict(summary.pd_weight_missing_reason_counts))
    if summary.pd_evidence_quality_counts:
        print("- PD evidence quality: " + format_count_dict(summary.pd_evidence_quality_counts))
    if summary.pd_capability_evidence_source_counts:
        print("- PD capability evidence sources: " + format_count_dict(summary.pd_capability_evidence_source_counts))
    if summary.pd_capability_observed_field_counts:
        print("- PD capability observed fields: " + format_count_dict(summary.pd_capability_observed_field_counts))
    if summary.pd_capability_missing_reason_counts:
        print("- PD capability missing reasons: " + format_count_dict(summary.pd_capability_missing_reason_counts))
    if summary.pd_capability_limitation_counts:
        print("- PD capability limitations: " + format_count_dict(summary.pd_capability_limitation_counts))
    print(
        "- assigned shots observed: "
        f"{summary.assigned_shots_numeric_cycles} numeric cycles, "
        f"{summary.assigned_shots_unknown_cycles} unknown cycles, "
        f"total {format_optional_total(summary.total_assigned_shots)}"
    )
    print(f"- unassigned shots: {format_optional_total(summary.total_unassigned_shots)}")
    print(f"- allocations: {summary.allocations}")
    print(f"- rejections: {summary.rejections}")
    print(f"- no-op/skip decisions: {summary.no_op_decisions}")
    if summary.top_rejection_reason is None:
        print("- top rejection reason: none")
    else:
        print(f"- top rejection reason: {summary.top_rejection_reason} ({summary.top_rejection_reason_count})")
    if summary.top_no_op_reason is None:
        print("- top no-op/skip reason: none")
    else:
        print(f"- top no-op/skip reason: {summary.top_no_op_reason} ({summary.top_no_op_reason_count})")
    print(f"- average / median kill package size: {format_average_median(summary.kill_size)}")
    print(f"- average / median saturation size: {format_average_median(summary.saturation_size)}")
    print(f"- average / median launch-window score: {format_average_median(summary.launch_window_score)}")
    print(f"- average / median score per shot: {format_average_median(summary.score_per_shot)}")
    print(
        "- missing fields: "
        + ", ".join(
            format_missing_rate(field_name, summary.missing_input_counts.get(field_name, 0), summary.shadow_cycles)
            for field_name in CRITICAL_ALLOCATION_INPUTS
        )
    )
    print("- suspicious patterns: " + "; ".join(summary.suspicious_patterns))


def print_summary(summary: LogSummary, require_launchlogs: bool, require_snapshots: bool) -> None:
    """Print a human-readable summary of parsed MissileWarfare log markers."""
    verdict, reasons = logger_verdict(summary, require_launchlogs, require_snapshots)
    print(f"Log: {summary.path}")
    if not summary.exists:
        print("Status: missing")
        print("Verdict: FAIL")
        return

    print(f"Size: {summary.size_bytes} bytes")
    print(f"Lines: {summary.line_count}")
    print(f"MissileWarfare version: {summary.version or 'not found'}")
    print(
        "Load markers: "
        f"loaded={'yes' if summary.loaded_line else 'no'}, "
        f"enabled={'yes' if summary.enabled_line else 'no'}, "
        f"active={'yes' if summary.active_line else 'no'}"
    )
    print(
        "Diagnostics bootstrap: "
        f"patched={summary.bootstrap_patched if summary.bootstrap_patched is not None else 'unknown'}, "
        f"skipped={summary.bootstrap_skipped if summary.bootstrap_skipped is not None else 'unknown'}"
    )

    print("Patched hooks:")
    if summary.patched_hooks:
        for hook in summary.patched_hooks:
            print(f"  line {hook.line}: {hook.description} -> {hook.target}")
    else:
        print("  none")

    print(f"LaunchLog entries: {summary.launch_log_count}")
    if summary.launch_log_count:
        print(f"  seq range: {summary.first_seq}-{summary.last_seq}")
        print(f"  first: line {summary.first_launch_line}, utc={summary.first_launch_utc}")
        print(f"  last:  line {summary.last_launch_line}, utc={summary.last_launch_utc}")
        print("  hooks:")
        for hook, count in summary.hook_counts.items():
            print(f"    {hook}: {count}")
        print(f"  sequence gaps: {', '.join(summary.sequence_gaps) if summary.sequence_gaps else 'none'}")
        print(
            "  duplicate sequences: "
            + (", ".join(map(str, summary.duplicate_sequences)) if summary.duplicate_sequences else "none")
        )
        if summary.missile_try_fire_count:
            print("  missile try-fire ammo/gate evidence:")
            print(f"    rows: {summary.missile_try_fire_count}")
            if summary.missile_try_fire_pre_fire_field_counts:
                print("    pre-fire fields:")
                for field_name, count in summary.missile_try_fire_pre_fire_field_counts.items():
                    print(f"      {field_name}: {count}/{summary.missile_try_fire_count}")
            if summary.missile_try_fire_pre_fire_ammo_source_counts:
                print("    pre-fire ammo sources:")
                for source, count in summary.missile_try_fire_pre_fire_ammo_source_counts.items():
                    print(f"      {source}: {count}")
            if summary.missile_try_fire_pre_post_ammo_delta_counts:
                print(
                    "    pre/post remaining ammo numeric pairs: "
                    f"{summary.missile_try_fire_pre_post_ammo_numeric_count}/{summary.missile_try_fire_count}"
                )
                print("    preFireRemaining - postFireRemaining:")
                for delta, count in summary.missile_try_fire_pre_post_ammo_delta_counts.items():
                    print(f"      {delta}: {count}")
            if summary.controlled_command_launch_correlation_counts:
                print("    controlled command launch correlation:")
                print(f"      stamped rows: {summary.controlled_command_launch_context_rows}")
                print(
                    "      numeric controlled observed spent rows: "
                    f"{summary.controlled_command_launch_observed_spent_numeric_count}"
                )
                for correlation, count in summary.controlled_command_launch_correlation_counts.items():
                    print(f"      {correlation}: {count}")

    print(f"SnapshotLog entries: {summary.snapshot_log_count}")
    if summary.snapshot_log_count:
        print(f"  first: line {summary.first_snapshot_line}")
        print(f"  last:  line {summary.last_snapshot_line}")
        print("  sources:")
        for source, count in summary.snapshot_source_counts.items():
            print(f"    {source}: {count}")
        print("  missing fields:")
        if summary.snapshot_missing_counts:
            for field_name, count in summary.snapshot_missing_counts.items():
                print(f"    {field_name}: {count}")
        else:
            print("    none")
        if summary.snapshot_ammo_gate_budget_shots_counts:
            print("  ammoGateBudgetShots:")
            for value, count in summary.snapshot_ammo_gate_budget_shots_counts.items():
                print(f"    {value}: {count}")
        if summary.snapshot_ammo_gate_budget_evidence_source_counts:
            print("  ammo/gate budget evidence sources:")
            for source, count in summary.snapshot_ammo_gate_budget_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.snapshot_ammo_gate_budget_missing_reason_counts:
            print("  ammo/gate budget missing reasons:")
            for reason, count in summary.snapshot_ammo_gate_budget_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.snapshot_ammo_evidence_source_counts:
            print("  ammo evidence sources:")
            for source, count in summary.snapshot_ammo_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.snapshot_live_weapon_state_counts:
            print("  live weapon states:")
            for state, count in summary.snapshot_live_weapon_state_counts.items():
                print(f"    {state}: {count}")
        print(
            "  target identity: "
            f"{summary.snapshot_known_target_count}/{summary.snapshot_log_count} snapshots"
        )
        if summary.snapshot_target_identity_source_counts:
            print("  target identity sources:")
            for source, count in summary.snapshot_target_identity_source_counts.items():
                print(f"    {source}: {count}")
        if summary.snapshot_target_velocity_evidence_source_counts:
            print("  target velocity evidence sources:")
            for source, count in summary.snapshot_target_velocity_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.snapshot_target_velocity_missing_reason_counts:
            print("  target velocity missing reasons:")
            for reason, count in summary.snapshot_target_velocity_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.snapshot_relative_velocity_evidence_source_counts:
            print("  relative velocity evidence sources:")
            for source, count in summary.snapshot_relative_velocity_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.snapshot_relative_velocity_missing_reason_counts:
            print("  relative velocity missing reasons:")
            for reason, count in summary.snapshot_relative_velocity_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.snapshot_pd_weight_evidence_source_counts:
            print("  PD weight evidence sources:")
            for source, count in summary.snapshot_pd_weight_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.snapshot_pd_weight_default_reason_counts:
            print("  PD weight default reasons:")
            for reason, count in summary.snapshot_pd_weight_default_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.snapshot_pd_weight_missing_reason_counts:
            print("  PD weight missing reasons:")
            for reason, count in summary.snapshot_pd_weight_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.snapshot_pd_evidence_quality_counts:
            print("  PD evidence quality:")
            for quality, count in summary.snapshot_pd_evidence_quality_counts.items():
                print(f"    {quality}: {count}")
        if summary.snapshot_pd_capability_evidence_source_counts:
            print("  PD capability evidence sources:")
            for source, count in summary.snapshot_pd_capability_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.snapshot_pd_capability_observed_field_counts:
            print("  PD capability observed fields:")
            for field_name, count in summary.snapshot_pd_capability_observed_field_counts.items():
                print(f"    {field_name}: {count}")
        if summary.snapshot_pd_capability_missing_reason_counts:
            print("  PD capability missing reasons:")
            for reason, count in summary.snapshot_pd_capability_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.snapshot_pd_capability_limitation_counts:
            print("  PD capability limitations:")
            for limitation, count in summary.snapshot_pd_capability_limitation_counts.items():
                print(f"    {limitation}: {count}")
        if summary.snapshot_target_counts:
            print("  targets:")
            for target, count in summary.snapshot_target_counts.items():
                print(f"    {target}: {count}")
        if summary.snapshot_target_team_counts:
            print("  target teams:")
            for team, count in summary.snapshot_target_team_counts.items():
                print(f"    {team}: {count}")

    print(f"OutcomeLog entries: {summary.outcome_log_count}")
    if summary.outcome_log_count:
        print(f"  first: line {summary.first_outcome_line}")
        print(f"  last:  line {summary.last_outcome_line}")
        if summary.outcome_record_type_counts:
            print("  record types:")
            for record_type, count in summary.outcome_record_type_counts.items():
                print(f"    {record_type}: {count}")
        if summary.outcome_event_level_counts:
            print("  event levels:")
            for event_level, count in summary.outcome_event_level_counts.items():
                print(f"    {event_level}: {count}")
        if summary.outcome_attribution_level_counts:
            print("  attribution levels:")
            for attribution_level, count in summary.outcome_attribution_level_counts.items():
                print(f"    {attribution_level}: {count}")
        if summary.outcome_identity_bridge_counts:
            print("  identity bridges:")
            for identity_bridge, count in summary.outcome_identity_bridge_counts.items():
                print(f"    {identity_bridge}: {count}")
        if summary.outcome_source_hook_counts:
            print("  source hooks:")
            for source_hook, count in summary.outcome_source_hook_counts.items():
                print(f"    {source_hook}: {count}")

    print(f"AllocationLog entries: {summary.allocation_log_count}")
    if summary.allocation_log_count:
        print(f"  first: line {summary.first_allocation_line}")
        print(f"  last:  line {summary.last_allocation_line}")
        print("  record types:")
        for record_type, count in summary.allocation_record_type_counts.items():
            print(f"    {record_type}: {count}")
        if summary.allocation_status_counts:
            print("  cycle status:")
            for status, count in summary.allocation_status_counts.items():
                print(f"    {status}: {count}")
        if summary.allocation_missing_input_counts:
            print("  missing inputs:")
            for field_name, count in summary.allocation_missing_input_counts.items():
                print(f"    {field_name}: {count}")
        if summary.allocation_ammo_gate_budget_evidence_source_counts:
            print("  ammo/gate budget evidence sources:")
            for source, count in summary.allocation_ammo_gate_budget_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.allocation_ammo_gate_budget_missing_reason_counts:
            print("  ammo/gate budget missing reasons:")
            for reason, count in summary.allocation_ammo_gate_budget_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.allocation_ammo_evidence_source_counts:
            print("  ammo evidence sources:")
            for source, count in summary.allocation_ammo_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.allocation_target_velocity_evidence_source_counts:
            print("  target velocity evidence sources:")
            for source, count in summary.allocation_target_velocity_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.allocation_target_velocity_missing_reason_counts:
            print("  target velocity missing reasons:")
            for reason, count in summary.allocation_target_velocity_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.allocation_relative_velocity_evidence_source_counts:
            print("  relative velocity evidence sources:")
            for source, count in summary.allocation_relative_velocity_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.allocation_relative_velocity_missing_reason_counts:
            print("  relative velocity missing reasons:")
            for reason, count in summary.allocation_relative_velocity_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.allocation_pd_weight_evidence_source_counts:
            print("  PD weight evidence sources:")
            for source, count in summary.allocation_pd_weight_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.allocation_pd_weight_default_reason_counts:
            print("  PD weight default reasons:")
            for reason, count in summary.allocation_pd_weight_default_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.allocation_pd_weight_missing_reason_counts:
            print("  PD weight missing reasons:")
            for reason, count in summary.allocation_pd_weight_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.allocation_pd_evidence_quality_counts:
            print("  PD evidence quality:")
            for quality, count in summary.allocation_pd_evidence_quality_counts.items():
                print(f"    {quality}: {count}")
        if summary.allocation_pd_capability_evidence_source_counts:
            print("  PD capability evidence sources:")
            for source, count in summary.allocation_pd_capability_evidence_source_counts.items():
                print(f"    {source}: {count}")
        if summary.allocation_pd_capability_observed_field_counts:
            print("  PD capability observed fields:")
            for field_name, count in summary.allocation_pd_capability_observed_field_counts.items():
                print(f"    {field_name}: {count}")
        if summary.allocation_pd_capability_missing_reason_counts:
            print("  PD capability missing reasons:")
            for reason, count in summary.allocation_pd_capability_missing_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.allocation_pd_capability_limitation_counts:
            print("  PD capability limitations:")
            for limitation, count in summary.allocation_pd_capability_limitation_counts.items():
                print(f"    {limitation}: {count}")
        if summary.allocation_assigned_shots_counts:
            print("  assigned shots:")
            for assigned_shots, count in summary.allocation_assigned_shots_counts.items():
                print(f"    {assigned_shots}: {count}")
        if summary.allocation_rejection_reason_counts:
            print("  rejection reasons:")
            for reason, count in summary.allocation_rejection_reason_counts.items():
                print(f"    {reason}: {count}")
        if summary.allocation_no_op_reason_counts:
            print("  no-op/skip reasons:")
            for reason, count in summary.allocation_no_op_reason_counts.items():
                print(f"    {reason}: {count}")
        print_allocation_battle_summary(summary.allocation_summary)

    print("MissileWarfare issues:")
    if summary.issues:
        for issue in summary.issues:
            print(f"  line {issue.line}: {issue.text}")
    else:
        print("  none")

    print(f"Verdict: {verdict}")
    for reason in reasons:
        print(f"  - {reason}")
    if verdict == "OK" and summary.issues:
        print("  Logger markers are healthy; issues above are separate mod/runtime warnings.")


def main() -> None:
    """Parse command-line arguments and report the Player.log verdict."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", nargs="?", type=Path, default=DEFAULT_LOG, help=f"default: {DEFAULT_LOG}")
    parser.add_argument("--json", action="store_true", help="emit the parsed summary as JSON")
    parser.add_argument("--max-issues", type=int, default=12, help="maximum issue lines to print/store")
    parser.add_argument(
        "--require-launchlogs",
        action="store_true",
        help="fail when startup markers are present but no combat LaunchLog entries were emitted",
    )
    parser.add_argument(
        "--require-snapshots",
        action="store_true",
        help="fail when startup markers are present but no SnapshotLog entries were emitted",
    )
    args = parser.parse_args()

    summary = parse_log(args.log, args.max_issues)
    verdict, _reasons = logger_verdict(summary, args.require_launchlogs, args.require_snapshots)

    if args.json:
        print(json.dumps(asdict(summary), indent=2, ensure_ascii=False))
    else:
        print_summary(summary, args.require_launchlogs, args.require_snapshots)

    raise SystemExit(0 if verdict == "OK" else 1)


if __name__ == "__main__":
    main()
