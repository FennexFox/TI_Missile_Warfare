# Phase 01: Discovery and safety boundary

## Goal

- Resolve the #34 safety boundary, affected files, and minimal dry-run schema before runtime/parser edits.

## Scope

- Review Issue #34, Issue #6 context, current shadow allocation logging, parser record-type handling, settings, and UMM panel.
- Decide the experiment trigger, experiment id format, and dry-run record types.

## Non-goals

- No runtime behavior change in this phase.
- No parser/schema implementation in this phase.

## Affected files

- `dev-docs/plan/issue_34/00-master-plan.md`
- `dev-docs/plan/issue_34/01-discovery.md`
- `dev-docs/plan/issue_34/02-implementation.md`
- `dev-docs/plan/issue_34/03-verification.md`

## Implementation steps

- Read GitHub issue #34 and local issue contexts.
- Inspect `ModSettings`, `Main`, `ShadowAllocationDiagnostics`, `parse_player_log.py`, and existing fixtures.
- Record schema decisions and validation expectations.

## Acceptance criteria

- Plan states that #34 is diagnostics-only.
- Plan explicitly forbids live command application and target/weapon mutation.
- Plan identifies parser-visible dry-run grouping fields.

## Validation commands

- `python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_34`

## Manual smoke tests

- Not applicable for discovery.

## Rollback risks

- Low. Revert plan files if the chosen scope changes before implementation.

## Progress

- Completed source review for Issue #34, Issue #6 context, settings, UMM UI, shadow allocation logging, parser record handling, and fixtures.

## Decision log

- Use a disabled-by-default controlled dry-run setting plus one-shot UMM trigger.
- Consume the one-shot on the next shadow allocation cycle so the dry-run can reuse existing projectile-fire snapshot evidence and allocator intent.
- Keep dry-run records under `[AllocationLog]` with new parser-known record types to avoid a second marker family.
- Use `experimentId` as the grouping key and keep `cycleId` as the allocator cycle key.
- Log selected scope as best-effort evidence with explicit missing reasons; do not fall back to broad combatant lists.

## Outcomes / Retrospective

- Discovery complete. The implementation can stay narrow and reviewable.
