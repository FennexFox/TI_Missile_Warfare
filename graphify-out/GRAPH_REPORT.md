# Graph Report - .  (2026-06-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 483 nodes · 661 edges · 60 communities (37 shown, 23 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `04f4567b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- [[_COMMUNITY_Packaging Tool|Packaging Tool]]
- [[_COMMUNITY_Initial Commit Checklist|Initial Commit Checklist]]
- [[_COMMUNITY_Serena Configuration|Serena Configuration]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]

## God Nodes (most connected - your core abstractions)
1. `CombatLaunchDiagnostics` - 34 edges
2. `GameObjectReader` - 19 edges
3. `CombatSnapshotExtractor` - 14 edges
4. `Codex Task` - 11 edges
5. `Codex Task` - 11 edges
6. `Log` - 10 edges
7. `parse_log()` - 10 edges
8. `Codex Task` - 10 edges
9. `Codex Task` - 10 edges
10. `Main` - 9 edges

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

## Communities (60 total, 23 thin omitted)

### Community 0 - "Documentation Roadmap"
Cohesion: 0.18
Nodes (11): Active Projectile Instances, Automatic Weapon Fire Decisions, Battle Snapshot Extractor, Combat Ship State, Diagnostics First, Log-Only Patches, Manual Target Commands, MissileInventorySnapshot (+3 more)

### Community 1 - "Salvo Allocation Core"
Cohesion: 0.13
Nodes (13): MissileFireControl.Core.Allocation, SalvoAllocator, TargetCandidate, AllocationRequest, LaunchWindowEvaluator, SalvoPackageCalculator, AllocationResult, IEnumerable (+5 more)

### Community 2 - "Mod Entry Settings"
Cohesion: 0.23
Nodes (5): Main, MissileFireControl.Mod, bool, Harmony, ModEntry

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
Cohesion: 0.26
Nodes (6): Exception, Log, MissileFireControl.Mod, object, bool, ModEntry

### Community 9 - "Project Build Files"
Cohesion: 0.33
Nodes (4): net48, netstandard2.0, Microsoft.NET.Sdk, Microsoft.NET.Sdk

### Community 10 - "Vector Math Model"
Cohesion: 0.48
Nodes (6): Distance(), Dot(), Length(), MissileFireControl.Core.Models, Normalized(), Vector3d

### Community 11 - "Decision Logging Sink"
Cohesion: 0.40
Nodes (3): DecisionLogSink, MissileFireControl.Mod.Diagnostics, AllocationResult

### Community 12 - "Combat Patch Placeholder"
Cohesion: 0.50
Nodes (3): CombatLaunchPatchPlaceholder, MissileFireControl.Mod.Patches, string

### Community 26 - "Patch Bootstrap"
Cohesion: 0.29
Nodes (5): MissileFireControl.Mod.Patches, PatchBootstrap, bool, Harmony, Type

### Community 27 - "Layout Check Tool"
Cohesion: 0.43
Nodes (6): fail(), main(), Print a validation error and stop with a failing exit code., Return the subset of candidate paths currently tracked by git., Validate the repository scaffold and committed metadata., tracked_paths()

### Community 29 - "GitHub Templates"
Cohesion: 0.15
Nodes (11): Change type, Implementation notes, Live combat behavior, Non-goals, Reverse-engineering notes, Risk, Rollback, Scope (+3 more)

### Community 32 - "Packaging Tool"
Cohesion: 0.13
Nodes (22): Path, load_mod_id(), main(), Read and validate the UMM mod id from ModInfo.json., Package already-built mod binaries into a local UMM mod folder., is_issue_line(), LineHit, logger_verdict() (+14 more)

### Community 35 - "Community 35"
Cohesion: 0.17
Nodes (8): Action, CombatLaunchDiagnostics, int, MethodInfo, BindingFlags, StringBuilder, Type, TryFireObservation

### Community 36 - "Community 36"
Cohesion: 0.19
Nodes (5): GameObjectReader, MissileFireControl.Mod.Adapters, BindingFlags, Type, Vector3d

### Community 37 - "Community 37"
Cohesion: 0.20
Nodes (7): CombatSnapshotExtractor, ExtractedCombatSnapshot, MissileFireControl.Mod.Adapters, MissileInventorySnapshot, MissileProfile, ShipSnapshot, WeaponRole

### Community 38 - "Community 38"
Cohesion: 0.17
Nodes (11): Acceptance Criteria, Allowed Paths, Codex Task, Completion Contract, Context Summary, Forbidden Paths, Implementation Scope, Inspect First (+3 more)

### Community 39 - "Community 39"
Cohesion: 0.17
Nodes (11): Acceptance Criteria, Allowed Paths, Codex Task, Completion Contract, Context Summary, Forbidden Paths, Implementation Scope, Inspect First (+3 more)

### Community 40 - "Community 40"
Cohesion: 0.17
Nodes (11): Controlled Auto-Allocation Command, Issue 1: Create UMM/Harmony scaffold, Issue 2: Identify combat launch entry points, Issue 3: Add battle snapshot extractor, Issue 4: Recommendation-only salvo allocation, Issue 5: Add debug UI or hotkey, Issue 6: Controlled auto-allocation command, Issue 7: Launch discipline prototype (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.24
Nodes (5): MissileFireControl.Mod.Diagnostics, SnapshotDiagnostics, ExtractedCombatSnapshot, StringBuilder, Vector3d

### Community 42 - "Community 42"
Cohesion: 0.18
Nodes (10): Acceptance Criteria, Allowed Paths, Codex Task, Completion Contract, Context Summary, Forbidden Paths, Implementation Scope, Inspect First (+2 more)

### Community 43 - "Community 43"
Cohesion: 0.18
Nodes (10): Acceptance Criteria, Allowed Paths, Codex Task, Completion Contract, Context Summary, Forbidden Paths, Implementation Scope, Inspect First (+2 more)

### Community 44 - "Community 44"
Cohesion: 0.22
Nodes (9): Explainable Rather Than Physically Exact, Launch Discipline, LaunchWindowEvaluator, MissileProfile, PDScoreCalculator, SalvoPackageCalculator, ShipSnapshot, TargetValueCalculator (+1 more)

### Community 45 - "Community 45"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Background, Candidate Fields, Duplicate Guard, Non-goals, Problem, Proposed Direction, Recover true pre-fire readyShots via live weapon observation (+1 more)

### Community 46 - "Community 46"
Cohesion: 0.33
Nodes (5): Assert-FileExists(), ConvertTo-FullPath(), Get-GameDirFromManagedDir(), Reset-Directory(), Stop-Build()

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (9): Goal, Phase 0: identify objects, Phase 1: log-only patches, Phase 2: snapshot extraction, Phase 3: recommendation-only output, Phase 4: controlled command helper, Phase 5: launch discipline, Reverse-engineering plan (+1 more)

### Community 48 - "Community 48"
Cohesion: 0.25
Nodes (7): Battle snapshot extractor, Launcher-selected target identity runtime findings, Log format, Runtime source, Snapshot mapping, Toggle, Validation

### Community 49 - "Community 49"
Cohesion: 0.25
Nodes (8): Architecture conventions, Commit message rules, Local-only files, Project intent, Pull request rules, Repository instructions for GitHub Copilot, Reverse-engineering rules, Validation expectations

### Community 50 - "Community 50"
Cohesion: 0.43
Nodes (5): Auto Salvo Allocation, Keep Game Integration Thin, MissileFireControl.Core, MissileFireControl.Mod, SalvoAllocator

### Community 51 - "Community 51"
Cohesion: 0.29
Nodes (7): Architecture, Boundaries, Core, Do not do in early versions, Heuristic model, Mod, Principle

### Community 52 - "Community 52"
Cohesion: 0.29
Nodes (6): Caveats, Confirmation snapshot, Confirmed combat launch hooks, Evidence markers, Hook table, Logged fields

### Community 53 - "Community 53"
Cohesion: 0.29
Nodes (6): Acceptance criteria for the next phase, Candidate fields, Guardrails, Next step: true pre-fire `readyShots` observation, Proposed next implementation phase, Validation commands

### Community 54 - "Community 54"
Cohesion: 0.29
Nodes (7): Development strategy, Local setup notes, Repository layout, Scope, Suggested first commit, TI MissileWarfare, Validation

## Knowledge Gaps
- **215 isolated node(s):** `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation`, `AllocationResult`, `MissileFireControl.Core.Allocation` (+210 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Reverse-engineering plan` connect `Community 47` to `Documentation Roadmap`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `Launch Discipline` connect `Community 44` to `Community 40`, `Documentation Roadmap`, `Community 50`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Why does `CombatLaunchDiagnostics` connect `Community 35` to `Community 55`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **What connects `MissileFireControl.Core.Allocation`, `AllocationRequest`, `MissileFireControl.Core.Allocation` to the rest of the system?**
  _227 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Salvo Allocation Core` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Should `Packaging Tool` be split into smaller, more focused modules?**
  _Cohesion score 0.12681159420289856 - nodes in this community are weakly interconnected._