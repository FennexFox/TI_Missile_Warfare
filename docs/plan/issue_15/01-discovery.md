# Phase 01: Discovery and safety boundaries

## Goal

Confirm Issue #15 scope, current readiness semantics, and exact code touchpoints before
editing runtime behavior.

## Scope

- Review GitHub issue #15, the reviewed prompt, and local docs.
- Inspect current snapshot, allocation, model, and parser code paths.
- Record the decision that ammo/gate/cooldown evidence remains distinct from proven
  ready shots.

## Non-goals

- No production code changes in this phase.
- No controlled allocation, command application, targeting, suppression, AI, projectile,
  physics, or guidance changes.

## Affected files

- `.chatgpt/codex-runs/2026-06-20T000000Z-issue-15-readiness-evidence/PROMPT.md`
- `docs/plan/issue_15/*`
- `docs/battle-snapshot-extractor.md`
- `docs/confirmed-hooks.md`
- `src/MissileFireControl.Mod/Adapters/CombatSnapshotExtractor.cs`
- `src/MissileFireControl.Mod/Diagnostics/SnapshotDiagnostics.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `tools/parse_player_log.py`

## Implementation steps

1. Confirm issue #15 acceptance criteria and non-goals.
2. Confirm the reviewed prompt's risk: the current extractor has an optimistic
   `FirstKnownCount` ready-shot mapping.
3. Confirm current docs say pre/post ammo evidence is not true ready/loaded/chambered
   evidence.
4. Write the phased implementation plan.

## Acceptance criteria

- The phase plan identifies readiness semantics and the risky current mapping.
- The plan states that `readyShots` remains unknown unless a proven ready source exists.
- The worktree remains buildable because no production behavior changes are made.

## Validation commands

- `python C:/Users/techn/.codex/skills/phased-issue-implementation/scripts/phase_plan_helper.py validate --plan-dir docs/plan/issue_15`

## Manual smoke tests

- None for discovery.

## Rollback risks

- Removing the plan directory would lose the implementation audit trail but not affect
  runtime behavior.

## Progress

- Completed issue, prompt, docs, and code-path review.
- Created a concrete phased plan under `docs/plan/issue_15`.

## Decision log

- The current plan uses `docs/plan/issue_15` because the Issue #15 prompt explicitly
  allows focused docs in that path.
- Numeric `readyShots` will not be populated from ammo dictionary, magazine, cooldown,
  or gate-state evidence.

## Outcomes / Retrospective

- Discovery completed. Phase 2 can implement evidence metadata without changing live
  combat behavior.
