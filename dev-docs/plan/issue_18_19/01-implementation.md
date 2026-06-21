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
- Added explicit PD default model fields to snapshot and allocation logs.
- Added parser counters and summary output for the new evidence fields.
- Updated diagnostics schema documentation.

## Decision Log

- Kept `pdWeightsDefaulted` in `missingInputs` as a limitation marker because observed PD weights are still not recovered.
- Used the hook-provided origin velocity as launcher velocity evidence for shadow allocation diagnostics when present.
- Did not derive velocity from previous positions because no stable same-battle/tick history exists in the current snapshot path.

## Validation Results

- `dotnet build TI_Missile_Fire_Control.sln`: passed with 0 warnings and 0 errors.
- `python tools\check_layout.py`: passed.
- `python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py`: passed.
- `python -m compileall tools`: passed.
- `python tools\parse_player_log.py --require-launchlogs --require-snapshots`: passed against the currently deployed pre-change `Player.log`.
- Fresh deployed runtime smoke on `Player.log` last written `2026-06-21 09:23:17` local time: passed.

Fresh runtime smoke results:

- diagnostics bootstrap remained `patched=3`, `skipped=0`.
- `LaunchLog`: 4,363 entries, contiguous sequence range `1-4363`, no duplicates.
- `SnapshotLog`: 745 entries.
- `AllocationLog`: 1,490 entries: 745 `cycle`, 745 `allocation`.
- `ammoGateBudgetShots`: 745/745 numeric snapshot/cycle evidence, total cycle budget 5,985 shots.
- Target velocity fields emitted on snapshot and allocation logs, but target velocity evidence remains missing on 745/745 cycles with `targetVelocityMissingReason=targetVelocityMemberUnavailable`.
- Relative velocity fields emitted on snapshot and allocation logs, but relative velocity remains missing on 745/745 cycles because target velocity is unavailable.
- PD weight fields emitted on snapshot and allocation logs: 745/745 cycles `pdWeightEvidenceSource=defaultModel`, `pdWeightDefaulted=True`, `pdWeightDefaultReason=pdEvidenceUnavailable`, `pdWeightMissingReason=none`.
- MissileWarfare issues: none.

Interpretation: #19 default formalization is runtime-confirmed. #18 now reports a precise, actionable missing reason, but direct target velocity is still not recovered from the launcher-selected target object.
