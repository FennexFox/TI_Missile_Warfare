# Phase 02: Tooling, docs, and validation

## Goal

- Verify existing parser/fitting behavior handles observed-vs-default PD status
  and update docs with the Issue #27 implementation boundary.

## Scope

- Existing parser/fitting summaries that already count
  `pdWeightDefaulted=False` as observed evidence.
- Diagnostics documentation and roadmap status.
- Static build and tool validation.

## Non-goals

- No parser/fitter retuning unless runtime emits a new required schema field.
- No committed selected combat logs or generated fitting artifacts.
- No claim of runtime validation without a fresh local combat smoke.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_27/*.md`

## Implementation steps

- Confirm parser/fitter already summarize `pdWeightDefaulted` and PD evidence
  sources.
- Document `observedTargetWeaponTemplates` as an observed count-style PD
  capability source.
- Record the decompiled-source review basis without copying source.
- Update roadmap wording from source discovery to fresh runtime validation.
- Run validation commands.

## Acceptance criteria

- Docs distinguish code availability from fresh runtime smoke evidence.
- Static validation passes.
- Manual runtime smoke requirements are explicit.

## Validation commands

- `dotnet build TI_Missile_Fire_Control.sln`
- `python tools/check_layout.py`
- `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py tools/fit_shadow_allocation.py`
- `python -m compileall tools`

## Manual smoke tests

- `python tools/fit_shadow_allocation.py --input artifacts/combat-logs/selected --output artifacts/shadow-fitting/latest`
- `python tools/parse_player_log.py --require-launchlogs --require-snapshots`
- These are only meaningful after collecting a fresh local Player.log with the
  updated diagnostics enabled.

## Rollback risks

- Documentation can be reverted independently if runtime smoke shows the chosen
  target-template path is unavailable in practice.

## Progress

- Documentation updates completed.
- Static validation completed.
- Phase-plan helper validation was attempted, but the helper treats
  `00-context.md` as a phase file and has no exclude option.

## Decision log

- No parser/fitter schema change is required for the first Issue #27 slice
  because the existing tools already report PD observed/defaulted/unknown
  counts and evidence-source histograms.

## Outcomes / Retrospective

- `dotnet build TI_Missile_Fire_Control.sln`: passed.
- `python tools/check_layout.py`: passed.
- `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py tools/fit_shadow_allocation.py`: passed.
- `python -m compileall tools`: passed.
- `python tools/parse_player_log.py tools/fixtures/shadow_allocation_synthetic.txt --require-launchlogs --require-snapshots`: passed.
- `python tools/fit_shadow_allocation.py --input tools/fixtures --output artifacts/shadow-fitting/issue_27_synthetic`: passed; verdict remains `Not ready` because the fixture is synthetic.
- `phase_plan_helper.py validate --plan-dir dev-docs/plan/issue_27`: not
  applicable without moving or rewriting the user-provided `00-context.md`.
