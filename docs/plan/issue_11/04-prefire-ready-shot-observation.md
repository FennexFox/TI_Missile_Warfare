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

- Planned from the 2026-06-19 Issue #11 follow-up comment.

## Decision log

- Phase 02 and Phase 03 validated post-fire ammo evidence and cooldown evidence, but `SnapshotLog readyShots` remains unknown.
- The next step stays inside Issue #11 because the original ready-shot goal is only partially complete.
- Any future `readyShots` mapping must be backed by pre-fire ready, loaded, or chambered evidence, not by post-decrement ammo or capacity.

## Outcomes / Retrospective

- Not started.
