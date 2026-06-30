# Phase 04: Report closure and validation

## Goal

- Close the offline fitting loop by producing ranked candidate reports,
  machine-readable candidate verdicts, and documentation that preserves the
  live-validation boundary.

## Scope

- Emit `ranked-candidates.md`.
- Emit machine-readable candidate verdicts such as `candidate-filtered`,
  `needs-live-validation`, `inconclusive`, or `blocked`.
- Emit a guardrail report that separates hard failures from soft objective
  scores.
- Preserve dataset identity, candidate identity, parameter snapshot, evidence
  modes, scenario tags, parser warning state, and raw-log privacy notes.
- Document that behavior-changing candidates still need small controlled-live or
  fleet-wide-controlled validation before becoming project direction.

## Non-goals

- Do not open the door to live tuning solely from offline replay.
- Do not make outcome-aware ranking claims.
- Do not publish private raw log paths.
- Do not broaden issue scope into #6/#7 behavior-changing allocation or launch
  discipline work.

## Affected files

- `tools/report_offline_fitting_candidates.py`
- `docs/diagnostics/experiment-corpus.md`
- `dev-docs/plan/issue_60/00-master-plan.md`
- `dev-docs/plan/issue_60/04-reporting.md`

## Implementation steps

- Define report output directory and filenames.
- Aggregate dataset and replay outputs into candidate-level metrics.
- Implement verdict rules that block or downgrade evidence-weak candidates.
- Generate `ranked-candidates.md`, machine-readable verdicts, and a guardrail
  report.
- Update durable docs with only non-private, durable decisions.
- Run final validation and update this phase's outcome notes.

## Acceptance criteria

- `ranked-candidates.md` is generated.
- Machine-readable candidate verdicts are generated.
- Guardrail failures, parser warnings, lower-bound pressure, missing
  alternatives, spillover ambiguity, and command-safety failures prevent
  overconfident `candidate-filtered` verdicts.
- Docs state that selected candidates still require controlled-live or
  fleet-wide-controlled validation before behavior-changing implementation.
- No live combat behavior changes are included in #60.

## Validation commands

- `python tools/check_layout.py`
- `python -m compileall tools`
- `python tools/build_offline_fitting_dataset.py --registry tools/fixtures/offline_fitting/registry.jsonl --output artifacts/offline-fitting/fixture-dataset --require-row-evidence --force`
- `python tools/replay_offline_fitting_candidates.py --dataset artifacts/offline-fitting/fixture-dataset/decision-contexts.jsonl --output artifacts/offline-fitting/fixture-replay --require-replay-evidence --force`
- `python tools/report_offline_fitting_candidates.py --replay artifacts/offline-fitting/fixture-replay/replay-results.jsonl --summary artifacts/offline-fitting/fixture-replay/candidate-summary.json --output artifacts/offline-fitting/fixture-report --require-report-evidence --force`
- `dotnet build TI_Missile_Fire_Control.sln` only if the final change touches
  C# source or project files.

## Manual smoke tests

- Inspect generated `ranked-candidates.md` for private raw log paths before any
  artifact is copied into durable docs or PR text.
- Confirm report language does not claim live combat improvement.

## Rollback risks

- Low to medium. Reports are generated artifacts, but bad verdict wording could
  mislead later behavior-changing work. Keep verdict rules conservative.

## Progress

- Implemented report closure over replay artifacts.
- Generates `ranked-candidates.md`, `candidate-verdicts.json`, and
  `guardrail-report.md` under ignored `artifacts/` paths.
- Fixture report emits two machine-readable candidate verdicts using the #60
  vocabulary.
- The generated report explicitly states that offline replay is a candidate
  filter only and not live combat proof.

## Decision log

- The report is the issue closure artifact. Later live validation belongs to a
  follow-up issue unless #60 explicitly grows new acceptance criteria.
- Verdict rules are conservative: hard guardrail failures become `blocked`, and
  parser warnings, lower-bound pressure, missing alternatives, or spillover
  ambiguity prevent favorable verdicts.
- `ranked-candidates.md` is generated under `artifacts/` and should be inspected
  before any content is copied into durable docs or PR text.

## Outcomes / Retrospective

- Phase 4 is complete for fixture-backed report closure. No live combat
  behavior changes are included.
