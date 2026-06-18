#!/usr/bin/env python3
"""Create a local UMM mod folder after building MissileFireControl.Mod.dll.

This script does not build the DLL. It only packages already-built output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
MOD_METADATA_FILE = "ModInfo.json"


def load_mod_id() -> str:
    """Read and validate the UMM mod id from ModInfo.json."""
    metadata_path = ROOT / MOD_METADATA_FILE
    try:
        mod_info = json.loads(metadata_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"{MOD_METADATA_FILE} not found: {metadata_path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{MOD_METADATA_FILE} is invalid JSON: {exc}") from exc

    mod_id = mod_info.get("Id")
    if not isinstance(mod_id, str) or not mod_id.strip():
        raise SystemExit(f"{MOD_METADATA_FILE} must contain a non-empty string Id.")

    return mod_id.strip()


MOD_ID = load_mod_id()


def main() -> None:
    """Package already-built mod binaries into a local UMM mod folder."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration", default="Release", choices=["Debug", "Release"])
    parser.add_argument("--target-framework", default="net48")
    parser.add_argument("--output", default=str(ROOT / "dist" / MOD_ID))
    args = parser.parse_args()

    dll = ROOT / "src" / "MissileFireControl.Mod" / "bin" / args.configuration / args.target_framework / "MissileFireControl.Mod.dll"
    if not dll.exists():
        raise SystemExit(f"DLL not found: {dll}\nBuild the mod project first.")

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    legacy_metadata = output / "ModFile.json"
    if legacy_metadata.exists():
        legacy_metadata.unlink()
    shutil.copy2(ROOT / MOD_METADATA_FILE, output / MOD_METADATA_FILE)
    shutil.copy2(dll, output / "MissileFireControl.Mod.dll")

    core_dll = dll.parent / "MissileFireControl.Core.dll"
    if core_dll.exists():
        shutil.copy2(core_dll, output / "MissileFireControl.Core.dll")

    print(f"Packaged local mod folder: {output}")


if __name__ == "__main__":
    main()
