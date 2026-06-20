# Phase 01: Readiness decision, schema rename, and durable docs

## Goal

- Record the #17 Path A readiness decision and align code, parser, and durable
  docs with explicit ammo/gate budget terminology.

## Scope

- Choose Path A from `00-context.md`.
- Document the decompiled call path that validates `ammo[weaponData]` plus gates.
- Rename Core/mod/parser schema fields from ready-shot terminology to
  `ammoGateBudgetShots` terminology.
- Populate `ammoGateBudgetShots` only from same-thread `MissileWeapon.TryFire`
  prefix evidence when module-keyed ammo and live gates are visible.
- Keep Issue #6 blocked on selected-player command scope and command safety.

## Non-goals

- Do not implement live command application.
- Do not claim a distinct loaded/chambered shot source exists.
- Do not infer ammo/gate budget from post-fire ammo, projectile remaining count,
  or capacity values.
- Do not require backwards compatibility for old unpublished log keys.

## Affected files

- `src/MissileFireControl.Core/**`
- `src/MissileFireControl.Mod/**`
- `tools/parse_player_log.py`
- `docs/research/readiness-semantics.md`
- `docs/planning/mvp-roadmap.md`
- `docs/research/reverse-engineering-plan.md`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/hooks.md`
- `docs/README.md`
- `docs/maintenance/assumption-audit.md`
- `dev-docs/plan/issue_17/00-master-plan.md`
- `dev-docs/plan/issue_17/01-decision.md`

## Implementation steps

- Review decompiled `MissileWeapon`, base `Weapon`, `TISpaceShipState`,
  `SalvoFireMode`, UI ammo, and salvo-target command path.
- Record Path A with validity constraints in `readiness-semantics.md`.
- Rename model/log/parser fields to `ammoGateBudgetShots` and related
  ammo/gate budget names.
- Derive budget only when `preFireRemaining`, `WeaponHasAmmo=True`,
  `WeaponCanFire=True`, and `OnCooldown=False` are observed for the live weapon.
- Update roadmap and diagnostics docs so #6 is blocked on command scope, not
  on finding a separate shot-budget source.

## Acceptance criteria

- `readiness-semantics.md` chooses Path A and cites the exact source path.
- Code no longer exposes `ReadyShots`/`TotalReadyShots` model properties.
- Snapshot/allocation log schema uses `ammoGateBudgetShots`.
- Parser consumes the renamed schema.
- #6 remains blocked until selected-player command scope is verified.

## Validation commands

- `dotnet build TI_Missile_Fire_Control.sln`
- `python -m py_compile tools\parse_player_log.py`
- `rg -n "ReadyShots|readyShots|TotalReadyShots|readyShot|ready-shot|ready shots" src tools docs dev-docs`

## Manual smoke tests

- Runtime smoke is still required after deployment if the new schema is used to
  validate live logs. This phase is source/docs/static-validation only.

## Rollback risks

- Reverting this phase would reopen the #17 decision gate and restore ambiguous
  ready-shot terminology.

## Progress

- Completed decompiled source review.
- Implemented schema rename in Core, Mod diagnostics, and parser.
- Updated durable docs to Path A.

## Decision log

- Path A selected. Decompiled source shows `MissileWeapon.TryFire` delegates to
  `TryFireCommon`, which gates cooldown, target, `WeaponCanFire(weaponData)`,
  and on-target state before `FireWeapon(weaponData, ...)` decrements
  `TISpaceShipState.ammo[weaponData]`.
- No distinct loaded/chambered shot source was found.
- The derived value is named `ammoGateBudgetShots` and is valid only with paired
  module-keyed ammo and gate evidence.

## Outcomes / Retrospective

- Phase completed. Final validation results are recorded in
  [`02-verification.md`](02-verification.md).
