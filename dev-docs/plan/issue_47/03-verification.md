# Phase 03: Validation and closeout

## Goal

- Validate the diagnostics-only implementation statically and document the
  remaining runtime smoke gap.

## Scope

- Build, layout, Python compile, and parser smoke commands.
- Record commands actually run and any environment limitations.

## Non-goals

- Claiming in-game validation unless a fresh Terra Invicta runtime smoke is
  actually performed.

## Affected files

- Implementation files from Phase 02.
- Documentation and phase plan files.

## Implementation steps

- Run listed validation commands.
- Fix failures.
- Update plan progress and final notes.

## Acceptance criteria

- Static validation passes or any failure is explained with a concrete blocker.
- Runtime smoke gap is explicitly documented if not run.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools\check_layout.py
- python -m compileall tools
- python tools\parse_player_log.py --require-launchlogs

## Manual smoke tests

- Runtime smoke pending: the active `Player.log` was produced by an older build
  and correctly reports `OutcomeLog entries: 0`.

## Rollback risks

- Parser changes are additive for new `[OutcomeLog]` rows; if they regress old
  logs, revert parser summary additions.

## Progress

- Static validation completed. Runtime validation remains pending.

## Decision log

- Do not claim outcome hooks are runtime-confirmed until a fresh deployed build
  emits `patched=7`, `skipped=0` and nonzero `[OutcomeLog]` rows during combat.

## Outcomes / Retrospective

- `dotnet build TI_Missile_Fire_Control.sln`: passed.
- `python tools\check_layout.py`: passed.
- `python -m compileall tools`: passed.
- `python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py`: passed.
- `python tools\parse_player_log.py tools\fixtures\outcome_hooks.txt --require-launchlogs`: passed with `patched=7`, `skipped=0`, and two outcome rows.
- `python tools\parse_player_log.py --require-launchlogs`: passed against the active older runtime log with `patched=3`, `skipped=0`, and `OutcomeLog entries: 0`.
