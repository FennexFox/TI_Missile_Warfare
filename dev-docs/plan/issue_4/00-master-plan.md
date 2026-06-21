# Shadow allocation policy and decision logging cleanup

## Issue Target And Scope Summary

- Issue target: #4
- Title: Shadow allocation policy and decision logging cleanup
- Source plan: GitHub issue #4 and the 2026-06-21 owner cleanup comment.
- Scope: close the remaining Issue #4 cleanup items after PR #20 by making
  no-op shadow decisions explicit in logs/parser output, refreshing durable
  docs to current ammo/gate-budget terminology, and validating the
  observation-only diagnostics path.

## Strategy

- Keep the implementation narrow. Preserve the existing shadow-allocation
  runtime path and add only diagnostic records/reporting needed to explain
  skipped or no-op cycles.
- Do not add command application, target assignment, fire-mode mutation, launch
  suppression, AI behavior changes, or player-control changes.

## Phase Order

1. [No-op logging, parser separation, and docs cleanup](01-cleanup.md)
2. [Validation and issue closure checks](02-verification.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation plan source of truth.
- Phase files in this directory define phase-local scope and validation.
- Current shot-budget terminology is `ammoGateBudgetShots` /
  `totalAmmoGateBudgetShots`; remaining `readyShots` mentions are allowed only
  as explicit historical or negative guardrail wording.
- `dev-docs/plan/issue_21/` is unrelated user work in this checkout and must
  not be staged or modified for Issue #4.

## Global Validation Expectations

- dotnet build TI_Missile_Fire_Control.sln
- python tools/check_layout.py
- python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py
- python -m compileall tools
- .\\build.ps1
- python tools/parse_player_log.py --require-launchlogs --require-snapshots

## Known Risks And Assumptions

- The current branch is `issue_21`, but the requested work is Issue #4 cleanup.
  Stage only Issue #4 files if committing.
- Live tactical smoke cannot be reproduced unless Terra Invicta is available
  and the mod is deployed; parser validation against the active `Player.log`
  is the local substitute.
