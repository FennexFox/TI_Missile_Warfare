# Phase 05: Quality pass and evidence semantics

## Goal

- Strengthen #60 from minimum loop closure into a durable offline fitting
  foundation with explicit row-level evidence state, row eligibility, policy
  verdict separation, focused regression tests, and documentation.

## Scope

- Model row-local evidence state for pressure, target alternatives, score/rank
  comparison, command correlation, outcome context, and overall row quality.
- Separate bad observed rows, bad candidate rows, evidence-blocked rows, and
  policy verdict downgrades.
- Keep report-only candidate replay conservative and fail closed when exact
  pressure, target-alternative, or score/rank evidence is missing.
- Add fixture coverage for unknown pressure evidence and candidate guardrail
  failures.
- Add Python regression tests for evidence-state classification, retained
  above-threshold semantics, row/policy aggregation, and report output.
- Update durable diagnostics and planning docs.

## Non-goals

- Do not change live combat behavior.
- Do not tune live allocator heuristics.
- Do not treat fixture evidence as live validation.
- Do not use outcome rows as rewards or kill proof.

## Affected files

- `tools/build_offline_fitting_dataset.py`
- `tools/replay_offline_fitting_candidates.py`
- `tools/report_offline_fitting_candidates.py`
- `tools/test_offline_fitting.py`
- `tools/fixtures/offline_fitting/evidence_quality_cases.txt`
- `tools/fixtures/offline_fitting/registry.jsonl`
- `docs/diagnostics/experiment-corpus.md`
- `docs/planning/offline-fitting-loop.md`
- `dev-docs/plan/issue_60/00-master-plan.md`
- `dev-docs/plan/issue_60/05-quality-pass.md`

## Acceptance criteria

- Dataset rows expose an `evidenceState` object with stable labels:
  `exact`, `lower-bound`, `unknown`, `inferred`, and `not-applicable`.
- Replay output exposes `rowEvaluation` separately from policy summaries.
- Candidate guardrail failures block policy verdicts without hiding observed
  source-row failures.
- Evidence-blocked rows are excluded from favorable candidate signals but still
  visible in reports.
- Fixture-only evidence can exercise the toolchain but remains inconclusive for
  live validation.
- Regression tests cover the new semantics.

## Validation commands

- `python tools/check_layout.py`
- `python -m compileall tools`
- `python tools/test_offline_fitting.py`
- `python tools/build_offline_fitting_dataset.py --registry tools/fixtures/offline_fitting/registry.jsonl --output artifacts/offline-fitting/fixture-dataset --require-row-evidence --force`
- `python tools/replay_offline_fitting_candidates.py --dataset artifacts/offline-fitting/fixture-dataset/decision-contexts.jsonl --output artifacts/offline-fitting/fixture-replay --require-replay-evidence --force`
- `python tools/report_offline_fitting_candidates.py --replay artifacts/offline-fitting/fixture-replay/replay-results.jsonl --summary artifacts/offline-fitting/fixture-replay/candidate-summary.json --output artifacts/offline-fitting/fixture-report --require-report-evidence --force`

## Progress

- Implemented explicit dataset `evidenceState` modeling.
- Implemented replay `rowEvaluation` output and policy summary fields for row
  eligibility, bad observed rows, bad candidate rows, evidence blockers,
  favorable rows, target changes, and eligible score deltas.
- Updated reports to show row counts, downgrade reasons, diagnostic warnings,
  and separated guardrail categories.
- Added focused Python regression tests and evidence-quality fixture cases.

## Decision log

- A row can carry useful diagnostic signal while still being excluded from a
  favorable policy verdict.
- Policy verdicts should communicate why they were downgraded instead of
  collapsing row exclusions into a single hard-failure count.
- Fixture evidence remains tooling coverage only, even when the replay finds a
  favorable-looking candidate.

## Outcomes / Retrospective

- Phase 5 is complete for fixture-backed quality-pass semantics. No live combat
  behavior changes are included.
