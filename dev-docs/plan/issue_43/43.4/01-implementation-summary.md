# Issue #43.4 implementation summary

Updated: 2026-06-28

## Scope completed

This slice adds measurement-readiness diagnostics and corpus tooling for bounded
fleet-wide live apply. It does not change allocator scoring, shot allocation,
live command caps, vanilla salvo behavior, projectile behavior, or outcome
attribution hooks.

Runtime bounded-live candidate/result rows now preserve:

- real same-cycle visible-hostile target denominator fields from
  `FleetWideScopeEvidence`;
- compact bounded target alternative identity lists with explicit truncation;
- allocator decision fields available from `TargetAllocation`;
- selected target `scorePerShot` as `selectedTargetScore` with
  `selectedTargetScoreBasis="scorePerShot"`;
- conservative saturation/kill overcommit ratios based on controlled assigned
  shots already applied in the bounded-live experiment;
- explicit hard measurement blockers separated from external #47/#48 blockers.

Parser/importer/corpus tooling now preserves these fields into per-experiment
`summary.json` artifacts and aggregates #43.4 readiness counters into
`corpus-summary.json`.

## Evidence limits preserved

The implementation intentionally separates blockers:

Hard #43.4 measurement blockers that should not be treated as terminal closure
state:

- alternative target comparable score/features;
- prior allocator and in-flight missile shot pressure when unavailable;
- cap blocked-vs-applied score comparison.

External blockers that may remain explicit handoffs:

- exact target survival/destruction attribution pending #47;
- vanilla salvo suppression / selected-ship distribution pending #48.

## Validation

Passed:

```text
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m compileall tools
python -m ruff check tools\parse_player_log.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py
python tools\parse_player_log.py tools\fixtures\fleet_wide_bounded_live_apply.txt
python tools\parse_player_log.py tools\fixtures\fleet_wide_bounded_live_apply.txt --json
python tools\import_player_log_experiments.py --log tools\fixtures\fleet_wide_bounded_live_apply.txt --output artifacts\experiments\issue_43_4_fixture --parameters tools\fixtures\experiment_corpus\baseline-fleet-wide-bounded-live-v1.parameters.json --heuristic-candidate-id baseline-fleet-wide-bounded-live-v1 --run-mode fleet-wide-controlled --scenario-tag issue-43.4 --verdict evidence-limited --mod-commit fixture --fixture --force
python tools\summarize_experiment_corpus.py --registry artifacts\experiments\issue_43_4_fixture\registry.jsonl --output artifacts\fitting\issue_43_4_fixture_summary
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
git diff --check
```

Generated artifacts remain under ignored `artifacts/` paths.
