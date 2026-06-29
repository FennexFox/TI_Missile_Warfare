# Tuning loop context

## Goal

- Establish the first bounded-live tuning loop as pressure-aware tuning.
- Define the objective, guardrails, corpus baseline requirements, and first
  narrow parameter family before changing heuristics.

## Scope

- Planning and review criteria for bounded fleet-wide controlled runs.
- Metrics that can already be summarized from `AllocationLog` and imported
  experiment corpus artifacts.
- Use `[OutcomeLog]` rows only as runtime validation context for outcome-hook
  coverage.

## Non-goals

- Outcome-aware scoring or allocator reward/punishment.
- Broad target-value, launch-window, or point-defense weight retuning.
- Vanilla salvo suppression.
- Command-authority expansion or selected/fleet scope policy changes.
- Projectile guidance, burn-model, or physics changes.

## First loop mode

The first tuning loop is pressure-aware bounded-live tuning.

The objective function must come from controlled allocation pressure evidence:

- controlled prior pressure on the selected target;
- recovered exact in-flight target pressure;
- `killSize` and `saturationSize`;
- same-cycle target alternatives and comparable target feature evidence;
- retarget/retain counters from bounded-live pressure decision rows.

`[OutcomeLog]` rows are validation context for the separate outcome hook layer.
They confirm that outcome diagnostics are installed and firing, but they are not
the primary objective function for this loop. Do not join outcome rows back to
allocation rows or use them to reward/punish candidate choices until a separate
outcome-to-allocation correlation design exists.

## Objective

Reduce repeated same-target over-pressure in bounded-live controlled allocation
without widening command authority or changing combat behavior outside the
existing bounded controlled command path.

Minimum signals:

- reduce retained selected-target decisions where controlled pressure plus
  exact recovered in-flight pressure is at or above the pressure reference;
- reduce repeated same-target commands when viable same-cycle alternatives
  exist;
- keep lower-bound in-flight pressure rows diagnostic-only for v1;
- preserve direct controlled command-spend evidence separately from vanilla or
  none-correlated spillover.

## Guardrails

The tuning loop must preserve these constraints:

- no command-authority expansion;
- no selected-scope or fleet-scope policy changes;
- preserve per-ship caps and command safety gates;
- preserve ammo accounting and manual-control behavior;
- same-team and scope-violation markers remain zero;
- parser verdict remains OK;
- `MissileWarfare` warnings and errors remain zero;
- do not treat `DestroyShip` text or `shipDestroyed` rows as unique projectile
  attribution;
- do not treat vanilla or none-correlated launch rows as direct controlled
  command spend.

## First parameter family

Start with a narrow pressure threshold and retarget-preference family:

- pressure reference: `max(killSize, saturationSize)`;
- initial threshold multiplier: `1.0`;
- pressure source for decisions: prior controlled shots plus exact recovered
  in-flight shots only;
- lower-bound in-flight pressure: logged and summarized, but diagnostic-only;
- retarget preference: when selected-target pressure is at or above threshold,
  prefer the best viable same-cycle under-threshold alternative;
- viable alternative: target denominator is greater than one, runtime target
  evidence is available, and target-alternative feature evidence is comparable.

Defer these knobs until a later loop:

- broad target-value weight changes;
- broad launch-window score changes;
- point-defense scoring retune;
- outcome-based reward or punishment;
- vanilla salvo suppression;
- command-scope broadening.

## Corpus baseline requirement

Before changing heuristics, import and summarize enough bounded-live evidence to
avoid tuning from one anecdotal combat run.

Evidence buckets:

- post-#56 bounded-live pressure-aware runs;
- the #47 runtime-confirmed log as outcome-hook validation context only;
- existing #43.3/#43.4 bounded-live corpus entries;
- private raw logs remain local under ignored `artifacts/` paths unless a
  redacted fixture policy is explicitly chosen.

Expected local artifact pattern:

```text
artifacts/
  experiments/
    tuning-loop-baseline/
      registry.jsonl
      EXP-.../
  fitting/
    tuning-loop-baseline-summary/
```

Use `tools/import_player_log_experiments.py` for local `Player.log` imports and
`tools/summarize_experiment_corpus.py` for corpus summaries. Omit
`sourceLogPath` from committed artifacts unless the log is synthetic or safely
redacted.

## Baseline metrics

Record at least these counters before and after each tuning change:

- bounded-live applied results;
- applied rows with target alternative denominator greater than one;
- applied rows with comparable target-alternative features;
- applied rows with fully comparable score/rank evidence;
- applied rows with exact prior in-flight pressure;
- applied rows with lower-bound prior in-flight pressure;
- retained selected-target decisions above threshold;
- retargeted decisions above threshold;
- lower-bound pressure diagnostic-only rows;
- applied/skipped/failed command counts;
- direct controlled command correlation counts;
- vanilla or none-correlated spillover counts;
- same-team target markers;
- scope-violation markers;
- parser warnings and errors.

## Follow-up boundary

Outcome-aware tuning requires a separate correlation plan. That plan must define
join keys, conservative confidence levels, vanilla/none-correlated spillover
handling, multiple controlled launches into the same target window, and the rule
that `shipDestroyed` killer/weapon evidence without a unique projectile id is
not exact projectile attribution.

The current pressure-aware loop may reference outcome-hook runtime health, but
it must not perform outcome-to-allocation joins.
