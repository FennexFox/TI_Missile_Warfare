# Phase 01: Classify targetIdentity-missing no-op semantics

## Goal

Classify the repeated targetIdentity-missing no-op pattern as a specific command-safety case instead of a generic evidence-limited allocation case.

## Scope

- Update the fitting wrapper classification list.
- Classify no-op rows with only hard missing `targetIdentity` as `command-safety no-op`.
- Exclude PD defaulting on those no-op rows from allocation evidence limitations.
- Add a synthetic fixture for future wrapper smoke coverage.

## Non-goals

- No allocator tuning.
- No live command application.
- No change to parser health verdicts.

## Affected files

- `tools/fit_shadow_allocation.py`
- `tools/fixtures/shadow_allocation_missing_target_noop.txt`
- `dev-docs/plan/issue_32/`

## Implementation steps

- Added `command-safety no-op` to fitting classifications.
- Moved hard missing input handling into allocation/rejection/no-op branches so no-op rows can be classified separately.
- Added a no-op-specific classification when the only hard missing input is `targetIdentity`.
- Suppressed `PD evidence defaulted` limitations for `command-safety no-op` because no target was allocated and PD evidence was not used for an allocation/rejection decision.
- Added a synthetic smoke fixture for targetIdentity-missing no-op rows.

## Acceptance criteria

- The Issue #30 pattern is reproduced and classified as `command-safety no-op`.
- Fitting output distinguishes it from parser failure and allocator-design ambiguity.
- Missing target identity on allocation/rejection rows remains evidence-limited.

## Validation commands

- `python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_32_classification`
- `python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_32_synthetic`
- `python -m compileall tools`
- `python -m ruff check tools\fit_shadow_allocation.py`

## Manual smoke tests

- Reviewed `artifacts/shadow-fitting/issue_32_classification/shadow-fitting-report.md`.

## Rollback risks

- Reverting the classification would return the Issue #30 no-op rows to generic `missing-evidence-limited` and would again make target-object PD fallback look like allocation evidence.

## Progress

- Completed.

## Decision log

- Accepted the pattern as safe no-op evidence: no concrete launcher-selected target identity was visible, so the shadow allocator did not infer a target and did not allocate shots.
- Decompiled source review supports this distinction: selected salvo commands set `combatPrimaryTarget`, but normal missile firing also uses a live `MissileWeapon.base.target`.

## Outcomes / Retrospective

- The four-log fitting sweep now reports 54 `command-safety no-op` rows, 0 `missing-evidence-limited` rows, no evidence limitations, and `Ready for #6 baseline` under fitting-wrapper rules.
