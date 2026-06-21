# Phase 1: Planning and boundaries

## Goal

Record the implementation boundaries and decisions for Issue #24 before editing
tooling or durable docs.

## Scope

- Capture selected-log path decisions.
- Capture readiness rules from user answers.
- Keep temporary implementation context under `dev-docs/plan/issue_24/`.

## Non-goals

- No runtime code changes.
- No heuristic tuning.
- No generated report artifacts.

## Affected files

- `dev-docs/plan/issue_24/00-master-plan.md`
- `dev-docs/plan/issue_24/01-planning-and-boundaries.md`

## Implementation steps

- Add this plan.
- Keep `00-context.md` as source context without rewriting it.

## Acceptance criteria

- Plan names the default ignored input and output locations.
- Plan records PD-default-only readiness limits.
- Plan preserves the no-live-command boundary.

## Validation commands

```powershell
git status --short
```

## Manual smoke tests

- Confirm no runtime or Core files are changed in this phase.

## Rollback risks

- Low; this phase is temporary documentation only.

## Progress

- Completed.

## Decision log

- `artifacts/combat-logs/selected/` is the default selected-log input path.
- `artifacts/shadow-fitting/latest/` is the default generated output path.

## Outcomes / Retrospective

- Planning boundaries are explicit before implementation.

