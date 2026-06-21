# Phase 02: Four-log fitting analysis and follow-up triage

## Goal

Run the parser/fitting sweep and classify whether the result blocks, conditionally supports, or clears pre-#6 readiness.

## Scope

- Run the existing fitting wrapper on the four scoped logs.
- Run parser validation on each log.
- Identify repeated severe or evidence-limited patterns.
- Create a named follow-up if required by Issue #30.

## Non-goals

- No fitting heuristic changes.
- No generated artifact commits.
- No live command application.

## Affected files

- `artifacts/shadow-fitting/issue_30_four_logs/` (ignored generated output)
- GitHub Issue #32
- `dev-docs/plan/issue_30/`

## Implementation steps

- Ran `tools\fit_shadow_allocation.py` over the scoped four-log input.
- Ran `tools\parse_player_log.py --require-launchlogs --require-snapshots` for all four logs.
- Reviewed aggregate and per-log fitting counts from `summary.json`.
- Created Issue #32 for the repeated evidence-limited `targetIdentity` no-op pattern.

## Acceptance criteria

- Parser verdict is `OK` for each selected log.
- Critical missing fields are zero or explicitly explained.
- PD evidence quality is reported per log.
- Fitting output distinguishes plausible, partial saturation, ambiguous, missing-evidence-limited, and severe classifications per log.
- Repeated evidence-limited pattern has a named follow-up.

## Validation commands

- `python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_30_four_logs`
- `python tools\parse_player_log.py artifacts\combat-logs\issue_30_four_logs\Player.log --require-launchlogs --require-snapshots`
- `python tools\parse_player_log.py artifacts\combat-logs\issue_30_four_logs\Player-prev.log --require-launchlogs --require-snapshots`
- `python tools\parse_player_log.py artifacts\combat-logs\issue_30_four_logs\Player-prev1.log --require-launchlogs --require-snapshots`
- `python tools\parse_player_log.py artifacts\combat-logs\issue_30_four_logs\Player-prev2.log --require-launchlogs --require-snapshots`

## Manual smoke tests

- Reviewed `artifacts/shadow-fitting/issue_30_four_logs/shadow-fitting-report.md`.

## Rollback risks

- Closing or deleting Issue #32 would remove the named follow-up required by Issue #30.

## Progress

- Completed.

## Decision log

- No severe classifications were found across the four logs.
- The repeated evidence-limited pattern is 54 no-op cycles in `Player-prev.log` missing `targetIdentity`; Issue #32 tracks it before #6.
- `Player-prev1.log`, `Player-prev2.log`, and `Player.log` had observed target PD evidence for every shadow cycle and zero critical missing fields.

## Outcomes / Retrospective

- The aggregate verdict is `Conditionally ready`, not full ready, because evidence limitations remain.
