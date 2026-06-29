# Phase 05: First pressure-aware sweep boundary

## Goal

Define the first pressure-aware sweep boundary without duplicating behavior that
already exists in the current #56 implementation. This keeps the tuning loop
small enough to interpret while reducing the manual fatigue of deciding scope
each time.

## Sweep name

`pressure-aware-bounded-live-v1`

## Current implementation status

Code inspection shows that the originally proposed Candidate A behavior is
already present in `ShadowAllocationDiagnostics`:

- bounded-live pressure decisions use prior controlled shots plus exact recovered
  in-flight shots;
- lower-bound in-flight pressure is recorded separately and remains
  diagnostic-only;
- selected-target pressure is compared against `max(killSize, saturationSize)`;
- retargeting only proceeds when same-cycle alternatives exist;
- retargeting requires `allocatorComparableFeatures` target-alternative evidence;
- the chosen retarget is the best under-threshold alternative by the current
  allocator score space.

Therefore the first sweep should not implement Candidate A again. Treat Candidate
A as the current baseline behavior that must be validated through comparison.
The next code change, if any, should be Candidate B or a diagnostics-only
comparison helper.

## Baseline / Candidate A snapshot

```json
{
  "heuristicCandidateId": "baseline-fleet-wide-bounded-live-v1",
  "family": "pressure-aware-bounded-live-v1",
  "pressureReference": "maxKillSaturation",
  "thresholdMultiplier": 1.0,
  "pressureSourcePolicy": "priorControlledPlusExactRecoveredInFlightOnly",
  "lowerBoundPressurePolicy": "diagnosticOnly",
  "retargetPolicy": "preferBestViableUnderThresholdAlternativeWhenSelectedAtOrAboveThreshold",
  "viableAlternativePolicy": "targetDenominatorGtOneAndAllocatorComparableFeaturesRequired",
  "implementationStatus": "alreadyImplementedInIssue56",
  "deferredKnobs": [
    "targetValueWeights",
    "pointDefenseWeights",
    "launchWindowWeights",
    "outcomeAwareScoring",
    "vanillaSalvoSuppression",
    "commandAuthorityScope"
  ],
  "notes": "Current pressure-aware bounded-live behavior. Outcome rows are hook-health context only."
}
```

## Candidate A validation target

Candidate A should be validated, not reimplemented.

Expected behavior to preserve:

- only applies to bounded-live controlled allocation rows;
- only considers pressure from prior controlled shots plus exact recovered
  in-flight shots;
- only triggers when selected-target pressure is at or above
  `max(killSize, saturationSize)`;
- only retargets when same-cycle alternatives exist with comparable target
  feature evidence;
- chooses the best viable under-threshold alternative from the current allocator
  candidate space;
- keeps lower-bound in-flight pressure diagnostic-only.

Not allowed in validation or follow-up changes:

- lowering the threshold based on lower-bound pressure;
- retargeting without comparable alternative feature evidence;
- changing target-value, PD, or launch-window weights;
- changing global, per-ship, or per-target caps;
- changing selected/fleet scope or command authority;
- using `[OutcomeLog]` rows as success/failure reward.

## Optional Candidate B

Do not implement Candidate B until Candidate A has a comparison record using
`04-comparison-template.md` and the result is `no material change`,
`inconclusive`, or too sparse to evaluate while guardrails hold.

Possible Candidate B shapes, still inside the same family:

- keep threshold at `1.0` but add clearer diagnostics for why an above-threshold
  selected target was retained despite alternatives;
- keep threshold and alternative policy fixed but add a small deterministic
  tie-breaker against already pressured selected targets, only among fully
  comparable alternatives;
- keep behavior fixed and add a report-only comparison helper before changing any
  additional heuristic behavior.

Candidate B must not introduce a second heuristic family.

Suggested Candidate B parameter snapshot, if later selected:

```json
{
  "heuristicCandidateId": "pressure-aware-bounded-live-v1-candidate-b",
  "family": "pressure-aware-bounded-live-v1",
  "pressureReference": "maxKillSaturation",
  "thresholdMultiplier": 1.0,
  "pressureSourcePolicy": "priorControlledPlusExactRecoveredInFlightOnly",
  "lowerBoundPressurePolicy": "diagnosticOnly",
  "retargetPolicy": "candidateBToBeDefinedAfterCandidateAComparison",
  "viableAlternativePolicy": "targetDenominatorGtOneAndAllocatorComparableFeaturesRequired",
  "deferredKnobs": [
    "targetValueWeights",
    "pointDefenseWeights",
    "launchWindowWeights",
    "outcomeAwareScoring",
    "vanillaSalvoSuppression",
    "commandAuthorityScope"
  ],
  "notes": "Do not implement until Candidate A/current behavior is compared."
}
```

## Required comparison

Compare Candidate A/current behavior against the existing baseline corpus and any
new comparable follow-up run using `04-comparison-template.md`.

Primary expected movement or preservation:

- `boundedLiveRetainedSelectedTargetDecisionsAboveThreshold` decreases or remains
  zero with an explanation;
- `boundedLiveRetargetedDecisionsAboveThreshold` appears only when viable
  alternatives exist;
- `boundedLiveLowerBoundPressureDiagnosticOnlyRows` remains diagnostic-only;
- hard guardrails remain clean.

A supportive verdict requires both objective movement/preservation and guardrail
preservation.

## Validation before live follow-up

For docs-only or comparison-template changes:

```powershell
python tools\check_layout.py
```

For any future code change:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m compileall tools
python tools\parse_player_log.py --require-launchlogs
```

If parser/importer/comparison tooling changes are included:

```powershell
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
```

## Live follow-up expectation

Before Candidate B or any broader tuning change:

1. run one comparable bounded-live combat scenario under the current Candidate A
   behavior;
2. import the new `Player.log` to an ignored follow-up artifact directory;
3. summarize the follow-up corpus;
4. fill out the comparison template;
5. classify the verdict before deciding whether to keep current behavior,
   improve diagnostics, or design Candidate B.

## Fixture verdict policy

Compact bounded-live fixtures that lack modern required hook labels should be
classified as schema fixtures, not full parser-health fixtures, unless they are
explicitly upgraded.

Recommended next cleanup:

- either add a short note near the fixture validation command explaining that
  compact fixtures are expected to parse rows but not satisfy full modern hook
  health; or
- upgrade those fixtures with the current required hook labels and make parser
  verdict OK part of their acceptance.

This fixture cleanup is not a blocker for Candidate A validation, but it should
be resolved before treating fixture parse verdicts as hard regression gates.

## Exit criteria for large preparation

Large preparation is complete when:

- this sweep boundary is accepted;
- the comparison template is available;
- parameter snapshots can be recorded in run notes or import metadata;
- compact fixture verdict status is documented;
- Candidate A/current behavior is recognized as already implemented;
- the next code change, if any, is Candidate B or a report-only comparison helper,
  not a duplicate Candidate A implementation.
