# Issue #43.4 context — Bounded-live tuning-readiness measurement

Updated: 2026-06-26
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.4/00-context.md`

## Position in the #43 umbrella

Issue #43 expands selected-group controlled missile allocation toward a bounded fleet-wide controlled path. The prior slices established the following:

```text
#43.1  fleet-wide dry-run/report scaffold
#43.2  bounded fleet-wide live apply / command-authority proof
#43.3  corpus review and no-tuning handoff
#43.4  bounded-live tuning-readiness measurement
```

#43.4 is a measurement-readiness slice. It is not an allocator-tuning slice.

The #43.3 corpus review showed that bounded fleet-wide live commands can be applied and correlated to direct runtime launch/spend rows, but the current bounded-live log/corpus surface cannot decide whether observed same-target concentration is good, bad, or unavoidable. This slice should add the missing diagnostic and corpus fields needed to make that decision in a later narrow tuning issue.

## Triggering evidence

The local #43.3 review used generated ignored artifacts from:

```text
artifacts/experiments/bounded-live-playerlog-20260626/
artifacts/fitting/bounded-live-playerlog-20260626-summary/
```

and an additional non-committed local pass over the uploaded private `Player.log` from `Player.zip`.

Observed #43.3 corpus state:

```text
experimentCount: 8
runModeCounts.fleet-wide-controlled: 8
fleet-wide bounded live applied command results: 24
directRuntimeContext launch rows: 167
failed command results: 0
warnings: []
pdEvidenceCategory.observedTemplateCapability: 8/8
```

Observed skipped reasons:

```text
allocatorLauncherNotFleetEligible: 315
noAllocatorAllocation: 66
fleetWideBoundedLivePerShipCapBlocked: 14
```

Observed same-target concentration exists, but the evidence surface is insufficient:

- seven of eight imported bounded-live experiments put all three applied commands on one target;
- one experiment split applied commands 2/1 across two targets;
- `targetCount="1"` is not a count of remaining enemies or allocator alternatives;
- source review showed `targetCount` is emitted as snapshot target presence: `snapshot.Target == null ? "0" : "1"`;
- the uploaded raw `Player.log` also does not recover a simultaneous target-alternative denominator from existing bounded-live rows;
- all 2,980 allocation cycles in that uploaded log had exactly one `allocation`/`rejection` target row, and the 24 bounded-live applied candidate cycles also had exactly one allocator target row each;
- there were no `fleetWideDryRunExperiment` / `fleetWideTarget` / `visibleHostileTargets` rows available in that log to reconstruct same-cycle alternatives.

Therefore #43.3 should remain a no-tuning-yet conclusion. #43.4 should make the next bounded-live corpus tuning-ready.

## Core question

#43.4 answers:

```text
Can a bounded-live corpus classify each applied fleet-wide command as reasonable, over-concentrated, under-saturated, cap-distorted, target-value mismatched, execution-failed, spillover-limited, or evidence-limited?
```

A later allocator tuning issue should only be opened after #43.4 produces a corpus where repeated allocator-quality failure can be classified without relying on `targetCount` or raw anecdotal inspection.

## Scope

In scope:

- emit real same-cycle target alternative denominators on bounded-live runtime diagnostic rows;
- preserve selected target decision features on bounded-live candidate/result rows;
- import those fields into per-experiment `summary.json` artifacts;
- aggregate those fields into `corpus-summary.json` and any readable scenario/corpus breakdown;
- add a tuning-readiness report or section that groups same-target concentration by denominator quality;
- add or update fixtures/tests for the new log fields and importer behavior;
- document the interpretation boundary clearly: measurement only, not tuning.

Out of scope:

- changing allocator scoring weights;
- changing shot allocation heuristics;
- changing live command caps except to log cap state more clearly;
- suppressing vanilla salvos or changing selected-ship distribution behavior;
- requiring exact hit/damage/kill attribution before #47 provides a stable hook;
- committing raw private `Player.log` or generated ignored artifacts.

## Required runtime fields

Each `fleetWideBoundedLiveCandidate` and `fleetWideBoundedLiveResult` row should preserve the real target alternative denominator from `FleetWideScopeEvidence`:

```text
visibleTargetSource
visibleTargetConfidence
visibleTargetSourceCount
visibleHostileTargets
targetAlternativeDenominator
targetAlternativeEvidence
```

The intended initial mapping is:

```text
visibleTargetSource = scope.TargetSource
visibleTargetConfidence = scope.TargetConfidence
visibleTargetSourceCount = scope.Targets.Count
targetAlternativeDenominator = count(scope.Targets where classification == visibleHostile)
targetAlternativeEvidence = visibleHostileTargetsFromActiveShips | missingFleetWideScope
```

The row should also preserve enough target identity context to know whether the selected target had viable same-cycle alternatives. If full target lists would be too verbose, use a compact bounded representation:

```text
targetAlternativeIds
targetAlternativeNames
targetAlternativeTeams
targetAlternativeCountTruncated
```

If target lists are not emitted in the first implementation, the count fields are still required and the document should explicitly state that target identity comparison remains limited.

Do not use the existing cycle-level `targetCount` field as a denominator. It is snapshot target presence only.

## Required allocator decision surface

For each bounded-live selected candidate, preserve these fields where available:

```text
launcherId
launcherName
launcherTeam
allocatorLauncherId
allocatorLauncherName
targetId
targetName
targetTeam
assignedShots
ammoGateBudgetShots
targetValue
pdScore
saturationSize
killSize
launchWindowScore
selectedTargetScore
selectedTargetScoreSpace
selectedTargetRank
selectedTargetRankComparisonSpace
selectedTargetRankLevel
candidateSource
allocatorEvidence
```

If `selectedTargetScore` or `selectedTargetRank` is not currently available from the allocator, do not invent it. Instead, emit `unknown` and mark the readiness blocker in corpus output.

## Saturation and over-concentration evidence

The corpus should allow same-target concentration to be separated into at least these groups:

```text
targetAlternativeDenominator = 1
targetAlternativeDenominator > 1
targetAlternativeDenominator unknown
```

For potential over-concentration classification, preserve or derive:

```text
selectedTargetPriorControlledShots
selectedTargetPriorAllocatorShots
selectedTargetPriorVanillaShotsKnown
selectedTargetPriorMissileInFlightEstimate
selectedTargetPriorMissileInFlightEstimateBound
selectedTargetPriorMissileInFlightTargetAttribution
selectedTargetNewAssignedShots
selectedTargetCumulativeAssignedShots
selectedTargetSaturationSize
selectedTargetKillSize
selectedTargetOverSaturationRatio
selectedTargetKillOvercommitRatio
```

A same-target repeated package is not tuning evidence unless viable same-cycle alternatives existed and the selected target was already sufficiently saturated or overcommitted under the available evidence.

## Under-saturation evidence

For potential under-saturation classification, preserve or derive:

```text
assignedShots
directRuntimeContextRows
actualLaunchRows
missileSpendConfirmed
targetSaturationSize
targetKillSize
targetSurvivedAfterControlledWindow
targetDestroyedAfterControlledWindow
timeToImpactWindowKnown
```

Without stable outcome hooks, under-saturation classification may remain evidence-limited. That is acceptable, but the corpus should say so explicitly instead of implying a tuning recommendation.

## Cap-induced misallocation evidence

Cap blocks are not tuning evidence by themselves. For each bounded-live cap block that is relevant to allocator quality, preserve:

```text
capReason
globalCapRemaining
perShipCapRemaining
perTargetCapRemaining
blockedCandidateLauncherId
blockedCandidateTargetId
blockedCandidateScore
appliedCandidateScore
wouldHaveAppliedRankWithoutCap
blockedCandidateWasBetterThanApplied
```

If blocked-vs-applied score comparison is not available, corpus output should classify cap effects as safety containment or evidence-limited, not misallocation.

## Launcher-side evidence

To distinguish repeated launcher choice from limited eligible inventory, preserve:

```text
launcherId
launcherName
launcherTeam
launcherFleetEligible
launcherCommandable
launcherCanFireMissiles
launcherAmmoBefore
launcherAmmoAfter
launcherWeaponTemplate
launcherMissileCountAvailable
launcherAlreadyCommandedThisExperiment
launcherPriorTargetId
launcherSelectionRelation
```

## Battle-window and spillover attribution

#43.4 should not require exact projectile hit/damage/kill attribution. It should, however, keep the existing #39/#39.1 separation between controlled spend and vanilla or none-correlated spillover.

Preserve or derive:

```text
battleSegmentId
cycleId
commandResultId
launchRowsByCommandResultId
directRuntimeContextRows
nonCorrelatedLaunchRowsNearWindow
vanillaSpilloverRowsNearTarget
targetOutcomeAttribution
attributionConfidence
```

Suggested attribution classes:

```text
controlledDirectOnly
controlledPlusVanillaSpillover
vanillaOnly
multiBattleTail
unattributed
evidenceLimited
```

Rows with `controlledCommandCorrelation="none"` or `commandResultId="none"` are not controlled command spend, even if they occur near a bounded-live experiment.

## Importer and corpus requirements

Update `tools/import_player_log_experiments.py` so generated per-experiment summaries preserve the new bounded-live runtime fields. The summary should make it easy to answer, per experiment:

- how many bounded-live commands were applied;
- which launchers and targets were commanded;
- how assigned shots were distributed by target;
- whether same-target packages occurred with `targetAlternativeDenominator = 1`, `>1`, or `unknown`;
- which skipped reasons occurred and whether they are safety containment, eligibility filtering, missing allocation, or potential allocator-quality evidence;
- whether direct runtime launch/spend rows match assigned shots;
- whether battle-window provenance limits outcome classification.

Update corpus summary output so it reports tuning-readiness counters across experiments, not just command counts.

At minimum:

```text
boundedLiveAppliedResults
boundedLiveAppliedWithTargetAlternativeDenominator
boundedLiveAppliedWithTargetAlternativeDenominatorGtOne
boundedLiveAppliedWithUnknownTargetAlternativeDenominator
boundedLiveAppliedWithFullyComparableScoreRankEvidence
boundedLiveAppliedWithPartialOrAmbiguousScoreSpaceEvidence
boundedLiveAppliedWithKnownPriorInFlightPressure
boundedLiveAppliedWithLowerBoundPriorInFlightPressure
sameTargetPackagesWithDenominatorOne
sameTargetPackagesWithDenominatorGtOne
sameTargetPackagesWithUnknownDenominator
potentialOverConcentrationCandidates
potentialUnderSaturationCandidates
potentialCapMisallocationCandidates
targetValueMismatchCandidates
evidenceLimitedResults
```

## Tuning-readiness gate

A corpus is tuning-ready only if:

1. Every applied bounded-live result has:
   - `experimentId`
   - `battleSegmentId`
   - `cycleId`
   - `commandResultId`
   - `launcherId`
   - `targetId`
   - `assignedShots`
   - `directRuntimeContextRows`
2. At least 95% of applied bounded-live results have:
   - `targetAlternativeDenominator`
   - `visibleHostileTargets`
   - selected target score or rank, or an explicit `unknown` blocker;
   - saturation or kill-size evidence, or an explicit `unknown` blocker;
   - `targetValue`
   - `pdScore`
3. Same-target concentration claims are grouped by denominator quality:
   - denominator 1;
   - denominator greater than 1;
   - denominator unknown.
4. Tuning recommendation is forbidden if most same-target concentration cases have unknown denominator.
5. Any non-evidence-limited tuning recommendation must identify the narrow failure class it addresses.

## Failure classes to classify

Each applied bounded-live result should be classifiable as one of:

```text
reasonable concentration
target over-concentration candidate
under-saturation candidate
cap-induced misallocation candidate
target-value mismatch candidate
command/execution failure
vanilla spillover / attribution-limited
evidence-limited
```

These are diagnostic classes, not behavior changes.

## When to open a tuning issue

Open a later narrow allocator tuning issue only if #43.4 establishes one repeated pattern:

### Target over-concentration

Required evidence:

- `targetAlternativeDenominator > 1`;
- same target receives multiple controlled packages;
- cumulative assigned shots exceed saturation or kill threshold under the available evidence;
- viable lower-saturation alternatives existed;
- repeated in at least three independent experiments or at least 30% of eligible cases.

### Under-saturation

Required evidence:

- selected target receives less than saturation or kill threshold;
- target survives the controlled attribution window;
- no vanilla spillover or battle-window confounder explains the result;
- repeated pattern points to shot-count calculation, not command failure.

### Cap-induced misallocation

Required evidence:

- cap blocks a higher-scoring or higher-need candidate;
- a lower-quality candidate is applied instead, or no equivalent candidate remains;
- repeated pattern indicates cap policy issue rather than expected safety containment.

### Target-value mismatch

Required evidence:

- selected target has materially lower value/score than available alternatives;
- logged allocator features show the difference;
- outcome or saturation evidence supports that the selected target was harmful or wasteful.

## Expected files to inspect

A Codex worker should inspect at least:

```text
src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs
tools/import_player_log_experiments.py
tools/parse_player_log.py
docs/diagnostics/snapshot-and-allocation.md
docs/diagnostics/runtime-validation-history.md
dev-docs/plan/issue_43/43.3/03-corpus-pattern-review.md
```

Potentially relevant generated artifacts for local validation, not for commit:

```text
artifacts/experiments/bounded-live-playerlog-20260626/
artifacts/fitting/bounded-live-playerlog-20260626-summary/
```

Raw private logs must remain uncommitted.

## Verification loop

The intended Codex loop is:

```text
1. Add or adjust bounded-live runtime fields.
2. Update parser/importer preservation of those fields.
3. Update per-experiment and corpus summaries.
4. Add fixture coverage for the new fields and denominator grouping.
5. Re-import a local Player.log into ignored artifacts.
6. Confirm corpus readiness counters are present.
7. Decide whether the corpus is tuning-ready, evidence-limited, or blocked by missing runtime fields.
```

The loop succeeds when a reviewer can answer:

```text
Did same-target concentration happen when multiple viable hostile targets existed?
Was the selected target already saturated or overcommitted?
Were cap blocks merely safety containment or did they displace better candidates?
Did direct controlled spend match assigned shots?
Was outcome interpretation clean, spillover-limited, multi-battle-tail-limited, or evidence-limited?
```

## Exit condition

#43.4 is complete when a bounded-live corpus summary can support a conservative decision among:

```text
no tuning, because concentration was reasonable or unavoidable;
open narrow target-over-concentration tuning issue;
open narrow under-saturation tuning issue;
open narrow cap-policy tuning issue;
open narrow target-value weighting issue;
remain evidence-limited because outcome hooks or vanilla suppression work is still missing.
```

If the corpus remains evidence-limited, the handoff should point to the specific blocker, such as #47 outcome hooks or #48 vanilla salvo suppression / selected-ship distribution, instead of recommending allocator tuning.
