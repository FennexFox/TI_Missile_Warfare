# Issue #29 contexts for Codex

This file is context for Codex before it plans or implements Issue #29. It is not a phase plan. Codex should use this as background, inspect the repo, and then make its own implementation plan.

## Issue intent

Issue #29 should upgrade observed target point-defense evidence from simple presence/count-style evidence into a richer capability model where the runtime and decompiled-source evidence supports it.

The current system can observe target weapon templates whose `defenseMode` flag is true and emits that as `pdWeightEvidenceSource=observedTargetWeaponTemplates`. That is useful, but Issue #28 correctly classifies it as `presenceOnly`: it proves that a defense-mode template was observed, not that the mod has calibrated vanilla interception capability, cooldown/readiness, ammo, arc, range geometry, support behavior, or exact defensive pressure.

The goal of Issue #29 is to reduce that specific limitation without overclaiming. If the repo can observe only template presence, the report must still say presence-only. If it can observe template capability fields, live capability fields, or geometry-aware fields, the output should label those quality levels explicitly.

## Location of source and docs

Decompiled source of Terra Invicta is in `../TI_RE_Workspace`. Refer to `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master`to navigate the relevant missile fire control code. Do not include the decompiled source in the repo. It is only for local inspection.

## Relationship to nearby issues

- Issue #27 recovered observed target PD evidence by reading visible target weapon templates with `defenseMode=true`. Current `pdWeight` is a count-style signal, not a calibrated vanilla PD model.
- Issue #28 added the evidence-sufficiency layer. It keeps the four-log fitting baseline as `Ready for #6 baseline` while reporting evidence sufficiency as `Baseline-ready with named limitations`, and observed target PD evidence as `presenceOnly`.
- Issue #29 should upgrade the PD evidence quality if possible. It should not weaken the #28 distinction between parser health, fitting baseline readiness, evidence sufficiency, and controlled live command readiness.
- Issue #30/#32 context: the four-log sweep is parser-OK and fitting-baseline-ready after command-safety no-op classification. #29 should preserve that useful baseline while improving the named PD limitation.
- Issue #22 dry-run command-intent logging, Issue #23 live command safety, and Issue #6 controlled allocation remain separate. Do not implement live command behavior in Issue #29.

## Current observed PD evidence state

Current durable docs say decompiled-source review identified `TISpaceShipState` weapon template lists and `TIShipWeaponTemplate.defenseMode` as the conservative diagnostic signal. Vanilla defensive fire is represented by `DefenseFireMode`, available for defense-mode weapons, and uses projectile-defense range members such as `EffectiveRangeAgainstProjectiles_km()`.

Current runtime/documented behavior:

- When target templates and `defenseMode` are visible, diagnostics emit:
  - `pdWeightEvidenceSource=observedTargetWeaponTemplates`
  - `pdWeightDefaulted=False`
  - `pdWeightDefaultReason=none`
  - `pdWeightMissingReason=none`
- The scalar `pdWeight` is currently count-style.
- If the target object, template list, or defense-mode field is unavailable, diagnostics keep the explicit fallback:
  - `pdWeightEvidenceSource=defaultModel`
  - `pdWeightDefaulted=True`
  - `pdWeightDefaultReason=pdEvidenceUnavailable`
  - `pdWeightMissingReason=<specific reason>`

Issue #29 should keep this fallback/default distinction intact.

## Important code observations

The current extraction path is in `src/MissileFireControl.Mod/Adapters/CombatSnapshotExtractor.cs`.

Important current behavior:

- `ExtractTargetPointDefenseEvidence(...)` or the nearby target-PD extraction path reads target weapon templates.
- It checks `defenseMode` / `DefenseMode`.
- It already attempts to read range-like fields such as:
  - `EffectiveRangeAgainstProjectiles_km`
  - `effectiveRangeAgainstProjectiles_km`
  - `targetingRange_km`
  - `TargetingRangeKm`
- Even though `supportRange` is read, current scoring still does `evidence.PointDefenseWeight += 1.0` for each defense-mode weapon, so the scalar remains essentially a count of observed defense-mode templates.
- `WeaponSnapshot` already has fields that may be useful for richer PD representation:
  - `PointDefenseWeight`
  - `ThreatWeight`
  - `CanDefendOtherShips`
  - `SupportRangeKm`
  - `AmmoGateBudgetShots`
  - `RemainingShots`

The current logging path is in:

- `src/MissileFireControl.Mod/Diagnostics/SnapshotDiagnostics.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`

Those currently log `pdWeight`, `pdWeightEvidenceSource`, `pdWeightDefaulted`, `pdWeightDefaultReason`, and `pdWeightMissingReason`.

The parser/reporting path is in:

- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`

`parse_player_log.py` already aggregates PD evidence source/default/missing reason counts. `fit_shadow_allocation.py` currently uses those counts in `target_pd_status(...)`; after Issue #28, `observedTargetWeaponTemplates` maps to `presenceOnly`.

## Suggested evidence quality vocabulary

Issue #29 should consider explicit quality levels such as:

- `none`: no usable PD evidence.
- `defaultModel`: fallback model, no observed target PD capability.
- `observedPresenceOnly`: current defense-mode template presence/count evidence.
- `observedTemplateCapability`: template-derived capability fields are observed, such as support/projectile-defense range or other static weapon-template fields.
- `observedLiveCapability`: live target defensive weapon state is observed, such as ammo/gates/cooldown/readiness, if reachable and proven.
- `geometryAwareCapability`: capability incorporates engagement geometry such as distance, arc/coverage, target-to-projectile relation, or support range applicability.

Codex should inspect current source and decide exact field names. Prefer additive fields over ambiguous repurposing of `pdWeightEvidenceSource` alone.

Possible additive field families:

- `pdEvidenceQuality`
- `pdCapabilityEvidenceSource`
- `pdCapabilityWeight`
- `pdCapabilityRangeKm`
- `pdCapabilityWeaponCount`
- `pdCapabilityMissingReason`
- `pdCapabilityLimitations`

These names are suggestions, not requirements. The important requirement is that generated logs, parser output, fitting reports, and docs can tell the difference between presence-only evidence and richer capability evidence.

## Compatibility expectations

Preserve existing fields unless there is a deliberate migration:

- `pdWeight`
- `pdWeightEvidenceSource`
- `pdWeightDefaulted`
- `pdWeightDefaultReason`
- `pdWeightMissingReason`

Existing selected logs and synthetic fixtures should remain parseable. If new fields are absent in old logs, parser/fitting should gracefully classify the PD evidence as current/legacy `presenceOnly` or `defaultModel`, not fail.

If `pdWeight` remains, do not silently make it look calibrated unless docs and source evidence justify the new scale. A safe approach is to keep `pdWeight` backward-compatible and add separate capability fields/quality labels.

## Files Codex should inspect first

Start with these files:

- `src/MissileFireControl.Mod/Adapters/CombatSnapshotExtractor.cs`
- `src/MissileFireControl.Mod/Diagnostics/SnapshotDiagnostics.cs`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `src/MissileFireControl.Core/Models/WeaponSnapshot.cs`
- `src/MissileFireControl.Core/Calculators/PDScoreCalculator.cs`
- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`
- `tools/fixtures/shadow_allocation_synthetic.txt`
- `tools/fixtures/shadow_allocation_missing_target_noop.txt`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/planning/mvp-roadmap.md`
- `docs/research/readiness-semantics.md`
- `dev-docs/plan/issue_28/00-contexts.md`

If source-level confirmation is needed, inspect the local decompiled Terra Invicta reference. The decompiled source is outside this repo and must not be copied into it. Current local navigation context from #28 is:

- `../TI_RE_Workspace`
- `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master`

Useful decompiled-source questions:

- Which fields/methods define defense-mode weapon capability?
- Whether `DefenseFireMode` exposes projectile-defense range, cooldown, target selection, firing cadence, or support behavior.
- Whether target live ship state exposes current defensive weapon readiness, ammo, or cooldown in a safe observation-only way.
- Whether any geometry/arc/range condition can be read without changing game behavior.

## Boundaries

Do not implement Issue #22, #23, or #6 in this issue.
Do not apply game commands.
Do not change vanilla fire behavior.
Do not tune allocator scoring unless the issue explicitly requires it and the evidence model justifies it.
Do not claim a calibrated vanilla point-defense simulator unless the implementation actually observes enough source-backed fields.
Do not commit raw real combat logs or generated fitting artifacts under `artifacts/`.
Do not remove the #28 evidence-sufficiency distinction.

## Expected reporting outcome

A good #29 result should let reports say something more precise than the current all-or-nothing split:

- default-only PD evidence: `defaultModel` / `defaulted`
- current defense-mode template count: `observedPresenceOnly` / still `presenceOnly`
- template-derived capability evidence: `observedTemplateCapability` / probably `provisional` unless live state or geometry is also known
- live state evidence: `observedLiveCapability` when proven
- geometry-aware evidence: `geometryAwareCapability` when proven

After #29, `fit_shadow_allocation.py` should upgrade `target_pd_status(...)` only when the selected logs actually contain richer evidence. Logs with only `observedTargetWeaponTemplates` and no new capability fields should continue to report `presenceOnly`.

## Validation commands to consider

Use commands that match the final implementation, but these are the known useful checks:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_29_pd_capability
python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_29_synthetic
python -m compileall tools
python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_29
```

If fresh runtime evidence is collected after deploying a C# change, also run:

```powershell
python tools\parse_player_log.py --require-launchlogs --require-snapshots
```

## Acceptance reminders

Issue #29 should be considered successful only if the repo can distinguish current presence-only PD evidence from richer capability evidence in code, generated reports, and durable docs. If richer fields cannot be safely observed yet, the correct result is to document that limitation and keep #28's `presenceOnly` classification rather than overclaiming readiness.
