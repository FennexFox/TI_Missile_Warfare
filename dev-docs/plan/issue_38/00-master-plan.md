# Small selected-group controlled experiment report

## Issue Target And Scope Summary

- Issue target: #38
- Title: Small selected-group controlled experiment report
- Source context: GitHub issue #38, `00-context.md`, the #37 phase plan, `docs/diagnostics/snapshot-and-allocation.md`, and `docs/planning/mvp-roadmap.md`
- Scope: expand the default-off controlled command experiment from exactly one selected ship to a small explicitly selected player missile group, while keeping command application one-shot, capped, and auditable.

## Strategy

- Preserve the #37 command path and safety model: `SelectSalvoTargetCommand.OnCommandExecute(TISpaceShipState, CombatTargetableState)` remains the only live command path, and it remains behind controlled diagnostics plus `AllowCommandApply=True`.
- Treat the command-panel selected ship or group-selected ship list as the only live selected-group source. The active-player launcher fallback remains diagnostic only.
- Cap selected group scope at three ships, cap live command attempts at one per selected ship, and cap total live attempts per trigger at three.
- For selected groups larger than one, command only the selected group member whose identity matches the allocator snapshot launcher. This keeps every row attributable to one selected ship and avoids using unselected allocator evidence to command an arbitrary selected group member.
- Keep dry-run/report rows useful when live apply is disabled or when scope is unavailable, empty, mixed-team, too broad, non-player/AI, or ambiguous.
- Extend parser output with selected-group context, live apply counts by experiment and by ship, and visible assigned/spent evidence fields where present.
- Update durable docs to identify #38 as the selected-group safety/fitting step and #43 as the later full-fleet expansion.

## Phase Order

1. [Selected-group implementation and parser reporting](01-implementation.md)
2. [Docs and validation](02-verification.md)

## Phase Dependencies

- Phase 1 depends on resolved issue context and the #37 single-ship apply baseline.
- Phase 2 depends on completion and validation of phase 1.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation source of truth for #38.
- `00-context.md` is input context only.
- Runtime logging source of truth: `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`.
- Parser/report source of truth: `tools/parse_player_log.py`.
- Durable behavior docs belong in `docs/diagnostics/snapshot-and-allocation.md` and `docs/planning/mvp-roadmap.md`.

## Global Validation Expectations

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\selected_group_controlled_apply.txt --require-launchlogs --require-snapshots

## Known Risks And Assumptions

- Static validation cannot prove Terra Invicta runtime selected-group field names or command effects; fresh runtime smoke is required before claiming live success.
- The selected group remains command-panel scoped and capped. This is not #43 fleet-wide eligibility.
- Current runtime logs do not prove missiles spent directly from a controlled command result; parser reporting must distinguish visible assigned shot evidence from unknown spend evidence.
- Experiments can remain armed while waiting for remaining selected group members, but command attempts are still capped per selected ship and per trigger.
