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

| Role | Target method | Parameter signature used by bootstrap | Patch method(s) | LaunchLog hook label | Confirmed count |
| --- | --- | --- | --- | --- | --- |
| Primary ship fire hook | `PavonisInteractive.TerraInvicta.TISpaceShipState.FireWeapon` | `ModuleDataEntry`, `PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState` | `CombatLaunchDiagnostics.OnShipFireWeaponPostfix` | `TISpaceShipState.FireWeapon` | `4273` |
| Secondary missile try-fire hook | `PavonisInteractive.TerraInvicta.Ship.MissileWeapon.TryFire` | `System.DateTime` | `CombatLaunchDiagnostics.OnMissileTryFirePrefix` + `CombatLaunchDiagnostics.OnMissileTryFirePostfix` | `MissileWeapon.TryFire` | `60` |
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
targeted position, fire mode, current time, live weapon ammo evidence, cooldown
and salvo evidence, capacity evidence, and battle context.

`TISpaceCombatProjectileState.Fire(missile)` currently logs projectile,
launcher, missile template, launch time, origin position, expected target
position, origin velocity, and battle context.

Battle snapshot launcher-selected target identity is not a direct argument of
the projectile-state fire hook. The current candidate source is the visible
launcher/carrier target state, especially `TISpaceShipState.combatPrimaryTarget`
reached from the hook's `CombatWeaponCarrierState` argument or
`ref_shipCarrier()` method. `targetIdentitySource=launcher` should be read as
launcher/carrier primary-target or focus-fire identity, not as proof of the
actual in-flight missile guidance target. The live `MissileWeapon.target` /
`MissileController.target` chain remains the stronger runtime source for
projectile/controller target identity, but using it would require a separate
observation point.

Ready-shot source discovery found that reliable ship ammo state is keyed as
`TISpaceShipState.ammo[ModuleDataEntry]`. The projectile-state fire hook does
not receive the firing `ModuleDataEntry`, so it cannot safely resolve per-weapon
ammo by itself. `MissileWeapon.TryFire` owns the live weapon and `weaponData`;
`TISpaceShipState.FireWeapon(module, targetedProjectile)` owns the module key and
decrements ammo before triggering `ShipWeaponFired`. Existing postfix
observations around those methods should be treated as post-fire remaining ammo,
not allocator-safe `readyShots`.

Issue #11 Phase 02 records that live weapon evidence on successful
`MissileWeapon.TryFire` postfix rows with optional fields including
`ammoEvidenceSource`, `postFireRemaining`, `postFireWeaponHasAmmo`,
`postFireWeaponCanFire`, `postFireOnCooldown`, cooldown/salvo fields, and
magazine capacity fields. `ammoEvidenceSource=shipAmmoByWeaponData` means the
diagnostic indexed `TISpaceShipState.ammo` by the live weapon's `weaponData`.
Because this is postfix evidence after `FireWeapon`, it is not a source for
`SnapshotLog readyShots`.

Fresh Phase 02 runtime validation found 649 successful `MissileWeapon.TryFire`
rows with `ammoEvidenceSource=shipAmmoByWeaponData` and populated
`postFireRemaining` on every row. `postFireRemaining=0` appeared 42 times and
matched the 42 rows where both `postFireWeaponHasAmmo` and
`postFireWeaponCanFire` were `False`; all nonzero rows reported both fields as
`True`. The same run had parser verdict `OK`, 13,644 `LaunchLog` rows, 649
`SnapshotLog` rows, no sequence gaps, no duplicate sequences, and no
MissileWarfare issues.

That run still logged `cooldownDuration=null`. Phase 03 traced the cause to
`currentCooldownDuration_s` being a private field declared on the base `Weapon`
class while the hook observes a `MissileWeapon` runtime object. The diagnostics
now use a narrow inherited-member read for that exact field. Fresh runtime
validation confirmed `cooldownDuration=00:00:07` on all 675 successful
`MissileWeapon.TryFire` rows in the follow-up smoke log. This remains
observation-only.

Issue #11 Phase 04 changes the missile try-fire hook to a paired prefix/postfix
on the same `MissileWeapon.TryFire(System.DateTime)` target. The prefix captures
optional pre-fire values (`preFireAmmoEvidenceSource`, `preFireRemaining`,
`preFireWeaponHasAmmo`, `preFireWeaponCanFire`, `preFireOnCooldown`,
`preFireSalvoShotsFired`, and `preFireSalvoShots`) into Harmony `__state`; the
existing successful postfix writes them on the same `MissileWeapon.TryFire`
`LaunchLog` row before the post-fire fields. The bootstrap still counts this as
one patched target method, so the healthy patch summary remains `patched=3`,
`skipped=0`. The prefix is observation-only and returns normally; it does not
skip, suppress, or alter the original `TryFire` method.

Static review of the confirmed decompiled path found that `TryFireCommon`
checks cooldown, target presence, `WeaponCanFire(weaponData)`, salvo reset, and
`OnTarget`, while `TISpaceShipState.FireWeapon(module, targetedProjectile)`
decrements magazine ammo through `ChangeAmmoValue(module, -1)`. That source path
does not expose a separate allocator-safe fireable-shot count, so `SnapshotLog
readyShots` remains unknown unless runtime evidence proves another source.

Fresh Phase 04 runtime validation on the active `Player.log` found 670
successful `MissileWeapon.TryFire` rows. Every row had all seven `preFire*`
fields, `preFireAmmoEvidenceSource=shipAmmoByWeaponData`, numeric
`preFireRemaining`, and numeric `postFireRemaining`. Every numeric pair had
`preFireRemaining - postFireRemaining = 1`, consistent with pre/post observation
of the `FireWeapon` ammo decrement. The same log had 670 `SnapshotLog` rows, and
all 670 still reported `readyShots=unknown`; no allocator-safe fireable-shot
source beyond ammo/gate evidence was recovered.

Issue #15 reuses that same-thread prefix evidence for the projectile-fire
snapshot and shadow allocation diagnostics. When a `TISpaceCombatProjectileState`
missile fire hook runs inside a successful `MissileWeapon.TryFire`, the snapshot
path can now log:

- `readyShotEvidenceSource`;
- `readinessMissingReason`;
- `ammoEvidenceSource`;
- `liveWeaponState`;
- `readyWeaponCount`;
- `unknownReadinessWeaponCount`.

The current source remains `readyShotEvidenceSource=unknown` because the
correlated live evidence is ammo and gate/cooldown state, not a proven
allocator-safe fireable-shot count. `preFireRemaining` continues to mean
pre-decrement ammo dictionary state. It must not be used as controlled
allocation-ready `readyShots` without a separately documented source.

## Caveats

- The hooks are diagnostics only. The missile try-fire hook now has an
  observation-only prefix paired with the existing successful postfix; these
  patches should not alter launch, targeting, projectile, or AI behavior.
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
