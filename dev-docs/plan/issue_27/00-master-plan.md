# Observed target PD evidence recovery

## Issue Target And Scope Summary

- Issue target: #27
- Title: Observed target PD evidence recovery
- Source context: `dev-docs/plan/issue_27/00-context.md`
- Scope: recover an observed, conservative target point-defense diagnostic
  signal so parser/fitting output can distinguish observed PD evidence from the
  explicit default model.

## Strategy

- Start from runtime source discovery, not parser tuning.
- Use the visible launcher-selected target object already captured by
  `CombatSnapshotExtractor`.
- Reflect target ship weapon-template evidence only; do not issue commands,
  change fire modes, change projectile behavior, or tune allocation behavior.
- Treat `TIShipWeaponTemplate.defenseMode` as the observed capability signal
  and keep fallback defaults when templates or defense-mode fields are missing.
- Let existing parser/fitting code consume `pdWeightDefaulted=False` as
  observed evidence without introducing new committed log fixtures.

## Phase Order

1. [Recover runtime target PD evidence](01-runtime-pd-evidence.md)
2. [Tooling, docs, and validation](02-tooling-docs-validation.md)

## Phase Dependencies

- Phase 1 depends on source review of Terra Invicta combat weapon-template and
  defensive-fire classes.
- Phase 2 depends on the runtime extractor emitting observed/defaulted PD
  status through the existing snapshot and allocation log fields.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation plan source of truth.
- `00-context.md` remains the authoritative issue context and non-goal list.
- Decompiled Terra Invicta source remains local reference only; no decompiled
  source is copied into this repo.
- The first recovered scalar `pdWeight` is an observed count-style capability
  signal, not a calibrated PD simulator.

## Global Validation Expectations

- `dotnet build TI_Missile_Fire_Control.sln`
- `python tools/check_layout.py`
- `python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py tools/fit_shadow_allocation.py`
- `python -m compileall tools`
- Runtime smoke remains manual because committed real Player.log fixtures are a
  non-goal.

## Known Risks And Assumptions

- The projectile-fire snapshot target is still launcher-selected target
  evidence, not direct in-flight missile-controller target evidence.
- Runtime target weapon-template visibility must be confirmed with a fresh
  local combat log.
- `defenseMode` recovers capability, not cooldown, target arc, magazine, or
  exact defensive-fire success probability.
