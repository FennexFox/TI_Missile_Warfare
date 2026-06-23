# Phase 03: Documentation and validation

## Goal

- Document #35 diagnostics and complete validation.

## Scope

- Update durable diagnostics/planning docs.
- Run static and fixture validation.
- Record runtime smoke status.

## Non-goals

- No additional code beyond defects found during validation.
- No live command smoke.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_35/*.md`

## Implementation steps

- Document command-candidate schema and parser summary fields.
- State that #35 remains diagnostics-only and still applies zero commands.
- Run fixture parser validation, ruff, compileall, layout, and build.
- Update phase outcomes.

## Acceptance criteria

- Durable docs describe command-candidate rows and safety boundary.
- Validation commands are recorded.
- Runtime smoke limitations are explicit if not run.

## Validation commands

- `python tools\check_layout.py`
- `python tools\parse_player_log.py tools\fixtures\controlled_dry_run_experiment.txt --require-launchlogs --require-snapshots`
- `python tools\parse_player_log.py tools\fixtures\command_resolvability_scope_skip.txt --require-launchlogs --require-snapshots`
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`
- `python -m compileall tools`
- `dotnet build TI_Missile_Fire_Control.sln`

## Manual smoke tests

- Runtime smoke completed against the live Terra Invicta `Player.log`.

## Rollback risks

- Documentation-only rollback risk is low.

## Progress

- Complete. Local validation and live runtime smoke both pass the #35
  diagnostics-only safety criteria.

## Decision log

- #35 remains diagnostics-only. Runtime smoke should verify parser output and
  zero applied commands before any later live command-application work.

## Outcomes / Retrospective

- Local fixture validation passes for eligible and skip-closed candidates.
- `dotnet build TI_Missile_Fire_Control.sln` passes with zero warnings and zero
  errors.
- Fitting report generation now keeps controlled dry-run rows out of allocation
  quality classifications and reports dry-run command evidence separately.
- Live logs at `Player.log` and `Player-prev.log` contained 9 controlled
  dry-run experiments, 7 command candidates, 0 scope violations, 0 applied
  commands, and 0 failed commands. All candidates skipped with
  `reason="unsafeScope"` because command scope reported
  `activePlayerUnavailable`.
- The active-player fallback now reads `GameControl.control.activePlayer`.
  A follow-up live log then changed the command-scope missing reason to
  `nonPlayerOrAIControlled`, confirming that the active-player lookup path is
  no longer missing and that non-player launcher candidates skip closed.
- The selected-scope resolver now also checks the decompiled runtime HUD path
  `GameControl.spaceCombat.combatHUD`.
- A later live log confirmed that selected scope is visible through
  `GameControl.spaceCombat.combatHUD.selectedFriendlyShipState` in runtime:
  3 controlled dry-run experiments, 3 command candidates, 0 applied commands,
  0 failed commands, and 0 scope violations. One experiment had
  `selectedShipCount="1"` and skipped the allocator-motivated launcher with
  `reason="outsidePlayerControlledScope"` because the launcher was not in the
  selected command scope. The other two skipped as `nonPlayerOrAIControlled`.
- `tools/parse_player_log.py` now configures stdout as UTF-8 so runtime ship
  names containing non-ASCII characters do not crash parser output on Windows
  code pages.
