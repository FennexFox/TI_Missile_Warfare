# Phase 02: Docs and validation

## Goal

- Update durable documentation and run static validation for the selected-group controlled experiment.

## Scope

- Document #38 selected-group behavior and #43 fleet-wide boundary.
- Record validation commands and any runtime smoke gaps.
- Keep PR-visible docs honest about default-off behavior and missing live smoke.

## Non-goals

- No new behavior beyond Phase 01.
- No PR creation unless separately requested.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_38/01-implementation.md`
- `dev-docs/plan/issue_38/02-verification.md`

## Implementation steps

- Update diagnostics docs with selected-group caps and parser report fields.
- Update roadmap wording so #38 is the selected-group rung and #43 remains the full-fleet path.
- Run validation commands from Phase 01.
- Record validation results and any manual smoke not run.

## Acceptance criteria

- Durable docs do not imply selected-subgroup allocation is the final #6 design.
- Validation results are recorded in the plan.
- Any missing runtime smoke is explicit.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\selected_group_controlled_apply.txt --require-launchlogs --require-snapshots

## Manual smoke tests

- Same selected-group runtime smoke listed in Phase 01.

## Rollback risks

- Documentation can be reverted independently if Phase 01 is reverted.

## Progress

- Completed.

## Decision log

- Static validation can prove build, schema, parser, and fixture behavior only. Fresh Terra Invicta runtime smoke is still required before claiming selected-group live combat validation.
- Durable docs explicitly describe #38 as a selected-group safety/fitting rung and #43 as the fleet-wide expansion path.

## Outcomes / Retrospective

- Updated diagnostics and roadmap documentation for selected-group caps, parser report fields, and the #43 boundary.
- Validation passed:
  - `dotnet build TI_Missile_Fire_Control.sln`
  - `python tools\check_layout.py`
  - `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`
  - `python -m compileall tools`
  - `python tools\parse_player_log.py tools\fixtures\selected_group_controlled_apply.txt --require-launchlogs --require-snapshots`
- Manual runtime smoke was not run in this environment.
