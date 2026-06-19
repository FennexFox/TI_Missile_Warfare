# Phase 03: Runtime validation and documentation

## Goal

Validate the ready-shot diagnostics in a live combat log and document the confirmed source, fallback behavior, and remaining gaps.

## Scope

- Run static validation after implementation.
- Parse runtime logs for `readyShots`, `remainingShots`, missing fields, and any new source/evidence fields.
- Document findings locally and prepare a GitHub issue #11 comment for user review unless explicit GitHub write approval is given.
- Decide whether issue #11 is complete or whether a follow-up observation point is needed.

## Non-goals

- Do not broaden implementation during verification unless validation proves a small parser/doc fix is required.
- Do not change combat behavior or start recommendation/allocation work.

## Affected files

- `docs/battle-snapshot-extractor.md`
- `docs/confirmed-hooks.md`
- `tools/parse_player_log.py`
- `docs/plan/issue_11/03-verification.md`
- GitHub issue #11 comment draft

## Implementation steps

- Run all validation commands from this phase.
- Deploy the mod and run a short missile combat when local game access is available.
- Parse the log and record counts for `readyShots`, `remainingShots`, missing fields, and warnings/errors.
- Update docs with exact runtime counts and source names.
- Prepare a concise GitHub issue #11 comment with results and remaining risks for user review. Post it only when explicit GitHub write approval is given.

## Acceptance criteria

- Static validation passes.
- Parser verdict is `OK` for launch and snapshot requirements.
- Runtime findings clearly state whether `readyShots` is recovered, partially recovered, or still unavailable.
- Live smoke test produces no MissileWarfare warnings/errors.
- Documentation records the confirmed source or explains why the source remains unknown.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools/check_layout.py
- python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py
- python -m compileall tools
- .\build.ps1
- python tools/parse_player_log.py --require-launchlogs --require-snapshots

## Manual smoke tests

- Deploy with `.\build.ps1`.
- Enable `EnableDiagnostics` and `EnableSnapshotDiagnostics`.
- Run a short missile combat with missile launches.
- Parse the active `Player.log`; if the game overwrote it, parse `Player-prev.log`.

## Rollback risks

- Documentation-only changes are low risk.
- If diagnostics cause overhead or log spam, disable battle snapshot diagnostics or revert Phase 2.

## Progress

- Planned.

## Decision log

- Runtime validation should compare against the Issue #10 baseline carefully: one focused-target smoke run showed launcher-selected target identity at 671/671 snapshots, but that is not a general guarantee and is not proof of actual in-flight missile guidance target identity. Ready shots remained unknown in that run.

## Outcomes / Retrospective

- Not completed yet.
