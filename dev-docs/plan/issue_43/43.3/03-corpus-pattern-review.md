# Issue #43.3 corpus pattern review — 8-run bounded-live import

Updated: 2026-06-26
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.3/03-corpus-pattern-review.md`
Parent context: `dev-docs/plan/issue_43/43.3/00-context.md`
Prior conclusion: `dev-docs/plan/issue_43/43.3/01-corpus-review-conclusion.md`

## Scope

This note reviews allocator-quality patterns in the ignored local 2026-06-26 bounded-live corpus import.

Reviewed generated artifacts:

```text
artifacts/experiments/bounded-live-playerlog-20260626/*/summary.json
artifacts/fitting/bounded-live-playerlog-20260626-summary/corpus-summary.json
```

Raw private `Player.log` remains uncommitted and is not a review artifact for this document. All observations below are derived from generated summaries and redacted corpus counters.

A local pass over the uploaded private `Player.log` from `Player.zip` was used as additional non-committed evidence. That pass confirmed the current bounded-live log surface still cannot recover a real simultaneous target-alternative denominator: all 2,980 allocation cycles in the uploaded log have exactly one `allocation`/`rejection` target row, and the 24 bounded-live applied candidate cycles also have exactly one allocator target row each. The cycle-level `targetCount` field is only snapshot target presence, not enemy-count or candidate-count evidence.

The review question is narrow:

```text
Do the 8 imported fleet-wide-controlled runs show a repeated allocator-quality failure pattern strong enough to justify a tuning issue now?
```

## Corpus aggregate

```text
experimentCount: 8
runModeCounts.fleet-wide-controlled: 8
heuristicCandidateId: baseline-fleet-wide-bounded-live-v1
selectedMode: fleet-wide
warnings: []
verdictCounts.evidence-limited: 8
directRuntimeContext launch rows: 167
fleet-wide bounded live applied command results: 24
failed command results: 0
pdEvidenceCategory: observedTemplateCapability for 8/8 experiments
```

Aggregate skipped command reasons:

```text
allocatorLauncherNotFleetEligible: 315
noAllocatorAllocation: 66
fleetWideBoundedLivePerShipCapBlocked: 14
```

Aggregate allocator-quality counters from the corpus summary remain empty:

```text
overkill_counts: {}
under_saturation_counts: {}
target_mismatch_counts: {}
regression_counts: {}
vanilla_spillover_counts: {}
```

Interpretation: the corpus is strong for command-authority and direct-spend confirmation, but it is still outcome-limited and classification-limited for allocator tuning.

## Experiment-level applied command summary

| Run suffix | Primary battle window | Applied commands | Assigned/direct rows | Target concentration | Skipped reason counts | Provenance note |
|---|---:|---:|---:|---|---|---|
| `-1` | `BATTLE-0001` | 3 | 33 / 33 | `Amun Ra`: 33 | per-ship cap: 2 | single detected segment |
| `-2` | `BATTLE-0001` | 3 | 21 / 21 | `Oboro`: 14, `Echo`: 7 | not fleet eligible: 2; per-ship cap: 2 | single detected segment |
| `-5` | `BATTLE-0001` | 3 | 22 / 22 | `Nereus`: 22 | no allocator allocation: 4 | allocation rows in `BATTLE-0001`; launch/runtime spans `BATTLE-0001..0004` |
| `-6` | `BATTLE-0001` | 3 | 16 / 16 | `Nereus`: 16 | none | allocation rows in `BATTLE-0001`; launch/runtime spans `BATTLE-0001`, `BATTLE-0002`, `BATTLE-0004` |
| `-7` | `BATTLE-0002` | 3 | 21 / 21 | `Banshee`: 21 | not fleet eligible: 73; no allocation: 7; per-ship cap: 2 | one stray skipped row in `BATTLE-0001`; main applied run in `BATTLE-0002` |
| `-12` | `BATTLE-0003` | 3 | 18 / 18 | `Squall`: 18 | not fleet eligible: 142; no allocation: 13; per-ship cap: 2 | single detected segment |
| `-14` | `BATTLE-0004` | 3 | 18 / 18 | `Chernobog`: 18 | not fleet eligible: 98; no allocation: 42; per-ship cap: 2 | single detected segment |
| `-16` | `BATTLE-0004` | 3 | 18 / 18 | `Helios`: 18 | per-ship cap: 4 | single detected segment |

Every run produced exactly three applied command results. Every applied command has matching `directRuntimeContextRows` equal to its `assignedShots`; the corpus reports zero failed command results.

## Applied command detail

| Run suffix | Applied commands |
|---|---|
| `-1` | `Valcour Island -> Amun Ra` 11; `Gaugamela -> Amun Ra` 11; `Ramillies -> Amun Ra` 11 |
| `-2` | `Philippine Sea -> Oboro` 7; `Valmy -> Echo` 7; `Syracuse -> Oboro` 7 |
| `-5` | `Orleans -> Nereus` 8; `Monterey -> Nereus` 7; `Thapsus -> Nereus` 7 |
| `-6` | `Orleans -> Nereus` 6; `Monterey -> Nereus` 5; `Thapsus -> Nereus` 5 |
| `-7` | `Lake Champlain -> Banshee` 7; `Karbala -> Banshee` 7; `Heraclea -> Banshee` 7 |
| `-12` | `El Alamein -> Squall` 6; `Savo Island -> Squall` 6; `Arbela -> Squall` 6 |
| `-14` | `Xiaoting -> Chernobog` 6; `Stalingrad -> Chernobog` 6; `Mobile Bay -> Chernobog` 6 |
| `-16` | `Metaurus -> Helios` 6; `Puebla -> Helios` 6; `Austerlitz -> Helios` 6 |

Across the corpus, applied shot totals by target are:

```text
Nereus: 38
Amun Ra: 33
Banshee: 21
Squall: 18
Chernobog: 18
Helios: 18
Oboro: 14
Echo: 7
```

Launcher distribution is bounded inside each experiment: no experiment applies two live commands to the same launcher. Cross-experiment repeats exist for `Orleans`, `Monterey`, and `Thapsus` in `-5`/`-6`, but those two runs also carry multi-segment launch/runtime provenance limitations and appear to be adjacent evidence windows rather than independent proof of a launcher-selection defect.

## Pattern review

### 1. Target over-concentration

Observed pattern: yes, superficially. Seven of eight experiments apply all three commands to one target. The remaining run, `-2`, applies two commands to `Oboro` and one to `Echo`.

Tuning interpretation: not proven. The attached same-battle/same-cycle context rows report `targetCount="1"` throughout the generated summaries, but source review shows this field is a 0/1 snapshot target-presence field: the diagnostics write `1` when `snapshot.Target` is present and `0` when it is absent. It is not a count of all remaining hostile ships, nor a count of simultaneous allocator target alternatives. Therefore, the repeated same-target pattern remains visible, but the current `targetCount` field cannot prove either that concentration was unavoidable or that better simultaneous target alternatives were ignored.

Important caveat: this weakens both directions of the inference. The corpus does not prove a bad over-concentration policy, but `targetCount="1"` also cannot exonerate the allocator by showing only one enemy remained.

Verdict:

```text
No tuning-worthy target over-concentration pattern established yet.
```

### 2. Under-saturation

Observed pattern: not classified in the corpus. `under_saturation_counts` is empty. Every applied command's direct runtime rows match assigned shots, so there is no command-spend under-delivery in the generated summaries.

The corpus does show several packages of 5-8 shots and one set of 11-shot packages, but without hit/damage/kill attribution or target survival timing those package sizes cannot be judged as too small or too large.

Verdict:

```text
No under-saturation tuning evidence yet; outcome attribution is the blocker.
```

### 3. Cap-induced misallocation

Observed pattern: only per-ship cap blocks are visible.

```text
fleetWideBoundedLivePerShipCapBlocked: 14 total
```

No generated corpus counter shows a global cap or per-target cap block. The per-ship cap blocks are expected containment behavior for `perShipCap=1`: a launcher that has already received a bounded-live command should not receive another command in the same experiment.

The summaries do not show that a higher-quality allocation was displaced by a cap. In particular, there is no evidence that the cap blocked a different launcher-target pair that should have been selected over the applied commands.

Verdict:

```text
No cap-induced misallocation pattern established. Current cap blocks read as safety containment, not allocator-quality failure.
```

### 4. Target-value mismatch

Observed pattern: not classified in the corpus. `target_mismatch_counts` is empty, and the generated summaries do not include a target-value or outcome ranking strong enough to say that the selected targets were low-value.

The repeated targets are not enough by themselves. For example, `Nereus`, `Banshee`, `Squall`, `Chernobog`, and `Helios` each received all three commands in their respective run, but the attached context does not expose alternative target value comparisons.

Verdict:

```text
No target-value mismatch tuning evidence yet.
```

### 5. Skipped reason pattern

Observed skipped reasons split into three categories:

```text
allocatorLauncherNotFleetEligible: 315
noAllocatorAllocation: 66
fleetWideBoundedLivePerShipCapBlocked: 14
```

Interpretation by reason:

- `allocatorLauncherNotFleetEligible` dominates in `-7`, `-12`, and `-14`. This looks like the bounded fleet-wide apply layer scanning allocator rows that are outside the player fleet eligibility boundary. It is a scope-filtering/reporting pattern, not direct evidence that the allocator made bad target choices.
- `noAllocatorAllocation` appears most heavily in `-14` and also appears in `-7` and `-12`. Some of this is normal for cycles where no allocator-backed command candidate exists. In `-7`, one `BATTLE-0001` skipped/no-allocation row is explicitly a provenance stray before the main `BATTLE-0002` applied run.
- `fleetWideBoundedLivePerShipCapBlocked` appears in small counts and is expected with `perShipCap=1`.

Verdict:

```text
Skipped reasons suggest measurement/reporting cleanup opportunities, not allocator tuning.
```

A future report-only improvement could summarize skipped reasons after excluding non-fleet-eligible rows from allocator-quality denominators, but that is not a behavior change.

### 6. Launch/runtime tail and battle-window provenance

Observed pattern: yes, and it affects interpretation.

```text
-5: AllocationLog rows all in BATTLE-0001; LaunchLog/runtime spans BATTLE-0001..0004.
-6: AllocationLog rows all in BATTLE-0001; LaunchLog/runtime spans BATTLE-0001, BATTLE-0002, BATTLE-0004.
-7: BATTLE-0001 has one skipped/noAllocatorAllocation row; applied commands and LaunchLog rows are in BATTLE-0002.
```

The importer now records these limitations instead of collapsing them. That is good enough for command-spend review because each applied command still has direct runtime rows. It is not good enough for outcome-quality tuning because late runtime rows and cross-battle tails can confuse target destruction, spillover, and repeated-trigger interpretation.

Verdict:

```text
Battle-window provenance is a measurement blocker for tuning, especially for outcome attribution and repeated same-target interpretation.
```

## Tuning decision

Do not open a broad allocator tuning issue from this 8-run corpus alone.

The strongest visible pattern is same-target concentration. The uploaded raw `Player.log` confirms that current bounded-live diagnostics cannot distinguish unavoidable single-target contexts from ignored alternatives: bounded-live applied cycles contain only one allocator target row, and `targetCount` is not a real target-candidate denominator. The cap blocks are expected safety behavior. Skipped rows mostly reflect fleet eligibility filtering or absent allocator allocation. The corpus contains no classified overkill, under-saturation, target-value mismatch, regression, failed command, or vanilla spillover counter.

Current decision:

```text
Tuning-worthy repeated allocator-quality failure pattern: not established.
Broad allocator tuning: no.
Narrow target-over-concentration tuning issue: not yet.
Next owner: measurement / outcome attribution / spillover separation.
```

## Recommended follow-up

Recommended issue title:

```text
Improve bounded-live outcome attribution and spillover separation
```

Suggested scope:

- keep direct controlled command spend separate from none-correlated vanilla/runtime spillover;
- attach conservative target outcome hints to direct command result groups without inheriting skipped-row outcomes;
- emit `visibleHostileTargets`, `visibleTargetSourceCount`, and a bounded-live `targetAlternativeDenominator` on `fleetWideBoundedLiveCandidate` and `fleetWideBoundedLiveResult` rows from `FleetWideScopeEvidence`;
- include enough target identities or compact target summaries to tell whether the selected target had viable same-cycle alternatives;
- add or expose a real simultaneous-target denominator before treating same-target packages as over-concentration evidence;
- do not use `targetCount` as that denominator unless its schema changes, because current runtime diagnostics emit it as snapshot target presence rather than target-candidate count;
- preserve battle-window provenance limitations in any outcome summary;
- do not change allocator scoring or command behavior in this measurement issue.

A later narrow tuning issue, such as:

```text
Tune fleet-wide target over-concentration guard
```

should require evidence that multiple fleet-wide controlled runs had independently measured simultaneous target alternatives and still repeatedly over-concentrated on a lower-value or already-sufficiently-saturated target.

## Handoff statement

#43.3 now has enough local/private bounded-live corpus evidence to close the command-authority/corpus-import question. The 8-run pattern review does not justify allocator tuning yet. It points instead to measurement work: outcome attribution, spillover separation, and a real target-alternative denominator that can distinguish unavoidable single-target contexts from genuine over-concentration.
