# MVP roadmap

This roadmap records durable issue-sized work. Temporary per-PR plans belong under `dev-docs/plan/**` and may be deleted after the PR is merged, closed, or abandoned.

## Current milestone state

The project has enough diagnostics to observe missile launches and shadow
allocation inputs, and Issues #34-#36 validate the controlled experiment
envelope through a default-off apply gate. Issue #37 now has post-fix runtime
smoke evidence for the first behavior-changing selected single-ship apply path:
enemy allocator / friendly-target candidates wait, and the first selected-team
hostile candidate can apply exactly one vanilla salvo-target command. The path
remains default-off and selected-single-ship only.

Current blocker:

- Issue #17 resolved the shot-budget design gate to Path A:
  `TISpaceShipState.ammo[weaponData]` plus vanilla fire gates is the
  game-equivalent per-weapon fire budget. The mod names this explicit value
  `ammoGateBudgetShots`; no distinct loaded/chambered source was found. See
  [`readiness-semantics.md`](../research/readiness-semantics.md).
- Issue #21 resolved one safe selected-player scope source for command design:
  the tactical command panel's single selected ship or group-selected ship list.
  It is not the broader left-hand player-side combatant list. See
  [`selected-command-scope.md`](../research/selected-command-scope.md).
- Issue #34 runtime smoke validated the dry-run envelope but did not resolve
  selected command-panel scope in that runtime context. The probe failed closed
  with explicit `selectedScopeUnavailable` evidence and zero applied commands.
- Issue #35 runtime smoke validates command-candidate reporting, selected-scope
  visibility through the combat HUD path, non-player skip-closed behavior,
  outside-selected-scope skip-closed behavior, zero scope violations, and zero
  applied commands.

Current missing or provisional inputs:

- Issue #37 adds and runtime-smoke-validates a first live command path only for
  one explicitly selected player missile ship and one resolved hostile target
  from a selected-team allocator cycle; additional runtime evidence is still
  needed before selected-group or fleet-wide expansion;
- the current selected four-log fitting snapshot is baseline-ready with named
  limitations, not controlled-command ready;
- Issue #29 upgrades observed target point-defense evidence from
  defense-mode presence to provisional static template capability when range,
  cooldown, ammo-capacity-like, or similar template fields are visible;
  `pdCapabilityObservedFields` names the observed categories, and live
  readiness, live ammo, geometry, and arc coverage remain unproven;
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

Status: tooling available; the 2026-06-22 selected four-log fitting run is
baseline-ready with named limitations.

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
- The 2026-06-22 selected four-log fitting run found 541 plausible, 114 partial
  saturation, 58 ambiguous, 204 command-safety no-op, 0
  missing-evidence-limited, and zero severe classifications across four
  parser-OK real logs.
- `command-safety no-op` classifies missing launcher-selected `targetIdentity`
  no-op evidence as a safe skip when no concrete launcher-selected priority
  target is visible. It is not allocation-quality evidence and not proof that
  vanilla had no missile target.
- Issue #28/#29 sufficiency reporting keeps the fitting baseline distinct from
  controlled command readiness while naming limitations: target PD evidence is
  `presenceOnly` for legacy template-presence logs and `provisional` only when
  static capability fields are present; target-identity no-op evidence is
  `provisional`, observed launch/ammo deltas are `provisional`, future
  geometry-aware PD evidence is also `provisional` until separately validated,
  and controlled live command readiness is `Not ready`.
- #6 readiness now separates three remaining concerns: evidence quality
  (#29 after #28's gate), command safety (#22/#23), and allocator design choices
  (#6).

## Blocked controlled features

### Issue 6: Controlled auto-allocation command

Goal: apply target assignments for selected friendly missile ships.

Status: blocked pending later selected-group / fleet-wide scope expansion. #37
now supplies selected-single-ship live smoke evidence only.

Do not implement Issue 6 around a fictitious `readyShots` source. Issue #17
validated the per-weapon `ammoGateBudgetShots` semantics. Issue #21 validates
the selected-player command path for later dry-run logging, but controlled
command application still must let vanilla combat enforce the final legal launch
result.

Future #6 design should continue from the Issue #34 dry-run envelope, the #35
command-resolvability report, the #36 hard-stop proof, and the #37 single-ship
apply boundary: preserve the audited player-controlled command scope, selected
or otherwise verified player missile ship identity, visible weapon/module
identity, `ammoGateBudgetShots` and its evidence source, the allocator
recommendation that motivated the command, command intent and target,
skipped/failure reason, and observed ammo delta or launch evidence when
available.

Additional gate: vanilla salvo target command granularity is ship-level and all
salvo-capable weapons on that ship, not one visible missile module. The Issue
#34 dry-run logs make that broader granularity explicit, but later command
resolvability and safety reports must still prove whether a concrete player
controlled scope and command can be safely attempted.

Acceptance criteria once unblocked:

- Command scope is an explicit, auditable player-controlled scope. The
  command-panel selected ship/group path is one valid source when visible;
  current-combat active-player missile combatants may be another only after
  #35 verifies them. Enemy, AI-controlled, allied non-player, and accidental
  broad-side ships must not become eligible.
- Existing manual control remains possible after the command-scope path is verified.
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

1. Use the post-fix #37 selected-single-ship smoke as the current live-apply
   baseline, and expand only through the planned #38 selected-subgroup and #43
   fleet-wide rungs. Any further #37 retest should preserve the same checks:
   `launcherId` names the selected ship, `allocatorLauncherId` names a same-team
   cycle producer, `targetTeam` differs from `launcherTeam`, with at most one
   applied/failed command per trigger and no scope violations, same-team missile
   target snapshots, or MissileWarfare warnings/errors.
2. Re-run selected-log fitting after the Issue #29 PD capability schema is
   present in fresh real combat logs and
   record whether multiple real logs remain free of defaulted or evidence-limited
   classifications.
3. Design Issue #6 around explicit `ammoGateBudgetShots` diagnostics and the
   documented vanilla salvo command granularity.
4. Expand controlled apply only through the planned #38 selected subgroup and
   #43 fleet-wide rungs after #37 evidence is understood.
