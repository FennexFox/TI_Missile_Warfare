# Issue #56 implementation summary

Updated: 2026-06-29

## Scope completed

This slice adds the first saturation-aware bounded-live target distribution
heuristic. It remains inside the explicit fleet-wide bounded-live apply path and
does not change vanilla salvo behavior, projectile physics, missile guidance,
cooldowns, ammo accounting, or broad command-authority policy.

The v1 pressure policy is:

```text
pressureReference = max(killSize, saturationSize)
decisionPressure = prior controlled assigned shots + exact recovered in-flight pressure
```

Lower-bound in-flight pressure is logged and summarized, but it is diagnostic
only for v1 and does not contribute to decision pressure or trigger retargeting
by itself.

When the selected target is already at or above the pressure reference, the
bounded-live path looks for a same-cycle visible hostile alternative with
comparable allocator feature evidence, runtime target evidence, a useful
allocator package, and under-threshold controlled/exact pressure. If found, the
command candidate is retargeted to the best under-threshold alternative by
diagnostic target score.

## Diagnostics added

Bounded-live candidate/result rows now include pressure decision fields:

```text
boundedLivePressureDecision
boundedLivePressureDecisionReason
boundedLivePressureReference
boundedLivePressureThreshold
boundedLiveDecisionPressure
boundedLiveDecisionPressureAtOrAboveThreshold
boundedLiveDecisionPriorControlledShots
boundedLiveDecisionExactInFlightShots
boundedLiveDecisionLowerBoundInFlightShots
boundedLiveDecisionInFlightEvidenceQuality
boundedLiveOriginalTargetId
boundedLiveOriginalTarget
boundedLiveRetargetedToTargetId
boundedLiveRetargetedToTarget
boundedLiveSelectedTargetScore
boundedLiveRetargetedTargetScore
boundedLiveDecisionTargetAlternativeDenominator
```

Parser and corpus summaries now expose:

- pressure decision and reason counts;
- retained vs retargeted above-threshold decisions;
- exact/lower-bound/unknown decision pressure evidence buckets;
- lower-bound diagnostic-only rows.

## Fixture coverage

New synthetic fixtures:

- `tools/fixtures/fleet_wide_bounded_live_pressure_retarget.txt`
- `tools/fixtures/fleet_wide_bounded_live_pressure_lower_bound.txt`

The retarget fixture demonstrates one retained below-threshold command followed
by one above-threshold retarget. The lower-bound fixture demonstrates that
lower-bound in-flight pressure is counted but does not create an above-threshold
retarget.

## Validation

Passed:

```text
dotnet build TI_Missile_Fire_Control.sln
python -m py_compile tools\parse_player_log.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py
python -m ruff check tools\parse_player_log.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py
python tools\parse_player_log.py tools\fixtures\fleet_wide_bounded_live_pressure_retarget.txt
python tools\parse_player_log.py tools\fixtures\fleet_wide_bounded_live_pressure_lower_bound.txt
python tools\import_player_log_experiments.py --log tools\fixtures\fleet_wide_bounded_live_pressure_retarget.txt --output artifacts\experiments\issue_56_retarget_fixture --parameters tools\fixtures\experiment_corpus\baseline-fleet-wide-bounded-live-v1.parameters.json --heuristic-candidate-id baseline-fleet-wide-bounded-live-v1 --run-mode fleet-wide-controlled --scenario-tag issue-56 --verdict evidence-limited --mod-commit fixture --fixture --force
python tools\import_player_log_experiments.py --log tools\fixtures\fleet_wide_bounded_live_pressure_lower_bound.txt --output artifacts\experiments\issue_56_lower_bound_fixture --parameters tools\fixtures\experiment_corpus\baseline-fleet-wide-bounded-live-v1.parameters.json --heuristic-candidate-id baseline-fleet-wide-bounded-live-v1 --run-mode fleet-wide-controlled --scenario-tag issue-56 --verdict evidence-limited --mod-commit fixture --fixture --force
python tools\summarize_experiment_corpus.py --registry artifacts\experiments\issue_56_retarget_fixture\registry.jsonl --output artifacts\fitting\issue_56_retarget_fixture_summary
python tools\summarize_experiment_corpus.py --registry artifacts\experiments\issue_56_lower_bound_fixture\registry.jsonl --output artifacts\fitting\issue_56_lower_bound_fixture_summary
python tools\parse_player_log.py <private Terra Invicta Player.log>
python tools\import_player_log_experiments.py --log <private Terra Invicta Player.log> --output artifacts\experiments\issue_56_runtime_playerlog_20260628 --parameters tools\fixtures\experiment_corpus\baseline-fleet-wide-bounded-live-v1.parameters.json --heuristic-candidate-id baseline-fleet-wide-bounded-live-v1 --run-mode fleet-wide-controlled --scenario-tag issue-56 --scenario-tag bounded-live --scenario-tag real-runtime-validation --verdict good --mod-commit e2524fdd91fdc673a73968b704f2146479e69249 --force
python tools\summarize_experiment_corpus.py --registry artifacts\experiments\issue_56_runtime_playerlog_20260628\registry.jsonl --output artifacts\fitting\issue_56_runtime_playerlog_20260628_summary
```

Fresh runtime validation passed on a real `Player.log` captured from
`fleetwide-bounded-live-20260628T113733931Z-1`. The raw log remains private and
uncommitted; the importer omitted `sourceLogPath` from the local registry.

Generated local artifacts:

- `artifacts\experiments\issue_56_runtime_playerlog_20260628\registry.jsonl`
- `artifacts\fitting\issue_56_runtime_playerlog_20260628_summary\corpus-summary.json`
- `artifacts\fitting\issue_56_runtime_playerlog_20260628_summary\scenario-breakdown.md`

Real-log corpus result:

- `boundedLiveAppliedResults`: 3
- `boundedLiveRetargetedDecisionsAboveThreshold`: 2
- `boundedLiveRetainedSelectedTargetDecisionsAboveThreshold`: 0
- `boundedLiveLowerBoundPressureDiagnosticOnlyRows`: 1
- `boundedLivePressureDecisionExactInFlightRows`: 2
- `boundedLivePressureDecisionLowerBoundInFlightRows`: 1
- `boundedLivePressureDecisionUnknownInFlightRows`: 0
- `boundedLiveAppliedWithTargetAlternativeDenominatorGtOne`: 3
- `failed_command_counts`: none
- parser verdict: `OK`

The two retargeted applied rows used exact recovered in-flight target pressure
and moved above-threshold selected-target pressure from `Dragon` to `Seraph`
and then to `Corona`. The retained lower-bound row stayed below the pressure
threshold and remained diagnostic-only, as intended for v1.

A filtered scan of non-structured MissileWarfare/MFC log lines found no
warnings, errors, or exceptions. The remaining outcome-evaluation limitation is
still exact hit/damage/kill attribution, which is handed off to #47.
