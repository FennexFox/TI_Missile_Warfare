# MVP roadmap

This roadmap records durable issue-sized work. Temporary per-PR plans belong under `dev-docs/plan/**` and may be deleted after the PR is merged, closed, or abandoned.

## Current milestone state

The project has enough diagnostics to observe missile launches and shadow allocation inputs, but it is not ready for controlled command application.

Current blocker:

- Issue #17 resolved the shot-budget design gate to Path A:
  `TISpaceShipState.ammo[weaponData]` plus vanilla fire gates is the
  game-equivalent per-weapon fire budget. The mod names this explicit value
  `ammoGateBudgetShots`; no distinct loaded/chambered source was found. See
  [`readiness-semantics.md`](../research/readiness-semantics.md).

Current missing or provisional inputs:

- selected-player command scope;
- target point-defense weapon weights;
- in-flight projectile/controller guidance target identity.

## Completed diagnostic foundation

### Issue 1: Create UMM/Harmony scaffold

Goal: make the mod load without changing gameplay.

Status: complete as scaffold foundation.

Completion evidence:

- UMM displays the mod.
- Settings panel opens.
- Diagnostic ping writes to logs.
- Harmony patches are diagnostics-first and should not alter combat behavior.

### Issue 2: Identify combat launch entry points

Goal: locate methods involved in missile launch decisions.

Status: complete for the initial diagnostics set.

Completion evidence:

- Confirmed launch hook notes are in [`diagnostics/hooks.md`](../diagnostics/hooks.md).
- At least one log-only patch fires during tactical combat.
- Logs include battle context and method names.

### Issue 3: Add battle snapshot extractor

Goal: convert visible game combat objects into Core snapshots.

Status: complete as observation-only diagnostics, with known missing inputs.

Completion evidence:

- Snapshot extraction is wired to the confirmed missile projectile hook.
- Launcher, missile profile, conservative weapon role, and partial target identity are logged when visible.
- Missing fields are reported explicitly instead of being treated as fatal.
- Snapshot logging can be enabled/disabled from settings.

Implementation notes: [`diagnostics/snapshot-and-allocation.md`](../diagnostics/snapshot-and-allocation.md). Runtime smoke history: [`runtime-validation-history.md`](../diagnostics/runtime-validation-history.md).

### Issue 4: Recommendation-only salvo allocation

Goal: produce target/shots recommendations without applying commands.

Status: complete as observation-only shadow diagnostics.

Completion evidence:

- Shadow allocation logs cycle/allocation/rejection/no-op records without changing commands.
- Parser summaries distinguish evaluated cycles, skipped cycles, missing inputs, allocations, rejections, no-op/skip reasons, and future controlled-apply records.
- Post-PR #20 runtime smoke validated numeric `ammoGateBudgetShots`, target velocity, and relative velocity evidence in shadow allocation logs.
- Numeric sample rows are schema examples unless all required runtime inputs are present and documented.

### Issue 5: Add debug UI or hotkey

Goal: expose recommendations during combat.

Status: not the current blocker.

Acceptance criteria:

- Player can trigger recommendation generation on demand.
- Output is readable in UMM log or an in-game panel.
- The UI clearly says recommendation-only.

## Blocked controlled features

### Issue 6: Controlled auto-allocation command

Goal: apply target assignments for selected friendly missile ships.

Status: blocked pending selected-player command scope validation and
command-application safety work.

Do not implement Issue 6 around a fictitious `readyShots` source. Issue #17
validated the per-weapon `ammoGateBudgetShots` semantics, but controlled command
application still needs a verified selected-player command path and must let
vanilla combat enforce the final legal launch result.

Future #6 design should log selected player ship identity, visible weapon/module
identity, `ammoGateBudgetShots` and its evidence source, the allocator
recommendation that motivated the command, command intent and target,
skipped/failure reason, and observed ammo delta or launch evidence when
available.

Additional gate: selection scope must be based on a verified player-selection or player-command hook. Until then, command application remains disabled.

Acceptance criteria once unblocked:

- Selection scope is based on a verified player-selection or player-command hook.
- Existing manual control remains possible after the selected-ship command path is verified.
- Recommendation-only mode prevents command changes.
- Failures are logged without breaking combat.

### Issue 7: Launch discipline prototype

Goal: prevent obviously wasteful launches.

Status: blocked on runtime scoring inputs.

Acceptance criteria once unblocked:

- Launch window score is computed only from validated range and target/relative-velocity evidence; otherwise the score is marked provisional or unavailable.
- Conservative/balanced/aggressive thresholds are configurable after the scoring inputs are validated.
- Rejected launches are logged with reason, including missing-input reasons.
- Feature can be disabled independently from allocation.

## Recommended next work

1. Verify selected-player command scope before any command application.
2. Locate target velocity and point-defense weapon data sources.
3. Design Issue #6 around the vanilla selected ship/weapon command path and explicit `ammoGateBudgetShots` diagnostics.
4. Only then revisit controlled allocation and launch discipline behavior.
