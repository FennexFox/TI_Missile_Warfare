# Offline fitting runbook

Status: absorbed into `dev-docs/plan/issue_60/`. This file is retained as
historical input and is not the active implementation plan.

## Goal

Make archived-log pressure analysis repeatable enough that future agents do not
have to re-interpret individual `Player.log` files by hand. The desired loop is:

```text
log corpus -> dataset -> candidate replay -> scoring -> report -> live validation shortlist
```

This runbook supersedes the earlier baseline/follow-up live tuning framing for
this folder. Live runs still matter, but only after offline fitting has produced
a short, auditable candidate list.

## Preconditions

- `00-context.md` describes the current pre-tuning measurement posture.
- The working tree commit is recorded for any generated artifact.
- Private raw logs remain under ignored `artifacts/` paths.
- Runtime settings and UMM toggles are recorded when a log was generated.
- No behavior-changing heuristic is made until offline fitting identifies a
  repeated, avoidable problem.

## Dataset capture

1. Record the source commit and working tree state:

   ```powershell
   git rev-parse HEAD
   git status --short
   ```

2. Import bounded-live `Player.log` files into ignored local artifacts:

   ```powershell
   python tools\import_player_log_experiments.py `
     --log <private Player.log> `
     --output artifacts\experiments\offline-fitting-input `
     --parameters tools\fixtures\experiment_corpus\baseline-fleet-wide-bounded-live-v1.parameters.json `
     --heuristic-candidate-id current-pressure-aware-bounded-live-v1 `
     --run-mode fleet-wide-controlled `
     --scenario-tag bounded-live `
     --scenario-tag offline-fitting-input `
     --mod-commit <commit-sha> `
     --force
   ```

3. Summarize the corpus:

   ```powershell
   python tools\summarize_experiment_corpus.py `
     --registry artifacts\experiments\offline-fitting-input\registry.jsonl `
     --output artifacts\fitting\offline-fitting-input-summary
   ```

4. Build or refresh a decision-context dataset when that tool exists. Until then,
   use corpus summaries and raw imported experiment rows as the intermediate
   artifact.

## Candidate replay target

The replay tool should eventually evaluate candidate policies without changing
combat behavior. At minimum it should replay:

- current Candidate A behavior;
- a report-only policy that records what would happen if least-over-threshold
  fallback were allowed;
- any future candidate generated from the search space.

The replay result must record hard guardrail failures separately from soft
objective scores.

## Objective and guardrail scoring

First-loop surrogate objective:

- selected-target over-pressure when comparable alternatives exist;
- pressure imbalance between selected and alternative targets;
- undercoverage or churn penalties where pressure evidence is weak;
- uncertainty penalties for lower-bound or missing in-flight evidence.

Hard guardrails:

- parser verdict must remain OK;
- same-team target markers must remain zero;
- scope-violation markers must remain zero;
- failed commands must be zero or explained;
- vanilla / none-correlated spillover must not be counted as controlled spend;
- lower-bound pressure must not be treated as exact pressure;
- no outcome-aware scoring is introduced.

## Current missing dataset feature

When a row says `noUnderThresholdAlternative`, the dataset must expose the
per-alternative pressure and threshold evidence used to reach that conclusion.
Without that table, the result is `inconclusive`, not proof that over-pressure was
unavoidable.

Required next report-only fields:

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

## Comparison and reports

For summary-to-summary comparisons, use `tools\compare_experiment_summaries.py`
when available. For candidate replay results, the future report should produce:

```text
artifacts/fitting/<run-id>/ranked-candidates.md
artifacts/fitting/<run-id>/candidate-results.jsonl
artifacts/fitting/<run-id>/guardrail-report.md
```

A report may recommend live validation only when the candidate passes hard
guardrails and improves the surrogate objective on enough auditable rows.

## Verdict vocabulary

Use one of these verdicts for each offline replay or comparison:

- `candidate-filtered`: passes offline guardrails and merits live validation.
- `blocked`: hard guardrail failed or required evidence is missing.
- `no material change`: comparable evidence exists, but the candidate does not
  improve the surrogate objective enough to justify live validation.
- `inconclusive`: evidence is too sparse or too ambiguous to classify.
- `needs-live-validation`: offline evidence is supportive but not causal proof.

## Validation commands

For docs-only planning changes:

```powershell
python tools\check_layout.py
```

For parser/importer/corpus/comparison tooling changes:

```powershell
python tools\check_layout.py
python -m compileall tools
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py tools\compare_experiment_summaries.py
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
```

For mod or allocator changes:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m compileall tools
python tools\parse_player_log.py --require-launchlogs
```

Do not claim mod-load or in-game validation unless it was actually performed.
