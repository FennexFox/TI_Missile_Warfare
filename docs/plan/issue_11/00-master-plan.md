# Recover ready missile shot count in snapshot diagnostics

## Issue Target And Scope Summary

- Issue target: #11
- Title: Recover ready missile shot count in snapshot diagnostics
- Source plan: GitHub issue #11 plus Issue #10 runtime findings in `docs/battle-snapshot-extractor.md`.
- Scope: identify a reliable observation-only source for ready/loaded/chambered missile shot count, expose it in snapshot diagnostics when available, and keep `readyShots=unknown` valid when the source is unavailable.

## Strategy

Start from evidence, not inference. The current projectile-state snapshot hook can recover launcher, missile template, launcher-selected target identity, and remaining magazine-like counts, but the latest smoke tests still report `readyShots=unknown` for every snapshot. Because ready/loaded/chambered state likely lives on the live `MissileWeapon` or module runtime object, inspect that path first and add compact diagnostics only after a candidate member is documented.

Keep the feature diagnostics-only. Do not change launch timing, launch permission, ammo consumption, target selection, allocation, projectile physics, or hook selection unless a later phase explicitly documents why a new observation point is required.

## Phase Order

1. [Ready-shot source discovery](01-discovery.md)
2. [Add log-only ready-shot evidence](02-diagnostics.md)
3. [Runtime validation and documentation](03-verification.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.
- Phase 3 depends on completion and validation of phase 2.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation plan source of truth.
- Phase files in this directory define phase-local scope and validation.
- GitHub issue #11 is the product requirement source of truth.
- `docs/battle-snapshot-extractor.md` records runtime evidence and confirmed limitations.
- Decompiled Terra Invicta source under `../TI_RE_Workspace` is reference-only and must not be changed or copied into committed source.

## Global Validation Expectations

- dotnet build TI_Missile_Fire_Control.sln
- python tools/check_layout.py
- python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py
- python -m compileall tools
- .\build.ps1
- python tools/parse_player_log.py --require-launchlogs --require-snapshots

## Known Risks And Assumptions

- `remainingShots` is visible but must not be treated as `readyShots` unless source semantics are documented.
- Ready-shot state may be transient and weapon-specific; a ship-level projectile snapshot may never have enough context.
- Extra reflection inside high-volume combat logs can hurt runtime performance, so diagnostics should be compact and only enabled behind `EnableSnapshotDiagnostics`.
- If a new observation point is needed, it should be postfix/log-only and should not alter combat state.
