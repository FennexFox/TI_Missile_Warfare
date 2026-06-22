# Issue #38 context

This is local context for Codex planning, not a phased implementation plan.

## Role in #6

Issue #38 expands the first live controlled apply from one selected ship to a small explicitly selected player missile group, such as two or three ships. It should remain one-shot, bounded, and report-focused.

This slice should assume #37 already proved the minimal single-ship path with manual control preserved and no unselected/AI ship effects.

## Planning information for Codex

The plan should preserve the same safety model as #37 while adding group-level reporting. Important context includes selected player ship set, per-ship command intent/result, conservative per-trigger and per-ship caps, visible pre/post state, missiles assigned/spent when available, and explicit mismatch reporting.

Observed mismatches are evidence, not automatic bugs and not automatic tuning instructions. Heuristic changes belong to #39 unless the change is only report formatting.

## Report emphasis

The report should summarize applied/skipped/failed counts by experiment and by ship where visible. It should summarize missiles assigned/spent when visible, and it should record mismatch evidence instead of silently ignoring it.

## Boundary

Do not enable continuous automation. Do not command unselected player ships or AI ships. Do not alter projectile physics, missile guidance, cooldowns, or ammo accounting. Do not tune heuristic parameters here.
