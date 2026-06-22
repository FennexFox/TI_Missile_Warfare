# Phase 01: Discovery and safety boundary

## Goal

- Establish the #36 safety boundary and identify the smallest apply-gate surface that can be reviewed independently.

## Scope

- Read local #36 and #6 context, GitHub issue #36, current diagnostics docs, and completed #34/#35 plans.
- Confirm the existing dry-run candidate classification path and parser summary points.
- Define the gate record schema and validation fixture expectations.

## Non-goals

- Do not implement live command application.
- Do not change allocator heuristics.
- Do not broaden selected/player command scope eligibility.

## Affected files

- `dev-docs/plan/issue_36/*`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `src/MissileFireControl.Mod/ModSettings.cs`
- `src/MissileFireControl.Mod/Main.cs`
- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`
- `tools/fixtures/apply_gate_hard_stop.txt`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/planning/mvp-roadmap.md`

## Implementation steps

- Confirm #36 acceptance criteria from local docs and `gh issue view 36`.
- Preserve #35 candidate skip/fail classifications before the apply gate.
- Route only `eligible` candidates to a named diagnostics-only gate.
- Count `blockedBySafetyToggle` separately in parser/fitting summaries.

## Acceptance criteria

- Discovery identifies a named gate, default-off command-apply toggle, parser fields, and deterministic validation fixture.
- Plan documents #36 as diagnostics-only and #37 as the first live apply slice.

## Validation commands

- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\apply_gate_hard_stop.txt --require-launchlogs --require-snapshots

## Manual smoke tests

- Fresh runtime smoke after deployment: enable controlled dry-run diagnostics, leave command application disabled, trigger once, and confirm zero applied commands. If no eligible candidate appears, use fixture coverage for the gate-reachable path.

## Rollback risks

- Removing gate logging should restore #35 behavior. Parser additions are additive and should tolerate older logs.

## Progress

- Completed source and issue-context review.

## Decision log

- Use `dryRunApplyGate` as the explicit gate record type.
- Use `controlledCommandApplyGate` as the stable gate name.
- Use `blockedBySafetyToggle` as the stable default-off block reason.

## Outcomes / Retrospective

- Discovery completed. The implementation can be additive: default-off setting, one gate logger for eligible candidates, parser/fitting counters, docs, and one deterministic fixture.
