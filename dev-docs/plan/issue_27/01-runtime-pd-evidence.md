# Phase 01: Recover runtime target PD evidence

## Goal

- Recover observed target point-defense capability evidence from runtime combat
  state and feed it into existing snapshot/allocation diagnostics.

## Scope

- `CombatSnapshotExtractor` target extraction and PD evidence mapping.
- `ShadowAllocationDiagnostics` missing-input handling for defaulted PD.
- Read-only RE review of Terra Invicta combat weapon-template and defensive
  fire classes.

## Non-goals

- No command application, target assignment, fire-mode changes, projectile
  changes, allocator tuning, or committed real combat log fixtures.
- No attempt to model exact vanilla PD success probability in this phase.

## Affected files

- `src/MissileFireControl.Mod/Adapters/CombatSnapshotExtractor.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`

## Implementation steps

- Preserve the raw target object before converting it to `ShipSnapshot`.
- Read target weapon templates from `allWeaponTemplates` or equivalent template
  and module-list members.
- Normalize module entries through `moduleTemplate.ref_weapon` where needed.
- Treat visible `defenseMode=True` weapon templates as observed PD capability.
- Populate target PD-only `WeaponSnapshot` entries with `PointDefenseWeight=1`
  and `ThreatWeight=0`.
- Keep `defaultModel` and explicit missing reasons when target/template/member
  evidence is unavailable.
- Omit `pdWeightsDefaulted` from allocation missing inputs when observed PD
  evidence is available.

## Acceptance criteria

- Observed target weapon-template evidence emits
  `pdWeightEvidenceSource=observedTargetWeaponTemplates`.
- Default model evidence remains explicit when target PD evidence is
  unavailable.
- The shadow allocator receives observed PD weight only through existing Core
  PD score paths.
- No gameplay behavior paths are changed.

## Validation commands

- `dotnet build TI_Missile_Fire_Control.sln`

## Manual smoke tests

- Run tactical combat against a target with likely PD.
- Confirm `SnapshotLog` and `AllocationLog` show either observed PD evidence or
  a precise fallback missing reason.
- Confirm no live command behavior changed.

## Rollback risks

- Revert the extractor PD helper path and the conditional missing-input change.
- Parser/fitting behavior remains compatible with default-model logs.

## Progress

- Completed source review and implementation.

## Decision log

- `TISpaceShipState.allWeaponTemplates` and equivalent module/template lists are
  used as the first runtime evidence source.
- `TIShipWeaponTemplate.defenseMode` is the conservative observed capability
  flag.
- The scalar `pdWeight` is a count-style signal. It deliberately does not claim
  cooldown, ammo, damage, arc, or exact vanilla interception probability.

## Outcomes / Retrospective

- Runtime diagnostics can now distinguish observed target weapon-template PD
  evidence from defaulted PD evidence when the target template data is visible.
- `dotnet build TI_Missile_Fire_Control.sln` passed after implementation.
- Fresh runtime smoke is still required before #6 readiness can be upgraded.
