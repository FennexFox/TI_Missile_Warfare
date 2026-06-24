# Issue #43.2b context — Bounded fleet-wide live apply after command-authority proof

Updated: 2026-06-24
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.2/03-bounded-fleet-wide-live-apply-context.md`
Parent context: `dev-docs/plan/issue_43/43.2/00-context.md`
Required predecessor: `dev-docs/plan/issue_43/43.2/02-command-authority-rung-context.md`

This context is for expanding from one proven non-selected command-authority probe to a small bounded fleet-wide live apply batch. Do not start this context until the command-authority rung has runtime evidence proving at least one safe non-selected player-controlled command invocation or a maintainer explicitly accepts the remaining evidence limitation.

## Required prior evidence

Before this slice starts, the repo should have:

```text
#43.1 fleet-wide report-only surface validated
#43.2 RE-blocked probe validated
one-command non-selected command-authority probe implemented
runtime smoke for exactly one non-selected command attempt
parser-visible commandResultId and result row
post-state review showing no unsafe selection/UI/targeting mutation
same-team target snapshots = 0
scope violations = 0
```

Preferred prior evidence also includes direct command-result launch/spend correlation:

```text
controlledCommandCorrelation="directRuntimeContext"
controlledCommandObservedSpentShots numeric
```

If direct correlation remains missing, this slice may still implement bounded apply behind default-off gates, but it must label resulting runs evidence-limited and must not use them as fitting-ready `fleet-wide-controlled` evidence.

## Purpose

This slice answers:

```text
Can the mod apply a very small bounded batch of allocator-evidence-backed commands across multiple eligible non-selected fleet launchers without losing caps, safety gates, attribution, or evidence separation?
```

It should build on the exact command path and pre/post state instrumentation proven by the command-authority rung. It is not a tactical AI rewrite.

## Expansion model

Start with conservative caps. Suggested initial defaults:

```text
global cap = 3
per-trigger cap = 3
per-ship cap = 1
per-target cap = 1 or target-level assigned-shot cap, whichever is stricter
```

The caps can be made settings later, but initial implementation should prefer hard-coded conservative constants over user-facing configurability.

Only candidates with `candidateSource="currentAllocatorSnapshot"` may be applied. Visible-only missing allocator evidence remains skip-only.

## Required gates

Behavior-changing bounded fleet-wide apply requires all of these:

```text
EnableDiagnostics=True
EnableShadowAllocationDiagnostics=True
EnableFleetWideLiveApplyDiagnostics=True or a more specific bounded-live setting
AllowCommandApply=True
EnableRecommendationOnlyMode=False
command-authority rung status is proven or explicitly allowed
explicit one-shot bounded fleet-wide trigger armed
launcher is player-controlled friendly missile-capable commandable ship
target is concrete hostile combat ship
candidate has current allocator snapshot evidence
same-team / neutral / unknown / ambiguous target is false
caps pass
```

Do not reuse #43.1 dry-run report trigger for live behavior. #43.1 `scopeMode="fleetWideReportOnly"` must remain report-only forever.

## Result rows

Every live candidate should produce parser-visible rows. Suggested vocabulary:

```text
recordType="fleetWideLiveApplyDecision"
recordType="fleetWideLiveApplyResult"
recordType="fleetWideLiveCapState"
recordType="fleetWideLiveCommandCorrelation"
```

Acceptable result classes:

```text
applied
skipped
blocked
failed
```

Required fields:

```text
experimentId
candidateId
commandResultId
scopeMode
runMode
launcherId / launcher / launcherTeam
allocatorLauncherId / allocatorLauncher / allocatorLauncherTeam
targetId / target / targetTeam
candidateSource
assignedShots
commandPath
commandGranularity
capReason
result
reason
exceptionType
preStateVisible
postState
appliedCommands
failedCommands
controlledCommandCorrelation
```

Use:

```text
runMode="fleet-wide-controlled"
```

only when real bounded live commands were attempted and evidence quality is adequate for the claim. If live commands were invoked but direct launch/spend correlation is absent, include an evidence-limited flag or verdict so #43.3 does not treat the run as clean fitting input.

## Direct spend and spillover separation

Direct controlled command spend requires command-result correlation. Rows with:

```text
controlledCommandCorrelation="none"
commandResultId="none"
```

remain vanilla / none-correlated spillover. This is true even if they occur shortly after the bounded fleet-wide experiment.

The parser and fitting/corpus layers must report direct controlled spend and vanilla spillover side by side, never merged into one causal success score.

## Safety boundaries

This slice must not:

- issue commands continuously;
- command missing-evidence candidates;
- command selected scope as a hidden fallback;
- command enemy, AI, non-player, same-team, neutral, unknown-control, or ambiguous ships;
- exceed global, per-trigger, per-ship, or per-target caps;
- suppress vanilla missile behavior;
- tune allocator parameters;
- infer exact kill attribution from `DestroyShip` text;
- mark synthetic fixtures as live evidence;
- begin #43.3 tuning when direct spend/correlation is missing or confounded.

## Acceptance criteria

1. #43.1 report-only path is unchanged.
2. #43.2 RE-blocked probe remains available and blocked until command-authority proof is present.
3. Bounded live apply requires explicit setting, `AllowCommandApply=True`, recommendation-only disabled, and explicit trigger.
4. Caps prevent more than the intended small batch.
5. Only allocator-evidence-backed hostile candidates can be applied.
6. All applied/skipped/blocked/failed rows are parser-visible and include candidate/result ids.
7. Direct controlled spend is distinguished from none-correlated spillover.
8. The parser summarizes bounded fleet-wide live counts, reasons, caps, direct spend, and spillover.
9. Fixtures cover schema and parser behavior without pretending to be real combat evidence.
10. Runtime smoke handoff states whether the run is clean `fleet-wide-controlled`, evidence-limited, or blocked.

## Validation commands

Static validation should include all prior fixture checks plus a new bounded-live fixture:

```powershell
python tools\parse_player_log.py tools\fixtures\fleet_wide_report_only.txt
python tools\parse_player_log.py tools\fixtures\fleet_wide_live_re_blocked.txt
python tools\parse_player_log.py tools\fixtures\fleet_wide_command_authority_probe.txt
python tools\parse_player_log.py tools\fixtures\fleet_wide_bounded_live_apply.txt
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
python -m compileall tools
dotnet build src\MissileFireControl.Core\MissileFireControl.Core.csproj
dotnet build src\MissileFireControl.Mod\MissileFireControl.Mod.csproj
```

Runtime validation requires a real battle log. A minimal useful smoke should report:

```text
bounded fleet-wide experiment id
1-3 command attempts
0 failed commands, unless failure reason is the artifact under review
0 same-team missile target snapshots
0 scope violations
nonzero appliedCommands only for cap-passing allocator-evidence candidates
all missing-evidence candidates skipped
all direct launch/spend correlation either present or explicitly marked missing
```

## Handoff to #43.3

#43.3 may start after this slice only if the output is one of:

```text
clean fleet-wide-controlled evidence
bounded live evidence-limited report with explicit blocker
clear command-authority blocker explaining why broader live apply remains unsafe
```

If vanilla spillover remains large or direct correlation is missing, #43.3 should review it as measurement/authority work, not allocator tuning evidence.

## Implementation note — multi-cycle bounded trigger

The first bounded-live implementation should preserve current allocator evidence rather than infer commands for every visible launcher in one frame. The trigger may remain armed across allocation cycles and apply at most one allocator-evidence-backed command per cycle until the global cap is reached.

Initial implementation shape:

```text
experiment id prefix: fleetwide-bounded-live-
global cap: 3
per-ship cap: 1
per-target cap: 3
scopeMode="fleetWideBoundedLiveApply"
runMode="fleet-wide-controlled"
recordType="fleetWideBoundedLiveCandidate"
recordType="fleetWideBoundedLivePreState"
recordType="fleetWideBoundedLiveResult"
recordType="fleetWideBoundedLivePostState"
```

The trigger can re-arm after irrelevant or missing-evidence cycles, and after successful commands until `totalAppliedCommands` reaches the global cap. Each applied command must still have `candidateSource="currentAllocatorSnapshot"`, a concrete hostile target, cap pass, and direct command-result correlation must be checked in subsequent `LaunchLog` rows.
