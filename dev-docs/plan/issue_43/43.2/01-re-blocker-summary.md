# Issue #43.2 RE blocker summary

Updated: 2026-06-24
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.2/01-re-blocker-summary.md`
Related context: `dev-docs/plan/issue_43/43.2/00-context.md`

## Result

Issue #43.2 is completed as an explicit RE-blocked handoff, not as bounded fleet-wide live apply.

The implementation adds a distinct default-off fleet-wide live apply diagnostics setting and an explicit one-shot UMM trigger. When triggered, the next allocation cycle emits parser-visible #43.2 rows, but it does not call the Terra Invicta command API and always reports `appliedCommands="0"`.

## RE decision

Static review confirmed the existing selected-scope live command path remains:

```text
SelectSalvoTargetCommand.OnCommandExecute(TISpaceShipState, CombatTargetableState)
```

The underlying command path accepts explicit launcher and target runtime objects. However, the reviewed path also mutates combat primary target, salvo fire mode, and UI global targeting state. The repo does not yet have runtime smoke evidence proving that invoking this path for a non-selected fleet-wide launcher is safe, preserves manual state, avoids no-op/failure surprises, and produces direct command-result correlation.

Therefore the #43.2 RE gate remains blocked with:

```text
fleetWideLiveCommandPathStatus="blocked"
reGateStatus="blocked"
blockReason="nonSelectedFleetWideRuntimeSmokeMissing"
nonSelectedCommandPathProven="False"
resultReason="reGateBlockedUnprovenNonSelectedCommandPath"
```

## Implemented surface

Runtime diagnostics now include:

- `fleetWideLiveCommandPathStatus`
- `fleetWideLiveApplyDecision`
- `fleetWideLiveResult`

All #43.2 blocked rows use:

```text
scopeMode="fleetWideLiveReBlocked"
runMode="blocked"
appliedCommands="0"
failedCommands="0"
controlledCommandCorrelation="none"
```

The parser summarizes these rows through `fleet_wide_live_*` fields and the human-readable parser output now includes a fleet-wide live section when such rows are present.

Synthetic fixture:

```text
tools/fixtures/fleet_wide_live_re_blocked.txt
```

## What remains impossible

This slice still cannot:

- issue fleet-wide live commands;
- produce `runMode = fleet-wide-controlled` evidence;
- count any #43.2 row as direct controlled command spend;
- suppress vanilla missile behavior;
- support fitting/tuning from fleet-wide live evidence.

## Handoff

#43.3 should receive this as an explicit RE blocker. If #43.3 needs live evidence, a later focused command-authority/runtime-smoke issue must first prove safe non-selected player-controlled launcher invocation and command-result correlation.

## Next context files

The next work should not jump directly from this blocker to broad multi-ship apply. It should use these local contexts in order:

```text
dev-docs/plan/issue_43/43.2/02-command-authority-rung-context.md
dev-docs/plan/issue_43/43.2/03-bounded-fleet-wide-live-apply-context.md
```

`02-command-authority-rung-context.md` is the first behavior-changing rung: one non-selected player-controlled allocator-evidence-backed command at cap=1, with pre/post state and command-result correlation instrumentation.

`03-bounded-fleet-wide-live-apply-context.md` is the follow-up expansion after the cap=1 rung has clean runtime evidence or a maintainer explicitly accepts the remaining evidence limitation.
