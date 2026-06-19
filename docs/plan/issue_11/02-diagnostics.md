# Phase 02: Add log-only ready-shot evidence

## Goal

Add the smallest log-only diagnostic evidence needed to confirm whether the discovered ready-shot source is available at runtime.

## Scope

- Add optional extraction or logging for documented ready-shot candidate members.
- Prefer using existing snapshot diagnostics if the candidate object is visible there.
- If the candidate object is only visible from `MissileWeapon.TryFire`, add compact evidence to `LaunchLog` or a parser-supported diagnostic field without changing launch behavior.
- Keep `readyShots=unknown` valid when no reliable source is present.
- Update `tools/parse_player_log.py` only if new fields need first-class summary support.

## Non-goals

- Do not change launch timing, target assignment, ammo consumption, cooldowns, allocation, or projectile physics.
- Do not add broad reflection scans in high-volume paths.
- Do not make ready-shot count mandatory for snapshot emission.
- Do not use ready-shot data for decisions in this phase.

## Affected files

- `src/MissileFireControl.Mod/Adapters/CombatSnapshotExtractor.cs`
- `src/MissileFireControl.Mod/Adapters/GameObjectReader.cs`
- `src/MissileFireControl.Mod/Diagnostics/CombatLaunchDiagnostics.cs`
- `src/MissileFireControl.Mod/Diagnostics/SnapshotDiagnostics.cs`
- `tools/parse_player_log.py`
- `docs/battle-snapshot-extractor.md`

## Implementation steps

- Add narrowly named member probes based on Phase 1 findings.
- Include an evidence/source field if needed, such as `readyShotsSource`, so runtime logs explain where the value came from.
- Keep formatting parser-compatible with quoted key/value pairs.
- Avoid repeated fallback chains that produced no signal in prior target-identity work.
- Build and run parser checks before requesting runtime smoke testing.

## Acceptance criteria

- Runtime logs can show whether the ready-shot candidate source is visible.
- `[SnapshotLog]` reports `readyShots` when safely discoverable, or keeps `unknown` with missing-field reporting when not.
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
- Confirm whether `readyShots` is populated and whether `remainingShots` remains stable.

## Rollback risks

- Reflection paths may be version-sensitive. Roll back by disabling snapshot diagnostics or reverting this phase's diagnostic additions.
- Extra diagnostics can increase log volume or runtime overhead, so keep new fields compact and behind existing diagnostic toggles.

## Progress

- Planned.

## Decision log

- Implementation should wait for Phase 1 source discovery; do not add speculative member names beyond documented candidates.

## Outcomes / Retrospective

- Not completed yet.
