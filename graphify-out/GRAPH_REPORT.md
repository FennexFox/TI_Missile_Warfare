# Graph Report - .  (2026-06-20)

## Corpus Check
- 0 files · ~16,230 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 346 nodes · 568 edges · 36 communities (20 shown, 16 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Combat Launch Diagnostics|Combat Launch Diagnostics]]
- [[_COMMUNITY_Shadow Allocation Diagnostics|Shadow Allocation Diagnostics]]
- [[_COMMUNITY_Combat Snapshot Extraction|Combat Snapshot Extraction]]
- [[_COMMUNITY_Game Object Reading|Game Object Reading]]
- [[_COMMUNITY_Readiness Diagnostics Docs|Readiness Diagnostics Docs]]
- [[_COMMUNITY_Snapshot Diagnostics|Snapshot Diagnostics]]
- [[_COMMUNITY_Salvo Allocation Core|Salvo Allocation Core]]
- [[_COMMUNITY_Mod Logging|Mod Logging]]
- [[_COMMUNITY_Mod Entry Settings|Mod Entry Settings]]
- [[_COMMUNITY_Project Overview|Project Overview]]
- [[_COMMUNITY_Salvo Package Calculation|Salvo Package Calculation]]
- [[_COMMUNITY_Target Value Scoring|Target Value Scoring]]
- [[_COMMUNITY_Harmony Patch Bootstrap|Harmony Patch Bootstrap]]
- [[_COMMUNITY_Point Defense Scoring|Point Defense Scoring]]
- [[_COMMUNITY_Launch Window Evaluation|Launch Window Evaluation]]
- [[_COMMUNITY_Mod Settings Model|Mod Settings Model]]
- [[_COMMUNITY_Inventory Snapshot Models|Inventory Snapshot Models]]
- [[_COMMUNITY_Vector Math Model|Vector Math Model]]
- [[_COMMUNITY_Decision Log Sink|Decision Log Sink]]
- [[_COMMUNITY_Combat Patch Placeholder|Combat Patch Placeholder]]
- [[_COMMUNITY_Allocation Request Model|Allocation Request Model]]
- [[_COMMUNITY_Allocation Result Model|Allocation Result Model]]
- [[_COMMUNITY_Target Allocation Model|Target Allocation Model]]
- [[_COMMUNITY_Launch Window Options|Launch Window Options]]
- [[_COMMUNITY_Launch Window Result|Launch Window Result]]
- [[_COMMUNITY_PD Scoring Options|PD Scoring Options]]
- [[_COMMUNITY_Salvo Package Model|Salvo Package Model]]
- [[_COMMUNITY_Salvo Package Options|Salvo Package Options]]
- [[_COMMUNITY_Target Value Options|Target Value Options]]
- [[_COMMUNITY_Try Fire Observation|Try Fire Observation]]
- [[_COMMUNITY_Missile Profile Model|Missile Profile Model]]
- [[_COMMUNITY_Ship Snapshot Model|Ship Snapshot Model]]
- [[_COMMUNITY_Hull Class Model|Hull Class Model]]
- [[_COMMUNITY_Weapon Role Model|Weapon Role Model]]
- [[_COMMUNITY_Development Docs Index|Development Docs Index]]
- [[_COMMUNITY_Plan Docs Index|Plan Docs Index]]

## God Nodes (most connected - your core abstractions)
1. `CombatLaunchDiagnostics` - 37 edges
2. `ShadowAllocationDiagnostics` - 27 edges
3. `GameObjectReader` - 19 edges
4. `CombatSnapshotExtractor` - 16 edges
5. `Log` - 10 edges
6. `Readiness Semantics` - 10 edges
7. `SnapshotDiagnostics` - 9 edges
8. `Main` - 9 edges
9. `SalvoAllocator` - 7 edges
10. `TargetValueCalculator` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Keep ReadyShots Unknown Until Proven Safe` --rationale_for--> `ShadowAllocationDiagnostics`  [INFERRED]
  docs/diagnostics/snapshot-and-allocation.md → src/MissileFireControl.Mod/Diagnostics/ShadowAllocationDiagnostics.cs
- `Keep ReadyShots Unknown Until Proven Safe` --rationale_for--> `SnapshotDiagnostics`  [INFERRED]
  docs/diagnostics/snapshot-and-allocation.md → src/MissileFireControl.Mod/Diagnostics/SnapshotDiagnostics.cs
- `Do Not Assume a Separate ReadyShots Model` --rationale_for--> `MissileInventorySnapshot`  [INFERRED]
  docs/research/readiness-semantics.md → src/MissileFireControl.Core/Models/MissileInventorySnapshot.cs
- `Do Not Assume a Separate ReadyShots Model` --rationale_for--> `WeaponSnapshot`  [INFERRED]
  docs/research/readiness-semantics.md → src/MissileFireControl.Core/Models/WeaponSnapshot.cs
- `Issue 17 Context` --references--> `Confirmed Combat Launch Hooks`  [EXTRACTED]
  dev-docs/plan/issue_17/00-context.md → docs/diagnostics/hooks.md

## Import Cycles
- None detected.

## Communities (36 total, 16 thin omitted)

### Community 0 - "Combat Launch Diagnostics"
Cohesion: 0.16
Nodes (9): Action, CombatLaunchDiagnostics, MethodInfo, BindingFlags, int, ReadinessEvidenceSnapshot, StringBuilder, Type (+1 more)

### Community 1 - "Shadow Allocation Diagnostics"
Cohesion: 0.10
Nodes (18): AllocationResult, MissileFireControl.Mod.Diagnostics, ShadowAllocationDiagnostics, IEnumerable, List, SalvoAllocator, BindingFlags, ExtractedCombatSnapshot (+10 more)

### Community 2 - "Combat Snapshot Extraction"
Cohesion: 0.18
Nodes (8): CombatSnapshotExtractor, ExtractedCombatSnapshot, MissileFireControl.Mod.Adapters, ReadinessEvidenceSnapshot, MissileInventorySnapshot, MissileProfile, ShipSnapshot, WeaponRole

### Community 3 - "Game Object Reading"
Cohesion: 0.19
Nodes (5): GameObjectReader, MissileFireControl.Mod.Adapters, BindingFlags, Type, Vector3d

### Community 4 - "Readiness Diagnostics Docs"
Cohesion: 0.15
Nodes (19): Allocator-Safe Shot Budget, Ammo-as-Fireable-Budget Hypothesis, Controlled Allocation, Confirmed Combat Launch Hooks, Runtime Validation History, Battle Snapshot and Allocation Diagnostics, Docs README, Gate and Cooldown Evidence (+11 more)

### Community 5 - "Snapshot Diagnostics"
Cohesion: 0.17
Nodes (9): MissileFireControl.Mod.Diagnostics, SnapshotDiagnostics, Keep ReadyShots Unknown Until Proven Safe, ExtractedCombatSnapshot, Func, MissileInventorySnapshot, ReadinessEvidenceSnapshot, StringBuilder (+1 more)

### Community 6 - "Salvo Allocation Core"
Cohesion: 0.13
Nodes (13): MissileFireControl.Core.Allocation, SalvoAllocator, TargetCandidate, AllocationRequest, LaunchWindowEvaluator, SalvoPackageCalculator, AllocationResult, IEnumerable (+5 more)

### Community 7 - "Mod Logging"
Cohesion: 0.26
Nodes (6): Exception, Log, MissileFireControl.Mod, object, bool, ModEntry

### Community 8 - "Mod Entry Settings"
Cohesion: 0.23
Nodes (5): Harmony, Main, MissileFireControl.Mod, bool, ModEntry

### Community 9 - "Project Overview"
Cohesion: 0.18
Nodes (10): Auto Salvo Allocation, Diagnostics First, Launch Discipline, Development strategy, Local setup notes, Repository layout, Scope, Suggested first commit (+2 more)

### Community 10 - "Salvo Package Calculation"
Cohesion: 0.25
Nodes (7): MissileFireControl.Core.Calculators, SalvoPackageCalculator, SalvoPackage, SalvoPackageOptions, HullClass, MissileProfile, ShipSnapshot

### Community 11 - "Target Value Scoring"
Cohesion: 0.25
Nodes (6): MissileFireControl.Core.Calculators, TargetValueCalculator, HullClass, PDScoreCalculator, ShipSnapshot, TargetValueOptions

### Community 12 - "Harmony Patch Bootstrap"
Cohesion: 0.29
Nodes (5): MissileFireControl.Mod.Patches, PatchBootstrap, bool, Harmony, Type

### Community 13 - "Point Defense Scoring"
Cohesion: 0.31
Nodes (5): MissileFireControl.Core.Calculators, PDScoreCalculator, PdScoringOptions, IEnumerable, ShipSnapshot

### Community 14 - "Launch Window Evaluation"
Cohesion: 0.25
Nodes (6): LaunchWindowEvaluator, MissileFireControl.Core.Calculators, LaunchWindowOptions, LaunchWindowResult, MissileProfile, ShipSnapshot

### Community 15 - "Mod Settings Model"
Cohesion: 0.29
Nodes (5): double, MissileFireControl.Mod, ModSettings, bool, ModEntry

### Community 16 - "Inventory Snapshot Models"
Cohesion: 0.29
Nodes (5): MissileFireControl.Core.Models, MissileInventorySnapshot, MissileFireControl.Core.Models, WeaponSnapshot, Do Not Assume a Separate ReadyShots Model

### Community 17 - "Vector Math Model"
Cohesion: 0.48
Nodes (6): Distance(), Dot(), Length(), MissileFireControl.Core.Models, Normalized(), Vector3d

### Community 18 - "Decision Log Sink"
Cohesion: 0.40
Nodes (3): DecisionLogSink, MissileFireControl.Mod.Diagnostics, AllocationResult

### Community 19 - "Combat Patch Placeholder"
Cohesion: 0.50
Nodes (3): CombatLaunchPatchPlaceholder, MissileFireControl.Mod.Patches, string

## Knowledge Gaps
- **123 isolated node(s):** `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation`, `AllocationResult`, `MissileFireControl.Core.Allocation` (+118 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ShadowAllocationDiagnostics` connect `Shadow Allocation Diagnostics` to `Snapshot Diagnostics`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `Keep ReadyShots Unknown Until Proven Safe` connect `Snapshot Diagnostics` to `Shadow Allocation Diagnostics`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **What connects `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation` to the rest of the system?**
  _125 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Shadow Allocation Diagnostics` be split into smaller, more focused modules?**
  _Cohesion score 0.09745293466223699 - nodes in this community are weakly interconnected._
- **Should `Readiness Diagnostics Docs` be split into smaller, more focused modules?**
  _Cohesion score 0.14619883040935672 - nodes in this community are weakly interconnected._
- **Should `Salvo Allocation Core` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._