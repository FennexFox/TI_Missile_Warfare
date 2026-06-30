# Phase 02: Decision-context dataset extraction

## Goal

- Implement the corpus import or read path that emits allocation
  decision-context rows suitable for candidate replay without re-reading private
  raw logs.

## Scope

- Define and emit a dataset row for each allocation decision context.
- Preserve run identity: experiment id, scenario tags, mod commit/build
  identity, parameter snapshot hash, run mode, and parser warning state where
  available.
- Preserve launcher identity, command eligibility, player-control evidence,
  weapon/module evidence, and `ammoGateBudgetShots`.
- Preserve selected-target pressure, threshold, score/rank evidence,
  selected-target pressure decision, and target identity.
- Preserve per-alternative pressure, threshold, under-threshold status,
  comparable-feature evidence, score/rank evidence, and eligibility reason when
  diagnostics provide them.
- Preserve command result evidence, direct command-spend correlation, command
  caps, skipped/failed reasons, and safety guardrails.
- Preserve uncertainty fields for exact vs lower-bound pressure, missing
  evidence, parser warnings, and spillover classification.

## Non-goals

- Do not score candidates in this phase except for basic dataset health checks.
- Do not join `[OutcomeLog]` rows to allocation rows.
- Do not treat lower-bound pressure as exact pressure.
- Do not import private raw logs into committed paths.
- Do not change live command behavior.

## Affected files

- `tools/build_offline_fitting_dataset.py`
- `tools/fixtures/offline_fitting/**`
- `docs/diagnostics/experiment-corpus.md`
- `dev-docs/plan/issue_60/00-master-plan.md`
- `dev-docs/plan/issue_60/02-dataset.md`

## Implementation steps

- Inventory current `AllocationLog`, `LaunchLog`, `SnapshotLog`, and experiment
  corpus fields that already satisfy #60.
- Define the decision-context row schema and machine-readable output format.
- Add fixture coverage for selected-target evidence, alternative-target
  evidence, command results, warnings, and uncertainty classes.
- Implement the import/read command over a fixed archived corpus.
- Ensure rows preserve enough evidence to replay candidate policies without
  private raw logs.
- Document fields that remain unavailable as explicit blocker or uncertainty
  columns.

## Acceptance criteria

- One command imports or reads a fixed archived log corpus.
- The command emits allocation decision-context rows with selected-target and
  alternative-target evidence when present.
- The dataset preserves enough evidence to replay candidate policies without
  re-reading private raw logs.
- Retained above-threshold rows with `noUnderThresholdAlternative` carry enough
  alternative pressure evidence to classify as `avoidable`, `unavoidable`, or
  `inconclusive`.
- Parser warnings, lower-bound pressure, missing alternatives, and spillover
  ambiguity are represented as data rather than silently ignored.

## Validation commands

- `python tools/check_layout.py`
- `python -m compileall tools`
- `python tools/build_offline_fitting_dataset.py --registry tools/fixtures/offline_fitting/registry.jsonl --output artifacts/offline-fitting/fixture-dataset --require-row-evidence --force`
- Optional parser smoke, separate from dataset validation:
  `python tools/parse_player_log.py tools/fixtures/outcome_hooks.txt --require-launchlogs`

## Manual smoke tests

- Run the dataset command against an ignored local corpus only if private logs
  are available.
- Confirm generated artifacts stay under ignored `artifacts/` paths.

## Rollback risks

- Medium. Dataset schema changes can break later replay phases. Keep schema
  additions additive unless a fixture proves an existing field is wrong.

## Progress

- Implemented the Phase 2 dataset command and committed fixture registry.
- The command emits `decision-contexts.jsonl`, `decision-contexts.json`, and
  `dataset-summary.json` under ignored `artifacts/` output paths.
- Fixture validation currently emits eight rows: bounded-live rows with target
  alternatives, retained above-threshold classification cases, lower-bound
  pressure, and one selected-scope `wouldFail` command candidate.

## Decision log

- Dataset rows are the #60 unit of analysis; whole-battle summaries are useful
  context but not sufficient for candidate replay.
- `tools/build_offline_fitting_dataset.py` reads row-level `AllocationLog`
  records from `sourceLogPath` when present. Summary-only registry entries are
  warned as evidence-limited instead of being expanded from aggregate counters.
- Rows include normalized replay groups plus `rawFields` so later replay/scoring
  phases do not need private raw logs to recover diagnostic fields.
- Bounded-live pressure is attached to `boundedLiveOriginalTargetId` when
  present, while `isSelectedTarget` remains the actual command target after any
  retarget.
- `targetAlternative*` fields are parsed as pipe-delimited lists, not CSV.

## Outcomes / Retrospective

- Phase 2 is complete for fixture-backed corpus input. It does not score
  candidates, join outcome logs, or change live combat behavior.
