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

## Why #21 is the right standalone unit

Issue #17 resolved the shot-budget semantics to Path A: `TISpaceShipState.ammo[weaponData]` plus vanilla fire gates is the game-equivalent per-weapon fire budget for the observed fire decision. The mod names this explicit derived value `ammoGateBudgetShots`; it is not a separate loaded/chambered/ready-shot source.

After #17, the remaining controlled-allocation blocker is not shot budgeting. It is command scope and command safety. #21 is the first half of that blocker: selected-player scope must be verified before any dry-run or live command path can be trusted.

## Current repo state observed for this plan

- Repo id: `ti-missile-warfare`
- Branch observed while preparing this context: `issue_21_22_23`
- Local head observed: `4b583392b8286db510e08043d0e00c123bc57dd9`
- Worktree was clean before initial plan files were generated.

If continuing with #21-only work, prefer renaming/recreating the local branch to an issue-21-specific branch before implementation, for example `issue_21` or `issue_21_selected_scope`.

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

## Primary source-review targets

Prioritize the command/action and selection flow around:

- `SelectSalvoTargetCommand`
- `FleetSelectSalvoTargetCommand`
- `SetCombatPrimaryTargetAction`
- `SetWeaponModeAction`
- tactical combat selection/controller classes that feed those commands/actions

## Questions #21 must answer

- Which runtime object/list represents explicitly selected player-controlled ships?
- How is player ownership/faction distinguished from AI ships?
- How are unselected player ships excluded?
- Can visible missile weapon/module identity be tied to the selected ship?
- What target identity is passed to the vanilla command/action path?
- Is the command/action path usable later for #22 dry-run intent logging and #23 minimal live smoke?

## Acceptance criteria for this branch/PR

- Source review identifies the vanilla selected-player command/action path or records why it is not usable.
- Selected friendly ship identity can be distinguished from AI ships and unselected player ships.
- Visible missile weapon/module identity can be tied to the selected ship where available.
- Target identity passed to the vanilla command path is understood enough for a later dry-run/apply phase.
- Durable docs state whether #6 can proceed to #22 dry-run command-intent logging.
- Durable docs cite inspected classes/methods.

## Manual validation policy

Manual tactical-combat smoke is not automatically required for #21.

Source-review-only completion is acceptable if the decompiled source clearly proves selected-player scope, ownership filtering, unselected-player exclusion, and command/action input identity.

Manual diagnostics-only validation is required if any of those are ambiguous. In that case, validate:

1. Enter tactical combat.
2. Select one or a small number of friendly missile ships.
3. Trigger or observe the selection diagnostics.
4. Confirm logs include selected player ships only.
5. Confirm unselected player ships are excluded.
6. Confirm AI ships are excluded.
7. Confirm weapon/module identity is attached when visible.
8. Confirm target identity is visible enough for a later dry-run/apply phase.
9. Confirm no target, fire mode, launch, ammo, cooldown, projectile, AI, or manual-control behavior changes occur.

## Non-goals

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
