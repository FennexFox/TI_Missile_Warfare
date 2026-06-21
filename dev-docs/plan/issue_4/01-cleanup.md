# Phase 01: No-op logging, parser separation, and docs cleanup

## Goal

- Make Issue #4 shadow allocation diagnostics fully explain no-op/skip cases
  and update durable docs to the post-PR #20 schema.

## Scope

- Add an explicit shadow-allocation no-op record when a cycle cannot produce an
  allocation/rejection recommendation.
- Teach `tools/parse_player_log.py` to bucket no-op/skip records and reasons
  separately from rejections.
- Update diagnostics, roadmap, README, and runtime-history docs for current
  ammo/gate-budget terminology and parser behavior.

## Non-goals

- Do not add any command application, target assignment, fire-mode update,
  launch suppression, AI behavior change, or player-control mutation.
- Do not edit the unrelated Issue #21 plan.

## Affected files

- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `tools/parse_player_log.py`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/planning/mvp-roadmap.md`
- `README.md`

## Implementation steps

- Emit `recordType="noOp"` with `noOpReason` for missing required inputs,
  unavailable allocation results, missing ammo/gate budget, zero ammo/gate
  budget, or otherwise empty shadow decisions.
- Add parser fields, counters, JSON data, and human-readable report lines for
  no-op/skip decisions and reasons.
- Document the `noOp` schema and post-PR #20 closure evidence.

## Acceptance criteria

- Shadow allocation remains observation-only.
- Cycle/allocation/rejection/no-op rows are distinguishable.
- Parser output separates cycle status, allocations, rejections, missing inputs,
  no-op/skip reasons, and future controlled-apply records.
- Durable current docs use `ammoGateBudgetShots` /
  `totalAmmoGateBudgetShots` for the validated budget.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools/check_layout.py
- python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py
- python -m compileall tools
- .\\build.ps1
- python tools/parse_player_log.py --require-launchlogs --require-snapshots

## Manual smoke tests

- Deploy the mod, enable diagnostics, battle snapshot diagnostics, and shadow
  allocation diagnostics, then run a short missile combat.
- Confirm allocation cycle/allocation/rejection/no-op records appear as
  applicable and no combat behavior changes.
- Confirm no MissileWarfare warnings/errors appear.

## Rollback risks

- Low runtime risk because the changes only add log records and parser fields.
  Roll back by reverting the diagnostic writer/parser/doc edits or disabling
  shadow allocation diagnostics.

## Progress

- Completed implementation cleanup.

## Decision log

- Represent shadow no-op/skip outcomes as `recordType="noOp"` so parser
  summaries can separate them from tactical rejections.

## Outcomes / Retrospective

- No-op logging, parser bucketing, and docs cleanup completed.
