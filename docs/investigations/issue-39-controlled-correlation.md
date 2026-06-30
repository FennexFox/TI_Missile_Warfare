# Issue #39 controlled correlation investigation

This page preserves detailed Issue #39 investigation notes that were split from
the MVP roadmap. The roadmap should keep only the current milestone summary and
link here for evidence history.

## Current conclusion

The selected-group command-spend blocker is resolved for the #39 diagnostic
path: fresh controlled smokes produced directly stamped
`MissileWeapon.TryFire` rows for applied command results, while skipped command
rows did not receive direct launch attribution.

Command-spend attribution is no longer the blocker for the #39 diagnostic path.
The next blocker for heuristic tuning is offline problem characterization:
archived logs must be turned into auditable decision-context rows before a
behavior-changing rule slice is selected.

Needs verification: exact missile hit, intercept, damage, and kill attribution
still requires a stable combat outcome hook.

Needs verification: actual vanilla salvo suppression and selected-ship budget
distribution remain unresolved and need a later focused design before or during
Issue `#43`.

## Target identity bridge note

A fresh instrumented #39 log showed that launch telemetry was present but direct
correlation still failed because command results and `MissileWeapon.TryFire`
launch rows used different target identity forms. The #39 diagnostics now add a
launch-side `targetStateId` bridge and fitting-report fallback so the next fresh
selected-group smoke can test direct command-result launch/spend correlation
instead of relying on same-launcher/same-target line-window evidence.

## Direct correlation status

The selected-group command-spend blocker is now resolved for the #39 diagnostic
path: a fresh controlled smoke produced directly stamped `MissileWeapon.TryFire`
rows for applied command results, while the skipped command had no direct launch
attribution. Command-spend attribution is therefore no longer the blocker for
that path. Parser/report tooling now records conservative post-command target
destruction hints from vanilla `DestroyShip` log text, but exact hit/kill
attribution remains out of scope until a stable combat outcome hook is
identified. Heuristic work should next flow through the archived-log offline
fitting loop, not directly from this single investigation.

## Follow-up boundary

The latest selected-group smokes show stable direct command-spend correlation and
post-direct-launch target destruction hints. The current diagnostics PR does not
need more command-spend instrumentation code. The next implementation candidate
should not be a direct behavior-changing rule yet; first, the evidence should be
fed into an offline fitting dataset that can show whether same-target pressure or
cap problems repeat across archived logs and are actually avoidable.

## Pre-tuning diagnostic closeout

Before the next heuristic/rule PR, #39 evidence should be treated as report-only
input to offline fitting. Direct command-spend rows and available kill-size /
outcome hints can suggest candidate target-level aggregate salvo caps, but they
should not by themselves justify a behavior change. The actual allocator behavior
change remains a separate follow-up after archived-log replay identifies a
repeated, avoidable problem.

## Same-target controlled-command cap follow-up

The focused follow-up implements the first bounded rule from that evidence:
selected-group controlled command experiments now skip later eligible commands to
the same target with `targetAggregateControlledCommandCapReached` after the
experiment has already applied that target's assigned-shot budget. The change is
deliberately limited to the controlled selected-group command gate and does not
expand command scope or claim fleet-wide allocation readiness.

Fresh runtime smoke on `Player.log` written 2026-06-23 11:04 local confirmed the
new skip reason in a same-target selected-group case: after one direct Dragon
command, later eligible Dragon commands were skipped with
the target aggregate controlled-command cap. Older artifacts use the pre-rename
label `targetAggregateSalvoCapReached`; newly generated logs use
`targetAggregateControlledCommandCapReached`.

Issue #39.1 closes the fitting-readiness boundary around that smoke: commit
`92ebc65` is a controlled-command application and attribution guard, not an
actual missile expenditure cap. The fitting report now separates direct
controlled command spend from same-target none-correlated vanilla spillover
launches. Actual vanilla salvo suppression and selected-ship budget distribution
remain unresolved and belong to a later focused design before or during #43.

The report also separates applied-launcher post-budget spillover: a ship can
consume its direct controlled assigned-shot budget and later keep producing
same-target none-correlated `TryFire` rows. This is visible vanilla spillover
evidence, not exact causal expenditure attribution.

## Future combat outcome hook RE issue

A separate follow-up issue should investigate stable combat outcome hooks for
missile hit/intercept/damage/kill attribution. This is not an immediate blocker
for the #39 same-target controlled-command cap or selected-group heuristic work.
It belongs to the deeper measurement layer that becomes more valuable after #44
corpus/ledger infrastructure and before or alongside outcome-aware #43
fleet-wide evaluation.

Until that issue finds a stable hook, `DestroyShip` text remains a conservative
post-direct-launch outcome hint rather than exact projectile, command, or kill
attribution.
