# Resolve controlled-allocation readiness design after #15

## Issue Target And Scope Summary

- Issue target: #17
- Title: Resolve controlled-allocation readiness design after #15
- Source plan: `dev-docs/plan/issue_17/00-context.md`
- Scope: resolve the controlled-allocation readiness design gate from #11/#15
  diagnostics plus the decompiled-source slice in `../TI_RE_Workspace`.

## Strategy

- Use the decompiled missile fire-control path to choose one of the explicit
  #17 paths.
- Choose Path A: `TISpaceShipState.ammo[weaponData]` plus vanilla fire gates is
  the game-equivalent per-weapon fire budget.
- Rename the mod/Core/parser surface from ambiguous ready-shot terminology to
  explicit `ammoGateBudgetShots` terminology.
- Keep live command application out of this issue; #6 remains blocked on
  selected-player command scope and command-application safety.

## Phase Order

1. [Readiness decision, schema rename, and durable docs](01-decision.md)
2. [Validation and follow-up gates](02-verification.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation plan source of truth.
- Phase files in this directory define phase-local scope and validation.
- `00-context.md` remains the issue-specific context and acceptance criteria
  source for #17.
- Durable conclusions belong under `docs/**`, not only in this temporary plan
  directory.

## Global Validation Expectations

- `dotnet build TI_Missile_Fire_Control.sln`
- `python -m py_compile tools\parse_player_log.py`
- Text search for stale `readyShots` schema usage outside historical notes and
  issue context.

## Known Risks And Assumptions

- Risk: treating `ammoGateBudgetShots` as valid without same-weapon module-keyed
  ammo and live gate evidence would reintroduce the original design bug.
- Risk: selected-player command application can still affect combat if #6 uses
  an unverified command scope.
- Assumption: decompiled source in `../TI_RE_Workspace/decompiled_source` matches
  the runtime version targeted by the current diagnostic work closely enough for
  source-level semantics.

