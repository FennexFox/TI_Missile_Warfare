## #43.3 corpus update — bounded fleet-wide live evidence imported

I expanded the local #43.3 corpus review from the earlier single bounded-live smoke into a newer private `Player.log` import.

Local/private artifacts:

```text
artifacts/experiments/bounded-live-playerlog-20260626/
artifacts/fitting/bounded-live-playerlog-20260626-summary/
```

Raw `Player.log` remains uncommitted by policy.

### Import result

```text
experimentCount: 8
runModeCounts.fleet-wide-controlled: 8
warnings: []
directRuntimeContext launch rows: 167
fleet-wide bounded live applied command results: 24
failed command results: 0
pdEvidenceCategory: observedTemplateCapability for 8/8 experiments
```

The previous bogus `EXP-IMPORTED-NONE` artifact is fixed by excluding placeholder experiment ids such as `none` and `unknown`.

### Importer improvements

`tools/import_player_log_experiments.py` now:

- detects battle segments before context attachment;
- stores row-level `battleSegmentId` for `AllocationLog` and `LaunchLog` rows;
- emits `battleSegmentBreakdown` in `summary.json` and `metadata.json`;
- separates allocation-row multi-segment provenance from launch/runtime multi-segment provenance;
- attaches nearby PD context row-locally by `(battleSegmentId, cycleId)`;
- avoids double-counting battle provenance limitations in corpus summaries.

### Battle/window provenance findings

```text
Z-5: AllocationLog rows are all in BATTLE-0001; LaunchLog/runtime context spans BATTLE-0001..0004.
Z-6: AllocationLog rows are all in BATTLE-0001; LaunchLog/runtime context spans BATTLE-0001, BATTLE-0002, BATTLE-0004.
Z-7: BATTLE-0001 has one skipped/noAllocatorAllocation row; applied commands and LaunchLog rows are in BATTLE-0002.
```

Final aggregate provenance limitations after deduplication:

```text
source Player.log path omitted from registry: 8
launch runtime context spans multiple detected battle segments: 2
allocation rows span multiple detected battle segments: 1
```

### #43.3 conclusion

The earlier next step, “collect 2-3 additional bounded fleet-wide live runs and add them to the corpus,” is satisfied for local/private evidence: we now have 8 real `fleet-wide-controlled` imported experiments.

I still do **not** think broad allocator tuning is justified from this alone. The corpus now strongly supports command authority, direct spend attribution, and importer/corpus representation. The next decision should be one of:

1. inspect the 8-run corpus for a repeated allocator-quality failure pattern;
2. improve measurement if vanilla/runtime spillover, combat-window provenance, or outcome attribution blocks interpretation;
3. open a narrow tuning issue only if a repeated failure pattern is visible.

Recommended status: close or mark #43.3 evidence-collection/importer work as complete, but defer allocator tuning to a narrower follow-up issue if the corpus review identifies a specific repeated failure.
