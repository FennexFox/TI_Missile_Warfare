# Phase 2: durable documentation and validation

## Goal

Capture Issue #21 findings in durable docs and verify the branch remains documentation-only and buildable.

## Scope

- Add a durable selected-command-scope research note.
- Update roadmap and reverse-engineering docs.
- Update documentation entry points and assumption audit.
- Run local validation commands.

## Non-goals

- No source, parser, or runtime instrumentation changes.
- No #22 dry-run command intent logging.
- No #23 live command smoke gate.
- No #6 controlled allocation implementation.

## Affected files

- `docs/research/selected-command-scope.md`
- `docs/research/reverse-engineering-plan.md`
- `docs/planning/mvp-roadmap.md`
- `docs/README.md`
- `docs/maintenance/assumption-audit.md`
- `dev-docs/plan/issue_21/00-master-plan.md`
- `dev-docs/plan/issue_21/02-docs-validation.md`

## Implementation steps

1. Add a durable research note with inspected classes/methods and findings.
2. Update durable docs to link the new note and revise blocker language.
3. Verify no source files changed.
4. Run layout, Python, build, and diff validation.

## Acceptance criteria

- Durable docs state whether #6 can proceed to #22.
- Durable docs cite inspected classes/methods.
- Docs preserve the distinction between selected player scope, friendly/allied combatants, and broad fleet-panel scope.
- Validation commands pass or any failures are documented.

## Validation commands

- `python C:/Users/techn/.codex/skills/phased-issue-implementation/scripts/phase_plan_helper.py validate --plan-dir dev-docs/plan/issue_21`
- `python tools/check_layout.py`
- `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py`
- `python -m compileall tools`
- `dotnet build TI_Missile_Fire_Control.sln`
- `git diff --check`

## Manual smoke tests

Manual tactical-combat smoke is not required because no runtime patch or gameplay code changed.

## Rollback risks

Docs-only. Rollback risk is limited to reverting the documentation updates.

## Progress

- Added `docs/research/selected-command-scope.md`.
- Updated roadmap, reverse-engineering plan, docs README, and assumption audit.
- Ran all planned validation commands.

## Decision log

- Kept Issue #21 documentation-only because source review was sufficient.
- Preserved `dev-docs/plan/issue_21/00-context.md` as the user-facing context file even though the phase-plan helper reports numbering warnings for it.

## Outcomes / Retrospective

- `phase_plan_helper.py validate` passed with numbering warnings caused by the preserved `00-context.md`.
- `python tools/check_layout.py` passed.
- `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py` passed.
- `python -m compileall tools` passed.
- `dotnet build TI_Missile_Fire_Control.sln` passed with 0 warnings and 0 errors.
- `git diff --check` passed.
