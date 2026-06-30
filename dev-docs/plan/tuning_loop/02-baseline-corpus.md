# Baseline corpus snapshot

Status: absorbed into `dev-docs/plan/issue_60/`. This file is retained as
historical input and is not the active implementation plan.

## Goal

- Record the first local pressure-aware bounded-live corpus refresh before any
  heuristic tuning.
- Keep raw logs and generated corpus artifacts private under ignored
  `artifacts/` paths.

## Source log

- Raw log: `%USERPROFILE%\AppData\LocalLow\Pavonis Interactive\TerraInvicta\Player.log`
- Raw log modified: 2026-06-29 14:38:06 local time
- Raw log status: private/local, not committed
- Baseline commit: `a60a2f40d27985ed5403bb113cf566ed85e681dd`

## Parser health

`python tools\parse_player_log.py <Player.log> --require-launchlogs` reported:

- diagnostics bootstrap: `patched=7`, `skipped=0`;
- `LaunchLog` entries: 894, with no sequence gaps or duplicates;
- controlled command launch correlation: 25
  `directRuntimeContext` rows and 95 `none` rows;
- `SnapshotLog` entries: 120;
- `OutcomeLog` entries: 221 across all four outcome source hooks;
- `AllocationLog` entries: 260;
- bounded fleet-wide live experiment:
  `fleetwide-bounded-live-20260629T053623952Z-1`;
- bounded fleet-wide live results: 3 applied, 8 skipped;
- skipped reason: `fleetWideBoundedLivePerShipCapBlocked`;
- bounded-live pressure decisions above threshold: 0 retained, 10 retargeted;
- `MissileWarfare` issues: none;
- parser verdict: OK.

Outcome rows are validation context only for this tuning loop. They are not
joined back to allocation rows.

## Import artifacts

Generated ignored artifacts:

- `artifacts/experiments/tuning-loop-baseline/registry.jsonl`
- `artifacts/experiments/tuning-loop-baseline/fleetwide-bounded-live-20260629t053623952z-1/`
- `artifacts/fitting/tuning-loop-baseline-summary/corpus-summary.json`
- `artifacts/fitting/tuning-loop-baseline-summary/scenario-breakdown.md`
- `artifacts/fitting/tuning-loop-baseline-summary/candidate-comparison.csv`

Import command:

```powershell
python tools\import_player_log_experiments.py `
  --log "$env:USERPROFILE\AppData\LocalLow\Pavonis Interactive\TerraInvicta\Player.log" `
  --output artifacts\experiments\tuning-loop-baseline `
  --parameters tools\fixtures\experiment_corpus\baseline-fleet-wide-bounded-live-v1.parameters.json `
  --heuristic-candidate-id baseline-fleet-wide-bounded-live-v1 `
  --run-mode fleet-wide-controlled `
  --scenario-tag bounded-live `
  --scenario-tag pressure-aware `
  --scenario-tag tuning-loop-baseline `
  --mod-commit a60a2f40d27985ed5403bb113cf566ed85e681dd `
  --force
```

Summary command:

```powershell
python tools\summarize_experiment_corpus.py `
  --registry artifacts\experiments\tuning-loop-baseline\registry.jsonl `
  --output artifacts\fitting\tuning-loop-baseline-summary
```

## Corpus summary

The generated corpus summary contains one `fleet-wide-controlled` experiment:

- experiment id:
  `EXP-IMPORTED-FLEETWIDE-BOUNDED-LIVE-20260629T053623952Z-1`;
- source experiment id:
  `fleetwide-bounded-live-20260629T053623952Z-1`;
- heuristic candidate: `baseline-fleet-wide-bounded-live-v1`;
- verdict: `evidence-limited`;
- selected mode: `fleet-wide`;
- PD evidence category: `observedTemplateCapability`;
- known missing evidence:
  `source Player.log path omitted from registry`.

Direct command-spend evidence:

- `directRuntimeContext launch rows`: 25;
- `fleet-wide bounded live applied command results`: 3;
- skipped commands: `fleetWideBoundedLivePerShipCapBlocked`: 8;
- failed command counts: none;
- vanilla spillover counts: none.

Bounded-live tuning readiness counters:

- `boundedLiveAppliedResults`: 3;
- `boundedLiveAppliedWithTargetAlternativeDenominatorGtOne`: 3;
- `boundedLiveAppliedWithComparableAlternativeFeatures`: 3;
- `boundedLiveAppliedWithFullyComparableScoreRankEvidence`: 3;
- `boundedLiveAppliedWithKnownPriorInFlightPressure`: 2;
- `boundedLiveAppliedWithLowerBoundPriorInFlightPressure`: 1;
- `boundedLivePressureDecisionExactInFlightRows`: 2;
- `boundedLivePressureDecisionLowerBoundInFlightRows`: 1;
- `boundedLiveLowerBoundPressureDiagnosticOnlyRows`: 1;
- `boundedLiveRetainedSelectedTargetDecisionsAboveThreshold`: 0;
- `boundedLiveRetargetedDecisionsAboveThreshold`: 1.

Blockers:

- hard measurement blocker:
  `prior in-flight target attribution unavailable for observed live missiles`: 1;
- external outcome blocker:
  `exact outcome attribution pending OutcomeLog correlation`: 3.

## Interpretation

This snapshot is suitable as a local baseline input for the first
pressure-aware loop, but it remains a single combat run and is
`evidence-limited`. Use it with the existing #43.4/#56 ignored corpus artifacts
for comparison, not as sole proof of tuning quality.

The first heuristic change should still stay inside the documented pressure
threshold / retarget-preference family from `00-context.md`.
