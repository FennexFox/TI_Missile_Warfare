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

## Issue 3: Add battle snapshot extractor

Goal: convert game combat objects into Core snapshots.

Acceptance criteria:

- Friendly launchers and enemy targets are discoverable.
- Weapon roles are mapped with conservative defaults.
- Ready missile shots can be counted.
- Snapshot dump can be enabled/disabled from settings.

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

Acceptance criteria:

- Only selected player ships are affected.
- Existing manual control remains possible.
- Recommendation-only mode prevents actual command changes.
- Failures are logged without breaking combat.

## Issue 7: Launch discipline prototype

Goal: prevent obviously wasteful launches.

Acceptance criteria:

- Launch window score is computed from range and relative velocity.
- Conservative/balanced/aggressive thresholds are configurable.
- Rejected launches are logged with reason.
- Feature can be disabled independently from allocation.
