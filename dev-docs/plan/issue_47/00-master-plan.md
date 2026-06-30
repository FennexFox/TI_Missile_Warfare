# Outcome hook diagnostics

## Issue Target And Scope Summary

- Issue target: #47
- Title: Outcome hook diagnostics
- Source plan: None
- Scope: reverse-engineer Terra Invicta combat outcome surfaces and add
  diagnostics-only hooks only where concrete, stable method signatures are
  visible.

## Strategy

- Keep #47 separate from allocator tuning and live command behavior.
- Use concrete managed-code combat classes rather than broad interfaces.
- Emit a distinct `[OutcomeLog]` marker so precise outcome-hook rows remain
  separate from `LaunchLog`, `SnapshotLog`, `AllocationLog`, vanilla spillover,
  and conservative post-command destruction hints.
- Document each hook's evidence level and avoid claiming unique projectile or
  command kill attribution unless identity fields support it.

## Phase Order

1. [Outcome hook surface inventory](01-discovery.md)
2. [Diagnostics-only outcome hooks](02-implementation.md)
3. [Validation and closeout](03-verification.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.
- Phase 3 depends on completion and validation of phase 2.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation plan source of truth.
- Phase files in this directory define phase-local scope and validation.
- Earlier monolithic plans are input material only unless explicitly retained.
- The local handoff `.chatgpt/handoffs/2026-06-29-issue-47-outcome-hooks-context.local.md`
  defines the attribution discipline for this issue.

## Global Validation Expectations

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m compileall tools
- python tools\parse_player_log.py --require-launchlogs

## Known Risks And Assumptions

- Runtime validation completed on the active 2026-06-29 `Player.log` with
  `patched=7`, `skipped=0`, and nonzero `[OutcomeLog]` rows from all four
  source-reviewed outcome hooks.
- Outcome rows may prove event-level evidence such as projectile destruction,
  ship damage, or ship destruction without proving unique kill causality.
- Hook bootstrap health must not regress the already confirmed launch hooks.
