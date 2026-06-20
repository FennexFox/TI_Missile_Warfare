# Phase 02: Validation and follow-up gates

## Goal

- Verify the Path A decision, renamed schema, parser, and durable docs against
  #17 acceptance criteria.

## Scope

- Build the C# solution.
- Compile-check the parser.
- Search for stale ready-shot schema usage.
- Record that runtime validation is still required after deploying the renamed
  schema.

## Non-goals

- Do not run deployed-game smoke tests from this repository-only pass.
- Do not implement selected-player command application.
- Do not preserve unpublished old log keys.

## Affected files

- `dev-docs/plan/issue_17/02-verification.md`
- All files changed in Phase 01 for validation status only.

## Implementation steps

- Run `dotnet build TI_Missile_Fire_Control.sln`.
- Run `python -m py_compile tools\parse_player_log.py`.
- Run a text search for stale `readyShots` schema fields and review remaining
  hits as historical or prohibition wording only.
- Update this phase file with validation results.

## Acceptance criteria

- C# build succeeds.
- Parser compiles.
- Current code and schema use `ammoGateBudgetShots`.
- Durable docs choose Path A explicitly.
- #6 remains blocked until selected-player command scope is verified.

## Validation commands

- `dotnet build TI_Missile_Fire_Control.sln`
- `python -m py_compile tools\parse_player_log.py`
- `python tools\check_layout.py`
- `python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py`
- `rg -n "ReadyShots|readyShots|TotalReadyShots|readyShot|ready-shot|ready shots" src tools docs dev-docs`

## Manual smoke tests

- Not run in this pass. A fresh deployed combat log should be captured after
  deploying the schema rename to confirm live `ammoGateBudgetShots` rows.

## Rollback risks

- If verification is skipped, #6 may proceed from stale terminology or a broken
  parser/build.

## Progress

- Completed static validation:
  - `dotnet build TI_Missile_Fire_Control.sln` passed with 0 warnings and 0 errors.
  - `python -m py_compile tools\parse_player_log.py tools\check_layout.py` passed.
  - `python tools\check_layout.py` passed after updating stale required docs paths.
  - `python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py` passed.
  - `rg -n "ReadyShots|readyShots|TotalReadyShots|readyShot|ready-shot|ready shots" src tools` returned no matches.
  - Broader docs search leaves only prohibition wording, validation search strings, or historical context.
  - `phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_17` does not support excluding `00-context.md`; it failed only because that issue-context file is not a phase file.

## Decision log

- No additional design decisions beyond Phase 01.

## Outcomes / Retrospective

- Phase complete. Issue #17 is resolved to Path A in durable docs and current
  code/parser schema uses `ammoGateBudgetShots`.
