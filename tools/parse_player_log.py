#!/usr/bin/env python3
"""Summarize MissileWarfare markers in a Terra Invicta Player.log."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
import sys


DEFAULT_LOG = Path.home() / "AppData" / "LocalLow" / "Pavonis Interactive" / "TerraInvicta" / "Player.log"
MOD_PREFIX = "[MissileWarfare]"

VERSION_RE = re.compile(r"^\[MissileWarfare\] Version '(?P<version>[^']+)'\. Loading\.")
PATCH_RE = re.compile(r"^\[MissileWarfare\] \[MFC\] Patched (?P<description>.*?): (?P<target>.+)$")
BOOTSTRAP_RE = re.compile(
    r"^\[MissileWarfare\] \[MFC\] Combat launch diagnostics patch bootstrap complete\. "
    r"patched=(?P<patched>\d+), skipped=(?P<skipped>\d+)"
)
LAUNCH_RE = re.compile(r"^\[MissileWarfare\] \[MFC\] \[LaunchLog\] (?P<pairs>.*)$")
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
    issues: list[LineHit] = field(default_factory=list)


def parse_pairs(text: str) -> dict[str, str]:
    return {match.group("key"): match.group("value") for match in PAIR_RE.finditer(text)}


def is_issue_line(line: str) -> bool:
    if not line.startswith(MOD_PREFIX):
        return False

    lowered = line.lower()
    markers = ("[error]", "[exception]", "[warning]", " skipped ", " failed", "not loaded")
    return any(marker in lowered for marker in markers)


def parse_log(path: Path, max_issues: int) -> LogSummary:
    summary = LogSummary(path=str(path), exists=path.exists())
    if not path.exists():
        return summary

    summary.size_bytes = path.stat().st_size
    sequences: list[int] = []
    seen_sequences: set[int] = set()
    duplicate_sequences: set[int] = set()
    hook_counts: Counter[str] = Counter()

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

            if is_issue_line(line) and len(summary.issues) < max_issues:
                summary.issues.append(LineHit(line=line_number, text=line))

    summary.hook_counts = dict(sorted(hook_counts.items()))
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


def logger_verdict(summary: LogSummary, require_launchlogs: bool) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if not summary.exists:
        return "FAIL", ["Player.log was not found."]

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
    if require_launchlogs and summary.launch_log_count == 0:
        reasons.append("No LaunchLog entries were found.")
    if summary.sequence_gaps:
        reasons.append("LaunchLog sequence gaps found: " + ", ".join(summary.sequence_gaps[:8]))
    if summary.duplicate_sequences:
        reasons.append("Duplicate LaunchLog sequences found: " + ", ".join(map(str, summary.duplicate_sequences[:8])))

    return ("FAIL" if reasons else "OK"), reasons


def print_summary(summary: LogSummary, require_launchlogs: bool) -> None:
    verdict, reasons = logger_verdict(summary, require_launchlogs)
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", nargs="?", type=Path, default=DEFAULT_LOG, help=f"default: {DEFAULT_LOG}")
    parser.add_argument("--json", action="store_true", help="emit the parsed summary as JSON")
    parser.add_argument("--max-issues", type=int, default=12, help="maximum issue lines to print/store")
    parser.add_argument(
        "--require-launchlogs",
        action="store_true",
        help="fail when startup markers are present but no combat LaunchLog entries were emitted",
    )
    args = parser.parse_args()

    summary = parse_log(args.log, args.max_issues)
    verdict, _reasons = logger_verdict(summary, args.require_launchlogs)

    if args.json:
        print(json.dumps(asdict(summary), indent=2, ensure_ascii=False))
    else:
        print_summary(summary, args.require_launchlogs)

    raise SystemExit(0 if verdict == "OK" else 1)


if __name__ == "__main__":
    main()
