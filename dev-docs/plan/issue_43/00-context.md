# Issue #43 umbrella context — Fleet-wide controlled missile allocation path

Updated: 2026-06-23
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/00-context.md`

This directory is the umbrella planning context for Issue #43. It should not be used as a one-shot implementation work order. Use this file to understand the whole shape of #43, then hand Codex one numbered sub-slice context under this directory and let Codex produce the actual implementation plan/docs.

## Why this is an umbrella

Issue #43 is too broad to implement safely in one PR. It expands from selected-group controlled allocation to a fleet-wide controlled path, so each step must preserve the safety and evidence boundaries established by #37, #38, #39/#39.1, and #44.

The controlling rule is:

```text
Fleet-wide experiments may broaden the eligible player-controlled launcher set, but they must not broaden evidence claims.
```

That means #43 may eventually command more than the currently selected 1-3 ships, but only after fleet-wide eligibility, exclusion reasons, caps, command results, direct spend evidence, spillover, and missing evidence are visible in reports and in the experiment corpus.

## Directory structure

```text
dev-docs/plan/issue_43/
  00-context.md             # this umbrella context
  00-master-plan.md         # phase index / handoff map, not an implementation plan
  43.1/
    00-context.md           # fleet-wide dry-run/report scaffold context
  43.2/
    00-context.md           # bounded default-off fleet-wide live apply context
  43.3/
    00-context.md           # corpus review and fitting/no-tuning handoff context
```

Do not add `01-implementation.md`, `02-verification.md`, or similar execution documents here unless the next worker explicitly chooses to create them. Codex should derive the concrete implementation instructions from the relevant `00-context.md` when it starts a slice.

## Roadmap position

Relevant order:

```text
#37 selected-single-ship controlled live apply
  -> #38 small selected-group controlled experiment
  -> #39 / #39.1 command-spend attribution and spillover diagnostics
  -> #44 experiment corpus and parameter ledger
  -> #43 fleet-wide controlled allocation umbrella
       -> #43.1 fleet-wide dry-run/report scaffold
       -> #43.2 bounded fleet-wide live apply
       -> #43.3 corpus review and fitting/no-tuning handoff
```

#43 should consume the #44 corpus layer. If a branch does not yet contain the #44 docs/tooling, do not begin #43 live work; either merge/rebase onto that work or limit the slice to planning only.

## Parent intent

Issue #43 answers:

```text
How do we safely expand from selected-group controlled allocation to fleet-wide controlled allocation?
```

It is not a broad autonomous tactical AI rewrite. It is a bounded, auditable experiment path for comparing allocator behavior across all eligible player-controlled missile ships in a battle.

## Phase summary

### #43.1 — Fleet-wide dry-run/report scaffold

Purpose: make fleet-wide scope visible before changing combat behavior.

This slice identifies eligible player-controlled friendly missile launchers, records excluded launchers with concrete reasons, builds candidate launcher-target command rows, applies cap logic in report-only form, and prepares corpus-ready fixture or shadow evidence.

No live fleet-wide command application belongs in #43.1.

Exit condition: a reviewer can inspect a report/corpus summary and answer which ships would be eligible, which were excluded, which hostile targets would receive candidates, which caps would block over-broad application, and which evidence gaps remain.

### #43.2 — Bounded default-off fleet-wide live apply

Purpose: enable the first behavior-changing fleet-wide controlled path only after #43.1 proves eligibility and reporting.

This slice may apply controlled commands to fleet-wide eligible player-controlled launchers, but only when explicitly player-triggered and explicitly enabled. It must preserve global, per-ship, per-target, and per-trigger caps; hostile-target gates; same-team safety failures; command-result ids; and parser/corpus evidence separation.

Exit condition: a bounded live run can be recorded as `fleet-wide-controlled` without confusing direct controlled spend with vanilla / none-correlated spillover.

### #43.3 — Corpus review and fitting/no-tuning handoff

Purpose: use the #44 corpus layer to evaluate fleet-wide evidence without overfitting one batch.

This slice should aggregate #43.1/#43.2 evidence by run mode, candidate id, parameter snapshot, scenario tags, direct command spend, spillover, missing evidence, and manual verdict. It may recommend one narrow next tuning or implementation issue, or explicitly decline tuning.

Exit condition: the corpus can explain whether #43 produced enough evidence for a narrow heuristic/rule change, or whether remaining blockers belong to outcome hooks (#47), vanilla salvo suppression / selected-ship distribution (#48), more controlled live runs, or no tuning.

## Global invariants

These apply to every #43 sub-slice:

- controlled command application remains disabled by default;
- behavior-changing apply requires an explicit player action and an explicit allow/apply setting;
- only player-controlled friendly missile ships may become live command candidates;
- AI, enemy, non-player, unknown-control, or ambiguous ownership ships must skip or fail closed;
- targets must be concrete hostile combat ships;
- same-team missile target snapshots remain parser failures or high-severity safety evidence;
- failed commands, scope violations, missing context, and safety-gate blocks must be counted and reported;
- every command candidate/result row must identify launcher, allocator launcher when different, target, experiment id, and result class;
- per-ship, per-target, per-trigger, and global command caps must exist before live fleet-wide apply;
- manual control should remain available after the bounded controlled attempt;
- no sub-slice may treat `DestroyShip` text as exact projectile, damage, or kill attribution.

## Evidence model to preserve

#43 must keep these channels separate:

```text
controlled command spend
vs.
vanilla / none-correlated spillover spend
```

Direct controlled spend requires command-result correlation. Rows with `controlledCommandCorrelation="none"` or `commandResultId="none"` are not controlled command spend, even if they occur near a controlled experiment.

Important inherited conclusions:

- direct command-spend correlation exists for selected-group controlled commands;
- skipped controlled rows must not inherit launch or outcome evidence from later target destruction;
- conservative `DestroyShip` lines are post-direct-launch outcome hints only;
- same-target duplicate controlled-command guards do not suppress vanilla launch behavior;
- selected-ship budget distribution and actual vanilla salvo suppression remain unresolved unless a later focused issue handles them.

A #43 report may show direct controlled spend and vanilla spillover side by side, but must never merge them into one causal success score.

## #44 corpus contract

#43 should emit or prepare corpus-ready evidence using `docs/diagnostics/experiment-corpus.md`.

Run-mode interpretation:

```text
fixture = schema/tooling proof only
shadow-replay = candidate filter and regression check
controlled-live = selected-scope causal command-behavior evidence
fleet-wide-controlled = #43+ expanded live evidence class
```

Use `fleet-wide-controlled` only for real bounded fleet-wide live evidence. Use `fixture` for synthetic tests and `shadow-replay` or report-only metadata for dry-run analysis.

A useful #43 corpus entry should include:

- `selectedMode`: `fleet-wide` in scenario metadata;
- heuristic candidate id and parameter snapshot hash;
- source artifact references without committing private raw logs by default;
- eligible launcher count and excluded launcher counts by reason;
- enemy target count and target classification summary;
- command candidate, applied, skipped, failed, blocked, and missing-evidence counts;
- direct command-spend counts by launcher and target when available;
- vanilla / none-correlated spillover counts when visible;
- manual verdict and evidence gaps.

Failed or evidence-limited runs are valid corpus entries. They should be just as visible as good runs.

## Global non-goals

Unless a later explicit issue narrows one of these, #43 does not:

- automate tactical combat or continuously fire missiles;
- command enemy, AI, non-player, or unknown-control ships;
- change projectile physics, missile guidance, weapon cooldowns, or ammo accounting;
- implement actual vanilla salvo suppression;
- implement selected-ship budget distribution;
- infer exact kill attribution from `DestroyShip` text;
- tune allocator parameters from shadow replay alone;
- collapse shadow replay, selected-scope controlled live, and fleet-wide controlled evidence into one proof score.

## Files to inspect first

Start each sub-slice with the subdirectory-specific context. The global list is:

- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/diagnostics/experiment-corpus.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_38/00-context.md`
- `dev-docs/plan/issue_39/01-no-tuning-decision.md`
- `dev-docs/plan/issue_39.1/00-context.md`
- `dev-docs/plan/issue_44/00-context.md`
- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`
- `tools/summarize_experiment_corpus.py`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`

## Handoff rule

Do not hand off `dev-docs/plan/issue_43/00-context.md` alone as a Codex implementation prompt. Hand off one sub-slice context instead:

- for first implementation, use `dev-docs/plan/issue_43/43.1/00-context.md`;
- for live behavior, use `dev-docs/plan/issue_43/43.2/00-context.md` only after #43.1 is complete;
- for fitting decisions, use `dev-docs/plan/issue_43/43.3/00-context.md` only after enough #43.1/#43.2 corpus evidence exists.

The first useful #43 milestone is not better combat performance. It is a report that makes this safe failure state visible:

```text
eligible fleet-wide launcher set
+ excluded launcher reasons
+ candidate commands
+ caps and safety blocks
+ direct vs none-correlated spend separation
+ corpus-ready summary
```
