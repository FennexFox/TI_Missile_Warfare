# Phase 02: Validation and issue closure checks

## Goal

- Validate Issue #4 cleanup locally and document any manual smoke limits.

## Scope

- Run static build/layout/lint/parser checks.
- Confirm no current code/parser schema uses legacy shot-budget terminology.
- Confirm the change remains observation-only by source inspection.

## Non-goals

- Do not perform a live Terra Invicta smoke test unless the game/mod runtime is
  available in this session.
- Do not close or mutate GitHub issue state unless explicitly requested after
  validation.

## Affected files

- `dev-docs/plan/issue_4/**`
- Validation outputs only; no additional source files are expected unless a
  validation failure requires a fix.

## Implementation steps

- Run the listed validation commands where possible.
- Inspect `git diff` for command-application APIs or unrelated Issue #21 edits.
- Update this phase with validation outcomes.

## Acceptance criteria

- Required static validation passes or any failures are explicitly documented.
- Manual live smoke gap is documented if it cannot be run locally.
- Issue #4 files are ready for review without staging unrelated work.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools/check_layout.py
- python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py
- python -m compileall tools
- .\\build.ps1
- python tools/parse_player_log.py --require-launchlogs --require-snapshots

## Manual smoke tests

- Same as Phase 01 live smoke test. If not run locally, verify parser output
  against the active `Player.log` and document the live-smoke gap.

## Rollback risks

- Low. Verification-only changes should be plan/documentation updates.

## Progress

- Completed local validation.

## Decision log

- Live Terra Invicta smoke was not rerun in-session. The active `Player.log`
  parser validation and prior runtime-history smoke are the local evidence for
  Issue #4 closure; the new build was packaged and deployed by `build.ps1`.

## Outcomes / Retrospective

- `dotnet build TI_Missile_Fire_Control.sln`: passed with 0 warnings and 0
  errors.
- `python tools/check_layout.py`: passed.
- `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py`:
  passed.
- `python -m compileall tools`: passed.
- `.\\build.ps1`: passed, packaged, and deployed.
- `python tools/parse_player_log.py --require-launchlogs --require-snapshots`:
  passed with parser verdict `OK`, 748 snapshot rows, 748 shadow cycles, 748
  allocation rows, 0 no-op rows in the active historical log, and no
  MissileWarfare issues.
- Synthetic parser smoke with one `recordType="noOp"` row passed and confirmed
  no-op reason bucketing.
- Source inspection of the changed files found no command application, target
  assignment, fire-mode mutation, launch suppression, ammo mutation, AI
  behavior change, or manual-control mutation.
