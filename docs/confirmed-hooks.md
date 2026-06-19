# Confirmed combat launch hooks

This note records the Terra Invicta runtime hooks confirmed by the
MissileWarfare diagnostics build. These are confirmed from a local deployed run
and `Player.log` parser output, not from committed decompiled source.

## Confirmation snapshot

- Mod version: `0.1.0`.
- Validation command: `python tools\parse_player_log.py --require-launchlogs`.
- Parser verdict: `OK`.
- Diagnostics bootstrap: `patched=3`, `skipped=0`.
- LaunchLog entries: `4393`.
- Sequence range: `1-4393`.
- Sequence gaps: none.
- Duplicate sequences: none.
- MissileWarfare issues in the current log: none.

## Hook table

| Role | Target method | Parameter signature used by bootstrap | Postfix | LaunchLog hook label | Confirmed count |
| --- | --- | --- | --- | --- | --- |
| Primary ship fire hook | `PavonisInteractive.TerraInvicta.TISpaceShipState.FireWeapon` | `ModuleDataEntry`, `PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState` | `CombatLaunchDiagnostics.OnShipFireWeaponPostfix` | `TISpaceShipState.FireWeapon` | `4273` |
| Secondary missile try-fire hook | `PavonisInteractive.TerraInvicta.Ship.MissileWeapon.TryFire` | `System.DateTime` | `CombatLaunchDiagnostics.OnMissileTryFirePostfix` | `MissileWeapon.TryFire` | `60` |
| Secondary missile projectile fire hook | `PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState.Fire` | `PavonisInteractive.TerraInvicta.CombatWeaponCarrierState`, `TIMissileTemplate`, `TIDateTime`, `UnityEngine.Vector3`, `UnityEngine.Vector3`, `UnityEngine.Vector3` | `CombatLaunchDiagnostics.OnProjectileMissileFirePostfix` | `TISpaceCombatProjectileState.Fire(missile)` | `60` |

## Evidence markers

The parser considers the hook set healthy when it finds:

- the MissileWarfare load, enable, and UMM active markers;
- three `Patched ... hook` lines;
- the bootstrap completion line with `patched=3`, `skipped=0`;
- at least one `[LaunchLog]` entry when `--require-launchlogs` is used;
- contiguous `seq` values with no duplicates.

The latest confirmed run found all three patch lines:

```text
primary ship fire hook -> PavonisInteractive.TerraInvicta.TISpaceShipState.FireWeapon
secondary missile try-fire hook -> PavonisInteractive.TerraInvicta.Ship.MissileWeapon.TryFire
secondary missile projectile fire hook -> PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState.Fire
```

## Logged fields

`TISpaceShipState.FireWeapon` currently logs launcher, weapon/module/template,
primary target where visible, targeted projectile, default fire mode, and battle
context.

`MissileWeapon.TryFire` currently logs weapon/module/template, launcher, target,
targeted position, fire mode, current time, and battle context.

`TISpaceCombatProjectileState.Fire(missile)` currently logs projectile,
launcher, missile template, launch time, origin position, expected target
position, origin velocity, and battle context.

Battle snapshot target identity is not a direct argument of the projectile-state
fire hook. The current candidate source is the visible launcher/carrier target
state, especially `TISpaceShipState.combatPrimaryTarget` reached from the hook's
`CombatWeaponCarrierState` argument or `ref_shipCarrier()` method. The live
`MissileWeapon.target` / `MissileController.target` chain remains the stronger
runtime source if primary-target probing does not recover identity in a smoke
test, but using it would require a separate observation point.

## Caveats

- The hooks are postfix diagnostics only. They are intended to observe combat
  launch flow and should not alter launch, targeting, projectile, or AI behavior.
- `TISpaceShipState.FireWeapon` also observes non-missile weapon fire. Missile
  analysis should filter by hook label and missile/template fields rather than
  treating every `FireWeapon` row as a missile launch.
- `battle` context can still report `unavailable`; future snapshot work should
  identify a stable combat manager/state access path.
- The current runtime build resolved short parameter type names such as
  `ModuleDataEntry`, `TIMissileTemplate`, and `TIDateTime`. If a future Terra
  Invicta update causes skipped hooks, replace those with fully qualified type
  names confirmed from the current game assembly.
- The confirmed counts are from one local smoke run. They prove the hooks fire,
  but they are not expected to be stable across battles.
