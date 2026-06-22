# Phase 02: Single-command apply and parser reporting

## Goal

- Add the live apply attempt behind the existing hard-stop gate and teach parser output to summarize applied/skipped/failed controlled apply rows.

## Scope

- Convert the gate-allowed case from `allowedDryRunOnly/applyPathNotImplemented` into one guarded reflection invocation of the reviewed vanilla command path.
- Cap each controlled experiment at one attempt.
- Log additive first-live-apply result rows with experiment id, candidate id, scope, target, intent, pre-state, result, failure reason, and visible post-state.
- Extend parser summaries for controlled live apply attempts.
- Add a deterministic fixture covering one applied row and dry-run result counts.

## Non-goals

- No multi-ship or group-selected live apply.
- No retries, continuous automation, allocator tuning, launch suppression, projectile changes, or direct ammo/cooldown mutation.
- No Core dependency on Terra Invicta, Unity, Harmony, or UMM.

## Affected files

- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `tools/parse_player_log.py`
- `tools/fixtures/first_live_apply.txt`

## Implementation steps

- Add a small command-result model for `applied`, `skipped`, and `failed` live attempts.
- Resolve runtime launcher and target objects from the current snapshot and re-check identity against the candidate immediately before invocation.
- Find `SelectSalvoTargetCommand` and invoke `OnCommandExecute` only if the exact runtime parameter types are compatible.
- Treat missing type/method/object identity, invocation exceptions, and scope mismatch as skip/fail rows with explicit reasons.
- Update dry-run result counts to include applied/failed command totals.
- Add parser counters and printed summary fields for first-live-apply rows.

## Acceptance criteria

- Controlled command application remains disabled by default.
- Live command application requires the explicit controlled trigger and `AllowCommandApply=True`.
- Exactly one candidate can attempt a live apply per trigger.
- Ambiguous command plans skip/fail closed with reasons.
- Logs pair result rows with `experimentId` and `candidateId`.
- Parser/report distinguishes applied, skipped, and failed live command attempts.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\first_live_apply.txt --require-launchlogs --require-snapshots

## Manual smoke tests

- Deploy the mod, enter tactical combat, select exactly one player missile ship, enable controlled dry-run diagnostics and `AllowCommandApply`, trigger once, then parse the fresh log.
- Confirm parser reports at most one applied/failed live command, no scope violations, no unknown record types, and no MissileWarfare warnings/errors.

## Rollback risks

- Disable `AllowCommandApply` to restore the #36 hard-stop behavior at runtime.
- Revert this phase to remove the live invocation and parser schema additions.

## Progress

- Completed.

## Decision log

- `activePlayerLauncher` fallback diagnostics are not sufficient for #37 live apply; first-live apply requires a selected command-panel source with exactly one ship.
- The result row uses existing parser-known record types: `appliedDecision`, `skippedDecision`, and `failedCommand`.
- The live command path is invoked by reflection so `MissileFireControl.Core` remains independent of Terra Invicta and the mod project avoids compile-time game type coupling.
- `dryRunResult` remains the aggregate controlled experiment result row, but it can now report nonzero `appliedCommands` for #37.

## Outcomes / Retrospective

- Added one-attempt controlled live apply flow behind `controlledCommandApplyGate`.
- Added fail-closed checks for single selected command scope, runtime launcher/target objects, identity match, command type/method lookup, command construction, and invocation exceptions.
- Added `appliedDecision` / `skippedDecision` / `failedCommand` controlled result logging with command path, reason, pre-state, post-state, applied count, and failed count.
- Extended parser summaries with controlled live apply attempts, applied/skipped/failed counts, reason counts, and command path counts.
- Added `tools/fixtures/first_live_apply.txt` to exercise the parser/report shape for one allowed and applied first-live command.
