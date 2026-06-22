# Issue #35 context

This is local context for Codex planning, not a phased implementation plan.

## Role in #6

Issue #35 builds on #34 by translating allocator intent into dry-run command-plan candidates and proving selected-scope safety. It should answer whether the launcher, weapon/module evidence, target, assigned shots, and selected-player scope are resolvable enough for a later controlled command attempt.

This is still a no-live-command slice.

## Context carried from earlier work

#34 should already provide experiment id, explicit dry-run trigger, selected player ship snapshot where visible, and parser grouping for controlled dry-run experiments.

#21 is the key safety reference: the selected scope comes from the tactical command panel single selected ship or group-selected ship list. The left-hand player-side combatant list is not selection. Vanilla salvo command granularity is ship-level and all salvo-capable weapons on the selected ship, not one visible missile module.

## Planning information for Codex

Codex should plan how command-plan candidates are represented without applying them. The result categories should remain conceptual and reportable: eligible, would-skip, or would-fail. Missing evidence should be named rather than collapsed into a generic failure.

Potential reason vocabulary from the issue body includes `outsideSelectedScope`, `nonPlayerOrAIControlled`, `missingLauncherIdentity`, `missingWeaponIdentity`, `missingTargetIdentity`, `insufficientAmmo`, `ambiguousCommandPath`, and `unsafeScope`. The exact final vocabulary can differ, but it should be stable enough for parser/report summaries and future comparison.

## Report emphasis

The report should make scope safety obvious. It should surface selected ship set evidence, eligible/skipped/failed candidate counts, and scope-violation counts. Validation logs should show zero scope violations and zero applied commands.

## Boundary

Do not trigger launches or target reassignment. Do not tune the allocator. Do not broaden beyond selected player ships to make a candidate resolvable.
