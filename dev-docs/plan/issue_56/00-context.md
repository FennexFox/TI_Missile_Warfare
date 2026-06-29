# Issue #56 context — Saturation-aware bounded-live target distribution

Remote issue: https://github.com/FennexFox/TI_Missile_Warfare/issues/56
Parent / umbrella: Issue `#43` fleet-wide controlled allocation
Origin: post-Issue `#43.4` tuning-readiness handoff

## Status

Issue `#56` is the first narrow behavior-tuning slice after Issue `#43.4`. It remains logically under the Issue `#43` fleet-wide controlled missile allocation path, but it is tracked as a separate issue so Issue `#43` can stay an umbrella / roadmap issue rather than accumulating another large behavior-changing slice.

This issue is no longer measurement-readiness work. Issue `#43.4` established the measurement boundary needed to begin a limited tuning loop. Issue `#56` should implement a small, explainable overcommit mitigation heuristic using the evidence Issue `#43.4` made available.

## Problem statement

The bounded-live path can repeatedly assign additional controlled missile packages to the same selected target even after controlled assigned shot pressure has reached or exceeded a reasonable `killSize` / `saturationSize` reference.

Recent Issue `#43.4` validation showed this pattern can occur while:

- real same-cycle hostile target alternatives exist;
- comparable target-level feature evidence exists;
- selected-target rank semantics are explicit;
- cap blocked-vs-applied comparison is available;
- in-flight pressure evidence is classified as exact / lower-bound / unknown.

The candidate problem is therefore not broad target-value mismatch. It is narrower:

> A top-ranked target may keep receiving additional bounded-live packages after controlled shot pressure already reaches or exceeds the target's kill or saturation scale.

## Measurement handoff from #43.4

Issue `#43.4` established and validated the following diagnostic surface:

- `targetAlternativeDenominator` identifies real same-cycle hostile target alternatives.
- `targetAlternativeFeatureEvidence=allocatorComparableFeatures` can provide comparable target-level features.
- `selectedTargetScoreSpace=launcherCandidateAllocation` and `targetAlternativeScoreSpace=diagnosticTargetAlternativeRecomputed` prevent candidate-level and target-level scores from being compared directly.
- `selectedTargetRankComparisonSpace=targetAlternativeScores` and `selectedTargetRankLevel=target-level` define selected-target rank semantics.
- prior in-flight pressure is classified by evidence quality:
  - exact when controller targets are recovered;
  - lower-bound when live missile count is visible but target attribution is not recovered;
  - unknown when no usable source exists.
- runtime validation confirmed `GameControl.spaceCombat._projectiles` can recover live missile target ids through active missile controllers for later applied rows.
- first-row lower-bound evidence may still occur when live missile count is visible before `MissileController.target` attribution is recoverable at the sampling hook.

The first-row lower-bound case is a diagnostic timing boundary. It is not evidence that the first missile was outside controlled command influence.

Do not move the pre-command pressure hook merely to eliminate that first-row lower-bound case. Moving the hook later could mix current-command launches into pre-command pressure; moving it earlier could reduce controller availability. If more precision is needed later, add a separate post-command or next-frame reconciliation field instead of changing the meaning of the pre-command sample.

## Scope

Issue `#56` may tune bounded-live target distribution using:

- prior controlled assigned shots;
- recovered in-flight pressure when evidence is exact;
- lower-bound pressure as diagnostic-only evidence for v1;
- `max(killSize, saturationSize)` as the first conservative pressure reference;
- same-cycle viable target alternatives from the #43.4 diagnostic surface.

The intended behavior change is small and explainable:

- recognize when the currently selected target is already at or beyond a controlled pressure threshold;
- prefer a viable alternative target when one exists and evidence supports retargeting;
- retain the current selected target when alternatives are unavailable, worse, blocked by caps/safety gates, or evidence quality is insufficient.

## Non-goals / boundaries

Do not use #56 to implement or change:

- outcome-based underkill / overkill tuning;
- target destruction or survival scoring;
- exact hit / damage / kill attribution; this remains #47;
- projectile physics;
- missile guidance;
- cooldowns;
- ammo accounting semantics;
- Terra Invicta weapon stats;
- vanilla salvo behavior;
- selected-ship distribution outside the bounded-live controlled path;
- broad command-authority policy;
- continuous or always-on automation.

Do not treat count-only live missile evidence as fully known selected-target pressure.

## Implementation direction

Prefer a conservative pressure-aware heuristic over broad weight retuning.

A reasonable first pass is to compute or reuse a target pressure signal such as:

```text
controlledAssignedPressure
+ recoveredInFlightPressure when exact
```

Then compare that pressure against `max(killSize, saturationSize)`.

For v1, lower-bound in-flight pressure should remain visible in diagnostics and
parser/corpus summaries, but it should not contribute to decision pressure or
trigger retargeting by itself. This keeps first-row hook-timing ambiguity from
changing behavior while preserving the evidence for later review.

The heuristic should avoid naked fixed shot-count thresholds. The threshold should scale with target-specific `killSize` / `saturationSize` and should remain explainable in diagnostics.

Possible decision shape:

```text
if selected target pressure is already beyond threshold
and viable same-cycle alternatives exist
and the alternative is not worse under comparable target-level evidence
and safety / cap / ammo gates allow it:
    retarget or deprioritize selected target for this bounded-live package
else:
    retain selected target
```

Exact policy details are intentionally left for implementation review, but the behavior must remain bounded, manual-command scoped, and diagnostic-heavy.

## Diagnostic expectations

Every changed decision should explain why it retained or retargeted the selected target, including:

- selected target id/name;
- alternative target id/name when retargeted;
- pressure inputs;
- pressure evidence quality;
- `killSize` / `saturationSize` reference;
- threshold / ratio used;
- whether same-cycle alternatives existed;
- whether cap/safety/ammo gates affected the decision.

Parser and corpus summaries should expose before/after counters for:

- same-target packages with denominator > 1;
- potential over-concentration candidates;
- retained selected-target decisions above threshold;
- retargeted decisions above threshold;
- exact vs lower-bound in-flight pressure buckets;
- any evidence-limited cases.

## Acceptance criteria carried from the remote issue

- Bounded-live allocation considers prior controlled assigned shots when deciding whether to assign another package to the same target.
- Exact recovered in-flight pressure is included in decision pressure; lower-bound pressure remains diagnostic-only for v1, and exact/lower-bound rows remain distinguishable in diagnostics.
- Targets at or beyond the chosen controlled pressure threshold are deprioritized or retargeted when viable same-cycle alternatives exist.
- The heuristic uses `max(killSize, saturationSize)` as the first conservative pressure reference rather than a naked fixed shot count.
- Existing bounded-live safety gates, per-ship caps, ammo accounting, command authority, and manual control behavior are preserved.
- Diagnostics explain why a target was retained or retargeted, including pressure inputs and evidence quality.
- Parser/corpus summaries expose enough counters to compare before/after same-target package concentration and lower-bound/exact evidence buckets.
- Fresh runtime validation demonstrates the new behavior on bounded-live logs without MissileWarfare warnings/errors.
- Any remaining outcome-evaluation limitation is explicitly handed off to #47 rather than solved here.

## Validation expectations

Use the normal repository validation flow plus fresh bounded-live Player.log import/summarization when available.

Generated artifacts under `artifacts/` and private raw `Player.log` files must remain uncommitted.

The final report should state:

- what pressure threshold policy was implemented;
- what evidence sources contributed to pressure;
- how exact and lower-bound in-flight pressure were treated;
- whether same-target concentration was reduced in fresh runtime validation;
- whether any safety/cap/ammo behavior changed;
- what remains blocked pending #47.
