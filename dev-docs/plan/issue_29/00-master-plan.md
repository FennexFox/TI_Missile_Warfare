# Point-defense capability evidence quality

## Issue Target And Scope Summary

- Issue target: #29
- Title: Point-defense capability evidence quality
- Scope: distinguish default PD evidence, defense-mode presence evidence, and source-backed static template capability evidence in runtime logs, parser output, fitting reports, and durable docs.

## Strategy

- Preserve legacy `pdWeight*` fields and their count-style semantics.
- Add additive PD capability fields from the current target weapon-template observation path.
- Treat visible template range/cooldown/ammo-capacity style fields as `observedTemplateCapability`, and expose the exact observed categories through `pdCapabilityObservedFields`.
- Keep live defensive readiness, ammo, arc coverage, and target/projectile geometry out of the quality claim until a future hook proves them.
- Keep future geometry-aware evidence provisional by default until a separate source-backed readiness gate and real-log validation justify a stronger status.
- Keep legacy logs parseable: missing new fields must not fail parser or fitting reports.

## Phase Order

1. [Add PD capability evidence fields](01-implementation.md)
2. [Parse and report PD capability quality](02-reporting.md)
3. [Document source-backed limits and validation](03-documentation.md)

## Phase Dependencies

- Phase 1 provides additive C# fields for snapshot and allocation logs.
- Phase 2 consumes those fields and preserves legacy `observedTargetWeaponTemplates` as `presenceOnly`.
- Phase 3 records the source-backed interpretation and validation results.

## Source Of Truth Decisions

- `dev-docs/plan/issue_29/00-master-plan.md` is the issue #29 implementation plan source of truth.
- `dev-docs/plan/issue_29/00-contexts.md` remains background context, not the phase plan.
- Decompiled Terra Invicta source under `../TI_RE_Workspace` is read-only reference material and is not copied into this repo.

## Global Validation Expectations

- `dotnet build TI_Missile_Fire_Control.sln`
- `python tools\check_layout.py`
- `python -m compileall tools`
- `python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py`
- `python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\issue_29_synthetic`
- `python C:\Users\techn\.codex\skills\phased-issue-implementation\scripts\phase_plan_helper.py validate --plan-dir dev-docs\plan\issue_29`

## Known Risks And Assumptions

- Current hook observes target templates, not live defensive weapon objects for target PD readiness.
- Static template capability is stronger than presence-only, but still provisional.
- Ammo-capacity-like template fields are not live ammo/readiness evidence.
- `geometryAwareCapability` is a reserved future label and must not imply `ready` by string alone.
- The allocator still consumes legacy `pdWeight`; issue #29 does not tune scoring.
- Fresh real runtime logs are needed before claiming real-log `observedTemplateCapability` coverage.
