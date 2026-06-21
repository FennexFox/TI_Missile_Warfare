# Phase 2: Wrapper and fitting classification

## Goal

Add a repeatable offline wrapper that consumes selected logs and writes per-log
JSON plus aggregate Markdown fitting artifacts.

## Scope

- Add `tools/fit_shadow_allocation.py`.
- Import parser helpers from `tools/parse_player_log.py`.
- Discover `.log` and `.txt` files under the selected input directory.
- Classify shadow allocation rows conservatively.
- Fail when all selected logs lack required fitting evidence or parser
  validation fails.

## Non-goals

- No live command execution.
- No Core heuristic tuning.
- No real combat logs committed.

## Affected files

- `tools/fit_shadow_allocation.py`
- Optionally a tiny synthetic fixture if needed for wrapper smoke validation.

## Implementation steps

- Discover selected logs.
- Parse each log with `parse_log`.
- Scan `[AllocationLog]` rows for cycle context and target decisions.
- Write per-log JSON.
- Write aggregate `shadow-fitting-report.md`.
- Include readiness and PD limitation fields.

## Acceptance criteria

- Default command works with ignored selected-log/output paths.
- Report includes classification buckets, parser evidence, missing evidence, and
  readiness verdict.
- Synthetic fixture, if added, is marked as non-evidence.

## Validation commands

```powershell
python tools\fit_shadow_allocation.py --input <fixture-or-selected-log-dir> --output artifacts\shadow-fitting\latest
python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
python -m compileall tools
```

## Manual smoke tests

- Inspect generated aggregate Markdown for clear conditional-readiness wording.
- Confirm generated output is under ignored `artifacts/`.

## Rollback risks

- Wrapper behavior is isolated to tooling and can be reverted without runtime
  impact.

## Progress

- Completed.

## Decision log

- The wrapper imports parser helpers from `tools/parse_player_log.py` and scans
  `[AllocationLog]` rows only for offline classification.
- The synthetic fixture is a wrapper smoke input only and is excluded from real
  evidence readiness.
- Bad classification counts block the generated readiness verdict until
  reviewed against real selected logs.

## Outcomes / Retrospective

- `tools/fit_shadow_allocation.py` writes per-log JSON, `summary.json`, and
  `shadow-fitting-report.md`.
- Focused smoke with `tools/fixtures/shadow_allocation_synthetic.txt` completed
  and produced `Not ready` because no real selected combat log was analyzed.
