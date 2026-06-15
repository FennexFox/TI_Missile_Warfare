#!/usr/bin/env python3
"""Create a local UMM mod folder after building MissileFireControl.Mod.dll.

This script does not build the DLL. It only packages already-built output.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration", default="Release", choices=["Debug", "Release"])
    parser.add_argument("--target-framework", default="net472")
    parser.add_argument("--output", default=str(ROOT / "dist" / "MissileFireControl"))
    args = parser.parse_args()

    dll = ROOT / "src" / "MissileFireControl.Mod" / "bin" / args.configuration / args.target_framework / "MissileFireControl.Mod.dll"
    if not dll.exists():
        raise SystemExit(f"DLL not found: {dll}\nBuild the mod project first.")

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "ModFile.json", output / "ModFile.json")
    shutil.copy2(dll, output / "MissileFireControl.Mod.dll")

    core_dll = dll.parent / "MissileFireControl.Core.dll"
    if core_dll.exists():
        shutil.copy2(core_dll, output / "MissileFireControl.Core.dll")

    print(f"Packaged local mod folder: {output}")


if __name__ == "__main__":
    main()
