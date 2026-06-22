# Issue #37 context

This is local context for Codex planning, not a phased implementation plan or a detailed work order. Codex should use it together with the durable docs, #36 results, and issue text to create its own focused plan for #37.

## Role in #6

Issue #37 is the first behavior-changing controlled slice. It should exercise at most one reviewed game-control operation for one explicitly scoped, player-controlled, eligible candidate, behind the full safety model proven by #34-#36.

This is not a general allocator, fleet automation, or always-on assistant slice. It is a single-operation smoke slice whose value is proving that the reviewed boundary, logging, and rollback assumptions hold for one tightly bounded case.

## Preconditions from earlier slices

#34 supplied the controlled dry-run envelope:

- controlled diagnostics are disabled by default beyond the base toggle;
- a UMM trigger arms one dry-run experiment;
- the next shadow allocation cycle receives an `experimentId`;
- runtime smoke validated trigger-to-cycle pairing and zero applied commands.

#35 supplied candidate and scope safety reporting:

- `dryRunCommandCandidate` rows classify candidates as `eligible`, `wouldSkip`, or `wouldFail` without changing game state;
- parser and fitting reports summarize dry-run evidence separately from normal allocation fitting quality;
- active-player lookup uses `GameControl.control.activePlayer`;
- selected-scope probing checks `GameControl.spaceCombat.combatHUD.selectedFriendlyShipState`;
- runtime evidence showed 3 candidates, all `wouldSkip`, with zero scope violations, zero applied commands, and zero failed commands;
- selected scope was visible in one runtime experiment and correctly skipped a candidate outside that selected scope with `reason="outsidePlayerControlledScope"`.

#36 must complete before #37 starts. #36 should introduce a named hard-stop gate and prove that a gate-reachable dry-run candidate is blocked with `appliedCommands="0"` while the allow condition is false. If #36 only has fixture proof and no real-log eligible candidate, #37 planning must acknowledge that caveat and keep the first behavior-changing attempt narrower, not broader.

#37 also depends on a reviewed safety verdict for the actual game-control path. Do not infer that the path is safe just because #35/#36 diagnostics are clean.

## Planning information for Codex

The #37 plan should be narrower than the future product UX. The useful shape is:

- one explicit user trigger;
- one selected or otherwise explicitly audited player-controlled scope;
- one candidate that is already `eligible` or gate-reachable under the #35/#36 evidence model;
- one resolved objective;
- one unambiguous game-control path;
- one conservative attempt;
- complete intent/result/pre-state/post-state logging where visible;
- immediate stop after the attempt, whether it applied, skipped, or failed.

If any identity, scope, authority, objective, resource, or path evidence is ambiguous, the safe result is skip/fail with a reason. Do not broaden scope to manufacture an eligible case.

Because no real-log eligible candidate was observed during #35, Codex should plan how to obtain or simulate the first eligible path safely before changing anything. A deterministic fixture can prove parser/report behavior, but a runtime behavior-changing attempt should require a very small setup where the scoped candidate is visibly player-controlled and the #36 gate path has already been exercised.

## Report emphasis

The parser/report should link every result back to:

- `experimentId`;
- dry-run candidate id or allocator decision id;
- scope source and scoped entity evidence;
- pre-boundary classification;
- hard-stop gate state;
- final result: skipped, failed, blocked, or applied.

The report should make it obvious that at most one behavior-changing attempt occurred, that all non-scoped candidates remained untouched, and that no scope violation occurred.

## Runtime validation target

A successful #37 smoke should show one and only one bounded attempt. The expected report shape is auditable containment:

- one explicit experiment trigger;
- one scoped candidate;
- zero unscoped candidates applied;
- zero AI/non-player/out-of-scope candidates applied;
- at most one applied result;
- clear skip/fail reason if the attempt does not apply;
- no parser unknown record types.

## Boundary

Do not support multi-ship operation, retries, continuous automation, always-on behavior, or broad fleet management in #37. Do not include unselected, AI-controlled, non-player, or otherwise unproven entities. Do not change unrelated live state or tune allocator heuristics.

Do not proceed from #37 to #38 unless the single bounded attempt is logged clearly and the result is understood. If the first attempt skips or fails for a safety reason, that may still be a useful #37 result, but it should be documented as such rather than broadened in the same slice.
