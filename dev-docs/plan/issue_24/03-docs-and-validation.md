# Phase 3: Durable docs and validation

## Goal

Document the selected-log fitting workflow and record the initial #24 readiness
rules for Issue #6.

## Scope

- Update durable diagnostics docs with the wrapper command.
- Update runtime validation history with the #24 log-only fitting verdict rules.
- Run validation commands that are possible without real local combat logs.

## Non-goals

- Do not claim full readiness from synthetic fixtures.
- Do not claim selected-log fitting is complete unless a real selected log was
  actually analyzed.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/planning/mvp-roadmap.md` if roadmap status needs a concise pointer.
- Phase plan files for progress notes.

## Implementation steps

- Document default input/output paths.
- Document wrapper command and report artifacts.
- Record that PD-default-only evidence supports at most conditional readiness.
- Record validation results.

## Acceptance criteria

- Durable docs distinguish synthetic smoke from selected-log fitting evidence.
- Docs preserve #6 safety gate language.
- Validation results are recorded in the final handoff.

## Validation commands

```powershell
python tools\check_layout.py
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py
python -m compileall tools
```

## Manual smoke tests

- Run wrapper against a synthetic fixture or selected local logs.

## Rollback risks

- Low; docs and isolated tooling only.

## Progress

- Completed.

## Decision log

- Durable docs should describe the wrapper and readiness rules without claiming
  a real selected-log fitting verdict from synthetic smoke.
- #6 remains blocked on safety gates and selected-log evidence; Issue #24 does
  not apply commands.

## Outcomes / Retrospective

- Updated diagnostics and roadmap docs with default paths, wrapper outputs,
  classification categories, and PD-default readiness limits.
- Focused validation passed for wrapper smoke, ruff, compileall, and layout.
