# Phase 01: Outcome hook surface inventory

## Goal

- Identify stable Terra Invicta outcome-related method surfaces and classify
  their evidence level before implementing diagnostics.

## Scope

- Review decompiled source under `../TI_RE_Workspace`.
- Classify projectile lifecycle, point-defense/interception, ship damage, and
  destruction surfaces.
- Preserve the distinction between exact hook evidence and conservative hints.

## Non-goals

- Allocator heuristic changes.
- Live command behavior changes.
- Broad selected/fleet command authority changes.
- Claiming unique projectile kill attribution from target destruction alone.

## Affected files

- `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master-source/PavonisInteractive.TerraInvicta.SpaceCombat/MissileController.cs`
- `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master-source/PavonisInteractive.TerraInvicta.SpaceCombat/CombatShipController.cs`
- `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master-source/PavonisInteractive.TerraInvicta.SpaceCombat/CombatHabModuleController.cs`
- `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master-source/PavonisInteractive.TerraInvicta.Ship/DamageSource.cs`
- `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master-source/PavonisInteractive.TerraInvicta.Ship/Damage.cs`

## Implementation steps

- Review candidate source signatures.
- Reject broad interface patching when a concrete class method is available.
- Select the smallest diagnostics-only hook set that provides useful #47
  evidence without altering behavior.

## Acceptance criteria

- Candidate hooks are listed with event level and identity limits.
- No implementation decision depends on allocator tuning.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m compileall tools
- python tools\parse_player_log.py --require-launchlogs

## Manual smoke tests

- Runtime smoke pending: enable diagnostics and outcome diagnostics, run a
  combat, then parse the active `Player.log`.

## Rollback risks

- Discovery-only changes have no runtime rollback risk.

## Progress

- Completed source review of concrete outcome candidates.

## Decision log

- `MissileController.ApplyDamage(DamageSource)` is a point-defense /
  projectile-damage candidate for missile destruction or damage by beams and
  burst damage.
- `MissileController.Destruct(bool)` is a projectile lifecycle candidate for
  hit, timeout, lost-target, or removal outcomes, but it does not by itself
  prove the cause of target damage.
- `CombatShipController.ApplyDamage(DamageSource)` is a concrete ship damage
  candidate. When the source is `MissileController.MissileDamage` or
  `MissileController.BurstDamage`, it is stronger than later text hints but
  still must be logged as damage evidence, not automatic kill attribution.
- `CombatShipController.TriggerShipDestruction(TIGameState, TIShipWeaponTemplate)`
  is a ship destruction state candidate. It records final destruction and
  killer/weapon fields, but it does not expose a unique projectile id.

## Outcomes / Retrospective

- The first implementation slice should add diagnostics-only hooks for the
  selected concrete methods and keep their rows in a separate `[OutcomeLog]`
  evidence class.
