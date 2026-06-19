# Phase 01: Ready-shot source discovery

## Goal

Identify where ready, loaded, chambered, salvo, or per-weapon missile shot state is visible without changing combat behavior.

## Scope

- Inspect `MissileWeapon`, base `Weapon`, module data, weapon templates, and launcher/carrier state in the decompiled reference source.
- Compare candidate member names against the current extractor probes.
- Use existing logs to confirm that `remainingShots` is visible while `readyShots` is not.
- Decide whether the current projectile-state hook is sufficient or a live weapon observation point is required.

## Non-goals

- Do not add or change runtime code in this phase.
- Do not infer ready shots from `remainingShots`.
- Do not change hooks, launch behavior, target selection, ammo consumption, or allocation logic.

## Affected files

- `docs/plan/issue_11/01-discovery.md`
- `docs/battle-snapshot-extractor.md`
- Reference only: `../TI_RE_Workspace/**`

## Implementation steps

- Inspect `../TI_RE_Workspace` for `MissileWeapon`, `Weapon`, module magazine/ammo members, salvo counters, cooldown state, and reload/chamber fields.
- Record candidate member names and the object that owns them.
- Check whether the candidate object is visible from `TISpaceCombatProjectileState.Fire(missile)`.
- If not visible from the snapshot hook, identify the narrowest log-only source, likely `MissileWeapon.TryFire`.
- Update this phase's Decision log with the candidate source and why it is safe or insufficient.

## Acceptance criteria

- At least one candidate ready-shot source is documented, or a clear reason is recorded that no source is visible from current hooks.
- The plan states whether Phase 2 can stay inside the snapshot extractor or needs a separate live weapon diagnostic path.
- No production code is changed in this phase.

## Discovery findings

### Current snapshot extractor limitation

`CombatSnapshotExtractor.FromProjectileMissileFire(...)` receives the projectile
state hook arguments: launcher/carrier, missile template, launch time, origin
position, expected target position, and origin velocity. It does not receive the
live `MissileWeapon` instance or the `ModuleDataEntry` that identifies the firing
weapon slot.

The current extractor probes `weapon`, launcher, and missile template aliases
for `readyShots` and `remainingShots`. Source discovery shows this is not enough
to recover per-weapon ready/loaded/chambered state:

- the projectile-state hook has no live weapon object;
- `ModuleDataEntry` is an identity object with `moduleTemplateName`,
  `slotIndex`, and `weaponTemplate`, not ammo state;
- `TISpaceShipState.ammo` is keyed by `ModuleDataEntry`, so the current snapshot
  path cannot safely read the value for the firing weapon without the module key;
- reading a collection-like `ammo` member without a module key risks counting
  dictionary entries rather than shots.

### Candidate source table

| Candidate | Owner type | Member / access path | Observation point | Timing | Classification | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| Ship ammo dictionary value | `TISpaceShipState` | `ammo[weaponData]` | Live weapon path via `MissileWeapon.TryFire` (`weapon.combatant.WeaponCarrierState` + `weapon.weaponData`) or `TISpaceShipState.FireWeapon(module, targetedProjectile)` | Existing postfixes observe after `FireWeapon` has decremented ammo; a prefix would be needed for pre-fire value | `postFireRemaining` in postfix; `preFireRemaining` only from prefix/pre-decrement observation | High for remaining ammo, low for ready/loaded semantics |
| Weapon fire gate | `TISpaceShipState` / `CombatWeaponCarrierState` | `WeaponHasAmmo(module)`, `WeaponCanFire(module)` | Live weapon path before or during `TryFireCommon` | `TryFireCommon` checks this before launch; existing `TryFire` postfix is after launch | `canFire` / ammo-positive gate, not shot count | High as readiness gate, not count |
| Live weapon cooldown state | `Weapon` / `MissileWeapon` | `OnCooldown(currentTime)`, `lastFiredAt`, `currentCooldownDuration_s` | Live weapon path around `MissileWeapon.TryFire` | `TryFireCommon` requires not on cooldown; `EnterCooldown()` runs before `TryFire` postfix returns | `cooldown` / availability gate, not shot count | Medium; private fields need reflection if logged directly |
| Salvo progress | `Weapon` | `shotsFiredThisSalvo`, `weaponTemplate.salvo_shots`, `weaponTemplate.intraSalvoCooldown_s` | Live weapon path around `MissileWeapon.TryFire` | `EnterCooldown()` increments `shotsFiredThisSalvo` after projectile creation | `salvo` progress, not ready count | Medium; useful evidence for salvo behavior only |
| Salvo fire-mode counters | `SalvoFireMode` | `_totalSalvo`, `_shotsFired` | `currentFireMode` when it is `SalvoFireMode` | Updated by `ShipWeaponFired` event after firing | `salvo` command progress, not ammo readiness | Low to medium; private and only active in salvo mode |
| Template magazine capacity | `TIProjectileWeaponTemplate` / `TIMissileTemplate` | `magazine`, `FullAmmoCount_Current(ship)`, `FullAmmoCount_Max(template)` | Snapshot or live weapon path | Static/current capacity, not consumed count | `magazine-like` / capacity | High for capacity, not remaining or ready |
| Out-of-ammo event | `ShipWeaponOutOfAmmo` | `shipState`, `weaponData` | Event listener or `FireWeapon` path | Triggered when `ChangeAmmoValue` reaches zero after firing | zero-ammo transition | High for empty state only |

### Timing evidence

`MissileWeapon.TryFire(currentTime)` calls `TryFireCommon(currentTime)`, creates
the projectile, calls the projectile-state `Fire(...)`, fires the Unity
projectile controller, calls `EnterCooldown()`, and then calls
`WeaponCarrierState.FireWeapon(weaponData, ref_projectile)`.

`TISpaceShipState.FireWeapon(module, targetedProjectile)` calls
`ChangeAmmoValue(module, -1)` when the weapon has a magazine, then triggers
`ShipWeaponFired`. Therefore current postfix hooks on `MissileWeapon.TryFire` or
`TISpaceShipState.FireWeapon` can document post-fire remaining ammo, but should
not call that value `readyShots`.

### Phase 02 recommendation

Phase 02 should not try to solve this inside
`CombatSnapshotExtractor` / `SnapshotLog` alone. The snapshot hook lacks the
firing `ModuleDataEntry`, so it cannot reliably index `TISpaceShipState.ammo`.

Use a separate live weapon diagnostic path around `MissileWeapon.TryFire` and/or
`TISpaceShipState.FireWeapon`:

- log `postFireRemaining` from `TISpaceShipState.ammo[weaponData]` after a
  successful fire;
- log capacity evidence from `weaponTemplate.ref_projectileWeapon`:
  `FullAmmoCount_Current(ship)` and `FullAmmoCount_Max(ship.template)`;
- optionally log `WeaponCanFire`, `WeaponHasAmmo`, cooldown, and salvo evidence
  as separate fields, not as `readyShots`;
- only populate `SnapshotLog readyShots` later if a documented pre-fire
  ready/loaded/chambered source is found.

If Phase 02 needs a pre-fire count, it should use a log-only prefix or paired
pre/post observation around the live weapon path. A postfix-only value should be
named `postFireRemaining` or similar.

## Validation commands

- dotnet build TI_Missile_Fire_Control.sln
- python tools/check_layout.py
- python -m ruff check tools/check_layout.py tools/package_local.py tools/parse_player_log.py
- python -m compileall tools
- .\build.ps1
- python tools/parse_player_log.py --require-launchlogs --require-snapshots

## Manual smoke tests

- Not required for read-only discovery.

## Rollback risks

- None for read-only discovery. Incorrect conclusions are the main risk; mitigate by citing concrete source members and validating with runtime logs in later phases.

## Progress

- Completed source discovery.

## Decision log

- Initial evidence: current logs show `readyShots=unknown` for all snapshots while `remainingShots` is visible, so ready-shot work should focus on live weapon/module state rather than projectile-state-only inference.
- `TISpaceShipState.ammo[weaponData]` is the strongest candidate for remaining missile ammo, but the existing projectile snapshot hook lacks `weaponData`.
- Current postfix timing observes after ammo decrement, so ammo values from existing fire hooks must be treated as post-fire remaining ammo unless Phase 02 adds a pre-fire observation.
- No reliable ready/loaded/chambered count was found in the projectile-state snapshot path.

## Outcomes / Retrospective

- Phase 01 found candidate ammo, cooldown, and salvo state sources, but no evidence-backed ready/loaded/chambered count visible from the current snapshot hook. Phase 02 should add compact live weapon diagnostics before deciding whether any value can become `readyShots`.
