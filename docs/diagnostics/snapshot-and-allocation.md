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

Shadow allocation output remains diagnostics-first by default. It validates
schema, parser behavior, and recommendation math when required inputs are
visible. Issue #37 added one explicitly triggered, default-off exception for a
single selected player missile ship. Issue #38 expands that exception to a
small explicitly selected player missile group while preserving the same
default-off gate, selected-command scope, vanilla salvo-target command path,
and bounded command caps.

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

Controlled dry-run diagnostics require all three settings plus an explicit UMM
panel trigger:

- `EnableDiagnostics`
- `EnableShadowAllocationDiagnostics`
- `EnableControlledDryRunDiagnostics`

The command-apply boundary has a separate default-off setting:

- `AllowCommandApply`

Recommendation-only mode is a second command-apply interlock:

- `EnableRecommendationOnlyMode`

Both snapshot and shadow allocation diagnostics default to `false` beyond the
base diagnostics toggle. Controlled dry-run diagnostics also default to
`false`. `AllowCommandApply` also defaults to `false`.
`EnableRecommendationOnlyMode` defaults to `true`.

When `AllowCommandApply=False`, the #36 hard stop remains active and controlled
experiments are diagnostics-only. When `AllowCommandApply=True` but
`EnableRecommendationOnlyMode=True`, the gate still blocks with
`blockedByRecommendationOnlyMode`. Live apply requires both
`AllowCommandApply=True` and `EnableRecommendationOnlyMode=False`; then Issue
#38 can perform at most one live command attempt per selected ship and at most
three live command attempts total for the next explicitly armed selected-group
controlled experiment. The reviewed command path is
`SelectSalvoTargetCommand.OnCommandExecute(TISpaceShipState,
CombatTargetableState)`, which queues the vanilla primary-target and salvo mode
actions through the game player-action runner. The mod does not directly mutate
ammo, cooldowns, projectile physics, or AI behavior.

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
fire hook does not receive the live `MissileController.target` object, but the
paired `MissileWeapon.TryFire` prefix can observe the live weapon `target`
before the projectile fire hook runs on the same thread.

The snapshot extractor first checks the launcher/carrier for
`combatPrimaryTarget` or related primary-target members. If no launcher priority
target is visible, it falls back to the live `MissileWeapon.TryFire` target from
the same-thread readiness handoff. Candidate target wrappers are unwrapped
through members such as `combatTargetableState`, `GetCombatantState`,
`GetTargetableState`, `ShipState`, and `WeaponCarrierState` when present.

`targetIdentitySource=launcher` means launcher/carrier primary-target or
focus-fire identity. `targetIdentitySource=tryFireTarget` means the identity was
derived from the live `MissileWeapon.target` observed immediately before the
projectile fire hook.

If no concrete launcher-selected identity is visible, `targetId`, `target`, and
`targetTeam` remain `unknown`, `targetIdentitySource` is `none`, and
`missing=targetIdentity` remains valid.

This missing field means neither a launcher-selected priority target nor a
same-thread `MissileWeapon.TryFire` target could be normalized into a concrete
combat target identity. It does not prove vanilla combat had no target.
Decompiled source review shows `SelectSalvoTargetCommand` sets
`combatPrimaryTarget` through `SetCombatPrimaryTargetAction`, while
`MissileWeapon.TryFire` still fires through a live `base.target` object. Fighting
without a player-set priority target is therefore compatible with
`targetIdentitySource=tryFireTarget`; it should not require enabling combat AI
control just to expose allocator target identity.

## SnapshotLog schema

Snapshot diagnostics use a separate marker so existing launch diagnostics remain
unchanged:

```text
[SnapshotLog] source="TISpaceCombatProjectileState.Fire(missile)" launcherId="..." launcher="..." launcherTeam="..." targetId="..." target="..." targetTeam="..." targetIdentitySource="..." expectedTargetPosition="..." targetVelocityKps="..." targetVelocityEvidenceSource="targetCombatState" targetVelocityMissingReason="none" relativeVelocityKps="..." relativeSpeedKps="..." relativeVelocityEvidenceSource="targetAndLauncherVelocity" relativeVelocityMissingReason="none" missileId="..." missile="..." weaponRole="Missile" ammoGateBudgetShots="..." ammoGateBudgetEvidenceSource="shipAmmoByWeaponData+TryFireCommonGates" ammoGateBudgetMissingReason="none" ammoEvidenceSource="shipAmmoByWeaponData" liveWeaponState="..." ammoGateWeaponCount="1" unknownAmmoGateWeaponCount="0" remainingShots="..." pdWeight="0" pdWeightEvidenceSource="defaultModel" pdWeightDefaulted="True" pdWeightDefaultReason="pdEvidenceUnavailable" pdWeightMissingReason="none" pdEvidenceQuality="defaultModel" pdCapabilityEvidenceSource="none" pdCapabilityWeaponCount="0" pdCapabilityRangeKm="0" pdCapabilityCooldownSeconds="0" pdCapabilityObservedFields="none" pdCapabilityMissingReason="none" pdCapabilityLimitations="targetPdEvidenceUnavailable" missing="targetIdentity"
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
[AllocationLog] recordType="noOp" cycleId="2" targetId="..." target="..." assignedShots="0" pdScore="unknown" targetValue="unknown" saturationSize="unknown" killSize="unknown" launchWindowScore="unknown" scorePerShot="unknown" noOpReason="no ammo/gate budget shots"
```

Cycle records include battle context, source hook, cycle id, friendly launcher
count, target count, total ammo/gate budget shots, assigned shots, unassigned
shots, and missing inputs.

Allocation, rejection, and no-op records include target identity when
available, assigned shots, PD score, target value, saturation and kill package
sizes, launch-window score, score per shot, and reason fields. No-op records
use `noOpReason` when the shadow cycle cannot or should not recommend an
allocation, such as missing required inputs or zero ammo/gate budget.

When controlled dry-run diagnostics are enabled and explicitly triggered from
the UMM panel, the next shadow allocation cycle is tagged with a local
`experimentId` and emits additional diagnostics-only rows:

```text
[AllocationLog] recordType="dryRunExperiment" experimentId="dryrun-..." cycleId="1" requestedUtc="..." sourceHook="TISpaceCombatProjectileState.Fire(missile)" status="evaluated" selectedScopeVisible="True" selectedScopeSource="SpaceCombatCanvasController.selectedFriendlyShipState" selectedScopeMissingReason="none" selectedShipCount="1" selectedShipIds="..." selectedShipNames="..." selectedShipTeams="..." commandScopeSource="SpaceCombatCanvasController.selectedFriendlyShipState" commandScopeMissingReason="none" commandScopeShipCount="1" commandScopeShipIds="..." targetId="..." target="..." missingInputs="none" appliedCommands="0"
[AllocationLog] recordType="dryRunIntent" experimentId="dryrun-..." cycleId="1" decisionType="allocation" commandIntent="salvoTargetRecommendationDryRun" commandGranularity="shipAllSalvoCapableWeapons" launcherId="..." launcher="..." targetId="..." target="..." intendedShots="4" reason="kill package" appliedCommands="0"
[AllocationLog] recordType="dryRunCommandCandidate" experimentId="dryrun-..." cycleId="1" candidateId="cycle-1-allocation-1" classification="eligible" reason="none" scopeViolation="False" candidateSource="allocatorAllocation" commandIntent="salvoTargetRecommendationDryRun" commandGranularity="shipAllSalvoCapableWeapons" commandScopeSource="SpaceCombatCanvasController.selectedFriendlyShipState" commandScopeMissingReason="none" commandScopeShipCount="1" launcherId="..." launcher="..." launcherTeam="..." allocatorLauncherId="..." allocatorLauncher="..." allocatorLauncherTeam="..." weaponId="..." missileProfileId="..." targetId="..." target="..." targetTeam="..." assignedShots="4" ammoGateBudgetShots="8" appliedCommands="0"
[AllocationLog] recordType="dryRunApplyGate" experimentId="dryrun-..." cycleId="1" candidateId="cycle-1-allocation-1" gateName="controlledCommandApplyGate" gateResult="blocked" blockReason="blockedBySafetyToggle" controlledExperimentMode="True" allowCommandApply="False" recommendationOnlyMode="True" candidateSource="allocatorAllocation" commandIntent="salvoTargetRecommendationDryRun" commandGranularity="shipAllSalvoCapableWeapons" launcherId="..." launcher="..." launcherTeam="..." allocatorLauncherId="..." allocatorLauncher="..." allocatorLauncherTeam="..." weaponId="..." missileProfileId="..." targetId="..." target="..." targetTeam="..." assignedShots="4" ammoGateBudgetShots="8" preStateVisible="candidateIdentity" postState="notApplied" appliedCommands="0"
[AllocationLog] recordType="dryRunResult" experimentId="dryrun-..." cycleId="1" intendedCommands="1" skippedCommands="0" appliedCommands="0" failedCommands="0" safetyGateBlockedCommands="1" result="dryRunOnly" resultReason="blockedBySafetyToggle"
```

The selected-scope probe is intentionally narrow. It looks for the verified
tactical command-panel single selected ship and group selected ship members
(`selectedFriendlyShipState`, `selectedFriendlyShip`, and
`groupSelectedFriendlyShips`). If those members are unavailable or empty, the
dry-run experiment row reports `selectedShipCount="0"` with an explicit
`selectedScopeMissingReason` instead of falling back to the broad left-hand
player-side combatant list.

`dryRunIntent` rows describe allocator-motivated command intent.
`dryRunCommandCandidate` rows classify the diagnostics-only command candidate as
`eligible`, `wouldSkip`, or `wouldFail` under the resolved player-controlled
command scope. They include command scope source, missing reason, scope
violation flag, selected command launcher, allocator snapshot launcher,
weapon/module, target, assigned shot, candidate source, and ammo/gate budget
evidence. `launcherId` / `launcher` / `launcherTeam` name the selected command
ship; `allocatorLauncherId` / `allocatorLauncher` / `allocatorLauncherTeam`
name the ship that produced the current projectile-fire allocation cycle.
`targetTeam` records the resolved target side used by the live-apply safety
gate. The rows do not call
`SelectSalvoTargetCommand`,
`FleetSelectSalvoTargetCommand`, `SetCombatPrimaryTargetAction`,
`SetWeaponModeAction`, or equivalent live command APIs. `dryRunResult` rows must
report `appliedCommands="0"` for Issues #34 through #36.

Issue #43.1 adds a separate fleet-wide dry-run report trigger. It is not the
controlled dry-run trigger, does not broaden selected command scope, and does
not emit `appliedDecision`, `skippedDecision`, or `failedCommand` rows. Every
fleet-wide row carries `scopeMode="fleetWideReportOnly"` and
`appliedCommands="0"`.

Fleet-wide report rows use active player-side combatants only as an eligibility
source and visible hostile combat ships only as a target universe. They report
source, confidence, missing-reason, launcher exclusion, visible-target, command
candidate, diagnostic cap would-block, and missing allocator-evidence fields:

```text
[AllocationLog] recordType="fleetWideDryRunExperiment" scopeMode="fleetWideReportOnly" experimentId="fleetwide-dryrun-..." cycleId="1" fleetEligibilitySource="GameControl.spaceCombat.leftHandCombatants" fleetEligibilityConfidence="activePlayerSideCombatants" fleetEligibilityMissingReason="none" visibleTargetSource="GameControl.spaceCombat.activeShips" visibleTargetConfidence="visibleCombatants" visibleTargetMissingReason="none" eligibleLaunchers="2" excludedLaunchers="1" visibleHostileTargets="2" candidateRows="4" emittedCandidateRows="4" eligibleCandidateRows="1" capWouldBlockCandidates="1" missingAllocatorEvidenceCandidates="2" appliedCommands="0"
[AllocationLog] recordType="fleetWideLauncher" scopeMode="fleetWideReportOnly" experimentId="fleetwide-dryrun-..." cycleId="1" classification="eligible" reason="none" fleetEligibilitySource="..." fleetEligibilityConfidence="..." launcherId="..." launcher="..." launcherTeam="..." playerControlEvidence="True" commandAuthorityKnown="True" canPerformCommands="True" missileReadinessKnown="True" canFireMissiles="True" appliedCommands="0"
[AllocationLog] recordType="fleetWideTarget" scopeMode="fleetWideReportOnly" experimentId="fleetwide-dryrun-..." cycleId="1" classification="visibleHostile" reason="none" targetId="..." target="..." targetTeam="..." visibleTargetSource="..." visibleTargetConfidence="..." appliedCommands="0"
[AllocationLog] recordType="fleetWideCommandCandidate" scopeMode="fleetWideReportOnly" experimentId="fleetwide-dryrun-..." cycleId="1" classification="wouldSkip" reason="missingAllocatorSnapshotEvidence" candidateSource="visibleTargetOnlyMissingAllocatorEvidence" commandIntent="fleetWideSalvoTargetReportOnly" launcherId="..." targetId="..." allocatorEvidence="missingAllocatorSnapshotEvidence" fleetReportOnlyPerTargetCapWouldBlock="False" appliedCommands="0"
[AllocationLog] recordType="fleetWideCapState" scopeMode="fleetWideReportOnly" experimentId="fleetwide-dryrun-..." cycleId="1" candidateRows="4" eligibleCandidateRows="1" capWouldBlockCandidates="1" fleetReportOnlyGlobalCommandCap="12" fleetReportOnlyPerShipCommandCap="3" fleetReportOnlyPerTargetCommandCap="3" fleetReportOnlyPerTriggerCommandCap="12" appliedCommands="0"
[AllocationLog] recordType="fleetWideResult" scopeMode="fleetWideReportOnly" experimentId="fleetwide-dryrun-..." cycleId="1" candidateRows="4" eligibleCandidateRows="1" capWouldBlockCandidates="1" missingEvidenceCandidates="2" result="reportOnly" resultReason="fleetWideReportOnly" appliedCommands="0"
```

Visible hostile targets that are not backed by the current allocator/snapshot
cycle are reported as candidates with missing allocator evidence, not as
allocator-approved recommendations. The fleet report-only caps are diagnostics
for would-block state only and do not affect the existing selected-group live
caps.

Issue #43.2 adds a separate fleet-wide live-apply probe trigger, but the current
implementation intentionally keeps the RE gate blocked. Decompiled-source review
shows the vanilla salvo command path accepts explicit launcher and target runtime
objects through `SelectSalvoTargetCommand.OnCommandExecute`, but the command also
mutates combat primary target, salvo fire mode, and UI global targeting state.
Until a real runtime smoke proves non-selected fleet-wide invocation is safe and
correlatable, the #43.2 path emits blocker diagnostics only and must not call the
command API.

The #43.2 blocked rows use `scopeMode="fleetWideLiveReBlocked"` and always keep
`appliedCommands="0"`. They are distinct from #43.1 `fleetWideReportOnly` rows
and from selected-scope `controlled-live` rows:

```text
[AllocationLog] recordType="fleetWideLiveCommandPathStatus" scopeMode="fleetWideLiveReBlocked" experimentId="fleetwide-live-..." cycleId="1" fleetWideLiveCommandPathStatus="blocked" reGateStatus="blocked" blockReason="nonSelectedFleetWideRuntimeSmokeMissing" commandPath="SelectSalvoTargetCommand.OnCommandExecute" underlyingCommandApi="explicitLauncherAndTargetObjects" uiSelectionRequiredForExecute="False" nonSelectedCommandPathProven="False" knownStateMutations="combatPrimaryTarget,salvoFireMode,uiGlobalTargetingModeShutdown" runMode="blocked" appliedCommands="0"
[AllocationLog] recordType="fleetWideLiveApplyDecision" scopeMode="fleetWideLiveReBlocked" experimentId="fleetwide-live-..." cycleId="1" candidateId="cycle-1-fleetwide-live-1" commandResultId="none" decision="blocked" result="blocked" reason="reGateBlockedUnprovenNonSelectedCommandPath" candidateSource="currentAllocatorSnapshot" commandIntent="fleetWideSalvoTargetLiveApply" launcherId="..." targetId="..." allocatorEvidence="currentAllocatorSnapshot" controlledCommandCorrelation="none" appliedCommands="0" failedCommands="0"
[AllocationLog] recordType="fleetWideLiveResult" scopeMode="fleetWideLiveReBlocked" experimentId="fleetwide-live-..." cycleId="1" candidateRows="4" emittedDecisionRows="4" allocatorEvidenceCandidates="1" capBlockedCandidates="1" missingEvidenceCandidates="3" reBlockedCandidates="1" result="blocked" resultReason="reGateBlockedUnprovenNonSelectedCommandPath" runMode="blocked" appliedCommands="0" failedCommands="0"
```

These rows are useful #43.2 evidence because they make the failed live attempt
explicit and parser-visible. They are not `fleet-wide-controlled` evidence and
must not be used as direct controlled command spend. A later command-authority or
runtime-smoke issue must prove non-selected command invocation safety before this
probe can become bounded live apply.

The first #43.2b behavior-changing rung is the fleet-wide command-authority
probe. It is still default-off and explicitly triggered, but unlike the
RE-blocked probe it may call the vanilla command path exactly once when all
safety gates pass. It requires `AllowCommandApply=True`,
`EnableRecommendationOnlyMode=False`, a distinct command-authority setting, and a
visible non-selected allocator-evidence-backed launcher-target candidate. It is
capped at one command per trigger, one command per ship, and one command per
target.

Command-authority rows use `scopeMode="fleetWideCommandAuthorityProbe"` and
`runMode="fleet-wide-command-authority-probe"`:

```text
[AllocationLog] recordType="fleetWideCommandAuthorityCandidate" scopeMode="fleetWideCommandAuthorityProbe" runMode="fleet-wide-command-authority-probe" experimentId="fleetwide-authority-..." cycleId="1" candidateId="cycle-1-fleetwide-authority-1" commandResultId="fleetwide-authority-...:cycle-1-fleetwide-authority-1" classification="eligible" candidateSource="currentAllocatorSnapshot" launcherSelectionRelation="nonSelected" commandIntent="fleetWideCommandAuthorityProbe" commandPath="SelectSalvoTargetCommand.OnCommandExecute" launcherId="..." allocatorLauncherId="..." targetId="..." assignedShots="4" globalCap="1" perTriggerCap="1" perShipCap="1" perTargetCap="1" appliedCommands="0"
[AllocationLog] recordType="fleetWideCommandAuthorityPreState" scopeMode="fleetWideCommandAuthorityProbe" runMode="fleet-wide-command-authority-probe" experimentId="fleetwide-authority-..." cycleId="1" candidateId="cycle-1-fleetwide-authority-1" commandResultId="..." launcherSelectionRelation="nonSelected" launcherPrimaryTargetId="..." launcherWeaponModeSummary="..." uiGlobalTargetingMode="..." canPerformCommands="True" canFireMissiles="True" appliedCommands="0"
[AllocationLog] recordType="fleetWideCommandAuthorityResult" scopeMode="fleetWideCommandAuthorityProbe" runMode="fleet-wide-command-authority-probe" experimentId="fleetwide-authority-..." cycleId="1" candidateId="cycle-1-fleetwide-authority-1" commandResultId="..." result="applied" reason="none" exceptionType="none" launcherSelectionRelation="nonSelected" preStateVisible="runtimeObjects" postState="commandInvoked" appliedCommands="1" failedCommands="0" controlledCommandCorrelation="pendingRuntimeContext"
[AllocationLog] recordType="fleetWideCommandAuthorityPostState" scopeMode="fleetWideCommandAuthorityProbe" runMode="fleet-wide-command-authority-probe" experimentId="fleetwide-authority-..." cycleId="1" candidateId="cycle-1-fleetwide-authority-1" commandResultId="..." launcherPrimaryTargetId="..." launcherWeaponModeSummary="..." uiGlobalTargetingMode="..." canPerformCommands="True" canFireMissiles="True" appliedCommands="0"
```

The probe fails closed when selected scope is unavailable, when the allocator
candidate is selected rather than non-selected, or when allocator/hostile-target
evidence is missing. A clean runtime smoke for this rung proves command
authority only for the single non-selected command; it is not yet broad bounded
fleet-wide live apply.

Issue #36 routes only `eligible` candidates to a named
`controlledCommandApplyGate` boundary. With the default `AllowCommandApply=False`
setting, the gate emits `recordType="dryRunApplyGate"` with
`gateResult="blocked"`, `blockReason="blockedBySafetyToggle"`,
`postState="notApplied"`, and `appliedCommands="0"`. This is still
diagnostics-only; it records the hard stop before any live command API exists in
the mod. If runtime logs do not naturally produce an eligible candidate, the
synthetic `tools/fixtures/apply_gate_hard_stop.txt` fixture exercises the
gate-reachable blocked path.

With `AllowCommandApply=True` and `EnableRecommendationOnlyMode=True`, the same
gate emits `blockReason="blockedByRecommendationOnlyMode"` and
`recommendationOnlyMode="True"`. The synthetic
`tools/fixtures/recommendation_only_apply_gate.txt` fixture exercises this
explicit recommendation-only interlock.

Issue #37 changes only the gate-allowed case. With `AllowCommandApply=True` and
`EnableRecommendationOnlyMode=False`, an eligible candidate from exactly one
selected command-panel ship can emit `gateResult="allowed"` and then one result
row:

```text
[AllocationLog] recordType="appliedDecision" experimentId="dryrun-..." cycleId="1" candidateId="cycle-1-allocation-1" commandIntent="salvoTargetRecommendationLiveApply" commandGranularity="shipAllSalvoCapableWeapons" commandPath="SelectSalvoTargetCommand.OnCommandExecute" candidateSource="allocatorAllocation" result="applied" reason="none" exceptionType="none" commandScopeSource="SpaceCombatCanvasController.selectedFriendlyShipState" commandScopeMissingReason="none" commandScopeShipCount="1" launcherId="..." launcher="..." launcherTeam="..." allocatorLauncherId="..." allocatorLauncher="..." allocatorLauncherTeam="..." weaponId="..." missileProfileId="..." targetId="..." target="..." targetTeam="..." assignedShots="4" ammoGateBudgetShots="8" preStateVisible="runtimeObjects" postState="commandInvoked" appliedCommands="1" failedCommands="0"
```

If live preconditions fail after the gate, the row uses
`recordType="skippedDecision"` or `recordType="failedCommand"` with a concrete
`reason`, `appliedCommands="0"`, and `postState="notApplied"`. Each controlled
experiment consumes at most one live attempt per selected ship and at most three
live attempts per trigger; additional eligible candidates for an already
attempted selected ship or a capped trigger are skipped with
`reason="perShipCommandCapReached"` or
`reason="controlledGroupTriggerCapReached"`.

For #38, a live attempt additionally requires a selected command-panel scope of
one to three ships. The active-player launcher fallback remains useful
diagnostics, but it is not eligible for live apply. The selected ship runtime
object is kept through the command scope and re-checked for
`CanPerformShipCommands()`, `AnyOffensiveMissileWeaponCanFire()`, player-faction
ownership, and non-AI control before the command is invoked. For groups larger
than one, the allocator snapshot launcher must be one of the selected group
members so every candidate and result row is attributable to exactly one
selected ship. Broader fleet-wide controlled application remains future #43
scope.

Selected groups above three ships, mixed-team groups, non-player/AI ships,
unknown player-control evidence, unknown command readiness, same-team targets,
and allocator launchers outside the selected group skip or fail closed with an
explicit reason. Each selected ship can consume at most one post-gate live
command attempt per trigger, and each trigger can consume at most three
post-gate attempts. Controlled result rows include `selectedGroupMaxShips`,
`commandTriggerCap`, `launcherId`, `allocatorLauncherId`, `missilesAssigned`,
and `missilesSpent`. `missilesSpent` remains `unknown` until a runtime row can
directly prove spend evidence for that command result.

If the current allocation cycle was emitted by a different ship, the controlled
experiment can command the exactly-one selected ship only when the allocator
cycle was produced by the selected ship's team and the resolved target is on a
different concrete team. Enemy allocator cycles and friendly-target cycles are
classified as `wouldSkip` with `allocatorLauncherOutsideSelectedTeam` or
`hostileTargetRequired`, and the experiment remains armed until a selected-team
hostile candidate appears. Same-team target snapshots are parser failures
because they can indicate a friendly primary-target command leaked into combat
state. Valid selected-team candidates are logged with
`candidateSource="allocatorAllocation"` when the allocator emitted an
allocation, or `candidateSource="selectedShipRejectedTarget"` when the
allocator rejected the target only because the observed firing module did not
have enough `ammoGateBudgetShots` to form a useful package. In both cases, the
live command still calls only `SelectSalvoTargetCommand.OnCommandExecute` for
the selected ship and resolved hostile target. Pressing the trigger again while
an experiment is already armed does not replace it; the mod reports the pending
experiment id instead. The experiment consumes when it applies, fails, reaches
the safety gate, or otherwise reaches a selected-ship command decision.

The 2026-06-22 Lake Maracaibo smoke showed why the selected command ship must be
separate from the allocator snapshot launcher. The first controlled apply
invoked the command for selected ship `Lake Maracaibo` id `276` and target
`Persephone` id `280`. A second trigger stayed pending because Lake Maracaibo
stopped emitting missile projectile-fire cycles after 15 missile shots, while
other friendly ships continued to emit cycles. Late allocator cycles therefore
reported only per-module `ammoGateBudgetShots="1"` or `"2"` rejections for
other launchers, even though the selected ship had previously shown additional
module ammo. New logs should use `launcherId`, `launcherTeam`,
`allocatorLauncherId`, and `allocatorLauncherTeam` to make that distinction
explicit.

The later 2026-06-22 Sadowa/Tempest smoke showed the unsafe case that the team
gate prevents. The selected command ship was friendly `Sadowa` id `276` team
`47`, but the allocator cycle was emitted by enemy `Tempest` id `283` team
`50` against friendly `Vella Gulf` id `279` team `47`. The vanilla command
threw after beginning command execution, and the following missile snapshots
showed same-team target evidence. Controlled live apply must now wait for a
selected-team allocator candidate against a hostile target instead of applying
that enemy allocator cycle.

The immediate post-fix Cape St. George/Yayoi/Taiho smoke showed the intended
runtime behavior. Two enemy allocator cycles from `Yayoi` team `50` toward
friendly `Verdun` team `47` classified as `wouldSkip` with
`allocatorLauncherOutsideSelectedTeam` and left the controlled experiment armed.
The later selected-ship cycle from `Cape St. George` team `47` toward hostile
`Taiho` team `50` classified as `eligible`, reached `gateResult="allowed"`, and
emitted one `appliedDecision` through `SelectSalvoTargetCommand.OnCommandExecute`.
The parser verdict was `OK`, with one applied command, zero failed commands,
zero scope violations, zero same-team missile target snapshots, and no
suspicious patterns.

The 2026-06-22 runtime smoke validated the dry-run envelope with three explicit
UMM triggers, three grouped dry-run experiment/intent/result sets, and zero
applied or failed commands. In that smoke, selected command-panel scope was not
visible (`selectedShipCount="0"`,
`selectedScopeMissingReason="selectedScopeUnavailable"`). That is a safe #34
result because the probe failed closed; #35 should use it as input for a
broader auditable player-controlled command-scope resolver.

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

`pdWeightsDefaulted` remains a limitation marker only when the current snapshot
cannot recover target point-defense weapon evidence from the runtime ship state.
Issue #27 adds a conservative observed source:
`pdWeightEvidenceSource=observedTargetWeaponTemplates`. That source reflects
visible target weapon templates whose `defenseMode` flag is true. The current
scalar `pdWeight` is an observed count-style capability signal, not a calibrated
vanilla point-defense simulator. When target weapon templates or their
`defenseMode` members are not visible, diagnostics keep
`pdWeightEvidenceSource=defaultModel`, `pdWeightDefaulted=True`, and a specific
`pdWeightMissingReason` such as `targetObjectUnavailable`,
`targetWeaponTemplatesUnavailable`, or `targetWeaponDefenseModeUnavailable`.
The cycle also reports `pdWeightEvidenceSource`, `pdWeightDefaulted`,
`pdWeightDefaultReason`, and `pdWeightMissingReason` so a formal default model
is distinguishable from observed PD evidence and unknown PD evidence.

Issue #29 adds a separate point-defense capability evidence layer without
renaming or recalibrating the legacy `pdWeight` count. The new fields are:

- `pdEvidenceQuality`: `defaultModel`, `observedPresenceOnly`, or
  `observedTemplateCapability` in the current runtime path.
- `pdCapabilityEvidenceSource`: `observedTargetWeaponTemplateCapability` when
  static target weapon-template capability fields were visible.
- `pdCapabilityWeaponCount`: observed defense-mode weapon count.
- `pdCapabilityRangeKm`: maximum observed projectile-defense range from
  `EffectiveRangeAgainstProjectiles_km()` / targeting-range style fields.
- `pdCapabilityCooldownSeconds`: average observed cooldown from template
  cooldown fields when visible.
- `pdCapabilityObservedFields`: comma-separated static template field
  categories that justify `observedTemplateCapability`, such as `range`,
  `cooldown`, `ammoCapacity`, `range,cooldown`, or `none`.
- `pdCapabilityMissingReason`: why capability evidence is absent.
- `pdCapabilityLimitations`: comma-separated limits such as
  `templateCapabilityOnly`, `noLiveReadiness`, `noGeometry`, and
  `noArcCoverage`.

`observedTemplateCapability` means static template fields such as range,
cooldown, or ammo-capacity-like fields were observed. It is stronger than
defense-mode presence, but it is still provisional. Ammo-capacity-like template
fields are not live ammo/readiness, and the current schema is still not arc
coverage, target/projectile geometry, or a calibrated vanilla point-defense
simulator.

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

The parser separates current shadow cycles, allocations, rejections, and no-op
records from controlled dry-run experiment rows and controlled-apply result
records. Controlled dry-run rows are summarized by experiment count, experiment
id, selected group members, intent count, command-candidate count, apply-gate
count, intended/skipped/applied/failed/safety-gate-blocked command counts,
candidate classification/reason counts, apply-gate result counts, safety-gate
block reason counts, command-scope source and missing-reason counts,
scope-violation count, selected ship counts, and selected-scope missing
reasons. Controlled live apply rows with an `experimentId` are summarized
separately by attempts, applied, skipped, failed, reason counts, command path
counts, counts by experiment, counts by selected ship, assigned shots by
selected ship, visible spent shots by selected ship when present, and explicit
mismatch evidence when assigned/spent or selected/command scope counts disagree.

The parser also treats same-team missile target snapshots as a failed verdict.
Those snapshots can indicate that a controlled command or external combat state
set a friendly ship as the missile target, so they must be inspected before
using the log as safe live-apply evidence.

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
evidence source counts, missing reason counts, no-op/skip reason counts, and
cycle status counts. PD input reporting separates observed, defaulted, and
unknown cycles, then prints the evidence source, default reason, missing
reason, capability quality, capability source, capability missing reason, and
capability observed-field, and capability limitation breakdowns.

Parser warnings such as `all shadow cycles missing ammoGateBudgetShots`, `too
many launch-window rejects`, or `allocation report limited by missing runtime
inputs` are tuning hints from observed diagnostic fields. They are not proof of
combat outcome quality.

## Shadow fitting wrapper

Issue #24 adds an offline wrapper for replaying selected combat logs through the
parser and classifying shadow allocation decisions without launching Terra
Invicta:

```powershell
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\selected --output artifacts\shadow-fitting\latest
```

Both default paths are under `artifacts/`, which is ignored. Real selected
combat logs should stay local and should not be committed. The wrapper accepts
`.log` and `.txt` files, writes one per-log JSON summary, writes
`summary.json`, and writes `shadow-fitting-report.md`.

The fitting report classifies allocation, rejection, and no-op rows into
conservative buckets:

- `plausible`
- `overkill`
- `underkill`
- `late/out-of-window`
- `target-value mismatch`
- `PD-risk mismatch`
- `partial saturation`
- `command-safety no-op`
- `missing-evidence-limited`
- `impossible`
- `ambiguous`

Controlled dry-run rows such as `dryRunExperiment`, `dryRunIntent`,
`dryRunCommandCandidate`, `dryRunApplyGate`, and `dryRunResult` are not
allocation-quality rows. The fitting report summarizes them separately with
experiment, candidate, apply-gate, classification, reason, command-scope,
selected-scope, scope-violation, safety-gate-blocked, and applied/failed command
counts instead of treating them as ambiguous allocation decisions.

`command-safety no-op` means no allocation was made because no concrete
launcher-selected target identity was visible. It is safe skip evidence, not
allocation-quality evidence and not proof that vanilla had no missile target.

PD default-model evidence is reported as an evidence limitation when it qualifies
an allocation/rejection decision. PD defaulting on `command-safety no-op` rows is
not counted as an allocation evidence limit because no target was allocated.
PD-defaulted allocation/rejection evidence can support at most a conditional #6
baseline recommendation; it cannot establish full readiness.

Issue #28 adds a separate evidence-sufficiency gate to the fitting report. This
gate is intentionally distinct from parser health, required-evidence presence,
empty `missingInputs`, and the fitting-wrapper `Ready for #6 baseline` verdict.
It reports these per-input statuses:

- `ready`: source-labeled evidence is sufficient for the scoped claim.
- `provisional`: usable for cautious baseline diagnostics, with a named limit.
- `presenceOnly`: proves existence or presence, not capability magnitude or
  live state.
- `defaulted`: a fallback/default model affected allocation or rejection
  evidence.
- `unknown`: absent or not interpretable from the selected logs.
- `commandUnsafe`: unsafe for controlled command application even when parser
  and fitting evidence are healthy.

Legacy `observedTargetWeaponTemplates` point-defense evidence with no
`pdEvidenceQuality` field remains `presenceOnly`. New
`pdEvidenceQuality=observedPresenceOnly` is also `presenceOnly`. New
`pdEvidenceQuality=observedTemplateCapability` is `provisional`: it proves
static template capability fields were visible, but not live readiness, ammo,
arc coverage, range geometry, support behavior applicability, or exact
interception capability. `pdCapabilityObservedFields` names which template field
categories justified that label. `geometryAwareCapability` is reserved for
future source-backed work and is not automatically `ready`; until separately
validated, richer-than-presence PD capability remains `provisional`.
`defaultModel` or `pdWeightDefaulted=True` remains a named limitation whenever
it qualifies allocation or rejection evidence.

The same report also carries controlled live command readiness separately from
fitting readiness. Current reports should remain `Not ready` for controlled
live commands until command-intent logging, vanilla command granularity mapping,
and live-command safety gates pass.

Rows scoped as `fitting baseline` describe allocator-consumable evidence for
offline diagnostics. They do not prove that the same evidence is sufficient for
controlled command application.

A tiny synthetic fixture exists at
`tools/fixtures/shadow_allocation_synthetic.txt` for wrapper smoke validation.
It is not real combat evidence and must not be used for the Issue #24 fitting
verdict.

## Validation commands

Static validation:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py
python -m compileall tools
python tools\parse_player_log.py --require-launchlogs
```

Runtime validation after deploying and enabling battle snapshot diagnostics:

```powershell
python tools\parse_player_log.py --require-launchlogs --require-snapshots
```

Offline fitting validation after copying selected local logs:

```powershell
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\selected --output artifacts\shadow-fitting\latest
```

Expected runtime result:

- diagnostics bootstrap remains `patched=3`, `skipped=0`;
- LaunchLog entries remain present and contiguous;
- SnapshotLog entries are present;
- MissileWarfare issues remain empty.
