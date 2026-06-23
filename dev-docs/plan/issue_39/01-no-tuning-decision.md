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

## Fresh Instrumented Log Follow-up

A fresh instrumented `Player.log` was reviewed after the initial correlation
instrumentation. The new launch-side fields were present on `MissileWeapon.TryFire`
rows, but direct correlation still remained unavailable: launch rows reported
`controlledCommandCorrelation="none"` because the command result target id and
launch diagnostic target id used different identity systems.

Observed mismatch:

- controlled command result rows used allocator target ids such as `280` / `283`;
- launch diagnostics used a runtime `CombatShipController` stable id for
  `targetId`, while the target text still exposed the tactical target id;
- therefore line-window same-launcher/same-target evidence was visible, but the
  runtime direct context match could not fire.

This follow-up adds a diagnostics-only target identity bridge:

- `MissileWeapon.TryFire` now also logs `targetStateId`, derived from the target
  object's gameplay id/name or description suffix;
- controlled command runtime matching accepts either the stable launch
  `targetId` or the bridged `targetStateId`;
- the fitting report prefers `targetStateId` and target-text id fallback before
  falling back to launch-side stable `targetId`;
- the synthetic selected-group fixture now exercises a stable `targetId` plus a
  bridged `targetStateId`.

This still does not tune allocator heuristics. A new smoke run with this target
identity bridge is required before #39 can reassess whether direct stamped
launch/spend evidence identifies one bounded heuristic family to change.

## Direct Correlation Smoke Success

A fresh selected-group controlled smoke after the target identity bridge produced
the first direct command-result launch/spend correlation evidence for #39:

- selected ships: 3, within `selectedGroupMaxShips=3`;
- command result rows: 4 total;
- applied decisions: 3;
- skipped decisions: 1, due to `perShipCommandCapReached`;
- failed decisions: 0;
- directly stamped `MissileWeapon.TryFire` launch rows: 18;
- each applied command row had six direct launch rows and observed spent shots of
  six;
- the skipped command row had no direct launch attribution.

This resolves the previous command-spend correlation blocker for selected-group
controlled apply. The remaining #39 blocker is now outcome quality rather than
command-spend attribution: the fitting loop still needs evidence about whether
the allocated salvo was excessive, insufficient, aimed at the wrong target, or
absorbed by point defense.

A best-effort parser/report follow-up now records vanilla
`CombatManager ActiveShip(DestroyShip)` lines as target outcome hints when they
appear after a controlled command result for the same target id. These rows are
labeled as post-command outcome evidence only; they are not unique hit,
projectile, or kill attribution. Exact damage packet, hit, or destruction
attribution would require additional reverse engineering of Terra Invicta combat
internals and should remain out of scope for this #39 slice unless a stable hook
is identified later.

## Additional Multi-target Smoke Observation

A later controlled smoke strengthened the direct-correlation result:

- controlled command result rows included three applied commands and many
  `perShipCommandCapReached` skipped rows;
- direct `MissileWeapon.TryFire` rows were observed for the applied commands
  only;
- one Medusa command spent six directly observed shots and Medusa later appeared
  in vanilla `DestroyShip` text;
- two Yudachi commands spent seven directly observed shots each and Yudachi later
  appeared in vanilla `DestroyShip` text;
- skipped rows for Yudachi had no direct launch attribution, even though the
  target was later destroyed.

The report logic now only attaches target-outcome hints to command rows that have
directly correlated launch evidence, so skipped same-target rows do not receive a
misleading post-command destruction hint. The outcome remains conservative:
post-direct-launch target destruction is useful quality evidence, but not unique
projectile or kill attribution.

## Additional Sphinx/Ghost Smoke Observation

A later controlled smoke added another successful direct-correlation sample:

- experiment `dryrun-20260622T224547798Z-1` selected one ship and applied one
  command to Sphinx;
- Puebla spent six directly correlated shots on Sphinx, and Sphinx later
  appeared in vanilla `DestroyShip` text;
- experiment `dryrun-20260622T224608094Z-2` selected three ships and applied two
  commands to Ghost;
- Friedland spent eight directly correlated shots on Ghost;
- Ramillies spent eight directly correlated shots on Ghost;
- Ghost later appeared in vanilla `DestroyShip` text;
- twenty-eight skipped rows were `perShipCommandCapReached` and had no direct
  launch attribution.

This reinforces the current #39 state: the controlled command-spend evidence path
is working, target outcome hints are useful after direct launches, and skipped
rows remain causally separated. It also exposes the first concrete tuning
candidate for a later implementation slice: same-target duplicate kill packages.
In the Ghost case, two ships each committed a kill-sized salvo to the same target
and the target was later destroyed. That is a candidate for a target-level
aggregate salvo cap or duplicate kill-package suppression rule, but not a rule
change in this diagnostics PR.

Implementation boundary: no additional instrumentation code is required for the
current #39 evidence closeout. A future PR should decide and implement at most one
bounded heuristic/rule-family change, using these direct command-spend and
post-direct-launch outcome hints as supporting evidence.

## Final Pre-tuning Diagnostic Closeout

Before moving to an actual heuristic/rule change, #39 now also makes the next
candidate mechanically visible in the fitting report. The controlled report emits
a `Controlled tuning candidates` section that groups directly correlated applied
commands by experiment and target, then flags same-target duplicate kill-package
candidates when multiple direct commands spend on the same target and total
observed spend exceeds the target's available kill-size evidence.

This is still report-only. It does not alter allocator behavior, command scope,
missile spending, target choice, or any heuristic parameter. Its purpose is to
make the next PR's precondition explicit: a future same-target aggregate salvo cap
or duplicate kill-package suppression change should cite a report row produced
from direct command-spend evidence and, where available, post-direct-launch
DestroyShip outcome hints.

With this diagnostic in place, #39 has done the useful pre-tuning work available
without changing allocator behavior:

- direct command-spend correlation is instrumented and validated;
- target identity bridging is instrumented and validated;
- skipped rows are causally separated from applied launch rows;
- post-direct-launch target destruction hints are parsed conservatively;
- skipped same-target rows cannot inherit destruction hints;
- same-target duplicate kill-package candidates are now report-visible;
- exact projectile/hit/kill attribution remains out of scope without a stable RE
  hook.

## Focused Same-target Cap Follow-up

A focused behavior-changing follow-up now implements the first bounded rule from
the report-only candidate evidence: within one selected-group controlled command
experiment, once a target has received an applied command package, later eligible
commands to that same target are skipped with
`targetAggregateSalvoCapReached` if they would exceed the experiment's
target-level assigned-shot budget.

This is intentionally a controlled selected-group command gate, not a broad
allocator rewrite. The current live path builds one-target allocation requests
from `MissileWeapon.TryFire` cycles, so the cross-ship duplicate evidence is only
visible in the controlled experiment state that spans selected ships and cycles.
The existing selected-scope, hostile-target, per-ship, and group command caps are
preserved.

Evidence cited from the regenerated local report
`artifacts\shadow-fitting\issue_39_latest_local\shadow-fitting-report.md`:

- `dryrun-20260622T224037268Z-3` / Yudachi#284: two direct applied commands,
  14 assigned and 14 directly observed spent shots, with a conservative
  post-direct-launch destroyed hint.
- `dryrun-20260622T224608094Z-2` / Ghost#281: two direct applied commands,
  16 assigned and 16 directly observed spent shots, with a conservative
  post-direct-launch destroyed hint.

The rule does not infer exact projectile, hit, or kill attribution from
`DestroyShip` text. It only uses the direct command-spend rows as support for
preventing repeated same-target ship-level command packages in the selected
controlled experiment.

Fresh runtime smoke on the active `Player.log` written 2026-06-23 11:04 local
validated the new skip reason. In experiment `dryrun-20260623T020248174Z-1`,
Pharsalos applied one direct command to Dragon#281 for eight assigned and eight
directly observed spent shots. Later same-target eligible commands from El
Alamein and Kasserine Pass were skipped with
`targetAggregateSalvoCapReached` at report lines 88 and 90 in
`artifacts\shadow-fitting\issue_39_20260623_1104_local\shadow-fitting-report.md`.
Dragon later appeared in conservative post-direct-launch `DestroyShip` outcome
text.
