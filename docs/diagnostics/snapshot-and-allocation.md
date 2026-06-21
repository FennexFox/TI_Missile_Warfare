# Battle snapshot and allocation diagnostics

This document describes the current observation-first snapshot and shadow allocation diagnostics.

For historical smoke results and issue-by-issue runtime validation numbers, see [`runtime-validation-history.md`](runtime-validation-history.md).

## Current status

Current code correlates projectile-fire snapshots with live
`MissileWeapon.TryFire` prefix evidence. Issue #17 validates the source-level
semantics for a per-weapon ammo/gate budget: `TISpaceShipState.ammo[weaponData]`
plus the vanilla `TryFireCommon` / `WeaponCanFire` / cooldown / target gates is
the game-equivalent fire budget for that weapon and timing window.

The schema now calls that value `ammoGateBudgetShots`. It is not a separate
loaded/chambered source, and it is not valid without the paired module-keyed
ammo and gate evidence documented in
[`readiness-semantics.md`](../research/readiness-semantics.md).

Shadow allocation output is still diagnostics-first. It validates schema,
parser behavior, and recommendation math when required inputs are visible; it
does not apply commands.

## Runtime source

The first extractor is wired to the confirmed missile projectile hook:

```text
PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState.Fire
```

This hook is used because it has confirmed missile-only launch coverage and
exposes the launcher/carrier, missile template, launch time, origin position,
expected target position, and origin velocity.

## Toggles

Snapshot logging requires both settings:

- `EnableDiagnostics`
- `EnableSnapshotDiagnostics`

Shadow allocation diagnostics require both settings:

- `EnableDiagnostics`
- `EnableShadowAllocationDiagnostics`

Both snapshot and shadow allocation diagnostics default to `false` beyond the
base diagnostics toggle. Shadow allocation is diagnostics-only: it never applies
assignments, never issues commands, never changes fire mode, and never
suppresses or delays original game methods.

## Snapshot mapping

The mod adapter maps visible runtime objects into Core models:

- launcher/carrier -> `ShipSnapshot`
- missile template -> `MissileProfile`
- missile launch inventory state -> `MissileInventorySnapshot`
- launcher missile weapon -> `WeaponSnapshot`
- optional launcher-selected targetable state -> target `ShipSnapshot`

Weapon role mapping is conservative. The confirmed projectile-fire snapshot
marks the launcher weapon as `WeaponRole.Missile` when the template reports
`isMissileWeapon` or when the confirmed missile hook is the only available
signal.

Unknown counts are emitted as `unknown` in logs and stored as `-1` in Core
snapshot count fields.

## Target identity semantics

Launcher-selected target identity probing is conservative. The projectile-state
fire hook does not receive the live `MissileController.target` object.
`MissileWeapon` passes that target to the Unity controller immediately after the
state fire call.

The snapshot extractor checks the launcher/carrier for `combatPrimaryTarget` or
related primary-target members. Candidate target wrappers are unwrapped through
members such as `combatTargetableState`, `GetCombatantState`,
`GetTargetableState`, `ShipState`, and `WeaponCarrierState` when present.

`targetIdentitySource=launcher` means launcher/carrier primary-target or
focus-fire identity. It is not proof of the actual in-flight missile guidance
target. For projectile/controller guidance target coverage, add a separate
observation point around `MissileWeapon.target` or `MissileController.target`.

If no concrete launcher-selected identity is visible, `targetId`, `target`, and
`targetTeam` remain `unknown`, `targetIdentitySource` is `none`, and
`missing=targetIdentity` remains valid.

## SnapshotLog schema

Snapshot diagnostics use a separate marker so existing launch diagnostics remain
unchanged:

```text
[SnapshotLog] source="TISpaceCombatProjectileState.Fire(missile)" launcherId="..." launcher="..." launcherTeam="..." targetId="..." target="..." targetTeam="..." targetIdentitySource="..." expectedTargetPosition="..." targetVelocityKps="..." targetVelocityEvidenceSource="targetCombatState" targetVelocityMissingReason="none" relativeVelocityKps="..." relativeSpeedKps="..." relativeVelocityEvidenceSource="targetAndLauncherVelocity" relativeVelocityMissingReason="none" missileId="..." missile="..." weaponRole="Missile" ammoGateBudgetShots="..." ammoGateBudgetEvidenceSource="shipAmmoByWeaponData+TryFireCommonGates" ammoGateBudgetMissingReason="none" ammoEvidenceSource="shipAmmoByWeaponData" liveWeaponState="..." ammoGateWeaponCount="1" unknownAmmoGateWeaponCount="0" remainingShots="..." pdWeight="0" pdWeightEvidenceSource="defaultModel" pdWeightDefaulted="True" pdWeightDefaultReason="pdEvidenceUnavailable" pdWeightMissingReason="none" missing="targetIdentity"
```

The `missing` field records which fields were not visible from the hook rather
than treating partial snapshots as fatal. If the prefix cannot read a valid
ammo/gate budget, `ammoGateBudgetShots="unknown"` and
`missing="ammoGateBudgetShots"` are expected.

## AllocationLog schema

The observation-only shadow allocation loop builds an `AllocationRequest` from
available projectile-fire snapshot fields and runs the Core `SalvoAllocator`
when enough safe data exists to form a launcher, target list, missile profile,
and ammo/gate budget.

The sample numeric allocation values below are illustrative schema examples.
They are not validated combat recommendations unless the corresponding runtime
inputs are present and documented.

```text
[AllocationLog] recordType="cycle" cycleId="1" status="evaluated" sourceHook="TISpaceCombatProjectileState.Fire(missile)" battle="..." friendlyLaunchers="1" targetCount="1" totalAmmoGateBudgetShots="6" ammoGateBudgetEvidenceSource="shipAmmoByWeaponData+TryFireCommonGates" ammoGateBudgetMissingReason="none" ammoEvidenceSource="shipAmmoByWeaponData" liveWeaponState="..." ammoGateWeaponCount="1" unknownAmmoGateWeaponCount="0" targetVelocityKps="..." targetVelocityEvidenceSource="targetCombatState" targetVelocityMissingReason="none" relativeVelocityKps="..." relativeSpeedKps="..." relativeVelocityEvidenceSource="targetAndLauncherVelocity" relativeVelocityMissingReason="none" pdWeight="0" pdWeightEvidenceSource="defaultModel" pdWeightDefaulted="True" pdWeightDefaultReason="pdEvidenceUnavailable" pdWeightMissingReason="none" assignedShots="4" unassignedShots="2" missingInputs="pdWeightsDefaulted"
[AllocationLog] recordType="allocation" cycleId="1" targetId="..." target="..." assignedShots="4" pdScore="0" targetValue="19" saturationSize="1" killSize="4" launchWindowScore="0.72" scorePerShot="3.42" reason="kill package"
[AllocationLog] recordType="rejection" cycleId="1" targetId="..." target="..." assignedShots="0" pdScore="0" targetValue="19" saturationSize="1" killSize="4" launchWindowScore="0.12" scorePerShot="0" rejectionReason="outside estimated launch window"
```

Cycle records include battle context, source hook, cycle id, friendly launcher
count, target count, total ammo/gate budget shots, assigned shots, unassigned
shots, and missing inputs.

Allocation and rejection records include target identity, assigned shots, PD
score, target value, saturation and kill package sizes, launch-window score,
score per shot, and reason.

## Ammo/gate budget fields

Known limitations are explicit in `missingInputs` and the ammo/gate budget
fields.

- `ammoGateBudgetShots`: per-snapshot budget derived only from module-keyed
  pre-fire ammo plus valid live fire gates.
- `ammoGateBudgetEvidenceSource`: evidence source, currently
  `shipAmmoByWeaponData+TryFireCommonGates` when populated.
- `ammoGateBudgetMissingReason`: why the budget is unknown, such as
  `missing module-keyed ammo evidence`, `missing ammo/gate evidence`,
  `ammo/gate evidence not currently fireable`, or
  `missing live weapon correlation`.
- `ammoEvidenceSource`: where ammo-like evidence came from, such as
  `shipAmmoByWeaponData` or `projectileSnapshotCount`.
- `liveWeaponState`: compact live gate/cooldown state from the correlated
  `MissileWeapon.TryFire` prefix when available.
- `ammoGateWeaponCount`: count of weapons with a validated ammo/gate budget in
  this snapshot.
- `unknownAmmoGateWeaponCount`: count of weapons whose ammo/gate budget remains
  unknown for this snapshot.

The shadow path does not infer `ammoGateBudgetShots` from `remainingShots`,
post-fire ammo evidence, or capacity values.

## Other known missing inputs

`pdWeightsDefaulted` remains a limitation marker when the current snapshot does
not recover detailed target point-defense weapon weights from the runtime ship
state. The cycle also reports `pdWeightEvidenceSource`, `pdWeightDefaulted`,
`pdWeightDefaultReason`, and `pdWeightMissingReason` so a formal default model
is distinguishable from observed PD evidence and unknown PD evidence.

`targetVelocity` is reported when target velocity cannot be read from runtime
target evidence. The preferred evidence path is the live `MissileWeapon.target`
`IDamageable` observed in the `MissileWeapon.TryFire` prefix, using
`velocityVector_kps`. If that direct value is unavailable, diagnostics attempt a
same-target `positionAtTime(t + 1s) - positionAtTime(t)` derivative and convert
from combat scale units to kps. The older projectile-fire target combat-state
read remains a fallback. When available, `targetVelocityKps` is paired with a
source such as `tryFireTargetDamageableVelocity`,
`tryFireTargetPositionAtTimeDelta`, or `targetCombatState`, and
`targetVelocityMissingReason="none"`. The diagnostics derive
`relativeVelocityKps` and `relativeSpeedKps` only when both target velocity and
launcher/origin velocity are present; otherwise the relative-velocity missing
reason names the unavailable source.

`missileProfileData` is reported when the missile identity or profile cannot be
safely formed.

## Parser report

`tools/parse_player_log.py` summarizes `[AllocationLog]` rows into a compact
battle-level allocation report for before/after tuning comparisons.

The parser separates current shadow cycles, allocations, and rejections from
future controlled-apply records. Future record types such as applied decisions,
skipped decisions, and failed command applications are bucketed when they
appear, but current logs are expected to show zero controlled-apply counts.

Battle-level shot totals are taken from `recordType="cycle"` rows only. When any
cycle has an unknown value, the corresponding total remains `unknown` rather
than implying a complete battle total.

Missing-field rates are computed from shadow cycle `missingInputs` values for
allocator-critical fields:

- `ammoGateBudgetShots`
- `targetIdentity`
- `targetVelocity`
- `missileProfileData`
- `pdWeightsDefaulted`

The parser also reports target-velocity and relative-velocity coverage,
evidence source counts, and missing reason counts. PD input reporting separates
observed, defaulted, and unknown cycles, then prints the evidence source,
default reason, and missing reason breakdowns.

Parser warnings such as `all shadow cycles missing ammoGateBudgetShots`, `too
many launch-window rejects`, or `allocation report limited by missing runtime
inputs` are tuning hints from observed diagnostic fields. They are not proof of
combat outcome quality.

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
