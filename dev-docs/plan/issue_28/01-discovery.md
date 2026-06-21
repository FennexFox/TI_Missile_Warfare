# Phase 01: Context and source review

## Goal

Confirm current parser, fitting, and documentation semantics before changing
the report surface.

## Scope

- Read `00-contexts.md` and current related docs.
- Inspect `tools/fit_shadow_allocation.py` and `tools/parse_player_log.py`.
- Identify which Issue #28 statuses can be derived from existing fitting data
  and which must be documented static gates.

## Non-goals

- No code changes in this phase.
- No reclassification of fitting allocation outcomes.
- No live command or allocator scoring changes.

## Affected files

- `dev-docs/plan/issue_28/`

## Implementation steps

- Read the required context and existing plan/docs.
- Compare current fitting output to Issue #28 acceptance criteria.
- Decide on additive reporting shape before implementation.

## Acceptance criteria

- Current source of truth files have been inspected.
- The implementation target is limited to additive sufficiency reporting and
  docs wording.
- The plan distinguishes parser completeness, fitting baseline readiness,
  evidence sufficiency, and command safety.

## Validation commands

- python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_28_sufficiency
- python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_28_synthetic
- python -m compileall tools
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_28

## Manual smoke tests

- Review planned status vocabulary against Issue #28 inputs.

## Rollback risks

- None beyond reverting plan documentation.

## Progress

- Completed.

## Decision log

- Use aggregate `evidence_sufficiency` output rather than changing parser OK or
  `readiness_verdict`.
- Treat `observedTargetWeaponTemplates` as `presenceOnly`, not calibrated PD
  capability.

## Outcomes / Retrospective

- Current code has baseline fitting verdicts and limitations but no distinct
  evidence-sufficiency gate. Issue #28 should fill that reporting gap.
