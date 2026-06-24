# Issue #43.3 context — Corpus review and no-tuning handoff

Updated: 2026-06-24
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.3/00-context.md`
Parent umbrella: `dev-docs/plan/issue_43/00-context.md`
Previous slices:
- `dev-docs/plan/issue_43/43.1/00-context.md`
- `dev-docs/plan/issue_43/43.2/00-context.md`
Latest #43.2 evidence:
- `docs/diagnostics/runtime-validation-history.md`
- `docs/diagnostics/snapshot-and-allocation.md`
- implementation commit: `a40bacda1f8d74645a960c48ac4afdd58bb953b1`
- final smoke doc commit: `67cc4929711f6cee3e6b55cc8eee6e6f5607e9d1`

This is context for the third #43 sub-slice. It is not an implementation plan. Codex should read this context after #43.1/#43.2 evidence or blockers exist.

## Purpose

#43.3 exists so #43 ends with a corpus-level conclusion instead of isolated local logs.

It should answer:

```text
Across the corpus, did the fleet-wide dry-run/live evidence justify a narrow next change, or should tuning be explicitly declined until specific evidence gaps are closed?
```

This slice is a review and handoff layer. It should not turn one batch into allocator tuning by default.

## Required prior state

#43.3 should receive at least one of these:

- #43.1 dry-run/report corpus-ready evidence;
- #43.2 bounded live `fleet-wide-controlled` evidence;
- an explicit #43.2 blocker summary explaining why live fleet-wide apply remains unsafe;
- fixture evidence proving schema/report behavior for the intended review surface.

If none of these exist, #43.3 is premature.

## Actual prior state entering #43.3

#43.3 is no longer premature. #43.2 produced real bounded fleet-wide live evidence and was documented in `runtime-validation-history.md`.

Confirmed #43.2 runtime smoke:

```text
experimentId="fleetwide-bounded-live-20260624T125727207Z-1"
fleetWideBoundedLiveCandidate: 3
fleetWideBoundedLivePreState: 3
fleetWideBoundedLiveResult: 5
fleetWideBoundedLivePostState: 3
result="applied": 3
result="skipped": 2
failedCommands="0"
directRuntimeContext LaunchLog rows: 21
scopeViolation markers: 0
same-team markers: 0
```

Applied commands:

```text
Thapsus -> Volcano, 7 shots
Salamis -> Volcano, 7 shots
Cannae -> Volcano, 7 shots
```

The two skipped rows were expected `perShipCap="1"` blocks:

```text
reason="fleetWideBoundedLivePerShipCapBlocked"
```

This proves bounded command authority, cap enforcement, and direct command-result launch/spend correlation for a small cap=3 fleet-wide run. It does not prove allocator quality, target-selection quality, kill attribution, vanilla salvo suppression, or general tuning safety.

## Evidence channels to keep separate

Run modes:

```text
fixture
shadow-replay
controlled-live
fleet-wide-controlled
```

Spend/evidence categories:

```text
direct controlled command spend
vanilla / none-correlated spillover spend
missing or ambiguous spend evidence
```

#43.3 may summarize these side by side, but must not collapse them into one proof score.

## Corpus fields that matter

The #44 corpus layer should let this slice group or compare by:

- `runMode`;
- `selectedMode`;
- `heuristicCandidateId`;
- `parameterSnapshotHash`;
- scenario tags;
- manual verdict;
- eligible launcher count;
- excluded launcher counts by reason;
- hostile target count;
- command candidate/applied/skipped/failed/blocked counts;
- direct command-spend counts;
- vanilla / none-correlated spillover counts;
- missing evidence counts;
- conservative outcome hints;
- reviewer evidence gaps and next action.

If the current corpus cannot express one of these, record that as a handoff gap instead of inventing a metric.

Current known corpus gap: the committed corpus fixtures include `fleetWideReportOnly` schema coverage, but no committed `fleet-wide-controlled` corpus artifact for the successful #43.2 runtime smoke yet. Raw private `Player.log` should not be committed by default. The next worker should create a redacted/private artifact entry under ignored `artifacts/experiments/` or add a synthetic fixture only for schema coverage, depending on the review goal.

## Possible conclusions

#43.3 should leave one clear conclusion:

- A narrow next change is justified by direct evidence.
- No tuning yet.
- More bounded live evidence is needed.
- Measurement quality is the blocker.
- Existing uncontrolled behavior prevents interpretation.
- Safety evidence is still ambiguous.

Each conclusion should name the next issue or sub-slice that should own the follow-up.

Given the current prior evidence, the default starting hypothesis for #43.3 is:

```text
No allocator tuning yet from this single bounded-live run alone.
```

The first task is to turn the #43.2 bounded-live smoke into a corpus-level entry or blocker note, then decide whether more bounded live runs, outcome-hook measurement, vanilla salvo suppression, or allocator-quality review should own the next issue.

## Non-goals

#43.3 does not:

- implement new live behavior;
- tune allocator parameters directly from shadow replay;
- treat dry-run candidate rows as live success;
- hide failed or evidence-limited runs;
- rewrite the #44 corpus schema unless the schema itself is the blocker.

## Handoff condition after #43.3

A future worker should be able to read the #43.3 output and know:

- which evidence modes were present;
- which candidate/parameter snapshots were compared;
- whether direct controlled spend was actually observed;
- how much vanilla / none-correlated spillover remained;
- which evidence gaps matter most;
- whether the next step is tuning, more live evidence, measurement work, uncontrolled-behavior work, or no change.

## Suggested first steps

1. Review the #43.2 bounded-live smoke evidence in `runtime-validation-history.md`.
2. Decide how to represent that run in the #44 corpus without committing private raw logs.
3. If needed, create local ignored `artifacts/experiments/...` metadata/summary/verdict files for the real run.
4. Run `tools/summarize_experiment_corpus.py` against the corpus registry.
5. Produce a #43.3 conclusion: tune, no tuning, more bounded live evidence, measurement blocker, vanilla-spillover blocker, or safety ambiguity.

## Files likely relevant to Codex

- `dev-docs/plan/issue_43/00-context.md`
- `dev-docs/plan/issue_43/43.1/00-context.md`
- `dev-docs/plan/issue_43/43.2/00-context.md`
- `docs/diagnostics/experiment-corpus.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/diagnostics/snapshot-and-allocation.md`
- `dev-docs/plan/issue_39.1/00-context.md`
- `tools/summarize_experiment_corpus.py`
- `tools/fit_shadow_allocation.py`
- `tools/fixtures/experiment_corpus/`
