# Issue #34 context

This is local context for Codex planning. It is not a phased implementation plan or a detailed work order. Codex should use it to build its own phased implementation plan for #34.

## Role in #6

Issue #34 is the first controlled-experiment envelope, but it must remain diagnostics-only. It should create the ability to explicitly trigger a controlled allocation experiment dry-run, tag the run with an experiment id, capture selected player ship context when visible, connect the run to shadow allocator intent, and make parser/report output group the resulting log without manual line-by-line analysis.

The core question for this slice is: can the mod describe a controlled experiment attempt end-to-end without applying any live combat command?

## Safety boundary

#34 must not apply live commands. It should not call vanilla target/launch/salvo command APIs, should not change target assignments or weapon mode, and should not alter AI ships, unselected player ships, projectile physics, missile guidance, cooldowns, or ammo accounting.

The output should be compatible with later command-planning work, but this slice should produce `0 applied` by construction.

## Existing context to preserve

- #4 supplies shadow allocation diagnostics and parser/reporting support.
- #21 verifies the safe selected-player scope. The safe scope is the tactical command panel single selected ship or group-selected ship list, not the left-hand player-side combatant list.
- `ShadowAllocationDiagnostics` currently runs from projectile-fire evidence when shadow allocation diagnostics are enabled and emits `[AllocationLog] recordType="cycle"`, `allocation`, `rejection`, and `noOp` rows.
- `tools/parse_player_log.py` already has future controlled-apply buckets for applied/skipped/failed records, but #34 needs a distinguishable controlled dry-run grouping, not a fake applied command.
- `ammoGateBudgetShots` is the current validated budget term. Avoid `readyShots`.

## Planning information for Codex

The implementation plan should decide where the explicit dry-run trigger belongs. A minimal UMM panel button or similarly explicit diagnostic trigger is acceptable for the slice, as long as it is disabled by default and clearly separate from passive shadow allocation. The UI does not need to be polished.

The plan should decide how to represent experiment identity. The id only needs to be stable enough to group one triggered experiment in logs and parser output. It can be simple and local, but it should not be confused with allocation `cycleId` alone. Future slices will need to connect experiment id, decision id/cycle id, selected ship identity, command candidate, and result class.

The plan should decide whether controlled dry-run rows remain under `[AllocationLog]` or use another marker. If they remain under `[AllocationLog]`, parser known-record-type handling should avoid classifying them as unknown. If a new marker is used, parser/report support should still surface the experiment summary near allocation summaries.

The selected-ship snapshot can be partial. Unknown fields should be explicit. It is better for #34 to log `selectedScopeUnavailable` or similar evidence gaps than to guess from broad fleet lists.

## Parser/report expectations

The parser/report should be able to show a controlled dry-run experiment separately from normal shadow allocation. Useful report-level concepts include experiment count, experiment id, selected ship count where visible, intended/dry-run command count, skipped/missing-evidence count if applicable, and applied count equal to zero.

The #34 report does not need to prove command resolvability. That belongs to #35. It only needs to prove that the experiment envelope and grouping exist and stay no-op.

## Useful validation context

The issue body lists these validation families:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
python -m compileall tools
python tools\parse_player_log.py <fresh-player-log> --require-launchlogs --require-snapshots
python tools\fit_shadow_allocation.py --input <fresh-log-dir> --output artifacts\shadow-fitting\controlled_dry_run
```

For a docs/planning-only pre-pass, static validation may be enough. For the actual #34 implementation, the plan should distinguish static checks, parser fixture checks, and manual runtime smoke.

## Non-obvious risk

The biggest #34 risk is accidentally letting the dry-run path become a command path. Treat the dry-run trigger as experiment logging, not command application. If selected scope is not visible from current runtime hooks, the safe result is a grouped experiment with explicit missing selected-scope evidence, not a broadened scope.
