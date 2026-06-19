#!/usr/bin/env python3
"""Summarize MissileWarfare markers in a Terra Invicta Player.log."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re


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
PAIR_RE = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9_]*)=\"(?P<value>[^\"]*)\"")


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
    snapshot_log_count: int = 0
    snapshot_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_missing_counts: dict[str, int] = field(default_factory=dict)
    snapshot_ready_shots_counts: dict[str, int] = field(default_factory=dict)
    snapshot_known_target_count: int = 0
    snapshot_target_identity_source_counts: dict[str, int] = field(default_factory=dict)
    snapshot_target_counts: dict[str, int] = field(default_factory=dict)
    snapshot_target_team_counts: dict[str, int] = field(default_factory=dict)
    first_snapshot_line: int | None = None
    last_snapshot_line: int | None = None
    allocation_log_count: int = 0
    allocation_record_type_counts: dict[str, int] = field(default_factory=dict)
    allocation_status_counts: dict[str, int] = field(default_factory=dict)
    allocation_missing_input_counts: dict[str, int] = field(default_factory=dict)
    allocation_rejection_reason_counts: dict[str, int] = field(default_factory=dict)
    allocation_assigned_shots_counts: dict[str, int] = field(default_factory=dict)
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
    snapshot_source_counts: Counter[str] = Counter()
    snapshot_missing_counts: Counter[str] = Counter()
    snapshot_ready_shots_counts: Counter[str] = Counter()
    snapshot_target_identity_source_counts: Counter[str] = Counter()
    snapshot_target_counts: Counter[str] = Counter()
    snapshot_target_team_counts: Counter[str] = Counter()
    allocation_record_type_counts: Counter[str] = Counter()
    allocation_status_counts: Counter[str] = Counter()
    allocation_missing_input_counts: Counter[str] = Counter()
    allocation_rejection_reason_counts: Counter[str] = Counter()
    allocation_assigned_shots_counts: Counter[str] = Counter()
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
                snapshot_ready_shots_counts[pairs.get("readyShots", "unknown")] += 1

                target_id = pairs.get("targetId", "unknown")
                target_name = pairs.get("target", "unknown")
                if target_id and target_id != "unknown":
                    summary.snapshot_known_target_count += 1
                    snapshot_target_counts[f"{target_name}#{target_id}"] += 1

                target_identity_source = pairs.get("targetIdentitySource")
                if target_identity_source:
                    snapshot_target_identity_source_counts[target_identity_source] += 1

                target_team = pairs.get("targetTeam")
                if target_team:
                    snapshot_target_team_counts[target_team] += 1

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

            allocation = ALLOCATION_RE.match(line)
            if allocation:
                pairs = parse_pairs(allocation.group("pairs"))
                summary.allocation_log_count += 1

                record_type = pairs.get("recordType", "unknown")
                allocation_record_type_counts[record_type] += 1

                status = pairs.get("status")
                if status:
                    allocation_status_counts[status] += 1

                missing = pairs.get("missingInputs")
                if missing and missing != "none":
                    for field_name in missing.split(","):
                        field_name = field_name.strip()
                        if field_name:
                            allocation_missing_input_counts[field_name] += 1

                rejection_reason = pairs.get("rejectionReason")
                if rejection_reason:
                    allocation_rejection_reason_counts[rejection_reason] += 1

                assigned_shots = pairs.get("assignedShots")
                if assigned_shots:
                    allocation_assigned_shots_counts[assigned_shots] += 1

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
    summary.snapshot_source_counts = dict(sorted(snapshot_source_counts.items()))
    summary.snapshot_missing_counts = dict(sorted(snapshot_missing_counts.items()))
    summary.snapshot_ready_shots_counts = dict(sorted(snapshot_ready_shots_counts.items()))
    summary.snapshot_target_identity_source_counts = dict(sorted(snapshot_target_identity_source_counts.items()))
    summary.snapshot_target_counts = dict(snapshot_target_counts.most_common(12))
    summary.snapshot_target_team_counts = dict(sorted(snapshot_target_team_counts.items()))
    summary.allocation_record_type_counts = dict(sorted(allocation_record_type_counts.items()))
    summary.allocation_status_counts = dict(sorted(allocation_status_counts.items()))
    summary.allocation_missing_input_counts = dict(sorted(allocation_missing_input_counts.items()))
    summary.allocation_rejection_reason_counts = dict(allocation_rejection_reason_counts.most_common(12))
    summary.allocation_assigned_shots_counts = dict(sorted(allocation_assigned_shots_counts.items()))
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
    if summary.bootstrap_patched != 3 or summary.bootstrap_skipped != 0:
        reasons.append(
            "Expected diagnostics bootstrap patched=3 and skipped=0; "
            f"got patched={summary.bootstrap_patched}, skipped={summary.bootstrap_skipped}."
        )
    if len(summary.patched_hooks) != 3:
        reasons.append(f"Expected 3 patched hook lines; found {len(summary.patched_hooks)}.")
    if require_launchlogs and startup_markers_present and summary.launch_log_count == 0:
        reasons.append("No LaunchLog entries were found.")
    if require_snapshots and startup_markers_present and summary.snapshot_log_count == 0:
        reasons.append("No SnapshotLog entries were found.")
    if summary.sequence_gaps:
        reasons.append("LaunchLog sequence gaps found: " + ", ".join(summary.sequence_gaps[:8]))
    if summary.duplicate_sequences:
        reasons.append("Duplicate LaunchLog sequences found: " + ", ".join(map(str, summary.duplicate_sequences[:8])))

    return ("FAIL" if reasons else "OK"), reasons


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
            print("  missile try-fire readiness evidence:")
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
        if summary.snapshot_ready_shots_counts:
            print("  readyShots:")
            for value, count in summary.snapshot_ready_shots_counts.items():
                print(f"    {value}: {count}")
        print(
            "  target identity: "
            f"{summary.snapshot_known_target_count}/{summary.snapshot_log_count} snapshots"
        )
        if summary.snapshot_target_identity_source_counts:
            print("  target identity sources:")
            for source, count in summary.snapshot_target_identity_source_counts.items():
                print(f"    {source}: {count}")
        if summary.snapshot_target_counts:
            print("  targets:")
            for target, count in summary.snapshot_target_counts.items():
                print(f"    {target}: {count}")
        if summary.snapshot_target_team_counts:
            print("  target teams:")
            for team, count in summary.snapshot_target_team_counts.items():
                print(f"    {team}: {count}")

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
        if summary.allocation_assigned_shots_counts:
            print("  assigned shots:")
            for assigned_shots, count in summary.allocation_assigned_shots_counts.items():
                print(f"    {assigned_shots}: {count}")
        if summary.allocation_rejection_reason_counts:
            print("  rejection reasons:")
            for reason, count in summary.allocation_rejection_reason_counts.items():
                print(f"    {reason}: {count}")

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
