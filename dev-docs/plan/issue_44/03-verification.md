# Phase 3: Validation and handoff

## Goal

Validate the #44 documentation, tooling, and fixtures without claiming runtime combat validation.

## Scope

- Run repository layout checks.
- Run Python lint/compile checks.
- Run the corpus summarizer against committed fixtures.
- Build the solution when local references allow it.

## Non-goals

- No in-game smoke test.
- No runtime mod-load claim.

## Affected Files

- `dev-docs/plan/issue_44/03-verification.md`

## Implementation Steps

- Run the validation commands from `00-master-plan.md`.
- Record exact command outcomes.
- Note any local environment limitations honestly.

## Acceptance Criteria

- Static tooling checks pass or any environment-specific failures are documented.
- The fixture summary workflow produces all expected output files under ignored `artifacts/`.

## Validation Commands

- `dotnet build TI_Missile_Fire_Control.sln`
- `python tools\check_layout.py`
- `python -m ruff check tools\parse_player_log.py tools\fit_shadow_allocation.py tools\summarize_experiment_corpus.py`
- `python -m compileall tools`
- `python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture`

## Manual Smoke Tests

- Confirm the generated fixture corpus summary separates fixture, shadow replay, and controlled-live modes.

## Rollback Risks

- Validation artifacts are under ignored `artifacts/` and can be deleted safely.

## Progress

- Completed validation.

## Decision Log

- `python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture` passed and wrote fixture outputs under ignored `artifacts/`.
- `python tools\check_layout.py` passed.
- `python -m ruff check tools\parse_player_log.py tools\fit_shadow_allocation.py tools\summarize_experiment_corpus.py` passed.
- `python -m compileall tools` passed.
- `dotnet build TI_Missile_Fire_Control.sln` passed with 0 warnings and 0 errors.

## Outcomes / Retrospective

- The #44 slice is docs/tooling/fixture infrastructure only. No runtime combat code, allocator behavior, command application scope, projectile physics, or Terra Invicta integration changed.
- The fixture corpus summary separates fixture, shadow replay, and controlled-live run modes and produced no registry validation warnings.
