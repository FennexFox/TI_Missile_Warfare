#!/usr/bin/env python3
"""Deterministic scaffold validation for TI Missile Fire Control."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    ".gitignore",
    ".gitattributes",
    "ModFile.json",
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

FORBIDDEN_PATHS = [
    "Directory.Build.props",
    "Assembly-CSharp.dll",
    "UnityModManager.dll",
    "0Harmony.dll",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing required paths:\n" + "\n".join(f"  - {x}" for x in missing))

    forbidden_found = []
    for forbidden in FORBIDDEN_PATHS:
        forbidden_found.extend(ROOT.rglob(forbidden))
    if forbidden_found:
        fail("forbidden local/binary files found:\n" + "\n".join(f"  - {x.relative_to(ROOT)}" for x in forbidden_found))

    mod_file = json.loads((ROOT / "ModFile.json").read_text(encoding="utf-8"))
    expected = {
        "Id": "MissileFireControl",
        "AssemblyName": "MissileFireControl.Mod.dll",
        "EntryMethod": "MissileFireControl.Mod.Main.Load",
    }
    for key, value in expected.items():
        if mod_file.get(key) != value:
            fail(f"ModFile.json {key!r} expected {value!r}, got {mod_file.get(key)!r}")

    cs_files = sorted(ROOT.rglob("*.cs"))
    if len(cs_files) < 15:
        fail(f"expected at least 15 C# files, found {len(cs_files)}")

    print("Scaffold layout OK")
    print(f"Root: {ROOT}")
    print(f"C# files: {len(cs_files)}")


if __name__ == "__main__":
    main()
