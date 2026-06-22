# Phase 03: Docs validation and smoke

## Goal

- Document the #34 dry-run envelope and complete static/parser validation.

## Scope

- Update durable diagnostics/roadmap docs.
- Run static and fixture validation.
- Record manual smoke status.

## Non-goals

- No additional runtime schema work beyond defects found during validation.
- No live command smoke unless explicitly safe and available.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_34/*.md`

## Implementation steps

- Document dry-run record types, safety boundary, and parser summary fields.
- Run fixture parser validation.
- Run layout, ruff, compileall, and build where possible.
- Update phase progress/outcomes.

## Acceptance criteria

- Durable docs state #34 remains diagnostics-only.
- Validation commands are recorded.
- Manual runtime smoke limitations are explicit if not run.

## Validation commands

- `python tools\parse_player_log.py tools\fixtures\controlled_dry_run_experiment.txt --require-launchlogs --require-snapshots`
- `python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_34_fixtures`
- `python tools\check_layout.py`
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`
- `python -m compileall tools`
- `dotnet build TI_Missile_Fire_Control.sln`

## Manual smoke tests

- Runtime smoke not available in the repository alone. User should verify in game with the steps from Phase 02.

## Rollback risks

- Documentation-only rollback risk is low.

## Progress

- Complete.

## Decision log

- Durable docs describe #34 as diagnostics-only and keep live command
  application blocked.
- Runtime smoke was not run in this repository-only pass; the fixture proves
  parser grouping, not in-game selected-scope visibility.

## Outcomes / Retrospective

- Updated diagnostics and roadmap docs.
- Ran parser fixture validation, fitting fixture validation, layout check,
  ruff, compileall, and `dotnet build`.
