# Issue #44 context — Experiment corpus and parameter ledger

Updated: 2026-06-24
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_44/00-context.md`

## Current status

Issue #44 is the next infrastructure step after the Issue #6 selected-scope controlled allocation slice was integrated into `develop` through PR #50.

Current branch context when this file was written:

```text
branch: Issue_6_later
HEAD: f6785da13ab5e37c9887cdc4f1b116e2893989af
worktree: clean before this file was created
```

The relevant roadmap order is now:

```text
#6 selected-scope controlled allocation / fitting-readiness slice
  -> #39 / #39.1 controlled evidence interpretation and spillover diagnostics
  -> #44 experiment corpus and parameter ledger
  -> #43 fleet-wide controlled missile allocation path
```

Treat #44 as data infrastructure for future fitting loops. It should make repeated fitting auditable, comparable, and reproducible across batches without treating shadow replay as causal proof of combat effectiveness.

## Why #44 exists

The #6/#39/#39.1 work made selected-scope controlled allocation observable enough to distinguish:

- controlled command application;
- direct command-spend attribution;
- selected-scope safety skips;
- same-target controlled-command cap skips;
- skipped-launcher vanilla spillover;
- applied-launcher post-budget vanilla spillover;
- conservative `DestroyShip` outcome hints.

However, those reports are still batch-local. If future tuning loops optimize one log batch at a time and discard parameter provenance, they can overfit scenario quirks, lose evidence about regressions, or confuse shadow replay with controlled live validation.

Issue #44 should introduce a repo-local corpus layer that records what was run, with which heuristic/parameter snapshot, against which scenario, in which evidence mode, and with what reviewer verdict.

## Source-of-truth issue scope

GitHub Issue #44 is titled:

```text
Experiment corpus and parameter ledger for fitting loops
```

Its goal is to create a repo-local experiment corpus and parameter ledger so live/shadow fitting evidence accumulates globally across batches instead of being optimized batch-by-batch and discarded.

Core principle:

```text
shadow replay = candidate filter + regression check
controlled live = causal evidence source for combat-behavior improvement
```

Do not collapse those evidence types into one score.

## Relationship to nearby issues

- #6 supplies the selected-scope controlled command path and live evidence envelope.
- #24 supplies log-only fitting and shadow replay sanity checks.
- #39 / #39.1 supply command-spend attribution, controlled-command cap diagnostics, and spillover separation.
- #43 should consume #44's corpus layer before fleet-wide tuning expands beyond selected-group experiments.
- #47 should later improve measurement quality through combat outcome hook RE.
- #48 should later investigate actual vanilla salvo suppression / selected-ship budget distribution.

## Scope boundary

Allowed work in #44:

- define a lightweight repo-local corpus format;
- define a durable experiment registry, likely JSONL;
- define parameter snapshot schema for heuristic/rule settings;
- define scenario metadata schema;
- add small parser/report wrapper tooling to ingest experiment artifacts;
- add corpus-level summary output;
- keep shadow replay and controlled live evidence separated;
- support manual verdict capture without a database;
- document how future fitting loops add batches without overwriting previous evidence.

Non-goals:

- do not implement #43 fleet-wide controlled allocation;
- do not broaden live command application scope;
- do not implement vanilla salvo suppression or selected-ship budget distribution;
- do not tune allocator parameters except for fixture-only examples needed to validate plumbing;
- do not automate game launch, save loading, battle setup, ship selection, or battle execution;
- do not require a server, external database, or cloud service;
- do not build a polished analytics UI;
- do not commit private raw `Player.log` files unless a later explicit policy says otherwise;
- do not treat `DestroyShip` text as exact projectile/command kill attribution.

## Evidence model to preserve

Every corpus entry should make evidence mode explicit.

Suggested `runMode` values:

```text
shadow-replay
controlled-live
fleet-wide-controlled   # real bounded fleet-wide live evidence from #43.2+
fixture                  # synthetic tooling validation only, if needed
```

Evidence interpretation:

```text
fixture = schema/tooling proof only
shadow-replay = regression check and candidate filter
controlled-live = causal command-behavior evidence
fleet-wide-controlled = expanded bounded fleet-wide live evidence class
```

Reports must not aggregate these as equivalent proof. Corpus summaries may show them side by side, but they should retain separate counts and verdicts.

## Suggested repo-local layout

Issue #44 proposes this approximate layout:

```text
artifacts/
  experiments/
    registry.jsonl
    live/
      EXP-.../
        metadata.json
        parameters.json
        raw-log.txt
        parsed.json
        report.md
        verdict.json
    shadow/
      EXP-.../
        metadata.json
        parameters.json
        parsed.json
        report.md
        verdict.json
  fitting/
    corpus-summary.json
    candidate-comparison.csv
    scenario-breakdown.md
```

Implementation can adjust paths, but must preserve:

- durable run identity;
- parameter provenance;
- source artifact references;
- evidence mode separation;
- manual verdict capture;
- corpus-level aggregation.

Recommended refinement before implementation:

```text
artifacts/experiments/registry.jsonl        # local/generated, likely ignored
artifacts/experiments/<mode>/<experimentId>/...
dev-docs/plan/issue_44/                    # temporary planning docs only
docs/diagnostics/experiment-corpus.md       # durable user-facing/spec doc
```

Decide early which generated artifact paths are ignored and which schema docs or fixtures are committed.

## Minimum registry entry fields

A registry entry should be append-friendly and durable enough to interpret old runs after heuristic defaults change.

Suggested fields:

```json
{
  "schemaVersion": 1,
  "experimentId": "EXP-...",
  "timestampUtc": "2026-06-23T00:00:00Z",
  "runMode": "controlled-live",
  "sourceLogPath": "artifacts/combat-logs/.../Player.log",
  "reportPath": "artifacts/shadow-fitting/.../shadow-fitting-report.md",
  "parsedPath": "artifacts/experiments/live/EXP-.../parsed.json",
  "metadataPath": "artifacts/experiments/live/EXP-.../metadata.json",
  "parametersPath": "artifacts/experiments/live/EXP-.../parameters.json",
  "verdictPath": "artifacts/experiments/live/EXP-.../verdict.json",
  "gameVersion": null,
  "modCommit": "f6785da13ab5e37c9887cdc4f1b116e2893989af",
  "heuristicCandidateId": "baseline-selected-scope-v1",
  "parameterSnapshotHash": "sha256:...",
  "scenarioTags": ["selected-group", "same-target-cap", "vanilla-spillover"],
  "verdict": "needs-live-validation",
  "notes": "Private raw logs are local-only unless explicitly committed."
}
```

The exact schema can change, but the first implementation should avoid fields that require unavailable game internals.

## Parameter snapshot schema

A parameter snapshot should capture every allocator setting that affects allocation interpretation, even if the current issue does not tune it.

Suggested categories:

- target value weights;
- PD risk scaling / capability evidence mode;
- launch-window thresholds and score weights;
- kill/saturation package sizing settings;
- partial saturation thresholds;
- target aggregate controlled-command cap behavior;
- selected-scope command safety toggles;
- recommendation-only / live-apply settings;
- named rule toggles that affect allocation or report classification.

Important rule:

```text
Do not rely on current defaults alone.
Store the actual parameter snapshot used for each run.
```

## Scenario metadata schema

Scenario metadata should be coarse but useful for corpus aggregation.

Suggested fields:

- selected mode: `selected-single-ship`, `selected-group`, `fleet-wide`, `shadow-only`, `fixture`;
- selected ship names and count when visible;
- friendly missile ship count when visible;
- enemy ship count when visible;
- launcher/weapon count when visible;
- missile profile or weapon family when visible;
- target names / target ids when visible;
- rough PD evidence category;
- range band / closing-speed band when available;
- command gate outcome summary;
- direct command-spend evidence summary;
- skipped command summary;
- vanilla spillover summary;
- conservative outcome hint summary;
- known missing evidence;
- freeform reviewer notes.

Avoid requiring exact hit/intercept/kill attribution until #47 finds a stable hook.

## Manual verdict model

Manual verdict capture must not require editing parser code.

Suggested verdict values:

```text
good
bad
ambiguous
safety-blocked
evidence-limited
needs-live-validation
regression-suspected
fixture-only
```

Suggested `verdict.json`:

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

## Corpus summary output

The first summary command should be boring and file-based. It can be added to an existing tool or a new small script.

Possible command names:

```powershell
python tools\summarize_experiment_corpus.py --registry artifacts\experiments\registry.jsonl --output artifacts\fitting\corpus-summary
```

or:

```powershell
python tools\fit_shadow_allocation.py --corpus artifacts\experiments\registry.jsonl --output artifacts\fitting\corpus-summary
```

Choose the simpler implementation after inspecting existing tool structure.

Minimum summary outputs:

- total experiments by run mode;
- verdict counts;
- scenario tag counts;
- parameter candidate counts;
- missing evidence counts;
- skipped/failed command counts when available;
- overkill / under-saturation / target mismatch summaries when present;
- vanilla spillover summaries when present;
- evidence gaps and next live-validation candidates.

## Suggested implementation phases

### Phase 1 — Schema and docs

- Add durable documentation, likely `docs/diagnostics/experiment-corpus.md`.
- Define registry, metadata, parameter snapshot, verdict, and summary semantics.
- State explicitly that private raw logs are not committed by default.

### Phase 2 — Minimal tooling

- Add a small script or wrapper that can:
  - read a registry JSONL;
  - validate required fields;
  - summarize mode/verdict/scenario counts;
  - report broken artifact links without failing catastrophically.

### Phase 3 — Seed fixtures / example entries

- Add synthetic or redacted fixture entries, not private live logs.
- Include examples for:
  - fixture-only;
  - shadow-replay;
  - controlled-live metadata without raw private log;
  - recommendation-only blocked run;
  - same-target controlled-command cap with vanilla spillover.

### Phase 4 — Integrate with existing reports

- Add optional output hooks from `fit_shadow_allocation.py` or a wrapper to produce corpus-ready metadata.
- Keep existing parser/fitter behavior stable.

### Phase 5 — Handoff to #43

- Ensure #43 can ask: “Which parameter candidate is globally best across the corpus, and which evidence gaps still require live validation?”

## Files to inspect first

Start with:

- `tools/fit_shadow_allocation.py`
- `tools/parse_player_log.py`
- `tools/fixtures/`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/planning/mvp-roadmap.md`
- `dev-docs/plan/issue_39/00-context.md`
- `dev-docs/plan/issue_39.1/00-context.md`

Likely new files:

- `dev-docs/plan/issue_44/00-context.md` — this file
- `docs/diagnostics/experiment-corpus.md`
- `tools/summarize_experiment_corpus.py` or similar
- `tools/fixtures/experiment_corpus/` examples, if practical

## Validation commands

Baseline commands from nearby issues:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\parse_player_log.py tools\fit_shadow_allocation.py
python -m compileall tools
```

If a new corpus tool is added, extend validation with something like:

```powershell
python tools\summarize_experiment_corpus.py --registry tools\fixtures\experiment_corpus\registry.jsonl --output artifacts\fitting\corpus-summary-fixture
```

## Completion criteria for this plan context

This context is sufficient when the next worker understands:

- #44 follows the integrated #6/#39 fitting-readiness work;
- #44 is infrastructure, not allocator behavior tuning;
- shadow replay and controlled live evidence must stay separated;
- parameter snapshots are required so old runs remain interpretable after defaults change;
- private raw logs should not be committed by default;
- the first implementation should be lightweight, file-based, and compatible with existing parser/fitting tools;
- #43 should consume corpus summaries before expanding to fleet-wide controlled allocation.
