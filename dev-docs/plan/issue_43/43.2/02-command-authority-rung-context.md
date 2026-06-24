# Issue #43.2b context — Non-selected command-authority rung

Updated: 2026-06-24
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.2/02-command-authority-rung-context.md`
Parent context: `dev-docs/plan/issue_43/43.2/00-context.md`
Previous handoff: `dev-docs/plan/issue_43/43.2/01-re-blocker-summary.md`

This is context for the first behavior-changing rung after the #43.2 RE-blocked handoff. It is not a separate broad issue and not a reason to endlessly subdivide #43.2. Its purpose is to open exactly one non-selected command in a way that can prove or reject command authority before any multi-ship fleet-wide live apply is enabled.

## Current state entering this rung

The #43.2 blocked probe exists and has runtime evidence:

```text
recordType="fleetWideLiveCommandPathStatus"
recordType="fleetWideLiveApplyDecision"
recordType="fleetWideLiveResult"
scopeMode="fleetWideLiveReBlocked"
reGateStatus="blocked"
blockReason="nonSelectedFleetWideRuntimeSmokeMissing"
appliedCommands="0"
failedCommands="0"
```

The uploaded runtime smoke from 2026-06-24 showed one blocked #43.2 probe with:

```text
fleetWideLiveCommandPathStatus: 1
fleetWideLiveApplyDecision: 9
fleetWideLiveResult: 1
allocatorEvidenceCandidates: 1
missingEvidenceCandidates: 8
reBlockedCandidates: 1
appliedCommands: 0
failedCommands: 0
```

That validates the blocked diagnostic surface. It does not prove non-selected command safety because no command API was called.

Known command path from selected-scope work:

```text
SelectSalvoTargetCommand.OnCommandExecute(TISpaceShipState, CombatTargetableState)
```

Static review shows the path accepts explicit launcher and target objects, but it can mutate:

```text
combatPrimaryTarget
salvoFireMode
uiGlobalTargetingModeShutdown
```

The next rung must prove what happens when this command path is invoked for a non-selected player-controlled launcher.

## Purpose

This rung answers one question:

```text
Can the mod safely issue exactly one vanilla salvo target command for one non-selected, player-controlled, allocator-evidence-backed launcher-target candidate, and can the result be attributed or safely failed?
```

It should not implement multi-ship fleet-wide live apply. It should create the narrowest possible command-authority experiment that makes the next decision obvious.

## Required behavior

Add a default-off, explicit, one-shot command-authority probe mode that is distinct from the existing RE-blocked diagnostic probe.

The probe may attempt at most one real command per trigger:

```text
global cap = 1
per-trigger cap = 1
per-ship cap = 1
per-target cap = 1
```

A candidate can be attempted only when all are true:

```text
EnableDiagnostics=True
EnableShadowAllocationDiagnostics=True
AllowCommandApply=True
EnableRecommendationOnlyMode=False
new command-authority probe setting=True
explicit one-shot command-authority trigger armed
launcher is player-controlled friendly missile-capable commandable ship
launcher is not the currently selected command-panel ship if non-selected evidence is required
target is a concrete hostile combat ship
candidateSource=currentAllocatorSnapshot
missing allocator evidence is false
same-team / neutral / unknown / ambiguous target is false
all caps pass
```

If the only allocator-evidence-backed candidate is selected rather than non-selected, the probe should skip or block with a reason such as:

```text
nonSelectedLauncherRequired
```

The probe must not silently broaden into selected-scope #37/#38 behavior.

## Instrumentation requirements

Before attempting the command, log pre-state sufficient to review command authority:

```text
experimentId
candidateId
commandResultId
launcherId / launcher / launcherTeam
allocatorLauncherId / allocatorLauncher / allocatorLauncherTeam
targetId / target / targetTeam
selectedScopeSource
selectedShipIds / selectedShipCount where visible
isLauncherSelected or launcherSelectionRelation
preLauncherPrimaryTargetId / preLauncherPrimaryTargetName
preLauncherSalvoModeSummary or preLauncherWeaponModeSummary
preUiGlobalTargetingMode if visible
preCanPerformCommands
preCanFireMissiles
```

After the command attempt, log post-state:

```text
postLauncherPrimaryTargetId / postLauncherPrimaryTargetName
postLauncherSalvoModeSummary or postLauncherWeaponModeSummary
postUiGlobalTargetingMode if visible
postState="commandInvoked" | "notApplied" | "partialOrUnknown"
result="applied" | "skipped" | "failed" | "blocked"
reason
exceptionType
appliedCommands
failedCommands
```

If a command is invoked, register a command-result correlation context like selected-group controlled work does. Later `MissileWeapon.TryFire` rows should be able to report:

```text
experimentId
commandResultId
controlledCommandCorrelation="directRuntimeContext" | "none"
controlledCommandObservedSpentShots
```

The first command-authority smoke may succeed even if direct launch correlation is not immediately observed, but that result must be labeled evidence-limited. Do not call it `fleet-wide-controlled` fitting evidence unless direct command-result launch/spend evidence is present or the handoff clearly says correlation remains missing.

## Record vocabulary

Existing #43.2 blocked vocabulary should remain valid. Add a distinct command-authority mode rather than reusing `fleetWideLiveReBlocked` for real attempts.

Suggested values:

```text
scopeMode="fleetWideCommandAuthorityProbe"
runMode="fleet-wide-command-authority-probe"
recordType="fleetWideCommandAuthorityCandidate"
recordType="fleetWideCommandAuthorityPreState"
recordType="fleetWideCommandAuthorityResult"
recordType="fleetWideCommandAuthorityPostState"
```

Names may follow existing style, but parser output must distinguish:

```text
blocked before command
skipped because not non-selected
skipped because missing allocator evidence
failed during invocation
applied command invoked
applied but no direct launch correlation yet
applied with direct launch/spend correlation
```

## Safety boundaries

This rung must not:

- attempt more than one command per trigger;
- command selected-group candidates as a fallback;
- apply missing-evidence visible-only candidates;
- command enemy, AI, non-player, same-team, neutral, unknown-control, or ambiguous ships;
- suppress vanilla missile behavior;
- tune allocator parameters;
- produce broad fleet-wide multi-ship apply;
- claim exact kill attribution from `DestroyShip` text;
- leave a second pending command after one attempt succeeds, fails, or is safety-blocked.

The experiment should consume the one-shot trigger after one decisive candidate/result row. If no valid non-selected allocator-backed hostile candidate appears, it may remain armed or time out, but that behavior must be explicit in logs and UI text.

## Acceptance criteria

1. #43.1 `fleetWideReportOnly` rows still imply no live application and `appliedCommands="0"`.
2. #43.2 RE-blocked probe still works and never calls the command API.
3. Command-authority probe requires its own default-off setting, `AllowCommandApply=True`, `EnableRecommendationOnlyMode=False`, and an explicit trigger.
4. At most one non-selected launcher-target command can be attempted per trigger.
5. Missing allocator evidence and selected-only candidates are skipped/blocked with explicit reasons.
6. Pre/post launcher target and weapon/salvo state are logged where visible.
7. Command result has a stable `commandResultId` and parser-visible result row.
8. Applied, skipped, blocked, and failed outcomes are parser-visible.
9. Direct controlled launch/spend correlation is preserved if it occurs; otherwise the run is marked evidence-limited.
10. Fixture/parser validation covers the new row vocabulary without claiming real combat evidence.

## Validation commands

Static and fixture validation should include:

```powershell
python tools\parse_player_log.py tools\fixtures\fleet_wide_report_only.txt
python tools\parse_player_log.py tools\fixtures\fleet_wide_live_re_blocked.txt
python tools\parse_player_log.py tools\fixtures\fleet_wide_command_authority_probe.txt
python -m compileall tools
dotnet build src\MissileFireControl.Core\MissileFireControl.Core.csproj
dotnet build src\MissileFireControl.Mod\MissileFireControl.Mod.csproj
```

Runtime smoke requires a real battle and a user-provided `Player.log`. The expected clean smoke is:

```text
one command-authority experiment id
one candidate attempted or explicitly blocked
appliedCommands is 0 or 1, never more
failedCommands is 0 unless invocation failed with a concrete exception
same-team missile target snapshots = 0
scope violations = 0
no broad fleet-wide multi-ship apply
```

## Handoff

If this rung succeeds with one clean non-selected command invocation and no unsafe post-state, the next context is:

```text
dev-docs/plan/issue_43/43.2/03-bounded-fleet-wide-live-apply-context.md
```

If it fails, update `01-re-blocker-summary.md` or add a follow-up blocker summary with the exact failed reason, post-state evidence, and whether the command mutated partial state before failing.
