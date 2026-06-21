# MVP roadmap

This roadmap records durable issue-sized work. Temporary per-PR plans belong under `dev-docs/plan/**` and may be deleted after the PR is merged, closed, or abandoned.

## Current milestone state

The project has enough diagnostics to observe missile launches and shadow allocation inputs, and Issue #21 verifies the selected-player command scope for later dry-run command-intent logging. It is still not ready for live controlled command application.

Current blocker:

- Issue #17 resolved the shot-budget design gate to Path A:
  `TISpaceShipState.ammo[weaponData]` plus vanilla fire gates is the
  game-equivalent per-weapon fire budget. The mod names this explicit value
  `ammoGateBudgetShots`; no distinct loaded/chambered source was found. See
  [`readiness-semantics.md`](../research/readiness-semantics.md).
- Issue #21 resolved selected-player command scope for the next dry-run phase:
  the safe scope is the tactical command panel's single selected ship or
  group-selected ship list. It is not the broader left-hand player-side
  combatant list. See
  [`selected-command-scope.md`](../research/selected-command-scope.md).

Current missing or provisional inputs:

- dry-run command-intent logging for the verified selected-player scope;
- evidence-sufficiency reporting now classifies the Issue #30 four-log fitting
  sweep as baseline-ready with named limitations, not controlled-command ready;
- Issue #29 upgrades observed target point-defense evidence from
  defense-mode presence to provisional static template capability when range,
  cooldown, or similar template fields are visible; live readiness, ammo,
  geometry, and arc coverage remain unproven;
- vanilla salvo target command granularity is ship-level across all
  salvo-capable weapons on the ship, so per-visible-module command assumptions
  remain unsafe;
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

### Issue 24: Shadow allocation log-only fitting pass

Goal: replay selected local combat logs through parser/fitting tooling before
using the allocator as a #6 baseline.

Status: tooling available; Issue #30 completed a four-real-log pre-#6 sweep
with local ignored artifacts and a durable summary in
`docs/diagnostics/runtime-validation-history.md`.

Implementation notes:

- Default selected logs: `artifacts/combat-logs/selected/`.
- Default generated fitting report: `artifacts/shadow-fitting/latest/`.
- Wrapper command:
  `python tools\fit_shadow_allocation.py --input artifacts\combat-logs\selected --output artifacts\shadow-fitting\latest`.
- One real selected combat log can support a `Conditionally ready` #6 baseline
  when required evidence is present and no impossible or obviously unsafe
  allocation behavior is classified, provided the report also includes at
  least one plausible allocation or no-op decision.
- Any PD-defaulted evidence blocks full readiness but does not block a
  conditional baseline.
- Issue #30's four-log sweep, after Issue #32 classification, found 993
  plausible, 349 partial saturation, 585 ambiguous, 54 command-safety no-op, 0
  missing-evidence-limited, and zero severe classifications across four
  parser-OK real logs.
- Issue #32 classifies intermittent missing `targetIdentity` no-op evidence as
  safe skip evidence when no launcher-selected priority target is visible. It is
  not allocation-quality evidence and not proof that vanilla had no missile
  target.
- Issue #28/#29 sufficiency reporting keeps the fitting baseline distinct from
  controlled command readiness while naming limitations: target PD evidence is
  `presenceOnly` for legacy template-presence logs and `provisional` only when
  Issue #29 static capability fields are present; target-identity no-op
  evidence is `provisional`, observed launch/ammo deltas are `provisional`,
  and controlled live command readiness is `Not ready`.
- #6 readiness now separates three remaining concerns: evidence quality
  (#29 after #28's gate), command safety (#22/#23), and allocator design choices
  (#6).

## Blocked controlled features

### Issue 6: Controlled auto-allocation command

Goal: apply target assignments for selected friendly missile ships.

Status: blocked pending dry-run command-intent logging and live
command-application safety work.

Do not implement Issue 6 around a fictitious `readyShots` source. Issue #17
validated the per-weapon `ammoGateBudgetShots` semantics. Issue #21 validates
the selected-player command path for later dry-run logging, but controlled
command application still must let vanilla combat enforce the final legal launch
result.

Future #6 design should log selected player ship identity, visible weapon/module
identity, `ammoGateBudgetShots` and its evidence source, the allocator
recommendation that motivated the command, command intent and target,
skipped/failure reason, and observed ammo delta or launch evidence when
available.

Additional gate: vanilla salvo target command granularity is ship-level and all
salvo-capable weapons on that ship, not one visible missile module. Later #22
dry-run logs must make that broader granularity explicit before #23 considers a
minimal live smoke.

Acceptance criteria once unblocked:

- Selection scope is based on the verified single selected ship or
  group-selected ship command-panel path.
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

1. Implement #22 dry-run command-intent logging from the verified selected ship
   and group-selected ship scopes.
2. Re-run selected-log fitting after the Issue #29 PD capability schema is
   present in fresh real combat logs and
   record whether multiple real logs remain free of defaulted or evidence-limited
   classifications.
3. Design Issue #6 around explicit `ammoGateBudgetShots` diagnostics and the
   documented vanilla salvo command granularity.
4. Only then revisit #23 live command safety, controlled allocation, and launch
   discipline behavior.
