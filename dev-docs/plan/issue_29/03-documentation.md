# Phase 03: Document source-backed limits and validation

## Goal

- Record issue #29's runtime schema, report semantics, source-backed limits, and validation results.

## Scope

- Durable diagnostics and roadmap docs.
- Issue #29 phase plan.

## Non-goals

- No generated fitting artifacts under version control.
- No rewrite of unrelated issue plans.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_29/*.md`

## Implementation steps

- Documented new `pdEvidenceQuality` and `pdCapability*` fields.
- Documented that `observedTemplateCapability` is provisional, not calibrated.
- Updated roadmap blockers/recommended next work to reflect issue #29 completion.
- Recorded validation and the synthetic fixture result.

## Acceptance criteria

- Durable docs say old logs remain `presenceOnly`.
- Durable docs say template capability is stronger than presence-only but still lacks live readiness, ammo, geometry, and arc coverage.
- Plan files contain completed outcomes and validation state.

## Validation commands

- `python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_29` - passed.

## Manual smoke tests

- Read documentation updates for consistency with issue #29 boundaries.

## Rollback risks

- Documentation is additive; the main risk is overstating capability quality, mitigated by explicit limitations.

## Progress

- Completed.

## Decision log

- The docs do not claim fresh real runtime `observedTemplateCapability` coverage until new Terra Invicta logs are collected.

## Outcomes / Retrospective

- Issue #29 is implemented as a conservative evidence-quality upgrade and leaves issue #22/#23/#6 live command work separate.
