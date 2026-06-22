# Issue #38 context

This is local context for Codex planning, not a phased implementation plan.

## Current branch state

Current branch: `issue_38`.

Issue #38 starts after the #37 selected-single-ship safety rung has been merged into `issue_6`. The #38 branch should be reviewed as a separate expansion rung on top of that baseline.

Preferred branch/review expectation:

- Keep the #38 PR diff focused on selected-group expansion only.
- If local branch history still contains pre-merge #37 commits, rebase or retarget so #37 changes do not obscure the #38 review.

## Role in #6

Issue #38 expands the first live controlled apply from one selected ship to a small explicitly selected player missile group, such as two or three ships. It should remain one-shot, bounded, and report-focused.

This slice should assume #37 already proved the minimal single-ship path with manual control preserved, no unselected/AI ship effects, and no same-team missile target snapshots in the latest post-fix smoke.

#38 does not complete #6. It is the selected-group rung between #37 selected-single-ship apply and later #43 / #6 fleet-wide controlled allocation.

## #37 baseline to preserve

The post-fix #37 runtime smoke established the current safety baseline:

- enemy allocator / friendly-target candidates must skip or wait;
- selected command launcher and allocator launcher are distinct fields and must not be conflated;
- selected command launcher team and allocator launcher team must be known and equal before live apply;
- target team must be known and different from the selected command ship team;
- per-trigger live apply must remain bounded;
- failed commands, scope violations, same-team missile target snapshots, and parser suspicious patterns should remain zero in clean smoke logs.

Concrete #37 smoke example:

- enemy `Yayoi` team `50` allocator candidates targeting friendly team `47` skipped with `allocatorLauncherOutsideSelectedTeam`;
- selected `Cape St. George` team `47` targeting hostile `Taiho` team `50` applied once;
- parser verdict was `OK` with zero same-team missile target snapshots.

## Planning information for Codex

The plan should preserve the same safety model as #37 while adding group-level reporting. Important context includes selected player ship set, per-ship command intent/result, conservative per-trigger and per-ship caps, visible pre/post state, missiles assigned/spent when available, and explicit mismatch reporting.

Start #38 with selected-group dry-run/report scaffold before broadening live apply. The first useful implementation step is not “apply to several ships”; it is proving that the selected command group is exactly the intended player-controlled 2-3 ship set and that every candidate/result row is attributable to one selected ship.

Suggested implementation order:

1. Report selected command group identity and size.
2. Fail closed or skip when selected group scope is unavailable, empty, too broad, mixed-team, or includes non-player/AI ships.
3. Emit per-ship command candidate rows under one group experiment id.
4. Add explicit per-trigger and per-ship caps before any group live apply.
5. Keep dry-run/reporting mode useful even when live apply is disabled.
6. Only then allow bounded live apply for compatible selected player ships.
7. Parse fresh runtime logs and record applied/skipped/failed counts by experiment and by ship.

Observed mismatches are evidence, not automatic bugs and not automatic tuning instructions. Heuristic changes belong to #39 unless the change is only report formatting.

## Report emphasis

The report should summarize applied/skipped/failed counts by experiment and by ship where visible. It should summarize missiles assigned/spent when visible, and it should record mismatch evidence instead of silently ignoring it.

Recommended #38 report fields or summaries:

- group experiment id / trigger id;
- selected group size and selected ship ids/names/teams;
- selected-scope source and confidence;
- per-ship allocator launcher id/team;
- per-ship target id/name/team;
- candidate classification and skip reason;
- gate result;
- live apply result when enabled;
- failed command reason when present;
- scope violation count;
- same-team missile target snapshot count;
- missiles assigned/spent or visible launch/ammo delta when available.

## Acceptance focus

A clean #38 smoke should show:

- selected group scope is explicit and auditable;
- only selected player missile ships are eligible;
- unselected player ships and AI/enemy ships are not commanded;
- every live command attempt maps to one selected group member;
- per-trigger and per-ship command caps are respected;
- skipped and failed ships remain visible in parser output;
- manual control remains available after the bounded command attempt;
- parser verdict remains `OK` for a clean smoke log.

## Boundary

Do not enable continuous automation. Do not command unselected player ships or AI ships. Do not alter projectile physics, missile guidance, cooldowns, or ammo accounting. Do not tune heuristic parameters here.
