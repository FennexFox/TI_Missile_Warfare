# Selected command scope

Issue #21 verifies selected-player command scope sufficiently for #22 dry-run command-intent logging.

The safe later scope is the tactical ship command panel's selected ship or group-selected ship list. Do not use the left-hand fleet/all-combatants list as selected-player scope.

## Inspected source

The review inspected these decompiled Terra Invicta classes and methods:

- `SpaceCombatCanvasController.SetupShipLists`
- `SpaceCombatCanvasController.OnCombatTargetableStateSelected`
- `SpaceCombatCanvasController.NewFriendlyShipSelected`
- `SpaceCombatCanvasController.HandleGroupSelect`
- `SpaceCombatCanvasController.SelectPrimaryShip`
- `SpaceCombatCanvasController.UpdateCommandPanelForSingleShip`
- `SpaceCombatCanvasController.UpdateCommandPanelForGroup`
- `SpaceCombatCanvasController.UpdateFleetCommandPanel`
- `SelectSalvoTargetCommand`
- `FleetSelectSalvoTargetCommand`
- `SelectTargetCommand`
- `FleetSelectTargetCommand`
- `TIShipCommandTemplate`
- `TIFleetCommandTemplate`
- `TICommandTargetableTargeting`
- `TICommandTargeting`
- `SetCombatPrimaryTargetAction`
- `SetWeaponModeAction`
- `ShipWeaponUIController`
- `TISpaceShipState.AllWeaponModuleData`
- `TISpaceShipState.AnyOffensiveMissileWeaponCanFire`
- `TISpaceShipState.CanPerformShipCommands`

## Selected player scope

`SpaceCombatCanvasController` tracks single selection with `selectedFriendlyShip` and `selectedFriendlyShipState`. It tracks multi-selection with `groupSelectedFriendlyShips`.

The selection event path only promotes a combat ship into friendly selection when the selected `TISpaceShipState` belongs to `base.activePlayer`. That is stricter than a friendly or allied relation. It excludes enemy ships, allied non-player ships, and player-side ships that were not selected.

The single-ship command panel executes commands against `selectedFriendlyShipState`. When a command requires a target, it calls the command's targeting setup with `selectedFriendlyShipState`; otherwise it executes the command against that same ship.

The group command panel builds a recipient list from `groupSelectedFriendlyShips`, filtering out null, destroyed, and disengaged ships. Targeted group commands receive that selected list. Non-targeted group commands execute against that selected list.

This is the selected-player command scope later #22 work should log: one selected player ship, or the explicitly group-selected player ships.

## Unsafe broad fleet scope

`SetupShipLists` assigns `leftHandFaction` to the active player faction when the active player participates in the combat. It then builds `leftHandCombatants` from that side's active combatants.

That list is useful for player-side UI layout, but it is not current selection. `UpdateFleetCommandPanel` can build command recipients from `leftHandCombatants.Keys`, which means all active player-side ships rather than the selected ship or selected group.

Later #6/#22/#23 work must not treat `leftHandCombatants`, the left-hand fleet controller, or fleet-panel commands as selected-player scope.

## Command authority filters

`TIShipCommandTemplate.CommandVisibleToActor` filters out ships under combat AI control and ships that cannot perform ship commands. `TIFleetCommandTemplate.CommandVisibleToPlayer`, `PlayerCanIssueCommand`, and `GetEligibleShips` similarly filter candidate ships by combat AI control and `CanPerformShipCommands`.

`CanPerformShipCommands` requires a ship that is not destroyed and has a functioning bridge above the vanilla threshold. `FleetSelectSalvoTargetCommand.PlayerCanIssueCommand` further requires at least one selected eligible ship that is not disengaged and has an offensive missile weapon that can fire.

These filters are command eligibility checks, not selection checks. The selected-recipient proof still comes from the command panel passing `selectedFriendlyShipState` or `groupSelectedFriendlyShips`.

## Vanilla salvo command path

`SelectSalvoTargetCommand` takes a `TISpaceShipState` and target `CombatTargetableState`. It starts `SetCombatPrimaryTargetAction` for that ship and target, then starts `SetWeaponModeAction` for every weapon on that ship whose available modes include `Salvo`.

`FleetSelectSalvoTargetCommand` reuses the ship command template for each eligible ship in the selected group. The group path therefore applies the same ship-level behavior independently to each selected eligible ship.

The vanilla salvo command granularity is ship-level and all salvo-capable weapons on that ship. It is not a command for one visible missile module. That is a design constraint for #22/#23 and later #6 work.

## Target identity

`TICommandTargetableTargeting` stores either one selected ship or a selected ship list plus the command object. It derives possible targets as `CombatTargetableState` objects, excluding destroyed combatants and applying the command's friendly-target flags. For salvo commands, friendly targets are not included.

When the player selects a valid target, the targeting controller passes that `CombatTargetableState` to the ship or fleet command. `SetCombatPrimaryTargetAction` stores the source ship ID and target state ID, then resolves both from the active combat lookup during execution before setting the ship's primary combat target.

This target identity is specific enough for #22 dry-run logging: log the selected ship identity, selected target `CombatTargetableState` identity, and the command-intent target label before any later live command work is considered.

## Weapon and module identity

Visible weapon rows for the selected ship are built from the selected ship controller's weapons. `ShipWeaponUIController` stores the exact `Weapon` and its `weaponData`, and `TISpaceShipState.AllWeaponModuleData` exposes nose and hull weapon module data.

That means visible module identity can be tied to the selected ship where the UI has a selected ship panel. However, the vanilla salvo target command does not use one exact visible module as its recipient. It changes every salvo-capable weapon on the ship.

Later command-intent logs should therefore distinguish:

- selected ship identity;
- visible module identity, when the dry-run intent is motivated by a specific recommendation;
- vanilla command granularity, which is broader than one visible module for salvo target commands.

## Handoff to #22

Issue #21 verifies selected-player command scope sufficiently for #22 dry-run command-intent logging.

#22 can proceed using the single selected ship and group-selected ship command panel scopes, with explicit logs showing selected ship IDs, target IDs, visible module IDs when available, recommended `ammoGateBudgetShots`, and skipped reasons.

#22 should not invoke `SelectSalvoTargetCommand`, `FleetSelectSalvoTargetCommand`, `SetCombatPrimaryTargetAction`, `SetWeaponModeAction`, or equivalent live actions. #23 remains the first place to consider a tightly gated live smoke.

## Non-goals confirmed

No source changes, parser changes, Harmony patches, command invocations, target assignment mutations, weapon-mode mutations, ammo mutations, cooldown mutations, projectile mutations, AI-control mutations, or manual-control changes are needed for #21.
