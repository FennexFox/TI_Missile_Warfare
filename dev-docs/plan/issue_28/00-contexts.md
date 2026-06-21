# Issue #28 contexts for Codex

This file is context for Codex before it plans or implements Issue #28. It is not a phase plan. Codex should use this as background, then inspect the repo and make its own implementation plan.

## Issue intent

Issue #28 should define evidence sufficiency gates before Issue #6 controlled allocation. The problem is not simply missing parser fields anymore. The project now has logs where parser validation is OK and allocator-critical `missingInputs` can be empty, but some evidence is still not strong enough for controlled command claims.

The gate must separate:

- evidence being present;
- evidence being allocator-consumable;
- evidence being sufficient for controlled command application;
- parser completeness;
- fitting baseline readiness;
- live command safety.

Do not collapse these into one readiness flag.

## Location of source and docs

Decompiled source of Terra Invicta is in `../TI_RE_Workspace`. Refer to `../TI_RE_Workspace/graphify-out/slices/missile-fire-control-master`to navigate the relevant missile fire control code. Do not include the decompiled source in the repo. It is only for local inspection.

## Important distinction

`Ready for #6 baseline` from `tools/fit_shadow_allocation.py` is a fitting-wrapper baseline verdict only. It means the current selected logs satisfy the fitting wrapper's conservative baseline rules. It does not mean Issue #6 live command application is safe or fully ready.

Similarly, an empty `missingInputs` field means the current allocation row had the required parser/allocator fields. It does not prove that every field has sufficient model fidelity for controlled command use.

## Current evidence state

The current relevant state is roughly:

- Issue #17 validates `ammoGateBudgetShots`: `TISpaceShipState.ammo[weaponData]` plus vanilla fire gates is the game-equivalent per-weapon ammo/gate budget. Do not use legacy `readyShots`, loaded, or chambered-shot wording unless a future source actually proves such a distinct state.
- Issue #21 verifies selected-player command scope for later work: use the tactical command panel's single selected ship or group-selected ship list. Do not use the broader left-hand player-side combatant list as selected scope.
- Issue #22 was closed as superseded by #4. The useful no-op, command-shaped dry-run/intent evidence is folded into observation-only shadow allocation logging. Do not treat #22 as a separate open blocker unless the repo has changed.
- Issue #23 is still the live command safety gate. Issue #28 must not implement live command application.
- Issue #24 added the log-only fitting wrapper.
- Issue #27 recovered observed target PD evidence from visible target weapon templates with `defenseMode=true`. This is currently emitted as `pdWeightEvidenceSource=observedTargetWeaponTemplates` and a count-style `pdWeight`.
- Issue #29 owns upgrading target PD evidence from presence/count-style evidence into a richer capability model. Issue #28 should classify current PD evidence honestly, not solve the whole PD model.
- Issue #30 ran the four-log pre-#6 sweep.
- Issue #32 classified target-identity-missing no-op rows as `command-safety no-op`, meaning no concrete launcher-selected priority target was visible and the allocator made no allocation. This is safe skip evidence, not allocation-quality evidence and not parser failure.

## Current #30/#32 fitting result to preserve

The Issue #30 sweep after Issue #32 classification found multiple real logs with parser OK, observed target PD evidence, no critical missing fields on allocation/rejection decisions, no severe fitting classifications, and a fitting verdict of `Ready for #6 baseline`.

Issue #28 should not weaken that useful fitting conclusion. It should add a higher-level sufficiency gate explaining what the conclusion does and does not prove.

A good end state can say all of these at once:

- parser verdict: OK;
- fitting baseline: Ready for #6 baseline;
- evidence sufficiency: baseline-ready with named limitations;
- controlled live command readiness: not ready until live safety and command-mapping gates pass.

## Current PD evidence limitation

The central Issue #28 example is point-defense evidence.

`observedTargetWeaponTemplates` currently proves the presence of target weapon templates whose `defenseMode` flag is visible. It does not yet prove calibrated vanilla defensive pressure. It does not necessarily include live cooldown/readiness, ammo, arc, range geometry, support behavior, or exact interception capability.

For Issue #28, classify this evidence as `presenceOnly` or at most `provisional` until Issue #29 enriches the model. Do not describe it as fully sufficient PD capability evidence.

If the source is `defaultModel` or `pdWeightDefaulted=True`, that should remain a named limitation whenever it affects allocation/rejection evidence.

## Suggested status vocabulary

Issue #28 asks for these statuses:

- `ready`
- `provisional`
- `presenceOnly`
- `defaulted`
- `unknown`
- `commandUnsafe`

Codex should decide how to represent these in code and reports after inspecting the current parser/fitting structures.

Expected rough interpretation:

- `ready`: source-labeled and sufficient for the scoped claim.
- `provisional`: usable for cautious baseline diagnostics, but limited.
- `presenceOnly`: proves existence, not capability magnitude or live state.
- `defaulted`: fallback/default model used instead of observed evidence.
- `unknown`: absent or not interpretable.
- `commandUnsafe`: unsafe for controlled command application even if parser/fitting is healthy.

## Inputs that Issue #28 should cover

At minimum, classify these inputs from the issue body:

- `ammoGateBudgetShots`
- target identity
- target velocity
- relative velocity
- missile profile data
- observed target PD evidence
- selected-player command scope
- vanilla command granularity
- dry-run command intent logging
- observed launch/ammo delta evidence

Pay special attention to vanilla command granularity: vanilla salvo target commands operate at ship level and affect all salvo-capable weapons on that ship. They are not a per-visible-missile-module command. Any allocator-to-command mapping that assumes per-module control should be treated as provisional or unsafe.

## Files Codex should inspect first

Start with these files before planning edits:

- `tools/fit_shadow_allocation.py`
- `tools/parse_player_log.py`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/planning/mvp-roadmap.md`
- `docs/research/readiness-semantics.md`
- `docs/research/selected-command-scope.md`
- `dev-docs/plan/issue_30/00-master-plan.md`
- `dev-docs/plan/issue_32/00-master-plan.md`
- `dev-docs/plan/issue_32/01-classification.md`
- `dev-docs/plan/issue_32/02-documentation.md`

Also inspect generated local artifacts only if needed. Real combat logs and generated fitting outputs under `artifacts/` are local evidence and should not be committed.

## Likely implementation direction, not a required plan

Prefer additive reporting over redefining existing parser verdicts. For example, keep parser `OK` and fitting classifications intact, then add an evidence-sufficiency section to JSON/report output that lists per-input statuses, limitations, and command blockers.

The implementation should make it impossible for docs or reports to imply full #6 controlled readiness solely because:

- parser verdict is OK;
- `missingInputs` is empty;
- fitting verdict says `Ready for #6 baseline`.

## Boundaries

Do not implement live command application in Issue #28.
Do not tune allocator scoring in Issue #28.
Do not claim a calibrated vanilla point-defense simulator.
Do not require raw real combat logs to be committed.
Do not delete or rewrite unrelated plan folders unless the user asks.

## Validation commands to consider

Use commands that match the current repo state, but these are known useful commands from nearby work:

```powershell
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_28_sufficiency
python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_28_synthetic
python -m compileall tools
python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_28
```

If an active runtime log is available, also consider:

```powershell
python tools\parse_player_log.py --require-launchlogs --require-snapshots
```

## Acceptance criteria reminders

Issue #28 is complete only if the output/docs can distinguish no missing parser fields from insufficient model fidelity. Observed target PD presence must be explicitly classified as provisional or presence-only until richer PD module/capability data exists. Roadmap wording should distinguish hard blockers, soft/provisional evidence limits, and live-command safety gates.
