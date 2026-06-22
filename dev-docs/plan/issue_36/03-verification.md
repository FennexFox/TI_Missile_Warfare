# Phase 03: Documentation and validation

## Goal

- Update durable docs and validate the additive schema.

## Scope

- Document the #36 gate and parser fields.
- Run layout, Python lint, Python compile, fixture parser smoke, fitting fixture smoke, and build when available.
- Record validation outcomes and runtime smoke limitations.

## Non-goals

- No private runtime logs committed.
- No requirement to produce a fresh runtime eligible candidate if local game smoke is unavailable.

## Affected files

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_36/*`

## Implementation steps

- Update docs with `AllowCommandApply`, `dryRunApplyGate`, safety-gate blocked parser fields, and fixture expectations.
- Run validation commands.
- Update phase progress/outcomes with exact results.

## Acceptance criteria

- Docs state #36 is still diagnostics-only and #37 is first live apply.
- Validation confirms parser sees one blocked safety-gate fixture and zero applied commands.

## Validation commands

- python tools\check_layout.py
- python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
- python -m compileall tools
- python tools\parse_player_log.py tools\fixtures\apply_gate_hard_stop.txt --require-launchlogs --require-snapshots

## Manual smoke tests

- If a fresh runtime smoke is available, run the issue #36 manual flow and parse the log. If unavailable, record that deterministic fixture coverage was used instead.

## Rollback risks

- Documentation must stay synchronized with parser schema to avoid future runtime smoke ambiguity.

## Progress

- Completed.

## Decision log

- Deterministic fixture validation is the committed #36 proof for the gate-reachable path because no fresh runtime smoke was run in this environment.

## Outcomes / Retrospective

- Updated durable diagnostics and roadmap docs for `AllowCommandApply`, `dryRunApplyGate`, `safetyGateBlockedCommands`, and the #36 fixture.
- `python tools\check_layout.py`: passed.
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`: passed.
- `python -m compileall tools`: passed.
- `python tools\parse_player_log.py tools\fixtures\apply_gate_hard_stop.txt --require-launchlogs --require-snapshots`: passed; reported one `dryRunApplyGate`, one `blockedBySafetyToggle`, and zero applied commands.
- Existing controlled dry-run and command-resolvability fixtures still parse OK.
- `python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_36_fixtures`: passed; readiness remains `Not ready` because fixtures are synthetic and no real selected combat log was analyzed.
- `dotnet build TI_Missile_Fire_Control.sln`: passed with 0 warnings and 0 errors.
- Manual runtime smoke was not run; next runtime validation should leave command application disabled and confirm zero applied commands in a fresh player log.
