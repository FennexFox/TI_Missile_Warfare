# Phase 03: Runtime validation and documentation

## Goal

Validate the ready-shot diagnostics in a live combat log and document the confirmed source, fallback behavior, and remaining gaps.

## Scope

- Run static validation after implementation.
- Parse runtime logs for `readyShots`, `remainingShots`, missing fields, and any new source/evidence fields.
- Document findings locally and prepare a GitHub issue #11 comment for user review unless explicit GitHub write approval is given.
- Decide whether issue #11 is complete or whether a follow-up observation point is needed.

## Non-goals

- Do not broaden implementation during verification unless validation proves a small parser/doc fix is required.
- Do not change combat behavior or start recommendation/allocation work.

## Affected files

- `docs/battle-snapshot-extractor.md`
- `docs/confirmed-hooks.md`
- `docs/plan/issue_11/03-verification.md`
- `src/MissileFireControl.Mod/Diagnostics/CombatLaunchDiagnostics.cs`
- GitHub issue #11 comment draft

## Implementation steps

- Run all validation commands from this phase.
- Deploy the mod and run a short missile combat when local game access is available.
- Parse the log and record counts for `readyShots`, `remainingShots`, missing fields, and warnings/errors.
- Update docs with exact runtime counts and source names.
- Prepare a concise GitHub issue #11 comment with results and remaining risks for user review. Post it only when explicit GitHub write approval is given.

## Acceptance criteria

- Static validation passes.
- Parser verdict is `OK` for launch and snapshot requirements.
- Runtime findings clearly state whether `readyShots` is recovered, partially recovered, or still unavailable.
- Live smoke test produces no MissileWarfare warnings/errors.
- Documentation records the confirmed source or explains why the source remains unknown.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools/check_layout.py
- python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py
- python -m compileall tools
- .\build.ps1
- python tools/parse_player_log.py --require-launchlogs --require-snapshots

## Manual smoke tests

- Deploy with `.\build.ps1`.
- Enable `EnableDiagnostics` and `EnableSnapshotDiagnostics`.
- Run a short missile combat with missile launches.
- Parse the active `Player.log`; if the game overwrote it, parse `Player-prev.log`.

## Rollback risks

- Documentation-only changes are low risk.
- If diagnostics cause overhead or log spam, disable battle snapshot diagnostics or revert Phase 2.

## Progress

- Completed Phase 03 static validation, active-log parser validation, cooldown follow-up triage, and local documentation.

## Decision log

- Runtime validation should compare against the Issue #10 baseline carefully: one focused-target smoke run showed launcher-selected target identity at 671/671 snapshots, but that is not a general guarantee and is not proof of actual in-flight missile guidance target identity. Ready shots remained unknown in that run.
- Phase 02 runtime validation confirmed `TISpaceShipState.ammo[weaponData]` is visible from successful `MissileWeapon.TryFire` postfix rows. This is post-decrement ammo evidence, not ready/loaded/chambered shot evidence.
- `cooldownDuration` logged as `null` in the Phase 02 runtime log because `currentCooldownDuration_s` is a private field declared on the base `Weapon` class while the runtime object is `MissileWeapon`. The existing `ReadMember` helper queried the concrete type only.
- A narrow diagnostic-only inherited-member helper was added and used only for `cooldownDuration`. It walks the runtime type's base chain for the exact member name with `DeclaredOnly`; it does not add broad reflection scans or affect gameplay.
- Issue #11 should be treated as partially complete: live post-fire ammo evidence is recovered and validated, but true pre-fire ready/loaded/chambered shot counts are still not recovered and require a separate prefix or paired pre/post observation.

## Outcomes / Retrospective

- Static validation passed:
  - `dotnet build TI_Missile_Fire_Control.sln`: passed, 0 warnings, 0 errors.
  - `python tools\check_layout.py`: passed.
  - `python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py`: passed.
  - `python -m compileall tools`: passed.
  - `.\build.ps1`: passed, packaged and deployed the mod.
  - `git diff --check`: passed with only the existing CRLF warning for `CombatLaunchDiagnostics.cs`.
- Active-log parser validation passed with `python tools\parse_player_log.py --require-launchlogs --require-snapshots`. The parsed `Player.log` was last written on 2026-06-19 at about 13:34 KST and still represents the pre-cooldown-helper runtime smoke:
  - verdict: `OK`
  - diagnostics bootstrap: `patched=3`, `skipped=0`
  - `LaunchLog` rows: 13,644
  - `MissileWeapon.TryFire` rows: 649
  - `TISpaceCombatProjectileState.Fire(missile)` rows: 649
  - `TISpaceShipState.FireWeapon` rows: 12,346
  - `SnapshotLog` rows: 649
  - sequence gaps: none
  - duplicate sequences: none
  - MissileWarfare issues: none
  - `SnapshotLog readyShots`: still `unknown` / missing for 649 snapshots
  - launcher-selected target identity: 649/649 snapshots with `targetIdentitySource=launcher`
- Confirmed Phase 02 live ammo evidence from the same runtime log:
  - `ammoEvidenceSource=shipAmmoByWeaponData`: 649/649 `MissileWeapon.TryFire` rows
  - `postFireRemaining`: populated 649/649, range `0` through `14`
  - distribution: `0:42`, `1:42`, `2:42`, `3:43`, `4:43`, `5:43`, `6:43`, `7:43`, `8:43`, `9:44`, `10:44`, `11:44`, `12:44`, `13:44`, `14:45`
  - `postFireWeaponHasAmmo=False`: 42 rows, matching `postFireRemaining=0`
  - `postFireWeaponCanFire=False`: 42 rows, matching `postFireRemaining=0`
  - `postFireOnCooldown=True`: 649/649
  - capacity evidence: `templateMagazine=6`, `magazineCapacityCurrent=15`, `magazineCapacityMax=15` on all 649 rows
- Cooldown follow-up status:
  - Implemented a bounded inherited-member read for `currentCooldownDuration_s`.
  - The code is built and deployed.
  - Fresh in-game runtime validation after deployment confirmed `cooldownDuration=00:00:07` on all 675 `MissileWeapon.TryFire` rows.
- Fresh cooldown-helper runtime validation passed with `python tools\parse_player_log.py --require-launchlogs --require-snapshots` against a log written on 2026-06-19 at about 13:52 KST:
  - verdict: `OK`
  - diagnostics bootstrap: `patched=3`, `skipped=0`
  - `LaunchLog` rows: 4,798
  - `MissileWeapon.TryFire` rows: 675
  - `TISpaceCombatProjectileState.Fire(missile)` rows: 675
  - `TISpaceShipState.FireWeapon` rows: 3,448
  - `SnapshotLog` rows: 675
  - sequence gaps: none
  - duplicate sequences: none
  - MissileWarfare issues: none
  - `ammoEvidenceSource=shipAmmoByWeaponData`: 675/675
  - `postFireRemaining`: populated 675/675 with each value from `0` through `14` appearing 45 times
  - `postFireWeaponHasAmmo=False`: 45 rows, matching `postFireRemaining=0`
  - `postFireWeaponCanFire=False`: 45 rows, matching `postFireRemaining=0`
  - `postFireOnCooldown=True`: 675/675
  - `cooldownDuration=00:00:07`: 675/675
  - `SnapshotLog readyShots`: still `unknown` / missing for 675 snapshots
  - launcher-selected target identity: 635/675 snapshots with `targetIdentitySource=launcher`; 40 snapshots had `targetIdentitySource=none`
- Issue #11 completion assessment:
  - Phase 01 source discovery: complete.
  - Phase 02 live post-fire ammo diagnostics: complete and runtime validated.
  - Phase 03 verification and documentation: complete for current evidence, including the cooldown follow-up.
  - Overall issue goal, recovering true `readyShots`: partial. `readyShots` should remain unknown until a documented pre-fire ready/loaded/chambered source is observed.

## GitHub issue #11 comment draft

```md
Phase 03 verification is complete locally; this is a draft for review, not yet posted.

Summary:

- Phase 01 confirmed the projectile snapshot hook lacks `weaponData`, so it cannot safely resolve per-weapon ammo from `TISpaceShipState.ammo[ModuleDataEntry]`.
- Phase 02 confirmed live `MissileWeapon.TryFire` postfix diagnostics can see `TISpaceShipState.ammo[weaponData]`.
- Phase 03 static validation and parser validation passed.
- `postFireRemaining` is confirmed as post-decrement ammo evidence, not `readyShots`.
- `SnapshotLog readyShots` remains intentionally unknown.

Validation:

- `dotnet build TI_Missile_Fire_Control.sln`: passed, 0 warnings, 0 errors.
- `python tools\check_layout.py`: passed.
- `python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py`: passed.
- `python -m compileall tools`: passed.
- `.\build.ps1`: passed, packaged and deployed.
- `python tools\parse_player_log.py --require-launchlogs --require-snapshots`: passed with verdict `OK`.
- `git diff --check`: passed with only the existing CRLF warning for `CombatLaunchDiagnostics.cs`.

Runtime evidence from the latest available Player.log:

- `LaunchLog` rows: 13,644
- `SnapshotLog` rows: 649
- `MissileWeapon.TryFire` rows: 649
- sequence gaps: none
- duplicate sequences: none
- MissileWarfare issues: none
- `ammoEvidenceSource=shipAmmoByWeaponData`: 649/649
- `postFireRemaining`: populated 649/649, range `0` through `14`
- `postFireRemaining=0`: 42 rows
- `postFireWeaponHasAmmo=False`: 42 rows
- `postFireWeaponCanFire=False`: 42 rows
- `postFireOnCooldown=True`: 649/649
- capacity evidence: `templateMagazine=6`, `magazineCapacityCurrent=15`, `magazineCapacityMax=15` on all 649 rows

Cooldown follow-up:

- `cooldownDuration` logged as `null` in the Phase 02 runtime log because `currentCooldownDuration_s` is a private field on base `Weapon`, while the observed runtime object is `MissileWeapon`.
- A narrow diagnostic-only helper now reads the exact inherited instance member for `cooldownDuration`.
- Fresh in-game runtime validation confirmed `cooldownDuration=00:00:07` on all 675 `MissileWeapon.TryFire` rows.

Fresh cooldown-helper runtime evidence:

- `LaunchLog` rows: 4,798
- `SnapshotLog` rows: 675
- `MissileWeapon.TryFire` rows: 675
- sequence gaps: none
- duplicate sequences: none
- MissileWarfare issues: none
- `ammoEvidenceSource=shipAmmoByWeaponData`: 675/675
- `postFireRemaining`: populated 675/675, values `0` through `14` each appeared 45 times
- `postFireWeaponHasAmmo=False`: 45 rows, matching `postFireRemaining=0`
- `postFireWeaponCanFire=False`: 45 rows, matching `postFireRemaining=0`
- `postFireOnCooldown=True`: 675/675
- `cooldownDuration=00:00:07`: 675/675

Issue status:

- Live post-fire ammo evidence is recovered and validated.
- Cooldown duration evidence is recovered and validated.
- True pre-fire ready/loaded/chambered `readyShots` is not recovered yet.
- Issue #11 should remain partial unless the acceptance scope is post-fire ammo evidence only; recovering real `readyShots` requires a follow-up prefix or paired pre/post live weapon observation.
```
