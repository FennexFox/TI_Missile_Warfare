# Issue #43.3 corpus review conclusion — no tuning yet

Updated: 2026-06-24
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_43/43.3/01-corpus-review-conclusion.md`
Parent context: `dev-docs/plan/issue_43/43.3/00-context.md`

## Conclusion

Do not tune allocator parameters from the current #43 evidence yet.

#43.2 successfully proved bounded fleet-wide command authority and direct command-spend attribution for a small cap=3 live run. That is enough to close the command-authority proof slice and to represent `fleet-wide-controlled` evidence in the #44 corpus. It is not enough to justify allocator-quality tuning.

The next work should gather or improve evidence before changing allocation policy.

Recommended next owner:

```text
More bounded fleet-wide live evidence or measurement/spillover work before tuning.
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

## What this proves

The evidence is sufficient for these claims:

- the mod can issue bounded fleet-wide controlled commands under explicit player-triggered settings;
- the cap=3 global command limit and per-ship cap=1 behavior worked in the observed run;
- applied command results produced matching `directRuntimeContext` launch correlation rows;
- no same-team or scope-violation marker was observed in the reviewed run;
- the #44 corpus can represent `fleet-wide-controlled` evidence without committing private raw `Player.log` files;
- direct controlled command spend, skipped command reasons, and evidence limitations are visible as separate corpus counters.

## What this does not prove

The evidence is not sufficient for these claims:

- the allocator made better tactical target choices than vanilla or manual play;
- the chosen target was globally optimal across all hostile ships;
- overkill or under-saturation behavior is known across scenarios;
- vanilla / none-correlated spillover is fully quantified;
- exact hit, damage, or kill attribution is available;
- a parameter change would improve results outside this one runtime smoke.

The current `fleet-wide-controlled` entry is deliberately marked `evidence-limited`, not `good`, because it proves command authority and attribution, not allocator quality.

## Tuning decision

No allocator tuning should be made from this corpus state alone.

Reason:

```text
single clean bounded-live run
+ direct command-spend attribution
- cross-scenario comparison
- outcome attribution
- vanilla spillover quantification
= command-authority proof, not tuning evidence
```

Tuning may begin after at least one of these becomes true:

1. multiple `fleet-wide-controlled` live runs show the same allocator-quality failure pattern;
2. measurement work separates controlled spend, vanilla spillover, and conservative outcomes well enough to compare alternatives;
3. a narrow, repeated problem is visible in corpus summaries, such as target over-concentration, under-saturation, target-value mismatch, or cap-induced misallocation;
4. the proposed tuning change has a specific before/after metric and a regression check.

## Recommended next step

The next task should not be a broad tuning pass. It should be one of the following, in this order of preference:

1. collect 2-3 additional bounded fleet-wide live runs and add redacted/private corpus entries;
2. improve measurement if vanilla / none-correlated spillover or outcome attribution blocks interpretation;
3. open a narrow tuning issue only if the expanded corpus shows a repeated allocator-quality failure.

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
allocator tuning: deferred
next evidence need: more bounded-live runs or measurement/spillover separation
```

This closes the current #43.3 review question with a conservative no-tuning decision. The project can now choose whether to gather more fleet-wide evidence, improve measurement, or open a narrowly scoped tuning issue when enough repeated evidence exists.
