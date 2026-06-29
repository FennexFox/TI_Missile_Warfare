# Issue #43.2 context — RE-gated bounded live apply before fitting authority control

Updated: 2026-06-24
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.2/00-context.md`
Parent umbrella: `dev-docs/plan/issue_43/00-context.md`
Previous slice: `dev-docs/plan/issue_43/43.1/00-context.md`

This is context for the second #43 sub-slice. It is not an implementation plan. Codex should read this context only after #43.1 has produced and validated the fleet-wide report-only surface.

## Current state entering #43.2

#43.1 is no longer just planned context. It has produced a reviewable fleet-wide report-only diagnostic path.

Validated #43.1 outcomes now available to inherit:

- separate fleet-wide report-only setting/trigger;
- `scopeMode="fleetWideReportOnly"` rows;
- active player-side combatants treated as a fleet eligibility source, not selected scope;
- visible hostile combatants treated as target enumeration, not allocator-approved recommendations;
- eligible/excluded launcher rows;
- visible hostile target rows;
- launcher-target candidate rows;
- report-only global/per-ship/per-target/per-trigger cap state;
- missing allocator evidence rows;
- `appliedCommands="0"` invariant for all fleet-wide report-only rows;
- parser support in `tools/parse_player_log.py`;
- synthetic fixture and experiment corpus metadata under `tools/fixtures/`;
- runtime smoke evidence from `Player.log` showing the expected fleet-wide report-only row family;
- row ordering polish so the runtime report reads as experiment -> launchers -> targets -> candidates -> cap/result;
- build validation through `MissileFireControl.Core` and `MissileFireControl.Mod`.

Known validation commands that passed during #43.1 handoff:

```powershell
python tools\parse_player_log.py tools\fixtures\fleet_wide_report_only.txt
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
python -m compileall tools
dotnet build src\MissileFireControl.Core\MissileFireControl.Core.csproj
dotnet build src\MissileFireControl.Mod\MissileFireControl.Mod.csproj
```

## Purpose

#43.2 exists to decide whether the fleet-wide candidate surface from #43.1 can safely become a bounded live command path. It also needs to preserve a clean path toward fitting by making vanilla spillover explicit and by handing off command-authority work before fitting begins.

It should answer two questions in order:

```text
1. RE question: what exact Terra Invicta command path can safely issue a target/salvo command for a specific non-selected player-controlled launcher?
2. Live-apply question: once that path is known, can a small bounded subset of #43.1 eligible fleet-wide candidates receive real commands without losing safety gates, caps, attribution, or corpus evidence separation?
```

#43.2 must not begin from abstract fleet-wide ambition. It must inherit #43.1's concrete eligibility, exclusion, target, cap, candidate, and missing-evidence report surface.

Fitting-oriented principle: because the fitting phase is still pre-release experimentation, variable control is more important than end-user-friendly coexistence with vanilla combat behavior. #43.2 itself should not silently suppress vanilla behavior, but it should make clear that high-quality fitting should happen only after either vanilla missile behavior is authoritatively suppressed for the managed scope or remaining vanilla behavior is excluded/deweighted as confounded evidence.

## Required first step: RE spike

#43.2 is partly a reverse-engineering task. Report-only fleet enumeration is not enough to justify live command application.

Before enabling any fleet-wide live apply behavior, Codex must identify and document:

- the existing selected-single or selected-group live apply path;
- the internal method or API that actually applies a target/salvo command;
- whether the method accepts explicit launcher and target objects, or depends on current UI-selected ships;
- whether the method can be safely called for a non-selected but player-controlled launcher;
- whether invoking the method mutates UI selection, tactical command state, weapon grouping, salvo mode, or other persistent combat state;
- what success, no-op, blocked, and exception/failure cases look like;
- which concrete object identities are needed to correlate command results back to `experimentId` and candidate rows.

The RE spike may produce logging, docs, and parser fields without applying commands. If the command path cannot be proven safe, #43.2 should stop with an explicit blocker summary rather than forcing live apply.

Suggested split inside #43.2:

```text
43.2a — RE/probe slice
- inspect selected live command application path;
- identify explicit ship-target command API if it exists;
- add diagnostic logging for candidate command-path availability;
- avoid fleet-wide live behavior change unless the path is proven safe.

43.2b — bounded live apply slice
- add default-off explicit setting/trigger;
- apply only cap-passing candidates with allocator evidence;
- preserve all #43.1 report rows;
- add applied/skipped/failed/blocked command-result rows;
- produce corpus-ready fleet-wide-controlled evidence only from real bounded live runs.
```

## Boundary

#43.2 may introduce live fleet-wide command application only when all of these remain true:

- default-off;
- explicitly player-triggered;
- explicitly allowed by a live apply setting distinct from #43.1 report-only diagnostics;
- limited to player-controlled friendly missile launchers;
- limited to concrete hostile combat ship targets;
- limited to #43.1 candidates with current allocator snapshot evidence;
- missing allocator evidence candidates are never applied;
- same-team, ambiguous-team, unknown-control, non-combat, and non-player candidates are never applied;
- bounded by global, per-ship, per-target, and per-trigger caps;
- logged with command candidate, applied, skipped, failed, blocked, and missing-evidence rows;
- parser-visible through `experimentId` and `commandResultId` or equivalent direct correlation ids;
- corpus-ready as `runMode = fleet-wide-controlled` only for real bounded live evidence.

#43.2 must preserve manual control after the bounded controlled attempt. It must not silently leave the UI or combat command state in a surprising mode.

## Live apply eligibility rule

A fleet-wide candidate may be considered for live apply only if all conditions are true:

```text
scopeMode is a #43.2 live/bounded mode, not fleetWideReportOnly
launcher is player-controlled and friendly
launcher has visible missile readiness / command authority evidence
target is concrete hostile combat ship
target is not same-team, neutral, unknown-team, or ambiguous
candidate has current allocator snapshot evidence
candidate passes report/live caps
command path RE gate is satisfied
explicit live apply trigger is armed
```

A visible hostile target discovered only through fleet-wide target enumeration is reportable, but not live-applicable unless current allocator evidence also ties it to the launcher-target candidate.

## Expected effect

The intended user-visible benefit is narrow but important:

- reduce the selected-scope limitation where only selected ships receive controlled missile commands;
- allow a small bounded batch of non-selected friendly missile launchers to follow allocator-backed target choices;
- make idle fleet-wide missile launchers visible and, where safe, usable;
- preserve a direct comparison between #43.1 report-only candidates and #43.2 applied/skipped results;
- create trustworthy evidence for later tuning without claiming broad tactical automation.

The expected effect is not better scoring by itself. #43.2 changes command reach, not allocator intelligence.

## Pre-fitting vanilla suppression policy

For end-user-facing assistive modes, preserving vanilla behavior may be desirable. For fitting, however, uncontrolled vanilla missile behavior is a confounder.

The preferred path before serious fitting is:

```text
1. prove bounded fleet-wide live apply can issue correlated commands;
2. introduce an experimental command-authority / vanilla-suppression mode for managed missile launchers;
3. collect fitting data with vanilla missile behavior suppressed inside the managed authority scope;
4. fit/tune allocator behavior against cleaner controlled evidence;
5. later decide, through command-authority policy, how much vanilla behavior can be safely re-enabled for user-facing modes.
```

This means vanilla spillover should not be treated as harmless background noise for fitting. It should be either removed by an explicit experimental suppression design or represented as a confounder that excludes or lowers the weight of that run.

The suppression design should be a separate focused issue because it changes combat authority more deeply than #43.2 bounded live apply. That issue should define an experimental authority mode first, not a polished end-user mode.

## Non-goals

#43.2 does not:

- continuously automate tactical combat;
- command enemy, AI, non-player, neutral, same-team, or unknown-control ships;
- apply commands to visible-only candidates lacking allocator snapshot evidence;
- broaden evidence claims beyond directly correlated command spend;
- implement broad vanilla salvo suppression inside #43.2 itself; a separate command-authority / experimental suppression issue should own that behavior before fitting;
- implement selected-ship budget distribution;
- infer exact kill attribution from `DestroyShip` text;
- tune allocator parameters from one live batch;
- collapse `controlled-live`, `fleet-wide-controlled`, `shadow-replay`, and `fixture` evidence into one proof score;
- treat active player-side combatants as selected scope.

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

remain vanilla / none-correlated spillover even if they happen near a fleet-wide controlled experiment. They may be logged as spillover or evidence-quality degradation, but they must not be used as controlled command-spend evidence for fitting unless a separate command-authority / suppression or correlation design proves causality.

For fitting, uncorrelated vanilla missile behavior should be treated as a confounder. Preferred fitting corpora should come from command-authority runs that suppress vanilla missile behavior for the managed launcher/weapon scope.

`DestroyShip` lines remain conservative outcome hints only after direct launch evidence. They are not exact projectile, hit, damage, or kill attribution.

#43.1 report-only rows must keep their existing meaning. `fleetWideReportOnly` rows must continue to imply no live fleet-wide command application and `appliedCommands="0"`.

## Failure should be visible

#43.2 should treat blocked or evidence-limited live attempts as valid evidence. The corpus should be able to preserve:

- RE blocked because no safe non-selected command path was found;
- command path requires UI-selected state and cannot be safely generalized yet;
- safety-blocked attempts;
- no-hostile-target attempts;
- cap-blocked attempts;
- missing allocator evidence candidates;
- failed command invocation with concrete exception/failure reason;
- command accepted but no direct command-result correlation found;
- direct controlled spend with later vanilla spillover;
- run marked fitting-confounded because vanilla missile behavior was not suppressed;
- direct spend without outcome evidence;
- same-team target safety failures.

A failed fleet-wide run is useful if it tells the next worker what must not be trusted yet.

## Suggested log/schema additions

Names can follow existing code style, but #43.2 should make these distinctions parser-visible:

- RE gate result, for example `fleetWideLiveCommandPathStatus`;
- live trigger id / experiment id;
- command candidate id reused from, or directly mappable to, #43.1 candidate rows;
- command apply decision, for example `fleetWideLiveApplyDecision`;
- skip/block reason vocabulary distinct from missing evidence;
- command result id when a real command was attempted;
- applied command count;
- cap state before application;
- cap state after application if it can differ;
- command correlation status.

The parser should be able to summarize:

- considered live candidates;
- applied live commands;
- skipped live candidates by reason;
- failed live command attempts by reason;
- cap-blocked candidates;
- missing allocator evidence candidates;
- commands lacking result correlation;
- none-correlated vanilla spillover near the experiment.

## Handoff condition to #43.3

Do not begin #43.3 until #43.2 has at least one of these:

1. at least one corpus-ready bounded live dataset with `runMode = fleet-wide-controlled`; or
2. an explicit RE blocker summary explaining why fleet-wide live apply remains unsafe or unproven.

Do not begin serious fitting until command authority has an explicit answer for vanilla missile behavior. The preferred pre-fitting answer is experimental suppression within the managed launcher/weapon scope, followed later by a policy decision about how much vanilla behavior to re-enable for user-facing modes.

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
- `docs/research/selected-command-scope.md`
- `docs/diagnostics/experiment-corpus.md`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/diagnostics/runtime-validation-history.md`
- `dev-docs/plan/issue_35/00-context.md`
- `dev-docs/plan/issue_37/00-context.md`
- `dev-docs/plan/issue_38/00-context.md`
- `dev-docs/plan/issue_39.1/00-context.md`
- `tools/parse_player_log.py`
- `tools/fit_shadow_allocation.py`
- `tools/summarize_experiment_corpus.py`
- `tools/fixtures/`
- `tools/fixtures/experiment_corpus/`
- `src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs`
- `src/MissileFireControl.Mod/Main.cs`
- `src/MissileFireControl.Mod/ModSettings.cs`
