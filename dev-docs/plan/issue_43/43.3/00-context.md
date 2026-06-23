# Issue #43.3 context — Corpus review and no-tuning handoff

Updated: 2026-06-23
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.3/00-context.md`
Parent umbrella: `dev-docs/plan/issue_43/00-context.md`
Previous slices:
- `dev-docs/plan/issue_43/43.1/00-context.md`
- `dev-docs/plan/issue_43/43.2/00-context.md`

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

## Possible conclusions

#43.3 should leave one clear conclusion:

- A narrow next change is justified by direct evidence.
- No tuning yet.
- More bounded live evidence is needed.
- Measurement quality is the blocker.
- Existing uncontrolled behavior prevents interpretation.
- Safety evidence is still ambiguous.

Each conclusion should name the next issue or sub-slice that should own the follow-up.

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
