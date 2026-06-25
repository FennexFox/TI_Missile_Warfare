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

Because the importer only groups rows carrying an `experimentId`, nearby `SnapshotLog` or untagged `cycle` context is not attached yet. If PD evidence is not present on the grouped rows, generated metadata keeps `pdEvidenceCategory` as `unknown` and records `pd evidence context not attached by experimentId importer` as missing evidence.

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
