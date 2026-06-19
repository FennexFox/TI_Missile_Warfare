# Phase 02: Add log-only live weapon ammo evidence

## Goal

Add the smallest log-only diagnostic evidence needed to confirm whether live weapon/module ammo state is visible at runtime.

## Scope

- Add optional extraction or logging for documented live weapon/module ammo-state candidate members.
- Prefer the existing successful `MissileWeapon.TryFire` postfix because it is missile-specific and owns the live weapon plus `weaponData`.
- Add compact evidence to `LaunchLog` without changing launch behavior.
- Keep `readyShots=unknown` valid when no reliable source is present.
- Update `tools/parse_player_log.py` only if new fields need first-class summary support.

## Non-goals

- Do not change launch timing, target assignment, ammo consumption, cooldowns, allocation, or projectile physics.
- Do not add broad reflection scans in high-volume paths.
- Do not make ready-shot count mandatory for snapshot emission.
- Do not use ready-shot data for decisions in this phase.
- Do not populate `SnapshotLog readyShots` from postfix ammo evidence.
- Do not infer ready/loaded/chambered shots from `remainingShots`.

## Affected files

- `src/MissileFireControl.Mod/Diagnostics/CombatLaunchDiagnostics.cs`
- `tools/parse_player_log.py`
- `docs/battle-snapshot-extractor.md`
- `docs/confirmed-hooks.md`

## Implementation steps

- Add narrowly named member probes based on Phase 1 findings.
- Include an evidence/source field, `ammoEvidenceSource`, so runtime logs explain where the value came from.
- Keep formatting parser-compatible with quoted key/value pairs.
- Avoid repeated fallback chains that produced no signal in prior target-identity work.
- Build and run parser checks before requesting runtime smoke testing.

## Acceptance criteria

- Runtime logs can show whether the live weapon/module ammo-state source is visible.
- `[SnapshotLog]` keeps `readyShots=unknown`; postfix evidence is not a ready/loaded/chambered count.
- Parser validation remains compatible with existing `LaunchLog` and `SnapshotLog` formats.
- No gameplay behavior changes are introduced.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools/check_layout.py
- python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py
- python -m compileall tools
- .\build.ps1
- python tools/parse_player_log.py --require-launchlogs --require-snapshots

## Manual smoke tests

- Deploy with `.\build.ps1`.
- Enable diagnostic logging and battle snapshot diagnostics in UMM.
- Run a short missile combat.
- Parse the active log with `python tools\parse_player_log.py --require-launchlogs --require-snapshots`.
- Confirm `readyShots` remains `unknown`, and verify `ammoEvidenceSource` and `postFireRemaining` are populated in `MissileWeapon.TryFire` log rows.

## Rollback risks

- Reflection paths may be version-sensitive. Roll back by disabling snapshot diagnostics or reverting this phase's diagnostic additions.
- Extra diagnostics can increase log volume or runtime overhead, so keep new fields compact and behind existing diagnostic toggles.

## Progress

- Implemented compact `MissileWeapon.TryFire` postfix evidence in `LaunchLog`.

## Decision log

- Implementation should wait for Phase 1 source discovery; do not add speculative member names beyond documented candidates.
- Runtime evidence is emitted from `MissileWeapon.TryFire` postfix instead of `SnapshotLog` because the projectile snapshot hook lacks `weaponData`.
- `postFireRemaining` is read from `TISpaceShipState.ammo[weaponData]` when visible and is explicitly named as post-fire evidence because `TISpaceShipState.FireWeapon` decrements ammo before the postfix returns.
- `postFireWeaponHasAmmo`, `postFireWeaponCanFire`, `postFireOnCooldown`, cooldown duration, salvo counters, and capacity fields are logged as separate evidence and are not used as `readyShots`.
- `tools/parse_player_log.py` did not need a code change because the parser already accepts optional quoted key/value fields in `LaunchLog`.

## Outcomes / Retrospective

- Phase 02 adds observation-only live weapon ammo evidence to successful missile `TryFire` launch logs. Runtime smoke should confirm whether `ammoEvidenceSource=shipAmmoByWeaponData` and `postFireRemaining` appear in active combat logs.
- Static validation passed: `dotnet build TI_Missile_Fire_Control.sln`, `python tools/check_layout.py`, `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py`, `python -m compileall tools`, and `.\build.ps1`.
- Fresh runtime validation passed with `python tools\parse_player_log.py --require-launchlogs --require-snapshots` against a log written on 2026-06-19 at about 13:32 KST. Parser verdict was `OK`: 13,644 `LaunchLog` rows, 649 `SnapshotLog` rows, no sequence gaps, no duplicate sequences, and no MissileWarfare issues.
- The new live weapon fields appeared on all 649 `MissileWeapon.TryFire` rows: `ammoEvidenceSource=shipAmmoByWeaponData` was 649/649 and `postFireRemaining` was populated 649/649.
- `postFireRemaining` ranged from 0 through 14 with this distribution: `0:42`, `1:42`, `2:42`, `3:43`, `4:43`, `5:43`, `6:43`, `7:43`, `8:43`, `9:44`, `10:44`, `11:44`, `12:44`, `13:44`, `14:45`.
- The 42 zero-ammo rows aligned with `postFireWeaponHasAmmo=False` and `postFireWeaponCanFire=False`; the other 607 rows reported both fields as `True`. This supports the interpretation that `postFireRemaining` is actual post-decrement ammo indexed by `TISpaceShipState.ammo[weaponData]`.
- `postFireOnCooldown=True` appeared on all 649 rows. Capacity evidence was stable: `templateMagazine=6`, `magazineCapacityCurrent=15`, and `magazineCapacityMax=15` on all 649 rows.
- `cooldownDuration` still logged as `null`, likely because the reflection path does not reach that base/private field. This does not affect the ammo evidence; `lastFiredAt`, salvo, ammo, and capacity fields are populated.
