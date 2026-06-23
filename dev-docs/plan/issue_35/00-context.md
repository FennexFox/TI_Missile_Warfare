# Issue #35 context

This is local context for Codex planning, not a phased implementation plan.

## Role in #6

Issue #35 builds on #34 by translating allocator intent into dry-run command-plan candidates and proving player-controlled command-scope safety. It should answer whether the launcher, weapon/module evidence, target, assigned shots, and an explicit audited player-controlled command scope are resolvable enough for a later controlled command attempt.

This is still a no-live-command slice.

## Context carried from earlier work

#34 provides experiment id, explicit dry-run trigger, selected player ship snapshot where visible, and parser grouping for controlled dry-run experiments. Runtime smoke validated the envelope with three experiments/intents/results and zero applied commands. In that runtime context, selected command-panel scope was unavailable (`selectedShipCount="0"`, `selectedScopeMissingReason="selectedScopeUnavailable"`), which is a safe #34 result and a #35 design input.

#21 remains a key safety reference: the tactical command panel single selected ship or group-selected ship list is a verified narrow scope source. The left-hand player-side combatant list is not selection. However, #35 should not require command-panel selection specifically. The required property is an explicit, auditable player-controlled command scope. Valid sources may include command-panel selection when visible, or verified current-combat active-player missile combatants if #35 proves that source is safe. Vanilla salvo command granularity is ship-level and all salvo-capable weapons on the scoped ship, not one visible missile module.

## Planning information for Codex

Codex should plan how command-plan candidates are represented without applying them. The result categories should remain conceptual and reportable: eligible, would-skip, or would-fail. Missing evidence should be named rather than collapsed into a generic failure. Do not implement these categories as part of the #34 closeout.

Potential reason vocabulary from the issue body includes `outsideSelectedScope`, `nonPlayerOrAIControlled`, `missingLauncherIdentity`, `missingWeaponIdentity`, `missingTargetIdentity`, `insufficientAmmo`, `ambiguousCommandPath`, and `unsafeScope`. The exact final vocabulary can differ, but it should be stable enough for parser/report summaries and future comparison.

## Report emphasis

The report should make scope safety obvious. It should surface the resolved player-controlled command scope source, scoped ship evidence, eligible/skipped/failed candidate counts, and scope-violation counts. Validation logs should show zero scope violations and zero applied commands.

## Boundary

Do not trigger launches or target reassignment. Do not tune the allocator. Do not treat unselected, AI-controlled, enemy, allied non-player, or broad side-list ships as eligible by accident. If no safe player-controlled command scope is available, command candidates must be skipped rather than broadened.
