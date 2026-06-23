# Issue #43 context — Fleet-wide controlled missile allocation path

Updated: 2026-06-23
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/00-context.md`

This is local context for Codex planning. It is not a phased implementation plan or a step-by-step work order. Codex should use this file, the linked durable docs, and the relevant GitHub issue body to produce a focused implementation plan for the next PR.

## Current status

Issue #43 is the planned fleet-wide expansion after the selected-scope controlled allocation and fitting-readiness work.

The relevant roadmap order is:

```text
#37 selected-single-ship controlled live apply
  -> #38 small selected-group controlled experiment
  -> #39 / #39.1 command-spend attribution and spillover diagnostics
  -> #44 experiment corpus and parameter ledger
  -> #43 fleet-wide controlled missile allocation path
```

#43 should start only after the #44 corpus layer is available to consume or after an equivalent local branch includes that infrastructure. The first #43 slice should be report/corpus-first and default-off. It should prove that fleet-wide eligibility, command intent, command result, direct spend evidence, and failure cases can be recorded without losing the safety invariants established by #37/#38.

## Parent intent

Issue #43 answers:

```text
How do we safely expand from selected-group controlled allocation to fleet-wide controlled allocation?
```

It should not be treated as a broad autonomous missile-fire rewrite. The purpose is to create a bounded, auditable fleet-wide controlled experiment path that can eventually compare allocator behavior across all eligible player-controlled missile ships in a battle.

The controlling principle is:

```text
Fleet-wide experiments may broaden the eligible player-controlled launcher set, but they must not broaden evidence claims.
```

In practice, this means #43 may eventually command more than the currently selected 1-3 ships, but only when eligibility is explicit, default-off, player-triggered, capped, logged, and corpus-recorded. Missing evidence must remain visible instead of being silently treated as success.

## Preconditions to preserve

#43 should consume the evidence and boundaries from nearby issues:

- #37 proved the first selected-single-ship behavior-changing command path with hostile-target gating and same-team safety checks.
- #38 proved a small selected player group with per-ship and per-trigger caps, selected-scope attribution, and fail-closed behavior for ambiguous scope.
- #39 proved direct command-result launch/spend correlation through `experimentId` and `commandResultId`, plus the `targetStateId` bridge for launch-side target identity.
- #39.1 clarified that same-target controlled-command caps only gate controlled command application/attribution; they do not suppress vanilla salvo launches.
- #44 adds the corpus and parameter-ledger layer that #43 should use for run provenance, mode separation, parameter snapshot identity, scenario metadata, and manual verdicts.

Do not reopen legacy assumptions such as a fictitious `readyShots` source. Use the documented `ammoGateBudgetShots` semantics and the existing direct command-spend diagnostics.

## Safety baseline from #37/#38

The following invariants should survive any #43 design:

- controlled command application remains disabled by default;
- behavior-changing apply requires an explicit player action and an explicit allow/apply setting;
- only player-controlled friendly missile ships may become live command candidates;
- AI, enemy, non-player, unknown-control, or ambiguous ownership ships must skip/fail closed;
- targets must be concrete hostile combat ships;
- same-team missile target snapshots remain parser failures or high-severity safety evidence;
- failed commands, scope violations, and safety-gate blocks must be counted and reported;
- every command candidate/result row must identify launcher, allocator launcher when different, target, experiment id, and result class;
- per-ship, per-target, per-trigger, and global command caps must exist before live fleet-wide apply;
- manual control should remain available after the bounded controlled attempt.

#43 may change the command scope from selected-group to fleet-wide player-controlled eligibility, but it must not drop the hostile-target gate, player-control gate, attribution fields, or caps.

## Evidence model from #39/#39.1

#43 must distinguish these channels:

```text
controlled command spend
vs.
vanilla / none-correlated spillover spend
```

Direct controlled spend requires command-result correlation. Rows with `controlledCommandCorrelation="none"` or `commandResultId="none"` are not controlled command spend, even if they occur near a controlled experiment.

Important existing conclusions:

- direct command-spend correlation is available for selected-group controlled commands;
- skipped controlled rows must not inherit launch or outcome evidence from later target destruction;
- conservative `DestroyShip` lines are post-direct-launch outcome hints only;
- `DestroyShip` text is not exact projectile, hit, damage, or kill attribution;
- same-target duplicate controlled-command guards do not suppress vanilla launch behavior;
- selected-ship budget distribution and actual vanilla salvo suppression remain unresolved.

A #43 report must therefore show direct controlled command spend and vanilla spillover separately. It should never use total nearby missile launches as if all of them were caused by controlled commands.

## #44 corpus handoff

#43 should write or prepare corpus-ready evidence using the #44 format.

Expected run-mode semantics:

```text
fleet-wide-controlled = future expanded live evidence class for #43+
controlled-live = selected-scope causal command-behavior evidence
shadow-replay = candidate filter and regression check
fixture = schema/tooling proof only
```

For #43, a useful corpus entry should include at least:

- `runMode`: `fleet-wide-controlled` for real bounded fleet-wide live evidence, or `fixture` for synthetic tests;
- `selectedMode`: `fleet-wide` in scenario metadata;
- heuristic candidate id and parameter snapshot hash;
- source artifact references without committing private raw logs by default;
- eligible launcher count and excluded launcher counts by reason;
- enemy target count and target classification summary;
- command candidate, applied, skipped, failed, blocked, and missing-evidence counts;
- direct command-spend counts by launcher and target when available;
- vanilla / none-correlated spillover counts when visible;
- manual verdict and evidence gaps.

#43 should be considered ready to proceed when a failed or evidence-limited fleet-wide run is just as visible in the corpus summary as a good run.

## Scope boundary

Allowed work for the first #43 slice:

- add fleet-wide dry-run/report scaffolding;
- identify all eligible player-controlled friendly missile launchers in the current battle context;
- report excluded launchers with concrete reasons;
- build fleet-wide command candidates without applying them by default;
- add or extend parser/fitting/corpus summaries for fleet-wide candidate/result rows;
- preserve direct command-spend attribution semantics when live apply is later enabled;
- add synthetic fixtures for fleet-wide dry-run and safety-blocked cases;
- consume #44 corpus summary conventions for `fleet-wide-controlled` evidence.

Behavior-changing live apply, if implemented in a later #43 slice, must remain:

- default-off;
- explicitly player-triggered;
- bounded by global, per-ship, per-target, and per-trigger caps;
- player-controlled friendly launcher only;
- hostile-target only;
- fully logged with applied/skipped/failed/safety-blocked rows;
- reversible by disabling the apply setting.

Non-goals for #43, unless a later explicit issue narrows one of them:

- do not automate tactical combat or continuously fire missiles;
- do not command enemy, AI, non-player, or unknown-control ships;
- do not change projectile physics, missile guidance, weapon cooldowns, or ammo accounting;
- do not implement actual vanilla salvo suppression without a separate design;
- do not implement selected-ship budget distribution unless the #43 issue body explicitly includes it;
- do not infer exact kill attribution from `DestroyShip` text;
- do not tune allocator parameters from shadow replay alone;
- do not collapse shadow replay, controlled-live, and fleet-wide-controlled evidence into one proof score.

## Recommended first implementation posture

The safest first #43 PR is:

```text
fleet-wide controlled dry-run/report scaffold
```

It should answer:

- Which friendly missile ships would be eligible fleet-wide?
- Which ships were excluded, and why?
- Which hostile targets would receive controlled command candidates?
- Which commands would be applied if live apply were enabled?
- What caps would block over-broad application?
- What evidence would be written to the #44 corpus?

It should not need to prove combat effectiveness. Its success condition is that fleet-wide scope is explicit, auditable, and fail-closed before any broad live command behavior is enabled.

A later behavior-changing #43 PR may enable bounded fleet-wide live apply only after the dry-run report demonstrates that eligibility and exclusion are correct and that parser/corpus output can expose failures.

## Report emphasis

A #43 report should include:

- fleet-wide experiment id / trigger id;
- battle-side fleet eligibility source and confidence;
- eligible launcher ids, names, teams, player-control evidence, and missile-readiness evidence;
- excluded launcher ids and concrete exclusion reasons;
- enemy target ids/names/teams and hostile-target confidence;
- command candidate rows by launcher and target;
- global/per-ship/per-target/per-trigger cap state;
- applied/skipped/failed/safety-blocked counts;
- direct command-spend evidence by launcher/target where available;
- none-correlated vanilla spillover by launcher/target where visible;
- missing evidence counts;
- conservative outcome hints only for rows with direct launch evidence;
- corpus-ready summary fields.

## Acceptance focus

The first #43 context is sufficient when the next worker can state all of the following:

- #43 is the fleet-wide expansion rung, not a general missile-fire rewrite.
- #43 should consume #44 corpus conventions before claiming fitting progress.
- #37/#38 safety gates must survive fleet-wide expansion.
- #39 direct command-spend attribution must remain the standard for causal spend evidence.
- #39.1 spillover distinctions must be preserved.
- Fleet-wide dry-run/reporting should come before broad live apply.
- Actual vanilla salvo suppression, selected-ship budget distribution, and exact kill attribution remain separate unresolved problems.

## Files to inspect first

Start with:

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

## Likely validation commands

Baseline static validation:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\parse_player_log.py tools\fit_shadow_allocation.py tools\summarize_experiment_corpus.py
python -m compileall tools
```

If #43 adds fixtures, add fixture-specific parser/fitting/corpus commands. If #43 writes corpus-ready fixture entries, also run:

```powershell
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
```

## Handoff warning

#43 should not begin by asking whether the allocator is globally optimal. It should begin by proving that a fleet-wide experiment can safely fail.

The first useful milestone is a report that makes this visible:

```text
eligible fleet-wide launcher set
+ excluded launcher reasons
+ candidate commands
+ caps and safety blocks
+ direct vs none-correlated spend separation
+ corpus-ready summary
```

Only after that should #43 consider bounded live fleet-wide command application or any evidence-backed rule-family change.
