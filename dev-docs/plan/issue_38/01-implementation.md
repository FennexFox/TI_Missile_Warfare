# Phase 01: Selected-group implementation and parser reporting

## Goal

- Allow a small explicit selected player missile group to participate in the controlled experiment and make parser output group-aware.

## Scope

- Accept selected command-panel groups of one to three ships.
- Reject empty, too-broad, mixed-team, non-player/AI, active-player fallback, and ambiguous selected scopes for live apply.
- Attribute each group candidate/result row to one selected ship.
- Enforce one live command attempt per selected ship and three live attempts per trigger.
- Add parser summaries for controlled apply counts by experiment and by ship, plus assigned/spent evidence fields where visible.
- Add a deterministic synthetic fixture for selected-group reporting.

## Non-goals

- No continuous automation.
- No commands for unselected ships or AI ships.
- No fleet-wide eligibility; #43 owns that scope.
- No allocator tuning or heuristic parameter changes.
- No projectile physics, missile guidance, cooldown, or ammo mutation changes.

## Affected files

- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `src/MissileFireControl.Mod/Main.cs`
- `tools/parse_player_log.py`
- `tools/fixtures/selected_group_controlled_apply.txt`

## Implementation steps

- Add selected-group constants and persistent per-trigger attempted-ship tracking.
- Resolve selected group members by stable id, team, runtime object, and per-ship command readiness.
- Update candidate construction so selected groups larger than one require the allocator launcher to be in the selected group.
- Replace the single live-attempt gate with per-ship and per-trigger caps.
- Add command result fields for trigger cap, selected-group size, selected ship attribution, missiles assigned, and missiles spent visibility.
- Extend parser counters and printed summaries for by-experiment and by-ship controlled results.
- Add a selected-group fixture with two applied rows and one skipped/capped or waiting-safe row.

## Acceptance criteria

- Controlled command application remains disabled by default.
- Live command application requires the explicit controlled trigger and `AllowCommandApply=True`.
- Only selected command-panel ships with player-controlled evidence are eligible.
- Selected groups above three ships skip/fail closed.
- Each selected ship can attempt at most one live command per trigger.
- A trigger can attempt at most three live commands.
- Parser/report summarizes applied/skipped/failed counts by experiment and by ship.
- Parser/report prints assigned shot totals and reports spent evidence as unknown unless visible.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\selected_group_controlled_apply.txt --require-launchlogs --require-snapshots

## Manual smoke tests

- Deploy the mod, enter tactical combat, select two or three player missile ships, enable controlled diagnostics and `AllowCommandApply`, trigger once, then parse the fresh log.
- Confirm only selected ships are affected and the parser reports no scope violations, no same-team missile target snapshots, and no MissileWarfare warnings/errors.
- Confirm manual control remains available after the bounded command attempts.

## Rollback risks

- Disable `AllowCommandApply` to restore diagnostics-only behavior at runtime.
- Revert this phase to return to the #37 selected-single-ship apply boundary.

## Progress

- Completed.

## Decision log

- Selected groups are capped at three ships, matching the issue's two-to-three ship rung and preserving #43 as the later fleet-wide expansion.
- For groups larger than one, the selected command ship must match the allocator snapshot launcher id. The #37 single-selected-ship fallback remains only for exactly one selected ship.
- Post-gate attempts are tracked on the controlled experiment request so requeued cycles can apply at most one command per selected ship and at most three commands total.
- `missilesSpent` is emitted and parsed, but remains `unknown` until runtime rows can directly prove command-result spend evidence.
- Parser output now reports selected group members plus controlled live apply counts by experiment and by selected ship.

## Outcomes / Retrospective

- Added selected-group live apply caps and per-ship attribution in `ShadowAllocationDiagnostics`.
- Added selected player/non-AI evidence checks for selected command-panel scope.
- Updated the UMM label from single selected ship to selected group capped apply.
- Extended parser summaries with selected group members, counts by experiment, counts by ship, assigned shots by ship, spent shots by ship when visible, and mismatch evidence counters.
- Added `tools/fixtures/selected_group_controlled_apply.txt` for selected-group parser validation.
