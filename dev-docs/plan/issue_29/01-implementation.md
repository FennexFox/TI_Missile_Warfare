# Phase 01: Add PD capability evidence fields

## Goal

- Add runtime diagnostic fields that identify target PD evidence quality without changing legacy `pdWeight` semantics.

## Scope

- C# snapshot extraction and diagnostics only.
- Static target weapon-template fields visible from the current observation path.

## Non-goals

- No live command behavior.
- No allocator scoring tune.
- No claim of live target defensive readiness or geometry-aware interception.

## Affected files

- `src/MissileFireControl.Mod/Adapters/CombatSnapshotExtractor.cs`
- `src/MissileFireControl.Mod/Diagnostics/SnapshotDiagnostics.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`

## Implementation steps

- Added `pdEvidenceQuality`, `pdCapabilityEvidenceSource`, count, range, cooldown, missing-reason, and limitation fields to `ExtractedCombatSnapshot`.
- Preserved `pdWeight`, `pdWeightEvidenceSource`, `pdWeightDefaulted`, `pdWeightDefaultReason`, and `pdWeightMissingReason`.
- Classified defaulted evidence as `defaultModel`.
- Classified defense-mode templates with no capability fields as `observedPresenceOnly`.
- Classified defense-mode templates with static range/cooldown/ammo-capacity style fields as `observedTemplateCapability`.
- Emitted new fields from SnapshotLog and AllocationLog cycle/allocation/rejection/no-op records.

## Acceptance criteria

- Existing PD fallback/default fields remain emitted.
- New logs can distinguish presence-only from template capability.
- `pdWeight` remains count-style and is not silently recalibrated.

## Validation commands

- `dotnet build TI_Missile_Fire_Control.sln` - passed.
- `python tools\check_layout.py` - passed.

## Manual smoke tests

- Not run in Terra Invicta during this implementation pass. Fresh runtime logs are still needed to confirm real combat coverage.

## Rollback risks

- Low runtime risk because fields are additive diagnostics and the allocator input scalar is unchanged.

## Progress

- Completed.

## Decision log

- Static template capability is named `observedTemplateCapability`, not ready or calibrated.
- Live readiness and geometry labels are reserved for future source-backed evidence.

## Outcomes / Retrospective

- Runtime diagnostics now expose richer PD capability quality while keeping issue #28's evidence-sufficiency separation intact.
