# Phase 01: Issue context and selected log inventory

## Goal

Resolve Issue #30 acceptance criteria and identify the exact four combat logs to analyze.

## Scope

- Read Issue #30.
- Inspect existing fitting artifacts and docs.
- Locate available local Terra Invicta `Player*.log` files.
- Stage a scoped ignored input folder containing only the four combat logs.

## Non-goals

- No runtime code changes.
- No live command application.
- No allocator tuning.

## Affected files

- `artifacts/combat-logs/issue_30_four_logs/` (ignored local input)
- `dev-docs/plan/issue_30/`

## Implementation steps

- Verified Issue #30 requires multiple real selected combat logs, per-log parser verdicts, per-log PD evidence quality, fitting classifications, named follow-ups for repeated evidence-limited/severe patterns, and a #6 readiness summary.
- Found four current local Terra Invicta logs: `Player.log`, `Player-prev.log`, `Player-prev1.log`, and `Player-prev2.log`.
- Copied only those four logs into `artifacts/combat-logs/issue_30_four_logs/`.

## Acceptance criteria

- Four real `Player*.log` files are identified and staged under an ignored artifact path.
- Non-combat `.txt` or mod log files are excluded from the final fitting input.

## Validation commands

- `Get-ChildItem artifacts\combat-logs\issue_30_four_logs\Player*.log`

## Manual smoke tests

- Confirmed the staged input folder contains exactly four files.

## Rollback risks

- Deleting the ignored staged folder loses local convenience copies but not repo source.

## Progress

- Completed.

## Decision log

- The first broad fitting pass over the Terra Invicta directory included two non-combat files and reported parser failures. The final sweep uses a scoped ignored input folder to avoid counting unrelated files.

## Outcomes / Retrospective

- The final input set matches the user's "available 4 combat logs" request and avoids false parser failures.
