# Apply-gate hard stop and safety-toggle proof

## Issue Target And Scope Summary

- Issue target: #36
- Title: Apply-gate hard stop and safety-toggle proof
- Source context: GitHub issue #36, `00-context.md`, `dev-docs/plan/issue_6/00-context.md`, completed #34/#35 plans, diagnostics docs
- Scope: add a diagnostics-only apply-gate boundary for eligible dry-run command candidates, keep command application disabled by default, and summarize safety-gate blocks separately from missing evidence, skipped scope, failures, and applied commands.

## Strategy

- Preserve the #34/#35 safety boundary: no live command APIs, target assignment changes, weapon mode changes, launch suppression, cooldown mutation, or scope broadening.
- Add an explicit default-off command-apply setting (`AllowCommandApply`) as the second step after controlled dry-run diagnostics.
- Route only `dryRunCommandCandidate classification="eligible"` rows to a named apply gate.
- Emit `recordType="dryRunApplyGate"` rows with experiment id, cycle id, candidate id, gate name, gate result, block reason, pre-state identity fields, post-state not-applied fields, and `appliedCommands="0"`.
- When the default-off setting blocks the gate, use stable reason `blockedBySafetyToggle`.
- Extend parser and fitting summaries with safety-gate blocked counts and reason/result histograms while keeping `dryRun*` rows out of allocation-quality fitting.
- Add deterministic fixture coverage for a gate-reachable candidate blocked by the hard stop.

## Phase Order

1. [Discovery and safety boundary](01-discovery.md)
2. [Apply-gate diagnostics and parser summaries](02-implementation.md)
3. [Documentation and validation](03-verification.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.
- Phase 3 depends on completion and validation of phase 2.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation source of truth for #36.
- `00-context.md` and `dev-docs/plan/issue_6/00-context.md` are input context, not phase status files.
- Runtime logging source of truth: `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`.
- Safety toggle source of truth: `src/MissileFireControl.Mod/ModSettings.cs` and `src/MissileFireControl.Mod/Main.cs`.
- Parser/report source of truth: `tools/parse_player_log.py`.
- Durable behavior docs belong in `docs/diagnostics/snapshot-and-allocation.md` and `docs/planning/mvp-roadmap.md`.

## Global Validation Expectations

- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\apply_gate_hard_stop.txt --require-launchlogs --require-snapshots

## Known Risks And Assumptions

- Deterministic fixture coverage exercises the gate-reachable path.
- Fresh #36 runtime smoke on 2026-06-22 observed one eligible selected-ship candidate reaching `controlledCommandApplyGate` and being blocked by `blockedBySafetyToggle` with zero applied commands.
- `AllowCommandApply` is an explicit safety toggle only. This issue does not implement live command application, even if that setting is manually enabled.
- #37 remains the first behavior-changing slice.
