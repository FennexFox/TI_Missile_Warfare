# Issue #17 context: controlled-allocation readiness design

## Issue target

- GitHub issue: #17, `Resolve controlled-allocation readiness design after #15`
- Related issues: #15, #6
- Source commit that introduced the blocker docs: `8abc16abcf1eb402887bab0644011f44401c9355`
- Current local branch when this context was written: `issue_15`

## Boundary between #15, #17, and #6

Issue #15 was diagnostic evidence plumbing. It connected live `MissileWeapon.TryFire`
ammo and gate/cooldown evidence into `SnapshotLog`, `AllocationLog`, and parser/report
output. It was not a requirement to prove `readyShots` at all costs, and it was not the
place to redesign controlled allocation.

Issue #17 exists because #15 produced useful evidence but did not prove true ready-shot
semantics. #17 must decide whether #6 can safely use numeric `readyShots`, or whether #6
must be revised to avoid a fleet-level ready-shot budget.

Issue #6 is the live controlled allocation experiment. It may apply commands after an
explicit player action, so it must not begin from a fake or inferred `readyShots` value.

## Current known evidence

Confirmed runtime evidence from previous diagnostics:

- `preFireRemaining` and `postFireRemaining` are read from
  `TISpaceShipState.ammo[weaponData]`.
- `WeaponHasAmmo`, `WeaponCanFire`, and `OnCooldown` expose useful gate/cooldown state.
- On successful launches, observed numeric pairs satisfy
  `preFireRemaining - postFireRemaining = 1`.
- `SnapshotLog readyShots` and allocation `totalReadyShots` remained `unknown` in the
  confirmed logs.

This evidence proves magazine/ammo visibility and current-fire gate state. It does not
prove a true ready, loaded, or chambered missile count.

## Important semantic rule

Do not promote any of the following to `readyShots` unless a separate true ready,
loaded, or chambered runtime source is proven and documented:

- `preFireRemaining`
- `postFireRemaining`
- `remainingShots`
- `TISpaceShipState.ammo[weaponData]`
- `WeaponHasAmmo`
- `WeaponCanFire`
- `OnCooldown`
- salvo/cooldown/gate fields that only say whether a weapon can fire now

These are evidence fields. They may support logging, failure explanations, or a weaker
command-attempt design, but they are not allocator-safe shot budgets by themselves.

## Decision paths

### Path A: true count found

Choose this only if a source with true ready/loaded/chambered semantics is found.
Document:

- exact type/member/call path;
- runtime meaning;
- update timing relative to `TryFire`, `TryFireCommon`, `FireWeapon`, cooldown, salvo
  state, and `ChangeAmmoValue`;
- whether the value is per weapon, per module, per salvo, per ship, or per magazine;
- whether it can be safely aggregated into allocator-level `readyShots`.

Only after this documentation should snapshot/allocation code map the source to numeric
`readyShots`.

### Path B: true count absent or still ambiguous

This is an acceptable outcome. Keep `readyShots` unknown and revise #6 around weaker
per-ship/per-weapon evidence.

In this design, #6 should not ask: "How many fleet-level ready shots can the allocator
spend?" Instead it should ask: "For the selected player ships and visible weapons, can we
attempt a controlled target command, log the intent, and observe the result without
breaking vanilla combat?"

The game should remain responsible for the actual legal launch count. The mod should log:

- selected player ship identity;
- visible weapon/module identity when available;
- ammo evidence as ammo evidence only;
- gate/cooldown state as gate evidence only;
- allocator recommendation that motivated the command;
- command intent and target;
- pre-state/post-state when visible;
- skipped/failure reason;
- observed ammo delta or launch evidence when available.

## Local files to inspect first

- `docs/reverse-engineering-plan.md`
- `docs/battle-snapshot-extractor.md`
- `docs/confirmed-hooks.md`
- `docs/mvp-issue-list.md`
- `docs/plan/issue_15/00-master-plan.md`
- `docs/plan/issue_15/04-verification.md`

Likely code areas if instrumentation is needed:

- `CombatLaunchDiagnostics` and launch/snapshot hooks around `MissileWeapon.TryFire`,
  `TISpaceShipState.FireWeapon`, and `TISpaceCombatProjectileState.Fire(missile)`.
- Snapshot/allocation model fields that currently carry `readyShots`,
  `readyShotEvidenceSource`, `readinessMissingReason`, `ammoEvidenceSource`,
  `liveWeaponState`, `readyWeaponCount`, and `unknownReadinessWeaponCount`.
- `tools/parse_player_log.py` readiness summaries and JSON output.

## Suggested implementation order

1. Re-read #15 result docs and confirmed hook notes to preserve the diagnostic-only
   boundary.
2. Inspect the decompiled/runtime areas listed in #17 only enough to decide whether a
   true ready/loaded/chambered count source exists.
3. Record the decision in docs before making any #6 command-path changes.
4. If Path A is chosen, add only narrowly sourced numeric `readyShots` mapping and keep
   old unknown/ammo-only cases explicit.
5. If Path B is chosen, update #6 docs/design to remove numeric fleet-level shot budget
   assumptions and describe per-ship/per-weapon command-attempt logging.
6. Keep all changes in #17 diagnostic/design scope. Live command application belongs in
   #6.

## Validation expectations

Docs-only resolution:

- Review changed docs against the #17 acceptance criteria.

Instrumentation/parser changes:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py
python -m compileall tools
python tools\parse_player_log.py --require-launchlogs --require-snapshots
```

Runtime evidence changes require deploying the mod and collecting a fresh combat log
before claiming that new runtime fields are proven.

## Risks

- Treating ammo dictionary values as `readyShots` would silently reintroduce the main
  safety bug this issue is meant to prevent.
- A source name containing `ready`, `loaded`, or `missiles` is not enough; the runtime
  semantics and update timing must be proven.
- Controlled allocation should remain blocked until this issue documents either Path A
  or Path B.
