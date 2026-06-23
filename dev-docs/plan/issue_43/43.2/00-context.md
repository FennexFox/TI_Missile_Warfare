# Issue #43.2 context — Bounded default-off fleet-wide live apply

Updated: 2026-06-23
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.2/00-context.md`
Parent umbrella: `dev-docs/plan/issue_43/00-context.md`
Previous slice: `dev-docs/plan/issue_43/43.1/00-context.md`

This is context for the second #43 sub-slice. It is not an implementation plan. Codex should read this context only after #43.1 has produced a reviewable dry-run/report surface.

## Purpose

#43.2 exists to enable the first bounded behavior-changing fleet-wide controlled allocation path.

It should answer:

```text
Can a fleet-wide eligible set of player-controlled friendly missile launchers receive bounded controlled commands without losing safety gates, caps, attribution, or corpus evidence separation?
```

#43.2 is not allowed to begin from abstract fleet-wide ambition. It must inherit #43.1's concrete eligibility, exclusion, target, cap, and missing-evidence report surface.

## Required prior state

Before #43.2 starts, #43.1 should already make these visible:

- eligible player-controlled friendly missile launcher set;
- excluded launchers grouped by reason;
- hostile target classification;
- same-team / ambiguous target safety evidence;
- candidate launcher-target rows;
- global, per-ship, per-target, and per-trigger cap state;
- corpus-ready dry-run or fixture summary;
- explicit evidence gaps.

If these are missing, stay in #43.1 instead of enabling live apply.

## Boundary

#43.2 may introduce live fleet-wide command application only when all of these remain true:

- default-off;
- explicitly player-triggered;
- explicitly allowed by a live apply setting;
- limited to player-controlled friendly missile launchers;
- limited to concrete hostile combat ship targets;
- bounded by global, per-ship, per-target, and per-trigger caps;
- logged with command candidate, applied, skipped, failed, blocked, and missing-evidence rows;
- parser-visible through `experimentId` and `commandResultId` or equivalent direct correlation ids;
- corpus-ready as `runMode = fleet-wide-controlled` only for real bounded live evidence.

#43.2 must preserve manual control after the bounded controlled attempt.

## Non-goals

#43.2 does not:

- continuously automate tactical combat;
- command enemy, AI, non-player, or unknown-control ships;
- broaden evidence claims beyond directly correlated command spend;
- suppress vanilla salvo launches unless a separate focused design explicitly owns that work;
- implement selected-ship budget distribution;
- infer exact kill attribution from `DestroyShip` text;
- tune allocator parameters from one live batch;
- collapse `controlled-live`, `fleet-wide-controlled`, `shadow-replay`, and `fixture` evidence into one proof score.

## Evidence meaning

A successful #43.2 live run can use:

```text
runMode = fleet-wide-controlled
selectedMode = fleet-wide
```

But only direct command-result-correlated launches count as controlled command spend.

Rows with:

```text
controlledCommandCorrelation="none"
commandResultId="none"
```

remain vanilla / none-correlated spillover even if they happen near a fleet-wide controlled experiment.

`DestroyShip` lines remain conservative outcome hints only after direct launch evidence. They are not exact projectile, hit, damage, or kill attribution.

## Failure should be visible

#43.2 should treat blocked or evidence-limited live attempts as valid evidence. The corpus should be able to preserve:

- safety-blocked attempts;
- no-hostile-target attempts;
- cap-blocked attempts;
- missing command-result correlation;
- direct controlled spend with later vanilla spillover;
- direct spend without outcome evidence;
- same-team target safety failures.

A failed fleet-wide run is useful if it tells the next worker what must not be trusted yet.

## Handoff condition to #43.3

Do not begin #43.3 until #43.2 has at least one corpus-ready live dataset or an explicit decision that live fleet-wide apply remains blocked.

#43.3 needs enough evidence to compare:

- dry-run candidate surface from #43.1;
- bounded live command results from #43.2 when available;
- direct controlled command spend;
- vanilla / none-correlated spillover;
- manual verdicts and evidence gaps.

If #43.2 cannot produce live evidence safely, #43.3 should receive a blocker summary rather than a tuning request.

## Files likely relevant to Codex

- `dev-docs/plan/issue_43/00-context.md`
- `dev-docs/plan/issue_43/43.1/00-context.md`
- `docs/diagnostics/experiment-corpus.md`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `dev-docs/plan/issue_39.1/00-context.md`
- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`
- `tools/summarize_experiment_corpus.py`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
