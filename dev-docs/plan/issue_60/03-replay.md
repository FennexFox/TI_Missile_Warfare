# Phase 03: Candidate replay and scoring

## Goal

- Replay candidate policies over the decision-context dataset and score
  surrogate pressure objectives separately from hard guardrail failures.

## Scope

- Replay current `pressure-aware-bounded-live-v1` behavior as the measured
  current policy.
- Replay at least one report-only candidate policy.
- Classify retained above-threshold selected-target rows as `avoidable`,
  `unavoidable`, or `inconclusive`.
- Score avoidable selected-target over-pressure, pressure imbalance among
  comparable alternatives, high-threat/high-score coverage preservation,
  churn/evidence-weak retarget penalties, and uncertainty penalties.
- Apply hard failure penalties for friendly targets, scope violations, command
  cap violations, parser failures, spillover misclassification, and command
  safety failures.

## Non-goals

- Do not implement a behavior-changing allocator heuristic.
- Do not treat shadow replay as proof of live combat improvement.
- Do not use `[OutcomeLog]` rows as rewards or kill proof.
- Do not collapse `shadow-replay`, `controlled-live`,
  `fleet-wide-controlled`, and `fixture` evidence modes into one proof score.

## Affected files

- `tools/replay_offline_fitting_candidates.py`
- `tools/fixtures/offline_fitting/retained_above_threshold_cases.txt`
- `tools/fixtures/offline_fitting/registry.jsonl`
- `docs/diagnostics/experiment-corpus.md`
- `dev-docs/plan/issue_60/00-master-plan.md`
- `dev-docs/plan/issue_60/02-dataset.md`
- `dev-docs/plan/issue_60/03-replay.md`

## Implementation steps

- Define the current-policy replay mapping from dataset row fields.
- Define the first report-only candidate policy. Prefer a conservative policy
  that exposes least-over-threshold fallback opportunities without changing live
  code.
- Implement replay output records with candidate id, parameter snapshot, row
  classification, objective metrics, guardrail results, and uncertainty state.
- Keep evidence-mode handling explicit in replay results.
- Add fixture cases for avoidable, unavoidable, inconclusive, blocked, and
  guardrail-failure rows.

## Acceptance criteria

- Current `pressure-aware-bounded-live-v1` behavior is replayed as current
  policy under measurement.
- At least one report-only candidate policy is replayed.
- Objective metrics and hard guardrail failures are reported separately.
- Rows with missing or lower-bound evidence cannot receive overconfident
  favorable verdicts.
- Candidate output is machine-readable and ready for report aggregation.

## Validation commands

- `python tools/check_layout.py`
- `python -m compileall tools`
- `python tools/build_offline_fitting_dataset.py --registry tools/fixtures/offline_fitting/registry.jsonl --output artifacts/offline-fitting/fixture-dataset --require-row-evidence --force`
- `python tools/replay_offline_fitting_candidates.py --dataset artifacts/offline-fitting/fixture-dataset/decision-contexts.jsonl --output artifacts/offline-fitting/fixture-replay --require-replay-evidence --force`

## Manual smoke tests

- Run replay against ignored local corpus artifacts if available.
- Inspect a small sample of replay rows and confirm evidence-mode and
  uncertainty fields are preserved.

## Rollback risks

- Medium. Bad scoring semantics could steer later live validation. Keep scoring
  transparent, fixture-backed, and conservative.

## Progress

- Implemented replay over Phase 2 decision-context rows.
- Replays current `pressure-aware-bounded-live-v1` as measured current behavior.
- Adds report-only `report-only-pressure-relief-v1`, which only suggests an
  alternate target with exact at-or-above-threshold pressure evidence.
- Fixture replay emits 16 records across 8 decision contexts and 2 policies.
- Retained above-threshold fixture cases cover `avoidable`, `unavoidable`, and
  `inconclusive`; selected-scope `wouldFail` exercises hard guardrail output.

## Decision log

- Candidate A is current behavior under measurement, not a validated tuning
  improvement.
- Candidate B remains report-only infrastructure until #60 produces evidence
  for a later behavior-changing issue.
- Soft objective metrics are reported separately from hard guardrail failures.
- Lower-bound pressure and missing alternatives block favorable report-only
  retarget conclusions instead of being treated as exact evidence.
- The first report-only policy prefers the highest-score non-pressure target
  only when exact pressure is at or above threshold. It is scoring
  infrastructure, not live allocator logic.

## Outcomes / Retrospective

- Phase 3 is complete for fixture-backed replay. It does not change live combat
  behavior and does not use outcome rows as rewards.
