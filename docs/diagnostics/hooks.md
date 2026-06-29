# Combat diagnostics hooks

This note records Terra Invicta runtime hooks used by the MissileWarfare
diagnostics build. Launch hooks below are confirmed from local deployed runs and
`Player.log` parser output. Issue #47 outcome hooks are source-reviewed,
implemented diagnostics-only, and runtime-confirmed in a fresh deployed combat
log.

## Launch hook confirmation snapshot

- Mod version: `0.1.0`.
- Validation command: `python tools\parse_player_log.py --require-launchlogs`.
- Parser verdict: `OK`.
- Diagnostics bootstrap for the deployed log: `patched=3`, `skipped=0`.
- LaunchLog entries: `4393`.
- Sequence range: `1-4393`.
- Sequence gaps: none.
- Duplicate sequences: none.
- MissileWarfare issues in the current log: none.

## Confirmed launch hook table

| Role | Target method | Parameter signature used by bootstrap | Patch method(s) | LaunchLog hook label | Confirmed count |
| --- | --- | --- | --- | --- | --- |
| Primary ship fire hook | `PavonisInteractive.TerraInvicta.TISpaceShipState.FireWeapon` | `ModuleDataEntry`, `PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState` | `CombatLaunchDiagnostics.OnShipFireWeaponPostfix` | `TISpaceShipState.FireWeapon` | `4273` |
| Secondary missile try-fire hook | `PavonisInteractive.TerraInvicta.Ship.MissileWeapon.TryFire` | `System.DateTime` | `CombatLaunchDiagnostics.OnMissileTryFirePrefix` + `CombatLaunchDiagnostics.OnMissileTryFirePostfix` | `MissileWeapon.TryFire` | `60` |
| Secondary missile projectile fire hook | `PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState.Fire` | `PavonisInteractive.TerraInvicta.CombatWeaponCarrierState`, `TIMissileTemplate`, `TIDateTime`, `UnityEngine.Vector3`, `UnityEngine.Vector3`, `UnityEngine.Vector3` | `CombatLaunchDiagnostics.OnProjectileMissileFirePostfix` | `TISpaceCombatProjectileState.Fire(missile)` | `60` |

## Evidence markers

The parser considers the launch hook set healthy when it finds:

- the MissileWarfare load, enable, and UMM active markers;
- all three required launch `Patched ... hook` lines;
- the bootstrap completion line with at least those three hooks patched and
  `skipped=0`;
- at least one `[LaunchLog]` entry when `--require-launchlogs` is used;
- contiguous `seq` values with no duplicates.

Additional diagnostics hooks, such as Issue #47 outcome hooks, are additive and
should not make older launch-hook health checks fail when they patch cleanly.

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

## Issue #47 outcome hooks

Outcome diagnostics are gated by `EnableDiagnostics` plus the default-off
`EnableOutcomeDiagnostics` setting. They emit `[OutcomeLog]` rows, not
`[LaunchLog]`, `[SnapshotLog]`, or `[AllocationLog]` rows. Parser output keeps
them in a separate summary by record type, event level, attribution level,
identity bridge, and source hook.

These hooks are source-reviewed against the local decompiled Terra Invicta
workspace, build cleanly, and were runtime-confirmed on the active
`Player.log` written on 2026-06-29. The parser reported `patched=7`,
`skipped=0`, `OutcomeLog entries: 221`, contiguous outcome `seq` values, and
all four source hooks below.

| Role | Target method | Parameter signature used by bootstrap | Patch method(s) | OutcomeLog record type | Evidence level |
| --- | --- | --- | --- | --- | --- |
| Missile damage / PD interaction | `PavonisInteractive.TerraInvicta.SpaceCombat.MissileController.ApplyDamage` | `PavonisInteractive.TerraInvicta.Ship.DamageSource` | `OutcomeDiagnostics.OnMissileApplyDamagePostfix` | `missileDamage` | projectile damage / point-defense interaction evidence |
| Missile lifecycle end | `PavonisInteractive.TerraInvicta.SpaceCombat.MissileController.Destruct` | `System.Boolean` | `OutcomeDiagnostics.OnMissileDestructPostfix` | `missileLifecycle` | projectile lifecycle state only |
| Ship damage application | `PavonisInteractive.TerraInvicta.SpaceCombat.CombatShipController.ApplyDamage` | `PavonisInteractive.TerraInvicta.Ship.DamageSource` | `OutcomeDiagnostics.OnShipApplyDamagePostfix` | `shipDamage` | concrete damage application evidence |
| Ship destruction state | `PavonisInteractive.TerraInvicta.SpaceCombat.CombatShipController.TriggerShipDestruction` | `TIGameState`, `TIShipWeaponTemplate` | `OutcomeDiagnostics.OnShipDestructionPostfix` | `shipDestroyed` | destroyed state with killer/weapon fields |

Outcome rows include fields such as `eventLevel`, `attributionLevel`,
`identityBridge`, target identity/team, attacker identity/team, damage source
type, weapon identity/class, damage amount/type, hit position, and battle
context where visible. `shipDamage` rows also include the
`shipDamageTargetDestructionTriggered` field from the concrete
`CombatShipController` instance; the generic target snapshot keeps its own
`targetDestroyed` field.

Important attribution limits:

- `missileDamage` can show a missile was damaged or destroyed by a damage
  source. It is the best current point-defense / projectile-destruction surface,
  but it is not target kill evidence.
- `missileLifecycle` can show a missile lifecycle ended with state such as
  `hasHit` or `beenDestroyed`, but `projectileStateOnly` rows do not identify
  the unique cause of target damage.
- `shipDamage` is stronger than a later vanilla destruction text hint when the
  damage source is a missile or burst damage source. The source exposes attacker
  and weapon fields, but not a unique projectile id.
- `shipDestroyed` records final destruction plus killer combatant and weapon
  fields. It remains `destroyedStateWithKillerWeapon`, not proof that a specific
  controlled projectile caused the kill.

Battle snapshot launcher-selected target identity is not a direct argument of
the projectile-state fire hook. The current candidate source is the visible
launcher/carrier target state, especially `TISpaceShipState.combatPrimaryTarget`
reached from the hook's `CombatWeaponCarrierState` argument or
`ref_shipCarrier()` method. `targetIdentitySource=launcher` should be read as
launcher/carrier primary-target or focus-fire identity, not as proof of the
actual in-flight missile guidance target. The live `MissileWeapon.target` /
`MissileController.target` chain remains the stronger runtime source for
projectile/controller target identity.

Issue #43.4 final measurement-boundary review found that
`SpaceCombatManager.liveMissiles` is a faction-count dictionary, not a missile
object list. Target-level in-flight pressure should therefore prefer active
`MissileController` objects reachable through `SpaceCombatManager._projectiles`
or `_reverseProjectiles`, then read `MissileController.target`. If those
controller objects are not available at the current hook point, the diagnostics
fall back to count-only lower-bound pressure.

Ammo/gate budget source discovery found that reliable ship ammo state is keyed as
`TISpaceShipState.ammo[ModuleDataEntry]`. The projectile-state fire hook does
not receive the firing `ModuleDataEntry`, so it cannot safely resolve per-weapon
ammo by itself. `MissileWeapon.TryFire` owns the live weapon and `weaponData`;
`TISpaceShipState.FireWeapon(module, targetedProjectile)` owns the module key and
decrements ammo before triggering `ShipWeaponFired`.

Issue #11 Phase 02 records that live weapon evidence on successful
`MissileWeapon.TryFire` postfix rows with optional fields including
`ammoEvidenceSource`, `postFireRemaining`, `postFireWeaponHasAmmo`,
`postFireWeaponCanFire`, `postFireOnCooldown`, cooldown/salvo fields, and
magazine capacity fields. `ammoEvidenceSource=shipAmmoByWeaponData` means the
diagnostic indexed `TISpaceShipState.ammo` by the live weapon's `weaponData`.
Because this is postfix evidence after `FireWeapon`, it is not the source for
the pre-fire `ammoGateBudgetShots` value.

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
decrements magazine ammo through `ChangeAmmoValue(module, -1)`. Issue #17
therefore validates `ammo[weaponData]` plus those gates as the per-weapon
game-equivalent fire budget. The diagnostics schema names this value
`ammoGateBudgetShots`; the source path does not expose a separate loaded or
chambered count.

Fresh Phase 04 runtime validation on the active `Player.log` found 670
successful `MissileWeapon.TryFire` rows. Every row had all seven `preFire*`
fields, `preFireAmmoEvidenceSource=shipAmmoByWeaponData`, numeric
`preFireRemaining`, and numeric `postFireRemaining`. Every numeric pair had
`preFireRemaining - postFireRemaining = 1`, consistent with pre/post observation
of the `FireWeapon` ammo decrement. The same log had 670 `SnapshotLog` rows, and
all 670 used the older unresolved-budget schema. Issue #17 later resolved the
source semantics from decompiled evidence rather than this deployed log.

Issue #15 reuses that same-thread prefix evidence for the projectile-fire
snapshot and shadow allocation diagnostics. When a `TISpaceCombatProjectileState`
missile fire hook runs inside a successful `MissileWeapon.TryFire`, the snapshot
path can now log:

- `ammoGateBudgetShots`;
- `ammoGateBudgetEvidenceSource`;
- `ammoGateBudgetMissingReason`;
- `ammoEvidenceSource`;
- `liveWeaponState`;
- `ammoGateWeaponCount`;
- `unknownAmmoGateWeaponCount`.

After Issue #17, the current source can populate
`ammoGateBudgetEvidenceSource=shipAmmoByWeaponData+TryFireCommonGates` when the
same-thread prefix has module-keyed pre-fire ammo and valid live gates.
`preFireRemaining` continues to mean pre-decrement ammo dictionary state; it is
only promoted to `ammoGateBudgetShots` when paired with those gates.

## Caveats

- The hooks are diagnostics only. The missile try-fire hook now has an
  observation-only prefix paired with the existing successful postfix; these
  patches should not alter launch, targeting, projectile, or AI behavior.
- Issue #47 outcome hooks are diagnostics-only postfixes and should not alter
  damage, destruction, targeting, projectile physics, command behavior, or
  allocator behavior.
- `AllocationLog` rows may report
  `attributionConfidence="outcomeCorrelationPending"` because #47 only
  establishes the separate `[OutcomeLog]` evidence stream. Allocation-to-outcome
  joining remains a separate follow-up.
- `TISpaceShipState.FireWeapon` also observes non-missile weapon fire. Missile
  analysis should filter by hook label and missile/template fields rather than
  treating every `FireWeapon` row as a missile launch.
- `[OutcomeLog]` rows are a separate evidence class. Do not collapse them with
  controlled command-spend rows, vanilla/none-correlated spillover, conservative
  post-command `DestroyShip` hints, or bounded-live pressure diagnostics.
- `battle` context can still report `unavailable`; future snapshot work should
  identify a stable combat manager/state access path.
- The current runtime build resolved short parameter type names such as
  `ModuleDataEntry`, `TIMissileTemplate`, and `TIDateTime`. If a future Terra
  Invicta update causes skipped hooks, replace those with fully qualified type
  names confirmed from the current game assembly.
- The confirmed counts are from one local smoke run. They prove the hooks fire,
  but they are not expected to be stable across battles.
