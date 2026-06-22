#!/usr/bin/env python3
"""Generate offline shadow-allocation fitting reports from selected logs."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
import shutil

from parse_player_log import (
    ALLOCATION_RE,
    LogSummary,
    logger_verdict,
    parse_log,
    parse_pairs,
    split_csv_field,
    try_parse_float,
    try_parse_int,
)


DEFAULT_INPUT = Path("artifacts/combat-logs/selected")
DEFAULT_OUTPUT = Path("artifacts/shadow-fitting/latest")
LOG_PATTERNS = ("*.log", "*.txt")
CLASSIFICATIONS = (
    "plausible",
    "overkill",
    "underkill",
    "late/out-of-window",
    "target-value mismatch",
    "PD-risk mismatch",
    "partial saturation",
    "command-safety no-op",
    "missing-evidence-limited",
    "impossible",
    "ambiguous",
)
BAD_CLASSIFICATIONS = {
    "overkill",
    "underkill",
    "target-value mismatch",
    "PD-risk mismatch",
    "impossible",
}
WINDOW_REASON_MARKERS = ("launch window", "range", "receding", "outside")
REQUIRED_EVIDENCE_FIELDS = (
    "LaunchLog",
    "SnapshotLog",
    "AllocationLog",
    "shadow allocation cycles",
)


@dataclass
class AllocationRecord:
    line: int
    record_type: str
    cycle_id: str
    target: str
    reason: str
    assigned_shots: int | None
    saturation_size: int | None
    kill_size: int | None
    launch_window_score: float | None
    target_value: float | None
    pd_score: float | None
    pd_weight_defaulted: str
    missing_inputs: list[str]
    classification: str
    limitations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class CycleContext:
    cycle_id: str
    line: int
    total_ammo_gate_budget_shots: int | None
    assigned_shots: int | None
    missing_inputs: list[str]
    target_velocity_evidence_source: str
    relative_velocity_evidence_source: str
    pd_weight_defaulted: str
    pd_weight_evidence_source: str
    pd_evidence_quality: str
    pd_capability_evidence_source: str
    pd_capability_observed_fields: str
    status: str


@dataclass
class FittingLogReport:
    path: str
    parser_verdict: str
    parser_reasons: list[str]
    has_required_evidence: bool
    missing_required_evidence: list[str]
    synthetic_fixture: bool
    classification_counts: dict[str, int]
    limitation_counts: dict[str, int]
    representative_records: list[dict[str, object]]
    parser_summary: dict[str, object]


@dataclass
class EvidenceSufficiencyInput:
    name: str
    status: str
    scope: str
    summary: str
    limitations: list[str] = field(default_factory=list)
    evidence: dict[str, object] = field(default_factory=dict)


@dataclass
class EvidenceSufficiencyReport:
    verdict: str
    verdict_reasons: list[str]
    controlled_command_readiness: str
    command_blockers: list[str]
    inputs: list[EvidenceSufficiencyInput]


@dataclass
class AggregateReport:
    input: str
    output: str
    log_count: int
    evidence_log_count: int
    real_evidence_log_count: int
    synthetic_fixture_count: int
    parser_failures: int
    classification_counts: dict[str, int]
    limitation_counts: dict[str, int]
    readiness_verdict: str
    readiness_reasons: list[str]
    evidence_sufficiency: EvidenceSufficiencyReport
    logs: list[FittingLogReport]


def discover_logs(input_path: Path) -> list[Path]:
    """Return selected log files in deterministic order."""
    if input_path.is_file():
        return [input_path]

    if not input_path.exists():
        return []

    files: list[Path] = []
    for pattern in LOG_PATTERNS:
        files.extend(path for path in input_path.rglob(pattern) if path.is_file())
    return sorted(set(files), key=lambda path: path.as_posix().lower())


def is_synthetic_fixture(path: Path) -> bool:
    """Return whether a path is the repo synthetic smoke fixture."""
    return "fixtures" in {part.lower() for part in path.parts}


def scan_allocation_records(path: Path) -> tuple[dict[str, CycleContext], list[dict[str, str | int]]]:
    """Read AllocationLog rows needed for fitting classification."""
    cycles: dict[str, CycleContext] = {}
    records: list[dict[str, str | int]] = []

    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            allocation = ALLOCATION_RE.match(raw_line.rstrip("\r\n"))
            if allocation is None:
                continue

            pairs: dict[str, str | int] = parse_pairs(allocation.group("pairs"))
            pairs["line"] = line_number
            record_type = str(pairs.get("recordType", "unknown"))
            cycle_id = str(pairs.get("cycleId", "unknown"))
            records.append(pairs)

            if record_type == "cycle":
                cycles[cycle_id] = CycleContext(
                    cycle_id=cycle_id,
                    line=line_number,
                    total_ammo_gate_budget_shots=try_parse_int(
                        str(pairs.get("totalAmmoGateBudgetShots", ""))
                    ),
                    assigned_shots=try_parse_int(str(pairs.get("assignedShots", ""))),
                    missing_inputs=split_csv_field(str(pairs.get("missingInputs", ""))),
                    target_velocity_evidence_source=str(
                        pairs.get("targetVelocityEvidenceSource", "unknown")
                    ),
                    relative_velocity_evidence_source=str(
                        pairs.get("relativeVelocityEvidenceSource", "unknown")
                    ),
                    pd_weight_defaulted=str(pairs.get("pdWeightDefaulted", "unknown")).lower(),
                    pd_weight_evidence_source=str(
                        pairs.get("pdWeightEvidenceSource", "unknown")
                    ),
                    pd_evidence_quality=str(pairs.get("pdEvidenceQuality", "unknown")),
                    pd_capability_evidence_source=str(
                        pairs.get("pdCapabilityEvidenceSource", "unknown")
                    ),
                    pd_capability_observed_fields=str(
                        pairs.get("pdCapabilityObservedFields", "unknown")
                    ),
                    status=str(pairs.get("status", "unknown")),
                )

    return cycles, records


def classify_records(
    cycles: dict[str, CycleContext],
    raw_records: list[dict[str, str | int]],
) -> list[AllocationRecord]:
    """Classify allocation/rejection/no-op rows using conservative evidence rules."""
    allocated_values_by_cycle: dict[str, list[float]] = {}
    for raw in raw_records:
        if raw.get("recordType") != "allocation":
            continue
        cycle_id = str(raw.get("cycleId", "unknown"))
        target_value = try_parse_float(str(raw.get("targetValue", "")))
        if target_value is not None:
            allocated_values_by_cycle.setdefault(cycle_id, []).append(target_value)

    classified: list[AllocationRecord] = []
    for raw in raw_records:
        record_type = str(raw.get("recordType", "unknown"))
        if record_type == "cycle":
            continue

        cycle_id = str(raw.get("cycleId", "unknown"))
        cycle = cycles.get(cycle_id)
        assigned = try_parse_int(str(raw.get("assignedShots", "")))
        saturation = try_parse_int(str(raw.get("saturationSize", "")))
        kill = try_parse_int(str(raw.get("killSize", "")))
        launch_window_score = try_parse_float(str(raw.get("launchWindowScore", "")))
        target_value = try_parse_float(str(raw.get("targetValue", "")))
        pd_score = try_parse_float(str(raw.get("pdScore", "")))
        pd_defaulted = str(raw.get("pdWeightDefaulted", "unknown")).lower()
        if pd_defaulted not in {"true", "false"} and cycle is not None:
            pd_defaulted = cycle.pd_weight_defaulted

        reason = str(
            raw.get("reason")
            or raw.get("rejectionReason")
            or raw.get("noOpReason")
            or "unknown"
        )
        missing_inputs = split_csv_field(str(raw.get("missingInputs", "")))
        if not missing_inputs and cycle is not None:
            missing_inputs = list(cycle.missing_inputs)

        classification, notes = classify_single_record(
            record_type,
            reason,
            assigned,
            saturation,
            kill,
            launch_window_score,
            target_value,
            cycle,
            allocated_values_by_cycle.get(cycle_id, []),
            missing_inputs,
        )
        limitations = record_limitations(
            pd_defaulted,
            missing_inputs,
            cycle,
            classification,
        )

        classified.append(
            AllocationRecord(
                line=int(raw["line"]),
                record_type=record_type,
                cycle_id=cycle_id,
                target=str(raw.get("target", "unknown")),
                reason=reason,
                assigned_shots=assigned,
                saturation_size=saturation,
                kill_size=kill,
                launch_window_score=launch_window_score,
                target_value=target_value,
                pd_score=pd_score,
                pd_weight_defaulted=pd_defaulted,
                missing_inputs=missing_inputs,
                classification=classification,
                limitations=limitations,
                notes=notes,
            )
        )

    return classified


def classify_single_record(
    record_type: str,
    reason: str,
    assigned: int | None,
    saturation: int | None,
    kill: int | None,
    launch_window_score: float | None,
    target_value: float | None,
    cycle: CycleContext | None,
    allocated_target_values: list[float],
    missing_inputs: list[str],
) -> tuple[str, list[str]]:
    """Return primary classification and human notes for one decision row."""
    notes: list[str] = []
    lowered_reason = reason.lower()
    hard_missing_inputs = [value for value in missing_inputs if value != "pdWeightsDefaulted"]

    if cycle is None:
        return "ambiguous", ["cycle context was not present in the log"]

    if cycle.total_ammo_gate_budget_shots is None and record_type == "allocation":
        return "impossible", ["allocation row exists without numeric ammo/gate budget"]

    if record_type == "allocation":
        if hard_missing_inputs:
            notes.append("required non-PD evidence is missing: " + ", ".join(hard_missing_inputs))
            return "missing-evidence-limited", notes
        if assigned is None or assigned <= 0:
            return "impossible", ["allocation row assigned no shots"]
        if kill is not None and assigned > kill:
            return "overkill", ["assigned shots exceed kill package size"]
        if saturation is not None and 0 < assigned < saturation:
            return "underkill", ["assigned shots are below saturation size"]
        if kill is not None and saturation is not None and saturation <= assigned < kill:
            return "partial saturation", ["assigned shots form saturation but not kill package"]
        if kill is not None and assigned >= kill and launch_window_score is not None:
            if launch_window_score >= 0.35:
                return "plausible", ["kill package with acceptable launch-window score"]
        return "ambiguous", ["allocation lacks enough numeric context for stronger fitting"]

    if record_type == "rejection":
        if hard_missing_inputs:
            notes.append("required non-PD evidence is missing: " + ", ".join(hard_missing_inputs))
            return "missing-evidence-limited", notes
        if any(marker in lowered_reason for marker in WINDOW_REASON_MARKERS):
            return "late/out-of-window", ["rejection reason is launch-window limited"]
        if (
            target_value is not None
            and allocated_target_values
            and target_value > max(allocated_target_values)
        ):
            return "target-value mismatch", [
                "higher-value target rejected while a lower-value target was allocated"
            ]
        if "pd" in lowered_reason:
            return "PD-risk mismatch", ["rejection reason is PD-risk related"]
        return "ambiguous", ["rejection is not directly classifiable from log evidence"]

    if record_type == "noOp":
        if hard_missing_inputs == ["targetIdentity"] and "missing" in lowered_reason:
            return "command-safety no-op", [
                "no allocation because no concrete launcher-selected target identity was visible"
            ]
        if cycle.total_ammo_gate_budget_shots == 0 or "no ammo/gate budget" in lowered_reason:
            return "plausible", ["no-op matches zero ammo/gate budget evidence"]
        if hard_missing_inputs or "missing" in lowered_reason:
            return "missing-evidence-limited", ["no-op is limited by missing evidence"]
        return "ambiguous", ["no-op reason needs manual review"]

    return "ambiguous", [f"unknown allocation record type: {record_type}"]


def record_limitations(
    pd_defaulted: str,
    missing_inputs: list[str],
    cycle: CycleContext | None,
    classification: str,
) -> list[str]:
    """Return evidence limitations that qualify a classification."""
    limitations: list[str] = []
    if (
        classification != "command-safety no-op"
        and (pd_defaulted == "true" or "pdWeightsDefaulted" in missing_inputs)
    ):
        limitations.append("PD evidence defaulted")

    if cycle is None:
        return limitations

    if cycle.target_velocity_evidence_source in {"unknown", "none"}:
        limitations.append("target velocity evidence missing")
    if cycle.relative_velocity_evidence_source in {"unknown", "none"}:
        limitations.append("relative velocity evidence missing")
    return limitations


def required_evidence(summary: LogSummary) -> tuple[bool, list[str]]:
    """Return whether a parsed log has the evidence required for fitting."""
    missing: list[str] = []
    if summary.launch_log_count <= 0:
        missing.append("LaunchLog")
    if summary.snapshot_log_count <= 0:
        missing.append("SnapshotLog")
    if summary.allocation_log_count <= 0:
        missing.append("AllocationLog")
    if summary.allocation_summary.shadow_cycles <= 0:
        missing.append("shadow allocation cycles")
    return not missing, missing


def fitting_log_report(path: Path, max_issues: int) -> FittingLogReport:
    """Parse one selected log and return fitting-oriented report data."""
    summary = parse_log(path, max_issues)
    parser_verdict, parser_reasons = logger_verdict(
        summary,
        require_launchlogs=True,
        require_snapshots=True,
    )
    has_evidence, missing_evidence = required_evidence(summary)
    cycles, raw_records = scan_allocation_records(path)
    classified_records = classify_records(cycles, raw_records)
    classification_counts = Counter(record.classification for record in classified_records)
    limitation_counts = Counter(
        limitation for record in classified_records for limitation in record.limitations
    )

    for classification in CLASSIFICATIONS:
        classification_counts.setdefault(classification, 0)

    representative_records = [
        asdict(record)
        for record in sorted(
            classified_records,
            key=lambda record: (
                record.classification == "plausible",
                record.classification,
                record.line,
            ),
        )[:20]
    ]

    return FittingLogReport(
        path=str(path),
        parser_verdict=parser_verdict,
        parser_reasons=parser_reasons,
        has_required_evidence=has_evidence,
        missing_required_evidence=missing_evidence,
        synthetic_fixture=is_synthetic_fixture(path),
        classification_counts=dict(sorted(classification_counts.items())),
        limitation_counts=dict(sorted(limitation_counts.items())),
        representative_records=representative_records,
        parser_summary=asdict(summary),
    )


def readiness_verdict(logs: list[FittingLogReport]) -> tuple[str, list[str]]:
    """Compute conservative #6 baseline readiness from selected-log reports."""
    evidence_logs = [log for log in logs if log.has_required_evidence]
    real_evidence_logs = [log for log in evidence_logs if not log.synthetic_fixture]
    parser_failures = [log for log in logs if log.parser_verdict != "OK"]
    aggregate_counts = Counter()
    limitations = Counter()
    for log in evidence_logs:
        aggregate_counts.update(log.classification_counts)
        limitations.update(log.limitation_counts)

    reasons: list[str] = []
    if parser_failures:
        reasons.append(f"{len(parser_failures)} selected log(s) failed parser validation")
    if not real_evidence_logs:
        reasons.append("no real selected combat log has required fitting evidence")
        return "Not ready", reasons

    severe_counts = {
        key: aggregate_counts.get(key, 0)
        for key in BAD_CLASSIFICATIONS
        if aggregate_counts.get(key, 0) > 0
    }
    if severe_counts:
        reasons.append(
            "bad or impossible classifications require review: "
            + ", ".join(f"{key}: {value}" for key, value in sorted(severe_counts.items()))
        )
        return "Not ready", reasons

    plausible = aggregate_counts.get("plausible", 0)
    if plausible <= 0:
        reasons.append("no plausible allocation or no-op decisions were classified")
        return "Not ready", reasons

    if limitations.get("PD evidence defaulted", 0):
        reasons.append("PD inputs are default-model evidence, so full readiness is blocked")
    if len(real_evidence_logs) == 1:
        reasons.append("only one real selected combat log was analyzed")

    if reasons:
        return "Conditionally ready", reasons

    reasons.append("multiple real selected logs have required evidence and no bad classifications")
    return "Ready for #6 baseline", reasons


def evidence_sufficiency_report(logs: list[FittingLogReport]) -> EvidenceSufficiencyReport:
    """Build Issue #28 evidence sufficiency gates separate from fitting readiness."""
    evidence_logs = [log for log in logs if log.has_required_evidence]
    real_evidence_logs = [log for log in evidence_logs if not log.synthetic_fixture]
    scoped_logs = real_evidence_logs or evidence_logs
    parser_failures = [log for log in logs if log.parser_verdict != "OK"]

    total_cycles = sum(allocation_summary_value(log, "shadow_cycles") for log in scoped_logs)
    missing_inputs = aggregate_allocation_counter(scoped_logs, "missing_input_counts")
    classification_counts = Counter()
    limitation_counts = Counter()
    for log in scoped_logs:
        classification_counts.update(log.classification_counts)
        limitation_counts.update(log.limitation_counts)

    inputs = [
        ammo_gate_budget_status(scoped_logs, total_cycles, missing_inputs),
        target_identity_status(scoped_logs, total_cycles, missing_inputs, classification_counts),
        target_velocity_status(scoped_logs, total_cycles),
        relative_velocity_status(scoped_logs, total_cycles),
        missile_profile_status(total_cycles, missing_inputs),
        target_pd_status(scoped_logs, total_cycles, limitation_counts),
        EvidenceSufficiencyInput(
            name="selected-player command scope",
            status="ready",
            scope="command design",
            summary=(
                "Issue #21 verifies the tactical command panel's single selected "
                "ship or group-selected ship list as the later command scope."
            ),
            limitations=["not exercised by the offline fitting wrapper"],
        ),
        EvidenceSufficiencyInput(
            name="vanilla command granularity",
            status="commandUnsafe",
            scope="controlled command mapping",
            summary=(
                "Vanilla salvo target commands operate at ship level and affect "
                "all salvo-capable weapons on that ship."
            ),
            limitations=[
                "allocator-to-command mapping must not assume per-visible-module salvo control"
            ],
        ),
        EvidenceSufficiencyInput(
            name="dry-run command intent logging",
            status="commandUnsafe",
            scope="controlled command mapping",
            summary=(
                "Current selected-log fitting is observation-only and does not log "
                "a selected-scope command intent."
            ),
            limitations=["required before live controlled command application"],
        ),
        observed_launch_delta_status(scoped_logs),
    ]

    command_blockers = [
        input_status.summary
        for input_status in inputs
        if input_status.status == "commandUnsafe"
    ]

    verdict_reasons: list[str] = []
    if parser_failures:
        verdict_reasons.append(f"{len(parser_failures)} selected log(s) failed parser validation")
    if not real_evidence_logs:
        verdict_reasons.append("no real selected combat log has required fitting evidence")
    if any(input_status.status in {"unknown", "defaulted"} for input_status in inputs[:6]):
        verdict_reasons.append("one or more allocator evidence inputs are unknown or defaulted")
    if any(input_status.status in {"presenceOnly", "provisional"} for input_status in inputs[:6]):
        verdict_reasons.append("one or more allocator evidence inputs have named fidelity limits")
    if command_blockers:
        verdict_reasons.append("controlled command application has separate command-safety blockers")

    if parser_failures or not real_evidence_logs or any(
        input_status.status in {"unknown", "defaulted"} for input_status in inputs[:6]
    ):
        verdict = "Not baseline-ready"
    elif any(input_status.status in {"presenceOnly", "provisional"} for input_status in inputs):
        verdict = "Baseline-ready with named limitations"
    else:
        verdict = "Ready"

    if not verdict_reasons:
        verdict_reasons.append("all scoped allocator evidence inputs are ready")

    return EvidenceSufficiencyReport(
        verdict=verdict,
        verdict_reasons=verdict_reasons,
        controlled_command_readiness="Not ready",
        command_blockers=command_blockers,
        inputs=inputs,
    )


def allocation_summary(log: FittingLogReport) -> dict[str, object]:
    """Return the parser allocation summary dictionary for a fitting log."""
    summary = log.parser_summary.get("allocation_summary", {})
    return summary if isinstance(summary, dict) else {}


def allocation_summary_value(log: FittingLogReport, key: str) -> int:
    """Return an integer allocation-summary field."""
    value = allocation_summary(log).get(key, 0)
    return value if isinstance(value, int) else 0


def aggregate_allocation_counter(logs: list[FittingLogReport], key: str) -> Counter[str]:
    """Aggregate a parser allocation-summary count dictionary."""
    counter: Counter[str] = Counter()
    for log in logs:
        values = allocation_summary(log).get(key, {})
        if isinstance(values, dict):
            counter.update({str(name): int(count) for name, count in values.items()})
    return counter


def ammo_gate_budget_status(
    logs: list[FittingLogReport],
    total_cycles: int,
    missing_inputs: Counter[str],
) -> EvidenceSufficiencyInput:
    """Classify ammo/gate budget sufficiency."""
    numeric_cycles = sum(
        allocation_summary_value(log, "ammo_gate_budget_shots_numeric_cycles") for log in logs
    )
    source_counts = aggregate_allocation_counter(logs, "ammo_gate_budget_evidence_source_counts")
    missing = missing_inputs.get("ammoGateBudgetShots", 0)
    if total_cycles <= 0:
        status = "unknown"
    elif missing == 0 and numeric_cycles == total_cycles:
        status = "ready"
    elif numeric_cycles > 0:
        status = "provisional"
    else:
        status = "unknown"

    limitations = []
    if missing:
        limitations.append(f"{missing}/{total_cycles} cycles report missing ammoGateBudgetShots")

    return EvidenceSufficiencyInput(
        name="ammoGateBudgetShots",
        status=status,
        scope="fitting baseline",
        summary=f"{numeric_cycles}/{total_cycles} cycles have numeric ammo/gate budget evidence.",
        limitations=limitations,
        evidence={"sources": dict(sorted(source_counts.items()))},
    )


def target_identity_status(
    logs: list[FittingLogReport],
    total_cycles: int,
    missing_inputs: Counter[str],
    classification_counts: Counter[str],
) -> EvidenceSufficiencyInput:
    """Classify launcher-selected target identity sufficiency."""
    del logs
    missing = missing_inputs.get("targetIdentity", 0)
    command_noops = classification_counts.get("command-safety no-op", 0)
    if total_cycles <= 0:
        status = "unknown"
    elif missing == 0:
        status = "ready"
    elif missing == command_noops:
        status = "provisional"
    else:
        status = "unknown"

    limitations = []
    if command_noops:
        limitations.append(
            f"{command_noops} no-op rows lacked launcher-selected target identity and allocated no shots"
        )
    if missing and missing != command_noops:
        limitations.append(f"{missing}/{total_cycles} cycles lacked target identity")

    return EvidenceSufficiencyInput(
        name="target identity",
        status=status,
        scope="fitting baseline",
        summary=f"{total_cycles - missing}/{total_cycles} cycles have launcher-selected target identity.",
        limitations=limitations,
        evidence={"command_safety_no_ops": command_noops},
    )


def target_velocity_status(
    logs: list[FittingLogReport],
    total_cycles: int,
) -> EvidenceSufficiencyInput:
    """Classify target velocity evidence sufficiency."""
    evidence_cycles = sum(allocation_summary_value(log, "target_velocity_evidence_cycles") for log in logs)
    source_counts = aggregate_allocation_counter(logs, "target_velocity_evidence_source_counts")
    return velocity_input_status(
        "target velocity",
        evidence_cycles,
        total_cycles,
        source_counts,
    )


def relative_velocity_status(
    logs: list[FittingLogReport],
    total_cycles: int,
) -> EvidenceSufficiencyInput:
    """Classify relative velocity evidence sufficiency."""
    evidence_cycles = sum(allocation_summary_value(log, "relative_velocity_evidence_cycles") for log in logs)
    source_counts = aggregate_allocation_counter(logs, "relative_velocity_evidence_source_counts")
    return velocity_input_status(
        "relative velocity",
        evidence_cycles,
        total_cycles,
        source_counts,
    )


def velocity_input_status(
    name: str,
    evidence_cycles: int,
    total_cycles: int,
    source_counts: Counter[str],
) -> EvidenceSufficiencyInput:
    """Classify one velocity-family input."""
    if total_cycles <= 0:
        status = "unknown"
    elif evidence_cycles == total_cycles:
        status = "ready"
    elif evidence_cycles > 0:
        status = "provisional"
    else:
        status = "unknown"

    limitations = []
    if evidence_cycles != total_cycles:
        limitations.append(f"{total_cycles - evidence_cycles}/{total_cycles} cycles lack {name}")

    return EvidenceSufficiencyInput(
        name=name,
        status=status,
        scope="fitting baseline",
        summary=f"{evidence_cycles}/{total_cycles} cycles have {name} evidence.",
        limitations=limitations,
        evidence={"sources": dict(sorted(source_counts.items()))},
    )


def missile_profile_status(
    total_cycles: int,
    missing_inputs: Counter[str],
) -> EvidenceSufficiencyInput:
    """Classify missile profile data sufficiency."""
    missing = missing_inputs.get("missileProfileData", 0)
    if total_cycles <= 0:
        status = "unknown"
    elif missing == 0:
        status = "ready"
    elif missing < total_cycles:
        status = "provisional"
    else:
        status = "unknown"

    limitations = []
    if missing:
        limitations.append(f"{missing}/{total_cycles} cycles report missing missileProfileData")

    return EvidenceSufficiencyInput(
        name="missile profile data",
        status=status,
        scope="fitting baseline",
        summary=f"{total_cycles - missing}/{total_cycles} cycles have missile profile data.",
        limitations=limitations,
    )


def target_pd_status(
    logs: list[FittingLogReport],
    total_cycles: int,
    limitation_counts: Counter[str],
) -> EvidenceSufficiencyInput:
    """Classify target point-defense evidence sufficiency."""
    source_counts = aggregate_allocation_counter(logs, "pd_weight_evidence_source_counts")
    quality_counts = aggregate_allocation_counter(logs, "pd_evidence_quality_counts")
    capability_source_counts = aggregate_allocation_counter(logs, "pd_capability_evidence_source_counts")
    capability_observed_field_counts = aggregate_allocation_counter(logs, "pd_capability_observed_field_counts")
    capability_missing_reason_counts = aggregate_allocation_counter(logs, "pd_capability_missing_reason_counts")
    capability_limitation_counts = aggregate_allocation_counter(logs, "pd_capability_limitation_counts")
    observed = sum(allocation_summary_value(log, "pd_weight_observed_cycles") for log in logs)
    defaulted = sum(allocation_summary_value(log, "pd_weight_defaulted_cycles") for log in logs)
    unknown = sum(allocation_summary_value(log, "pd_weight_unknown_cycles") for log in logs)
    defaulted_decision_limits = limitation_counts.get("PD evidence defaulted", 0)

    if total_cycles <= 0:
        status = "unknown"
    elif defaulted_decision_limits:
        status = "defaulted"
    elif quality_counts.get("geometryAwareCapability", 0):
        status = "provisional"
    elif quality_counts.get("observedLiveCapability", 0):
        status = "provisional"
    elif quality_counts.get("observedTemplateCapability", 0):
        status = "provisional"
    elif quality_counts.get("observedPresenceOnly", 0):
        status = "presenceOnly"
    elif source_counts.get("observedTargetWeaponTemplates", 0):
        status = "presenceOnly"
    elif observed:
        status = "provisional"
    else:
        status = "unknown"

    limitations = []
    if quality_counts.get("observedTemplateCapability", 0):
        limitations.append(
            "observed target weapon templates include static capability fields, but not live readiness or geometry"
        )
    if quality_counts.get("observedLiveCapability", 0):
        limitations.append("live defensive weapon state is observed, but geometry/arc coverage is not fully proven")
    if quality_counts.get("geometryAwareCapability", 0):
        limitations.append(
            "geometry-aware PD evidence is present, but calibrated interception readiness still requires source-backed validation and real-log confirmation"
        )
    if quality_counts.get("observedPresenceOnly", 0) or (
        not quality_counts and source_counts.get("observedTargetWeaponTemplates", 0)
    ):
        limitations.append(
            "observed target weapon templates prove defense-mode presence, not calibrated PD capability"
        )
    for limitation, count in sorted(capability_limitation_counts.items()):
        limitations.append(f"{count} cycles report PD capability limitation: {limitation}")
    if defaulted_decision_limits:
        limitations.append(
            f"{defaulted_decision_limits} allocation/rejection decisions used default-model PD evidence"
        )
    elif defaulted:
        limitations.append(
            f"{defaulted}/{total_cycles} cycles used default-model PD only on non-allocation decisions"
        )
    if unknown:
        limitations.append(f"{unknown}/{total_cycles} cycles had unknown PD evidence")

    return EvidenceSufficiencyInput(
        name="observed target PD evidence",
        status=status,
        scope="fitting baseline",
        summary=(
            f"{observed}/{total_cycles} observed cycles, {defaulted} defaulted cycles, "
            f"{unknown} unknown cycles."
        ),
        limitations=limitations,
        evidence={
            "sources": dict(sorted(source_counts.items())),
            "quality": dict(sorted(quality_counts.items())),
            "capability_sources": dict(sorted(capability_source_counts.items())),
            "capability_observed_fields": dict(sorted(capability_observed_field_counts.items())),
            "capability_missing_reasons": dict(sorted(capability_missing_reason_counts.items())),
        },
    )


def observed_launch_delta_status(logs: list[FittingLogReport]) -> EvidenceSufficiencyInput:
    """Classify observed launch/ammo delta evidence for command validation."""
    try_fire_rows = sum(int(log.parser_summary.get("missile_try_fire_count", 0)) for log in logs)
    numeric_pairs = sum(
        int(log.parser_summary.get("missile_try_fire_pre_post_ammo_numeric_count", 0))
        for log in logs
    )
    if try_fire_rows <= 0:
        status = "unknown"
    elif numeric_pairs == try_fire_rows:
        status = "provisional"
    elif numeric_pairs:
        status = "provisional"
    else:
        status = "unknown"

    limitations = [
        "launch/ammo deltas are observation evidence, not controlled-command result evidence"
    ]
    if numeric_pairs != try_fire_rows:
        limitations.append(f"{try_fire_rows - numeric_pairs}/{try_fire_rows} try-fire rows lack numeric deltas")

    return EvidenceSufficiencyInput(
        name="observed launch/ammo delta evidence",
        status=status,
        scope="post-command validation design",
        summary=f"{numeric_pairs}/{try_fire_rows} MissileWeapon.TryFire rows have numeric pre/post ammo pairs.",
        limitations=limitations,
    )


def aggregate_report(input_path: Path, output_path: Path, logs: list[FittingLogReport]) -> AggregateReport:
    """Build aggregate report data."""
    classification_counts = Counter()
    limitation_counts = Counter()
    for log in logs:
        classification_counts.update(log.classification_counts)
        limitation_counts.update(log.limitation_counts)
    for classification in CLASSIFICATIONS:
        classification_counts.setdefault(classification, 0)

    verdict, reasons = readiness_verdict(logs)
    sufficiency = evidence_sufficiency_report(logs)
    return AggregateReport(
        input=str(input_path),
        output=str(output_path),
        log_count=len(logs),
        evidence_log_count=sum(1 for log in logs if log.has_required_evidence),
        real_evidence_log_count=sum(
            1 for log in logs if log.has_required_evidence and not log.synthetic_fixture
        ),
        synthetic_fixture_count=sum(1 for log in logs if log.synthetic_fixture),
        parser_failures=sum(1 for log in logs if log.parser_verdict != "OK"),
        classification_counts=dict(sorted(classification_counts.items())),
        limitation_counts=dict(sorted(limitation_counts.items())),
        readiness_verdict=verdict,
        readiness_reasons=reasons,
        evidence_sufficiency=sufficiency,
        logs=logs,
    )


def write_outputs(report: AggregateReport, output_path: Path) -> None:
    """Write per-log JSON, aggregate JSON, and aggregate Markdown."""
    if output_path.exists():
        ensure_safe_to_clear(output_path)
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    for index, log in enumerate(report.logs, start=1):
        name = safe_output_name(Path(log.path), index)
        (output_path / f"{name}.json").write_text(
            json.dumps(asdict(log), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    (output_path / "summary.json").write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_path / "shadow-fitting-report.md").write_text(
        format_markdown_report(report),
        encoding="utf-8",
    )


def ensure_safe_to_clear(output_path: Path) -> None:
    """Refuse to delete arbitrary non-empty directories."""
    if not output_path.is_dir() or not any(output_path.iterdir()):
        return

    if (output_path / "summary.json").exists() or (output_path / "shadow-fitting-report.md").exists():
        return

    artifacts_root = Path("artifacts/shadow-fitting").resolve()
    resolved_output = output_path.resolve()
    try:
        resolved_output.relative_to(artifacts_root)
    except ValueError as exc:
        raise SystemExit(
            "Refusing to overwrite non-empty directory without fitting report "
            f"sentinel outside {artifacts_root}: {output_path}"
        ) from exc


def safe_output_name(path: Path, index: int) -> str:
    """Return a stable filesystem-safe per-log output name."""
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem).strip("._")
    if not stem:
        stem = "log"
    return f"{index:02d}-{stem}"


def format_markdown_report(report: AggregateReport) -> str:
    """Format the aggregate fitting report."""
    lines = [
        "# Shadow allocation fitting report",
        "",
        "This report is generated from selected logs for offline fitting only. It",
        "does not prove live combat improvement and does not apply game commands.",
        "",
        "## Inputs",
        "",
        f"- input: `{report.input}`",
        f"- output: `{report.output}`",
        f"- logs analyzed: {report.log_count}",
        f"- logs with required evidence: {report.evidence_log_count}",
        f"- real selected logs with required evidence: {report.real_evidence_log_count}",
        f"- synthetic fixture logs: {report.synthetic_fixture_count}",
        f"- parser failures: {report.parser_failures}",
        "",
        "## Readiness verdict",
        "",
        f"- verdict: **{report.readiness_verdict}**",
    ]

    for reason in report.readiness_reasons:
        lines.append(f"- reason: {reason}")

    lines.extend(
        [
            "",
            "## Evidence sufficiency gate",
            "",
            f"- verdict: **{report.evidence_sufficiency.verdict}**",
            f"- controlled live command readiness: "
            f"**{report.evidence_sufficiency.controlled_command_readiness}**",
        ]
    )
    for reason in report.evidence_sufficiency.verdict_reasons:
        lines.append(f"- reason: {reason}")
    if report.evidence_sufficiency.command_blockers:
        for blocker in report.evidence_sufficiency.command_blockers:
            lines.append(f"- command blocker: {blocker}")
    else:
        lines.append("- command blocker: none")

    lines.extend(
        [
            "",
            "| input | status | scope | summary | limitations |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for input_status in report.evidence_sufficiency.inputs:
        limitations = "; ".join(input_status.limitations) if input_status.limitations else "none"
        lines.append(
            "| {name} | {status} | {scope} | {summary} | {limitations} |".format(
                name=markdown_cell(input_status.name),
                status=input_status.status,
                scope=markdown_cell(input_status.scope),
                summary=markdown_cell(input_status.summary),
                limitations=markdown_cell(limitations),
            )
        )

    lines.extend(
        [
            "",
            "## Classification counts",
            "",
        ]
    )
    for classification, count in report.classification_counts.items():
        lines.append(f"- {classification}: {count}")

    lines.extend(["", "## Evidence limitations", ""])
    if report.limitation_counts:
        for limitation, count in report.limitation_counts.items():
            lines.append(f"- {limitation}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Per-log summaries", ""])
    for log in report.logs:
        parser_reasons = "; ".join(log.parser_reasons) if log.parser_reasons else "none"
        missing = (
            ", ".join(log.missing_required_evidence)
            if log.missing_required_evidence
            else "none"
        )
        lines.extend(
            [
                f"### {Path(log.path).name}",
                "",
                f"- path: `{log.path}`",
                f"- parser verdict: {log.parser_verdict}",
                f"- parser reasons: {parser_reasons}",
                f"- required evidence missing: {missing}",
                f"- synthetic fixture: {'yes' if log.synthetic_fixture else 'no'}",
                "- classification counts: "
                + ", ".join(
                    f"{key}: {value}" for key, value in log.classification_counts.items()
                ),
                "- limitations: "
                + (
                    ", ".join(
                        f"{key}: {value}" for key, value in log.limitation_counts.items()
                    )
                    if log.limitation_counts
                    else "none"
                ),
                "",
            ]
        )

        if log.representative_records:
            lines.append("| line | type | target | class | reason | notes |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for record in log.representative_records[:8]:
                notes = "; ".join(record["notes"]) if record["notes"] else ""
                lines.append(
                    "| {line} | {record_type} | {target} | {classification} | "
                    "{reason} | {notes} |".format(
                        line=record["line"],
                        record_type=record["record_type"],
                        target=markdown_cell(str(record["target"])),
                        classification=record["classification"],
                        reason=markdown_cell(str(record["reason"])),
                        notes=markdown_cell(notes),
                    )
                )
            lines.append("")

    lines.extend(
        [
            "## Interpretation rules",
            "",
            "- Synthetic fixtures validate the wrapper only; they are not fitting evidence.",
            "- Evidence sufficiency statuses are separate from parser health and the",
            "  fitting baseline verdict. Empty `missingInputs` can still leave model",
            "  fidelity limits such as presence-only PD evidence.",
            "- Rows scoped to `fitting baseline` describe allocator-consumable",
            "  evidence for offline diagnostics; controlled-command sufficiency is",
            "  represented separately by command-readiness rows and blockers.",
            "- `command-safety no-op` means no allocation was made because no concrete",
            "  launcher-selected target identity was visible; it is safe skip evidence,",
            "  not allocation-quality evidence.",
            "- `presenceOnly` PD evidence means target defense-mode weapon templates",
            "  were observed, but calibrated vanilla interception pressure, cooldown,",
            "  ammo, arc, range geometry, and support behavior are not yet proven.",
            "- PD-defaulted evidence on allocation/rejection decisions can support at",
            "  most `Conditionally ready`.",
            "- Full `Ready for #6 baseline` requires multiple real selected logs with",
            "  required evidence, at least one plausible decision, no severe",
            "  classifications, and no PD-defaulted allocation/rejection evidence.",
            "- Controlled live command readiness remains separate from the fitting",
            "  baseline and requires command-intent, command-mapping, and live-safety",
            "  gates before Issue #6 can apply commands.",
        ]
    )
    return "\n".join(lines) + "\n"


def markdown_cell(text: str) -> str:
    """Escape text for a compact Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def main() -> None:
    """Parse arguments and generate fitting artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help=f"default: {DEFAULT_INPUT}")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"default: {DEFAULT_OUTPUT}")
    parser.add_argument("--max-issues", type=int, default=12, help="maximum issue lines to store per log")
    args = parser.parse_args()

    selected_logs = discover_logs(args.input)
    if not selected_logs:
        print(f"No selected logs found in {args.input}.")
        raise SystemExit(1)

    logs = [fitting_log_report(path, args.max_issues) for path in selected_logs]
    report = aggregate_report(args.input, args.output, logs)
    write_outputs(report, args.output)

    print(f"Analyzed {report.log_count} selected log(s).")
    print(f"Wrote fitting artifacts to {args.output}.")
    print(f"Readiness verdict: {report.readiness_verdict}")
    for reason in report.readiness_reasons:
        print(f"  - {reason}")

    if report.parser_failures or report.evidence_log_count == 0:
        raise SystemExit(1)

    raise SystemExit(0)


if __name__ == "__main__":
    main()
