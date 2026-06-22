# Phase 03: Documentation and validation

## Goal

- Document #35 diagnostics and complete validation.

## Scope

- Update durable diagnostics/planning docs.
- Run static and fixture validation.
- Record runtime smoke status.

## Non-goals

- No additional code beyond defects found during validation.
- No live command smoke.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_35/*.md`

## Implementation steps

- Document command-candidate schema and parser summary fields.
- State that #35 remains diagnostics-only and still applies zero commands.
- Run fixture parser validation, ruff, compileall, layout, and build.
- Update phase outcomes.

## Acceptance criteria

- Durable docs describe command-candidate rows and safety boundary.
- Validation commands are recorded.
- Runtime smoke limitations are explicit if not run.

## Validation commands

- `python tools\check_layout.py`
- `python tools\parse_player_log.py tools\fixtures\controlled_dry_run_experiment.txt --require-launchlogs --require-snapshots`
- `python tools\parse_player_log.py tools\fixtures\command_resolvability_scope_skip.txt --require-launchlogs --require-snapshots`
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`
- `python -m compileall tools`
- `dotnet build TI_Missile_Fire_Control.sln`

## Manual smoke tests

- Runtime smoke not available in the repository alone. User should verify in game after deployment.

## Rollback risks

- Documentation-only rollback risk is low.

## Progress

- Not started.

## Decision log

- No decisions recorded yet.

## Outcomes / Retrospective

- Not completed yet.
