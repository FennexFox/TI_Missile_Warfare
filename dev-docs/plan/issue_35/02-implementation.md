# Phase 02: Command candidate logging and parser summaries

## Goal

- Emit diagnostics-only command-plan candidate rows and summarize them in the parser.

## Scope

- Add command-scope evidence and candidate classification to controlled dry-run logging.
- Add parser known record type and summary/report fields.
- Add/update synthetic fixtures.

## Non-goals

- No live command application.
- No vanilla command/action API calls.
- No target assignments, fire-mode changes, cooldowns, ammo changes, projectile/guidance changes, or combat AI changes.
- No #36 apply-gate hard-stop implementation.

## Affected files

- `src/MissileFireControl.Mod/Adapters/CombatSnapshotExtractor.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `tools/parse_player_log.py`
- `tools/fixtures/controlled_dry_run_experiment.txt`
- `tools/fixtures/command_resolvability_scope_skip.txt`

## Implementation steps

- Preserve runtime launcher object evidence for diagnostics-only scope checks.
- Resolve command scope from command-panel selection or verified active-player launcher evidence.
- Emit `recordType="dryRunCommandCandidate"` rows with classification, reason, scope source, scope violation, target, launcher, weapon, and ammo fields.
- Make `dryRunResult` intended/skipped/failed counts reflect candidate classifications.
- Extend parser dataclasses, known record types, parsing counters, JSON summary, and human report.
- Add fixture coverage for eligible and skipped candidates.

## Acceptance criteria

- Every dry-run allocation intent emits a command candidate row.
- Candidate classification is one of `eligible`, `wouldSkip`, or `wouldFail`.
- Parser reports eligible/skipped/failed candidate counts.
- Parser reports command scope source and missing-reason counts.
- Parser reports scope violation counts.
- `appliedCommands="0"` remains unchanged.

## Validation commands

- `python tools\parse_player_log.py tools\fixtures\controlled_dry_run_experiment.txt --require-launchlogs --require-snapshots`
- `python tools\parse_player_log.py tools\fixtures\command_resolvability_scope_skip.txt --require-launchlogs --require-snapshots`
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`
- `python -m compileall tools`
- `dotnet build TI_Missile_Fire_Control.sln`

## Manual smoke tests

- Deploy mod.
- Enable diagnostics, snapshot diagnostics, shadow allocation diagnostics, and controlled dry-run diagnostics.
- Trigger controlled dry-run in combat.
- Confirm candidate rows appear and parser reports classifications.
- Confirm no target, launch, weapon mode, cooldown, ammo, guidance, or AI behavior changes.

## Rollback risks

- Runtime rollback is straightforward: disable controlled dry-run diagnostics or revert this phase.
- Parser rollback would remove candidate summaries but leave #34 dry-run grouping intact.

## Progress

- Not started.

## Decision log

- No implementation decisions recorded yet.

## Outcomes / Retrospective

- Not completed yet.
