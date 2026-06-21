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
            "- `command-safety no-op` means no allocation was made because no concrete",
            "  launcher-selected target identity was visible; it is safe skip evidence,",
            "  not allocation-quality evidence.",
            "- PD-defaulted evidence on allocation/rejection decisions can support at",
            "  most `Conditionally ready`.",
            "- Full `Ready for #6 baseline` requires multiple real selected logs with",
            "  required evidence, at least one plausible decision, no severe",
            "  classifications, and no PD-defaulted allocation/rejection evidence.",
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
