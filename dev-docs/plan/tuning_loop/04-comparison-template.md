# Phase 04: Offline fitting comparison template

## Purpose

Use this template to review archived-log candidate replay or corpus-summary
comparisons. It is deliberately conservative: it should make evidence-quality
problems visible before claiming that a heuristic is worth live validation.

This template does not prove live combat improvement. It filters candidates for
later controlled-live or fleet-wide-controlled validation.

## Required inputs

- Dataset or corpus summary path.
- Candidate policy id and parameter snapshot.
- Baseline/current policy id and parameter snapshot.
- Mod commit or local diff identifier for generated artifacts.
- Evidence-mode mix: `shadow-replay`, `controlled-live`,
  `fleet-wide-controlled`, `fixture`.
- Notes on scenario/fleet/log comparability.
- Raw-log privacy note.

## Run identity

```text
comparisonId:
datasetOrSummary:
baselineCandidateId:
followupOrReplayCandidateId:
parameterSnapshotHash:
modCommitOrDiff:
evidenceModes:
scenarioTags:
rawLogsPrivate: yes
```

## Comparability checklist

Mark each item `same`, `different`, `unknown`, or `not applicable`.

| Check | Status | Notes |
| --- | --- | --- |
| Terra Invicta version |  |  |
| Mod branch/commit recorded |  |  |
| Evidence modes separated |  |  |
| Same run mode where before/after comparison is claimed |  |  |
| Same command caps unless intentionally changed |  |  |
| Same diagnostics toggles |  |  |
| Same scenario/fleet family or grouped separately |  |  |
| Same missile family or comparable weapon family |  |  |
| Raw logs private and not committed |  |  |
| Parser verdict OK |  |  |
| Outcome hooks, if enabled, used only as validation context |  |  |

If a core comparability item is `different` or `unknown`, the likely verdict is
`invalid comparison` or `inconclusive` unless the difference is explicitly part
of the candidate or the report groups the rows separately.

## Objective metrics

Compare these counters first.

| Metric | Baseline/current | Candidate/replay | Direction desired | Interpretation |
| --- | ---: | ---: | --- | --- |
| boundedLiveAppliedResults |  |  | explainable | More is not automatically better. |
| boundedLiveAppliedWithTargetAlternativeDenominatorGtOne |  |  | enough evidence | Needed for retarget review. |
| boundedLiveAppliedWithComparableAlternativeFeatures |  |  | enough evidence | Needed for fair alternative comparison. |
| boundedLiveAppliedWithFullyComparableScoreRankEvidence |  |  | enough evidence | Needed for rank/score interpretation. |
| boundedLiveAppliedWithKnownPriorInFlightPressure |  |  | up or stable | Exact/known pressure improves interpretability. |
| boundedLiveAppliedWithLowerBoundPriorInFlightPressure |  |  | isolated | Lower-bound rows stay diagnostic-only. |
| retainedAboveThresholdWithAuditableAlternatives |  |  | down | Primary avoidable over-pressure signal. |
| retargetedAboveThresholdWithAuditableAlternatives |  |  | up only if justified | Primary pressure-aware retarget signal. |
| noUnderThresholdAlternativeAudited |  |  | up | Needed to classify unavoidable over-pressure. |
| leastOverThresholdFallbackOpportunities |  |  | classified | Candidate-generation signal, not success proof. |
| potentialOverConcentrationCandidates |  |  | down | Candidate-level overconcentration signal. |
| potentialCapMisallocationCandidates |  |  | down or zero | Cap interaction signal. |

## Guardrail checks

Any hard guardrail failure blocks a candidate-filtered verdict.

| Guardrail | Baseline/current | Candidate/replay | Pass/Fail | Notes |
| --- | --- | --- | --- | --- |
| Parser verdict OK |  |  |  |  |
| MissileWarfare warnings/errors zero |  |  |  |  |
| same-team target markers zero |  |  |  |  |
| scope-violation markers zero |  |  |  |  |
| failed command counts zero or explained |  |  |  |  |
| skipped commands explainable |  |  |  |  |
| direct command-spend evidence preserved |  |  |  |  |
| vanilla / none-correlated spillover not counted as controlled spend |  |  |  |  |
| lower-bound pressure not used as exact pressure |  |  |  |  |
| no outcome-aware scoring introduced |  |  |  |  |
| no command-authority or scope expansion |  |  |  |  |
| offline replay not claimed as live proof |  |  |  |  |

## Blocker deltas

Track hard measurement blockers separately from external outcome blockers.

| Blocker | Baseline/current | Candidate/replay | Interpretation |
| --- | ---: | ---: | --- |
| per-alternative pressure unavailable |  |  | Hard offline fitting blocker. |
| prior in-flight target attribution unavailable for observed live missiles |  |  | Hard measurement blocker. |
| exact outcome attribution pending OutcomeLog correlation |  |  | External outcome blocker; not a pressure-loop blocker. |
| missing comparable target-alternative features |  |  | Hard comparison blocker. |
| ambiguous selected-target rank or score space |  |  | Hard comparison blocker. |

## Verdict vocabulary

Use exactly one verdict.

- `candidate-filtered`: offline metrics moved in the intended direction, hard
  guardrails held, and the candidate merits live validation.
- `blocked`: hard guardrail failed or required evidence is missing.
- `no material change`: comparable evidence exists, but metrics did not move
  enough to justify live validation.
- `invalid comparison`: scenario, settings, caps, evidence quality, or parser
  health changed enough that the comparison cannot be used.
- `inconclusive`: evidence is too sparse or ambiguous to classify.
- `needs-live-validation`: offline evidence is supportive but not causal proof.

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

Use this section for causal caveats that counters cannot capture.

Examples:

- enemy composition differs materially;
- missile family differs;
- target alternatives existed but were not tactically comparable;
- applied commands were too sparse;
- cap blocks dominate the result;
- `noUnderThresholdAlternative` is not auditable without per-alternative pressure;
- outcome rows show hook health but are not joined to allocation rows.

## Output location

For local ignored comparisons, use:

```text
artifacts/fitting/<candidate-or-comparison-id>/comparison.md
```

For durable docs or issue notes, copy only the non-private summary and omit raw
log paths.
