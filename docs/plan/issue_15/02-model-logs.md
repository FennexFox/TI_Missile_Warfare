# Phase 02: Readiness evidence model and diagnostics logs

## Goal

Add readiness evidence metadata to snapshot/allocation diagnostics while keeping numeric
`readyShots` unknown unless true ready-shot evidence is proven.

## Scope

- Add optional readiness evidence fields to Core snapshot models.
- Update `CombatSnapshotExtractor` to stop optimistic ready-shot inference.
- Emit `readyShotEvidenceSource`, `readinessMissingReason`, `ammoEvidenceSource`, and
  optional count context in `SnapshotLog` and allocation cycle rows.
- Keep shadow allocation observation-only and conservative.

## Non-goals

- No controlled allocation or combat command application.
- No launch suppression, reassignment, target behavior, AI, projectile, guidance,
  physics, or damage changes.
- No heuristic promotion of `preFireRemaining`, `remainingShots`, or gate-state fields
  into `readyShots`.

## Affected files

- `src/MissileFireControl.Core/Models/MissileInventorySnapshot.cs`
- `src/MissileFireControl.Core/Models/WeaponSnapshot.cs`
- `src/MissileFireControl.Mod/Adapters/CombatSnapshotExtractor.cs`
- `src/MissileFireControl.Mod/Diagnostics/CombatLaunchDiagnostics.cs`
- `src/MissileFireControl.Mod/Diagnostics/SnapshotDiagnostics.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`

## Implementation steps

1. Add model properties for readiness evidence source, missing reason, ammo evidence
   source, live weapon state, ready weapon count, and unknown readiness weapon count.
2. Replace `FirstKnownCount(... readyShots, loadedAmmo, loadedMissiles, readyMissiles)`
   with a helper that returns numeric ready shots only from explicitly accepted ready
   source names and records the source.
3. Treat remaining/magazine-like counts as ammo evidence and keep readiness missing
   reason precise when only ammo evidence exists.
4. Append optional evidence fields to `SnapshotLog` after existing fields.
5. Append optional evidence fields to allocation cycle rows after existing fields.
6. Keep allocation request construction and rejection semantics conservative when
   readiness is unknown.

## Acceptance criteria

- `readyShots` and `totalReadyShots` remain backward-compatible existing fields.
- Numeric ready shots require a non-`unknown` `readyShotEvidenceSource`.
- Unknown readiness includes a useful `readinessMissingReason`.
- Ammo evidence is visible without being treated as allocator-ready shots.
- Shadow allocation remains observation-only.

## Validation commands

- `dotnet build TI_Missile_Fire_Control.sln`

## Manual smoke tests

- Inspect generated log field ordering conceptually: new fields are appended and optional
  so older parser behavior remains valid.

## Rollback risks

- Model properties are additive. Rollback is low risk unless external tooling starts
  depending on new fields before the change is released.

## Progress

- Added readiness evidence metadata to inventory and weapon snapshots.
- Removed optimistic projectile-snapshot ready-shot inference from magazine-like member
  names.
- Threaded current `MissileWeapon.TryFire` pre-fire ammo/gate evidence into projectile
  snapshot and shadow allocation diagnostics.
- Appended readiness evidence fields to `SnapshotLog` and allocation cycle records.
- Ran `dotnet build TI_Missile_Fire_Control.sln`: passed with 0 warnings and 0 errors.

## Decision log

- Added `CombatLaunchDiagnostics.cs` to the phase write scope because it is the only
  existing place with live `MissileWeapon.TryFire` pre-fire evidence that can be safely
  correlated with the projectile-fire snapshot on the same thread.
- Kept `ReadyShots=-1` for current live evidence because pre-fire ammo and gate state are
  not proven true ready/loaded/chambered shot counts.
- Kept the observation-only allocator clamp of unknown ready shots to zero while exposing
  `totalReadyShots="unknown"` and missing-readiness metadata in logs.

## Outcomes / Retrospective

- Completed. Runtime behavior remains diagnostic-only; the new fields make readiness
  source and missing reason explicit without promoting ammo evidence to `readyShots`.
