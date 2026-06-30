# GitHub issue alignment

This page records how remote GitHub issues and milestones should be aligned with
the current project direction. Use it when updating issue bodies, labels,
milestones, or cross-links from the remote tracker.

## Current direction to preserve

TI MissileWarfare is in a diagnostics-first, pre-tuning measurement phase. The
next milestone is not a new behavior-changing heuristic. It is to close the
offline fitting loop over archived logs:

```text
archived Player.log / combat logs
  -> parser/importer
  -> allocation decision-context dataset
  -> candidate policy shadow replay
  -> objective / guardrail scoring
  -> ranked candidate report
  -> small live validation only for selected candidates
```

Remote issues should therefore describe behavior-changing work as blocked until
offline replay identifies a repeated, avoidable allocator-quality problem and a
fresh controlled-live or fleet-wide-controlled validation slice confirms the
candidate.

## Known remote alignment risks

The initial GitHub roadmap was created around bootstrap milestones and Issues
#1-#7. That structure is still useful historically, but it predates several
current decisions and can now mislead maintainers if read literally.

Check and update remote issue bodies for these drift patterns:

- references to `readyShots` or loaded/chambered missile counts; replace with
  the validated `ammoGateBudgetShots` terminology and link to
  `docs/research/readiness-semantics.md`;
- Issue #6 wording that implies broad fleet-wide auto-allocation is ready;
  clarify that selected-single, selected-group, and bounded fleet-wide paths are
  narrow, default-off controlled experiments, not general readiness;
- Issue #7 wording that implies launch suppression can start now; keep it
  blocked on validated runtime scoring inputs and independent disablement;
- Candidate A/B wording that treats Candidate A as a proposed improvement or
  Candidate B as a behavior-changing candidate; Candidate A is current
  `pressure-aware-bounded-live-v1` behavior under measurement, and the current
  Candidate B helper is measurement infrastructure;
- milestone names or issue ordering that skip the offline fitting loop and jump
  from diagnostics directly to live tuning;
- outcome-hook wording that treats `[OutcomeLog]` rows as allocation reward,
  unique projectile attribution, or command kill proof. Issue #47 establishes a
  separate event-level outcome evidence stream; AllocationLog-to-OutcomeLog
  correlation is later work.

## Recommended issue structure

Use the durable docs as the source of truth when updating remote issues:

- `docs/agent/CURRENT_STATE.md`: concise project posture and current blockers.
- `docs/planning/mvp-roadmap.md`: issue-sized roadmap and next work.
- `docs/planning/offline-fitting-loop.md`: current tuning sequence and minimum
  loop closure.
- `docs/diagnostics/snapshot-and-allocation.md`: allocation and bounded-live
  diagnostic schema.
- `docs/diagnostics/hooks.md`: confirmed launch and outcome hook evidence.
- `docs/research/readiness-semantics.md`: `ammoGateBudgetShots` semantics.
- `docs/research/selected-command-scope.md`: selected-player command scope.

Remote tracker structure should make these phases visible:

1. completed diagnostics foundation;
2. selected-scope and bounded-live controlled experiments;
3. offline fitting dataset/replay/report closure;
4. selected live validation for ranked candidates;
5. behavior-changing allocation or launch-discipline work only after evidence;
6. outcome correlation only after a conservative join design exists.

## Issue-specific update guidance

### Issues #1-#4

Mark these as completed diagnostic foundation if the remote issue state does not
already do so. Their body should point to `docs/diagnostics/hooks.md` and
`docs/diagnostics/snapshot-and-allocation.md` rather than old scaffold-only
language.

### Issue #5

Keep this as recommendation/debug presentation work, not a current blocker and
not behavior-changing command application. It should clearly say
recommendation-only output must remain distinguishable from live command apply.

### Issue #6

Update the body to say this is blocked by offline fitting and safety evidence.
The current safe framing is:

- use explicit player-controlled command scope;
- preserve `ammoGateBudgetShots` diagnostics;
- respect vanilla salvo target command granularity as ship-level across all
  salvo-capable weapons;
- keep command application default-off and gated;
- do not treat selected or bounded fleet-wide experiments as general readiness;
- continue from #37/#38 safety constraints and #39/#43 evidence rather than
  re-opening fictitious per-module command assumptions.

### Issue #7

Keep launch discipline as blocked until runtime scoring inputs are validated.
Any first slice should be diagnostics or report-only unless the issue explicitly
requires behavior change and the cited docs support it.

### Issues #39, #43, #47 and later

Use these as evidence-building issues, not as proof that tuning is complete:

- #39 resolves selected-group direct command-result launch/spend attribution for
  the diagnostic path, but not allocator quality or kill attribution.
- #43 bounded/fleet-wide work provides command-authority, bounded-live, corpus,
  and measurement-readiness evidence. It does not justify broad tuning without
  offline problem characterization.
- #47 outcome hooks are diagnostics-only and event-level. Do not merge them into
  command-spend proof or offline fitting rewards until a separate correlation
  issue defines conservative join keys and confidence levels.

## Suggested new or updated remote issues

If the remote tracker lacks them, create or update issues around these concrete
next slices:

1. Build/import allocation decision-context dataset from fixed archived logs.
2. Replay current policy and at least one report-only candidate policy offline.
3. Score surrogate pressure objectives and hard guardrails.
4. Emit `ranked-candidates.md` plus machine-readable candidate verdicts.
5. Audit retained above-threshold rows with `noUnderThresholdAlternative` using
   target-alternative and pressure evidence.
6. Design AllocationLog-to-OutcomeLog correlation separately from allocator
   tuning.

## Label and milestone guidance

Useful labels for future remote cleanup:

- `phase:diagnostics`
- `phase:offline-fitting`
- `phase:controlled-live`
- `phase:outcome-correlation`
- `status:blocked-by-evidence`
- `status:report-only`
- `status:default-off`
- `evidence:shadow-replay`
- `evidence:controlled-live`
- `evidence:fleet-wide-controlled`
- `evidence:fixture`

Milestones should avoid implying that live tuning follows directly after basic
diagnostics. A clearer sequence is:

- completed bootstrap / launch diagnostics;
- snapshot, recommendation, and command-safety diagnostics;
- bounded-live measurement and corpus import;
- offline fitting loop closure;
- selected live validation of ranked candidates;
- behavior-changing tuning only after validation.

## Remote update discipline

When editing a remote issue, preserve historical context but add a current-state
section near the top. Prefer this structure:

```markdown
## Current alignment

This issue is governed by the diagnostics-first / offline-fitting direction in
`docs/agent/CURRENT_STATE.md` and `docs/planning/offline-fitting-loop.md`.

## Current status

...

## Blockers / evidence gates

...

## Acceptance criteria

...
```

Do not delete old acceptance criteria merely because the project moved forward.
Mark them complete, superseded, or blocked, and link to the durable doc that
explains why.
