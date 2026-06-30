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

- Likely `tools/parse_player_log.py`
- Likely `tools/import_player_log_experiments.py`
- Likely `tools/fit_shadow_allocation.py` or a new offline-fitting dataset tool
- Likely `tools/fixtures/experiment_corpus/**`
- Relevant docs under `docs/diagnostics/` and `docs/planning/`

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
- `python tools/parse_player_log.py --require-launchlogs`
- Add the final dataset command over committed fixtures once its filename and
  fixture inputs are known.

## Manual smoke tests

- Run the dataset command against an ignored local corpus only if private logs
  are available.
- Confirm generated artifacts stay under ignored `artifacts/` paths.

## Rollback risks

- Medium. Dataset schema changes can break later replay phases. Keep schema
  additions additive unless a fixture proves an existing field is wrong.

## Progress

- Not started.

## Decision log

- Dataset rows are the #60 unit of analysis; whole-battle summaries are useful
  context but not sufficient for candidate replay.

## Outcomes / Retrospective

- Not completed yet.
