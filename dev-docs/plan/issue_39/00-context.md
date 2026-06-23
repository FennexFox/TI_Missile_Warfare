# Issue #39 context — Heuristic tuning from controlled evidence

Updated: 2026-06-23
Repo: `FennexFox/TI_Missile_Warfare`
Local path: `dev-docs/plan/issue_39/00-context.md`

## Current status

Issue #39 was accidentally closed earlier and has been reopened. Treat it as the immediate next step after #38, before the new corpus/ledger infrastructure issue #44 and before fleet-wide expansion #43.

Current intended order:

```text
#38 small selected-group controlled experiment report
  -> #39 bounded heuristic tuning / no-tuning decision from controlled evidence
  -> #44 experiment corpus and parameter ledger for future fitting loops
  -> #43 fleet-wide controlled missile allocation path
```

## Why #39 still comes before #44

#39 closes the first selected-group learning loop from #6. It should consume the controlled experiment evidence produced by #38 and decide whether there is enough evidence to make one bounded heuristic/rule-family change.

#44 exists because later repeated fitting needs durable parameter provenance and global corpus aggregation. That is important, but it should not block the first #39 decision unless #39 discovers that the current evidence cannot be interpreted without a ledger.

In other words:

- #39 answers: "Did the #38 controlled evidence justify one specific heuristic/rule-family change, or should we explicitly decline tuning for now?"
- #44 answers: "How do we prevent future batches from becoming isolated, untraceable, or overfit?"
- #43 answers: "How do we safely expand from selected-group allocation to fleet-wide allocation?"

## Inputs to inspect first

Use the GitHub issue bodies as source-of-truth scope:

- #6 — controlled allocation experiment and fitting loop.
- #24 — shadow allocation log-only fitting pass. Closed; useful as a pre-live sanity baseline, not proof of real combat effectiveness.
- #38 — small selected-group controlled experiment report. Closed; should provide the controlled evidence input for #39.
- #39 — heuristic tuning from controlled evidence. Open/reopened; current target issue.
- #44 — experiment corpus and parameter ledger. Open; follow-up data infrastructure for later repeated fitting.
- #43 — fleet-wide controlled missile allocation path. Open; should come after #39 and ideally after #44.

Repo-local references likely worth inspecting:

- `tools/fit_shadow_allocation.py`
- `tools/parse_player_log.py`
- `src/MissileFireControl.Core/Allocation/SalvoAllocator.cs`
- `src/MissileFireControl.Core/Calculators/PDScoreCalculator.cs`
- `src/MissileFireControl.Core/Calculators/SalvoPackageCalculator.cs`
- `src/MissileFireControl.Core/Calculators/TargetValueCalculator.cs`
- `src/MissileFireControl.Core/Calculators/LaunchWindowEvaluator.cs`
- `docs/diagnostics/runtime-validation-history.md`
- `docs/diagnostics/snapshot-and-allocation.md`
- `docs/planning/mvp-roadmap.md`

## Scope boundary for this issue

Do exactly one of these:

1. Make one bounded heuristic/rule/parameter-family change justified by #38 controlled evidence; or
2. Explicitly document that no tuning is justified yet and identify the next evidence needed.

Allowed candidate families include at most one of:

- target value weighting;
- PD risk scaling;
- launch-window score weighting;
- kill/saturation salvo sizing margin;
- partial saturation threshold;
- parser/report expectation updates needed to make the controlled evidence interpretable.

Do not tune multiple unrelated knobs in this issue.

## Evidence rules

Controlled live evidence is the only source that can justify causal tuning in #39. Shadow replay and old/fresh log-only fitting remain useful for regression checks and sanity checks, but they cannot prove combat improvement.

Interpretation rule:

```text
shadow/log replay = candidate filter + regression check + evidence-gap detector
controlled live report = causal evidence source for #39 tuning
```

If the #38 report shows an allocator mismatch but the evidence is ambiguous, prefer documenting a no-tuning decision and naming the missing evidence over guessing a parameter change.

Do not claim full-fleet readiness from #39. The maximum readiness conclusion is one of:

- selected-group evidence supports one bounded heuristic change and #44/#43 can proceed;
- selected-group evidence supports no change yet, but #43 planning can proceed cautiously after #44 infrastructure;
- more #38-style selected-group evidence is needed;
- a named blocker prevents #43.

## Relationship to #44

Do not implement the full #44 corpus/ledger in #39.

However, #39 should leave a clean handoff for #44 by recording, in durable docs or report output where practical:

- the controlled experiment id / run id used for the tuning decision;
- source log or artifact path;
- heuristic/rule family considered;
- before/after parameter values if a change is made;
- before/after classification summary;
- whether the evidence came from controlled live results, shadow replay, or both;
- known evidence gaps and manual verdict.

If a small local note or report field is needed to preserve parameter provenance for the single #39 change, it is acceptable. A general registry, JSONL corpus, scenario taxonomy, or candidate-comparison workflow belongs to #44.

## Non-goals

- Do not add new live command behavior.
- Do not broaden live command scope.
- Do not command unselected ships.
- Do not implement fleet-wide allocation.
- Do not implement the #44 corpus/ledger infrastructure except for minimal handoff notes.
- Do not treat shadow replay as proof of combat effectiveness.
- Do not tune multiple independent heuristic families.
- Do not claim final full-fleet readiness.

## Suggested implementation flow

1. Locate the #38 controlled experiment report and any generated parser/fitting artifacts.
2. Summarize the observed selected-group behavior:
   - allocator intent;
   - applied/skipped/failed command counts;
   - assigned/spent missile evidence when visible;
   - target assignment mismatches;
   - overkill / under-saturation / partial saturation evidence;
   - missing target identity, ammo, PD, or launch-window evidence.
3. Identify at most one candidate heuristic/rule family to change.
4. Decide whether the evidence justifies changing it.
5. If changing it, make a minimal bounded change and update tests/fixtures/docs as needed.
6. If not changing it, document the no-tuning decision and required next evidence.
7. Re-run synthetic, old-log, fresh-log, and controlled-experiment fitting/report validation.
8. Record before/after classification impact and limitations.
9. Add a handoff note stating whether the next step is #44, #43, more #38-style evidence, or a named blocker.

## Validation commands

Use the issue validation commands as the baseline:

```powershell
dotnet build TI_Missile_Fire_Control.sln
python tools\check_layout.py
python -m ruff check tools\fit_shadow_allocation.py tools\parse_player_log.py
python -m compileall tools
python tools\fit_shadow_allocation.py --input tools\fixtures --output artifacts\shadow-fitting\heuristic_tuning_synthetic
python tools\fit_shadow_allocation.py --input artifacts\combat-logs\selected --output artifacts\shadow-fitting\heuristic_tuning_selected
python tools\fit_shadow_allocation.py --input <controlled-experiment-log-dir> --output artifacts\shadow-fitting\heuristic_tuning_controlled
```

If exact artifact directories differ, document the actual paths used.

## Completion criteria for local planning

This context file is complete enough when the next worker understands:

- #39 is open/reopened and comes after #38;
- #44 is a follow-up infrastructure issue, not a prerequisite for the first #39 decision;
- #39 must make at most one heuristic/rule-family change or explicitly decline tuning;
- controlled live evidence is required for causal tuning;
- shadow fitting only filters candidates and checks regressions;
- #39 must hand off to #44/#43 with clear readiness, limitations, and blockers.
