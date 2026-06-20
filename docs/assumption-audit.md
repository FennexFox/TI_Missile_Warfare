# Assumption Audit

This note records documentation assumptions that should remain provisional until runtime diagnostics confirm them.

## Fixed in this pass

### 1. Shot-budget semantics

Previous wording could imply that a distinct budget source must exist beyond `TISpaceShipState.ammo[weaponData]`. That is premature.

Current wording should preserve three possibilities:

- `ammo[weaponData]` plus known gates is the game-equivalent budget.
- A distinct runtime source exists.
- The design avoids a numeric fleet-level budget.

Updated local files:

- `docs/readiness-semantics.md`
- `docs/battle-snapshot-extractor.md`
- `docs/reverse-engineering-plan.md`
- `docs/mvp-issue-list.md`

### 2. Selection and command scope

Previous Issue #6 wording could imply that selected-ship command scope was already verified. It is now conditional on a verified player-selection or command path.

### 3. Scoring inputs

Previous Issue #7 wording could imply that range and relative-velocity evidence were already validated. It is now conditional on validated runtime inputs, with missing-input reasons required.

### 4. Example numeric rows

Shadow allocation example numbers are now labeled as schema examples, not validated recommendations.

## Already sufficiently qualified

- Launcher-selected identity is documented as not being proof of the final in-flight guidance identity.
- Defaulted scoring weights are documented as a missing-input condition.

## Remaining follow-up

`docs/confirmed-hooks.md` still has wording that may sound too dismissive of paired ammo/gate evidence. It should be aligned later with `docs/readiness-semantics.md`: do not call the evidence `readyShots` yet, but do not assume a distinct source is required either.
