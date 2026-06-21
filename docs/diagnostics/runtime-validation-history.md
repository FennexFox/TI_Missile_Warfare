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

No fresh runtime smoke has been recorded in this document yet. Until a local
combat log confirms observed Issue #27 fields, #6 full readiness remains gated
by PD evidence validation rather than by code availability alone.
