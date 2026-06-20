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

Record candidate class/method names in `docs/reverse-engineering-notes.local.md` and do not commit machine-specific paths.

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
`docs/confirmed-hooks.md`.

### Current readiness blocker

Issue #15 confirmed that live `MissileWeapon.TryFire` ammo and gate/cooldown
evidence can be correlated into `SnapshotLog` and `AllocationLog`, but it did
not find a true ready, loaded, or chambered missile count. The active runtime
evidence is:

- `preFireRemaining` and `postFireRemaining` from
  `TISpaceShipState.ammo[weaponData]`;
- `WeaponHasAmmo`, `WeaponCanFire`, and `OnCooldown` gate state;
- `preFireRemaining - postFireRemaining = 1` on successful launches.

That evidence proves magazine/ammo visibility and current-fire gate state. It
does not prove allocator-safe numeric `readyShots`. Do not use ammo dictionary
or gate state as `readyShots` without a separately documented runtime source.

Before controlled allocation depends on shot budgets, add a focused
reverse-engineering pass to prove or disprove a true ready/loaded/chambered
source. Search likely areas:

- `MissileWeapon` and base `Weapon` fields/properties beyond the confirmed
  `TryFire` path;
- fire mode and salvo state classes;
- carrier weapon collections and module state;
- any loaded/chambered/queued ordnance structures;
- decompiled call sites around `TryFireCommon`, `WeaponCanFire`,
  `FireWeapon`, and `ChangeAmmoValue`.

If no true count exists, revise the controlled-allocation design so it does not
require numeric `readyShots`.

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

Only after recommendation quality is acceptable and readiness semantics are
resolved:

- Add a player-triggered button or hotkey.
- Apply target assignments to selected ships only.
- Keep an option to stay in recommendation-only mode.

Do not start controlled allocation from numeric `readyShots` until a true ready,
loaded, or chambered shot-count source is documented. If readiness remains
unknown, controlled allocation needs a different design that avoids pretending a
fleet-level ready-shot budget exists.

## Phase 5: launch discipline

Add a conservative filter for bad launches:

- Too far relative to estimated WEZ.
- Target receding too quickly.
- Required package cannot be formed.
- Salvo would arrive too desynchronized.

Start with player-controlled launches. Patch AI behavior later, if at all.
