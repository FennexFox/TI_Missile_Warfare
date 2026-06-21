# Define evidence sufficiency gates before controlled allocation

## Issue Target And Scope Summary

- Issue target: #28
- Title: Define evidence sufficiency gates before controlled allocation
- Source plan: `00-contexts.md`
- Scope: add an explicit evidence-sufficiency gate above the existing parser
  and fitting-wrapper verdicts so reports and docs can say the current logs are
  baseline-ready while still naming fidelity limits and live-command blockers.

## Strategy

- Keep `tools/parse_player_log.py` parser health semantics unchanged.
- Keep `tools/fit_shadow_allocation.py` baseline readiness semantics unchanged:
  `Ready for #6 baseline` remains a fitting-wrapper verdict only.
- Add aggregate evidence-sufficiency reporting to the fitting JSON and Markdown
  output with per-input statuses from Issue #28's vocabulary.
- Classify `observedTargetWeaponTemplates` PD evidence as presence-only until
  Issue #29 upgrades the model.
- Document that controlled live command application remains not ready until
  dry-run command-intent logging, command mapping, and live safety gates pass.

## Phase Order

1. [Context and source review](01-discovery.md)
2. [Add evidence sufficiency reporting](02-implementation.md)
3. [Document readiness semantics](03-documentation.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.
- Phase 3 depends on completion and validation of phase 2.

## Source Of Truth Decisions

- `tools/fit_shadow_allocation.py` is the source of truth for generated fitting
  and sufficiency report fields.
- `docs/diagnostics/snapshot-and-allocation.md` is the source of truth for
  diagnostic schema and generated-report interpretation.
- `docs/diagnostics/runtime-validation-history.md` preserves the Issue #30
  four-log result with Issue #28 interpretation.
- `docs/planning/mvp-roadmap.md` is the durable source for remaining #6 gates.
- `00-contexts.md` is background context, not a phase plan.

## Global Validation Expectations

- python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_28_sufficiency
- python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_28_synthetic
- python -m compileall tools
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_28

## Known Risks And Assumptions

- Real combat logs and generated fitting artifacts under `artifacts/` are local
  evidence and should not be committed.
- The current four-log baseline can remain useful even when the new gate names
  PD capability as presence-only.
- Issue #28 must not implement Issue #29's richer PD model, Issue #22 dry-run
  command intent, Issue #23 live safety, or Issue #6 live command application.
