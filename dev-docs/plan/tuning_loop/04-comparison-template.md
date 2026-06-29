# Phase 04: Baseline/follow-up comparison template

## Purpose

Use this template to compare a baseline bounded-live pressure-aware run with a
follow-up run after one narrow tuning change. The template is deliberately
conservative: it should make regression and evidence-quality problems visible
before claiming that a heuristic improved.

## Required inputs

- Baseline commit SHA.
- Follow-up commit SHA or local diff identifier.
- Baseline corpus summary path.
- Follow-up corpus summary path.
- Baseline parameter snapshot.
- Follow-up parameter snapshot.
- Runtime settings/toggles for both runs.
- Notes on scenario comparability.

## Run identity

```text
comparisonId:
baselineCommit:
followupCommitOrDiff:
baselineSummary:
followupSummary:
baselineCandidateId:
followupCandidateId:
runMode:
scenarioTags:
rawLogsPrivate: yes
```

## Comparability checklist

Mark each item `same`, `different`, `unknown`, or `not applicable`.

| Check | Status | Notes |
| --- | --- | --- |
| Terra Invicta version |  |  |
| Mod branch/commit recorded |  |  |
| Same run mode |  |  |
| Same command caps unless intentionally changed |  |  |
| Same diagnostics toggles |  |  |
| Same scenario/fleet family |  |  |
| Same missile family or comparable weapon family |  |  |
| Raw logs private and not committed |  |  |
| Parser verdict OK |  |  |
| Outcome hooks, if enabled, used only as validation context |  |  |

If a core comparability item is `different` or `unknown`, the likely verdict is
`invalid comparison` or `inconclusive` unless the difference is explicitly part
of the candidate.

## Objective metrics

Compare these counters first.

| Metric | Baseline | Follow-up | Direction desired | Interpretation |
| --- | ---: | ---: | --- | --- |
| boundedLiveAppliedResults |  |  | explainable | More is not automatically better. |
| boundedLiveAppliedWithTargetAlternativeDenominatorGtOne |  |  | enough evidence | Needed for retarget review. |
| boundedLiveAppliedWithComparableAlternativeFeatures |  |  | enough evidence | Needed for fair alternative comparison. |
| boundedLiveAppliedWithFullyComparableScoreRankEvidence |  |  | enough evidence | Needed for rank/score interpretation. |
| boundedLiveAppliedWithKnownPriorInFlightPressure |  |  | up or stable | Exact/known pressure improves interpretability. |
| boundedLiveAppliedWithLowerBoundPriorInFlightPressure |  |  | down or isolated | Lower-bound rows stay diagnostic-only. |
| boundedLiveRetainedSelectedTargetDecisionsAboveThreshold |  |  | down | Primary over-pressure reduction signal. |
| boundedLiveRetargetedDecisionsAboveThreshold |  |  | up if alternatives exist | Primary pressure-aware retarget signal. |
| boundedLiveLowerBoundPressureDiagnosticOnlyRows |  |  | not used as success | Must remain diagnostic-only. |
| potentialOverConcentrationCandidates |  |  | down | Candidate-level overconcentration signal. |
| potentialCapMisallocationCandidates |  |  | down or zero | Cap interaction signal. |

## Guardrail checks

Any hard guardrail failure blocks a supportive verdict.

| Guardrail | Baseline | Follow-up | Pass/Fail | Notes |
| --- | --- | --- | --- | --- |
| Parser verdict OK |  |  |  |  |
| MissileWarfare warnings/errors zero |  |  |  |  |
| same-team target markers zero |  |  |  |  |
| scope-violation markers zero |  |  |  |  |
| failed command counts zero or explained |  |  |  |  |
| skipped commands explainable |  |  |  |  |
| direct command-spend evidence preserved |  |  |  |  |
| vanilla / none-correlated spillover not counted as controlled spend |  |  |  |  |
| lower-bound pressure not used as retarget success |  |  |  |  |
| no outcome-aware scoring introduced |  |  |  |  |
| no command-authority or scope expansion |  |  |  |  |

## Blocker deltas

Track hard measurement blockers separately from external outcome blockers.

| Blocker | Baseline | Follow-up | Interpretation |
| --- | ---: | ---: | --- |
| prior in-flight target attribution unavailable for observed live missiles |  |  | Hard measurement blocker. |
| exact outcome attribution pending OutcomeLog correlation |  |  | External outcome blocker; not a pressure-loop blocker. |
| missing comparable target-alternative features |  |  | Hard comparison blocker. |
| ambiguous selected-target rank or score space |  |  | Hard comparison blocker. |

## Verdict vocabulary

Use exactly one verdict.

- `supportive`: objective metrics moved in the intended direction and guardrails
  held.
- `contradictory`: objective metrics moved against the intended direction or a
  hard guardrail failed.
- `no material change`: comparable run, but objective metrics did not move enough
  to justify the change.
- `invalid comparison`: scenario, settings, caps, evidence quality, or parser
  health changed enough that the comparison cannot be used.
- `inconclusive`: evidence is too sparse or ambiguous to classify.

## Verdict recommendation

```text
verdict:
confidence: low|medium|high
primaryReason:
secondaryReasons:
regressions:
nextAction:
```

## Human review notes

Use this section for causal caveats that the counters cannot capture.

Examples:

- enemy composition differs materially;
- missile family differs;
- target alternatives existed but were not tactically comparable;
- applied commands were too sparse;
- cap blocks dominate the result;
- outcome rows show hook health but are not joined to allocation rows.

## Output location

For local ignored comparisons, use:

```text
artifacts/fitting/<candidate-or-comparison-id>/comparison.md
```

For durable docs or issue notes, copy only the non-private summary and omit raw
log paths.
