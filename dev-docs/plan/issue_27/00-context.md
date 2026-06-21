# Issue #27 Execution Context: Observed Target PD Evidence Recovery

Target repo path:

```text
dev-docs/plan/issue_27/00-context.md
```

## Purpose

Issue #27 is a reverse-engineering and diagnostics slice for recovering observed target point-defense evidence during tactical combat.

It follows Issue #24, which completed the log-only shadow allocation fitting workflow, but left the selected-log result limited by target point-defense evidence being defaulted rather than observed.

The important distinction:

```text
Issue #24 = fitting workflow exists and can classify allocator behavior from logs.
Issue #27 = recover observed target PD evidence so fitting can evaluate PD-risk meaningfully.
```

Issue #27 should not start as parser/fitting tuning. It should start as runtime source discovery.

## Current problem

Current diagnostics emit target PD as an explicit default model rather than observed evidence.

The current extraction behavior is effectively:

```csharp
snapshot.PdWeight = 0.0;
snapshot.PdWeightEvidenceSource = "defaultModel";
snapshot.PdWeightDefaulted = true;
snapshot.PdWeightDefaultReason = "pdEvidenceUnavailable";
snapshot.PdWeightMissingReason = "none";
```

This means current fitting reports can say `PD-risk mismatch: 0`, but that does **not** prove PD-risk behavior is validated. It only means the fitting workflow did not observe enough target PD evidence to classify against.

The current Issue #24 result should therefore be interpreted as:

```text
Conditionally ready, PD-default-limited, one-real-log baseline.
Not full #6 readiness.
```

## Relationship to previous RE work

Issue #21 was also a prerequisite RE slice for #6, but it covered a different axis.

```text
Issue #21 = selected-player command scope and command-path safety.
Issue #27 = target point-defense evidence quality for allocator/fitting decisions.
```

Both matter for #6, but they answer different questions:

```text
#21: Which selected friendly ships/weapons can a controlled helper safely affect?
#27: Can allocator fitting observe target PD capability well enough to judge PD-aware allocations?
```

## Start here

Inspect these files first:

```text
src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs
tools/parse_player_log.py
tools/fit_shadow_allocation.py
docs/diagnostics/snapshot-and-allocation.md
docs/diagnostics/runtime-validation-history.md
docs/planning/mvp-roadmap.md
```

Primary runtime investigation should start around `ShadowAllocationDiagnostics.cs`, especially the snapshot extraction path that currently emits `pdWeightEvidenceSource=defaultModel`.

Parser and fitting changes should be secondary and should only adapt outputs once runtime can emit richer PD evidence.

## Location of source and docs

Decompiled source of Terra Invicta is in `../TI_RE_Workspace/`. Refer to `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master` to navigate the relevant decompiled classes and methods. Do not include any decompiled source in the repo; it is only for local RE reference.

## What to look for in Terra Invicta combat state

Find whether the target ship exposes any reliable point-defense capability during combat.

Candidate evidence sources:

```text
- Target ship mounted weapon/module list.
- Whether a mounted weapon/module can perform point defense.
- Weapon cooldown/readiness state.
- Weapon ammo or disabled/damaged state, if exposed.
- Existing combat defensive-fire or interception scoring.
- Any target ship threat/defense summary used by vanilla combat AI.
- Any runtime relation between incoming projectiles and defensive-fire candidates.
```

The minimum useful output is not a perfect PD simulator. The minimum useful output is an observed, conservative diagnostic signal such as:

```text
target has observed PD-like capability: yes/no
observed PD weight/source/reason: scalar or structured evidence
evidence status: observed / partial / defaulted / unavailable
```

## Desired diagnostics shape

Diagnostics should distinguish observed evidence from fallback defaults.

At minimum, aim for:

```text
pdWeightEvidenceSource=observed...
pdWeightEvidenceSource=defaultModel
pdWeightDefaulted=true|false
pdWeightDefaultReason=...
pdWeightMissingReason=...
```

A richer structure is acceptable if scalar `pdWeight` is too lossy, but the fitting/reporting path must still be able to summarize whether PD evidence was observed or defaulted.

## Non-goals

Do not use Issue #27 to change behavior.

Explicit non-goals:

```text
- No live command path changes.
- No target command application.
- No fire mode changes.
- No projectile behavior changes.
- No AI/player-control changes.
- No SalvoAllocator tuning in the initial RE pass.
- No treating heuristic guesses as observed PD evidence.
- No committed real Player.log fixtures.
```

Real combat logs should remain local/ignored under:

```text
artifacts/combat-logs/selected/
```

Generated fitting outputs should remain local/ignored under:

```text
artifacts/shadow-fitting/latest/
```

## Acceptable outcomes

Issue #27 can end in one of three valid states.

### 1. Observed PD evidence recovered

Runtime diagnostics can emit non-default target PD evidence for at least one selected local combat log.

Expected follow-up:

```text
- Update parser/fitting reports to distinguish observed-vs-default PD.
- Run tools/fit_shadow_allocation.py on selected logs.
- Update docs to say whether #6 is still PD-limited.
```

### 2. Partial evidence recovered

Runtime diagnostics can identify some PD-relevant evidence, but not enough for a confident scalar.

Expected follow-up:

```text
- Emit partial evidence with explicit reason fields.
- Keep default markers when confidence is insufficient.
- Document the remaining limitation.
```

### 3. No reliable source found

If no reachable runtime source exists, document the inspected classes/methods and why they are insufficient.

This is still a useful RE result.

Expected follow-up:

```text
- Keep #6 full readiness blocked, or explicitly scope #6 as a PD-blind controlled baseline.
- Do not silently treat defaultModel as validation.
```

## Validation workflow

Build/static validation:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py
python -m compileall tools
```

Log/fitting validation once diagnostics are updated:

```powershell
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\selected --output artifacts\shadow-fitting\latest
python tools\parse_player_log.py --require-launchlogs --require-snapshots
```

Manual validation:

```text
1. Run a tactical combat where at least one enemy target is known or likely to have PD.
2. Keep the generated Player.log local/ignored.
3. Confirm SnapshotLog/AllocationLog contains observed or partial PD evidence.
4. Confirm reports distinguish observed PD from defaultModel.
5. Confirm no live command behavior changed.
```

## Key warning for #6 readiness

Do not let Issue #24's `Conditionally ready` result become full #6 readiness by accident.

The intended readiness interpretation is:

```text
#24 complete: yes, for log-only fitting workflow.
#6 conditional baseline: possible, but PD-default-limited.
#6 full readiness: blocked until Issue #27 recovers observed PD evidence
                 or #6 is explicitly scoped as a PD-blind controlled experiment.
```
