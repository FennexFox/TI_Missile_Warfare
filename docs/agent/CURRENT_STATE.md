# Current state

This page is a concise orientation snapshot for future agents. It should stay
short and point to durable evidence rather than becoming a chronological log.

## Posture

TI MissileWarfare is still a conservative, diagnostics-first Terra Invicta
missile fire-control mod. The safe default is to observe and log before changing
launch behavior.

The core boundary remains:

- `MissileFireControl.Core`: pure, game-independent model and allocation logic.
- `MissileFireControl.Mod`: Unity Mod Manager, Harmony, settings, diagnostics,
  and Terra Invicta-facing glue.

See [Architecture](../guide/architecture.md).

## Confirmed durable facts

- Runtime diagnostics can observe missile launch hooks, launcher identity,
  selected target identity in some contexts, and paired pre/post ammo plus
  gate/cooldown evidence from `MissileWeapon.TryFire`. See
  [Confirmed combat launch hooks](../diagnostics/hooks.md).
- The validated shot-budget term is `ammoGateBudgetShots`: module-keyed
  `TISpaceShipState.ammo[weaponData]` plus vanilla fire gates. Do not reintroduce
  `readyShots` unless future source evidence exposes a distinct loaded or
  chambered count. See [Readiness semantics](../research/readiness-semantics.md).
- Selected-player command scope is the tactical command panel's single selected
  ship or group-selected ship list, not the broader left-hand player-side
  combatant list. See [Selected command scope](../research/selected-command-scope.md).
- Vanilla salvo target commands are ship-level across all salvo-capable weapons
  on the ship. They are not commands for one visible missile module.
- Issue #39 selected-group diagnostics now have direct command-result
  launch/spend attribution for applied commands. Heuristic tuning still depends
  on outcome-quality evidence and follow-up design. See
  [Issue #39 controlled correlation investigation](../investigations/issue-39-controlled-correlation.md).
- Experiment corpus docs separate `shadow-replay`, `controlled-live`,
  `fleet-wide-controlled`, and `fixture` evidence modes. These modes must not be
  collapsed into one proof score. See
  [Experiment corpus and parameter ledger](../diagnostics/experiment-corpus.md).

## Current blockers and boundaries

- Issue #6 controlled auto-allocation remains blocked on wider scope and outcome
  evidence. Existing selected-single and selected-group live paths are narrow,
  default-off controlled experiments, not fleet-wide readiness.
- Issue #7 launch discipline remains blocked on validated runtime scoring inputs.
- Needs verification: exact missile hit, intercept, damage, and kill attribution
  still requires a stable combat outcome hook.
- Needs verification: any heuristic tuning claim must be tied to fresh
  controlled-live evidence, not only shadow replay.

See [MVP roadmap](../planning/mvp-roadmap.md) for the detailed issue sequence.

## Documentation state

Durable docs live under `docs/**`. Temporary issue and PR plans live under
`dev-docs/plan/**` and may be deleted after the related work closes. If a
temporary plan contains a conclusion that should survive, promote the conclusion
into the smallest relevant durable doc before deleting the plan.

The durable documentation structure decision is recorded in
[ADR 0001](../adr/0001-durable-documentation-structure.md).
