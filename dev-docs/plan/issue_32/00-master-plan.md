# Classify intermittent missing targetIdentity no-op evidence before #6

## Issue Target And Scope Summary

- Issue target: #32
- Title: Classify intermittent missing targetIdentity no-op evidence before #6
- Scope: classify the 54 `Player-prev.log` no-op rows from Issue #30 that lacked launcher-selected `targetIdentity`, update fitting output so this case is distinct from parser failure and allocation ambiguity, document the #6 readiness impact, and close the issue.

## Strategy

Treat absent launcher-selected target identity as a command-safety no-op when the record is already a no-op and the only hard missing allocation input is `targetIdentity`. This is safe skip evidence: the shadow allocator did not infer a target and did not allocate shots. It is not allocation-quality evidence, and it is not proof that vanilla combat had no live missile target.

## Phase Order

1. [Classify targetIdentity-missing no-op semantics](01-classification.md)
2. [Document readiness impact and close issue](02-documentation.md)

## Phase Dependencies

- Phase 1 has no dependency beyond Issue #32 context and the Issue #30 artifact logs.
- Phase 2 depends on the fitting wrapper producing the new classification and validation passing.

## Source Of Truth Decisions

- `tools/fit_shadow_allocation.py` is the source of truth for fitting classifications.
- `docs/diagnostics/snapshot-and-allocation.md` is the source of truth for diagnostic schema semantics.
- `docs/diagnostics/runtime-validation-history.md` records the four-log sweep result after classification.
- `docs/planning/mvp-roadmap.md` records remaining #6 gates.
- Decompiled Terra Invicta source under `../TI_RE_Workspace/decompiled_source` confirms that `combatPrimaryTarget` is a player/launcher-selected target path, while `MissileWeapon.TryFire` also carries a live `base.target`.

## Global Validation Expectations

- `python tools\fit_shadow_allocation.py --input artifacts\combat-logs\issue_30_four_logs --output artifacts\shadow-fitting\issue_32_classification`
- `python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_32_synthetic`
- `python -m compileall tools`
- `python -m ruff check tools\fit_shadow_allocation.py`
- `python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_32`

## Known Risks And Assumptions

- The local four-log artifacts are ignored and should not be committed.
- `command-safety no-op` does not mean the mod can command targets live; #22/#23 remain required before controlled command application.
- This classification should not mask missing target identity on allocation or rejection rows; those remain evidence-limited.
