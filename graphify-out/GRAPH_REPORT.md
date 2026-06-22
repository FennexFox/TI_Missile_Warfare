# Graph Report - .  (2026-06-22)

## Corpus Check
- 27 files · ~24,552 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 152 nodes · 193 edges · 24 communities (11 shown, 13 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Launch Scoring|Launch Scoring]]
- [[_COMMUNITY_Diagnostics Pipeline|Diagnostics Pipeline]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Allocation Core|Allocation Core]]
- [[_COMMUNITY_Diagnostics Pipeline|Diagnostics Pipeline]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Diagnostics Pipeline|Diagnostics Pipeline]]
- [[_COMMUNITY_Diagnostics Pipeline|Diagnostics Pipeline]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Allocation Core|Allocation Core]]
- [[_COMMUNITY_Allocation Core|Allocation Core]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Allocation Core|Allocation Core]]
- [[_COMMUNITY_Allocation Core|Allocation Core]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Missile Models|Missile Models]]
- [[_COMMUNITY_Development Docs README|Development Docs README]]
- [[_COMMUNITY_Plan Docs README|Plan Docs README]]

## God Nodes (most connected - your core abstractions)
1. `GameObjectReader` - 19 edges
2. `Log` - 10 edges
3. `Main` - 9 edges
4. `TargetValueCalculator` - 7 edges
5. `PatchBootstrap` - 7 edges
6. `PDScoreCalculator` - 6 edges
7. `SalvoPackageCalculator` - 5 edges
8. `LaunchWindowEvaluator` - 4 edges
9. `ModEntry` - 4 edges
10. `ModSettings` - 4 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (24 total, 13 thin omitted)

### Community 0 - "Launch Scoring"
Cohesion: 0.19
Nodes (5): GameObjectReader, MissileFireControl.Mod.Adapters, BindingFlags, Type, Vector3d

### Community 1 - "Diagnostics Pipeline"
Cohesion: 0.26
Nodes (6): Exception, Log, MissileFireControl.Mod, object, bool, ModEntry

### Community 2 - "Missile Models"
Cohesion: 0.23
Nodes (5): Harmony, Main, MissileFireControl.Mod, bool, ModEntry

### Community 3 - "Allocation Core"
Cohesion: 0.25
Nodes (7): MissileFireControl.Core.Calculators, SalvoPackageCalculator, SalvoPackage, SalvoPackageOptions, HullClass, MissileProfile, ShipSnapshot

### Community 4 - "Diagnostics Pipeline"
Cohesion: 0.25
Nodes (6): MissileFireControl.Core.Calculators, TargetValueCalculator, HullClass, PDScoreCalculator, ShipSnapshot, TargetValueOptions

### Community 5 - "Missile Models"
Cohesion: 0.29
Nodes (5): MissileFireControl.Mod.Patches, PatchBootstrap, bool, Harmony, Type

### Community 6 - "Diagnostics Pipeline"
Cohesion: 0.31
Nodes (5): MissileFireControl.Core.Calculators, PDScoreCalculator, PdScoringOptions, IEnumerable, ShipSnapshot

### Community 7 - "Diagnostics Pipeline"
Cohesion: 0.25
Nodes (6): LaunchWindowEvaluator, MissileFireControl.Core.Calculators, LaunchWindowOptions, LaunchWindowResult, MissileProfile, ShipSnapshot

### Community 8 - "Missile Models"
Cohesion: 0.29
Nodes (5): double, MissileFireControl.Mod, ModSettings, bool, ModEntry

### Community 9 - "Missile Models"
Cohesion: 0.48
Nodes (6): Distance(), Dot(), Length(), MissileFireControl.Core.Models, Normalized(), Vector3d

### Community 10 - "Missile Models"
Cohesion: 0.50
Nodes (3): CombatLaunchPatchPlaceholder, MissileFireControl.Mod.Patches, string

## Knowledge Gaps
- **56 isolated node(s):** `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation`, `TargetAllocation`, `MissileFireControl.Core.Calculators` (+51 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation` to the rest of the system?**
  _56 weakly-connected nodes found - possible documentation gaps or missing edges._