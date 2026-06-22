# Runtime validation history

This document preserves smoke-test and runtime-validation findings for the missile-warfare diagnostics path.

For the current log schema and parser behavior, see [`snapshot-and-allocation.md`](snapshot-and-allocation.md).

## Issue #4 shadow allocation smoke

Fresh Issue #4 runtime smoke on the active `Player.log` after enabling shadow allocation diagnostics confirmed the shadow loop was observation-only and conservative when the then-current shot-budget field was unavailable.

The first two smoke results below preserve raw pre-#17 log field names for historical traceability. Current diagnostics use `ammoGateBudgetShots` / `totalAmmoGateBudgetShots`; do not treat those older field names as current allocator inputs.

First smoke, 2026-06-19, initial Issue #4 build:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- `LaunchLog` entries: 12,304, with contiguous sequence range `1-12304`
- `MissileWeapon.TryFire` rows: 665
- `SnapshotLog` entries: 665
- `AllocationLog` entries: 1,330
- `recordType=cycle`: 665
- `recordType=rejection`: 665
- `status=evaluated`: 665
- raw legacy `missingInputs` included the old shot-budget field, `targetVelocity`, and `pdWeightsDefaulted`: 665
- raw legacy rejection reason was missing shot-budget evidence: 665
- MissileWarfare issues: none

That first smoke also showed `battle="unavailable"` on both existing LaunchLog records and new AllocationLog records. Source tracing against the read-only decompiled reference found that `GameControl` is in the global namespace, while the diagnostic reflection lookup only tried `PavonisInteractive.TerraInvicta.GameControl`. The lookup now tries the global `GameControl` type first and keeps the namespaced form as a fallback.

Follow-up smoke, 2026-06-19, after rebuilding and redeploying the battle-context lookup fix:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- `LaunchLog` entries: 3,742, with contiguous sequence range `1-3742`
- `MissileWeapon.TryFire` rows: 675
- `SnapshotLog` entries: 675
- `AllocationLog` entries: 1,350
- `recordType=cycle`: 675
- `recordType=rejection`: 675
- `status=evaluated`: 675
- raw legacy `missingInputs` included the old shot-budget field, `targetVelocity`, and `pdWeightsDefaulted`: 675
- raw legacy rejection reason was missing shot-budget evidence: 675
- `AllocationLog battle unavailable`: `0/1350`
- `LaunchLog battle unavailable`: `0/3742`
- MissileWarfare issues: none

## Issue #10 launcher-selected target identity

Issue #10 smoke tests confirmed that the launcher primary-target path can recover launcher-selected target identity without changing combat behavior.

First launcher-selected target identity smoke test:

- `SnapshotLog` entries: 1416
- `targetIdentitySource=launcher`: 816
- `targetIdentitySource=none`: 600
- raw legacy shot-budget field was `unknown`: 1416
- `remainingShots`: visible for every snapshot

Later focused-target smoke run with the trimmed launcher-only path:

- `SnapshotLog` entries: 671
- `targetIdentitySource=launcher`: 671
- launcher-selected target identity: 671/671 snapshots
- raw legacy shot-budget field was `unknown`: 671
- `remainingShots`: visible for every snapshot
- MissileWarfare issues: none

Interpretation:

- `targetIdentitySource=launcher` means launcher/carrier primary-target or focus-fire identity.
- It is not evidence of the actual in-flight missile guidance target held by `MissileController.target`.
- `targetIdentitySource=none` does not mean the missile had no target; `MissileWeapon.TryFire` logged target values for the same run.

## Issue #11 live weapon ammo and gate evidence

Issue #11 Phase 01 recommended a separate live weapon diagnostic path around `MissileWeapon.TryFire` or `TISpaceShipState.FireWeapon` to record post-fire remaining ammo and capacity evidence. Existing postfix observations occur after ammo decrement, so those values should be named as post-fire remaining ammo, not as a fireable-shot budget.

Issue #11 Phase 02 added that evidence to successful `MissileWeapon.TryFire` `LaunchLog` rows. New optional diagnostics included:

- `ammoEvidenceSource`
- `postFireRemaining`
- `postFireWeaponHasAmmo`
- `postFireWeaponCanFire`
- `postFireOnCooldown`
- cooldown/salvo timing fields
- template and magazine capacity fields

Fresh Phase 02 runtime validation confirmed the live weapon evidence path:

- `MissileWeapon.TryFire` rows: 649
- `ammoEvidenceSource=shipAmmoByWeaponData`: 649/649
- `postFireRemaining`: populated 649/649, ranging from `0` through `14`
- `postFireWeaponHasAmmo=False` and `postFireWeaponCanFire=False`: 42 rows, matching the 42 `postFireRemaining=0` rows
- `postFireOnCooldown=True`: 649/649
- capacity evidence: `templateMagazine=6`, `magazineCapacityCurrent=15`, and `magazineCapacityMax=15` on every row

This confirmed that `TISpaceShipState.ammo[weaponData]` is visible from the live weapon postfix path and behaves as post-decrement ammo. It is not yet classified as allocator-safe fireable-shot evidence, but [`readiness-semantics.md`](../research/readiness-semantics.md) tracks the explicit hypothesis that this keyed ammo value may be the vanilla runtime shot budget when combined with known fire gates.

## Issue #11 cooldown evidence

The same runtime log showed `cooldownDuration=null`. Phase 03 traced this to `currentCooldownDuration_s` being a private field declared on the base `Weapon` class while the observed runtime object is `MissileWeapon`.

The diagnostics now use a narrow inherited-member read for that exact cooldown field. Fresh runtime validation after that change confirmed `cooldownDuration=00:00:07` on all 675 successful `MissileWeapon.TryFire` rows in the follow-up smoke log.

## Issue #11 paired pre/post observation

Issue #11 Phase 04 added paired pre/post observation on the live `MissileWeapon.TryFire(DateTime)` hook.

The prefix captures gate and ammo evidence before `MissileWeapon.TryFire` calls `TryFireCommon`, launches the projectile, enters cooldown, and calls `TISpaceShipState.FireWeapon`. The decompiled path shows `FireWeapon(module, targetedProjectile)` performs the magazine decrement through `ChangeAmmoValue(module, -1)`, so pre-fire and post-fire values must remain separately named.

New optional successful-launch fields:

- `preFireAmmoEvidenceSource`
- `preFireRemaining`
- `preFireWeaponHasAmmo`
- `preFireWeaponCanFire`
- `preFireOnCooldown`
- `preFireSalvoShotsFired`
- `preFireSalvoShots`

Fresh Phase 04 runtime smoke validation on the active `Player.log` confirmed the paired observation. This active-log smoke run superseded an earlier pre-smoke parser check that reported 4,798 `LaunchLog` rows and 675 `MissileWeapon.TryFire` rows from a previous log.

Phase 04 smoke result:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- `LaunchLog` entries: 21,474, with contiguous sequence range `1-21474`
- `MissileWeapon.TryFire` rows: 670
- `preFireAmmoEvidenceSource=shipAmmoByWeaponData`: 670/670
- all seven `preFire*` fields present on 670/670 successful try-fire rows
- numeric `preFireRemaining` and `postFireRemaining` pairs: 670/670
- `preFireRemaining - postFireRemaining = 1`: 670/670
- `SnapshotLog` entries: 670
- raw legacy shot-budget field was `unknown`: 670/670
- MissileWarfare issues: none

Interpretation: this relationship is consistent with observing the ship ammo dictionary before and after the `FireWeapon` magazine decrement. It proves useful pre-fire ammo state is visible from the live weapon hook, but `preFireRemaining` is still ammo-state evidence. It is not automatically an allocator-safe fireable-shot budget.

## Issue #15 readiness evidence result

Issue #15 wires the live `MissileWeapon.TryFire` pre-fire evidence into the projectile-fire snapshot/allocation diagnostic path when those hooks execute on the same thread.

The new snapshot and allocation cycle fields preserve the distinction between:

- numeric fireable-shot evidence from a future proven allocator-safe source;
- ammo-only evidence from `TISpaceShipState.ammo[weaponData]`;
- gate/cooldown evidence such as `WeaponHasAmmo`, `WeaponCanFire`, and `OnCooldown`;
- unknown readiness with a concrete missing reason.

The current implementation deliberately removed the earlier optimistic projectile-snapshot ready-shot inference from names such as `loadedAmmo`, `loadedMissiles`, and `readyMissiles`.

Current runtime evidence at this point remained ammo/gate evidence, not allocator-safe fireable-shot evidence, so the legacy snapshot and allocation shot-budget fields remained `unknown` until shot-budget semantics were validated.

That meant the project was not ready to proceed to Issue #6 controlled allocation based on numeric shot-budget counts alone. It was ready to collect fresh runtime smoke logs with Issue #15 fields and decide whether another runtime source could prove fireable-shot semantics, whether `ammo[weaponData]` plus known gates was sufficient, or whether controlled allocation should avoid a numeric fleet-level budget.

## Issue #18/#19 velocity and PD evidence result

Issue #18/#19 added explicit target/relative velocity evidence fields and explicit point-defense default-model fields to snapshot and allocation diagnostics.

Fresh runtime smoke on the active `Player.log`, last written `2026-06-21 09:23:17` local time, confirmed the new schema is emitted and the parser summarizes it:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- `LaunchLog` entries: 4,363, with contiguous sequence range `1-4363`
- `MissileWeapon.TryFire` rows: 745
- `SnapshotLog` entries: 745
- `AllocationLog` entries: 1,490: 745 `cycle`, 745 `allocation`
- `ammoGateBudgetShots`: 745/745 numeric snapshot/cycle evidence
- total allocation-cycle ammo/gate budget: 5,985 shots
- target velocity evidence: 0/745 cycles
- `targetVelocityMissingReason=targetVelocityMemberUnavailable`: 745/745 cycles
- relative velocity evidence: 0/745 cycles, blocked by missing target velocity
- PD weight inputs: 0 observed, 745 defaulted, 0 unknown cycles
- `pdWeightEvidenceSource=defaultModel`: 745/745 cycles
- `pdWeightDefaultReason=pdEvidenceUnavailable`: 745/745 cycles
- MissileWarfare issues: none

Interpretation: the point-defense default model is now explicit and runtime-confirmed instead of opaque. Target velocity is still unavailable from the current launcher-selected target object, but it now fails with a precise missing reason rather than a generic all-cycles missing flag. Controlled allocation remains blocked until this velocity gap is accepted or a better target combat-state/member source is found.

## Issue #18 target velocity recovery follow-up

Decompiled source review showed target velocity should be read from the live `MissileWeapon.target` object during `MissileWeapon.TryFire`, not from the later `TISpaceCombatProjectileState.Fire(...)` arguments. `Weapon.target` is an `IDamageable`; vanilla missile targeting uses that object's `position`, `velocityVector`, and `accelerationVector` for intercept calculation.

The diagnostics now capture `IDamageable.velocityVector_kps` in the `MissileWeapon.TryFire` prefix and pass it through the existing same-thread readiness handoff to snapshot/allocation diagnostics. A same-target `positionAtTime(t + 1s) - positionAtTime(t)` derivative remains as fallback if direct velocity is unavailable.

Fresh runtime smoke on the active `Player.log`, last written `2026-06-21 09:34:44` local time, confirmed the corrected target-velocity source:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- `LaunchLog` entries: 6,701, with contiguous sequence range `1-6701`
- `MissileWeapon.TryFire` rows: 748
- `SnapshotLog` entries: 748
- `AllocationLog` entries: 1,496: 748 `cycle`, 748 `allocation`
- `ammoGateBudgetShots`: 748/748 numeric snapshot/cycle evidence
- total allocation-cycle ammo/gate budget: 5,998 shots
- target velocity evidence: 748/748 cycles
- `targetVelocityEvidenceSource=tryFireTargetDamageableVelocity`: 748/748 cycles
- `targetVelocityMissingReason=none`: 748/748 cycles
- relative velocity evidence: 748/748 cycles
- `relativeVelocityEvidenceSource=targetAndLauncherVelocity`: 748/748 cycles
- `relativeVelocityMissingReason=none`: 748/748 cycles
- PD weight inputs: 0 observed, 748 defaulted, 0 unknown cycles
- `pdWeightEvidenceSource=defaultModel`: 748/748 cycles
- `pdWeightDefaultReason=pdEvidenceUnavailable`: 748/748 cycles
- MissileWarfare issues: none

Interpretation: #18 target/relative velocity evidence is now runtime-confirmed. The remaining all-cycle diagnostic limitation is #19's intentional PD default model, not missing target velocity.

## PR #20 / Issue #4 closure evidence

The post-PR #20 cleanup confirms Issue #4 is complete as an observation-only
shadow allocation loop:

- `ammoGateBudgetShots` / `totalAmmoGateBudgetShots` replaced the legacy
  shot-budget terminology in the current schema and parser.
- Fresh smoke history above records numeric ammo/gate budget evidence,
  target-velocity evidence, relative-velocity evidence, allocation records, and
  no MissileWarfare warnings/errors.
- Parser output separates shadow cycles, allocation records, rejection records,
  missing inputs, cycle status, and no-op/skip reasons.
- The mod path remains diagnostics-only: it logs recommendations and
  no-op/skip decisions, but does not assign targets, issue commands, change
  fire mode, suppress launches, alter AI behavior, or mutate manual player
  control.

## Issue #24 log-only fitting pass

Issue #24 adds an offline fitting wrapper for selected combat logs:

```powershell
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\selected --output artifacts\shadow-fitting\latest
```

The selected-log input and generated fitting outputs are intentionally under
ignored `artifacts/` paths. Real selected combat logs remain local. The wrapper
produces per-log JSON, aggregate `summary.json`, and
`shadow-fitting-report.md`, then classifies observed shadow allocation decisions
as plausible, bad, ambiguous, or evidence-limited without changing runtime
combat behavior.

Initial tooling validation used only
`tools/fixtures/shadow_allocation_synthetic.txt`. That fixture confirms the
wrapper/parser workflow but is not real combat evidence and does not count as
the Issue #24 fitting result.

Current Issue #24 readiness rule for #6:

- One real selected combat log with `LaunchLog`, `SnapshotLog`, and
  `AllocationLog` evidence can support `Conditionally ready` if the fitting
  report shows no impossible or obviously unsafe allocation behavior and at
  least one plausible allocation or no-op decision.
- Full `Ready for #6 baseline` requires multiple real selected logs with
  required evidence, at least one plausible decision, no severe
  classifications, and no PD-defaulted evidence.
- Any PD-defaulted evidence keeps the verdict at most `Conditionally ready`;
  observed target point-defense weapon recovery is still required before full
  readiness.
- Any heuristic or scoring change must be justified by repeated,
  evidence-supported bad classifications in selected real logs.

No #24 wrapper path applies targeting commands, launch commands, fire-mode
changes, projectile changes, AI behavior changes, or player-control mutations.

## Issue #27 target point-defense evidence implementation

Issue #27 adds a runtime extraction path for observed target point-defense
capability. Decompiled-source review identified `TISpaceShipState` weapon
template lists and `TIShipWeaponTemplate.defenseMode` as the conservative
diagnostic signal. Vanilla defensive fire is represented by `DefenseFireMode`,
which is available for defense-mode weapons and uses projectile-defense range
members such as `EffectiveRangeAgainstProjectiles_km()`.

The mod now attempts to read the visible target ship's weapon templates from
the existing projectile-fire snapshot target object. When templates and their
`defenseMode` fields are visible, it emits
`pdWeightEvidenceSource=observedTargetWeaponTemplates`,
`pdWeightDefaulted=False`, and uses an observed count-style `pdWeight` for
defense-mode weapons. If the target object, template list, or defense-mode
field is unavailable, the diagnostics keep the explicit default model and
record the missing reason.

Fresh runtime smoke on the active `Player.log`, last written
`2026-06-21 18:43:34` local time, confirmed the target weapon-template PD
evidence path:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- `LaunchLog` entries: 4,564, with contiguous sequence range `1-4564`
- `MissileWeapon.TryFire` rows: 730
- `SnapshotLog` entries: 730
- `AllocationLog` entries: 1,460: 730 `cycle`, 448 `allocation`, 282 `rejection`
- `ammoGateBudgetShots`: 730/730 numeric snapshot/cycle evidence
- total allocation-cycle ammo/gate budget: 5,922 shots
- target velocity evidence: 730/730 cycles
- relative velocity evidence: 730/730 cycles
- PD weight inputs: 730 observed, 0 defaulted, 0 unknown cycles
- `pdWeightEvidenceSource=observedTargetWeaponTemplates`: 730/730 cycles
- `pdWeightDefaultReason=none`: 730/730 cycles
- `pdWeightMissingReason=none`: 730/730 cycles
- critical missing fields: `pdWeightsDefaulted` 0/730, and all other critical
  allocation inputs 0/730
- parser suspicious patterns: none
- MissileWarfare issues: none

Fitting this one live log directly through
`tools/fit_shadow_allocation.py` produced:

- readiness verdict: `Conditionally ready`
- reason: only one real selected combat log was analyzed
- plausible: 328
- partial saturation: 120
- ambiguous: 282
- severe classifications: 0
- evidence limitations: none

Interpretation: Issue #27 recovered observed target PD capability evidence for
this combat log. Full #6 baseline readiness is no longer blocked by all-cycle
PD defaulting in this sample, but still requires multiple real selected logs
under the existing Issue #24 readiness rule.

## Current four-log fitting snapshot

On 2026-06-22, the offline fitting wrapper replayed the fresh selected
Terra Invicta `Player*.log` combat logs copied under ignored `artifacts/`
paths:

```powershell
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\selected --output artifacts\shadow-fitting\latest
```

The selected set was:

- `Player-prev2.log`, written 2026-06-22 09:03 local time
- `Player-prev1.log`, written 2026-06-22 09:05 local time
- `Player-prev.log`, written 2026-06-22 09:09 local time
- `Player.log`, written 2026-06-22 09:11 local time

Aggregate result:

- logs analyzed: 4
- logs with required evidence: 4
- real selected logs with required evidence: 4
- parser failures: 0
- fitting readiness verdict: `Ready for #6 baseline`
- evidence sufficiency verdict: `Baseline-ready with named limitations`
- controlled live command readiness: `Not ready`
- plausible: 541
- partial saturation: 114
- ambiguous: 58
- command-safety no-op: 204
- missing-evidence-limited: 0
- severe classifications: 0 (`overkill`, `underkill`, `target-value mismatch`,
  `PD-risk mismatch`, and `impossible` were all zero)
- evidence limitations: none

Per-log fitting summary:

- `Player-prev.log`: parser `OK`; 497 shadow cycles; 364 plausible, 79
  partial saturation, 54 ambiguous; no command-safety no-op rows.
- `Player-prev1.log`: parser `OK`; 195 shadow cycles; 156 plausible, 35
  partial saturation, 4 ambiguous; no command-safety no-op rows.
- `Player-prev2.log`: parser `OK`; 33 shadow cycles; 21 plausible, 12
  command-safety no-op.
- `Player.log`: parser `OK`; 192 shadow cycles; 192 command-safety no-op and
  no allocation-quality rows.

Evidence sufficiency summary:

- `ammoGateBudgetShots`: `ready`, 917/917 cycles numeric
- target identity: `provisional`, 713/917 cycles with launcher-selected target
  identity; 204 no-op rows lacked target identity and allocated no shots
- target velocity: `ready`, 917/917 cycles observed
- relative velocity: `ready`, 917/917 cycles observed
- missile profile data: `ready`, 917/917 cycles present
- observed target PD evidence: `provisional`, with 713/917 observed static
  template-capability cycles and 204/917 default-model cycles only on
  non-allocation decisions

Interpretation: the fresh selected logs support the fitting-wrapper #6 baseline
under current rules because multiple real logs parse, required evidence is
present, allocation/rejection rows avoid PD-defaulted evidence, and severe
classifications are zero. They do not unblock controlled live command
application; command intent logging, command mapping, and live-command safety
remain separate gates.

## Issue #28 evidence sufficiency gate

Issue #28 adds an explicit sufficiency layer above the parser verdict and the
Issue #24 fitting baseline. The gate separates parser/fitting health from
controlled live-command readiness and reports named evidence limits for each
input category.

The fitting report now names statuses such as `ready`, `provisional`,
`presenceOnly`, `defaulted`, `unknown`, and `commandUnsafe`. Parser `OK`, empty
allocator-critical `missingInputs`, and a fitting-wrapper readiness verdict are
not sufficient wording for controlled #6 readiness. They can support a baseline
for design and diagnostics only when the generated evidence-sufficiency report
is reviewed with the controlled-command blockers still in view.

## Issue #29 point-defense capability evidence quality

Issue #29 upgrades the point-defense evidence vocabulary without changing the
legacy `pdWeight` count-style scalar. Source review confirmed conservative
static template capability fields on `TIShipWeaponTemplate`, including
`defenseMode`, `EffectiveRangeAgainstProjectiles_km()`, `targetingRange_km`,
`cooldown_s`, and `averageCooldown_s`. The same review did not prove that the
current projectile-fire snapshot can safely observe target defensive weapon
cooldown/readiness, live ammo, arc coverage, or target/projectile geometry.

The runtime schema now emits additive fields:

- `pdEvidenceQuality`
- `pdCapabilityEvidenceSource`
- `pdCapabilityWeaponCount`
- `pdCapabilityRangeKm`
- `pdCapabilityCooldownSeconds`
- `pdCapabilityObservedFields`
- `pdCapabilityMissingReason`
- `pdCapabilityLimitations`

The fitting report interprets those fields conservatively:

- missing new fields on old logs preserve the Issue #28 legacy behavior:
  `observedTargetWeaponTemplates` remains `presenceOnly`;
- `pdEvidenceQuality=observedPresenceOnly` remains `presenceOnly`;
- `pdEvidenceQuality=observedTemplateCapability` becomes `provisional`, with
  limitations naming template-only evidence, no live readiness, no geometry,
  and no arc coverage;
- `pdCapabilityObservedFields` records which static template field categories
  justified the capability label, such as `range`, `cooldown`, or
  `ammoCapacity`;
- ammo-capacity-like template fields are not live ammo/readiness evidence;
- future `geometryAwareCapability` evidence remains `provisional` by default
  until a separate source-backed readiness gate and real-log validation prove a
  stronger claim;
- `pdEvidenceQuality=defaultModel` remains defaulted fallback evidence.

Static validation used `tools/fixtures/shadow_allocation_synthetic.txt` to
exercise `observedTemplateCapability` and
`tools/fixtures/shadow_allocation_missing_target_noop.txt` to preserve the
defaulted no-op path. The fixture fitting report correctly classified observed
target PD evidence as `provisional`; the aggregate readiness verdict remained
`Not ready` because fixtures are synthetic and do not count as real combat
evidence.

## Issue #36 apply-gate hard stop

Issue #36 adds the final diagnostics-only hard stop before any live command
application. It introduces the default-off `AllowCommandApply` setting, emits a
named `controlledCommandApplyGate` row for eligible controlled dry-run command
candidates, and keeps `appliedCommands="0"` in the current build.

Static fixture validation used
`tools/fixtures/apply_gate_hard_stop.txt` to prove a gate-reachable candidate is
blocked by `blockedBySafetyToggle` with zero applied commands.

Fresh runtime smoke on the active `Player.log` written 2026-06-22 15:19 local
time validated the same path in a real combat:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- LaunchLog entries: 169, no sequence gaps
- MissileWeapon.TryFire rows: 46
- SnapshotLog entries: 46
- target identity: 46/46 snapshots, all `targetIdentitySource=tryFireTarget`
- target velocity: 46/46 cycles from `tryFireTargetDamageableVelocity`
- observed target PD evidence: 46/46 cycles with
  `pdEvidenceQuality=observedTemplateCapability`
- shadow cycles: 46 evaluated, 0 skipped
- allocations: 46
- controlled dry-run experiments: 1
- controlled dry-run command candidates: 1
- candidate classification: `eligible: 1`
- selected command scope: one selected ship, `El Alamein` id `276`
- candidate launcher: `El Alamein` id `276`
- target: `Centaur` id `277`
- apply-gate records: 1
- apply-gate result: `blocked: 1`
- safety-gate reason: `blockedBySafetyToggle: 1`
- `safetyGateBlockedCommands`: 1
- applied commands: 0
- failed commands: 0
- scope violations: 0

Interpretation: #36 is validated as a diagnostics-only hard-stop proof. A
real selected single-ship candidate reached the named apply gate and was blocked
because command application was not explicitly allowed. No live command was
applied. #37 remains the first behavior-changing slice.

## Issue #37 first single-ship live controlled apply

Issue #37 introduces the first behavior-changing controlled command path behind
the #36 gate. The implementation keeps `AllowCommandApply` default-off and
requires an explicitly armed controlled experiment plus exactly one selected
command-panel ship before attempting any live command.

The reviewed live path is the vanilla single-ship salvo target command:

- `SelectSalvoTargetCommand.OnCommandExecute(TISpaceShipState, CombatTargetableState)`
- internally queues `SetCombatPrimaryTargetAction`
- internally queues `SetWeaponModeAction(..., FireMode.Salvo)` for salvo-capable
  weapons on that one ship

Static fixture validation uses `tools/fixtures/first_live_apply.txt` to prove
the parser recognizes one `gateResult="allowed"` row, one
`recordType="appliedDecision"` row, one controlled live apply attempt, one
applied command, zero skipped live attempts, zero failed live attempts, zero
safety-gate blocks, and no unknown record types.

Runtime smoke is still required before claiming a successful live game apply.
The expected live smoke must show one explicit experiment trigger, exactly one
selected player missile ship, at most one applied or failed command result, no
scope violations, no AI or unselected-player application, no unknown parser
record types, and no MissileWarfare warnings/errors.

## 2026-06-22 Issue #37 follow-up: selected command launcher vs allocator launcher

A later Lake Maracaibo combat log confirmed that the first controlled apply
reached `SelectSalvoTargetCommand.OnCommandExecute`, but also exposed a command
scope limitation in the first #37 implementation:

- selected command ship: `Lake Maracaibo` id `276`
- first controlled target: `Persephone` id `280`
- first controlled apply: one `appliedDecision`, one applied command, zero
  failed commands
- Lake Maracaibo missile `TryFire` rows: 15 total, five missile slots, each
  observed from pre-fire ammo `15` down to `13`
- other friendly ships continued to emit 75 missile `TryFire` rows each
- second controlled experiment: stayed pending across cycles 226-240 because
  the selected ship was no longer the projectile-fire launcher
- late rejection reason: `not enough ammo/gate budget shots to form a useful
  package`, with per-module `ammoGateBudgetShots` values of `1` or `2`

The important conclusion is that `ammoGateBudgetShots` is per observed
projectile-fire module, while `SelectSalvoTargetCommand` is ship-level and uses
the command-panel selected ship. The controlled apply path now keeps the
selected ship runtime object separately from the allocator snapshot launcher.
New candidate/apply rows log `launcherId` as the selected command ship and
`allocatorLauncherId` as the ship that produced the allocator cycle. When the
allocator only rejects a target because the observed module budget is too small,
an explicit controlled trigger may still issue the selected-ship command with
`candidateSource="selectedShipRejectedTarget"`, provided the selected ship still
reports `CanPerformShipCommands()` and `AnyOffensiveMissileWeaponCanFire()`.

## 2026-06-22 Issue #37 follow-up: enemy allocator and friendly target guard

A later Sadowa combat log showed that the selected-command-launcher follow-up
was too permissive. The controlled experiment accepted an allocator cycle from
an enemy ship and attempted to command the selected friendly ship at a friendly
target:

- selected command ship: `Sadowa` id `276`, team `47`
- allocator snapshot launcher: `Tempest` id `283`, team `50`
- resolved target: `Vella Gulf` id `279`, team `47`
- command result: `failedCommand`, `reason="commandInvocationFailed"`,
  `exceptionType="NullReferenceException"`
- subsequent controlled-ship missile snapshots targeted friendly
  `Vella Gulf`, matching the observed circular/near-self missile behavior

Interpretation: the vanilla command can mutate primary-target state before a
later invocation failure. #37 now requires known selected launcher, allocator
launcher, and target teams; the selected command ship team must match the
allocator launcher team; and the target team must differ. Enemy allocator
cycles classify as `allocatorLauncherOutsideSelectedTeam`, friendly targets
classify as `hostileTargetRequired`, and the experiment waits for a later
selected-team hostile candidate instead of applying. The parser now fails logs
with same-team missile target snapshots so this condition is not reported as a
clean smoke.

Post-fix runtime smoke on the latest `Player.log` validated the intended guard
and recovery path:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- LaunchLog entries: 1,790, no sequence gaps or duplicates
- MissileWeapon.TryFire rows: 252
- SnapshotLog entries: 252
- AllocationLog entries: 518: 252 `cycle`, 216 `allocation`, 36 `rejection`,
  three `dryRunExperiment`, three `dryRunIntent`, three
  `dryRunCommandCandidate`, one `dryRunApplyGate`, one `appliedDecision`, and
  three `dryRunResult` rows
- controlled dry-run command candidates: three total, with two `wouldSkip` and
  one `eligible`
- skipped candidate reason: `allocatorLauncherOutsideSelectedTeam: 2`
- selected command ship: `Cape St. George` id `276`, team `47`
- skipped allocator launcher: enemy `Yayoi` id `285`, team `50`, targeting
  friendly `Verdun` id `278`, team `47`
- applied candidate: selected `Cape St. George` team `47` targeting hostile
  `Taiho` id `280`, team `50`
- apply gate: one `allowed` result with `AllowCommandApply=True`
- live apply: one `appliedDecision` through
  `SelectSalvoTargetCommand.OnCommandExecute`
- applied commands: one
- failed commands: zero
- scope violations: zero
- same-team missile target snapshots: zero
- parser suspicious patterns: none

Interpretation: the post-fix log matches the intended #37 containment behavior.
Enemy allocator / friendly-target candidates wait without applying, and the
first selected-team hostile candidate can apply exactly one single-ship vanilla
salvo-target command. This is still selected single-ship evidence only; it does
not validate selected-group or fleet-wide allocation.

## 2026-06-23 Issue #38 selected-group controlled smoke

Issue #38 expands the controlled live experiment from the #37 single selected
ship path to a small explicitly selected player group. The group remains
default-off, explicitly triggered, capped at one live attempt per selected ship,
and capped at three live attempts per trigger.

Fresh runtime smoke on the latest `Player.log`, written 2026-06-23 06:03 local
time, validated selected-group scope visibility and bounded command behavior:

- parser verdict: `OK`
- diagnostics bootstrap: `patched=3`, `skipped=0`
- LaunchLog entries: 899, no sequence gaps or duplicates
- MissileWeapon.TryFire rows: 152
- SnapshotLog entries: 152
- AllocationLog entries: 412: 152 `cycle`, 147 `allocation`, five
  `rejection`, 22 `dryRunExperiment`, 22 `dryRunIntent`, 22
  `dryRunCommandCandidate`, 10 `dryRunApplyGate`, six `appliedDecision`, four
  `skippedDecision`, and 22 `dryRunResult` rows
- controlled experiment ids: `dryrun-20260622T210249826Z-1` and
  `dryrun-20260622T210303457Z-2`
- selected group source:
  `GameControl.spaceCombat.combatHUD.groupSelectedFriendlyShips`
- selected ship count: three in every controlled dry-run experiment row
- selected ships: `Shiloh` id `276`, `Carrhae` id `278`, and `Puebla` id
  `279`, all team `47`
- command candidates: 10 `eligible`, 12 `wouldSkip`
- skip reason before the apply gate: `allocatorLauncherOutsideSelectedGroup: 12`
- apply-gate records: 10, all `allowed`
- live apply attempts: 10
- applied decisions: six
- skipped live decisions: four
- skipped live reason: `perShipCommandCapReached: 4`
- failed commands: zero
- scope violations: zero
- safety-gate blocked commands: zero
- same-team missile target snapshots: zero
- parser suspicious patterns: none
- MissileWarfare issues: none

Per experiment:

- `dryrun-20260622T210249826Z-1`: three applied, two skipped
- `dryrun-20260622T210303457Z-2`: three applied, two skipped

Per selected ship:

- `Shiloh#276[team=47]`: two applied, two skipped
- `Carrhae#278[team=47]`: two applied, two skipped
- `Puebla#279[team=47]`: two applied

Interpretation: the selected-group probe now sees the in-game battle-menu group
selection through `groupSelectedFriendlyShips`. Live command application stayed
inside the selected three-ship group, ignored allocator cycles from outside the
group, respected the per-ship cap, and produced no failed commands, scope
violations, same-team target snapshots, parser suspicious patterns, or
MissileWarfare warnings/errors. This validates the #38 selected-group safety
rung. It does not validate fleet-wide #43 allocation.

Remaining limitation: controlled result rows still report command-result
`missilesSpent` as `unknown`. LaunchLog pre/post ammo deltas are visible
elsewhere in the log, but they are not yet directly correlated back to each
controlled command result row.

## Issue #39 controlled-correlation instrumentation attempt

Issue #39 reviewed the #38 selected-group controlled evidence as the first
selected-group learning-loop checkpoint. The selected-group smoke is sufficient
to show bounded command behavior: two controlled experiment ids, three selected
ships, six applied commands, four `perShipCommandCapReached` skips, zero failed
commands, zero scope violations, zero same-team missile target snapshots, no
parser suspicious patterns, and no MissileWarfare issues.

The regenerated pre-instrumentation #39 fitting artifact includes a controlled
command result evidence table tied to experiment id, selected ship, allocator
launcher, target, command result, and immediate same-launcher/same-target launch
evidence where visible. It found 10 command result rows: six applied and four
skipped. Direct command-result `missilesSpent` remained numeric on 0/10 rows.
All 10 rows had one immediate same-launcher/same-target `MissileWeapon.TryFire`
ammo delta, but the skipped rows also accounted for four observed deltas. That
means nearby launch evidence is visible, but it is not causal command-spend
proof.

#39 now adds diagnostics-only correlation support for fresh runtime evidence:
controlled apply-gate/result rows log `commandResultId`, successful applied
commands register a matching launch context, and later `MissileWeapon.TryFire`
rows can report `experimentId`, `commandResultId`,
`controlledCommandCorrelation`, and `controlledCommandObservedSpentShots` when
the launcher/target context matches.

No allocator parameters changed. The old controlled log still has 0/10 directly
stamped rows and 10/10 line-window heuristic rows, so it remains insufficient to
justify a heuristic/rule/parameter-family change. A fresh instrumented
selected-group controlled run is required before #39 can decide whether one
specific heuristic family should be tuned or whether a final no-tuning/blocker
decision is warranted.

## Issue #39 fresh instrumented log target identity follow-up

A fresh instrumented `Player.log` after the first #39 correlation slice confirmed
that launch-side telemetry fields are emitted, including launcher/target ids,
`visibleAmmoDelta`, `experimentId`, `commandResultId`,
`controlledCommandCorrelation`, and `controlledCommandObservedSpentShots`.
However, direct command correlation still did not occur in that log.

The identified blocker was target identity mismatch rather than missing launch
telemetry. Controlled command result rows used allocator target ids such as
`280` / `283`, while `MissileWeapon.TryFire` launch rows reported a runtime
`CombatShipController` stable id for `targetId`. The target text still exposed
the tactical target id, so line-window evidence remained visible, but the direct
runtime context match could not attribute the launch to the command result.

The follow-up fix adds a diagnostics-only target identity bridge: launch rows now
also report `targetStateId`, runtime context matching accepts either launch
`targetId` or bridged `targetStateId`, and the fitting report prefers
`targetStateId` / target-text id fallback before falling back to runtime stable
`targetId`. A new instrumented selected-group smoke is still required before #39
can decide whether direct stamped launch/spend evidence justifies one bounded
heuristic change.

## Issue #39 direct command-spend correlation smoke success

A fresh selected-group controlled smoke after the target identity bridge
confirmed direct command-result launch/spend correlation:

- selected ship count was 3, within `selectedGroupMaxShips=3`;
- controlled command result rows were 4 total: three `appliedDecision` rows and
  one `skippedDecision` row with `perShipCommandCapReached`;
- failed controlled commands remained zero;
- `MissileWeapon.TryFire` rows with `controlledCommandCorrelation="directRuntimeContext"`
  were observed for the applied commands;
- each applied command produced six directly stamped launch rows and observed
  spent shots of six;
- the skipped command produced no direct launch attribution.

This resolves the selected-group command-spend attribution blocker. The remaining
#39 evidence gap is outcome quality: the logs now show that controlled commands
spent missiles, but they still need conservative evidence about overkill,
under-saturation, target mismatch, or point-defense absorption before any
heuristic family should be tuned.

The fitting report now also records best-effort target destruction hints from
vanilla `CombatManager ActiveShip(DestroyShip)` lines when they occur after a
controlled command for the same target id. This is deliberately labeled as
post-command outcome evidence, not unique projectile/hit/kill attribution.
