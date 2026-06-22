# Issue #39 controlled-correlation instrumentation

## Current Decision

Issue #39 does not change allocator heuristics, rules, or parameters yet.

The previous no-tuning conclusion is now treated as an interim finding from the
pre-instrumentation evidence, not a final closeout. The #38 selected-group
controlled evidence validates the bounded selected-group command safety rung,
but it still does not causally connect controlled command result rows to actual
missile spend, launch, or outcome.

## Instrumentation Attempt

This slice adds diagnostics-only command correlation support:

- controlled apply-gate and apply-result rows now log `commandResultId`;
- successful controlled command invocations register an in-memory launch context
  keyed by `experimentId`, `commandResultId`, launcher id, target id, and
  assigned shots;
- `MissileWeapon.TryFire` launch diagnostics now log launcher/target ids,
  visible pre/post ammo delta, `experimentId`, `commandResultId`,
  `controlledCommandCorrelation`, and cumulative
  `controlledCommandObservedSpentShots` when an applied command context matches;
- failed command invocations clear the pending context;
- skipped rows still get a stable `commandResultId` for reporting but do not
  register causal launch context.

No gameplay behavior changed. The command scope, vanilla command invocation,
ammo accounting, target selection, projectile behavior, cooldowns, and allocator
heuristics are unchanged.

## Evidence Reviewed

Controlled evidence source:

- `docs/diagnostics/runtime-validation-history.md`
- `dev-docs/plan/issue_38/02-verification.md`
- raw controlled log:
  `C:\Users\techn\AppData\LocalLow\Pavonis Interactive\TerraInvicta\Player.log`
- regenerated controlled fitting artifact:
  `artifacts\shadow-fitting\heuristic_tuning_controlled`

The raw #38 `Player.log` was written 2026-06-23 06:03 local time. It predates
the new `commandResultId` launch stamping, so it can only exercise the legacy
line-window fallback.

Observed selected-group safety evidence remains:

- two selected-group controlled experiment ids:
  `dryrun-20260622T210249826Z-1` and `dryrun-20260622T210303457Z-2`;
- three selected ships: `Shiloh#276`, `Carrhae#278`, and `Puebla#279`;
- six applied commands total;
- four post-gate skips with `perShipCommandCapReached`;
- zero failed commands;
- zero scope violations;
- zero same-team missile target snapshots;
- no parser suspicious patterns;
- no MissileWarfare issues.

Regenerating `artifacts\shadow-fitting\heuristic_tuning_controlled` after the
tooling update produced:

- parser verdict: `OK`;
- readiness verdict: `Conditionally ready`, because only one real selected
  controlled log was analyzed;
- controlled command result rows: 10, with six applied and four skipped;
- direct spent evidence rows: 0/10;
- directly stamped rows: 0/10;
- line-window heuristic rows: 10/10;
- uncorrelated rows: 0/10;
- observed ammo deltas by result: applied=6, skipped=4.

The synthetic fixture report now demonstrates the new parser/report bucket with
one directly stamped command launch row, but synthetic fixture evidence is not a
tuning basis.

## Reassessment

Outcome B applies for the old controlled log: direct correlation is not
available yet because the log predates the new diagnostic fields.

Do not tune heuristics from the current evidence. The current controlled live
evidence is still safe-command evidence plus line-window launch observation, not
causal command-spend proof.

The next required manual smoke test is:

1. deploy the instrumented mod;
2. enter tactical combat;
3. select 2-3 player missile ships;
4. enable controlled mode / explicit apply;
5. trigger one selected-group controlled allocation;
6. capture `Player.log`;
7. regenerate `artifacts\shadow-fitting\heuristic_tuning_controlled`.

Only after a fresh instrumented controlled run should #39 decide whether direct
command-result spend/launch correlation identifies exactly one heuristic family
to tune. If it does not, record a final no-tuning/blocker decision with that
stronger evidence.

## Handoff

Named blocker: fresh runtime evidence is required with launch/spend diagnostics
stamped by `experimentId` and `commandResultId`. Until then, #39 remains a
controlled-evidence fitting loop with no heuristic change, not a successful
tuning validation.

#44 remains the follow-up corpus and parameter-ledger infrastructure issue.
#43 should not treat #39 as evidence of successful heuristic tuning.
