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

Weapon role mapping is conservative. The confirmed projectile-fire snapshot
marks the launcher weapon as `WeaponRole.Missile` when the template reports
`isMissileWeapon` or when the confirmed missile hook is the only available
signal. Unknown counts are emitted as `unknown` in logs and stored as `-1` in
Core snapshot count fields.

## Log format

Snapshot diagnostics use a separate marker so existing launch diagnostics remain
unchanged:

```text
[SnapshotLog] source="TISpaceCombatProjectileState.Fire(missile)" launcherId="..." launcher="..." targetId="..." target="..." expectedTargetPosition="..." missileId="..." missile="..." weaponRole="Missile" readyShots="unknown" remainingShots="..." missing="targetIdentity,readyShots"
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
