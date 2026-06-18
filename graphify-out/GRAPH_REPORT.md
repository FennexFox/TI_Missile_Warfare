# Graph Report - .  (2026-06-18)

## Corpus Check
- Corpus is ~7,000 words - fits in a single context window. You may not need a graph.

## Summary
- 197 nodes · 207 edges · 35 communities (14 shown, 21 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Documentation Roadmap|Documentation Roadmap]]
- [[_COMMUNITY_Salvo Allocation Core|Salvo Allocation Core]]
- [[_COMMUNITY_Mod Entry Settings|Mod Entry Settings]]
- [[_COMMUNITY_Salvo Package Sizing|Salvo Package Sizing]]
- [[_COMMUNITY_Target Value Scoring|Target Value Scoring]]
- [[_COMMUNITY_Point Defense Scoring|Point Defense Scoring]]
- [[_COMMUNITY_Launch Window Logic|Launch Window Logic]]
- [[_COMMUNITY_Mod Settings Persistence|Mod Settings Persistence]]
- [[_COMMUNITY_Logging Utilities|Logging Utilities]]
- [[_COMMUNITY_Project Build Files|Project Build Files]]
- [[_COMMUNITY_Vector Math Model|Vector Math Model]]
- [[_COMMUNITY_Decision Logging Sink|Decision Logging Sink]]
- [[_COMMUNITY_Combat Patch Placeholder|Combat Patch Placeholder]]
- [[_COMMUNITY_Allocation Request Model|Allocation Request Model]]
- [[_COMMUNITY_Allocation Result Model|Allocation Result Model]]
- [[_COMMUNITY_Target Allocation Model|Target Allocation Model]]
- [[_COMMUNITY_Launch Options Model|Launch Options Model]]
- [[_COMMUNITY_Launch Result Model|Launch Result Model]]
- [[_COMMUNITY_PD Options Model|PD Options Model]]
- [[_COMMUNITY_Salvo Package Model|Salvo Package Model]]
- [[_COMMUNITY_Salvo Options Model|Salvo Options Model]]
- [[_COMMUNITY_Target Value Options|Target Value Options]]
- [[_COMMUNITY_Missile Inventory Model|Missile Inventory Model]]
- [[_COMMUNITY_Missile Profile Model|Missile Profile Model]]
- [[_COMMUNITY_Ship Snapshot Model|Ship Snapshot Model]]
- [[_COMMUNITY_Weapon Snapshot Model|Weapon Snapshot Model]]
- [[_COMMUNITY_Patch Bootstrap|Patch Bootstrap]]
- [[_COMMUNITY_Layout Check Tool|Layout Check Tool]]
- [[_COMMUNITY_Sample Allocation Tool|Sample Allocation Tool]]
- [[_COMMUNITY_GitHub Templates|GitHub Templates]]
- [[_COMMUNITY_Hull Class Model|Hull Class Model]]
- [[_COMMUNITY_Weapon Role Model|Weapon Role Model]]
- [[_COMMUNITY_Initial Commit Checklist|Initial Commit Checklist]]
- [[_COMMUNITY_Serena Configuration|Serena Configuration]]

## God Nodes (most connected - your core abstractions)
1. `Reverse Engineering Plan` - 16 edges
2. `Architecture` - 12 edges
3. `Main` - 9 edges
4. `SalvoAllocator` - 7 edges
5. `TargetValueCalculator` - 7 edges
6. `PDScoreCalculator` - 6 edges
7. `ModSettings` - 6 edges
8. `SalvoPackageCalculator` - 5 edges
9. `Copilot Instructions` - 5 edges
10. `README` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Auto Salvo Allocation` --semantically_similar_to--> `SalvoAllocator`  [INFERRED] [semantically similar]
  README.md → docs/architecture.md
- `Launch Discipline` --semantically_similar_to--> `LaunchWindowEvaluator`  [INFERRED] [semantically similar]
  README.md → docs/architecture.md
- `Manual Auto-Allocation` --semantically_similar_to--> `Controlled Auto-Allocation Command`  [INFERRED] [semantically similar]
  .github/copilot-instructions.md → docs/mvp-issue-list.md
- `Diagnostics First` --rationale_for--> `Battle Snapshot Extractor`  [INFERRED]
  README.md → docs/mvp-issue-list.md
- `Diagnostics First` --rationale_for--> `Log-Only Patches`  [INFERRED]
  README.md → docs/reverse-engineering-plan.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core-Mod Snapshot Pipeline** — missilefirecontrol_mod, battle_snapshot_extractor, missilefirecontrol_core [INFERRED 0.95]
- **Combat Snapshot Model** — ship_snapshot, weapon_snapshot, missile_profile, missile_inventory_snapshot [EXTRACTED 1.00]
- **Heuristic Scoring Stack** — pdscore_calculator, target_value_calculator, salvo_package_calculator, launch_window_evaluator, salvo_allocator [EXTRACTED 1.00]

## Communities (35 total, 21 thin omitted)

### Community 0 - "Documentation Roadmap"
Cohesion: 0.09
Nodes (33): Active Projectile Instances, Auto Salvo Allocation, Automatic Weapon Fire Decisions, Battle Snapshot Extractor, Combat Ship State, Controlled Auto-Allocation Command, Diagnostics First, Architecture (+25 more)

### Community 1 - "Salvo Allocation Core"
Cohesion: 0.13
Nodes (13): MissileFireControl.Core.Allocation, SalvoAllocator, TargetCandidate, AllocationRequest, LaunchWindowEvaluator, SalvoPackageCalculator, AllocationResult, IEnumerable (+5 more)

### Community 2 - "Mod Entry Settings"
Cohesion: 0.23
Nodes (5): Harmony, Main, MissileFireControl.Mod, bool, ModEntry

### Community 3 - "Salvo Package Sizing"
Cohesion: 0.25
Nodes (7): MissileFireControl.Core.Calculators, SalvoPackageCalculator, SalvoPackage, SalvoPackageOptions, HullClass, MissileProfile, ShipSnapshot

### Community 4 - "Target Value Scoring"
Cohesion: 0.25
Nodes (6): MissileFireControl.Core.Calculators, TargetValueCalculator, HullClass, PDScoreCalculator, ShipSnapshot, TargetValueOptions

### Community 5 - "Point Defense Scoring"
Cohesion: 0.31
Nodes (5): MissileFireControl.Core.Calculators, PDScoreCalculator, PdScoringOptions, IEnumerable, ShipSnapshot

### Community 6 - "Launch Window Logic"
Cohesion: 0.25
Nodes (6): LaunchWindowEvaluator, MissileFireControl.Core.Calculators, LaunchWindowOptions, LaunchWindowResult, MissileProfile, ShipSnapshot

### Community 7 - "Mod Settings Persistence"
Cohesion: 0.33
Nodes (5): double, MissileFireControl.Mod, ModSettings, bool, ModEntry

### Community 8 - "Logging Utilities"
Cohesion: 0.29
Nodes (3): Exception, Log, MissileFireControl.Mod

### Community 9 - "Project Build Files"
Cohesion: 0.33
Nodes (4): net472, netstandard2.0, Microsoft.NET.Sdk, Microsoft.NET.Sdk

### Community 10 - "Vector Math Model"
Cohesion: 0.48
Nodes (6): Distance(), Dot(), Length(), MissileFireControl.Core.Models, Normalized(), Vector3d

### Community 11 - "Decision Logging Sink"
Cohesion: 0.40
Nodes (3): DecisionLogSink, MissileFireControl.Mod.Diagnostics, AllocationResult

### Community 12 - "Combat Patch Placeholder"
Cohesion: 0.50
Nodes (3): CombatLaunchPatchPlaceholder, MissileFireControl.Mod.Patches, string

## Knowledge Gaps
- **91 isolated node(s):** `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation`, `AllocationResult`, `MissileFireControl.Core.Allocation` (+86 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation` to the rest of the system?**
  _91 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Documentation Roadmap` be split into smaller, more focused modules?**
  _Cohesion score 0.0946969696969697 - nodes in this community are weakly interconnected._
- **Should `Salvo Allocation Core` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._