# Graph Report - .  (2026-06-23)

## Corpus Check
- 75 files · ~50,821 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 478 nodes · 1011 edges · 31 communities (27 shown, 4 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Shadow Allocation Diagnostics|Shadow Allocation Diagnostics]]
- [[_COMMUNITY_Combat Launch Diagnostics|Combat Launch Diagnostics]]
- [[_COMMUNITY_Controlled Apply Planning|Controlled Apply Planning]]
- [[_COMMUNITY_Combat Snapshot Extraction|Combat Snapshot Extraction]]
- [[_COMMUNITY_Controlled Command Apply Gate|Controlled Command Apply Gate]]
- [[_COMMUNITY_Game Object Reader Adapter|Game Object Reader Adapter]]
- [[_COMMUNITY_Runtime Validation Evidence|Runtime Validation Evidence]]
- [[_COMMUNITY_Logging|Logging]]
- [[_COMMUNITY_Mod Entry UI|Mod Entry UI]]
- [[_COMMUNITY_Salvo Package Sizing|Salvo Package Sizing]]
- [[_COMMUNITY_Target Value Scoring|Target Value Scoring]]
- [[_COMMUNITY_Harmony Patch Bootstrap|Harmony Patch Bootstrap]]
- [[_COMMUNITY_Point Defense Scoring|Point Defense Scoring]]
- [[_COMMUNITY_Launch Window Evaluation|Launch Window Evaluation]]
- [[_COMMUNITY_Mod Settings|Mod Settings]]
- [[_COMMUNITY_Vector Math Models|Vector Math Models]]
- [[_COMMUNITY_Launch Match Records|Launch Match Records]]
- [[_COMMUNITY_Patch Placeholder|Patch Placeholder]]
- [[_COMMUNITY_Allocation Request|Allocation Request]]
- [[_COMMUNITY_Target Allocation|Target Allocation]]
- [[_COMMUNITY_Launch Window Options|Launch Window Options]]
- [[_COMMUNITY_Launch Window Result|Launch Window Result]]
- [[_COMMUNITY_PD Scoring Options|PD Scoring Options]]
- [[_COMMUNITY_Salvo Package Model|Salvo Package Model]]
- [[_COMMUNITY_Salvo Package Options|Salvo Package Options]]
- [[_COMMUNITY_Target Value Options|Target Value Options]]
- [[_COMMUNITY_Missile Profile Model|Missile Profile Model]]
- [[_COMMUNITY_Hull Class Model|Hull Class Model]]
- [[_COMMUNITY_Weapon Role Model|Weapon Role Model]]
- [[_COMMUNITY_Development Docs README|Development Docs README]]
- [[_COMMUNITY_Plan Docs README|Plan Docs README]]

## God Nodes (most connected - your core abstractions)
1. `ShadowAllocationDiagnostics` - 70 edges
2. `CombatLaunchDiagnostics` - 59 edges
3. `CombatSnapshotExtractor` - 31 edges
4. `GameObjectReader` - 19 edges
5. `ExtractedCombatSnapshot` - 16 edges
6. `ControlledDryRunRequest` - 14 edges
7. `CommandScopeEvidence` - 14 edges
8. `TryFireObservation` - 12 edges
9. `Log` - 10 edges
10. `CommandCandidateDecision` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Controlled dry-run envelope` conceptually_related_to `Command resolvability and scope safety` (dev-docs/plan/issue_34/00-master-plan.md → dev-docs/plan/issue_35/00-master-plan.md)
- `Command resolvability and scope safety` conceptually_related_to `Apply-gate hard stop` (dev-docs/plan/issue_35/00-master-plan.md → dev-docs/plan/issue_36/00-master-plan.md)
- `Apply-gate hard stop` conceptually_related_to `Controlled Command Apply Gate` (dev-docs/plan/issue_36/00-master-plan.md → docs/diagnostics/snapshot-and-allocation.md)
- `Apply-gate hard stop` conceptually_related_to `First live apply, single ship` (dev-docs/plan/issue_36/00-master-plan.md → dev-docs/plan/issue_37/00-master-plan.md)
- `First live apply, single ship` conceptually_related_to `Selected-group expansion` (dev-docs/plan/issue_37/00-master-plan.md → dev-docs/plan/issue_38/00-context.md)

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Controlled command safety rung sequence** — controlled_dry_run_envelope, command_resolvability_and_scope_safety, apply_gate_hard_stop, first_live_apply_single_ship, selected_group_expansion [INFERRED 0.85]
- **Controlled Evidence Lifecycle** — issue_38_00_master_plan, issue_39_00_context, issue_39_01_no_tuning_decision, issue_39_1_00_context, issue_6_00_context [INFERRED 0.85]
- **Selected Scope and Apply Boundary** — selected_player_command_scope, selected_group_safety_rung, controlled_command_apply_gate, ammo_gate_budget_shots [INFERRED 0.75]
- **Correlation Instrumentation and Follow-up Measurement** — command_result_launch_spend_correlation, target_identity_bridge, future_combat_outcome_hook [INFERRED 0.85]

## Communities (31 total, 4 thin omitted)

### Community 0 - "Shadow Allocation Diagnostics"
Cohesion: 0.06
Nodes (88): ShadowAllocationDiagnostics, .LogShadowCycle(), ExtractedCombatSnapshot, ControlledDryRunRequest, .WriteCycleRecord(), .AppendPair(), .ReadMember(), CommandCandidateDecision, .ShouldWaitForSelectedCandidate(), .WriteTargetRecord() (+78 more)

### Community 1 - "Combat Launch Diagnostics"
Cohesion: 0.10
Nodes (68): CombatLaunchDiagnostics, .ReadMember(), .AppendPair(), .Describe(), .OnMissileTryFirePostfix(), TryFireObservation, .OnShipFireWeaponPostfix(), .AppendLiveWeaponAmmoEvidence(), .OnProjectileMissileFirePostfix(), .BattleContext() (+58 more)

### Community 2 - "Controlled Apply Planning"
Cohesion: 0.06
Nodes (53): Issue 34 master plan, Issue 36 master plan, Combat outcome hooks issue draft, Apply-gate hard stop, First live apply, single ship, Issue 35 context, Issue 37 master plan, Missile outcome attribution, AGENTS, Command resolvability and scope safety (+43 more)

### Community 3 - "Combat Snapshot Extraction"
Cohesion: 0.09
Nodes (47): CombatSnapshotExtractor, .FromProjectileMissileFire(), .ExtractPdWeaponEvidence(), .ExtractInventory(), ExtractedCombatSnapshot, PdWeaponEvidence, .AddPdWeightEvidence(), ReadinessEvidenceSnapshot, CombatSnapshotExtractor.cs, .AddWeapon() (+37 more)

### Community 4 - "Controlled Command Apply Gate"
Cohesion: 0.09
Nodes (40): .BuildCommandCandidate(), CommandScopeEvidence, .ApplyControlledCandidate(), .TryApplyControlledCommand(), .HasConcreteToken(), ShadowAllocationDiagnostics.cs, ControlledDryRunRequest, CommandApplyResult, .Failed(), .IndexOfShip() (+30 more)

### Community 5 - "Game Object Reader Adapter"
Cohesion: 0.19
Nodes (24): GameObjectReader, .ReadFirstMember(), .ReadMember(), .TryVector(), .Clean(), .Describe(), .FirstNonEmptyString(), .Label(), .StableId(), .TeamId() (+14 more)

### Community 6 - "Runtime Validation Evidence"
Cohesion: 0.17
Nodes (24): Selected-Group Safety Rung, Battle Snapshot and Allocation Diagnostics, Controlled Evidence Fitting Loop, MVP Roadmap, Selected-Player Command Scope, Command-Result Launch/Spend Correlation, Issue #38 Master Plan, Issue #38 Phase 02 Verification, Issue #39 Context, Ammo/Gate Budget Shots (+14 more)

### Community 7 - "Logging"
Cohesion: 0.26
Nodes (13): Log, .WriteFile(), .Initialize(), .Error(), .Warning(), Exception, Log.cs, .Info(), .ResolveFileLogPath(), ModEntry (+3 more)

### Community 8 - "Mod Entry UI"
Cohesion: 0.23
Nodes (12): Main, ModEntry, .OnGUI(), Main.cs, .Clamp(), .Load(), .OnSaveGUI(), .OnToggle(), Harmony, .IsEnabled() (+2 more)

### Community 9 - "Salvo Package Sizing"
Cohesion: 0.25
Nodes (11): SalvoPackageCalculator, .Calculate(), .EstimateRequiredLeakers(), .HullDurability(), SalvoPackageCalculator.cs, MissileProfile, ShipSnapshot, MissileFireControl.Core.Calculators, SalvoPackage, SalvoPackageOptions (+1 more)

### Community 10 - "Target Value Scoring"
Cohesion: 0.25
Nodes (11): TargetValueCalculator, .Calculate(), .HullValue(), .WeaponThreat(), TargetValueCalculator.cs, .Clamp01(), ShipSnapshot, MissileFireControl.Core.Calculators, HullClass, PDScoreCalculator (+1 more)

### Community 11 - "Harmony Patch Bootstrap"
Cohesion: 0.29
Nodes (11): PatchBootstrap, .TryPatch(), .ResolveParameterTypes(), .Apply(), .ResolveType(), PatchBootstrap.cs, .Skip(), Harmony, Type, MissileFireControl.Mod.Patches (+1 more)

### Community 12 - "Point Defense Scoring"
Cohesion: 0.31
Nodes (10): PDScoreCalculator, .Calculate(), .MaxSupportRange(), .OwnPd(), ShipSnapshot, PDScoreCalculator.cs, .DistanceWeight(), MissileFireControl.Core.Calculators, PdScoringOptions, IEnumerable

### Community 13 - "Launch Window Evaluation"
Cohesion: 0.25
Nodes (9): .Evaluate(), LaunchWindowEvaluator, LaunchWindowEvaluator.cs, .Clamp01(), MissileFireControl.Core.Calculators, LaunchWindowOptions, LaunchWindowResult, MissileProfile, ShipSnapshot

### Community 14 - "Mod Settings"
Cohesion: 0.33
Nodes (7): ModSettings, bool, ModSettings.cs, .Save(), MissileFireControl.Mod, double, ModEntry

### Community 15 - "Vector Math Models"
Cohesion: 0.48
Nodes (7): Vector3d.cs, Distance(), Length(), Normalized(), Vector3d, Dot(), MissileFireControl.Core.Models

### Community 16 - "Launch Match Records"
Cohesion: 0.33
Nodes (6): CombatLaunchDiagnostics.cs, ControlledCommandLaunchMatch, .None(), ControlledCommandLaunchContext, MissileFireControl.Mod.Diagnostics, TryFireObservation

### Community 17 - "Patch Placeholder"
Cohesion: 0.50
Nodes (4): string, CombatLaunchPatch.Placeholder.cs, CombatLaunchPatchPlaceholder, MissileFireControl.Mod.Patches

### Community 18 - "Allocation Request"
Cohesion: 0.67
Nodes (3): AllocationRequest.cs, AllocationRequest, MissileFireControl.Core.Allocation

### Community 19 - "Target Allocation"
Cohesion: 0.67
Nodes (3): TargetAllocation.cs, MissileFireControl.Core.Allocation, TargetAllocation

### Community 20 - "Launch Window Options"
Cohesion: 0.67
Nodes (3): LaunchWindowOptions.cs, LaunchWindowOptions, MissileFireControl.Core.Calculators

### Community 21 - "Launch Window Result"
Cohesion: 0.67
Nodes (3): LaunchWindowResult.cs, LaunchWindowResult, MissileFireControl.Core.Calculators

### Community 22 - "PD Scoring Options"
Cohesion: 0.67
Nodes (3): PdScoringOptions.cs, MissileFireControl.Core.Calculators, PdScoringOptions

### Community 23 - "Salvo Package Model"
Cohesion: 0.67
Nodes (3): SalvoPackage.cs, MissileFireControl.Core.Calculators, SalvoPackage

### Community 24 - "Salvo Package Options"
Cohesion: 0.67
Nodes (3): SalvoPackageOptions.cs, MissileFireControl.Core.Calculators, SalvoPackageOptions

### Community 25 - "Target Value Options"
Cohesion: 0.67
Nodes (3): TargetValueOptions.cs, MissileFireControl.Core.Calculators, TargetValueOptions

### Community 26 - "Missile Profile Model"
Cohesion: 0.67
Nodes (3): MissileProfile.cs, MissileFireControl.Core.Models, MissileProfile

## Knowledge Gaps
- **103 isolated node(s):** `Development Docs README`, `Plan Docs README`, `.IsEnabled()`, `.RequestControlledDryRun()`, `Action` (+98 more)
  These have ≤1 connection - possible missing edges, intentionally isolated model leaves, or documentation-only anchors.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Development Docs README`, `Plan Docs README`, `.IsEnabled()` to the rest of the system?**
  _103 weakly-connected nodes found - possible documentation gaps or expected leaves._
- **Where do controlled command safety, dry-run evidence, and live launch correlation meet?**
  _The semantic hyperedges now bridge issue plans, diagnostics docs, and command-application code paths._