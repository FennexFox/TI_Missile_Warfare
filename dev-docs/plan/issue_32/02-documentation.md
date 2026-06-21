# Phase 02: Document readiness impact and close issue

## Goal

Document the classification and close Issue #32 with validation evidence.

## Scope

- Update diagnostic schema docs.
- Update runtime validation history.
- Update the roadmap.
- Close Issue #32 after final validation.

## Non-goals

- No broad docs reorganization.
- No generated artifact commits.
- No claim that #6 live command application is ready.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_32/`
- GitHub Issue #32

## Implementation steps

- Documented that missing `targetIdentity` means no launcher-selected priority target was visible to the hook, not that vanilla had no live target.
- Documented `command-safety no-op` in the fitting classification list.
- Updated Issue #30 runtime history counts after Issue #32 classification.
- Removed #32 from remaining roadmap blockers while keeping #28/#29 and #22/#23 as separate gates.

## Acceptance criteria

- #6 readiness docs state missing target identity is command-safety evidence for no-op, not allocation evidence.
- Docs separate fitting baseline readiness from live command readiness.
- Issue #32 is closed after validation.

## Validation commands

- `python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_32_classification`
- `python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_32_synthetic`
- `python -m compileall tools`
- `python -m ruff check tools\fit_shadow_allocation.py`
- `python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_32`

## Manual smoke tests

- Review docs diff for consistency with the regenerated fitting report.

## Rollback risks

- If future diagnostics add direct projectile/controller target identity, this classification may need a more specific source label, but the no-op safety behavior should remain conservative.

## Progress

- Completed.

## Decision log

- `Ready for #6 baseline` remains a fitting-wrapper verdict only. Controlled command application still requires #22/#23, and evidence sufficiency/capability modeling still belongs to #28/#29.

## Outcomes / Retrospective

- Final validation passed.
- Issue #32 classification is documented and ready for closure.
