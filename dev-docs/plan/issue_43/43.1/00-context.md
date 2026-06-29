# Issue #43.1 context — Fleet-wide dry-run/report scaffold

Updated: 2026-06-23
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.1/00-context.md`
Parent umbrella: `dev-docs/plan/issue_43/00-context.md`

This is context for the first #43 sub-slice. It is not an implementation plan. Codex should read this context and create its own implementation instructions when it starts the slice.

## Purpose

#43.1 exists to make fleet-wide controlled allocation scope visible before changing live combat behavior.

The slice should answer:

```text
If fleet-wide controlled allocation were enabled, which player-controlled friendly missile launchers would be eligible, which would be excluded, which hostile targets would receive command candidates, and which caps or safety gates would block application?
```

#43.1 should prove that fleet-wide scope can fail safely. It does not need to prove better combat performance.

## Preconditions

This slice depends on these completed or available concepts:

- #37: selected-single-ship controlled live apply boundaries;
- #38: selected-group caps and parser fields;
- #39: direct command-result launch/spend correlation;
- #39.1: vanilla / none-correlated spillover diagnostics;
- #44: experiment corpus and parameter ledger conventions.

Do not reopen legacy assumptions such as a fictitious `readyShots` source. Use documented `ammoGateBudgetShots` semantics and existing command-spend diagnostics.

## Boundary

#43.1 is report-only for fleet-wide behavior.

It may define or expose:

- fleet-wide launcher eligibility context;
- explicit exclusion reasons;
- hostile target classification context;
- candidate launcher-target rows;
- report-only cap state;
- corpus-ready fixture or dry-run summary fields.

It must not:

- apply fleet-wide live commands;
- broaden selected-group live command behavior;
- tune allocator parameters;
- suppress vanilla salvo launches;
- implement selected-ship budget distribution;
- infer exact kill attribution from `DestroyShip` text;
- automate combat, save loading, ship selection, or repeated firing.

## Evidence meaning

#43.1 may produce fixture or report-only evidence. It must not claim fleet-wide causal combat improvement.

Recommended corpus interpretation:

- synthetic examples use `runMode = fixture`;
- dry-run analysis may produce corpus-ready metadata, but should not use `fleet-wide-controlled` unless live behavior actually changed;
- scenario metadata should use `selectedMode = fleet-wide` when representing fleet-wide dry-run scenarios.

A failed dry-run is useful if it records why fleet-wide eligibility or target classification was unsafe.

## Report information this slice should make possible

The report or corpus summary should eventually let a reviewer see:

- dry-run experiment id / trigger id;
- battle-side fleet eligibility source and confidence;
- eligible launcher ids, names, teams, player-control evidence, and missile-readiness evidence;
- excluded launcher ids and concrete exclusion reasons;
- enemy target ids/names/teams and hostile-target confidence;
- candidate command rows by launcher and target;
- global, per-ship, per-target, and per-trigger cap state;
- skipped, failed, safety-blocked, and missing-evidence counts;
- an explicit statement that no live fleet-wide command was applied.

## Exclusion reason vocabulary

Use concrete reason names rather than vague summaries. Suggested categories:

- `notPlayerControlled`
- `notFriendly`
- `unknownControl`
- `unknownTeam`
- `nonCombatShip`
- `notMissileLauncher`
- `noVisibleMissileReadiness`
- `ambiguousLauncherIdentity`
- `ambiguousTargetIdentity`
- `noHostileTargets`
- `sameTeamTargetBlocked`
- `capWouldBlock`
- `missingBattleContext`

Exact enum/string names can follow existing code style, but the report must distinguish safety blocks from ordinary non-eligibility.

## Handoff condition to #43.2

Do not begin #43.2 until #43.1 can show fleet-wide eligibility, exclusions, candidates, caps, safety blocks, and missing evidence in a reviewable report or corpus-ready summary without requiring manual raw-log archaeology.

#43.2 should inherit the exact visibility surface that #43.1 establishes.

## Files likely relevant to Codex

- `dev-docs/plan/issue_43/00-context.md`
- `docs/diagnostics/experiment-corpus.md`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `dev-docs/plan/issue_39.1/00-context.md`
- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`
- `tools/summarize_experiment_corpus.py`
- `tools/fixtures/`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
