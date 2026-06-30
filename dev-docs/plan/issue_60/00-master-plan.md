# Close offline fitting loop over archived allocation logs

## Issue Target And Scope Summary

- Issue target: #60
- Title: Close offline fitting loop over archived allocation logs
- Source plan: `dev-docs/plan/tuning_loop/` is absorbed into this issue plan.
- Scope: build the minimum archived-log offline fitting loop that turns
  allocation diagnostics into decision-context rows, replays current and
  report-only policies, scores surrogate pressure objectives with hard
  guardrails, and emits ranked candidate verdicts without changing live combat
  behavior.

## Strategy

- Treat `docs/planning/offline-fitting-loop.md` and the #60 issue body as the
  durable requirements.
- Treat `dev-docs/plan/tuning_loop/` as historical input: it supplied the
  measurement-first framing, local baseline snapshot, comparison template, and
  first-sweep boundary, but it is no longer a competing active plan.
- Preserve private raw logs and generated corpus artifacts under ignored
  `artifacts/` paths.
- Start with corpus-level decision-context extraction, not whole-battle
  summaries.
- Replay current `pressure-aware-bounded-live-v1` as the policy under
  measurement, not as a validated improvement.
- Add at least one report-only candidate policy so offline fitting can classify
  candidate value before any live behavior change.
- Score surrogate pressure objectives separately from hard safety and evidence
  guardrails.
- Keep `[OutcomeLog]` rows as hook-health context only until a separate
  allocation-to-outcome correlation issue defines conservative joins.

## Phase Order

1. [Plan absorption and source of truth](01-absorption.md)
2. [Decision-context dataset extraction](02-dataset.md)
3. [Candidate replay and scoring](03-replay.md)
4. [Report closure and validation](04-reporting.md)

## Phase Dependencies

- Phase 1 has no phase dependency beyond resolved issue context.
- Phase 2 depends on completion and validation of phase 1.
- Phase 3 depends on completion and validation of phase 2.
- Phase 4 depends on completion and validation of phase 3.

## Source Of Truth Decisions

- `00-master-plan.md` is the phased implementation plan source of truth.
- Phase files in this directory define phase-local scope and validation.
- `dev-docs/plan/tuning_loop/` is retained only as absorbed historical input.
- Durable project posture remains in `docs/planning/offline-fitting-loop.md`,
  `docs/agent/CURRENT_STATE.md`, and related diagnostics docs.
- Candidate verdict vocabulary for #60 is `candidate-filtered`,
  `needs-live-validation`, `inconclusive`, and `blocked`; auxiliary comparison
  notes may also say `no material change` when no candidate shortlist is
  justified.

## Global Validation Expectations

- `python tools/check_layout.py`
- `python -m compileall tools`
- `python tools/parse_player_log.py --require-launchlogs`
- `dotnet build TI_Missile_Fire_Control.sln` when source or integration changes
  make the solution build relevant.
- The new offline-fitting command, once named, must be added to this list and to
  phase-local validation.

## Known Risks And Assumptions

- The first useful objective is pressure/evidence quality, not damage, kill, or
  outcome-aware optimization.
- Offline replay is a candidate filter and must not be described as causal proof
  of live combat improvement.
- Rows with lower-bound pressure, missing alternatives, parser warnings, or
  ambiguous spillover must prevent overconfident candidate verdicts.
- The current local baseline snapshot in
  `dev-docs/plan/tuning_loop/02-baseline-corpus.md` is useful evidence context,
  but it is one local combat run and remains evidence-limited.
- `ammoGateBudgetShots` is the readiness budget term; do not reintroduce
  `readyShots`.
- No phase may broaden selected-scope, fleet-scope, command authority, or live
  allocator behavior unless a later behavior-changing issue explicitly asks for
  that work.
