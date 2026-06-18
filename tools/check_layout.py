#!/usr/bin/env python3
"""Deterministic scaffold validation for TI MissileWarfare."""
from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    ".gitignore",
    ".gitattributes",
    "ModInfo.json",
    "Directory.Build.props.example",
    "TI_Missile_Fire_Control.sln",
    "docs/architecture.md",
    "docs/reverse-engineering-plan.md",
    "docs/mvp-issue-list.md",
    "src/MissileFireControl.Core/MissileFireControl.Core.csproj",
    "src/MissileFireControl.Core/Models/ShipSnapshot.cs",
    "src/MissileFireControl.Core/Calculators/PDScoreCalculator.cs",
    "src/MissileFireControl.Core/Allocation/SalvoAllocator.cs",
    "src/MissileFireControl.Mod/MissileFireControl.Mod.csproj",
    "src/MissileFireControl.Mod/Main.cs",
    "src/MissileFireControl.Mod/Patches/PatchBootstrap.cs",
]

LOCAL_ONLY_PATHS = [
    "Directory.Build.props",
]

FORBIDDEN_BINARY_NAMES = [
    "Assembly-CSharp.dll",
    "UnityModManager.dll",
    "0Harmony.dll",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def tracked_paths(paths: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--", *paths],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    return [line for line in result.stdout.splitlines() if line]


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing required paths:\n" + "\n".join(f"  - {x}" for x in missing))

    tracked_local_only = tracked_paths(LOCAL_ONLY_PATHS)
    if tracked_local_only:
        fail("local-only files are tracked:\n" + "\n".join(f"  - {x}" for x in tracked_local_only))

    forbidden_found = []
    for forbidden in FORBIDDEN_BINARY_NAMES:
        forbidden_found.extend(ROOT.rglob(forbidden))
    if forbidden_found:
        fail("forbidden local/binary files found:\n" + "\n".join(f"  - {x.relative_to(ROOT)}" for x in forbidden_found))

    mod_file = json.loads((ROOT / "ModInfo.json").read_text(encoding="utf-8"))
    expected = {
        "Id": "MissileWarfare",
        "DisplayName": "MissileWarfare",
        "Title": "MissileWarfare",
        "AssemblyName": "MissileFireControl.Mod.dll",
        "EntryMethod": "MissileFireControl.Mod.Main.Load",
    }
    for key, value in expected.items():
        if mod_file.get(key) != value:
            fail(f"ModInfo.json {key!r} expected {value!r}, got {mod_file.get(key)!r}")

    cs_files = sorted(ROOT.rglob("*.cs"))
    if len(cs_files) < 15:
        fail(f"expected at least 15 C# files, found {len(cs_files)}")

    print("Scaffold layout OK")
    print(f"Root: {ROOT}")
    print(f"C# files: {len(cs_files)}")


if __name__ == "__main__":
    main()
