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

- Runtime smoke was run in game on 2026-06-22 with the controlled dry-run
  setting enabled and the UMM trigger pressed three times during combat.

## Rollback risks

- Documentation-only rollback risk is low.

## Progress

- Complete.

## Decision log

- Durable docs describe #34 as diagnostics-only and keep live command
  application blocked.
- Runtime smoke validated the #34 envelope: three explicit triggers paired to
  later shadow allocation cycles and emitted `dryRunExperiment`,
  `dryRunIntent`, and `dryRunResult` rows.
- Selected command-panel scope was unavailable in the runtime smoke. This does
  not invalidate #34; the probe failed closed and logged
  `selectedScopeMissingReason="selectedScopeUnavailable"`.
- Carry this into #35 as a scope-resolver design input: command candidates need
  an explicit, auditable player-controlled command scope before they can become
  eligible, but that scope does not have to be limited to command-panel
  selection if another current-combat active-player missile scope is safely
  verified.

## Outcomes / Retrospective

- Updated diagnostics and roadmap docs.
- Ran parser fixture validation, fitting fixture validation, layout check,
  ruff, compileall, and `dotnet build`.
- Runtime smoke parser verdict: OK, no logger issues.
- Runtime smoke dry-run counts: `dryRunExperiment=3`, `dryRunIntent=3`,
  `dryRunResult=3`, intended commands `3`, skipped commands `0`, applied
  commands `0`, failed commands `0`.
- Runtime smoke experiment ids:
  `dryrun-20260622T013335735Z-1`,
  `dryrun-20260622T013352410Z-2`,
  `dryrun-20260622T013357121Z-3`.
- Runtime smoke selected-scope result: `selectedShipCount="0"` and
  `selectedScopeMissingReason="selectedScopeUnavailable"` for all three
  experiments.
