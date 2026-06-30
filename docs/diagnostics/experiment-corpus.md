# Experiment corpus and parameter ledger

Issue #44 adds a repo-local corpus format for fitting experiments. The corpus is
an audit layer, not a combat automation layer: it records what was run, which
parameter snapshot produced the evidence, which scenario it represents, and how
a reviewer judged the result.

The evidence rule is strict:

- `shadow-replay` is a candidate filter and regression check.
- `controlled-live` is the causal evidence source for selected-scope controlled command behavior.
- `fleet-wide-controlled` is the causal evidence source for bounded fleet-wide controlled command behavior; use it only for real live runs with bounded fleet-wide command application, not report-only rows.
- `fixture` proves schema and tooling behavior only.

Summaries may show these modes side by side, but they must not collapse them
into one proof score.

## Offline fitting boundary

The corpus is also the input layer for the archived-log offline fitting loop. In
that loop, committed or local summaries may be converted into allocation
decision-context datasets and replayed through candidate policies outside the
game.

Offline fitting is a candidate filter, not live proof. It may rank candidates,
find repeated allocator-quality patterns, and identify which candidates deserve
controlled-live or fleet-wide-controlled validation. It must not collapse
`shadow-replay`, `controlled-live`, `fleet-wide-controlled`, and `fixture` rows
into one causal score.

A fitting-ready decision context should preserve per-candidate target evidence,
not only aggregate run counters. For pressure-aware fitting, retained
above-threshold rows must expose enough per-alternative pressure and threshold
evidence to audit reasons such as `noUnderThresholdAlternative`.

As of #43.2, `fleet-wide-controlled` is no longer only a future placeholder. A valid entry should still separate direct controlled command spend from vanilla / none-correlated spillover and should state whether command-result correlation such as `controlledCommandCorrelation="directRuntimeContext"` was observed.

## Local layout

Generated and private experiment artifacts stay under ignored `artifacts/`
paths:

```text
artifacts/
  experiments/
    registry.jsonl
    live/EXP-.../
    shadow/EXP-.../
  fitting/
    corpus-summary/
```

Committed examples live under `tools/fixtures/experiment_corpus/`. Those files
are synthetic or redacted and are not real combat evidence.

## Registry JSONL

The registry is append-friendly JSONL: one JSON object per experiment. Paths are
repo-relative unless absolute.

Required fields:

- `schemaVersion`: currently `1`.
- `experimentId`: durable run id, such as `EXP-20260623-0001`.
- `timestampUtc`: ISO-8601 UTC timestamp when known.
- `runMode`: `fixture`, `shadow-replay`, `controlled-live`, or
  `fleet-wide-controlled`.
- `heuristicCandidateId`: named candidate or baseline identifier.
- `parametersPath`: parameter snapshot JSON path.
- `parameterSnapshotHash`: `sha256:<hex>` hash of `parametersPath`.
- `metadataPath`: scenario metadata JSON path.
- `verdictPath`: reviewer verdict JSON path.
- `scenarioTags`: coarse tags for grouping and later regression checks.

Common optional fields:

- `sourceLogPath`: local raw log path. Omit it for private logs that are not
  committed.
- `parsedPath`: parser or fitting summary JSON path.
- `reportPath`: generated Markdown report path.
- `gameVersion`: game version when visible.
- `modCommit`: mod commit or build id when visible.
- `verdict`: cached verdict for quick registry scans.
- `notes`: short reviewer or provenance note.

## Parameter snapshot

Parameter snapshots are immutable run provenance. They must store the actual
settings used for the run, not just "current defaults." At minimum they should
cover categories that can affect allocation interpretation:

- target value weights;
- point-defense risk scaling and evidence mode;
- launch-window thresholds and score weights;
- kill and saturation package sizing;
- partial saturation thresholds;
- target aggregate controlled-command cap behavior;
- selected-scope command safety toggles;
- recommendation-only and live-apply settings;
- named rule toggles.

When defaults change, create a new snapshot and candidate id instead of
retroactively changing old experiment meaning.

Direct command-spend summaries should use `direct_command_spend_counts` in parsed or metadata evidence summaries. For #43.2+ `fleet-wide-controlled` runs, include applied command-result counts and direct runtime launch correlation counts when available.

For #43.4 bounded-live measurement summaries, preserve score/rank comparison
space instead of collapsing the fields into one score. `selectedTargetScore` is
the launcher/candidate allocation score; `targetAlternativeScores` are
diagnostic target-level comparable scores; `selectedTargetRank` is target-level
and ranks the selected target inside `targetAlternativeScores`. Corpus
readiness counters should separate fully comparable score/rank evidence from
partial or ambiguous score-space evidence.

Prior in-flight missile pressure must also distinguish exact target counts from
lower-bound evidence. `selectedTargetPriorMissileInFlightEstimate=0` is fully
known only when no live missiles were observed or all observed missile target ids
were recovered. If observed live missiles have unknown targets, the estimate is
a lower-bound target-attribution-limited value and remains a #43.4 measurement
blocker. For #43.4+, active missile controller sources
(`GameControl.spaceCombat._projectiles` / `_reverseProjectiles`) are the
target-attribution source; `liveMissiles` is count-only fallback evidence.

For #56 bounded-live pressure-aware measurement, corpus summaries also preserve
pressure-decision counters. `boundedLiveRetargetedDecisionsAboveThreshold`
counts applied commands where prior controlled pressure plus exact recovered
in-flight pressure reached `max(killSize, saturationSize)` and the command was
retargeted to a same-cycle alternative.
`boundedLiveRetainedSelectedTargetDecisionsAboveThreshold` counts rows that
stayed on an above-threshold selected target. Lower-bound pressure is counted
separately by `boundedLivePressureDecisionLowerBoundInFlightRows` and
`boundedLiveLowerBoundPressureDiagnosticOnlyRows`; those rows should not be
treated as pressure-triggered retargets in v1. These counters are measurement
signals for offline fitting, not proof that the current behavior is a validated
tuning improvement.

## Scenario metadata

Scenario metadata is intentionally coarse. Use fields that are visible and
reviewable:

- `selectedMode`: `selected-single-ship`, `selected-group`, `fleet-wide`,
  `shadow-only`, or `fixture`.
- selected ship names and count when visible;
- friendly missile ship count, enemy ship count, and launcher count when
  visible;
- missile family or weapon family when visible;
- target names or ids when visible;
- point-defense evidence category;
- range or closing-speed band when available;
- command gate, direct command-spend, skipped command, vanilla spillover, and
  conservative outcome summaries;
- known missing evidence;
- reviewer notes.

Do not require exact hit, intercept, damage, or kill attribution until a later
stable outcome hook is found.

## Manual verdict

Manual verdicts live in a separate JSON file so reviewers do not edit parser or
summary code.

Allowed verdict values:

- `good`
- `bad`
- `ambiguous`
- `safety-blocked`
- `evidence-limited`
- `needs-live-validation`
- `regression-suspected`
- `fixture-only`

Example:

```json
{
  "schemaVersion": 1,
  "verdict": "evidence-limited",
  "reviewer": "FennexFox",
  "reviewedAtUtc": "2026-06-23T00:00:00Z",
  "summary": "Controlled command spend is direct, but vanilla spillover remains.",
  "evidenceGaps": ["exact kill attribution", "vanilla salvo suppression"],
  "nextAction": "Add to corpus; do not tune from this run alone."
}
```

## Player.log import workflow

Use `tools/import_player_log_experiments.py` to turn one `Player.log` into one or more local corpus artifact drafts grouped by diagnostics `experimentId`. This is an experiment-level importer, not a full battle-boundary splitter.

Example for a bounded fleet-wide live run:

```powershell
python tools\import_player_log_experiments.py `
  --log Player.log `
  --output artifacts\experiments\fleet-wide-import `
  --parameters tools\fixtures\experiment_corpus\baseline-fleet-wide-bounded-live-v1.parameters.json `
  --heuristic-candidate-id baseline-fleet-wide-bounded-live-v1 `
  --scenario-tag issue-43.3 `
  --scenario-tag bounded-live `
  --mod-commit <commit-sha>
```

The importer writes, per source `experimentId`:

- `summary.json`
- `metadata.json`
- `verdict.json`

and writes a registry at `<output>/registry.jsonl` unless `--registry` is supplied. By default it omits `sourceLogPath` so private raw `Player.log` files are not recorded in committed corpus entries. Use `--include-source-log-path` only for private/local registries where that path is safe.

Useful validation flow:

```powershell
python tools\import_player_log_experiments.py --log Player.log --output artifacts\experiments\fleet-wide-import --parameters tools\fixtures\experiment_corpus\baseline-fleet-wide-bounded-live-v1.parameters.json --heuristic-candidate-id baseline-fleet-wide-bounded-live-v1 --scenario-tag issue-43.3
python tools\summarize_experiment_corpus.py --registry artifacts\experiments\fleet-wide-import\registry.jsonl --output artifacts\fitting\fleet-wide-import-summary
```

If a `Player.log` contains several experiments, the importer emits one artifact directory per `experimentId`. Full battle-level splitting is still future work.

Because the importer groups primary evidence rows by `experimentId`, raw `SnapshotLog` context is not attached yet. However, after battle segmentation it can attach nearby `AllocationLog recordType="cycle"` rows when they share the same detected battle segment and `cycleId` within `--context-line-window` lines. Generated metadata records attached rows under `nearbyContext`, sets `pdEvidenceCategorySource` to `same-battle-same-cycle-context` when PD evidence is recovered that way, and keeps `pd evidence context not attached by experimentId importer` as missing evidence only when no direct or attached PD context is available.

The importer is battle-aware before it performs any same-cycle context attachment. It first tries to detect battle segments from vanilla combat lifecycle markers such as `Init Canvas SpaceCombatCanvas`, `Adding ship to CombatManager as ActiveShip(CreateShip)`, `MaxShipsInCombat`, `FLTS: Combat End Triggered`, and `Combat Will End`. If those markers are absent, it falls back to `AllocationLog recordType="cycle" battle="..."` markers when present. Generated artifacts record `sourceBattleId`, boundary line numbers, boundary source, battle segment confidence, and a `battleSegmentBreakdown` that separates allocation rows from launch/runtime rows by detected battle segment. Context attachment is row-local: each allocation row can attach only `AllocationLog recordType="cycle"` context with the same detected battle segment and `cycleId`. If allocation rows span multiple detected segments, that is recorded separately from launch/runtime context spanning multiple segments.

## Summary workflow

Run the file-based summary command from the repo root:

```powershell
python tools\summarize_experiment_corpus.py --registry artifacts\experiments\registry.jsonl --output artifacts\fitting\corpus-summary
```

Fixture validation uses:

```powershell
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
```

The command writes:

- `corpus-summary.json`: machine-readable aggregate counts and validation
  warnings.
- `candidate-comparison.csv`: candidate rows split by run mode.
- `scenario-breakdown.md`: human-readable scenario and evidence-mode summary.

The summarizer reads optional fitting `summary.json` artifacts when `parsedPath`
points to them. When fields are present, it aggregates missing evidence,
skipped and failed commands, overkill risk, under-saturation risk, target
mismatch, regression markers, and vanilla spillover diagnostics. Missing private
raw logs are allowed when `sourceLogPath` is omitted.

## Offline-fitting decision contexts

Use `tools/build_offline_fitting_dataset.py` to turn a fixed experiment-corpus
registry into allocation decision-context rows for offline replay. This is the
row-level input to the archived-log fitting loop; it is not a scoring or live
behavior command.

Fixture validation uses:

```powershell
python tools\build_offline_fitting_dataset.py --registry tools\fixtures\offline_fitting\registry.jsonl --output artifacts\offline-fitting\fixture-dataset --require-row-evidence --force
```

The command writes:

- `decision-contexts.jsonl`: one allocation decision-context row per replayable
  command candidate/result.
- `decision-contexts.json`: the same rows wrapped in a JSON object.
- `dataset-summary.json`: row counts, source record types, pressure evidence
  counts, command-result counts, and non-fatal warnings.

Rows preserve normalized replay fields and a `rawFields` copy of the diagnostic
pairs. Target alternatives remain a list derived from the pipe-delimited
`targetAlternative*` diagnostics. Score/rank fields keep their original
comparison-space names. Exact and lower-bound pressure remain separate through
the `pressure`, `uncertainty`, and `replayReadiness` groups.

Registry entries without `sourceLogPath` are treated as summary-only evidence:
the command records a warning and does not invent row-level contexts from
aggregate counters. Keep generated datasets under ignored `artifacts/` paths.
