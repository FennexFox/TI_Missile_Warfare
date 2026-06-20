# Readiness Semantics

This document records the current evidence and open questions for Terra Invicta tactical-combat projectile allocation diagnostics.

## Current conclusion

Do not assume that the game has a separate `readyShots`, loaded, or chambered state model.

The current live evidence shows that `TISpaceShipState.ammo[weaponData]` can be read around `MissileWeapon.TryFire`, and successful launches show a one-count decrease across the observed fire path. That evidence may mean one of two things:

1. `ammo[weaponData]` is the vanilla runtime source for the currently usable shot budget at that moment.
2. `ammo[weaponData]` is only a broader magazine/ammunition count, while some other gate/cooldown/salvo logic determines whether a shot can actually fire.

Both interpretations remain possible until the runtime call path and UI semantics are checked more carefully.

## Hypothesis A: ammo-as-fireable-budget

`TISpaceShipState.ammo[weaponData]` may already be the best available runtime budget for shots that the current weapon can spend. Under this interpretation, there may be no additional `readyShots` state to recover.

Evidence that would support this hypothesis:

- The UI displays a count that matches `ammo[weaponData]` at the same tactical-combat moment.
- `WeaponCanFire(weaponData)` and cooldown/salvo gates explain all cases where `ammo[weaponData] > 0` but no shot is fired.
- The count changes only when the game spends an actual shot through the observed fire path.
- Multiple launchers or modules do not require a hidden per-launcher ready queue beyond the keyed ammo value.

If this hypothesis is confirmed, the allocator should not invent a separate `readyShots` concept. It should document `ammo[weaponData]` as the observed vanilla shot budget and keep all gate/cooldown/salvo checks explicit.

## Hypothesis B: separate fireable-shot source

There may be a separate runtime source for shots currently available to fire, distinct from the keyed ammo count. This source has not been confirmed.

Evidence that would support this hypothesis:

- A field or method changes independently from `ammo[weaponData]` and corresponds to launch readiness.
- The UI or fire path displays/uses a ready count that can diverge from `ammo[weaponData]`.
- `ammo[weaponData]` remains positive while a separate state explains why no launcher can spend a shot, beyond simple cooldown/salvo/target gates.
- Multi-launcher behavior cannot be represented by the keyed ammo value plus known gates.

Until such evidence is found, do not write requirements that assume a separate ready/loaded/chambered state model exists.

## Documentation rule

Use these terms carefully:

- Prefer: `observed ammo budget`, `fireable-shot evidence`, `allocator-safe shot budget`, `ammo/gate semantics`.
- Avoid: `true readyShots`, `loaded count`, `chambered count`, unless the game actually exposes such a state.

## Implementation rule

A numeric allocator budget can be promoted only after one of these is documented:

1. `ammo[weaponData]` is validated as the game-equivalent fireable budget for the relevant timing window.
2. A distinct runtime source is found and validated.
3. The allocator design is changed so it does not require a numeric ready-shot budget.

Until then, diagnostics should record raw observed values and should label any derived shot budget as provisional.
