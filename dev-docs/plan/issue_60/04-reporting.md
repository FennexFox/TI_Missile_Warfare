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

- Likely `tools/fit_shadow_allocation.py`
- Likely new report templates under `tools/` or `docs/`
- Relevant durable docs under `docs/planning/` and `docs/diagnostics/`
- This issue plan's phase progress and retrospective notes

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
- Add the final report command over committed fixtures once its filename is
  known.
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

- Not started.

## Decision log

- The report is the issue closure artifact. Later live validation belongs to a
  follow-up issue unless #60 explicitly grows new acceptance criteria.

## Outcomes / Retrospective

- Not completed yet.
