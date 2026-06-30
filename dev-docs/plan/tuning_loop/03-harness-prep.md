# Phase 03: Offline fitting harness prep

## Goal

Finish the remaining large-preparation work needed to make archived-log fitting
cheap to repeat. This phase should reduce manual agent-loop fatigue by closing a
single e2e path from logs to a reviewable candidate report.

## Scope

- Define the decision-context dataset expected from imported logs.
- Define the comparison/replay artifacts needed for offline candidate filtering.
- Keep Candidate A as current behavior under measurement, not a behavior change.
- Keep Candidate B as report-only infrastructure unless offline fitting later
  selects a behavior-changing candidate.
- Add docs or lightweight tooling only if it reduces repeated manual review.

## Non-goals

- Do not change allocator heuristics in this phase.
- Do not tune target-value, point-defense, launch-window, or outcome-aware
  scoring.
- Do not join `[OutcomeLog]` rows back to `[AllocationLog]` rows.
- Do not broaden command authority, selected scope, fleet scope, caps, or command
  behavior.
- Do not commit private raw `Player.log` files or ignored generated artifacts.

## Inputs

- `docs/planning/offline-fitting-loop.md`
- `dev-docs/plan/tuning_loop/00-context.md`
- `dev-docs/plan/tuning_loop/01-runbook.md`
- `dev-docs/plan/tuning_loop/02-baseline-corpus.md`
- local ignored bounded-live experiment imports under `artifacts/experiments/`
- existing #43.4/#56 bounded-live fixture and runtime corpus summaries

## Required deliverables

### 1. Dataset feature gap statement

Document the remaining field gap that blocks reliable offline pressure fitting:
per-alternative pressure and threshold evidence. In particular, retained
above-threshold rows with `noUnderThresholdAlternative` must become auditable.

Minimum future row fields:

- selected target pressure, threshold, and pressure source;
- alternative target pressure, threshold, under-threshold status, score/rank, and
  eligibility reason;
- best under-threshold alternative, if one exists;
- least-over-threshold alternative, if no under-threshold alternative exists;
- uncertainty class for exact, lower-bound, or missing pressure evidence.

### 2. Report artifact definition

The existing summary comparison helper is useful, but it is not the final fitting
loop. A complete offline fitting report should include:

- dataset identity and evidence-mode mix;
- candidate policy identity and parameter snapshot;
- objective metrics;
- hard guardrail checks;
- blocker and missing-feature counts;
- candidate ranking;
- live-validation shortlist.

### 3. First replay boundary

The first replay boundary should compare policies on archived rows without
changing live behavior:

- current Candidate A behavior;
- report-only least-over-threshold diagnostic policy;
- later parameterized variants only after the dataset exposes the required
  alternative pressure evidence.

The first replay should not include more than one new behavior family.

### 4. Compact fixture verdict policy

Classify compact bounded-live fixtures that lack modern required hook labels.
Either:

- declare them schema fixtures that are not expected to satisfy full parser
  health verdicts; or
- upgrade them with modern required hook labels and make them full-health
  parser fixtures.

This is not a heuristic blocker, but it should be documented so validation
reports stop repeating the same caveat.

## Acceptance criteria

This phase is complete when:

- the offline fitting posture is documented in durable docs;
- the old live tuning framing is replaced with pre-tuning measurement language;
- per-alternative pressure diagnostics are named as the next report-only blocker;
- comparison/report artifacts are defined;
- compact fixture verdict failures are classified as schema-fixture expected or
  upgraded away;
- validation commands for docs/tooling changes are listed;
- no heuristic behavior has changed.

## Validation commands

For documentation-only changes:

```powershell
python tools\check_layout.py
```

If comparison, importer, dataset, or replay tooling is added:

```powershell
python tools\check_layout.py
python -m compileall tools
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py tools\compare_experiment_summaries.py
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
```

## Decision rules

- If this phase remains docs-only, commit it separately from behavior changes.
- If small tooling is added, keep it report-only and deterministic.
- If a proposed change requires reading outcome rows as allocation success, move
  it to a separate outcome-correlation issue.
- If a proposed change touches command authority or scope, stop and create a
  separate command-safety issue.

## Next phase

Add report-only per-alternative pressure diagnostics, then build the smallest
possible dataset/replay command that turns archived logs into a candidate report.
Do not implement a behavior-changing Candidate B until the offline report shows a
repeated, avoidable pressure problem.
