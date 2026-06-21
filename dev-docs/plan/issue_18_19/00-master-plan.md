# Issue #18/#19 Master Plan

## Issue Target and Scope

Implement diagnostics-only evidence recovery for:

- #18 target/relative velocity evidence in snapshot and allocation logs.
- #19 explicit point-defense weight evidence/default reporting.

The scope is limited to observation, parser reporting, and documentation. No controlled allocation commands or gameplay behavior changes are in scope.

## Strategy

1. Preserve whether target velocity was read from runtime combat state instead of treating a zero vector as equivalent to missing evidence.
2. Derive relative velocity only when target velocity and launch/origin velocity are both present.
3. Keep the current PD weight default model, but log it explicitly as `defaultModel` with a named default reason.
4. Extend `tools/parse_player_log.py` to report coverage, source, default, and missing-reason breakdowns.
5. Update diagnostics documentation to match the emitted schema.

## Phase Order

1. Evidence fields and log emission.
2. Parser/report summaries.
3. Documentation and validation.

Each phase leaves the project buildable and keeps shadow allocation observation-only.

## Source-of-Truth Decisions

- Current-use shot budget terminology remains `ammoGateBudgetShots` / `totalAmmoGateBudgetShots`.
- `pdWeightsDefaulted` remains a limitation marker while direct PD evidence is unavailable, but it is no longer opaque because `pdWeightEvidenceSource`, `pdWeightDefaulted`, and `pdWeightDefaultReason` are emitted.
- Relative velocity is not derived from stale history or cross-session state.

## Validation

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py
python -m compileall tools
python tools\parse_player_log.py --require-launchlogs --require-snapshots
```

Manual runtime smoke still requires deploying the mod and capturing a fresh missile-heavy `Player.log`.
