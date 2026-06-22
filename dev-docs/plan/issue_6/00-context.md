# Issue #6 context

This is local context for Codex planning. It is not a phased implementation plan or a step-by-step work order. Codex should use this file, the linked durable docs, and the relevant GitHub issue bodies to produce its own phased implementation plan for each PR.

## Parent intent

Issue #6 is the controlled allocation experiment and fitting loop. It is the first project stream where allocator decisions may eventually be applied to selected player missile ships, but only after the dry-run and safety-gate slices prove the scope. The purpose is not merely to display recommendations; it is to collect causal evidence from controlled experiments and use that evidence to tune the allocator.

The controlling safety principle is: behavior-changing command application must remain disabled by default, player-triggered, reversible, and limited to explicitly selected player-controlled missile ships.

## Location of source and docs

Decompiled source of Terra Invicta is in `../TI_RE_Workspace`. Refer to `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master` to navigate the relevant missile fire control code. Do not include the decompiled source in the repo. It is only for local inspection.

## Sub-issue sequence

The #6 epic is split into bounded end-to-end slices:

| Slice | Role | Behavior boundary |
| --- | --- | --- |
| #34 | Controlled experiment dry-run envelope | Diagnostics-only; no live commands. |
| #35 | Command resolvability and selected-scope safety report | Dry-run command-plan candidates only; no live commands. |
| #36 | Apply-gate hard stop and safety-toggle proof | Routes plans to a named hard-stop gate; still no live commands. |
| #37 | First single-ship live controlled apply | First behavior-changing slice; one selected ship and one bounded command attempt. |
| #38 | Small selected-group controlled experiment report | Small selected player group; bounded one-shot controlled experiment. |
| #39 | Heuristic tuning from controlled evidence | At most one evidence-backed heuristic/rule family adjustment. |

#34-#36 are intended to be diagnostics-only / dry-run / hard-stop safety proof work. #37 is the first live-command slice and should stay extremely narrow. #38 expands only to a small explicitly selected player group. #39 closes the first learning loop and should not add new live command behavior.

## Current evidence base

Durable docs and completed work that matter before planning any #6 slice:

- `docs/guide/architecture.md`: keep game integration thin and heuristic logic testable. Core logic must remain independent of Terra Invicta, Unity, Harmony, and UMM.
- `docs/diagnostics/snapshot-and-allocation.md`: current `[SnapshotLog]` and `[AllocationLog]` schema, shadow allocation behavior, parser expectations, fitting wrapper context, and evidence terminology.
- `docs/research/readiness-semantics.md`: `ammoGateBudgetShots` is the confirmed ammo-plus-vanilla-gates budget. Do not revive legacy `readyShots` wording unless a distinct source is proven in later research.
- `docs/research/selected-command-scope.md`: #21 verifies the safe selected-player scope. The safe scope is the tactical command panel single selected ship or group-selected ship list. Do not treat the left-hand player-side combatant list as selected scope.
- `docs/planning/mvp-roadmap.md`: durable roadmap and current blocker state. Some older references still mention #22-style dry-run work; for the current #6 split, use #34-#39 as the active sub-issue chain.

Issue #4 already supplies observation-only shadow allocation logging and parser/reporting support. Issue #21 verifies selected-player command scope. Issue #23 is the minimal live command safety-gate work; #37+ should not assume that live application is safe until the relevant safety evidence exists.

## Cross-cutting constraints

- Preserve shadow-only behavior and a safety path that can force no command application.
- Do not apply commands, change target assignments, change weapon mode, suppress launches, alter cooldowns, mutate ammo accounting, affect AI factions, or touch unselected player ships in #34-#36.
- When runtime evidence is missing, log explicit unknown/missing reasons rather than silently inventing precision.
- Pair every controlled experiment record with enough identifiers to connect experiment id, allocation cycle/decision, selected ship evidence, target evidence, command intent, and result class.
- Keep parser/report support close to the logging schema so the user does not need line-by-line manual analysis.
- Keep real combat logs under ignored local `artifacts/` paths. Do not commit private logs.

## Existing code areas likely to matter

This list is context for planning, not an exhaustive implementation list:

- `src/MissileFireControl.Mod/ModSettings.cs`: feature toggles currently include diagnostics, snapshot diagnostics, shadow allocation diagnostics, recommendation-only mode, and launch-discipline placeholder.
- `src/MissileFireControl.Mod/Main.cs`: UMM settings panel and current diagnostic ping button.
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`: current shadow allocation cycle creation, allocator invocation, and `[AllocationLog]` writing.
- `tools/parse_player_log.py`: parser already recognizes shadow allocation record types and reserves applied/skipped/failed command buckets.
- `tools/fit_shadow_allocation.py`: offline fitting wrapper and report generation for selected logs.
- `tools/fixtures/*.txt`: synthetic allocation fixtures for parser/fitting smoke coverage.

## Planning posture for Codex

For each sub-issue, Codex should first decide the smallest independently reviewable PR that preserves the safety boundary. The plan should state whether the slice is docs-only, diagnostics-only, hard-stop safety proof, or behavior-changing. Any behavior-changing slice must explicitly name the safety evidence it relies on and the rollback path.
