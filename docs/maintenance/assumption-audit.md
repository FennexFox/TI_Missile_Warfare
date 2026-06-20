# Assumption Audit

This note records documentation assumptions that should remain provisional until runtime diagnostics confirm them.

## Fixed in this pass

### 1. Shot-budget semantics

Previous wording could imply that a distinct budget source must exist beyond `TISpaceShipState.ammo[weaponData]`. That is premature.

Current wording should preserve three possibilities:

- `ammo[weaponData]` plus known gates is the game-equivalent budget.
- A distinct runtime source exists.
- The design avoids a numeric fleet-level budget.

Updated durable files:

- [`research/readiness-semantics.md`](../research/readiness-semantics.md)
- [`diagnostics/snapshot-and-allocation.md`](../diagnostics/snapshot-and-allocation.md)
- [`research/reverse-engineering-plan.md`](../research/reverse-engineering-plan.md)
- [`planning/mvp-roadmap.md`](../planning/mvp-roadmap.md)

### 2. Selection and command scope

Previous Issue #6 wording could imply that selected-ship command scope was already verified. It is now conditional on a verified player-selection or command path.

### 3. Scoring inputs

Previous Issue #7 wording could imply that range and relative-velocity evidence were already validated. It is now conditional on validated runtime inputs, with missing-input reasons required.

### 4. Example numeric rows

Shadow allocation example numbers are now labeled as schema examples, not validated recommendations.

### 5. Paired ammo/gate evidence wording

The hook documentation now avoids both premature conclusions:

- do not call paired ammo/gate evidence `readyShots` yet;
- do not assume a distinct source must exist beyond `ammo[weaponData]` plus known gates.

See [`diagnostics/hooks.md`](../diagnostics/hooks.md) and [`research/readiness-semantics.md`](../research/readiness-semantics.md).

## Already sufficiently qualified

- Launcher-selected identity is documented as not being proof of the final in-flight guidance identity.
- Defaulted scoring weights are documented as a missing-input condition.

## Remaining follow-up

No known long-lived documentation assumption remains from this audit. Future assumption notes should be added here only if they remain useful after the current PR; temporary per-issue investigation notes belong under `dev-docs/plan/**` and may be deleted when the PR is complete.
