# Phase 2: Corpus summarizer and fixtures

## Goal

Add a minimal file-based corpus summary workflow with synthetic fixtures.

## Scope

- Add `tools/summarize_experiment_corpus.py`.
- Add fixture registry and artifact examples under `tools/fixtures/experiment_corpus/`.
- Add a `.gitignore` exception for committed fixture JSONL while preserving ignored generated JSONL elsewhere.

## Non-goals

- No polished analytics UI.
- No automatic game launch or combat setup.
- No mutation of existing fitting reports.

## Affected Files

- `.gitignore`
- `tools/summarize_experiment_corpus.py`
- `tools/fixtures/experiment_corpus/**`
- `dev-docs/plan/issue_44/02-tooling-fixtures.md`

## Implementation Steps

- Read registry entries from JSONL.
- Validate required fields and known run modes/verdicts.
- Check artifact links without treating missing private raw logs as fatal.
- Read optional parsed/fitting summaries when present.
- Write `corpus-summary.json`, `candidate-comparison.csv`, and `scenario-breakdown.md`.

## Acceptance Criteria

- Fixture, shadow replay, controlled-live, and recommendation-blocked evidence can be represented separately.
- Summary output includes run-mode counts, verdict counts, scenario tags, candidate counts, missing evidence, skipped/failed commands, overkill/under-saturation/target-mismatch risks, regressions, and vanilla spillover when fields are present.

## Validation Commands

- `python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture`
- `python -m ruff check tools\summarize_experiment_corpus.py`
- `python -m compileall tools`

## Manual Smoke Tests

- Inspect generated fixture summary files under ignored `artifacts\fitting\corpus-summary-fixture`.

## Rollback Risks

- Removing the tool and fixtures reverts to local/manual experiment tracking only.

## Progress

- Completed the summarizer and fixture corpus.

## Decision Log

- Candidate comparison rows are separated by run mode to avoid merging shadow replay with controlled-live evidence.
- Broken artifact links are reported as warnings in the summary and console output, not as catastrophic failures.

## Outcomes / Retrospective

- The initial workflow is intentionally boring and file-based, matching #44's scope and keeping future richer analytics optional.
