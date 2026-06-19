# Phase 04: Pre-fire ready-shot observation

## Goal

Add a narrow observation-only pre-fire or paired pre/post diagnostic around the live missile weapon path to determine whether true ready, loaded, or chambered missile shot count can be recovered.

## Scope

- Inspect `MissileWeapon.TryFire(DateTime currentTime)` and the base `Weapon.TryFireCommon(DateTime currentTime)` path for a safe pre-fire observation point.
- Prefer a log-only prefix around `MissileWeapon.TryFire(DateTime currentTime)` that records pre-fire evidence before ammo decrement.
- If prefix semantics are unsafe or ambiguous, use paired pre/post observation around the same live weapon path and explicitly compare values.
- Keep pre-fire and post-fire values separately named.
- Only consider `SnapshotLog readyShots` after a documented pre-fire ready, loaded, or chambered source is proven.

## Non-goals

- Do not change launch timing, launch permission, ammo consumption, targeting, allocation, recommendation logic, projectile physics, or combat behavior.
- Do not populate `SnapshotLog readyShots` from postfix ammo evidence.
- Do not infer `readyShots` from `remainingShots`, `postFireRemaining`, capacity, cooldown, or salvo evidence.
- Do not make ready-shot recovery mandatory for snapshot emission.
- Do not broaden reflection scans beyond documented fields needed for this phase.

## Affected files

- `src/MissileFireControl.Mod/Diagnostics/CombatLaunchDiagnostics.cs`
- `src/MissileFireControl.Mod/Patches/PatchBootstrap.cs`, if a prefix is added
- `src/MissileFireControl.Mod/Diagnostics/SnapshotDiagnostics.cs`, only if a proven pre-fire ready/loaded/chambered source is later mapped into `SnapshotLog readyShots`
- `tools/parse_player_log.py`, only if first-class summaries are needed for new optional fields
- `docs/plan/issue_11/04-prefire-ready-shot-observation.md`
- `docs/battle-snapshot-extractor.md`
- `docs/confirmed-hooks.md`

## Implementation steps

- Confirm the exact Harmony patch point and signature for a `MissileWeapon.TryFire(DateTime currentTime)` prefix.
- Add compact optional fields such as `preFireAmmoEvidenceSource`, `preFireRemaining`, `preFireWeaponHasAmmo`, `preFireWeaponCanFire`, `preFireOnCooldown`, and `preFireSalvoShotsFired`.
- Keep existing `postFireRemaining` fields unchanged so runtime logs can compare pre-fire and post-fire evidence.
- If a true ready/loaded/chambered source is discovered, add `readyShotsSource` or an adjacent clearly sourced field before considering `SnapshotLog readyShots`.
- Build, deploy, run a short missile combat, and parse the active log.
- Document whether true `readyShots` is recovered, still unavailable, or requires a different observation point.

## Acceptance criteria

- Runtime diagnostics show pre-fire ammo/gate evidence for successful missile launches, or clearly document why it is unavailable.
- Pre-fire and post-fire evidence are separately named and not conflated.
- `SnapshotLog readyShots` remains `unknown` unless a documented pre-fire ready/loaded/chambered source is proven.
- Parser validation passes with `--require-launchlogs --require-snapshots`.
- Runtime smoke test shows no MissileWarfare warnings/errors.
- Documentation states whether true `readyShots` is recovered, still unavailable, or requires another observation point.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools/check_layout.py
- python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py
- python -m compileall tools
- .\build.ps1
- python tools/parse_player_log.py --require-launchlogs --require-snapshots
- git diff --check

## Manual smoke tests

- Deploy with `.\build.ps1`.
- Enable diagnostic logging and battle snapshot diagnostics in UMM.
- Run a short missile combat with missile launches.
- Parse the active `Player.log`; if the game overwrote it, parse `Player-prev.log`.
- Confirm pre-fire fields appear on successful missile launches and can be compared with `postFireRemaining`.

## Rollback risks

- Prefix diagnostics are still observation-only but add a new hook point, so hook signature drift is the primary risk.
- Extra fields can increase log volume while diagnostics are enabled.
- If the prefix causes unexpected warnings, revert the prefix and keep Phase 02 postfix evidence as the validated fallback.

## Progress

- Implemented Phase 04 pre-fire observation from the 2026-06-19 Issue #11 follow-up comment.
- Confirmed from decompiled reference that `MissileWeapon.TryFire(DateTime)` calls `TryFireCommon(currentTime)`, launches the projectile, enters cooldown, and then calls `TISpaceShipState.FireWeapon(base.weaponData, ref_projectile)`.
- Confirmed `Weapon.TryFireCommon(DateTime)` exposes gate state (`OnCooldown`, target presence, `WeaponCanFire`, salvo reset, and `OnTarget`) but no dedicated ready/loaded/chambered count.
- Confirmed `TISpaceShipState.FireWeapon(module, targetedProjectile)` decrements magazine ammo through `ChangeAmmoValue(module, -1)`, so pre-fire and post-fire ammo observations must stay separately named.
- Implemented a Harmony prefix on the existing `MissileWeapon.TryFire(System.DateTime)` patch point and carried captured values to the successful postfix via `__state`.
- Added optional successful-launch fields: `preFireAmmoEvidenceSource`, `preFireRemaining`, `preFireWeaponHasAmmo`, `preFireWeaponCanFire`, `preFireOnCooldown`, `preFireSalvoShotsFired`, and `preFireSalvoShots`.
- Kept existing `postFireRemaining`, post-fire gate/cooldown fields, and `SnapshotLog readyShots` behavior unchanged.
- Updated `docs/battle-snapshot-extractor.md` and `docs/confirmed-hooks.md` with the paired pre/post observation semantics.
- Static/package validation completed on 2026-06-19:
  - `dotnet build TI_Missile_Fire_Control.sln`: passed with 0 warnings and 0 errors.
  - `python tools/check_layout.py`: passed.
  - `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py`: passed.
  - `python -m compileall tools`: passed.
  - `.\build.ps1`: passed and deployed `dist\MissileWarfare`.
  - `python tools/parse_player_log.py --require-launchlogs --require-snapshots`: passed against the current pre-existing `Player.log` with parser verdict `OK`, `patched=3`, `skipped=0`, 4,798 `LaunchLog` rows, 675 `SnapshotLog` rows, and no MissileWarfare issues.
  - `git diff --check`: passed with only Git CRLF normalization warnings for the two edited C# files.
- Added scoped Issue #11 readiness evidence to `tools/parse_player_log.py`: pre-fire field coverage, pre-fire ammo evidence source counts, numeric `preFireRemaining - postFireRemaining` deltas, and `SnapshotLog readyShots` counts. Allocation decision summaries and tuning reports remain out of scope for Issue #11.
- Fresh runtime smoke validation completed on the active `Player.log` after deployment:
  - `python tools/parse_player_log.py --require-launchlogs --require-snapshots`: passed with parser verdict `OK`.
  - Log launch window: `2026-06-19T08:26:32.1817341Z` through `2026-06-19T08:30:57.9316235Z`.
  - Diagnostics bootstrap: `patched=3`, `skipped=0`.
  - `LaunchLog` entries: 21,474, sequence range `1-21474`, no gaps, no duplicate sequences.
  - `MissileWeapon.TryFire` rows: 670.
  - All seven `preFire*` fields present on 670/670 successful try-fire rows.
  - `preFireAmmoEvidenceSource=shipAmmoByWeaponData`: 670/670.
  - Numeric `preFireRemaining` and `postFireRemaining` pairs: 670/670.
  - `preFireRemaining - postFireRemaining = 1`: 670/670.
  - `SnapshotLog` entries: 670.
  - `readyShots=unknown`: 670/670.
  - MissileWarfare issues: none.

## Decision log

- Phase 02 and Phase 03 validated post-fire ammo evidence and cooldown evidence, but `SnapshotLog readyShots` remains unknown.
- The next step stays inside Issue #11 because the original ready-shot goal is only partially complete.
- Any future `readyShots` mapping must be backed by pre-fire ready, loaded, or chambered evidence, not by post-decrement ammo or capacity.
- The implementation uses one paired prefix/postfix patch on the existing missile try-fire target instead of adding a fourth target method. The healthy bootstrap summary remains `patched=3`, `skipped=0`.
- The prefix does not emit its own `LaunchLog` row. It returns normally and does not skip or suppress the original `TryFire` method. Successful missile launches keep one `MissileWeapon.TryFire` row with pre-fire fields followed by the existing post-fire fields, making comparison straightforward without changing sequence expectations.
- No `SnapshotLog readyShots` mapping was added because static review found pre-fire magazine/gate evidence but no true ready, loaded, or chambered count source.
- Fresh runtime data confirms `preFireRemaining` behaves as pre-decrement ammo-state evidence. It is not automatically true ready/loaded/chambered `readyShots`.

## Outcomes / Retrospective

- Phase 04 is implemented, statically validated, deployed, and smoke validated against a fresh missile combat log.
- `preFireRemaining` and `postFireRemaining` are consistent with pre/post ammo decrement on every observed successful missile try-fire row.
- True ready/loaded/chambered recovery is still unavailable from the confirmed observation point. Another observation point is required if Issue #11 needs a value that is stricter than live ship ammo state.
- `SnapshotLog readyShots` remains `unknown` because no documented pre-fire ready, loaded, or chambered source has been proven.
