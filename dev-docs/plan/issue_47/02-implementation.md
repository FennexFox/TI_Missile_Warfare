# Phase 02: Diagnostics-only outcome hooks

## Goal

- Add diagnostics-only outcome hook rows for the stable concrete surfaces found
  in Phase 01.

## Scope

- Add a default-off outcome diagnostics setting and UMM toggle.
- Patch concrete outcome methods through `PatchBootstrap`.
- Add an `OutcomeDiagnostics` logger that emits compact `[OutcomeLog]` rows.
- Extend `tools/parse_player_log.py` to summarize outcome rows separately.
- Document the hook table and attribution limits.

## Non-goals

- Allocator tuning.
- Live command changes.
- Combining outcome hook rows with command-spend proof classes.
- Runtime validation claims before a real combat smoke is run.

## Affected files

- `src/MissileFireControl.Mod/ModSettings.cs`
- `src/MissileFireControl.Mod/Main.cs`
- `src/MissileFireControl.Mod/Patches/PatchBootstrap.cs`
- `src/MissileFireControl.Mod/Diagnostics/OutcomeDiagnostics.cs`
- `tools/parse_player_log.py`
- `tools/fixtures/outcome_hooks.txt`
- `docs/diagnostics/hooks.md`
- `docs/research/reverse-engineering-plan.md`
- `dev-docs/plan/issue_47/*.md`

## Implementation steps

- Add the setting and UI toggle.
- Add concrete Harmony patches for missile damage, missile lifecycle, ship
  damage, and ship destruction.
- Implement reflection-based row fields for target, attacker, projectile,
  damage source, damage amount/type, weapon, hit position, result amount, and
  evidence-level labels.
- Add parser counters and a summary section for `[OutcomeLog]`.
- Update docs with confirmed source-review and runtime-validation status.

## Acceptance criteria

- Outcome hooks are diagnostics-only and return normally.
- Outcome rows use a separate marker and attribution vocabulary.
- Parser accepts older logs with three launch hooks and newer logs with
  additional zero-skipped outcome hooks.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m compileall tools
- python tools\parse_player_log.py --require-launchlogs

## Manual smoke tests

- Runtime smoke completed on the active 2026-06-29 `Player.log` with
  diagnostic logging and outcome diagnostics enabled.

## Rollback risks

- Disable `EnableOutcomeDiagnostics` to stop row emission while leaving patches
  loaded.
- Revert the outcome patch entries and `OutcomeDiagnostics.cs` to remove hook
  installation.

## Progress

- Completed implementation of the default-off `[OutcomeLog]` hook slice.

## Decision log

- Outcome logs are gated separately from base launch diagnostics so normal
  diagnostics can remain quiet for outcome rows.
- Parser health now requires the original three launch hooks and `skipped=0`,
  while allowing additive outcome hooks when present.
- The first parser fixture uses `patched=7`, covering the three launch hooks
  plus the four source-reviewed outcome hooks.

## Outcomes / Retrospective

- Added default-off outcome diagnostics, parser support, a fixture, and durable
  docs. The implementation remains diagnostics-only and does not change
  allocator behavior or command application.
- Follow-up runtime validation confirmed hook installation and row emission in
  a deployed combat log; AllocationLog-to-OutcomeLog correlation terminology
  remains a later issue.
