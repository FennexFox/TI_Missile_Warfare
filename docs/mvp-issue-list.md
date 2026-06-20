# MVP issue list

## Issue 1: Create UMM/Harmony scaffold

Goal: make the mod load without changing gameplay.

Acceptance criteria:

- UMM displays the mod.
- Settings panel opens.
- Diagnostic ping writes to the UMM log.
- No Harmony patches alter combat behavior.

## Issue 2: Identify combat launch entry points

Goal: locate methods involved in missile launch decisions.

Acceptance criteria:

- Candidate class/method list documented.
- At least one log-only patch fires during tactical combat.
- Log includes battle context and method name.

Current confirmed hook notes: `docs/confirmed-hooks.md`.

## Issue 3: Add battle snapshot extractor

Goal: convert game combat objects into Core snapshots.

Acceptance criteria:

- Friendly launchers and enemy targets are discoverable.
- Weapon roles are mapped with conservative defaults.
- Allocator-safe fireable shot evidence can be reported when proven.
- Snapshot dump can be enabled/disabled from settings.

Implementation notes: `docs/battle-snapshot-extractor.md`.

## Issue 4: Recommendation-only salvo allocation

Goal: produce target/shots recommendations without applying commands.

Acceptance criteria:

- Each recommendation includes target, assigned shots, PD score, kill package, launch score, and reason.
- Targets below launch threshold are rejected with a reason.
- The system avoids assigning below saturation package unless no better option exists and partial saturation is enabled.

## Issue 5: Add debug UI or hotkey

Goal: expose recommendations during combat.

Acceptance criteria:

- Player can trigger recommendation generation on demand.
- Output is readable in UMM log or an in-game panel.
- The UI clearly says recommendation-only.

## Issue 6: Controlled auto-allocation command

Goal: apply target assignments for selected friendly missile ships.

Prerequisite: Issue #15 showed live ammo/gate evidence in snapshot/allocation
diagnostics, but `readyShots` remains unresolved. Do not implement Issue 6 using
a numeric shot budget until `docs/readiness-semantics.md` resolves whether
`ammo[weaponData]` plus known fire gates is the game-equivalent shot budget,
whether a distinct fireable-shot source exists, or whether the controlled-
allocation design should avoid a fleet-level shot budget entirely.

Acceptance criteria:

- Selection scope is based on a verified player-selection or player-command hook; until then, command application remains disabled.
- Existing manual control remains possible after the selected-ship command path is verified.
- Recommendation-only mode prevents command changes.
- Failures are logged without breaking combat.

Readiness gate:

- Validate `ammo[weaponData]` plus known fire gates as the game-equivalent shot budget; or
- prove a distinct allocator-safe fireable-shot source; or
- document that no numeric source is needed and update the Issue 6 design to use weaker per-weapon gate/ammo evidence without calling it `readyShots`.

## Issue 7: Launch discipline prototype

Goal: prevent obviously wasteful launches.

Acceptance criteria:

- Launch window score is computed only from validated range and target/relative-velocity evidence; otherwise the score is marked provisional or unavailable.
- Conservative/balanced/aggressive thresholds are configurable after the scoring inputs are validated.
- Rejected launches are logged with reason, including missing-input reasons.
- Feature can be disabled independently from allocation.
