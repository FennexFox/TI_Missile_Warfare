# Issue #18/#19 Implementation Phase

## Goal

Add explicit velocity and PD evidence/default diagnostics without changing controlled gameplay behavior.

## Scope

- `src/MissileFireControl.Core/Models/ShipSnapshot.cs`
- `src/MissileFireControl.Mod/Adapters/CombatSnapshotExtractor.cs`
- `src/MissileFireControl.Mod/Diagnostics/SnapshotDiagnostics.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `tools/parse_player_log.py`
- `docs/diagnostics/snapshot-and-allocation.md`

## Non-goals

- Recover observed target PD weapon lists.
- Add historical position-delta velocity derivation.
- Start controlled allocation experiments.

## Acceptance Criteria

- Snapshot logs include target velocity or a target velocity missing reason.
- Allocation cycle logs include target velocity and relative velocity evidence fields.
- Allocation cycle logs distinguish PD defaults from observed/unknown evidence.
- Parser reports coverage and missing/default reason breakdowns.
- Existing ammo/gate budget reporting remains intact.

## Progress

- Added target velocity presence tracking to extracted ship snapshots.
- Added target and relative velocity evidence fields to snapshot and allocation logs.
- Added target velocity capture from the live `MissileWeapon.TryFire` target (`IDamageable.velocityVector_kps`) and threaded it through the existing same-thread readiness handoff.
- Added a same-target `positionAtTime(t + 1s) - positionAtTime(t)` derivative fallback, converted from combat scale units to kps.
- Added explicit PD default model fields to snapshot and allocation logs.
- Added parser counters and summary output for the new evidence fields.
- Updated diagnostics schema documentation.

## Decision Log

- Kept `pdWeightsDefaulted` in `missingInputs` as a limitation marker because observed PD weights are still not recovered.
- Used the hook-provided origin velocity as launcher velocity evidence for shadow allocation diagnostics when present.
- Decompiled source review showed `TISpaceCombatProjectileState.Fire(...)` does not receive the direct target, while `MissileWeapon.TryFire(...)` has `Weapon.target` as `IDamageable`.
- Added target velocity capture from `IDamageable.velocityVector_kps` in the `MissileWeapon.TryFire` prefix, plus a `positionAtTime(t + 1s) - positionAtTime(t)` derivative fallback converted from combat scale units to kps.
- Did not derive velocity from cross-session or stale historical positions; the fallback uses the same target object and the current TryFire time.

## Validation Results

- `dotnet build TI_Missile_Fire_Control.sln`: passed with 0 warnings and 0 errors.
- `python tools\check_layout.py`: passed.
- `python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py`: passed.
- `python -m compileall tools`: passed.
- `python tools\parse_player_log.py --require-launchlogs --require-snapshots`: passed.

Final runtime smoke on `Player.log` last written `2026-06-21 09:34:44` local time: passed.

- diagnostics bootstrap remained `patched=3`, `skipped=0`.
- `LaunchLog`: 6,701 entries, contiguous sequence range `1-6701`, no duplicates.
- `MissileWeapon.TryFire`: 748 rows.
- `SnapshotLog`: 748 entries.
- `AllocationLog`: 1,496 entries: 748 `cycle`, 748 `allocation`.
- `ammoGateBudgetShots`: 748/748 numeric snapshot/cycle evidence, total cycle budget 5,998 shots.
- Target velocity evidence: 748/748 cycles with `targetVelocityEvidenceSource=tryFireTargetDamageableVelocity` and `targetVelocityMissingReason=none`.
- Relative velocity evidence: 748/748 cycles with `relativeVelocityEvidenceSource=targetAndLauncherVelocity` and `relativeVelocityMissingReason=none`.
- PD weight fields remained explicit defaults: 748/748 cycles `pdWeightEvidenceSource=defaultModel`, `pdWeightDefaulted=True`, `pdWeightDefaultReason=pdEvidenceUnavailable`, `pdWeightMissingReason=none`.
- MissileWarfare issues: none.

Final interpretation: #18 target/relative velocity evidence is runtime-confirmed. #19 is runtime-confirmed as explicit default-model reporting; direct observed PD weapon weights remain out of scope.

## Superseded Runtime Observation

An earlier runtime smoke on `Player.log` last written `2026-06-21 09:23:17` local time validated that the new schema fields were emitted, but still reported `targetVelocityMissingReason=targetVelocityMemberUnavailable` on 745/745 cycles. That result was superseded by the decompiled-source review and TryFire-target evidence fix.

## Source Review Notes

- Source checked: `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master-source/PavonisInteractive.TerraInvicta.Ship/MissileWeapon.cs`, `Weapon.cs`, `IDamageable.cs`, `PavonisInteractive.TerraInvicta.SpaceCombat/CombatShipController.cs`, and `PavonisInteractive.TerraInvicta/TISpaceCombatProjectileState.cs`.
- Finding: vanilla missile targeting computes intercepts from `IDamageable.position`, `velocityVector`, and `accelerationVector`; the direct target is available from `Weapon.target` during `MissileWeapon.TryFire`, not from the projectile-state `Fire(...)` hook arguments.
- Change: thread TryFire target velocity evidence through the existing readiness handoff so snapshot/allocation logs can report `tryFireTargetDamageableVelocity` or `tryFireTargetPositionAtTimeDelta`.
