# Graph Report - .  (2026-06-29)

## Corpus Check
- 22 files · ~51,165 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 125 nodes · 161 edges · 21 communities (9 shown, 12 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Game Object Reader|Game Object Reader]]
- [[_COMMUNITY_Mod Logging|Mod Logging]]
- [[_COMMUNITY_Salvo Package Calculation|Salvo Package Calculation]]
- [[_COMMUNITY_Target Value Calculation|Target Value Calculation]]
- [[_COMMUNITY_Point Defense Scoring|Point Defense Scoring]]
- [[_COMMUNITY_Launch Window Evaluation|Launch Window Evaluation]]
- [[_COMMUNITY_Vector Math Model|Vector Math Model]]
- [[_COMMUNITY_Agent Guidance|Agent Guidance]]
- [[_COMMUNITY_Allocation Request Model|Allocation Request Model]]
- [[_COMMUNITY_Target Allocation Model|Target Allocation Model]]
- [[_COMMUNITY_Launch Window Options|Launch Window Options]]
- [[_COMMUNITY_Launch Window Result|Launch Window Result]]
- [[_COMMUNITY_PD Scoring Options|PD Scoring Options]]
- [[_COMMUNITY_Salvo Package Model|Salvo Package Model]]
- [[_COMMUNITY_Salvo Package Options|Salvo Package Options]]
- [[_COMMUNITY_Target Value Options|Target Value Options]]
- [[_COMMUNITY_Command Scope Concepts|Command Scope Concepts]]
- [[_COMMUNITY_Missile Profile Model|Missile Profile Model]]
- [[_COMMUNITY_Combat Patch Placeholder|Combat Patch Placeholder]]
- [[_COMMUNITY_Hull Class Model|Hull Class Model]]
- [[_COMMUNITY_Weapon Role Model|Weapon Role Model]]

## God Nodes (most connected - your core abstractions)
1. `GameObjectReader` - 19 edges
2. `Log` - 10 edges
3. `TargetValueCalculator` - 7 edges
4. `PDScoreCalculator` - 6 edges
5. `SalvoPackageCalculator` - 5 edges
6. `LaunchWindowEvaluator` - 4 edges
7. `ShipSnapshot` - 3 edges
8. `Length()` - 3 edges
9. `Normalized()` - 3 edges
10. `Vector3d` - 3 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Durable reading path** — docs_readme, agent_index, agent_current_state, agent_workflow, planning_mvp_roadmap [INFERRED 0.85]

## Communities (21 total, 12 thin omitted)

### Community 0 - "Game Object Reader"
Cohesion: 0.19
Nodes (5): GameObjectReader, MissileFireControl.Mod.Adapters, BindingFlags, Type, Vector3d

### Community 1 - "Mod Logging"
Cohesion: 0.26
Nodes (6): Exception, Log, MissileFireControl.Mod, object, bool, ModEntry

### Community 2 - "Salvo Package Calculation"
Cohesion: 0.25
Nodes (7): MissileFireControl.Core.Calculators, SalvoPackageCalculator, SalvoPackage, SalvoPackageOptions, HullClass, MissileProfile, ShipSnapshot

### Community 3 - "Target Value Calculation"
Cohesion: 0.25
Nodes (6): MissileFireControl.Core.Calculators, TargetValueCalculator, HullClass, PDScoreCalculator, ShipSnapshot, TargetValueOptions

### Community 4 - "Point Defense Scoring"
Cohesion: 0.31
Nodes (5): MissileFireControl.Core.Calculators, PDScoreCalculator, PdScoringOptions, IEnumerable, ShipSnapshot

### Community 5 - "Launch Window Evaluation"
Cohesion: 0.25
Nodes (6): LaunchWindowEvaluator, MissileFireControl.Core.Calculators, LaunchWindowOptions, LaunchWindowResult, MissileProfile, ShipSnapshot

### Community 6 - "Vector Math Model"
Cohesion: 0.48
Nodes (6): Distance(), Dot(), Length(), MissileFireControl.Core.Models, Normalized(), Vector3d

### Community 7 - "Agent Guidance"
Cohesion: 1.00
Nodes (3): AGENTS, Diagnostics-first posture, Thin game integration

### Community 16 - "Command Scope Concepts"
Cohesion: 1.00
Nodes (3): Selected Command Scope, Selected-Player Command Scope, Vanilla Salvo Command Granularity

## Knowledge Gaps
- **45 isolated node(s):** `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation`, `TargetAllocation`, `MissileFireControl.Core.Calculators` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation` to the rest of the system?**
  _45 weakly-connected nodes found - possible documentation gaps or missing edges._