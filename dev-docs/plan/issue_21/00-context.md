# Issue #21 context: selected-player command scope for #6

## Issue target

- GitHub issue: #21, `Verify selected-player command scope for #6`
- Parent blocker: #6, `Controlled allocation experiment loop`
- Follow-up issues intentionally out of this branch/PR:
  - #22: dry-run command intent logging
  - #23: live command safety gate

## Scope verdict

Issue #21 should be handled as a narrow reverse-engineering and documentation pass. It may add diagnostics-only instrumentation if source review is insufficient, but it should not implement dry-run command intent logging or live command application.

This branch/PR should answer one question:

> Which Terra Invicta selected-player ship/weapon command scope can Issue #6 safely use later?

If that question cannot be answered from source review or diagnostics-only evidence, #21 should close with a documented blocker rather than falling forward into #22 or #23.

## Scope distinctions Codex must preserve

Do not collapse these into one vague "selected friendly ship" concept:

- tactical-combat UI selection or focus;
- explicit multi-selected ship/combatant list;
- current human player's controllable faction/team/ownership;
- friendly or allied relation to the player;
- the actual command-recipient object/list passed to vanilla actions.

For #21, finding a selected combat object is not enough. Finding a friendly or allied combat object is not enough. The plan must ask Codex to prove, or explicitly fail to prove, that the command-recipient scope is both selected and player-controllable, and that unselected player ships plus friendly/AI ships are excluded.

## Why #21 is the right standalone unit

Issue #17 resolved the shot-budget semantics to Path A: `TISpaceShipState.ammo[weaponData]` plus vanilla fire gates is the game-equivalent per-weapon fire budget for the observed fire decision. The mod names this explicit derived value `ammoGateBudgetShots`; it is not a separate loaded/chambered/ready-shot source.

After #17, the remaining controlled-allocation blocker is not shot budgeting. It is command scope and command safety. #21 is the first half of that blocker: selected-player scope must be verified before any dry-run or live command path can be trusted.

### Prior evidence boundary

Prior #17 documentation already reviewed parts of `SelectSalvoTargetCommand` for shot-budget semantics and vanilla command consequences. Do not treat that as sufficient proof of selected-player scope. #21 must independently trace the selection/controller source that feeds the command/action path, the ownership/faction filter, and the actual command recipient list.

## Current repo state observed for this plan

- Repo id: `ti-missile-warfare`
- Branch observed while preparing this context: `issue_21`
- Local head observed: `8199e1a447d08c01661e8f34ffda0f0f540a9201`
- Worktree contained this updated context file when the document was refreshed.

## Source and documentation location

Decompiled source of Terra Invicta is in `../TI_RE_Workspace`. You can refer to the graph slice in `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master` for a visual overview of the most relevant classes and methods to review for #21. Do not include decompiled source in this repo.

## Existing local surfaces that matter

### Settings and UI

`src/MissileFireControl.Mod/ModSettings.cs` currently has diagnostics, snapshot, shadow allocation, recommendation-only, launch-discipline, and launch-score settings. It does not have a #22 dry-run trigger or a #23 live-smoke safety gate.

For #21, that is fine. Do not add #22/#23 controls in this branch unless a tiny diagnostics-only selection probe needs an enable flag.

### Current Harmony patch bootstrap

`src/MissileFireControl.Mod/Patches/PatchBootstrap.cs` currently patches diagnostics around:

- `TISpaceShipState.FireWeapon(...)` postfix
- `PavonisInteractive.TerraInvicta.Ship.MissileWeapon.TryFire(DateTime)` prefix/postfix
- `TISpaceCombatProjectileState.Fire(... TIMissileTemplate ...)` postfix

For #21, add new patch points only if source review cannot prove selected-player scope. If a patch is added, it must be diagnostics-only and documented with:

- inspected game class and method;
- prefix/postfix choice;
- stability rationale;
- why it cannot mutate combat behavior;
- exact log fields used to distinguish selected player ships from unselected player ships and AI ships.

### Parser support

`tools/parse_player_log.py` already has future live-command buckets for applied/skipped/failed command-like allocation records. #21 should not depend on those categories.

If #21 adds selection diagnostics, either:

- keep them as simple diagnostic log lines outside `[AllocationLog]`; or
- add only minimal parser support needed to summarize selection-scope evidence.

Do not add #22 dry-run record categories in this branch.

Prefer keeping #21 selection evidence outside `[AllocationLog]` unless parser support is strictly necessary. A dedicated diagnostics prefix such as `[SelectionScopeLog]` or `[CommandScopeLog]` is safer than reusing future command-application buckets. Do not emit `applied`, `skipped`, `failed`, or command-intent allocation records for #21.

## Primary source-review targets

Prioritize the command/action and selection flow around:

- `SelectSalvoTargetCommand`
- `FleetSelectSalvoTargetCommand`
- `SetCombatPrimaryTargetAction`
- `SetWeaponModeAction`
- tactical combat selection/controller classes that feed those commands/actions

Also trace both upstream and downstream of those classes:

- upstream UI/controller state that records focus versus multi-selection;
- ownership/faction/team checks that distinguish player-controllable ships from friendly or AI ships;
- the exact recipient object/list passed into the command/action constructor or execution path;
- whether the action applies at ship level, fleet/selection level, weapon group level, or visible weapon/module level.

## Questions #21 must answer

- Which runtime object/list represents explicitly selected combat ships, and is it UI focus, multi-selection, or the actual command-recipient list?
- Which field/method proves current human player ownership, faction, team, or command authority, distinct from friendly/allied relation?
- How are unselected player ships excluded?
- How are friendly/allied AI ships excluded?
- Can visible missile weapon/module identity be tied to the selected ship?
- What command granularity does vanilla use: ship, fleet/selection, all offensive missile weapons, weapon group, or a specific visible weapon/module?
- If vanilla command granularity is broader than #6's intended per-weapon allocation, is that a blocker or a design constraint for #22/#23?
- What target object/type/identity is passed to the vanilla command/action path?
- Can that target identity be connected to the existing snapshot/projectile target identity well enough for later dry-run intent logging?
- Is the command/action path usable later for #22 dry-run intent logging and #23 minimal live smoke?

## Acceptance criteria for this branch/PR

- Source review identifies the vanilla selected-player command/action path or records why it is not usable.
- Selected combat UI state, player command authority, friendly/allied relation, and actual command-recipient scope are not conflated.
- Selected player ship identity can be distinguished from AI ships, friendly/allied AI ships, and unselected player ships.
- Visible missile weapon/module identity can be tied to the selected ship where available.
- Vanilla command granularity is documented: ship, fleet/selection, weapon group, all offensive missile weapons, or specific visible weapon/module.
- Target object/type/identity passed to the vanilla command path is understood enough for a later dry-run/apply phase.
- Durable docs state whether #6 can proceed to #22 dry-run command-intent logging, or whether command granularity/selection scope remains a blocker.
- Durable docs cite inspected classes/methods.

## Manual validation policy

Manual tactical-combat smoke is not automatically required for #21.

Source-review-only completion is acceptable if the decompiled source clearly proves selected-player scope, ownership filtering, unselected-player exclusion, and command/action input identity.

Source-review-only completion should still document negative evidence and rejected interpretations, especially if a discovered selection list is only UI focus, only friendly ships, or not the actual command-recipient list.

Manual diagnostics-only validation is required if any of those are ambiguous. In that case, validate:

1. Enter tactical combat.
2. Select one or a small number of friendly missile ships.
3. Trigger or observe the selection diagnostics.
4. Confirm logs include selected player ships only.
5. Confirm unselected player ships are excluded.
6. Confirm AI ships are excluded.
7. Confirm weapon/module identity is attached when visible.
8. Confirm target identity is visible enough for a later dry-run/apply phase.
9. Confirm no-selection, single-selection, multi-selection, unselected-friendly-present, AI/enemy-present, and non-missile-selected cases if practical.
10. Confirm no target, fire mode, launch, ammo, cooldown, projectile, AI, or manual-control behavior changes occur.

## Non-goals

Before finishing #21, inspect the diff for accidental command-application APIs, target assignment, fire-mode mutation, launch suppression, ammo mutation, AI behavior changes, or manual-control mutation.

- Do not implement #22 dry-run command intent logging.
- Do not implement #23 live command smoke.
- Do not implement #6 controlled allocation.
- Do not invoke `SelectSalvoTargetCommand`, `FleetSelectSalvoTargetCommand`, `SetCombatPrimaryTargetAction`, `SetWeaponModeAction`, or equivalent live actions.
- Do not mutate target assignment, weapon mode, ammo, cooldown, projectile state, selected state, AI behavior, or manual control.
- Do not revive ambiguous `readyShots` terminology.

## Durable docs likely to update

- `docs/planning/mvp-roadmap.md`
- `docs/research/reverse-engineering-plan.md`
- `docs/diagnostics/hooks.md` if new patch points are added
- `docs/diagnostics/runtime-validation-history.md` only if runtime smoke evidence is collected

## Validation expectations

If #21 remains documentation/source-review only, validation may be limited to diff inspection and durable-doc consistency. If code or parser changes are added, run the normal local checks where feasible:

- `dotnet build TI_Missile_Fire_Control.sln`
- `python tools/check_layout.py`
- `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py`
- `python tools/parse_player_log.py --require-launchlogs` if parser behavior or runtime log interpretation changed

Do not stage or commit unrelated work. The current `00-context.md` may already be staged in the local checkout; preserve user-authored/staged context instead of folding it into unrelated implementation changes.

## Follow-up branch split

After #21 is complete:

- Create a separate branch/PR for #22 using the verified selected scope.
- Create another separate branch/PR for #23 after #22 runtime dry-run evidence is available.

#21 should leave a clear handoff sentence for #22, for example:

```text
Issue #21 verifies selected-player command scope sufficiently for #22 dry-run command-intent logging.
```

or:

```text
Issue #21 did not verify a safe selected-player command scope; #22/#23 should remain blocked pending the documented gap.
```

## Goal

Provide the issue-specific source context and acceptance boundary for verifying selected-player command scope for #6.

## Scope

- Define the #21 source-review and documentation boundary.
- Preserve the distinction between selected combat objects, player-controllable faction ownership, friendly/allied relation, and command recipients.
- List the source classes, acceptance criteria, validation expectations, and follow-up branch split.

## Non-goals

- Do not implement #22 dry-run command intent logging.
- Do not implement #23 live command smoke.
- Do not implement #6 controlled allocation.
- Do not mutate target assignment, weapon mode, ammo, cooldown, projectile state, selected state, AI behavior, or manual control.

## Affected files

- `dev-docs/plan/issue_21/00-context.md`
- `dev-docs/plan/issue_21/00-master-plan.md`
- `dev-docs/plan/issue_21/01-source-review.md`
- `dev-docs/plan/issue_21/02-docs-validation.md`
- `docs/research/selected-command-scope.md`
- `docs/research/reverse-engineering-plan.md`
- `docs/planning/mvp-roadmap.md`
- `docs/README.md`
- `docs/maintenance/assumption-audit.md`

## Implementation steps

1. Use this context as the issue-specific source of truth.
2. Review the decompiled source paths named above.
3. Document selected-player command scope and vanilla salvo granularity.
4. Update durable docs and run validation.

## Acceptance criteria

- The branch answers whether #6 can proceed to #22 dry-run command-intent logging.
- Selected-player scope is not conflated with friendly/allied or broad fleet-side scope.
- Vanilla target and weapon granularity are documented.

## Validation commands

- `python C:/Users/techn/.codex/skills/phased-issue-implementation/scripts/phase_plan_helper.py validate --plan-dir dev-docs/plan/issue_21`
- `python tools/check_layout.py`
- `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py`
- `python -m compileall tools`
- `dotnet build TI_Missile_Fire_Control.sln`
- `git diff --check`

## Manual smoke tests

Manual tactical-combat smoke is not required if source review proves selected-player command scope. Runtime diagnostics-only validation is required only if source review is ambiguous.

## Rollback risks

Docs-only. Rollback risk is limited to removing issue-context and documentation updates.

## Progress

- Context updated for Issue #21 scope and acceptance boundaries.
- Source review completed without requiring runtime instrumentation.

## Decision log

- Preserve `00-context.md` as the context document referenced by the user and issue plan.
- Keep #21 documentation-only because the decompiled source proves command-recipient scope.

## Outcomes / Retrospective

This context file supported a source-review-only completion path for #21. Durable conclusions are recorded in `docs/research/selected-command-scope.md`.
