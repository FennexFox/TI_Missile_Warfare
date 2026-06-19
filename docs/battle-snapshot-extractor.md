# Battle snapshot extractor

Issue #3 adds an observation-only adapter that converts confirmed Terra Invicta
combat launch objects into the game-independent Core snapshot model.

## Runtime source

The first extractor is wired to the confirmed missile projectile hook:

```text
PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState.Fire
```

This hook is used because it has confirmed missile-only launch coverage and
exposes the launcher/carrier, missile template, launch time, origin position,
expected target position, and origin velocity.

## Toggle

Snapshot logging is controlled by two UMM settings:

- `EnableDiagnostics`
- `EnableSnapshotDiagnostics`

Both must be enabled before `[SnapshotLog]` entries are emitted.
`EnableSnapshotDiagnostics` defaults to `false` so normal diagnostic runs keep
their previous log volume.

## Snapshot mapping

The mod adapter maps visible runtime objects into Core models:

- launcher/carrier -> `ShipSnapshot`
- missile template -> `MissileProfile`
- missile launch inventory state -> `MissileInventorySnapshot`
- launcher missile weapon -> `WeaponSnapshot`
- optional launcher-selected targetable state -> target `ShipSnapshot`

Weapon role mapping is conservative. The confirmed projectile-fire snapshot
marks the launcher weapon as `WeaponRole.Missile` when the template reports
`isMissileWeapon` or when the confirmed missile hook is the only available
signal. Unknown counts are emitted as `unknown` in logs and stored as `-1` in
Core snapshot count fields.

Launcher-selected target identity probing is also conservative. The
projectile-state fire hook does not receive the live `MissileController.target`
object; `MissileWeapon` passes that target to the Unity controller immediately
after the state fire call. The snapshot extractor therefore checks the
launcher/carrier for `combatPrimaryTarget` or related primary-target members.
Candidate target wrappers are unwrapped through `combatTargetableState`,
`GetCombatantState`, `GetTargetableState`, `ShipState`, and
`WeaponCarrierState` when those members are present. This keeps the diagnostic
path compact and avoids repeated broad reflection probes that did not recover
identity in the first runtime test. If no concrete launcher-selected identity is
visible, `targetId`, `target`, and `targetTeam` remain `unknown`,
`targetIdentitySource` is `none`, and `missing=targetIdentity` remains valid.

## Log format

Snapshot diagnostics use a separate marker so existing launch diagnostics remain
unchanged:

```text
[SnapshotLog] source="TISpaceCombatProjectileState.Fire(missile)" launcherId="..." launcher="..." launcherTeam="..." targetId="..." target="..." targetTeam="..." targetIdentitySource="..." expectedTargetPosition="..." missileId="..." missile="..." weaponRole="Missile" readyShots="unknown" remainingShots="..." missing="targetIdentity,readyShots"
```

The `missing` field is expected to be useful early on. It records which fields
were not visible from the hook rather than treating partial snapshots as fatal.

## Validation

Static validation:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py
python tools\parse_player_log.py --require-launchlogs
```

Runtime validation after deploying and enabling battle snapshot diagnostics:

```powershell
python tools\parse_player_log.py --require-launchlogs --require-snapshots
```

Expected runtime result:

- diagnostics bootstrap remains `patched=3`, `skipped=0`;
- LaunchLog entries remain present and contiguous;
- SnapshotLog entries are present;
- MissileWarfare issues remain empty.

## Launcher-selected target identity runtime findings

Issue #10 smoke tests confirmed that the launcher primary-target path can
recover launcher-selected target identity without changing combat behavior.

The first launcher-selected target identity smoke test found partial coverage:

- `SnapshotLog` entries: 1416
- `targetIdentitySource=launcher`: 816
- `targetIdentitySource=none`: 600
- `readyShots=unknown`: 1416
- `remainingShots`: visible for every snapshot

A later focused-target smoke run with the trimmed launcher-only path found full
launcher-selected target identity coverage for that combat:

- `SnapshotLog` entries: 671
- `targetIdentitySource=launcher`: 671
- launcher-selected target identity: 671/671 snapshots
- `readyShots=unknown`: 671
- `remainingShots`: visible for every snapshot
- MissileWarfare issues: none

`targetIdentitySource=launcher` means the extractor recovered identity from the
launcher/carrier primary-target or focus-fire state. It is not evidence of the
actual in-flight missile guidance target held by `MissileController.target`.
`targetIdentitySource=none` does not mean the missile had no target;
`MissileWeapon.TryFire` logged target values for the same run. It means the
projectile-state snapshot hook could not see a concrete launcher-selected target
identity through the launcher primary-target path for that launch.

`readyShots` remains unknown because the projectile-state hook does not expose
the live `MissileWeapon` runtime object. The hook can see remaining magazine-like
counts from visible launcher/template state, but Issue #11 source discovery
found that the reliable runtime ammo value is `TISpaceShipState.ammo[weaponData]`.
That value is keyed by `ModuleDataEntry`, and the projectile-state hook does not
receive the firing module key. Any count found from the snapshot path should
therefore be treated as magazine-like evidence until a live weapon/module
observation confirms its semantics. Ready/loaded/chambered missile state appears
to live on weapon/module runtime state and should not be inferred from
`remainingShots` without a documented source.

Issue #11 Phase 01 recommends a separate live weapon diagnostic path around
`MissileWeapon.TryFire` or `TISpaceShipState.FireWeapon` to record post-fire
remaining ammo and capacity evidence. Existing postfix observations occur after
ammo decrement, so those values should be named as post-fire remaining ammo, not
`readyShots`.

Issue #11 Phase 02 adds that evidence to successful `MissileWeapon.TryFire`
`LaunchLog` rows. The new fields are optional diagnostics:

- `ammoEvidenceSource`: `shipAmmoByWeaponData` when `TISpaceShipState.ammo` can
  be indexed by the live weapon's `weaponData`; otherwise `none`.
- `postFireRemaining`: the post-decrement value from
  `TISpaceShipState.ammo[weaponData]`, or `unknown`.
- `postFireWeaponHasAmmo`, `postFireWeaponCanFire`, and `postFireOnCooldown`:
  post-fire gate/cooldown evidence, not ready-shot counts.
- `cooldownDuration`, `lastFiredAt`, `salvoShotsFired`, `salvoShots`, and
  `intraSalvoCooldownS`: compact cooldown and salvo timing evidence.
- `templateMagazine`, `magazineCapacityCurrent`, and `magazineCapacityMax`:
  capacity evidence from the projectile weapon template and launcher state, not
  a ready/loaded/chambered count.

These fields do not populate `SnapshotLog readyShots`. `readyShots` remains
unknown until a pre-fire ready, loaded, or chambered source is documented.

Fresh Phase 02 runtime validation confirmed the live weapon evidence path:

- `MissileWeapon.TryFire` rows: 649
- `ammoEvidenceSource=shipAmmoByWeaponData`: 649/649
- `postFireRemaining`: populated 649/649, ranging from `0` through `14`
- `postFireWeaponHasAmmo=False` and `postFireWeaponCanFire=False`: 42 rows,
  matching the 42 `postFireRemaining=0` rows
- `postFireOnCooldown=True`: 649/649
- capacity evidence: `templateMagazine=6`, `magazineCapacityCurrent=15`, and
  `magazineCapacityMax=15` on every row

This confirms that `TISpaceShipState.ammo[weaponData]` is visible from the
live weapon postfix path and behaves as post-decrement ammo. It is still not
ready/loaded/chambered shot evidence.

The same runtime log showed `cooldownDuration=null`. Phase 03 traced this to
`currentCooldownDuration_s` being a private field declared on the base `Weapon`
class while the observed runtime object is `MissileWeapon`. The diagnostics now
use a narrow inherited-member read for that exact cooldown field. Fresh runtime
validation after that change confirmed `cooldownDuration=00:00:07` on all 675
successful `MissileWeapon.TryFire` rows in the follow-up smoke log.

The initial target probe tried broader reflection fallbacks, but runtime data
showed only the launcher path recovered identity. The extractor now keeps that
narrow path to reduce diagnostic overhead while preserving the confirmed signal.
For actual projectile/controller guidance target coverage, add a separate
observation point around
`MissileWeapon.target` or `MissileController.target`.

Issue #11 Phase 04 adds paired pre/post observation on the live
`MissileWeapon.TryFire(DateTime)` hook. The prefix captures gate and ammo
evidence before `MissileWeapon.TryFire` calls `TryFireCommon`, launches the
projectile, enters cooldown, and calls `TISpaceShipState.FireWeapon`. The
decompiled path shows `FireWeapon(module, targetedProjectile)` performs the
magazine decrement through `ChangeAmmoValue(module, -1)`, so the pre-fire and
post-fire values must remain separately named. The Harmony prefix returns
normally and does not suppress the original `TryFire` method; it only captures
diagnostic `__state` for the successful postfix row.

New optional successful-launch fields are:

- `preFireAmmoEvidenceSource`: `shipAmmoByWeaponData` when
  `TISpaceShipState.ammo` can be indexed by the live weapon's `weaponData`;
  otherwise `none` or `unavailable`.
- `preFireRemaining`: the pre-decrement value from
  `TISpaceShipState.ammo[weaponData]`, or `unknown`.
- `preFireWeaponHasAmmo`, `preFireWeaponCanFire`, and `preFireOnCooldown`:
  pre-fire gate/cooldown evidence captured before `TryFireCommon`.
- `preFireSalvoShotsFired` and `preFireSalvoShots`: pre-fire salvo evidence.

The static source review still found no dedicated ready, loaded, or chambered
missile count in the confirmed `MissileWeapon.TryFire` / `TryFireCommon` path.
`SnapshotLog readyShots` therefore remains `unknown` until runtime evidence
proves a true ready/loaded/chambered source rather than magazine or gate state.

Fresh Phase 04 runtime smoke validation on the active `Player.log` confirmed the
paired observation:

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

This relationship is consistent with observing the ship ammo dictionary before
and after the `FireWeapon` magazine decrement. It proves useful pre-fire ammo
state is visible from the live weapon hook, but `preFireRemaining` is still
ammo-state evidence. It is not automatically a true ready, loaded, or chambered
`readyShots` source.
