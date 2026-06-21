# Issue #24 master plan

## Scope summary

Issue #24 implements a log-only fitting pass for the shadow allocator. The goal
is to make selected tactical-combat logs reusable for offline review before
Issue #6 uses the allocator as a controlled live-experiment baseline.

This plan follows the context in `00-context.md` and the GitHub issue body.

## Hard boundaries

- Do not change live command paths, target assignment, fire modes, projectile
  behavior, AI behavior, or player-control state.
- Do not tune `SalvoAllocator` or scoring options in the first pass unless the
  selected-log report shows repeated, evidence-supported bad classifications.
- Keep real combat logs and generated fitting artifacts under ignored
  `artifacts/` paths.
- Do not treat synthetic fixtures as fitting evidence.

## Source-of-truth decisions

- Default selected-log input: `artifacts/combat-logs/selected/`.
- Default generated output: `artifacts/shadow-fitting/latest/`.
- Real selected combat logs are local and ignored.
- One valid selected combat log can support `Conditionally ready` for #6 when
  required evidence exists and no impossible or obviously unsafe allocation
  behavior appears.
- Full readiness requires more than one log or more varied combat scenarios.
- PD-default-only logs may support conditional readiness, but block full
  readiness.

## Phase order

1. Planning and boundaries.
2. Wrapper and fitting classification.
3. Durable docs and validation.

## Global validation

Run the relevant static and smoke commands after implementation:

```powershell
python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
python -m compileall tools
python tools\fit_shadow_allocation.py --input <fixture-or-selected-log-dir> --output artifacts\shadow-fitting\latest
```

Run the broader project validation when practical:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py
.\build.ps1
```

Runtime parser validation with `--require-launchlogs --require-snapshots`
requires a current local `Player.log` or selected log with diagnostics enabled.

## Risks and assumptions

- A small log set can overfit the readiness conclusion.
- PD default-model evidence can make PD-risk conclusions provisional.
- Parser aggregates may hide per-cycle detail unless the wrapper scans allocation
  rows directly.
- Generated artifacts should remain ignored and should not be committed.

