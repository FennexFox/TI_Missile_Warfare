# Phase 02: Add evidence sufficiency reporting

## Goal

Add generated evidence-sufficiency output to the fitting wrapper.

## Scope

- Add dataclasses and classification helpers for per-input sufficiency status.
- Include the gate in `summary.json`.
- Render the gate in `shadow-fitting-report.md`.
- Keep fitting classifications and baseline readiness unchanged.

## Non-goals

- No parser health verdict changes.
- No allocator scoring changes.
- No live command application.
- No Issue #29 PD capability model.

## Affected files

- `tools/fit_shadow_allocation.py`
- `dev-docs/plan/issue_28/`

## Implementation steps

- Add Issue #28 status vocabulary to fitting output.
- Derive existing-evidence statuses from aggregate parser summaries and
  classification counts.
- Add static command-readiness gate rows for selected-player scope, vanilla
  command granularity, dry-run intent logging, and launch/ammo delta evidence.
- Render limitations and blockers separately from the fitting baseline verdict.

## Acceptance criteria

- Reports distinguish parser/fitting readiness from evidence sufficiency.
- Empty `missingInputs` and parser OK cannot imply full controlled-command
  readiness in generated output.
- Observed target PD templates are explicitly `presenceOnly`.
- Controlled live command readiness is `Not ready`.

## Validation commands

- python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_28_sufficiency
- python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_28_synthetic
- python -m compileall tools
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_28

## Manual smoke tests

- Review generated synthetic and four-log Markdown reports.

## Rollback risks

- Consumers of `summary.json` will see a new additive field; existing fields
  remain stable.

## Progress

- Completed.

## Decision log

- Added `evidence_sufficiency` as a new aggregate report field instead of
  changing `readiness_verdict`.
- PD defaulting only produces `defaulted` sufficiency when it affects
  allocation/rejection evidence. Defaulted PD on `command-safety no-op` rows is
  named but does not downgrade observed allocation/rejection evidence.
- `observedTargetWeaponTemplates` is classified as `presenceOnly` until Issue
  #29 adds a richer PD capability model.

## Outcomes / Retrospective

- `tools/fit_shadow_allocation.py` now emits the Issue #28 status vocabulary in
  JSON and Markdown.
- The four-log sweep still reports `Ready for #6 baseline`.
- The new sufficiency gate reports `Baseline-ready with named limitations` and
  controlled live command readiness `Not ready`.
