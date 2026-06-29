# Phase 03: Pressure-aware tuning harness prep

## Goal

Finish the remaining large-preparation work before the first heuristic tuning
change. This phase should make the tuning loop cheap to repeat: baseline and
follow-up runs must be comparable, parameter choices must be recorded, validation
noise must be classified, and verdicts must be reviewable.

## Scope

- Define the baseline/follow-up comparison artifact.
- Define the pressure-aware parameter snapshot format.
- Define the first small sweep boundary.
- Decide how compact bounded-live fixtures should be interpreted when they lack
  modern required hook labels.
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

- `dev-docs/plan/tuning_loop/00-context.md`
- `dev-docs/plan/tuning_loop/01-runbook.md`
- `dev-docs/plan/tuning_loop/02-baseline-corpus.md`
- `artifacts/experiments/tuning-loop-baseline/` local ignored baseline import
- `artifacts/fitting/tuning-loop-baseline-summary/` local ignored baseline
  summary
- existing #43.4/#56 bounded-live fixture and runtime corpus summaries

## Required deliverables

### 1. Comparison artifact definition

Create or update a comparison template that takes a baseline corpus summary and a
follow-up corpus summary and produces a reviewable before/after record.

Minimum output sections:

- run identity and comparability;
- objective metrics;
- guardrail checks;
- blocker deltas;
- verdict recommendation;
- human review notes.

The template may be documentation-only for the first pass. If implemented as a
script later, it should preserve the same section names and verdict vocabulary.

### 2. Parameter snapshot format

Define the first pressure-aware parameter snapshot schema. It should be small and
explicit enough to include in import metadata or a sidecar fixture.

Minimum fields:

- `heuristicCandidateId`;
- `family`;
- `pressureReference`;
- `thresholdMultiplier`;
- `pressureSourcePolicy`;
- `lowerBoundPressurePolicy`;
- `retargetPolicy`;
- `viableAlternativePolicy`;
- `deferredKnobs`;
- `notes`.

The first baseline candidate should continue to be
`baseline-fleet-wide-bounded-live-v1` unless a later change explicitly renames
it.

### 3. First sweep boundary

Document the first allowed sweep before writing heuristic code. The first sweep
must stay inside pressure threshold / retarget preference behavior.

Recommended first sweep shape:

- baseline: `thresholdMultiplier = 1.0`, current #56 behavior;
- candidate A: a minimal pressure-aware retarget preference change that only
  applies when exact pressure is at or above `max(killSize, saturationSize)` and
  a comparable same-cycle alternative exists;
- optional candidate B only if candidate A is too weak to move metrics, and only
  if it remains in the same family.

The first sweep should not include more than one behavioral code change family.

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

- a comparison template exists and names the metrics to compare;
- pressure-aware parameter snapshots have a documented schema;
- the first sweep boundary is documented with explicit non-goals;
- compact fixture verdict failures are classified as schema-fixture expected or
  upgraded away;
- validation commands for docs/tooling changes are listed;
- no heuristic behavior has changed.

## Validation commands

For documentation-only changes:

```powershell
python tools\check_layout.py
```

If a comparison helper or parameter-file loader is added:

```powershell
python tools\check_layout.py
python -m compileall tools
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
```

## Decision rules

- If this phase remains docs-only, commit it separately from heuristic changes.
- If small tooling is added, keep it report-only and deterministic.
- If a proposed change requires reading outcome rows as allocation success, move
  it to a separate outcome-correlation issue.
- If a proposed change touches command authority or scope, stop and create a
  separate command-safety issue.

## Next phase

After this phase, enter the first pressure-aware tuning sweep. The next phase may
apply one narrow heuristic change and then run the baseline/follow-up comparison
from the documented template.
