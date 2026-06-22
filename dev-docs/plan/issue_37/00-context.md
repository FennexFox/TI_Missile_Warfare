# Issue #37 context

This is local context for Codex planning, not a phased implementation plan.

## Role in #6

Issue #37 is the first behavior-changing controlled allocation slice. It should apply at most one resolved allocator command to one explicitly selected player-controlled missile ship, behind the full safety gate.

This slice should not be planned until #34-#36 have produced the dry-run envelope, selected-scope/resolvability report, and hard-stop safety-gate proof. It also depends on the separate live command safety evidence from #23 or an equivalent documented safety verdict.

## Planning information for Codex

The plan should be much narrower than a general allocator. The useful shape is a single selected eligible player missile ship, one resolved target, unambiguous command path, conservative shot/salvo cap, one command attempt per trigger, and complete logging of intent/result/pre-state/post-state where visible.

If any identity or safety evidence is ambiguous, the safe outcome is skip/fail with reason, not a broader command attempt.

## Report emphasis

The parser/report should link applied/skipped/failed command result back to experiment id and allocator decision id. The report should make it obvious that at most one live command attempt happened and that unselected/AI ships were unaffected.

## Boundary

Do not support multi-ship live allocation, retries, continuous automation, unselected player ships, AI ships, projectile physics, missile guidance, cooldowns, ammo mutation, or heuristic tuning in this slice.
