# Pre-tuning offline fitting context

## Goal

Rebaseline the former pressure-aware tuning loop as a pre-tuning measurement and
offline fitting loop. The immediate objective is not to prove Candidate A or to
implement a behavior-changing Candidate B. It is to make archived logs usable as
a fixed dataset for candidate replay and problem characterization.

## Current framing

The project should answer this question before tuning behavior:

```text
Does avoidable over-pressure repeatedly occur in bounded-live controlled allocation?
```

A row is not enough simply because one selected target has high pressure. It must
also be possible to show that comparable alternatives existed and that at least
one alternative had lower or under-threshold pressure according to auditable row
features.

## Scope

- Build or document the archived-log dataset path for allocation decision
  contexts.
- Preserve evidence needed to replay candidate policies outside the game.
- Keep pressure-aware bounded-live rows auditable, especially retained
  above-threshold decisions.
- Use comparison/reporting helpers to classify candidates and measurement gaps.
- Keep raw private logs under ignored `artifacts/` paths.

## Non-goals

- No behavior-changing allocator heuristic in this phase.
- No outcome-aware scoring or allocator reward/punishment.
- No broad target-value, launch-window, or point-defense weight retuning.
- No vanilla salvo suppression.
- No command-authority expansion or selected/fleet scope policy changes.
- No projectile guidance, burn-model, or physics changes.

## Offline fitting mode

The intended e2e loop is:

```text
archived Player.log / combat logs
  -> import / parse
  -> decision-context dataset
  -> candidate policy shadow replay
  -> objective and guardrail scoring
  -> ranked candidate report
  -> selected live validation only after offline filtering
```

This is a candidate-filtering loop. It does not replace controlled-live or
fleet-wide-controlled validation for behavior-changing claims.

## First dataset objective

The first dataset should support pressure-aware candidate replay with these
features:

- selected target pressure from prior controlled shots and exact recovered
  in-flight target pressure;
- selected target pressure reference, initially `max(killSize, saturationSize)`;
- lower-bound pressure recorded separately and kept diagnostic-only;
- same-cycle target alternatives with comparable feature evidence;
- per-alternative pressure, threshold, under-threshold status, score/rank
  evidence, and eligibility reason;
- applied/skipped/failed command result and cap reasons;
- direct controlled command-spend evidence separated from vanilla or
  none-correlated spillover.

## First measurement blocker

Current logs can say that alternatives existed and that an above-threshold target
was retained because of `noUnderThresholdAlternative`. They do not always expose
the per-alternative pressure table needed to audit that reason.

The next behavior-preserving diagnostics work should therefore add or preserve
per-alternative pressure evidence before any new live heuristic is implemented.

## Guardrails

The offline fitting loop must preserve these constraints:

- no command-authority expansion;
- no selected-scope or fleet-scope policy changes;
- preserve per-ship caps and command safety gates;
- preserve ammo accounting and manual-control behavior;
- same-team and scope-violation markers remain zero;
- parser verdict remains OK;
- `MissileWarfare` warnings and errors remain zero;
- do not treat `DestroyShip` text or `shipDestroyed` rows as unique projectile
  attribution;
- do not treat vanilla or none-correlated launch rows as direct controlled
  command spend;
- do not treat offline replay as causal proof of live combat improvement.

## Candidate terminology

- Candidate A is current `pressure-aware-bounded-live-v1` behavior under
  measurement. It is not a validated tuning improvement.
- The current Candidate B comparison helper is measurement infrastructure. It is
  not a behavior-changing candidate.
- Future behavior-changing candidates should be generated or selected from the
  offline fitting report.

## Follow-up boundary

Outcome-aware tuning requires a separate correlation plan. That plan must define
join keys, conservative confidence levels, vanilla/none-correlated spillover
handling, multiple controlled launches into the same target window, and the rule
that `shipDestroyed` killer/weapon evidence without a unique projectile id is
not exact projectile attribution.

The current offline fitting loop may reference outcome-hook runtime health, but
it must not perform outcome-to-allocation joins or use outcome rows as reward.
