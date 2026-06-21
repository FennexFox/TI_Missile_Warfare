# Issue #21 master plan: selected-player command scope

## Issue Target And Scope Summary

- GitHub issue: #21, `Verify selected-player command scope for #6`
- Parent blocker: #6, controlled auto-allocation command application
- Scope: source-review and documentation only unless source is insufficient.

Issue #21 answers whether later #22/#23 work can use a vanilla Terra Invicta command scope that is both explicitly selected and player-controllable. It must not implement dry-run command intent logging, live command application, target mutation, fire-mode mutation, launch suppression, ammo mutation, or allocation command execution.

## Strategy

Review the decompiled tactical-combat selection and command paths, then document the verified boundaries in durable repo docs. The review focuses on:

- selected single-ship state versus group-selected ship state;
- current human player ownership/faction checks versus friendly/allied relation;
- actual command recipient object/list passed to ship and fleet command templates;
- target identity passed to vanilla command/actions;
- visible weapon/module identity and whether vanilla salvo commands operate per module or broader than that.

No runtime diagnostics are planned because the inspected source is sufficient to answer the issue acceptance criteria.

## Phase Order

1. Source review and scope proof.
2. Durable documentation and validation.

## Phase Dependencies

Phase 2 depends on Phase 1 findings. No phase depends on code changes.

## Source Of Truth Decisions

- `dev-docs/plan/issue_21/00-context.md` is the issue-specific context file for this branch.
- Durable conclusions belong in `docs/research/selected-command-scope.md`, with summary links from roadmap and reverse-engineering docs.
- The selected-player scope for later dry-run work is the command panel's single selected ship or group-selected ship list, not the left-hand fleet/all-combatants list.
- Vanilla salvo command granularity is ship-level/all salvo-capable weapons on the ship, not a specific visible weapon/module.

## Global Validation Expectations

- `python C:/Users/techn/.codex/skills/phased-issue-implementation/scripts/phase_plan_helper.py validate --plan-dir dev-docs/plan/issue_21`
- `python tools/check_layout.py`
- `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py`
- `python -m compileall tools`
- `dotnet build TI_Missile_Fire_Control.sln`
- `git diff --check`

## Known Risks And Assumptions

- This branch relies on decompiled source review rather than runtime smoke. That is acceptable because the selection, command-recipient, and action-input paths are explicit in source.
- Later #22/#23 work must not treat `leftHandCombatants` or fleet-panel commands as selected-player scope.
- Later #6 design must account for vanilla salvo granularity being broader than per visible missile module.
