# Phase 02: Dry-run envelope and parser grouping

## Goal

- Implement the diagnostics-only controlled dry-run envelope and parser grouping.

## Scope

- Add settings and a one-shot UMM panel trigger.
- Add dry-run experiment state, selected-scope evidence capture, intent rows, and result rows.
- Extend parser summaries for controlled dry-run experiments.
- Add synthetic fixture coverage.

## Non-goals

- No live command application.
- No vanilla command API calls.
- No command resolvability proof; that belongs to #35.
- No allocator tuning.

## Affected files

- `src/MissileFireControl.Mod/ModSettings.cs`
- `src/MissileFireControl.Mod/Main.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `tools/parse_player_log.py`
- `tools/fixtures/controlled_dry_run_experiment.txt`

## Implementation steps

- Add `EnableControlledDryRunDiagnostics` setting.
- Add a UMM button that requests one controlled dry-run experiment only when diagnostics, shadow allocation diagnostics, and the new setting are enabled.
- Generate a stable local `experimentId`.
- Add `[AllocationLog]` rows:
  - `recordType="dryRunExperiment"`
  - `recordType="dryRunIntent"`
  - `recordType="dryRunResult"`
- Include selected-scope counts and missing reasons on experiment rows.
- Include intended command counts and `appliedCommands="0"` on result rows.
- Update parser known record types and summary fields.
- Add a fixture that proves parser grouping and zero applied commands.

## Acceptance criteria

- Controlled experiment mode is disabled by default.
- Player must explicitly trigger the dry-run.
- Triggering the dry-run cannot apply live commands.
- Logs include `experimentId`.
- Logs include selected ship identity/count where visible or explicit missing evidence when not visible.
- Parser output separates controlled dry-run records from normal shadow allocation.
- Parser/report shows intended dry-run command counts and `0 applied`.

## Validation commands

- `python tools\parse_player_log.py tools\fixtures\controlled_dry_run_experiment.txt --require-launchlogs --require-snapshots`
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`
- `python -m compileall tools`
- `python tools\check_layout.py`

## Manual smoke tests

- Deploy mod.
- Enable diagnostics, snapshot diagnostics, shadow allocation diagnostics, and controlled dry-run diagnostics.
- Select player missile ships in tactical combat.
- Press the controlled dry-run trigger once.
- Confirm no target, launch, weapon mode, cooldown, ammo, AI, or guidance behavior changes.
- Confirm `[AllocationLog]` dry-run rows appear with one experiment id and parse into a grouped summary.

## Rollback risks

- Runtime rollback is straightforward: revert this phase to remove the trigger and dry-run rows.
- Parser rollback would remove dry-run grouping but leave existing shadow allocation parsing intact.

## Progress

- Not started.

## Decision log

- No implementation decisions recorded yet.

## Outcomes / Retrospective

- Not completed yet.
