# Controlled experiment dry-run envelope

## Issue Target And Scope Summary

- Issue target: #34
- Title: Controlled experiment dry-run envelope
- Source context: `00-context.md`, `dev-docs/plan/issue_6/00-context.md`, GitHub issue #34
- Scope: add a diagnostics-only, disabled-by-default controlled experiment dry-run envelope that can be explicitly triggered from the UMM panel, tags the next shadow allocation cycle with an experiment id, logs selected-scope evidence where visible, emits dry-run command intent/result rows, and lets the parser group experiments without manual line inspection.

## Strategy

- Preserve the safety boundary: no command APIs, no target assignment changes, no weapon-mode changes, no launch suppression, no ammo/cooldown mutation.
- Add settings for controlled dry-run diagnostics and a one-shot UI trigger.
- Consume the one-shot trigger inside `ShadowAllocationDiagnostics` when the next projectile-fire shadow cycle is logged.
- Keep rows under `[AllocationLog]` so existing parser plumbing can count them, but add distinct record types for dry-run envelope/intent/result records.
- Use a separate `experimentId` instead of overloading `cycleId`.
- Capture selected player ship scope by reflection where possible; if unavailable, log explicit `selectedScopeUnavailable` / `selectedScopeMissingReason` fields rather than broadening scope.
- Extend `tools/parse_player_log.py` to count experiments, intended dry-run commands, selected ship evidence, skipped/missing-evidence rows, and applied count. #34 must always report zero applied commands.
- Add parser fixture coverage for a dry-run experiment and document runtime smoke steps.

## Phase Order

1. [Discovery and safety boundary](01-discovery.md)
2. [Dry-run envelope and parser grouping](02-implementation.md)
3. [Docs validation and smoke](03-verification.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.
- Phase 3 depends on completion and validation of phase 2.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation source of truth for #34.
- `00-context.md` and `dev-docs/plan/issue_6/00-context.md` are input context, not phase status files.
- Runtime schema source of truth: `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`.
- Parser/report source of truth: `tools/parse_player_log.py`.
- Durable behavior docs belong in `docs/diagnostics/snapshot-and-allocation.md` and `docs/planning/mvp-roadmap.md`.

## Global Validation Expectations

- `python tools\check_layout.py`
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`
- `python -m compileall tools`
- `python tools\parse_player_log.py tools\fixtures\controlled_dry_run_experiment.txt --require-launchlogs --require-snapshots`
- `python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_34_fixtures`
- `dotnet build TI_Missile_Fire_Control.sln` when local references are available

## Known Risks And Assumptions

- Selected-scope reflection may not resolve in all tactical contexts; logging explicit unknowns is acceptable for #34.
- The UMM button is a minimal diagnostic trigger, not polished UX.
- Dry-run rows must not be treated as applied/skipped/failed live command records.
- Fixture validation proves parser grouping only; manual in-game smoke is still needed to prove selected-scope visibility in the real UI.
