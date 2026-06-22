# Issue #36 context

This is local context for Codex planning, not a phased implementation plan or a detailed work order. Codex should use it together with the durable docs and issue text to create its own focused plan for #36.

## Role in #6

Issue #36 is the final diagnostics-only safety slice before any later behavior-changing path. Its job is to introduce a named, auditable hard-stop gate and prove that the gate blocks by default.

The expected #36 result is not live readiness. The expected result is: a resolved dry-run candidate can reach the named gate, the gate records that it blocked, and `appliedCommands="0"` remains true.

## Current state from #34 and #35

#34 established the controlled dry-run envelope:

- diagnostics are disabled by default beyond the base toggle;
- a UMM trigger arms one dry-run experiment;
- the next shadow allocation cycle receives an `experimentId`;
- `dryRunExperiment`, `dryRunIntent`, and `dryRunResult` rows are emitted;
- runtime smoke validated trigger-to-cycle pairing and zero applied commands.

#35 added candidate and scope reporting:

- `dryRunCommandCandidate` rows classify candidates as `eligible`, `wouldSkip`, or `wouldFail` without applying anything;
- parser and fitting output now summarize dry-run rows separately from normal allocation fitting quality;
- parser stdout is UTF-8 safe for non-ASCII runtime names;
- active player lookup now uses `GameControl.control.activePlayer`;
- selected-scope probing also checks `GameControl.spaceCombat.combatHUD.selectedFriendlyShipState`.

Latest #35 runtime evidence supports closing #35 as a safety/resolvability report:

- 3 controlled dry-run experiments;
- 3 dry-run candidates;
- selected scope visible in 1 experiment through `GameControl.spaceCombat.combatHUD.selectedFriendlyShipState`;
- selected ship count was 1 in that experiment;
- all 3 candidates were `wouldSkip`;
- reasons were `nonPlayerOrAIControlled` for 2 and `outsidePlayerControlledScope` for 1;
- the visible selected-scope case skipped a candidate outside the selected scope instead of treating it as eligible;
- scope violations, applied commands, and failed commands were all zero;
- parser verdict was OK and unknown record types were zero.

Important caveat for #36: no real-log `eligible` candidate has been observed yet. #36 should therefore focus on the hard-stop gate itself. It can use deterministic fixtures and, when possible, a targeted fresh runtime smoke to prove a gate-reachable candidate is blocked.

## Planning notes

Preserve the two-step safety model:

1. diagnostics / dry-run candidate reporting must be explicitly enabled or triggered;
2. application must remain blocked unless a separate explicit allow condition is true.

For #36, the allow condition should remain false by default. The hard-stop gate should be easy to search, easy to test, and easy to review before #37.

The report should distinguish:

- skipped candidates caused by unsafe or missing scope/evidence;
- failed candidates caused by missing required evidence;
- gate-reachable candidates blocked by the hard stop;
- applied candidates.

For #36, applied candidates must remain zero.

## Parser/report emphasis

Add or preserve summary fields for:

- controlled dry-run experiment count;
- candidate classification counts;
- safety-gate-blocked count;
- block reason, for example `blockedBySafetyToggle` or an equivalent stable reason;
- applied command count, expected zero;
- failed command count;
- scope-violation count, expected zero.

Keep `dryRun*` rows out of normal allocation fitting quality classifications. Gate reporting belongs in the controlled dry-run / candidate summary path.

## Validation target

The best #36 validation shows a dry-run candidate reaching the named hard-stop gate and being blocked with `appliedCommands="0"`.

If a fresh runtime log still produces only `wouldSkip` candidates, keep that as fail-closed evidence, but also include deterministic fixture coverage that exercises the hard-stop path.

## Boundary

Do not invoke behavior-changing game APIs in #36. Do not change live game state. Do not broaden scope just to produce an eligible candidate. Unselected, AI-controlled, non-player, or otherwise unproven entities must not become eligible by accident.

Do not tune allocator heuristics in #36. Do not implement the first behavior-changing application; that belongs to #37 after the hard-stop gate is reviewed and validated.
