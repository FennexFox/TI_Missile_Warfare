# Phase 01: Plan absorption and source of truth

## Goal

- Reconcile `dev-docs/plan/tuning_loop/` with #60 and make this directory the
  active local implementation plan for closing the archived-log offline fitting
  loop.

## Scope

- Identify the relationship between the tuning-loop notes and #60.
- Preserve useful planning material from the tuning-loop folder in this phased
  issue plan.
- Mark the tuning-loop folder as historical absorbed input.
- Keep durable project direction in `docs/planning/offline-fitting-loop.md`
  rather than duplicating it in temporary planning notes.

## Non-goals

- Do not implement dataset, replay, or scoring tooling in this phase.
- Do not delete the local baseline snapshot.
- Do not change live combat behavior.
- Do not create or update a PR.

## Affected files

- `dev-docs/plan/issue_60/00-master-plan.md`
- `dev-docs/plan/issue_60/01-absorption.md`
- `dev-docs/plan/issue_60/02-dataset.md`
- `dev-docs/plan/issue_60/03-replay.md`
- `dev-docs/plan/issue_60/04-reporting.md`
- `dev-docs/plan/tuning_loop/README.md`
- `dev-docs/plan/tuning_loop/*.md`

## Implementation steps

- Read the #60 issue body and labels.
- Read the tuning-loop planning files.
- Compare tuning-loop scope against durable docs in
  `docs/planning/offline-fitting-loop.md` and `docs/agent/CURRENT_STATE.md`.
- Create the issue-specific phase plan.
- Add absorbed-plan notices to the old tuning-loop folder.
- Run docs layout validation.

## Acceptance criteria

- `dev-docs/plan/issue_60/` exists and names #60 as the issue target.
- The master plan explains that `dev-docs/plan/tuning_loop/` is absorbed into
  #60.
- Phase documents preserve the useful tuning-loop details as implementation
  tasks, not a parallel plan.
- The old tuning-loop folder clearly points readers to this issue plan.
- No source or behavior-changing files are modified.

## Validation commands

- `python tools/check_layout.py`

## Manual smoke tests

- Open the #60 plan and confirm it can be followed without reading the old
  tuning-loop folder first.
- Open the old tuning-loop folder and confirm it points to #60 as the active
  source of truth.

## Rollback risks

- Low. This is planning-only documentation. Revert by removing the #60 plan
  folder and absorbed-plan notices.

## Progress

- Completed plan absorption and source-of-truth update.

## Decision log

- `dev-docs/plan/tuning_loop/` is not deleted because it contains a useful local
  baseline corpus snapshot and comparison template. It is retained as historical
  input only.
- The issue-specific plan lives under `dev-docs/plan/issue_60/` to match the
  repository's per-issue planning convention.

## Outcomes / Retrospective

- #60 now has a local phased plan. The old tuning-loop plan is marked as
  absorbed so future work can proceed from one source of truth.
