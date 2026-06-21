# Issue #24 implementation context: shadow allocation log-only fitting pass

## Purpose

Issue #24 is the pre-live fitting pass for the shadow allocator. The work should make real tactical-combat logs reusable for offline heuristic review before Issue #6 is allowed to consume the allocator as a live controlled-experiment baseline.

This is an observation-only model-validation issue. It may improve parser/report tooling, add an offline wrapper, classify observed shadow decisions, and record fitting conclusions. It must not apply Terra Invicta commands or change combat behavior.

## Current branch and local state

- Repo: `ti-missile-warfare` / `FennexFox/TI_Missile_Warfare`
- Local branch observed before writing this file: `issue_24`
- HEAD observed before writing this file: `61794c4dcd01798b55b659ebc2d8fafc62395e0c`
- Worktree observed before writing this file: clean
- This file is implementation context only. It does not implement the fitting pass.

## GitHub issue relationship

Primary issue:

- #24 `Shadow allocation log-only fitting pass`

Upstream/prerequisite evidence:

- #4 / PR #14 added observation-only `AllocationLog` diagnostics and parser recognition.
- #13 added allocation log parser/report summaries for tuning.
- #15 and #17 resolved the old readiness blocker by replacing legacy `readyShots` semantics with explicit `ammoGateBudgetShots` / `totalAmmoGateBudgetShots` semantics.
- #18 recovered target/relative velocity evidence.
- #19 formalized PD evidence/default reporting.
- PR #20 integrated the post-#17/#18/#19 evidence into diagnostics, parser, and docs.

Downstream consumers:

- #6 should use the #24 fitting result as its starting heuristic baseline once #21/#23 safety gates are satisfied.
- #21 and #23 are not prerequisites for #24 because #24 must remain log-only and command-free.
- #5 may later expose recommendations in UI/hotkeys, but #24 does not own UI polish.

## Hard safety boundary

Do not change or call any live command path while implementing #24.

Explicitly out of scope:

- target assignment
- launch commands
- fire-mode changes
- projectile behavior
- missile guidance
- ammo accounting changes
- AI behavior
- manual player-control mutation
- `SelectSalvoTargetCommand`
- `FleetSelectSalvoTargetCommand`
- `SetCombatPrimaryTargetAction`
- `SetWeaponModeAction`
- full game/UI automation, save loading, camera control, or battle execution

Allowed work:

- offline parser/reporting
- selected-log ingestion from repo-local ignored folders
- report artifact generation
- classification of already-emitted shadow allocation decisions
- diagnostics/model-only heuristic tuning when the log evidence justifies it
- durable notes recording findings and readiness for #6

## Current diagnostic evidence baseline

The current durable runtime history says the post-PR #20 smoke has the fields #24 needs for a first log-only fitting pass:

- `LaunchLog`: 6,701 entries
- `MissileWeapon.TryFire`: 748 rows
- `SnapshotLog`: 748 entries
- `AllocationLog`: 1,496 entries: 748 `cycle`, 748 `allocation`
- `ammoGateBudgetShots`: 748/748 numeric snapshot/cycle evidence
- total allocation-cycle ammo/gate budget: 5,998 shots
- target velocity evidence: 748/748 cycles
- `targetVelocityEvidenceSource=tryFireTargetDamageableVelocity`: 748/748 cycles
- relative velocity evidence: 748/748 cycles
- `relativeVelocityEvidenceSource=targetAndLauncherVelocity`: 748/748 cycles
- PD inputs: 0 observed, 748 defaulted, 0 unknown
- `pdWeightEvidenceSource=defaultModel`: 748/748 cycles
- `pdWeightDefaultReason=pdEvidenceUnavailable`: 748/748 cycles
- MissileWarfare issues: none

Interpretation for #24:

- The old blocker, “all cycles rejected due to missing shot budget,” is gone.
- Target/relative velocity are no longer the all-cycle missing input.
- The remaining major all-cycle limitation is PD being a formal default model, not observed target PD weapon recovery.
- A fitting pass must therefore treat PD-risk conclusions as provisional unless logs include direct PD evidence in the future.

## Existing files and responsibilities

### Core heuristic

- `src/MissileFireControl.Core/Allocation/SalvoAllocator.cs`
  - Sums `MissileInventorySnapshot.AmmoGateBudgetShots` into `TotalAmmoGateBudgetShots`.
  - Computes candidates from PD score, target value, salvo package, and best launch window.
  - Rejects outside launch windows and invalid packages.
  - Assigns kill packages first, or partial saturation when allowed.

- `src/MissileFireControl.Core/Calculators/PDScoreCalculator.cs`
  - Uses `WeaponSnapshot.PointDefenseWeight` plus support-PD weighting.
  - Current runtime diagnostics generally feed a default-model PD weight, not observed ship weapon weights.

- `src/MissileFireControl.Core/Calculators/TargetValueCalculator.cs`
  - Combines weapon threat, own PD removal value, hull class value, damage/vulnerability, and strategic priority.

- `src/MissileFireControl.Core/Calculators/SalvoPackageCalculator.cs`
  - Estimates saturation, kill, and overkill package sizes from PD score, target durability/armor, missile damage, and safety margin.

- `src/MissileFireControl.Core/Calculators/LaunchWindowEvaluator.cs`
  - Scores range, radial velocity, and lateral velocity.
  - Uses `MinimumLaunchScore`, range factor, receding/approaching/lateral velocity parameters.

### Runtime diagnostics wiring

- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
  - Runs shadow allocation only when mod enabled + diagnostics enabled + shadow allocation diagnostics enabled.
  - Builds `AllocationRequest` from `ExtractedCombatSnapshot`.
  - Emits `[AllocationLog]` records for `cycle`, `allocation`, `rejection`, and `noOp`.
  - Records `ammoGateBudgetShots`, evidence/missing reason, target/relative velocity evidence, PD evidence/default fields, assigned/unassigned shots, and missing inputs.
  - Must remain observation-only.

### Parser/reporting

- `tools/parse_player_log.py`
  - Parses `[LaunchLog]`, `[SnapshotLog]`, and `[AllocationLog]`.
  - Current allocation report summarizes:
    - shadow cycles / evaluated / skipped
    - future applied/skipped/failed command buckets
    - ammo/gate budget numeric/unknown cycles and totals
    - target/relative velocity evidence and missing reasons
    - PD observed/defaulted/unknown cycles
    - assigned/unassigned shots
    - allocation/rejection/no-op counts and reasons
    - average/median kill package, saturation size, launch-window score, score per shot
    - critical missing inputs
    - suspicious patterns such as all shots unassigned, too many launch-window rejects, repeated partial saturation, possible overkill, higher-value rejected target present, missing-input-limited report, and insufficient numeric data
  - Current CLI supports `--json`, `--max-issues`, `--require-launchlogs`, and `--require-snapshots`.

### Durable docs

- `docs/diagnostics/snapshot-and-allocation.md`
  - Current schema and parser behavior.
- `docs/diagnostics/runtime-validation-history.md`
  - Runtime smoke evidence and issue-by-issue validation history.
- `docs/research/readiness-semantics.md`
  - `ammoGateBudgetShots` semantics and validity window.
- `docs/planning/mvp-roadmap.md`
  - Issue state and downstream roadmap.

### Temporary implementation docs

- `dev-docs/plan/README.md`
  - This folder is for temporary per-issue / per-PR context.
- Suggested #24 temp docs:
  - `dev-docs/plan/issue_24/00-context.md` — this file.
  - `dev-docs/plan/issue_24/00-master-plan.md`
  - `dev-docs/plan/issue_24/01-planning-and-boundaries.md`
  - `dev-docs/plan/issue_24/02-wrapper-and-classification.md`
  - `dev-docs/plan/issue_24/03-docs-and-validation.md`

## Recommended implementation shape

### 1. Define selected-log input convention

Prefer an ignored, repo-local input folder so repeated fitting runs do not depend on the active `Player.log` path.

Candidate input locations:

- `artifacts/combat-logs/selected/`
- `logs/selected/`

The issue body allows either. Prefer `artifacts/combat-logs/selected/` if generated reports also live under `artifacts/`, because it keeps captured logs and generated fitting artifacts together and likely avoids accidentally committing large runtime logs.

Implementation note: verify `.gitignore` before relying on either path. Do not commit full `Player.log` samples unless they are intentionally small curated fixtures.

### 2. Add a repeatable wrapper command

Current parser can summarize one log. #24 wants a single wrapper command that can replay a selected log set and generate reviewable artifacts.

Possible wrapper:

```powershell
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\selected --output artifacts\shadow-fitting\latest
```

Alternative: extend `tools/parse_player_log.py` with multi-log/report arguments. A separate wrapper is probably cleaner because `parse_player_log.py` is already large and still serves as the core single-log parser/validator.

The wrapper should:

1. Discover `.log` / `.txt` files in the selected input directory.
2. Run or import the existing parser logic for each log.
3. Preserve per-log parser summaries, ideally JSON.
4. Produce an aggregate Markdown report.
5. Exit nonzero if required evidence is missing for all selected logs or parser validation fails.
6. Never require launching Terra Invicta.

### 3. Classify allocator decisions

Issue #24 needs categories beyond the current generic suspicious-pattern hints.

Recommended categories:

- `plausible`
- `overkill`
- `underkill`
- `late/out-of-window`
- `target-value mismatch`
- `PD-risk mismatch`
- `missing-evidence-limited`
- `impossible`
- `ambiguous`

Initial classification can be conservative and evidence-driven:

- Allocation rows with complete ammo/gate + target velocity + relative velocity evidence, no warnings, kill package assigned, and launch-window score above threshold can be `plausible` unless another rule flags them.
- Rejections with `outside estimated launch window` should be `late/out-of-window`; do not call them bad without battle context.
- Rows/cycles with `pdWeightDefaulted=True` should carry a PD evidence limitation marker; classify PD-risk claims as `missing-evidence-limited` or `ambiguous`, not “good/bad,” unless a future log has observed PD weights.
- `assignedShots > killSize` is `overkill`.
- `0 < assignedShots < saturationSize` is `underkill` or `impossible/ineffective partial`, depending on package semantics.
- `saturationSize <= assignedShots < killSize` is `partial saturation`; classify separately from under-saturation.
- Higher-value rejected target while lower-value allocated in the same cycle is a `target-value mismatch` candidate, but only if the rejection reason is not a hard launch-window failure.
- Unknown/zero ammo budget with allocation rows should be `impossible` or parser/schema inconsistency.

The classifier should prefer “ambiguous” over false certainty when the log cannot prove outcome quality.

### 4. Decide whether to tune the heuristic

Do not tune Core parameters just because a report looks odd. Tune only when the report identifies repeated, evidence-supported issues across the selected logs.

Likely tunable areas:

- `LaunchWindowOptions` if many plausible manual/combat launches are rejected as out-of-window despite strong velocity/range evidence.
- `SalvoPackageOptions` if repeated overkill/underkill appears with enough target durability/missile evidence.
- `TargetValueOptions` if target-value mismatch appears without hard launch-window or missing-evidence reasons.
- `PdScoringOptions` only after PD evidence is observed or the default model is explicitly accepted as a provisional assumption.

Any tuning change should update tests or at least parser/core validation and durable notes explaining the evidence.

### 5. Record the fitting verdict for #6

#24 must end by saying whether the shadow allocator is good enough to feed #6 controlled live experiments after #21/#23 safety gates pass.

Suggested verdict states:

- `Ready for #6 baseline`: selected logs show plausible allocations, no severe evidence-supported bad categories, and remaining gaps are documented.
- `Conditionally ready`: allocator can seed #6 but only for constrained scenarios, such as low-PD/default-PD acceptance, small selected missile groups, or specific target classes.
- `Not ready`: report finds repeated evidence-supported bad allocations or required evidence is still missing.

This verdict belongs in durable docs, probably `docs/diagnostics/runtime-validation-history.md` and/or a new durable note under `docs/diagnostics/` if the report format becomes substantial.

## Minimal implementation checklist

- [ ] Choose and document selected-log input path.
- [ ] Add or document a wrapper command that consumes selected logs and writes repeatable artifacts.
- [ ] Reuse `tools/parse_player_log.py` parser logic rather than duplicating key/value parsing.
- [ ] Add fitting/classification report fields for plausible/bad/ambiguous/evidence-limited decisions.
- [ ] Keep PD default-model limitations explicit.
- [ ] Add aggregate report output that is useful without reading raw log lines.
- [ ] Add at least one selected fresh/combat log to the local ignored input folder, or document the blocker if no log is available.
- [ ] Run parser validation with `--require-launchlogs --require-snapshots` against the selected sample(s).
- [ ] Run static validation commands.
- [ ] Record findings and #6 readiness verdict in durable docs.

## Validation commands from the issue

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py
python -m compileall tools
.\build.ps1
python tools\parse_player_log.py --require-launchlogs --require-snapshots
```

If a new wrapper is added, include it in validation, for example:

```powershell
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\selected --output artifacts\shadow-fitting\latest
```

If the wrapper imports parser internals, also run:

```powershell
python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
python -m compileall tools
```

## Risks

- Overfitting to one combat log.
- Treating PD default-model output as observed PD evidence.
- Treating shadow recommendation plausibility as proof of causal live combat improvement.
- Accidentally expanding into #6/#23 command application work.
- Letting generated log artifacts or full Player.log files become tracked unintentionally.

Mitigation:

- Keep reports evidence-labeled and conservative.
- Separate `classification` from `verdict`.
- Prefer repeated selected logs before heuristic tuning.
- Keep all live command paths out of the #24 diff.
- Check git status before/after generating artifacts.

## Open questions for implementation

1. Which exact input folder should be blessed: `artifacts/combat-logs/selected/` or `logs/selected/`?
2. Should selected logs be kept purely local/ignored, or should a tiny redacted fixture be committed for parser regression?
3. Should `tools/parse_player_log.py` expose a stable import API, or should the wrapper shell out to it and consume JSON?
4. What is the minimum log sample size before declaring `Ready for #6 baseline`?
5. Is the current PD default model acceptable for a conditional #6 baseline, or should #24 return `Conditionally ready` until observed PD weapon recovery exists?

## Suggested next action

Start with a no-behavior-change tooling slice:

1. Add `tools/fit_shadow_allocation.py` as a wrapper around selected logs.
2. Generate JSON + Markdown report artifacts under an ignored output folder.
3. Add conservative classification using existing parser fields.
4. Run it on the latest fresh log.
5. Record the fitting result and #6 verdict in durable docs.
