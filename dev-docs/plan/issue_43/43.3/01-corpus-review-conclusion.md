# Issue #43.3 corpus review conclusion — no tuning yet

Updated: 2026-06-26
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.3/01-corpus-review-conclusion.md`
Parent context: `dev-docs/plan/issue_43/43.3/00-context.md`

## Conclusion

Do not tune allocator parameters from the current #43 evidence yet.

#43.2 successfully proved bounded fleet-wide command authority and direct command-spend attribution. #43.3 then expanded the local private corpus from a single cap=3 smoke into 8 real `fleet-wide-controlled` imported experiments from a newer `Player.log`. That is enough to close the evidence-collection prerequisite for bounded-live command authority and corpus representation. It still does not by itself justify allocator-quality tuning because outcome attribution, vanilla/runtime spillover interpretation, and repeated allocator-quality failure classification remain insufficient.

The next work should either analyze repeated allocator-quality failure patterns in the 8-run corpus or improve measurement before changing allocation policy.

Recommended next owner:

```text
Measurement/spillover review or a narrow corpus-backed tuning issue, but only if the 8-run corpus shows a repeated allocator-quality failure pattern.
```

## Evidence reviewed

The relevant #43.2 runtime smoke was documented in `docs/diagnostics/runtime-validation-history.md`:

```text
experimentId="fleetwide-bounded-live-20260624T125727207Z-1"
fleetWideBoundedLiveCandidate: 3
fleetWideBoundedLivePreState: 3
fleetWideBoundedLiveResult: 5
fleetWideBoundedLivePostState: 3
result="applied": 3
result="skipped": 2
failedCommands="0"
directRuntimeContext LaunchLog rows: 21
scopeViolation markers: 0
same-team markers: 0
```

Applied commands:

```text
Thapsus -> Volcano, 7 shots
Salamis -> Volcano, 7 shots
Cannae -> Volcano, 7 shots
```

The two skipped rows were expected per-ship cap blocks:

```text
reason="fleetWideBoundedLivePerShipCapBlocked"
```

The #44 corpus fixture layer now includes a redacted `fleet-wide-controlled` entry:

```text
experimentId="EXP-FLEET-WIDE-CONTROLLED-0001"
runMode="fleet-wide-controlled"
heuristicCandidateId="baseline-fleet-wide-bounded-live-v1"
verdict="evidence-limited"
```

Fixture corpus summary validation produced:

```text
experimentCount: 6
runModeCounts.fleet-wide-controlled: 1
warnings: []
```

For `fleet-wide-controlled`, the corpus summary preserves direct controlled spend separately:

```text
direct_command_spend_counts:
  directRuntimeContext launch rows: 21
  fleet-wide bounded live applied command results: 3
skipped_command_counts:
  fleetWideBoundedLivePerShipCapBlocked: 2
failed_command_counts: {}
vanilla_spillover_counts: {}
```

## 2026-06-26 expanded local corpus import

A later private `Player.log` import produced additional bounded fleet-wide live evidence under ignored local artifacts:

```text
registry: artifacts/experiments/bounded-live-playerlog-20260626/registry.jsonl
summary:  artifacts/fitting/bounded-live-playerlog-20260626-summary/corpus-summary.json
experimentCount: 8
runModeCounts.fleet-wide-controlled: 8
warnings: []
```

Aggregate direct evidence:

```text
directRuntimeContext launch rows: 167
fleet-wide bounded live applied command results: 24
failed command results: 0
pdEvidenceCategory: observedTemplateCapability for 8/8 experiments
```

The importer now excludes placeholder `experimentId` values such as `none`, records row-level battle segment provenance, emits `battleSegmentBreakdown`, and attaches nearby PD context row-locally by `(battleSegmentId, cycleId)`.

Battle/window provenance findings from the expanded import:

```text
Z-5: AllocationLog rows all in BATTLE-0001; LaunchLog/runtime context spans BATTLE-0001..0004.
Z-6: AllocationLog rows all in BATTLE-0001; LaunchLog/runtime context spans BATTLE-0001, BATTLE-0002, BATTLE-0004.
Z-7: BATTLE-0001 has one skipped/noAllocatorAllocation row; applied commands and LaunchLog rows are in BATTLE-0002.
```

Final aggregate missing-evidence counters after deduplication:

```text
source Player.log path omitted from registry: 8
launch runtime context spans multiple detected battle segments: 2
allocation rows span multiple detected battle segments: 1
```

These limitations describe provenance and interpretation risk, not command-application failure.

## What this proves

The evidence is sufficient for these claims:

- the mod can issue bounded fleet-wide controlled commands under explicit player-triggered settings;
- the bounded-live command path repeatedly produced applied command results with `failedCommands` remaining zero in the imported corpus;
- applied command results produced matching `directRuntimeContext` launch correlation rows;
- no same-team or scope-violation marker was observed in the reviewed summaries;
- the #44 corpus can represent `fleet-wide-controlled` evidence without committing private raw `Player.log` files;
- direct controlled command spend, skipped command reasons, battle/window provenance, and evidence limitations are visible as separate corpus counters.

## What this does not prove

The evidence is not sufficient for these claims:

- the allocator made better tactical target choices than vanilla or manual play;
- the chosen target was globally optimal across all hostile ships;
- overkill or under-saturation behavior is known across scenarios;
- vanilla / none-correlated spillover is fully quantified;
- exact hit, damage, or kill attribution is available;
- a parameter change would improve results outside the reviewed command-authority corpus.

The current `fleet-wide-controlled` entry is deliberately marked `evidence-limited`, not `good`, because it proves command authority and attribution, not allocator quality.

## Tuning decision

No allocator tuning should be made from this corpus state alone.

Reason:

```text
8 real bounded-live imported experiments
+ 24 applied command results
+ 167 directRuntimeContext launch rows
+ row-local PD context recovery
- exact outcome attribution
- full vanilla/runtime spillover interpretation
- repeated allocator-quality failure classification
= strong command-authority/corpus evidence, not yet tuning evidence
```

Tuning may begin after at least one of these becomes true:

1. multiple `fleet-wide-controlled` live runs show the same allocator-quality failure pattern;
2. measurement work separates controlled spend, vanilla spillover, and conservative outcomes well enough to compare alternatives;
3. a narrow, repeated problem is visible in corpus summaries, such as target over-concentration, under-saturation, target-value mismatch, or cap-induced misallocation;
4. the proposed tuning change has a specific before/after metric and a regression check.

## Recommended next step

The earlier first recommendation, collecting 2-3 additional bounded fleet-wide live runs, is complete for local/private evidence. The next task should not be a broad tuning pass. It should be one of the following, in this order of preference:

1. inspect the 8-run corpus for a repeated allocator-quality failure pattern, especially over-concentration, under-saturation, target-value mismatch, or cap-induced misallocation;
2. improve measurement if vanilla/runtime spillover, combat-window provenance, or outcome attribution blocks interpretation;
3. open a narrow tuning issue only if the expanded corpus shows a repeated allocator-quality failure.

Implementation support now exists for recurring imports: use `tools/import_player_log_experiments.py` to group `Player.log` rows by diagnostics `experimentId` and generate local `summary.json`, `metadata.json`, `verdict.json`, and `registry.jsonl` drafts under ignored `artifacts/experiments/...` paths. The importer is battle-aware enough for experiment review: it reports `battleSegmentBreakdown`, separates allocation rows from launch/runtime rows, excludes placeholder experiment ids, and attaches same-battle/same-cycle context row-locally.

Suggested future tuning issue title, once evidence supports it:

```text
Tune fleet-wide target over-concentration guard
```

That issue should require a corpus-backed pattern before changing allocator behavior.

## Handoff

#43.3 should hand off with this state:

```text
#43.2 command authority: proven
fleet-wide-controlled corpus representation: proven
additional bounded-live evidence collection: complete for local/private corpus review
allocator tuning: deferred
next evidence need: repeated allocator-quality failure analysis or measurement/spillover separation
```

This closes the current #43.3 review question with a conservative no-tuning decision. The project can now choose whether to analyze the expanded corpus for a narrow repeated failure pattern, improve measurement, or open a narrowly scoped tuning issue when enough repeated evidence exists.
