# Battle snapshot and allocation diagnostics

This document describes the current observation-only snapshot and shadow allocation diagnostics.

For historical smoke results and issue-by-issue runtime validation numbers, see [`runtime-validation-history.md`](runtime-validation-history.md).

## Current status

Current logs can correlate projectile-fire snapshots with live `MissileWeapon.TryFire` ammo and gate/cooldown evidence, but they do not yet validate an allocator-safe shot budget.

Do not treat `readyShots=unknown` as proof that a separate ready-state model exists. The open question is whether `TISpaceShipState.ammo[weaponData]` plus known gates is the game-equivalent shot budget, whether a distinct runtime source exists, or whether the allocator should avoid a numeric fleet-level budget. That decision is tracked in [`readiness-semantics.md`](../research/readiness-semantics.md).

Shadow allocation output is currently useful for schema validation, parser validation, and missing-input accounting. It is not yet a validated combat recommendation path.

## Runtime source

The first extractor is wired to the confirmed missile projectile hook:

```text
PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState.Fire
```

This hook is used because it has confirmed missile-only launch coverage and exposes the launcher/carrier, missile template, launch time, origin position, expected target position, and origin velocity.

## Toggles

Snapshot logging requires both settings:

- `EnableDiagnostics`
- `EnableSnapshotDiagnostics`

Shadow allocation diagnostics require both settings:

- `EnableDiagnostics`
- `EnableShadowAllocationDiagnostics`

Both snapshot and shadow allocation diagnostics default to `false` beyond the base diagnostics toggle. Shadow allocation is diagnostics-only: it never applies assignments, never issues commands, never changes fire mode, and never suppresses or delays original game methods.

## Snapshot mapping

The mod adapter maps visible runtime objects into Core models:

- launcher/carrier -> `ShipSnapshot`
- missile template -> `MissileProfile`
- missile launch inventory state -> `MissileInventorySnapshot`
- launcher missile weapon -> `WeaponSnapshot`
- optional launcher-selected targetable state -> target `ShipSnapshot`

Weapon role mapping is conservative. The confirmed projectile-fire snapshot marks the launcher weapon as `WeaponRole.Missile` when the template reports `isMissileWeapon` or when the confirmed missile hook is the only available signal.

Unknown counts are emitted as `unknown` in logs and stored as `-1` in Core snapshot count fields.

## Target identity semantics

Launcher-selected target identity probing is conservative. The projectile-state fire hook does not receive the live `MissileController.target` object. `MissileWeapon` passes that target to the Unity controller immediately after the state fire call.

The snapshot extractor checks the launcher/carrier for `combatPrimaryTarget` or related primary-target members. Candidate target wrappers are unwrapped through members such as `combatTargetableState`, `GetCombatantState`, `GetTargetableState`, `ShipState`, and `WeaponCarrierState` when present.

`targetIdentitySource=launcher` means launcher/carrier primary-target or focus-fire identity. It is not proof of the actual in-flight missile guidance target. For projectile/controller guidance target coverage, add a separate observation point around `MissileWeapon.target` or `MissileController.target`.

If no concrete launcher-selected identity is visible, `targetId`, `target`, and `targetTeam` remain `unknown`, `targetIdentitySource` is `none`, and `missing=targetIdentity` remains valid.

## SnapshotLog schema

Snapshot diagnostics use a separate marker so existing launch diagnostics remain unchanged:

```text
[SnapshotLog] source="TISpaceCombatProjectileState.Fire(missile)" launcherId="..." launcher="..." launcherTeam="..." targetId="..." target="..." targetTeam="..." targetIdentitySource="..." expectedTargetPosition="..." missileId="..." missile="..." weaponRole="Missile" readyShots="unknown" readyShotEvidenceSource="unknown" readinessMissingReason="ammo-and-gate-only live weapon evidence" ammoEvidenceSource="shipAmmoByWeaponData" liveWeaponState="..." readyWeaponCount="unknown" unknownReadinessWeaponCount="1" remainingShots="..." missing="targetIdentity,readyShots"
```

The `missing` field records which fields were not visible from the hook rather than treating partial snapshots as fatal.

## AllocationLog schema

Issue #4 adds an observation-only shadow allocation loop. The loop builds an `AllocationRequest` from available projectile-fire snapshot fields and runs the existing Core `SalvoAllocator` only when enough safe data exists to form a launcher, target list, and missile profile.

The sample numeric allocation values below are illustrative schema examples. They are not validated combat recommendations unless the corresponding runtime inputs are present and documented.

```text
[AllocationLog] recordType="cycle" cycleId="1" status="evaluated" sourceHook="TISpaceCombatProjectileState.Fire(missile)" battle="..." friendlyLaunchers="1" targetCount="1" totalReadyShots="unknown" readyShotEvidenceSource="unknown" readinessMissingReason="ammo-and-gate-only live weapon evidence" ammoEvidenceSource="shipAmmoByWeaponData" liveWeaponState="..." readyWeaponCount="unknown" unknownReadinessWeaponCount="1" assignedShots="0" unassignedShots="unknown" missingInputs="readyShots,targetVelocity,pdWeightsDefaulted"
[AllocationLog] recordType="allocation" cycleId="1" targetId="..." target="..." assignedShots="4" pdScore="0" targetValue="19" saturationSize="1" killSize="4" launchWindowScore="0.72" scorePerShot="3.42" reason="kill package"
[AllocationLog] recordType="rejection" cycleId="1" targetId="..." target="..." assignedShots="0" pdScore="0" targetValue="19" saturationSize="1" killSize="4" launchWindowScore="0.12" scorePerShot="0" rejectionReason="outside estimated launch window"
```

Cycle records include battle context, source hook, cycle id, friendly launcher count, target count, total ready shots, assigned shots, unassigned shots, and missing inputs.

Allocation and rejection records include target identity, assigned shots, PD score, target value, saturation and kill package sizes, launch-window score, score per shot, and reason.

## Readiness evidence fields

Known limitations are explicit in `missingInputs` and the readiness evidence fields. `readyShots` remains unknown until the project validates one of these designs:

- `ammo[weaponData]` plus known gates as the game-equivalent shot budget;
- a distinct allocator-safe source;
- a controlled-allocation design that does not need a numeric fleet-level budget.

The shadow path does not infer readiness from `remainingShots`, pre/post ammo evidence, or gate/cooldown state.

Readiness-related fields:

- `readyShotEvidenceSource`: `unknown` until allocator-safe shot-budget semantics are documented.
- `readinessMissingReason`: why `readyShots` is still unknown, such as `ammo-and-gate-only live weapon evidence`, `ammo-only projectile snapshot evidence`, or `missing live weapon correlation`.
- `ammoEvidenceSource`: where ammo-like evidence came from, such as `shipAmmoByWeaponData` or `projectileSnapshotCount`.
- `liveWeaponState`: compact live gate/cooldown state from the correlated `MissileWeapon.TryFire` prefix when available.
- `readyWeaponCount`: unknown until allocator-safe fireable-shot semantics are proven.
- `unknownReadinessWeaponCount`: count of weapons whose readiness remains unknown for this snapshot.

## Other known missing inputs

`pdWeightsDefaulted` is reported because the current snapshot does not recover detailed target point-defense weapon weights from the runtime ship state.

`targetVelocity` is reported when the target is unavailable or the snapshot only has the default zero vector.

`missileProfileData` is reported when the missile identity or profile cannot be safely formed.

## Parser report

`tools/parse_player_log.py` summarizes `[AllocationLog]` rows into a compact battle-level allocation report for before/after tuning comparisons.

The parser separates current shadow cycles, allocations, and rejections from future controlled-apply records. Future record types such as applied decisions, skipped decisions, and failed command applications are bucketed when they appear, but current logs are expected to show zero controlled-apply counts.

Battle-level shot totals are taken from `recordType="cycle"` rows only. When any cycle has an unknown value, the corresponding total remains `unknown` rather than implying a complete battle total.

Missing-field rates are computed from shadow cycle `missingInputs` values for allocator-critical fields:

- `readyShots`
- `targetIdentity`
- `targetVelocity`
- `missileProfileData`
- `pdWeightsDefaulted`

Parser warnings such as `all shadow cycles missing readyShots`, `too many launch-window rejects`, or `allocation report limited by missing runtime inputs` are tuning hints from observed diagnostic fields. They are not proof of combat outcome quality.

Issue #15 adds readiness evidence histograms to the parser report. The parser separates numeric ready-shot cycles, unknown ready-shot cycles, ammo-only readiness evidence cycles, and cycles blocked by missing readiness evidence. Older logs that lack `readyShotEvidenceSource`, `readinessMissingReason`, or `ammoEvidenceSource` continue to parse.

## Validation commands

Static validation:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py
python tools\parse_player_log.py --require-launchlogs
```

Runtime validation after deploying and enabling battle snapshot diagnostics:

```powershell
python tools\parse_player_log.py --require-launchlogs --require-snapshots
```

Expected runtime result:

- diagnostics bootstrap remains `patched=3`, `skipped=0`;
- LaunchLog entries remain present and contiguous;
- SnapshotLog entries are present;
- MissileWarfare issues remain empty.
