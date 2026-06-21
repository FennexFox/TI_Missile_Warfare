# Assumption Audit

This note records documentation assumptions that should remain provisional until runtime diagnostics confirm them.

## Fixed in this pass

### 1. Shot-budget semantics

Previous wording could imply that a distinct budget source must exist beyond `TISpaceShipState.ammo[weaponData]`. Issue #17 corrected that assumption.

Current wording records the confirmed source-level result:

- `ammo[weaponData]` plus vanilla fire gates is the game-equivalent per-weapon fire budget.
- No distinct loaded/chambered source was found.
- The mod should call the value `ammoGateBudgetShots`, not `readyShots`.

Updated durable files:

- [`research/readiness-semantics.md`](../research/readiness-semantics.md)
- [`diagnostics/snapshot-and-allocation.md`](../diagnostics/snapshot-and-allocation.md)
- [`research/reverse-engineering-plan.md`](../research/reverse-engineering-plan.md)
- [`planning/mvp-roadmap.md`](../planning/mvp-roadmap.md)
- [`research/selected-command-scope.md`](../research/selected-command-scope.md)

### 2. Selection and command scope

Previous Issue #6 wording could imply that selected-ship command scope was already verified. Issue #21 now verifies the selected-player command scope for later dry-run logging: use the tactical command panel's single selected ship or group-selected ship list, not the broader left-hand player-side combatant list.

Remaining constraint: vanilla salvo target commands operate at ship/all-salvo-capable-weapons granularity, not one visible missile module. Later dry-run and live-safety work must log and account for that.

### 3. Scoring inputs

Previous Issue #7 wording could imply that range and relative-velocity evidence were already validated. It is now conditional on validated runtime inputs, with missing-input reasons required.

### 4. Example numeric rows

Shadow allocation example numbers are now labeled as schema examples, not validated recommendations.

### 5. Paired ammo/gate evidence wording

The hook documentation now avoids the stale premature conclusion:

- do not assume a distinct source must exist beyond `ammo[weaponData]` plus known gates.

See [`diagnostics/hooks.md`](../diagnostics/hooks.md) and [`research/readiness-semantics.md`](../research/readiness-semantics.md).

## Already sufficiently qualified

- Launcher-selected identity is documented as not being proof of the final in-flight guidance identity.
- Defaulted scoring weights are documented as a missing-input condition.

## Remaining follow-up

No known long-lived documentation assumption remains from this audit. Future assumption notes should be added here only if they remain useful after the current PR; temporary per-issue investigation notes belong under `dev-docs/plan/**` and may be deleted when the PR is complete.
