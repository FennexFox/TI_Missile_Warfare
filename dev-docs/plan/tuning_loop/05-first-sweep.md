# Phase 05: First offline fitting boundary

## Goal

Replace the first pressure-aware live sweep framing with a measurement-first
offline fitting boundary. The first useful e2e loop should run over archived logs
and produce a candidate report, not a behavior-changing heuristic.

## Boundary name

`pressure-aware-bounded-live-offline-fitting-v1`

## Current implementation status

The originally proposed Candidate A behavior is already present in current
bounded-live diagnostics:

- bounded-live pressure decisions use prior controlled shots plus exact recovered
  in-flight shots;
- lower-bound in-flight pressure is recorded separately and remains
  diagnostic-only;
- selected-target pressure is compared against `max(killSize, saturationSize)`;
- retargeting only proceeds when same-cycle alternatives exist;
- retargeting requires `allocatorComparableFeatures` target-alternative evidence;
- the chosen retarget is the best under-threshold alternative by the current
  allocator score space.

Therefore Candidate A is current behavior under measurement. It is not a
validated tuning improvement and should not be reimplemented.

## Current Candidate A snapshot

```json
{
  "heuristicCandidateId": "current-pressure-aware-bounded-live-v1",
  "family": "pressure-aware-bounded-live-v1",
  "pressureReference": "maxKillSaturation",
  "thresholdMultiplier": 1.0,
  "pressureSourcePolicy": "priorControlledPlusExactRecoveredInFlightOnly",
  "lowerBoundPressurePolicy": "diagnosticOnly",
  "retargetPolicy": "preferBestViableUnderThresholdAlternativeWhenSelectedAtOrAboveThreshold",
  "viableAlternativePolicy": "targetDenominatorGtOneAndAllocatorComparableFeaturesRequired",
  "implementationStatus": "alreadyImplementedInIssue56",
  "evidenceStatus": "underMeasurementNotValidatedImprovement",
  "notes": "Outcome rows are hook-health context only. Offline replay must not be treated as live proof."
}
```

## First fitting question

The first offline fitting run should answer:

```text
When selected-target pressure is above threshold, are retained decisions avoidable?
```

Required classifications:

- `avoidable`: comparable alternatives existed and at least one had lower or
  under-threshold pressure;
- `unavoidable`: all comparable alternatives were also above threshold, or no
  comparable alternative existed;
- `inconclusive`: the log lacks per-alternative pressure, threshold, or
  eligibility evidence.

## Candidate B status

The existing Candidate B comparison helper is measurement infrastructure. It
compares corpus summaries and emits conservative verdicts. It should not be
presented as a behavior-changing candidate.

A behavior-changing Candidate B should not be designed until the offline fitting
report shows a repeated, avoidable pressure problem.

Possible future behavior families, after offline fitting evidence exists:

- least-over-threshold fallback when no under-threshold alternative exists;
- small deterministic pressure penalty among fully comparable alternatives;
- threshold multiplier sweep around `max(killSize, saturationSize)`.

## Required next diagnostics

Add report-only per-alternative pressure evidence so that
`noUnderThresholdAlternative` can be audited.

Minimum report-only fields:

```text
alternativeTargetId / name
alternativePressure
alternativeThreshold
alternativeUnderThreshold
alternativeScoreRank
alternativeEligibilityReason
bestUnderThresholdAlternative
leastOverThresholdAlternative
```

Do not change live combat behavior while adding these fields.

## Required comparison

For the current helper, compare available summaries only as measurement quality
reports. Do not call Candidate A validated unless the data has enough auditable
above-threshold alternative rows and guardrails remain clean.

Primary measurement criteria:

- enough bounded-live applied rows exist to interpret pressure decisions;
- above-threshold retained rows are auditable;
- `noUnderThresholdAlternative` is supported by per-alternative pressure data;
- lower-bound pressure remains diagnostic-only;
- hard guardrails remain clean.

## Validation before live follow-up

For docs-only or comparison-template changes:

```powershell
python tools\check_layout.py
```

For parser/importer/comparison tooling changes:

```powershell
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py tools\compare_experiment_summaries.py
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
```

For any future behavior-changing code:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m compileall tools
python tools\parse_player_log.py --require-launchlogs
```

## Exit criteria for large preparation

Large preparation is complete when:

- durable docs state that current work is offline fitting / pre-tuning
  measurement;
- Candidate A is recognized as current behavior under measurement, not a
  validated improvement;
- Candidate B comparison helper is recognized as measurement infrastructure;
- per-alternative pressure diagnostics are the next report-only blocker;
- a future dataset/replay command can be specified without re-deciding project
  scope;
- no heuristic behavior has changed.
