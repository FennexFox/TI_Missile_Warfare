# Offline fitting loop

This page defines the next project direction for missile allocation tuning. It is
a measurement-first loop over archived logs, not an automatic in-game combat
runner and not a live behavior-changing tuning loop.

## Decision

Before any new behavior-changing allocation heuristic is implemented, the project
should first close an offline fitting loop:

```text
archived Player.log / combat logs
  -> parser/importer
  -> allocation decision-context dataset
  -> candidate policy shadow replay
  -> objective / guardrail scoring
  -> ranked candidate report
  -> small live validation only for selected candidates
```

The immediate goal is to determine whether avoidable over-pressure exists in
bounded-live controlled allocation. The project should not assume that repeated
same-target pressure is a confirmed tuning problem until the dataset can classify
it as avoidable, unavoidable, or inconclusive.

## Why this replaces the previous tuning framing

Earlier working notes treated `pressure-aware-bounded-live-v1` as a first tuning
sweep and described Candidate A as current behavior to validate through a
baseline/follow-up run. That framing was too far ahead of the evidence. The
correct sequence is:

1. Build and audit the dataset.
2. Characterize the problem on archived logs.
3. Fit or rank candidate policies offline.
4. Use live runs only to validate a short list of candidates.
5. Implement behavior-changing tuning only after the offline evidence identifies
   a repeated, avoidable problem.

## Evidence modes

The offline fitting loop must preserve the evidence-mode boundary from
[Experiment corpus and parameter ledger](../diagnostics/experiment-corpus.md):

- `shadow-replay` can rank candidates and catch regressions, but it is not
  causal proof of combat improvement.
- `controlled-live` and `fleet-wide-controlled` remain the causal evidence modes
  for applied command behavior.
- `fixture` proves schema/tooling behavior only.

Offline fitting is a candidate filter. It narrows what deserves live validation;
it does not replace live validation.

## Dataset unit

The dataset row should represent an allocation decision context, not a whole
battle. Each row should preserve enough information to replay candidate policies
without re-reading the raw private log.

Minimum row groups:

- run identity: experiment id, run mode, mod commit, parameter snapshot hash, and
  scenario tags;
- launcher identity: ship, weapon/module evidence, player-control evidence, and
  command eligibility;
- selected target: id/name, pressure, threshold, score/rank evidence, and
  selected-target pressure decision;
- candidate targets: per-target pressure, threshold, under-threshold status,
  comparable feature evidence, score/rank evidence, and eligibility reason;
- command result: applied/skipped/failed, direct command-spend correlation, caps,
  and safety guardrails;
- evidence state: explicit `exact`, `lower-bound`, `unknown`, `inferred`, or
  `not-applicable` state for pressure, target alternatives, score/rank
  comparison, command correlation, outcome context, and overall row quality;
- uncertainty: exact vs lower-bound in-flight pressure, missing evidence, parser
  warnings, and spillover classification.

## First fitting objective

The first objective is not outcome-aware damage or kill optimization. It is a
surrogate pressure objective over auditable allocation contexts:

- penalize avoidable selected-target over-pressure;
- penalize large pressure imbalance when comparable alternatives exist;
- preserve high-threat or high-score target coverage when pressure evidence does
  not justify retargeting;
- penalize churny or evidence-weak retargets;
- apply hard failure penalties for friendly targets, scope violations, command
  cap violations, parser failures, or spillover misclassification.
- preserve row eligibility separately from policy verdicts so excluded evidence
  remains auditable instead of disappearing into one policy score.

Outcome rows may be used as hook-health context until a separate
outcome-to-allocation correlation design exists.

## Minimum loop closure

The offline loop is ready for real candidate fitting when one command can:

1. import or read a fixed log corpus;
2. emit a decision-context dataset;
3. replay at least the current policy and one report-only candidate policy;
4. score objective metrics and hard guardrails;
5. produce `ranked-candidates.md`, guardrail reports, row-evaluation summaries,
   and machine-readable results;
6. classify each candidate as `candidate-filtered`, `needs-live-validation`,
   `inconclusive`, or `blocked`.

## Current blocker

Issue #43.4 improves the measurement surface with target-alternative feature
lists, score/rank evidence, and best-effort pre-command in-flight pressure. The
remaining blocker is corpus-level loop closure, not immediate live tuning.

The next offline-fitting implementation should therefore:

- import a fixed archived-log corpus into allocation decision-context rows;
- preserve per-alternative pressure, threshold, score/rank, and eligibility
  evidence where present;
- classify retained above-threshold rows with `noUnderThresholdAlternative` as
  `avoidable`, `unavoidable`, or `inconclusive`;
- replay the current policy and at least one report-only candidate policy;
- score surrogate pressure objectives and hard guardrails;
- separate bad observed rows, bad candidate rows, evidence-blocked rows,
  diagnostic warnings, and policy-level downgrade reasons;
- keep live command behavior unchanged until a ranked candidate receives small
  controlled-live or fleet-wide-controlled validation.

## Relationship to Candidate A and Candidate B

- Candidate A is current `pressure-aware-bounded-live-v1` behavior under
  measurement. It is not a validated tuning improvement.
- The existing Candidate B comparison helper is measurement infrastructure. It
  is not a behavior-changing candidate.
- Future behavior-changing candidates should be generated from offline fitting
  evidence, not from ad hoc inspection of one live log.
