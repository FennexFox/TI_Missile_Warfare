# Phase 03: Docs and validation

## Goal

- Update durable documentation and run static validation for the new behavior-changing slice.

## Scope

- Document the default-off live apply boundary, reviewed command path, parser fields, validation limits, and #38/#43 follow-up scope.
- Run build, layout, parser, lint, compile, and fixture validation.

## Non-goals

- No private runtime logs committed.
- No claim that a live runtime smoke was performed unless it actually was.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_37/*`

## Implementation steps

- Update docs with #37 command result rows and safety boundary.
- Record validation output in this phase file.
- Record runtime smoke gap or result honestly.

## Acceptance criteria

- Docs state #37 is behavior-changing only when explicitly triggered and allowed.
- Docs identify #38/#43 as future scope expansion.
- Validation confirms the parser fixture has one applied live attempt and zero unknown record types.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\first_live_apply.txt --require-launchlogs --require-snapshots

## Manual smoke tests

- Fresh runtime smoke as described in Phase 02 when the local game environment is available.

## Rollback risks

- Documentation must remain synchronized with parser schema and behavior.

## Progress

- Completed.

## Decision log

- Static validation can prove build and parser behavior, but not actual in-game command effect. Runtime smoke remains required.

## Outcomes / Retrospective

- Updated durable docs for the #37 default-off live apply boundary, reviewed command path, parser output, selected-scope requirement, and future #38/#43 expansion.
- `dotnet build TI_Missile_Fire_Control.sln`: passed with 0 warnings and 0 errors.
- `python tools\check_layout.py`: passed.
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`: passed.
- `python -m compileall tools`: passed.
- `python tools\parse_player_log.py tools\fixtures\first_live_apply.txt --require-launchlogs --require-snapshots`: passed; reported one controlled live apply attempt, one applied command, zero skipped live attempts, zero failed live attempts, zero scope violations, and no unknown record types.
- `python tools\parse_player_log.py tools\fixtures\apply_gate_hard_stop.txt --require-launchlogs --require-snapshots`: passed; #36 hard-stop fixture still reports one blocked gate, zero applied commands, and zero failed commands.
- `python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_37_fixtures`: passed; readiness remains `Not ready` because fixtures are synthetic and no real selected combat log was analyzed.
- `python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_37`: passed.
- Manual runtime smoke was not performed in this environment.
