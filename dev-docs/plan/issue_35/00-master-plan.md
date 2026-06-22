# Command resolvability and player-controlled scope safety report

## Issue Target And Scope Summary

- Issue target: #35
- Title: Command resolvability and selected-scope safety report
- Source context: GitHub issue #35, `00-context.md`, `dev-docs/plan/issue_6/00-context.md`, #34 runtime smoke
- Scope: extend the #34 controlled dry-run envelope with diagnostics-only command-plan candidate rows and parser/report summaries that prove whether each allocator-motivated command candidate is eligible, would skip, or would fail under an explicit player-controlled command scope.

## Strategy

- Preserve the #34 safety boundary: no command APIs, no target assignment changes, no weapon-mode changes, no launch suppression, no ammo/cooldown mutation.
- Keep command candidates under `[AllocationLog]` so existing parser plumbing can group them with dry-run experiments.
- Add a distinct candidate record type rather than overloading `dryRunIntent`.
- Resolve command scope in this order:
  - command-panel selected ship/group, when visible;
  - current projectile launcher only when runtime evidence verifies it is active-player controlled and not AI-controlled;
  - otherwise no safe scope, and candidates skip closed.
- Classify only dry-run command candidates; do not implement live command execution or apply-gate behavior.
- Extend parser/report output with candidate classification, reason counts, scope sources, scope missing reasons, and scope-violation counts.
- Update docs and fixtures so #35 remains diagnostics-only and no live command readiness is implied.

## Phase Order

1. [Discovery and safety plan](01-discovery.md)
2. [Command candidate logging and parser summaries](02-implementation.md)
3. [Documentation and validation](03-verification.md)

## Phase Dependencies

- Phase 1 has no dependency beyond #34 being merged into `issue_6`.
- Phase 2 depends on the safety plan and selected command-scope findings from Phase 1.
- Phase 3 depends on Phase 2 implementation and validation.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation source of truth for #35.
- `00-context.md` and `dev-docs/plan/issue_6/00-context.md` are input context, not phase status files.
- Runtime logging source of truth: `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`.
- Parser/report source of truth: `tools/parse_player_log.py`.
- Durable behavior docs belong in `docs/diagnostics/snapshot-and-allocation.md` and `docs/planning/mvp-roadmap.md`.

## Global Validation Expectations

- `python tools\check_layout.py`
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`
- `python -m compileall tools`
- `python tools\parse_player_log.py tools\fixtures\controlled_dry_run_experiment.txt --require-launchlogs --require-snapshots`
- `python tools\parse_player_log.py tools\fixtures\command_resolvability_scope_skip.txt --require-launchlogs --require-snapshots`
- `dotnet build TI_Missile_Fire_Control.sln` when local references are available

## Known Risks And Assumptions

- Current command-panel selected scope may remain unavailable; #35 must skip closed when no audited scope can be resolved.
- Active-player launcher scope is only safe if runtime reflection can prove active-player faction identity and non-AI control for the launcher; otherwise it must not become eligible.
- Candidate classification is diagnostic evidence only. It is not a live-command apply gate.
- Runtime smoke is still required after implementation to prove active-player scope visibility in the real game.
