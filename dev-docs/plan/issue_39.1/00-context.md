# Issue #39.1 context — Fitting-ready closeout before #43

Updated: 2026-06-23
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_39.1/00-context.md`

## Purpose

Issue #39.1 is a local follow-up planning slice after Issue #39 and before the #43 fleet-wide controlled missile allocation path.

The purpose is not to solve all missile overfire. The purpose is to make the current selected-group evidence fitting-ready before #43 by clearly separating:

- controlled command application;
- direct command-spend attribution;
- skipped controlled commands;
- vanilla / none-correlated spillover launches;
- conservative target outcome hints;
- what can and cannot be inferred from the current logs.

This slice exists because the focused Issue #39 follow-up commit `92ebc65` showed that the new same-target cap is narrower than its first name implied: it can block duplicate controlled command application and attribution, but it does not suppress vanilla salvo launches from other selected ships.

## Current commit context

Relevant recent commits on branch `issue_39`:

```text
5330514 Close #39 pre-tuning diagnostics
92ebc65 Add target aggregate command cap
```

Observed state after `92ebc65`:

- `targetAggregateSalvoCapReached` can appear as the skip reason for later same-target controlled command candidates.
- The first same-target selected ship can receive the controlled command and produce `directRuntimeContext` launch rows.
- Later same-target selected ships can still launch missiles through vanilla / existing fire behavior with `controlledCommandCorrelation="none"` and `commandResultId="none"`.
- The first applied ship can also launch additional none-correlated shots after its assigned controlled shots are consumed.

Therefore, `92ebc65` should be treated as a controlled-command attribution guard, not as an actual missile expenditure cap.

## Key runtime observation to preserve

Latest Dragon selected-group smoke interpretation:

```text
Selected ships:
- Pharsalos#276
- El Alamein#278
- Kasserine Pass#279

Target:
- Dragon#281

Controlled result:
- Pharsalos#276 -> Dragon#281 appliedDecision, assignedShots=8
- El Alamein#278 -> Dragon#281 skippedDecision, reason=targetAggregateSalvoCapReached
- Kasserine Pass#279 -> Dragon#281 skippedDecision, reason=targetAggregateSalvoCapReached

Launch attribution:
- Pharsalos directRuntimeContext rows cover the assigned controlled shots.
- El Alamein and Kasserine Pass still produce same-target TryFire rows with controlledCommandCorrelation=none.
```

Interpretation:

```text
The controlled command cap worked.
Actual vanilla salvo suppression did not occur.
```

## Terminology correction

Current wording is potentially misleading:

```text
target aggregate command cap
```

More accurate wording:

```text
target aggregate controlled-command cap
```

or:

```text
duplicate controlled command attribution guard
```

If the skip reason is renamed before merge, prefer:

```text
targetAggregateControlledCommandCapReached
```

If the skip reason is kept for log continuity, every document and report section must state explicitly that it only gates controlled command application and does not suppress vanilla salvo launches.

## Scope boundary

Issue #39.1 should not implement fleet-wide allocation and should not claim actual overfire resolution.

Allowed work:

- clarify documentation and roadmap language around `92ebc65`;
- rename the skip reason if desired before merge;
- add report diagnostics that expose vanilla / none-correlated same-target spillover after a controlled skip;
- add fixtures or parser expectations for the spillover pattern;
- update #39 closeout criteria so #43 receives a fitting-ready evidence boundary.

Non-goals:

- do not claim `targetAggregateSalvoCapReached` prevents all missile launches;
- do not suppress vanilla salvo launches without a separate design and validation plan;
- do not implement selected-ship budget distribution in this slice;
- do not broaden command scope;
- do not command unselected ships;
- do not implement #43 fleet-wide behavior here.

## Required #39.1 report behavior

The fitting report should expose a dedicated diagnostic for controlled cap spillover.

Suggested section name:

```text
Controlled cap spillover diagnostics
```

The section should group by at least:

- `experimentId`;
- target id / target name;
- controlled applied command rows;
- controlled skipped rows with `targetAggregateSalvoCapReached` or renamed equivalent;
- same-target TryFire rows after the skip with `controlledCommandCorrelation="none"`;
- launcher id / launcher name for those none-correlated launches;
- conservative interpretation.

Example interpretation text:

```text
Controlled command cap prevented duplicate controlled command attribution, but same-target vanilla spillover launches remained visible from skipped selected ships.
```

This is the crucial fitting-ready distinction for #43: fitted heuristics must not confuse direct controlled command spend with vanilla spillover spend.

## Suggested implementation plan

1. Review `tools/fit_shadow_allocation.py` and `tools/parse_player_log.py` for current command-result and launch grouping.
2. Add a report-only spillover detector:
   - find controlled skipped rows for same target after a direct controlled apply;
   - find later same-target `TryFire` rows from skipped launchers with no command result id;
   - summarize those as vanilla spillover, not as controlled command spend.
3. Decide whether to rename the skip reason:
   - if renaming, update code, fixtures, parser expectations, docs, and report text;
   - if not renaming, add explicit terminology warnings in report and docs.
4. Update `dev-docs/plan/issue_39/01-no-tuning-decision.md`, `docs/diagnostics/runtime-validation-history.md`, and `docs/planning/mvp-roadmap.md` to reflect the narrower meaning of the cap.
5. Add or update fixtures that exercise:
   - one applied same-target controlled command;
   - later skipped same-target controlled command;
   - later same-target none-correlated vanilla TryFire from skipped launcher.
6. Regenerate the relevant Issue #39 fitting reports when possible.
7. Leave a clear handoff for #43 stating that actual vanilla salvo suppression or selected-ship budget distribution remains unresolved.

## Validation commands

Baseline commands:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
python -m compileall tools
```

Report regeneration targets should include the freshest Dragon smoke log when available. If the local controlled log directory does not exist, document that limitation and use available fixture/fresh-log paths.

## Completion criteria

Issue #39.1 is complete when the next worker can state all of the following without ambiguity:

- #39 direct command-spend attribution is available.
- `targetStateId` bridge works.
- `targetAggregateSalvoCapReached` or its renamed equivalent gates controlled command application only.
- Vanilla same-target spillover launches are detected and reported separately.
- Conservative `DestroyShip` lines remain outcome hints, not exact kill attribution.
- Actual vanilla salvo suppression / selected-ship distribution is out of scope and belongs to a later focused design before or during #43.

## Decision for #43 handoff

After #39.1, #43 should not assume that selected-group command caps reduce real missile expenditure by themselves. #43 should consume the report distinction between:

```text
controlled command spend
vs.
vanilla spillover spend
```

Any fleet-wide fitting loop must model or control both channels separately.
