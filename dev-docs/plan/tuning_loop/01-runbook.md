# Tuning loop runbook

## Goal

- Make each bounded-live pressure-aware tuning attempt repeatable and
  comparable.
- Keep baseline capture, heuristic changes, follow-up capture, and verdicts in
  separate reviewable steps.

## Preconditions

- Tuning-loop context is current in `00-context.md`.
- The working tree baseline commit is recorded.
- Private raw logs remain under ignored `artifacts/` paths.
- Runtime settings and UMM toggles are recorded before each live run.
- No heuristic change is made until a baseline corpus summary exists.

## Baseline capture

1. Record the baseline commit:

   ```powershell
   git rev-parse HEAD
   git status --short
   ```

2. Record settings and toggles for the live run:

   ```text
   EnableDiagnostics
   EnableSnapshotDiagnostics
   EnableShadowAllocationDiagnostics
   AllowCommandApply
   EnableRecommendationOnlyMode
   bounded fleet-wide trigger used
   command caps
   selected/fleet scope visible at runtime
   ```

3. Import the bounded-live `Player.log` into ignored local artifacts:

   ```powershell
   python tools\import_player_log_experiments.py `
     --log <private Player.log> `
     --output artifacts\experiments\tuning-loop-baseline `
     --parameters tools\fixtures\experiment_corpus\baseline-fleet-wide-bounded-live-v1.parameters.json `
     --heuristic-candidate-id baseline-fleet-wide-bounded-live-v1 `
     --run-mode fleet-wide-controlled `
     --scenario-tag bounded-live `
     --scenario-tag pressure-aware `
     --mod-commit <commit-sha> `
     --force
   ```

4. Summarize the imported baseline:

   ```powershell
   python tools\summarize_experiment_corpus.py `
     --registry artifacts\experiments\tuning-loop-baseline\registry.jsonl `
     --output artifacts\fitting\tuning-loop-baseline-summary
   ```

5. Record which raw logs are private and not committed.

## Tuning change

Apply exactly one narrow pressure-aware tuning change per loop.

Allowed first-loop change family:

- threshold behavior around `max(killSize, saturationSize)`;
- retarget preference once exact controlled pressure is at or above threshold;
- viable-alternative filtering using target denominator and comparable feature
  evidence.

Do not mix in broad allocator-weight changes, point-defense retunes,
outcome-aware scoring, vanilla salvo suppression, or command-scope changes.

## Follow-up capture

1. Record the follow-up commit or local diff identifier.
2. Run a comparable bounded-live combat scenario with the same documented
   toggles and caps unless the change explicitly requires a different value.
3. Import the follow-up log to a separate ignored artifact directory:

   ```powershell
   python tools\import_player_log_experiments.py `
     --log <private Player.log> `
     --output artifacts\experiments\tuning-loop-followup `
     --parameters <new parameter snapshot> `
     --heuristic-candidate-id <candidate-id> `
     --run-mode fleet-wide-controlled `
     --scenario-tag bounded-live `
     --scenario-tag pressure-aware `
     --mod-commit <commit-sha> `
     --force
   ```

4. Summarize the follow-up corpus:

   ```powershell
   python tools\summarize_experiment_corpus.py `
     --registry artifacts\experiments\tuning-loop-followup\registry.jsonl `
     --output artifacts\fitting\tuning-loop-followup-summary
   ```

## Comparison

Compare baseline and follow-up summaries using the metrics from `00-context.md`.
Record the comparison in the plan folder or in the issue notes before deciding
the next action.

Required comparison checks:

- retained selected-target decisions above threshold moved down, or a clear
  reason explains why not;
- retargeted decisions above threshold moved up only when viable alternatives
  existed;
- lower-bound pressure rows remain diagnostic-only;
- direct controlled command-spend evidence remains separate from vanilla or
  none-correlated spillover;
- same-team target and scope-violation markers remain zero;
- applied/skipped/failed command counts remain explainable;
- parser verdict remains OK;
- `MissileWarfare` warnings and errors remain zero;
- outcome-hook rows, when present, are used only as validation context.

## Verdict

Use one of these verdicts for each before/after comparison:

- `supportive`: metrics moved in the intended direction and guardrails held.
- `contradictory`: metrics moved against the objective or guardrails failed.
- `no material change`: metrics did not meaningfully move.
- `invalid comparison`: scenario, settings, caps, or evidence quality changed
  enough that the comparison is not valid.
- `inconclusive`: evidence is too sparse or too ambiguous to classify.

## Regression checks

For docs-only planning changes:

```powershell
python tools\check_layout.py
```

For parser/importer/corpus changes:

```powershell
python tools\check_layout.py
python -m compileall tools
python -m ruff check tools\check_layout.py tools\package_local.py tools\parse_player_log.py tools\fit_shadow_allocation.py tools\import_player_log_experiments.py tools\summarize_experiment_corpus.py
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
```

For mod or allocator changes:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m compileall tools
python tools\parse_player_log.py --require-launchlogs
```

Do not claim mod-load or in-game validation unless it was actually performed.
