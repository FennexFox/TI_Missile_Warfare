# Issue #17 context: controlled-allocation readiness design

## Issue target

- GitHub issue: #17, `Resolve controlled-allocation readiness design after #15`
- Related issues: #15, #6, #7
- Current milestone gate: resolve shot-budget semantics before controlled command/application work.

## Current answer

Issue #17 is still the right next step before Issue #6 controlled allocation.

The project has enough diagnostics to observe missile launches and shadow allocation inputs, but it is not ready to apply commands. The active blocker is not "find a separate ready-shot source at all costs." The active blocker is to decide which readiness model is actually true enough for the next design step:

1. `ammo[weaponData]` plus known gates is the game-equivalent shot budget.
2. A distinct allocator-safe runtime shot-budget source exists.
3. No numeric fleet-level shot budget should be used; Issue #6 should be redesigned around per-ship/per-weapon command attempts and observation.

Any of these can be a valid #17 outcome if documented with evidence.

## Boundary between #15, #17, and #6

Issue #15 was diagnostic evidence plumbing. It connected live `MissileWeapon.TryFire` ammo and gate/cooldown evidence into `SnapshotLog`, `AllocationLog`, and parser/report output. It was not a requirement to prove `readyShots` and it was not the place to redesign controlled allocation.

Issue #17 exists because #15 produced useful evidence but did not resolve shot-budget semantics. #17 must decide whether #6 can safely use a numeric shot budget, whether it needs a distinct runtime source, or whether #6 should avoid numeric fleet-level budgeting entirely.

Issue #6 is the live controlled-allocation experiment. It may apply commands after an explicit player action, so it must not begin from a fake or inferred `readyShots` value.

## Current known evidence

Confirmed runtime evidence from previous diagnostics:

- `preFireRemaining` and `postFireRemaining` are read from `TISpaceShipState.ammo[weaponData]`.
- `WeaponHasAmmo`, `WeaponCanFire`, and `OnCooldown` expose useful gate/cooldown state.
- On successful launches, observed numeric pairs satisfy `preFireRemaining - postFireRemaining = 1`.
- `SnapshotLog readyShots` and allocation `totalReadyShots` remain `unknown` in confirmed logs.

This evidence proves ammo visibility and current-fire gate state. It does not by itself prove allocator-safe numeric `readyShots`, but it also does not prove that a separate loaded/chambered/ready state must exist.

See durable docs:

- `docs/README.md`
- `docs/planning/mvp-roadmap.md`
- `docs/research/readiness-semantics.md`
- `docs/research/reverse-engineering-plan.md`
- `docs/diagnostics/hooks.md`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`

## Semantic rule

Do not use the name `readyShots` for ammo/gate evidence until the semantics are validated.

Treat these as raw evidence fields unless #17 explicitly promotes them with a documented reason:

- `preFireRemaining`
- `postFireRemaining`
- `remainingShots`
- `TISpaceShipState.ammo[weaponData]`
- `WeaponHasAmmo`
- `WeaponCanFire`
- `OnCooldown`
- salvo/cooldown/gate fields

They may support logging, failure explanations, or a weaker command-attempt design. They may also support a future numeric budget if #17 validates that `ammo[weaponData]` plus known gates is the game-equivalent shot budget.

## Decision paths

### Path A: ammo plus gates is validated as the game-equivalent shot budget

Choose this if runtime/decompiled evidence shows that `TISpaceShipState.ammo[weaponData]`, together with `WeaponCanFire`, cooldown, salvo, target, and similar gates, is the same budget vanilla uses for the relevant fire decision.

Document:

- exact call path from `MissileWeapon.TryFire` / `TryFireCommon` to ammo/gate checks;
- update timing relative to `TryFire`, `TryFireCommon`, `FireWeapon`, cooldown, salvo state, and `ChangeAmmoValue`;
- what cases are explained by gates when `ammo[weaponData] > 0` but no shot fires;
- whether the budget is per weapon, per module, per ship, or keyed by `ModuleDataEntry`;
- whether and how it can be aggregated for allocator diagnostics;
- terminology to use instead of inventing a separate ready/loaded/chambered model.

If Path A is confirmed, update docs and model naming so the allocator uses explicit ammo/gate semantics rather than pretending a separate `readyShots` source was found.

### Path B: distinct allocator-safe shot-budget source is found

Choose this only if a source with distinct fireable-shot semantics is found.

Document:

- exact type/member/call path;
- runtime meaning;
- update timing relative to `TryFire`, `TryFireCommon`, `FireWeapon`, cooldown, salvo state, and `ChangeAmmoValue`;
- whether the value is per weapon, per module, per salvo, per ship, or per magazine;
- whether it can be safely aggregated into allocator-level `readyShots`.

Only after this documentation should snapshot/allocation code map the source to numeric `readyShots`.

### Path C: numeric shot budget remains absent or ambiguous

This is an acceptable outcome. Keep `readyShots` unknown and revise #6 around weaker per-ship/per-weapon evidence.

In this design, #6 should not ask: "How many fleet-level ready shots can the allocator spend?" Instead it should ask: "For selected player ships and visible weapons, can we attempt a controlled target command, log the intent, and observe the result without breaking vanilla combat?"

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

## Likely code areas if instrumentation is needed

- `CombatLaunchDiagnostics` and launch/snapshot hooks around `MissileWeapon.TryFire`, `TISpaceShipState.FireWeapon`, and `TISpaceCombatProjectileState.Fire(missile)`.
- Snapshot/allocation model fields that currently carry `readyShots`, `readyShotEvidenceSource`, `readinessMissingReason`, `ammoEvidenceSource`, `liveWeaponState`, `readyWeaponCount`, and `unknownReadinessWeaponCount`.
- `tools/parse_player_log.py` readiness summaries and JSON output.

## Suggested implementation order

1. Re-read #15 result docs and confirmed hook notes to preserve the diagnostic-only boundary.
2. Inspect decompiled/runtime areas only enough to decide among Path A, Path B, and Path C.
3. Compare `ammo[weaponData]` with UI-visible ammo/launch availability when possible.
4. Check cases where `ammo[weaponData] > 0` but firing is blocked, and decide whether known gates fully explain them.
5. Record the decision in durable docs before making any #6 command-path changes.
6. If Path A is chosen, document ammo/gate semantics and update any misleading `readyShots` naming.
7. If Path B is chosen, add only narrowly sourced numeric `readyShots` mapping and keep unknown/ammo-only cases explicit.
8. If Path C is chosen, update #6 docs/design to remove numeric fleet-level shot-budget assumptions and describe per-ship/per-weapon command-attempt logging.
9. Keep all #17 changes diagnostic/design-scoped. Live command application belongs in #6.

## Acceptance criteria

- A documented decision chooses Path A, Path B, or Path C.
- Durable docs are updated consistently:
  - `docs/research/readiness-semantics.md`
  - `docs/planning/mvp-roadmap.md`
  - `docs/research/reverse-engineering-plan.md`
  - `docs/diagnostics/snapshot-and-allocation.md`
  - `docs/diagnostics/hooks.md` if runtime evidence changes
- #6 remains blocked unless #17 explicitly documents the safe command-design basis.
- No field is named or treated as `readyShots` without documented semantics.
- If runtime instrumentation changes, a fresh deployed combat log is collected before claiming new runtime semantics.

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

Runtime evidence changes require deploying the mod and collecting a fresh combat log before claiming that new runtime fields are proven.

## Risks

- Treating ammo dictionary values as `readyShots` without validating gates and timing would silently reintroduce the main design bug.
- Assuming a separate loaded/chambered/ready source must exist would also be premature.
- A source name containing `ready`, `loaded`, or `missiles` is not enough; runtime semantics and update timing must be proven.
- Controlled allocation should remain blocked until #17 documents either a numeric shot-budget basis or a no-numeric-budget command-attempt design.
