# Phase 02: Apply-gate diagnostics and parser summaries

## Goal

- Implement the diagnostics-only apply-gate hard stop and parser/fitting summaries.

## Scope

- Add default-off command-apply setting and UMM toggle copy.
- Emit `dryRunApplyGate` rows for eligible controlled dry-run command candidates.
- Extend `dryRunResult` with `safetyGateBlockedCommands`.
- Extend parser and fitting output with apply-gate record counts, blocked count, gate result counts, and block reason counts.
- Add deterministic fixture coverage for a blocked eligible candidate.

## Non-goals

- No live command APIs.
- No target assignment, weapon mode, launch discipline, ammo, cooldown, or scope-eligibility changes.

## Affected files

- `src/MissileFireControl.Mod/ModSettings.cs`
- `src/MissileFireControl.Mod/Main.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`
- `tools/fixtures/apply_gate_hard_stop.txt`

## Implementation steps

- Add `AllowCommandApply = false`.
- Add a UMM toggle that makes the safety boundary visible while stating this build still performs no live apply.
- Add `EvaluateCommandApplyGate` and `WriteDryRunApplyGate`.
- Call the gate only for `eligible` candidates during controlled dry-run cycles.
- Add parser counters and printed summary lines.
- Add fitting report aggregate/per-log safety-gate summary.
- Add fixture and parser smoke validation.

## Acceptance criteria

- Command application remains disabled by default.
- Controlled dry-run still runs with command application disabled.
- Eligible command plans reach `controlledCommandApplyGate`.
- `AllowCommandApply=false` blocks with `blockedBySafetyToggle`.
- Logs include experiment id, cycle id, candidate id, gate name, block reason, not-applied post-state, and `appliedCommands="0"`.
- Parser/fitting separate safety-gate blocks from skips/failures.

## Validation commands

- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\apply_gate_hard_stop.txt --require-launchlogs --require-snapshots

## Manual smoke tests

- Runtime smoke after deployment as described in Phase 01. Not required for deterministic fixture validation in this implementation pass.

## Rollback risks

- Additive schema rows may appear in newer logs; older parser versions would report them as unknown. This PR updates parser/fitting together with the schema.

## Progress

- Completed.

## Decision log

- Gate records remain under `[AllocationLog]` and the controlled dry-run record family so fitting ignores them as allocation-quality rows.
- `dryRunResult` now carries `safetyGateBlockedCommands`; parser counting uses the per-candidate gate rows and result total without double-counting.
- If `AllowCommandApply` is manually enabled in this diagnostics-only build, the gate can report `allowedDryRunOnly` / `applyPathNotImplemented`, but still applies zero commands.

## Outcomes / Retrospective

- Added default-off `AllowCommandApply`.
- Added `dryRunApplyGate` logging for eligible candidates only.
- Parser and fitting reports now summarize apply-gate records, blocked counts, gate results, and `blockedBySafetyToggle` reasons.
- Added deterministic `tools/fixtures/apply_gate_hard_stop.txt` coverage for the gate-reachable blocked path.
