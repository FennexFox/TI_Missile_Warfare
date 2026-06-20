# Phase 03: Parser reporting and documentation

## Goal

Teach the parser and docs to distinguish numeric ready-shot cycles from unknown,
ammo-only, and missing-readiness cycles.

## Scope

- Extend `tools/parse_player_log.py` summary dataclasses and report output.
- Count readiness evidence sources and missing reasons from `SnapshotLog` and
  allocation cycle rows.
- Add conservative suspicious-pattern text when all cycles have ammo-only or missing
  readiness evidence.
- Update Issue #15 documentation in battle snapshot and confirmed hooks docs.

## Non-goals

- No parser requirement that new fields are present in older logs.
- No inferred combat quality conclusions from partial readiness data.

## Affected files

- `tools/parse_player_log.py`
- `docs/battle-snapshot-extractor.md`
- `docs/confirmed-hooks.md`

## Implementation steps

1. Add optional counters for snapshot/allocation readiness source and missing reason.
2. Add allocation summary fields for ammo-only evidence and blocked-by-missing-readiness
   cycles.
3. Parse new fields only when present.
4. Print compact human-readable readiness evidence sections.
5. Ensure JSON output includes the new dataclass fields.
6. Update docs with the final Issue #15 finding and readiness gate for Issue #6.

## Acceptance criteria

- Parser distinguishes numeric ready-shot cycles from unknown cycles.
- Parser reports evidence source and missing-reason histograms.
- Parser identifies ammo-only readiness evidence and missing-readiness blockers.
- Older logs still parse without new fields.
- Docs record whether the project is ready for controlled allocation.

## Validation commands

- `python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py`
- `python -m compileall tools`
- `python tools\parse_player_log.py --require-launchlogs --require-snapshots`
- `python tools\parse_player_log.py --json --require-launchlogs --require-snapshots`

## Manual smoke tests

- Review parser output on the current local `Player.log` if available.
- Note that existing logs may not contain newly added fields until the mod is deployed
  and a fresh combat log is collected.

## Rollback risks

- Parser changes are additive but may affect report text. Keep old field parsing intact.

## Progress

- Added parser summary fields for snapshot and allocation readiness evidence sources,
  missing reasons, ammo evidence sources, and live weapon states.
- Added allocation summary counts for ammo-only readiness cycles and missing-readiness
  evidence cycles.
- Added human-report sections for readiness evidence while preserving older log parsing.
- Updated battle snapshot and confirmed hook docs with Issue #15 semantics.
- Ran parser validation commands: Ruff, compileall, text parser smoke, and JSON parser
  smoke all passed.

## Decision log

- Existing logs without Issue #15 fields remain valid; new histograms are empty for
  those logs.
- Old logs with `missingInputs=readyShots` still count as missing-readiness evidence
  cycles, so parser output remains useful before deploying the new build.
- `ammo-only readiness cycles` is based on explicit `readinessMissingReason` text so it
  does not infer ammo semantics from old logs.

## Outcomes / Retrospective

- Completed. Parser and docs now distinguish numeric, unknown, ammo-only, and missing
  readiness evidence without treating ammo or gate state as ready-shot counts.
