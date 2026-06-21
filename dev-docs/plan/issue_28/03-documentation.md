# Phase 03: Document readiness semantics

## Goal

Document how to interpret the new sufficiency gate and update durable #6
readiness language.

## Scope

- Update diagnostic report documentation.
- Update runtime-validation history for the Issue #30 result under Issue #28.
- Update the roadmap's current missing/provisional inputs and #6 gates.
- Update phase progress and outcomes.

## Non-goals

- No broad docs reorganization.
- No generated artifact commits.
- No issue tracker writes unless explicitly requested later.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_28/`

## Implementation steps

- Add report interpretation for evidence sufficiency statuses.
- Record that `Ready for #6 baseline` remains true for fitting while
  controlled live command readiness remains blocked.
- Ensure roadmap wording distinguishes hard blockers from provisional evidence
  limits.

## Acceptance criteria

- Docs distinguish no missing parser fields from insufficient model fidelity.
- Docs name observed target PD as presence-only/provisional.
- Docs keep #23/#6 live command safety separate from fitting readiness.

## Validation commands

- python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_28_sufficiency
- python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_28_synthetic
- python -m compileall tools
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_28

## Manual smoke tests

- Review docs diff for consistency with generated report wording.

## Rollback risks

- Reverting docs would make generated sufficiency output less discoverable.

## Progress

- Completed.

## Decision log

- Durable docs should cite the generated sufficiency gate rather than implying
  parser OK, empty `missingInputs`, or fitting readiness is enough for live #6.
- Roadmap language keeps Issue #29, command-intent logging, vanilla command
  granularity, and live safety as separate follow-up gates.

## Outcomes / Retrospective

- `docs/diagnostics/snapshot-and-allocation.md` documents the status
  vocabulary and report interpretation.
- `docs/diagnostics/runtime-validation-history.md` records the Issue #28
  four-log rerun and per-input statuses.
- `docs/planning/mvp-roadmap.md` now distinguishes fitting baseline readiness
  from evidence-quality limitations and live command safety.
