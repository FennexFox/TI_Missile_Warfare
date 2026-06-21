# Readiness Semantics

This document records the shot-budget semantics used by Terra Invicta tactical-combat projectile allocation diagnostics.

## Current conclusion

Issue #17 chooses Path A with explicit scope: `TISpaceShipState.ammo[weaponData]`
plus the vanilla fire gates is the game-equivalent budget for the observed
per-weapon missile fire decision.

That does not mean the game exposes a distinct `readyShots`, loaded, or
chambered-shot source. The reviewed source path uses module-keyed ammo plus
gates. The mod therefore names this derived value `ammoGateBudgetShots`, and it
must stay tied to the gates and timing that make it valid.

## Evidence

Reviewed decompiled source is under `../TI_RE_Workspace/decompiled_source`.

- `PavonisInteractive.TerraInvicta.Ship/MissileWeapon.cs:38-50` calls
  `TryFireCommon(currentTime)`, fires the projectile, enters cooldown, and then
  calls `WeaponCarrierState.FireWeapon(base.weaponData, ref_projectile)`.
- `PavonisInteractive.TerraInvicta.Ship/Weapon.cs:475-489` rejects fire when the
  weapon is on cooldown, has no target, fails
  `combatant.WeaponCarrierState.WeaponCanFire(weaponData)`, or is not on target.
- `PavonisInteractive.TerraInvicta/TISpaceShipState.cs:741` stores ammo as
  `Dictionary<ModuleDataEntry, int> ammo`.
- `TISpaceShipState.cs:3052-3075` loads and reads magazine ammo by module key;
  `WeaponHasAmmo(module)` returns `ammo[module] > 0` for magazine weapons.
- `TISpaceShipState.cs:3130-3158` decrements the same keyed ammo in
  `FireWeapon(module, targetedProjectile)` through `ChangeAmmoValue(module, -1)`
  and then triggers `ShipWeaponFired`.
- `TISpaceShipState.cs:3581-3597` makes `WeaponCanFire(moduleData)` depend on
  `WeaponIsOperable`, ammo, power, heat, and active fire control.
- `SpaceCombat.UI/ShipWeaponUIController.cs:109-113` displays
  `ship.ammo[weapon.weaponData]` as the weapon ammo count.
- `PavonisInteractive.TerraInvicta.Ship/SalvoFireMode.cs:22-49` counts fired
  `ShipWeaponFired` events and resets mode after a salvo quota. This is
  fire-mode accounting, not a separate shot-budget source.
- `SelectSalvoTargetCommand.cs:15-20` gates the command on
  `AnyOffensiveMissileWeaponCanFire`, and `SelectSalvoTargetCommand.cs:39-51`
  applies primary target plus `FireMode.Salvo` through vanilla player actions.

The source review did not find a separate allocator-safe loaded/chambered shot
count.

## Validity window

`ammoGateBudgetShots` is valid only when all of these are true for the same
weapon/module and timing window:

- ammo comes from `TISpaceShipState.ammo[weaponData]`;
- the weapon is observed before the relevant `TryFire` attempt spends ammo;
- `WeaponCanFire(weaponData)` is true;
- `OnCooldown(currentTime)` is false;
- the fire path has a target and passes vanilla on-target checks;
- salvo state is treated as mode/cooldown behavior, not as a separate budget.

If any of those inputs are missing, the budget remains unknown and diagnostics
must emit an `ammoGateBudgetMissingReason`.

## Aggregation rule

Fleet-level allocation may sum only explicitly sourced per-weapon
`ammoGateBudgetShots` values. It must not derive a budget from projectile
remaining counts, post-fire ammo, stale UI values, ship-level magazine capacity,
or a count without the paired gate evidence.

The current shadow allocation remains diagnostics-first. It can run the Core
allocator when it has an `ammoGateBudgetShots` value, but future controlled
commands still need a verified selected-player command scope before any command
application.

## Command consequence

Issue #6 is no longer blocked on finding a distinct shot-budget source. It
remains blocked on selected-player command scope and command-application safety.
The likely safe command basis is the vanilla command path: set a selected
player ship's primary target and missile weapon mode through the same player
action family used by `SelectSalvoTargetCommand`, while logging intent,
`ammoGateBudgetShots`, skipped reasons, and observed launch/ammo deltas.

## Documentation rule

Use these terms carefully:

- Prefer: `ammoGateBudgetShots`, `ammo/gate budget`, `module-keyed ammo`,
  `vanilla fire gates`.
- Avoid: `readyShots`, `loaded count`, `chambered count`, unless a future source
  actually exposes that distinct state.

