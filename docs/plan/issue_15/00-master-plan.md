# Wire live weapon readiness evidence into allocation snapshots

## Issue Target And Scope Summary

- Issue target: #15
- Title: Wire live weapon readiness evidence into allocation snapshots
- Source plan: `.chatgpt/codex-runs/2026-06-20T000000Z-issue-15-readiness-evidence/PROMPT.md`
- Scope: diagnostic-only readiness evidence for snapshot and shadow allocation logs.

Issue #15 must make `SnapshotLog`, `AllocationLog`, and `tools/parse_player_log.py`
distinguish proven numeric ready shots from ammo-only, gate/cooldown-only, and unknown
readiness. The shadow allocator remains observation-only. No combat command, launch
suppression, targeting, AI, projectile, physics, or guidance behavior changes are in
scope.

## Strategy

1. Preserve the current `int` ready-shot fields for Core allocator compatibility, but
   add explicit optional evidence metadata to missile inventory and weapon snapshots.
2. Remove the optimistic projectile-snapshot mapping that treats reflective names such
   as `loadedAmmo`, `loadedMissiles`, or `readyMissiles` as proven ready shots without
   source semantics.
3. Allow `readyShots` to become numeric only through a narrow helper that records a
   `readyShotEvidenceSource` whose semantics are true ready/loaded/chambered evidence.
   If no such source is proven, keep `readyShots=-1` / log `readyShots="unknown"`.
4. Keep ammo and gate/cooldown observations as evidence context, not allocator-ready
   counts. For the current runtime state this means `readinessMissingReason` should say
   why readiness is unknown rather than promoting `preFireRemaining`.
5. Propagate readiness metadata through `SnapshotLog` and `AllocationLog` cycle records.
6. Extend the parser report and JSON summary with readiness source and missing-reason
   histograms while preserving parsing of older logs.
7. Update docs and write the run `RESULT.md`.

## Phase Order

1. [Discovery and safety boundaries](01-discovery.md)
2. [Readiness evidence model and diagnostics logs](02-model-logs.md)
3. [Parser reporting and documentation](03-parser-docs.md)
4. [Validation and result handoff](04-verification.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on phase 1's source-of-truth decisions about readiness semantics.
- Phase 3 depends on the Phase 2 log field names and model behavior.
- Phase 4 depends on all code, parser, docs, and result artifacts being complete.

## Source Of Truth Decisions

- `docs/plan/issue_15/00-master-plan.md` is the implementation source of truth for this
  run.
- The GitHub issue and reviewed prompt are authoritative for scope and non-goals.
- `docs/battle-snapshot-extractor.md` and `docs/confirmed-hooks.md` are authoritative
  for current runtime findings: pre/post ammo evidence is not true ready-shot evidence.
- `readyShots` may be numeric only when a concrete runtime member with ready/loaded/
  chambered semantics is identified and logged as `readyShotEvidenceSource`.
- Current ammo dictionary evidence from `TISpaceShipState.ammo[weaponData]` remains
  ammo evidence only.
- The plan lives under `docs/plan/issue_15` because the issue prompt explicitly allows
  that path for focused Issue #15 docs.

## Global Validation Expectations

- `dotnet build TI_Missile_Fire_Control.sln`
- `python tools\check_layout.py`
- `python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py`
- `python -m compileall tools`
- `python tools\parse_player_log.py --require-launchlogs --require-snapshots`
- `python tools\parse_player_log.py --json --require-launchlogs --require-snapshots`

Runtime smoke after deploying the mod still requires a fresh Terra Invicta combat log and
is expected to be documented as not run in this repository-only implementation pass.

## Known Risks And Assumptions

- There may be no proven true ready/loaded/chambered runtime source in the current hooks.
  In that case the correct Issue #15 result is still `readyShots=unknown` with precise
  evidence and missing-reason fields.
- Parser changes must be optional-field tolerant so old logs still parse.
- Shadow allocation currently clamps unknown ready shots to zero when building an
  observation-only allocation request. That can remain only if logs still expose unknown
  readiness clearly and reject missing ready shots.
- The repository may not have a live `Player.log` with the latest build deployed; parser
  validation on the existing log is a parser smoke, not runtime proof of new fields.
