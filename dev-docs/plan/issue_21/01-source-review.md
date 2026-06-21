# Phase 1: source review and scope proof

## Goal

Prove or reject a vanilla selected-player command scope usable for later command-intent logging and controlled command safety work.

## Scope

- Inspect tactical combat selection state.
- Inspect single-ship and group command-panel recipient construction.
- Inspect vanilla salvo target command/action classes.
- Inspect ownership, AI-control, destroyed, disengaged, and bridge-function filters.

## Non-goals

- No Harmony patches.
- No parser changes.
- No dry-run or live command records.
- No target, fire-mode, ammo, cooldown, projectile, AI, or manual-control mutation.

## Affected files

- `dev-docs/plan/issue_21/01-source-review.md`
- `docs/research/selected-command-scope.md`

## Implementation steps

1. Review source around `SpaceCombatCanvasController` selected ship and group selection fields.
2. Trace `UpdateCommandPanelForSingleShip` and `UpdateCommandPanelForGroup` into ship/fleet command templates.
3. Compare with the fleet-panel path to reject any all-left-hand-combatants interpretation.
4. Trace `SelectSalvoTargetCommand`, `FleetSelectSalvoTargetCommand`, `SetCombatPrimaryTargetAction`, and `SetWeaponModeAction`.
5. Record target identity, ownership filters, command-recipient scope, and weapon/module granularity.

## Acceptance criteria

- Selected combat UI state is separated from command-recipient scope.
- Player-controllable ownership is separated from friendly/allied relation.
- Unselected player ships and AI/friendly allied ships are excluded from the selected command scope.
- Target identity and vanilla salvo command granularity are documented.

## Validation commands

- `git diff --check`

## Manual smoke tests

Manual tactical-combat smoke is not required for this phase because source review proved the recipient and action-input paths.

## Rollback risks

Docs-only. Rollback risk is limited to removing the generated issue notes.

## Progress

- Reviewed source for selected single-ship state, group selection, command panel construction, target selection, command templates, and vanilla action execution.
- Confirmed `selectedFriendlyShipState` and `groupSelectedFriendlyShips` are the selected player-controllable command scope used by the ship command panel.
- Confirmed `leftHandCombatants` is a player-side/all-left-hand combatant list and is not selected-player scope.

## Decision log

- No runtime instrumentation is needed because source clearly traces selected state through command execution.
- Treat vanilla salvo commands as a safe identity reference but not a per-module application primitive.

## Outcomes / Retrospective

Phase 1 verified selected-player command scope sufficiently for #22 dry-run command-intent logging, with the design constraint that vanilla salvo applies at ship/all-salvo-weapons granularity.
