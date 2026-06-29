# Phase 05: First pressure-aware sweep boundary

## Goal

Define the first heuristic tuning sweep before any allocator behavior changes.
This keeps the first loop small enough to interpret while still reducing the
manual fatigue of deciding scope each time.

## Sweep name

`pressure-aware-bounded-live-v1`

## Baseline candidate

```json
{
  "heuristicCandidateId": "baseline-fleet-wide-bounded-live-v1",
  "family": "pressure-aware-bounded-live-v1",
  "pressureReference": "maxKillSaturation",
  "thresholdMultiplier": 1.0,
  "pressureSourcePolicy": "priorControlledPlusExactRecoveredInFlightOnly",
  "lowerBoundPressurePolicy": "diagnosticOnly",
  "retargetPolicy": "currentIssue56Behavior",
  "viableAlternativePolicy": "allocatorComparableTargetFeaturesRequired",
  "deferredKnobs": [
    "targetValueWeights",
    "pointDefenseWeights",
    "launchWindowWeights",
    "outcomeAwareScoring",
    "vanillaSalvoSuppression",
    "commandAuthorityScope"
  ],
  "notes": "Baseline for the first pressure-aware tuning sweep. Outcome rows are hook-health context only."
}
```

## Candidate A: minimal exact-pressure retarget preference

Candidate A is the recommended first code change.

Allowed behavior:

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

Not allowed:

- lowering the threshold based on lower-bound pressure;
- retargeting without comparable alternative feature evidence;
- changing target-value, PD, or launch-window weights;
- changing global, per-ship, or per-target caps;
- changing selected/fleet scope or command authority;
- using `[OutcomeLog]` rows as success/failure reward.

Suggested parameter snapshot:

```json
{
  "heuristicCandidateId": "pressure-aware-bounded-live-v1-candidate-a",
  "family": "pressure-aware-bounded-live-v1",
  "pressureReference": "maxKillSaturation",
  "thresholdMultiplier": 1.0,
  "pressureSourcePolicy": "priorControlledPlusExactRecoveredInFlightOnly",
  "lowerBoundPressurePolicy": "diagnosticOnly",
  "retargetPolicy": "preferBestViableUnderThresholdAlternativeWhenSelectedAtOrAboveThreshold",
  "viableAlternativePolicy": "targetDenominatorGtOneAndAllocatorComparableFeaturesRequired",
  "deferredKnobs": [
    "targetValueWeights",
    "pointDefenseWeights",
    "launchWindowWeights",
    "outcomeAwareScoring",
    "vanillaSalvoSuppression",
    "commandAuthorityScope"
  ],
  "notes": "First minimal pressure-aware tuning candidate."
}
```

## Optional Candidate B

Do not implement Candidate B unless Candidate A produces `no material change` or
is too sparse to evaluate while guardrails hold.

Possible Candidate B shapes, still inside the same family:

- keep threshold at `1.0` but loosen alternative rank acceptance only among fully
  comparable alternatives;
- keep alternative policy fixed but add a small deterministic tie-breaker against
  already pressured selected targets;
- add clearer diagnostics for why an above-threshold selected target was retained
  despite alternatives.

Candidate B must not introduce a second heuristic family.

## Required comparison

For each candidate, compare against the baseline using
`04-comparison-template.md`.

Primary expected movement:

- `boundedLiveRetainedSelectedTargetDecisionsAboveThreshold` decreases or remains
  zero with an explanation;
- `boundedLiveRetargetedDecisionsAboveThreshold` increases only when viable
  alternatives exist;
- `boundedLiveLowerBoundPressureDiagnosticOnlyRows` remains diagnostic-only;
- hard guardrails remain clean.

A supportive verdict requires both objective movement and guardrail preservation.

## Validation before live follow-up

For the code change:

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

After Candidate A is implemented and statically validated:

1. run one comparable bounded-live combat scenario;
2. import the new `Player.log` to an ignored follow-up artifact directory;
3. summarize the follow-up corpus;
4. fill out the comparison template;
5. classify the verdict before deciding whether to keep, revert, or iterate.

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

This fixture cleanup is not a blocker for Candidate A, but it should be resolved
before treating fixture parse verdicts as hard regression gates.

## Exit criteria for large preparation

Large preparation is complete when:

- this sweep boundary is accepted;
- the comparison template is available;
- parameter snapshots can be recorded in run notes or import metadata;
- compact fixture verdict status is documented;
- the next change is a narrow Candidate A implementation, not more preparation.
