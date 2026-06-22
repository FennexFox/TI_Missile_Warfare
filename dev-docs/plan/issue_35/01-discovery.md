# Phase 01: Discovery and safety plan

## Goal

- Confirm #35 boundaries, scope model, and implementation surfaces.

## Scope

- Read GitHub issue #35, local #35/#6 context, #34 implementation, parser, and selected command-scope docs.
- Confirm no live command behavior belongs in this issue.
- Decide the smallest diagnostics-only implementation shape.

## Non-goals

- No code implementation in this phase.
- No command-plan candidate classification logic yet.
- No live command API calls or behavior changes.

## Affected files

- `dev-docs/plan/issue_35/*.md`

## Implementation steps

- Create a phase plan for #35.
- Record the revised player-controlled command scope model.
- Validate phase-plan structure.

## Acceptance criteria

- Plan documents #35 as diagnostics-only.
- Plan states command-panel selection is optional, not mandatory.
- Plan requires skip-closed behavior when no safe player-controlled scope is available.
- Plan includes validation commands.

## Validation commands

- `python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_35`

## Manual smoke tests

- Not applicable for planning.

## Rollback risks

- Low; documentation-only plan files can be reverted.

## Progress

- Complete.

## Decision log

- #35 will add dry-run command-candidate diagnostics and parser summaries only.
- A candidate can become eligible only under an explicit, auditable player-controlled command scope.
- Active-player launcher scope is allowed only when runtime evidence verifies active-player ownership and non-AI control.

## Outcomes / Retrospective

- Plan created from issue body plus #34 runtime smoke and scope handoff.
