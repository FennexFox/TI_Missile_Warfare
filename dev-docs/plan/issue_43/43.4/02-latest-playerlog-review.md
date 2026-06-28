# Issue #43.4 latest Player.log review — remaining interpretation risks

Updated: 2026-06-28

## Reviewed input

A latest uploaded `Player.log` was reviewed after commit:

```text
a5b9169 Add bounded-live comparable target diagnostics
```

The reviewed bounded-live experiment was:

```text
fleetwide-bounded-live-20260628T030126702Z-1
```

The raw log is private runtime evidence and must not be committed. Generated review artifacts, if regenerated, must remain under ignored `artifacts/` paths.

## What the latest log validates

The latest log validates that the new #43.4 runtime fields are emitted in a real bounded-live run, not just in fixtures.

Observed runtime shape:

```text
fleetWideBoundedLiveCandidate: 3
fleetWideBoundedLiveResult: 5
fleetWideBoundedLivePreState: 3
fleetWideBoundedLivePostState: 3
applied: 3
skipped: 2
skip reason: fleetWideBoundedLivePerShipCapBlocked = 2
directRuntimeContext launch rows: 18
```

Target alternative evidence is now present:

```text
targetAlternativeDenominator = 5
targetAlternativeNames = Lahar|Arashi|Harpy|Talos|Dragon
targetAlternativeCountTruncated = 0
targetAlternativeFeatureEvidence = allocatorComparableFeatures
targetAlternativeFeatureCount = 5
targetAlternativeFeatureMissingCount = 0
targetAlternativeScoreBasis = scorePerShot
```

Selected target rank evidence is also present:

```text
selected target = Talos
selectedTargetRank = 5
selectedTargetRankBasis = scorePerShot
selectedTargetRankConfidence = exact
selectedTargetRankTieCount = 1
```

Cap comparison evidence remains present for the skipped commands:

```text
cap skip records = 2
blockedCandidateScore = 3.677
appliedCandidateScore = 3.677
blockedCandidateWasBetterThanApplied = False
```

This means the earlier #43.3 blocker, "same-target concentration without a real target alternative denominator," is resolved for this runtime path.

## Interpretation risk: selected score and comparable alternative score space

The latest log exposes a score interpretation issue that must be resolved before treating #43.4 as tuning-ready.

The selected bounded-live rows preserve:

```text
selectedTargetScore = 3.677
selectedTargetScoreBasis = scorePerShot
selectedTargetRank = 5
selectedTargetRankBasis = scorePerShot
```

The comparable target alternative score list records:

```text
Lahar   1.967
Arashi  1.967
Harpy   2.201
Talos   1.838
Dragon  1.877
```

`selectedTargetRank = 5` is consistent with `Talos = 1.838` if higher score is better and the five target alternatives are ranked by the comparable alternative score list. However, `selectedTargetScore = 3.677` does not match Talos's comparable alternative score of `1.838`, even though both fields report `scorePerShot` basis.

This may be legitimate if the two fields intentionally refer to different score spaces, for example:

```text
selectedTargetScore = launcher/candidate-specific allocator allocation score
targetAlternativeScores = target-level reconstructed comparable score
```

But if that distinction is intended, the field names, score basis, docs, importer summaries, or scenario breakdowns must make it explicit. Otherwise a reviewer could incorrectly conclude either:

```text
selectedTargetScore 3.677 proves Talos was the best target;
```

or:

```text
selectedTargetRank 5 proves Talos was the worst target and therefore a target-value mismatch.
```

Neither conclusion is safe until the score semantics are clarified.

Required follow-up:

```text
Confirm whether selectedTargetScore and targetAlternativeScores are in the same comparison space.
If they are the same space, investigate why selectedTargetScore=3.677 while Talos alternative score=1.838.
If they are different spaces, rename, document, or summarize them so rank and score cannot be misread.
State which score basis selectedTargetRank uses and whether that rank is target-level, launcher-target-level, or candidate-level.
```

Follow-up implemented:

```text
selectedTargetScore is intentionally in launcher/candidate allocation space.
targetAlternativeScores are diagnostic target-level comparable scores recomputed for the visible-hostile target alternative list.
selectedTargetRank is target-level and ranks the selected target inside targetAlternativeScores.
The emitted diagnostics now add selectedTargetScoreSpace, targetAlternativeScoreSpace, selectedTargetRankComparisonSpace, and selectedTargetRankLevel so reviewers cannot compare the candidate score directly to the target alternative score list.
```

## Interpretation risk: in-flight missile pressure confidence

The latest log also validates that in-flight pressure fields are emitted, but the confidence remains limited:

```text
selectedTargetPriorMissileInFlightEstimate = 0
selectedTargetPriorMissileInFlightEstimateSource = GameControl.spaceCombat.liveMissiles
selectedTargetPriorMissileInFlightEstimateObserved = 2
selectedTargetPriorMissileInFlightEstimateUnknownTargetCount = 2
selectedTargetPriorMissileInFlightEstimateConfidence = targetOwnershipSourceUnavailable
```

This should not be interpreted as a fully known estimate that there were definitely no missiles already headed toward the selected target. It is better read as:

```text
2 live missiles were observed, but target ownership/source could not be recovered, so the selected-target attribution estimate is a lower-confidence lower-bound value.
```

Required follow-up:

```text
Do not mark prior in-flight missile pressure as fully resolved when UnknownTargetCount > 0.
Represent this case as partial/lower-bound evidence rather than a complete estimate.
Keep a precise residual blocker for target ownership/source recovery if the estimate cannot attribute live missiles to target ids.
```

Follow-up implemented:

```text
Importer readiness now treats observed live missiles with UnknownTargetCount > 0 as lower-bound target-attribution-limited pressure evidence, even when selectedTargetPriorMissileInFlightEstimate = 0.
Fully known pressure is counted only when no live missiles are observed or all observed live missile target ids are recovered.
Rows where all observed live missiles have unknown targets retain the hard blocker: prior in-flight target attribution unavailable for observed live missiles.
```

## Current #43.4 judgment after this log

The latest runtime validation proves that #43.4 field emission works in a real Player.log after `a5b9169`.

It also means that #43.4 is closer to tuning readiness than before:

```text
real target alternative denominator: resolved
compact target identities: resolved
comparable alternative feature emission: runtime-present
selected target rank field emission: runtime-present
cap comparison evidence: runtime-present
exact outcome attribution: still external #47 blocker
```

However, #43.4 should not be closed as fully tuning-ready until the remaining interpretation issues are addressed or explicitly narrowed:

```text
score/rank comparison-space semantics are now explicit for new diagnostics;
in-flight pressure estimate can still be target-attribution-limited when observed live missile targets are unknown.
```

The remaining implementation work, if any, should stay small and diagnostic-only: improve live missile target ownership/source recovery when observed missiles cannot be attributed to targets, or document why that evidence must remain a later blocker. Do not tune allocator behavior as part of that follow-up.
