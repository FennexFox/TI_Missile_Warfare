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

Only after recommendation quality is acceptable:

- Add a player-triggered button or hotkey.
- Apply target assignments to selected ships only.
- Keep an option to stay in recommendation-only mode.

## Phase 5: launch discipline

Add a conservative filter for bad launches:

- Too far relative to estimated WEZ.
- Target receding too quickly.
- Required package cannot be formed.
- Salvo would arrive too desynchronized.

Start with player-controlled launches. Patch AI behavior later, if at all.
