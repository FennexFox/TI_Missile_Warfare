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
- optional targetable state -> target `ShipSnapshot`

Weapon role mapping is conservative. The confirmed projectile-fire snapshot
marks the launcher weapon as `WeaponRole.Missile` when the template reports
`isMissileWeapon` or when the confirmed missile hook is the only available
signal. Unknown counts are emitted as `unknown` in logs and stored as `-1` in
Core snapshot count fields.

Target identity probing is also conservative. The projectile-state fire hook
does not receive the live `MissileController.target` object; `MissileWeapon`
passes that target to the Unity controller immediately after the state fire
call. The snapshot extractor therefore checks the launcher/carrier for
`combatPrimaryTarget` or related primary-target members. Candidate target
wrappers are unwrapped through `combatTargetableState`, `GetCombatantState`,
`GetTargetableState`, `ShipState`, and `WeaponCarrierState` when those members
are present. This keeps the diagnostic path compact and avoids repeated broad
reflection probes that did not recover identity in the first runtime test. If no
concrete identity is visible, `targetId`, `target`, and `targetTeam` remain
`unknown`, `targetIdentitySource` is `none`, and `missing=targetIdentity`
remains valid.

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

## Target identity runtime findings

The first Issue #10 smoke test with target identity probing found partial
coverage:

- `SnapshotLog` entries: 1416
- `targetIdentitySource=launcher`: 816
- `targetIdentitySource=none`: 600
- `readyShots=unknown`: 1416
- `remainingShots`: visible for every snapshot

`targetIdentitySource=launcher` means the extractor recovered identity from the
launcher/carrier primary-target state. `targetIdentitySource=none` does not mean
the missile had no target; `MissileWeapon.TryFire` logged target values for the
same run. It means the projectile-state snapshot hook could not see a concrete
target identity through the launcher primary-target path for that launch.

`readyShots` remains unknown because the projectile-state hook does not expose
the live `MissileWeapon` runtime object. The hook can see remaining magazine-like
counts from visible launcher/template state, but ready/loaded/chambered missile
state appears to live on weapon/module runtime state and should not be inferred
from `remainingShots` without a documented source.

The initial target probe tried broader reflection fallbacks, but runtime data
showed only the launcher path recovered identity. The extractor now keeps that
narrow path to reduce diagnostic overhead while preserving the confirmed signal.
For fuller target coverage, add a separate observation point around
`MissileWeapon.target` or `MissileController.target`.
