# Reverse-engineering plan

## Goal

Find safe Terra Invicta combat entry points for diagnostics and later launch-control helpers.

## Search terms

Use dnSpy, ILSpy, or another .NET decompiler on:

```text
TerraInvicta_Data/Managed/Assembly-CSharp.dll
```

Suggested search terms:

```text
missile
projectile
launcher
weapon
salvo
target
combat
point defense
PD
range
fire
launch
ordnance
```

## Phase 0: identify objects

Find classes or structs representing:

- Tactical combat controller.
- Combat ship state.
- Ship weapon state.
- Missile or projectile templates.
- Active projectile instances.
- Manual target commands.
- Automatic weapon fire decisions.

Record candidate class/method names in `docs/research/reverse-engineering-notes.local.md` and do not commit machine-specific paths.

## Phase 1: log-only patches

Add Harmony postfixes/prefixes that log:

- Battle start/end.
- Ship list and weapon list.
- Missile launch event.
- Target ID/name.
- Launcher ID/name.
- Current distance.
- Launcher and target velocity.
- Missile type.
- Later: hit, PD kill, miss, or projectile expiration.

No gameplay behavior should change in this phase.

Current confirmed runtime hook findings are recorded in
[`diagnostics/hooks.md`](../diagnostics/hooks.md).

### Current readiness decision

Issue #17 resolved the shot-budget semantics to Path A. Source review confirms
that the vanilla missile fire path spends module-keyed
`TISpaceShipState.ammo[weaponData]` only after `TryFireCommon` passes cooldown,
target, `WeaponCanFire(weaponData)`, and on-target gates. See
[`readiness-semantics.md`](readiness-semantics.md).

The mod should call the derived value `ammoGateBudgetShots`. Do not introduce
`readyShots`, loaded, or chambered terminology unless a future source actually
exposes a distinct state.

Issue #21 verifies selected-player command scope for later dry-run command
intent logging. The selected command scope is the tactical command panel's
single selected ship or group-selected ship list, not the broader left-hand
player-side combatant list. Vanilla salvo target commands operate at
ship/all-salvo-capable-weapons granularity rather than one visible module. See
[`selected-command-scope.md`](selected-command-scope.md).

Future reverse-engineering should focus on:

- dry-run command-intent logging from the verified selected-player scope;
- target velocity and relative velocity sources;
- target point-defense weapon weights;
- projectile/controller guidance target identity;
- later live command safety around `SelectSalvoTargetCommand`,
  `FleetSelectSalvoTargetCommand`, `SetCombatPrimaryTargetAction`, and
  `SetWeaponModeAction`.

## Phase 2: snapshot extraction

Build adapter methods that convert game objects into Core snapshots:

```text
Combat ship object -> ShipSnapshot
Weapon object      -> WeaponSnapshot
Missile object     -> MissileProfile
Magazine state     -> MissileInventorySnapshot
```

Keep mapping tables close to the adapter. Do not put game-specific names in Core.

## Phase 3: recommendation-only output

Use Core to produce allocation recommendations and write them to logs or a debug UI.

Acceptance criteria:

- No actual launch commands are changed.
- Recommendation includes target, shots, PD score, kill package size, launch score, and rejection reason.
- Logs are compact enough to inspect after one battle.

## Phase 4: controlled command helper

Only after recommendation quality is acceptable and dry-run command-intent logs
confirm the verified selected-player scope:

- Add a player-triggered button or hotkey.
- Apply target assignments to selected ships only.
- Keep an option to stay in recommendation-only mode.

Do not start controlled allocation from a fictitious `readyShots` source. Use
explicit `ammoGateBudgetShots` evidence and let vanilla combat enforce the final
legal launch result while the mod logs command intent, skipped reasons, and
observed results.

## Phase 5: launch discipline

Add a conservative filter for bad launches:

- Too far relative to estimated WEZ.
- Target receding too quickly.
- Required package cannot be formed.
- Salvo would arrive too desynchronized.

Start with player-controlled launches. Patch AI behavior later, if at all.

## Issue #47 combat outcome hook issue

Issue #47 investigates combat outcome hooks for missile hit, intercept, damage,
and kill attribution. It is not an allocator tuning issue: #39 already has
direct command-spend evidence and conservative post-direct-launch `DestroyShip`
outcome hints. The outcome-hook work is a deeper measurement layer for later
outcome-aware fitting and fleet-wide evaluation.

The research question is whether Terra Invicta exposes stable managed-code hooks
for any of the following, in increasing precision:

- projectile expiration or removal;
- projectile miss / lost target;
- point-defense interception;
- projectile hit;
- damage packet application;
- target disabled/destroyed;
- destroy/disable cause attributable to projectile, launcher, or command
  context.

Any hook added under that issue must be diagnostics-only first and must not
change allocator heuristics, live command behavior, or command scope. Until a
stable hook is found, vanilla `DestroyShip` text remains a conservative outcome
hint only, not exact kill attribution.

Current source-reviewed #47 implementation adds default-off `[OutcomeLog]`
diagnostics for:

- `MissileController.ApplyDamage(DamageSource)`;
- `MissileController.Destruct(bool)`;
- `CombatShipController.ApplyDamage(DamageSource)`;
- `CombatShipController.TriggerShipDestruction(TIGameState, TIShipWeaponTemplate)`.

These hooks are deliberately concrete-class postfixes rather than broad
`IDamageable` interface patches. They can provide projectile lifecycle,
point-defense / missile-damage, ship-damage, and ship-destruction evidence, but
the current ship damage/destruction surfaces expose attacker and weapon fields
rather than a unique projectile id. Runtime confirmation remains required after
deploying the new build.
