# Phase 06: Merge-readiness evidence follow-up

## Goal

- Address the final pre-merge quality gaps in offline fitting evidence
  semantics without changing game runtime behavior.

## Scope

- Add explicit per-target-alternative pressure evidence state.
- Tighten row-level exact pressure to require exact bound and exact in-flight
  evidence quality.
- Make the report-only policy skip known friendly alternatives.
- Keep candidate guardrail failure coverage through focused tests instead of
  making the main report-only policy intentionally unsafe.
- Split diagnostic signal counts from report-only candidate-improvement counts.
- Add fixture-level regression coverage for dataset, replay, and report
  summaries.
- Update durable docs for the final #60 semantics.

## Non-goals

- Do not change C# source or live combat behavior.
- Do not introduce live allocator tuning.
- Do not treat fixture evidence as validation of candidate quality.
- Do not use private logs or generated artifacts as committed evidence.

## Affected files

- `tools/build_offline_fitting_dataset.py`
- `tools/replay_offline_fitting_candidates.py`
- `tools/report_offline_fitting_candidates.py`
- `tools/test_offline_fitting.py`
- `docs/diagnostics/experiment-corpus.md`
- `docs/planning/offline-fitting-loop.md`
- `dev-docs/plan/issue_60/00-master-plan.md`
- `dev-docs/plan/issue_60/06-merge-readiness-follow-up.md`

## Implementation steps

- Add `pressureEvidenceState`, `pressureEvidenceReason`, and nested
  alternative `evidenceState.pressure` to target alternatives.
- Count per-target-alternative pressure evidence states in dataset summaries and
  fixture gates.
- Change `pressure_evidence_state()` so `exact` requires exact bound plus exact
  in-flight evidence quality; exact-bound/unknown-quality rows become
  `inferred`.
- Filter known-friendly alternatives out of `report-only-pressure-relief-v1`.
- Replace ambiguous favorable summary usage with `diagnosticSignalRowCount` and
  `candidateImprovementRowCount`.
- Extend regression tests with fixture-level dataset/replay/report assertions.
- Update docs with the stricter exactness and signal semantics.

## Acceptance criteria

- Non-pressure alternatives no longer rely on `pressure=None` alone to convey
  evidence meaning.
- Exact pressure is not granted to unknown-quality pressure rows.
- The real report-only policy does not select a known friendly target.
- Candidate-created guardrail failures remain covered by direct helper tests.
- Reports distinguish current-policy diagnostic signals from report-only
  candidate-improvement signals.
- Fixture-level tests assert expected row counts, evidence counts,
  bad-candidate separation, and final verdicts.

## Validation commands

- `python tools/check_layout.py`
- `python -m compileall tools`
- `python tools/test_offline_fitting.py`
- `python tools/parse_player_log.py tools/fixtures/outcome_hooks.txt --require-launchlogs`
- `python tools/build_offline_fitting_dataset.py --registry tools/fixtures/offline_fitting/registry.jsonl --output artifacts/offline-fitting/fixture-dataset --require-row-evidence --force`
- `python tools/replay_offline_fitting_candidates.py --dataset artifacts/offline-fitting/fixture-dataset/decision-contexts.jsonl --output artifacts/offline-fitting/fixture-replay --require-replay-evidence --force`
- `python tools/report_offline_fitting_candidates.py --replay artifacts/offline-fitting/fixture-replay/replay-results.jsonl --summary artifacts/offline-fitting/fixture-replay/candidate-summary.json --output artifacts/offline-fitting/fixture-report --require-report-evidence --force`

## Manual smoke tests

- Inspect generated fixture verdicts to confirm fixture-only evidence remains
  inconclusive.
- Confirm no C# or runtime integration files changed.

## Rollback risks

- Low. Changes are limited to offline Python tools, fixtures tests, and docs.
  The main risk is downstream consumers expecting the older `favorableRowCount`
  summary field.

## Progress

- Added per-target-alternative pressure evidence state and summary counts.
- Tightened exact pressure evidence to require exact prior bound and exact
  in-flight evidence quality.
- Updated report-only policy selection to skip known friendly alternatives.
- Split current-policy diagnostic signals from report-only candidate-improvement
  signals in replay summaries and reports.
- Added fixture-level regression assertions for dataset, replay, and verdict
  outputs.
- Updated durable docs for final #60 evidence semantics.

## Decision log

- Per-target pressure state is explicit even when pressure is not applicable or
  unknown for a non-pressure alternative.
- Friendly-target policy filtering belongs in the real report-only candidate;
  direct helper tests cover unsafe candidate guardrail accounting.
- Split signal counts replace the ambiguous favorable-row summary in reports.

## Outcomes / Retrospective

- Phase 6 is complete for merge-readiness follow-up semantics. No live combat
  behavior changes are included.
