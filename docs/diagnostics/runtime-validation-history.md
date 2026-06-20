# Runtime validation history

This document preserves smoke-test and runtime-validation findings for the missile-warfare diagnostics path.

For the current log schema and parser behavior, see [`snapshot-and-allocation.md`](snapshot-and-allocation.md).

## Issue #4 shadow allocation smoke

Fresh Issue #4 runtime smoke on the active `Player.log` after enabling shadow allocation diagnostics confirmed the shadow loop was observation-only and conservative when allocator-safe numeric `readyShots` were unavailable.

First smoke, 2026-06-19, initial Issue #4 build:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- `LaunchLog` entries: 12,304, with contiguous sequence range `1-12304`
- `MissileWeapon.TryFire` rows: 665
- `SnapshotLog` entries: 665
- `AllocationLog` entries: 1,330
- `recordType=cycle`: 665
- `recordType=rejection`: 665
- `status=evaluated`: 665
- `missingInputs=readyShots,targetVelocity,pdWeightsDefaulted`: 665
- `rejectionReason=missing readyShots`: 665
- MissileWarfare issues: none

That first smoke also showed `battle="unavailable"` on both existing LaunchLog records and new AllocationLog records. Source tracing against the read-only decompiled reference found that `GameControl` is in the global namespace, while the diagnostic reflection lookup only tried `PavonisInteractive.TerraInvicta.GameControl`. The lookup now tries the global `GameControl` type first and keeps the namespaced form as a fallback.

Follow-up smoke, 2026-06-19, after rebuilding and redeploying the battle-context lookup fix:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- `LaunchLog` entries: 3,742, with contiguous sequence range `1-3742`
- `MissileWeapon.TryFire` rows: 675
- `SnapshotLog` entries: 675
- `AllocationLog` entries: 1,350
- `recordType=cycle`: 675
- `recordType=rejection`: 675
- `status=evaluated`: 675
- `missingInputs=readyShots,targetVelocity,pdWeightsDefaulted`: 675
- `rejectionReason=missing readyShots`: 675
- `AllocationLog battle unavailable`: `0/1350`
- `LaunchLog battle unavailable`: `0/3742`
- MissileWarfare issues: none

## Issue #10 launcher-selected target identity

Issue #10 smoke tests confirmed that the launcher primary-target path can recover launcher-selected target identity without changing combat behavior.

First launcher-selected target identity smoke test:

- `SnapshotLog` entries: 1416
- `targetIdentitySource=launcher`: 816
- `targetIdentitySource=none`: 600
- `readyShots=unknown`: 1416
- `remainingShots`: visible for every snapshot

Later focused-target smoke run with the trimmed launcher-only path:

- `SnapshotLog` entries: 671
- `targetIdentitySource=launcher`: 671
- launcher-selected target identity: 671/671 snapshots
- `readyShots=unknown`: 671
- `remainingShots`: visible for every snapshot
- MissileWarfare issues: none

Interpretation:

- `targetIdentitySource=launcher` means launcher/carrier primary-target or focus-fire identity.
- It is not evidence of the actual in-flight missile guidance target held by `MissileController.target`.
- `targetIdentitySource=none` does not mean the missile had no target; `MissileWeapon.TryFire` logged target values for the same run.

## Issue #11 live weapon ammo and gate evidence

Issue #11 Phase 01 recommended a separate live weapon diagnostic path around `MissileWeapon.TryFire` or `TISpaceShipState.FireWeapon` to record post-fire remaining ammo and capacity evidence. Existing postfix observations occur after ammo decrement, so those values should be named as post-fire remaining ammo, not `readyShots`.

Issue #11 Phase 02 added that evidence to successful `MissileWeapon.TryFire` `LaunchLog` rows. New optional diagnostics included:

- `ammoEvidenceSource`
- `postFireRemaining`
- `postFireWeaponHasAmmo`
- `postFireWeaponCanFire`
- `postFireOnCooldown`
- cooldown/salvo timing fields
- template and magazine capacity fields

Fresh Phase 02 runtime validation confirmed the live weapon evidence path:

- `MissileWeapon.TryFire` rows: 649
- `ammoEvidenceSource=shipAmmoByWeaponData`: 649/649
- `postFireRemaining`: populated 649/649, ranging from `0` through `14`
- `postFireWeaponHasAmmo=False` and `postFireWeaponCanFire=False`: 42 rows, matching the 42 `postFireRemaining=0` rows
- `postFireOnCooldown=True`: 649/649
- capacity evidence: `templateMagazine=6`, `magazineCapacityCurrent=15`, and `magazineCapacityMax=15` on every row

This confirmed that `TISpaceShipState.ammo[weaponData]` is visible from the live weapon postfix path and behaves as post-decrement ammo. It is not yet classified as allocator-safe fireable-shot evidence, but [`readiness-semantics.md`](../research/readiness-semantics.md) tracks the explicit hypothesis that this keyed ammo value may be the vanilla runtime shot budget when combined with known fire gates.

## Issue #11 cooldown evidence

The same runtime log showed `cooldownDuration=null`. Phase 03 traced this to `currentCooldownDuration_s` being a private field declared on the base `Weapon` class while the observed runtime object is `MissileWeapon`.

The diagnostics now use a narrow inherited-member read for that exact cooldown field. Fresh runtime validation after that change confirmed `cooldownDuration=00:00:07` on all 675 successful `MissileWeapon.TryFire` rows in the follow-up smoke log.

## Issue #11 paired pre/post observation

Issue #11 Phase 04 added paired pre/post observation on the live `MissileWeapon.TryFire(DateTime)` hook.

The prefix captures gate and ammo evidence before `MissileWeapon.TryFire` calls `TryFireCommon`, launches the projectile, enters cooldown, and calls `TISpaceShipState.FireWeapon`. The decompiled path shows `FireWeapon(module, targetedProjectile)` performs the magazine decrement through `ChangeAmmoValue(module, -1)`, so pre-fire and post-fire values must remain separately named.

New optional successful-launch fields:

- `preFireAmmoEvidenceSource`
- `preFireRemaining`
- `preFireWeaponHasAmmo`
- `preFireWeaponCanFire`
- `preFireOnCooldown`
- `preFireSalvoShotsFired`
- `preFireSalvoShots`

Fresh Phase 04 runtime smoke validation on the active `Player.log` confirmed the paired observation. This active-log smoke run superseded an earlier pre-smoke parser check that reported 4,798 `LaunchLog` rows and 675 `MissileWeapon.TryFire` rows from a previous log.

Phase 04 smoke result:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- `LaunchLog` entries: 21,474, with contiguous sequence range `1-21474`
- `MissileWeapon.TryFire` rows: 670
- `preFireAmmoEvidenceSource=shipAmmoByWeaponData`: 670/670
- all seven `preFire*` fields present on 670/670 successful try-fire rows
- numeric `preFireRemaining` and `postFireRemaining` pairs: 670/670
- `preFireRemaining - postFireRemaining = 1`: 670/670
- `SnapshotLog` entries: 670
- `readyShots=unknown`: 670/670
- MissileWarfare issues: none

Interpretation: this relationship is consistent with observing the ship ammo dictionary before and after the `FireWeapon` magazine decrement. It proves useful pre-fire ammo state is visible from the live weapon hook, but `preFireRemaining` is still ammo-state evidence. It is not automatically an allocator-safe `readyShots` source.

## Issue #15 readiness evidence result

Issue #15 wires the live `MissileWeapon.TryFire` pre-fire evidence into the projectile-fire snapshot/allocation diagnostic path when those hooks execute on the same thread.

The new snapshot and allocation cycle fields preserve the distinction between:

- numeric `readyShots` from a future proven allocator-safe fireable-shot source;
- ammo-only evidence from `TISpaceShipState.ammo[weaponData]`;
- gate/cooldown evidence such as `WeaponHasAmmo`, `WeaponCanFire`, and `OnCooldown`;
- unknown readiness with a concrete missing reason.

The current implementation deliberately removed the earlier optimistic projectile-snapshot ready-shot inference from names such as `loadedAmmo`, `loadedMissiles`, and `readyMissiles`.

Current runtime evidence remains ammo/gate evidence, not allocator-safe fireable-shot evidence, so `SnapshotLog readyShots` and allocation `totalReadyShots` remain `unknown` until shot-budget semantics are validated.

That means the project is not ready to proceed to Issue #6 controlled allocation based on numeric ready-shot counts alone. It is ready to collect fresh runtime smoke logs with Issue #15 fields and decide whether another runtime source can prove readiness semantics, whether `ammo[weaponData]` plus known gates is sufficient, or whether controlled allocation should avoid a numeric fleet-level budget.
