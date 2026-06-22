using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;
using MissileFireControl.Core.Allocation;
using MissileFireControl.Core.Calculators;
using MissileFireControl.Core.Models;
using MissileFireControl.Mod.Adapters;

namespace MissileFireControl.Mod.Diagnostics
{
    internal static class ShadowAllocationDiagnostics
    {
        private static int _cycleSequence;
        private static int _experimentSequence;
        private static readonly object DryRunLock = new object();
        private static ControlledDryRunRequest _pendingDryRun;

        private static readonly string[] SelectedScopeMemberNames =
        {
            "selectedFriendlyShipState",
            "selectedFriendlyShip",
            "groupSelectedFriendlyShips",
            "SelectedFriendlyShipState",
            "SelectedFriendlyShip",
            "GroupSelectedFriendlyShips"
        };

        private static readonly string[] CanvasControllerRootMemberNames =
        {
            "spaceCombatCanvasController",
            "SpaceCombatCanvasController",
            "spaceCombatCanvas",
            "SpaceCombatCanvas",
            "canvasController",
            "CanvasController",
            "canvas",
            "Canvas",
            "controller",
            "Controller"
        };

        public static void LogProjectileFireShadowAllocation(
            object projectile,
            object[] args,
            ReadinessEvidenceSnapshot readinessEvidence)
        {
            if (!ShouldLog())
            {
                return;
            }

            try
            {
                ExtractedCombatSnapshot snapshot = CombatSnapshotExtractor.FromProjectileMissileFire(projectile, args, readinessEvidence);
                LogShadowCycle(snapshot);
            }
            catch (Exception ex)
            {
                Log.Warning($"Shadow allocation diagnostics failed: {ex.GetType().Name}: {ex.Message}");
            }
        }

        public static string RequestControlledDryRun()
        {
            if (!Main.IsEnabled())
            {
                return "Controlled dry-run experiment not armed: mod is disabled.";
            }

            if (Main.Settings == null || !Main.Settings.EnableDiagnostics)
            {
                return "Controlled dry-run experiment not armed: diagnostics are disabled.";
            }

            if (!Main.Settings.EnableShadowAllocationDiagnostics)
            {
                return "Controlled dry-run experiment not armed: shadow allocation diagnostics are disabled.";
            }

            if (!Main.Settings.EnableControlledDryRunDiagnostics)
            {
                return "Controlled dry-run experiment not armed: controlled dry-run diagnostics are disabled.";
            }

            string requestedUtc = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ", CultureInfo.InvariantCulture);
            string compactUtc = DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ", CultureInfo.InvariantCulture);
            string experimentId = "dryrun-" + compactUtc + "-" + Interlocked.Increment(ref _experimentSequence).ToString(CultureInfo.InvariantCulture);
            lock (DryRunLock)
            {
                _pendingDryRun = new ControlledDryRunRequest(experimentId, requestedUtc);
            }

            return "Controlled dry-run experiment armed: experimentId=" + experimentId + ". The next shadow allocation cycle will log diagnostics only.";
        }

        private static bool ShouldLog()
        {
            return Main.IsEnabled()
                && Main.Settings != null
                && Main.Settings.EnableDiagnostics
                && Main.Settings.EnableShadowAllocationDiagnostics;
        }

        private static void LogShadowCycle(ExtractedCombatSnapshot snapshot)
        {
            int cycleId = Interlocked.Increment(ref _cycleSequence);
            ControlledDryRunRequest dryRun = ConsumePendingControlledDryRun();
            SelectedScopeEvidence selectedScope = dryRun == null ? null : CaptureSelectedScopeEvidence();
            CommandScopeEvidence commandScope = dryRun == null ? null : ResolveCommandScope(selectedScope, snapshot);
            List<CommandCandidateDecision> commandCandidates = new List<CommandCandidateDecision>();
            List<string> missingInputs = MissingInputs(snapshot);
            bool canAllocate = snapshot != null
                && HasConcreteIdentity(snapshot.Launcher, "launcher")
                && snapshot.Target != null
                && HasConcreteMissile(snapshot.Missile);

            AllocationResult result = null;
            if (canAllocate)
            {
                AllocationRequest request = BuildRequest(snapshot);
                result = BuildAllocator().Allocate(request);
            }

            WriteCycleRecord(cycleId, snapshot, result, missingInputs, canAllocate);
            if (dryRun != null)
            {
                WriteDryRunExperimentRecord(dryRun, cycleId, snapshot, missingInputs, canAllocate, selectedScope, commandScope);
            }

            if (!canAllocate)
            {
                WriteNoOp(cycleId, snapshot, "missing required allocation inputs");
                WriteDryRunResult(dryRun, cycleId, 0, 1, 0, "missing required allocation inputs");
                return;
            }

            if (result == null)
            {
                WriteNoOp(cycleId, snapshot, "allocation result unavailable");
                WriteDryRunResult(dryRun, cycleId, 0, 1, 0, "allocation result unavailable");
                return;
            }

            int allocationIndex = 0;
            foreach (TargetAllocation allocation in result.Allocations)
            {
                allocationIndex++;
                WriteTargetRecord("allocation", cycleId, snapshot, allocation, "reason", allocation.Reason);
                WriteDryRunIntent(dryRun, cycleId, snapshot, allocation);
                CommandCandidateDecision candidate = BuildCommandCandidate(cycleId, allocationIndex, snapshot, allocation, commandScope);
                commandCandidates.Add(candidate);
                WriteDryRunCommandCandidate(dryRun, candidate);
            }

            foreach (TargetAllocation rejection in result.Rejections)
            {
                WriteTargetRecord("rejection", cycleId, snapshot, rejection, "rejectionReason", rejection.Reason);
            }

            if (result.Allocations.Count == 0 && result.Rejections.Count == 0)
            {
                string noOpReason = NoOpReason(snapshot);
                WriteNoOp(cycleId, snapshot, noOpReason);
                WriteDryRunResult(dryRun, cycleId, 0, 1, 0, noOpReason);
                return;
            }

            if (commandCandidates.Count == 0)
            {
                WriteDryRunResult(dryRun, cycleId, 0, result.Allocations.Count == 0 ? 1 : 0, 0, "dryRunOnly");
                return;
            }

            WriteDryRunResult(
                dryRun,
                cycleId,
                commandCandidates.Count(candidate => candidate.Classification == "eligible"),
                commandCandidates.Count(candidate => candidate.Classification == "wouldSkip"),
                commandCandidates.Count(candidate => candidate.Classification == "wouldFail"),
                "dryRunOnly");
        }

        private static ControlledDryRunRequest ConsumePendingControlledDryRun()
        {
            lock (DryRunLock)
            {
                if (_pendingDryRun == null)
                {
                    return null;
                }

                if (Main.Settings == null || !Main.Settings.EnableControlledDryRunDiagnostics)
                {
                    _pendingDryRun = null;
                    return null;
                }

                ControlledDryRunRequest request = _pendingDryRun;
                _pendingDryRun = null;
                return request;
            }
        }

        private static void WriteDryRunExperimentRecord(
            ControlledDryRunRequest request,
            int cycleId,
            ExtractedCombatSnapshot snapshot,
            List<string> missingInputs,
            bool canAllocate,
            SelectedScopeEvidence selectedScope,
            CommandScopeEvidence commandScope)
        {
            if (request == null)
            {
                return;
            }

            selectedScope = selectedScope ?? new SelectedScopeEvidence();
            commandScope = commandScope ?? new CommandScopeEvidence();
            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", "dryRunExperiment");
            AppendPair(builder, "experimentId", request.ExperimentId);
            AppendPair(builder, "cycleId", cycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "requestedUtc", request.RequestedUtc);
            AppendPair(builder, "sourceHook", snapshot == null ? "unknown" : snapshot.Source);
            AppendPair(builder, "status", canAllocate ? "evaluated" : "skipped");
            AppendPair(builder, "selectedScopeVisible", selectedScope.Count > 0 ? "True" : "False");
            AppendPair(builder, "selectedScopeSource", selectedScope.Source);
            AppendPair(builder, "selectedScopeMissingReason", selectedScope.MissingReason);
            AppendPair(builder, "selectedShipCount", selectedScope.Count.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "selectedShipIds", selectedScope.Count == 0 ? "none" : string.Join(",", selectedScope.Ids.ToArray()));
            AppendPair(builder, "selectedShipNames", selectedScope.Count == 0 ? "none" : string.Join(",", selectedScope.Names.ToArray()));
            AppendPair(builder, "selectedShipTeams", selectedScope.Count == 0 ? "none" : string.Join(",", selectedScope.TeamIds.ToArray()));
            AppendPair(builder, "commandScopeSource", commandScope.Source);
            AppendPair(builder, "commandScopeMissingReason", commandScope.MissingReason);
            AppendPair(builder, "commandScopeShipCount", commandScope.Count.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "commandScopeShipIds", commandScope.Count == 0 ? "none" : string.Join(",", commandScope.Ids.ToArray()));
            AppendPair(builder, "targetId", snapshot == null || snapshot.Target == null ? "unknown" : snapshot.Target.Id);
            AppendPair(builder, "target", snapshot == null || snapshot.Target == null ? "unknown" : snapshot.Target.DisplayName);
            AppendPair(builder, "missingInputs", missingInputs == null || missingInputs.Count == 0 ? "none" : string.Join(",", missingInputs.ToArray()));
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteDryRunCommandCandidate(
            ControlledDryRunRequest request,
            CommandCandidateDecision candidate)
        {
            if (request == null || candidate == null)
            {
                return;
            }

            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", "dryRunCommandCandidate");
            AppendPair(builder, "experimentId", request.ExperimentId);
            AppendPair(builder, "cycleId", candidate.CycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "candidateId", candidate.CandidateId);
            AppendPair(builder, "classification", candidate.Classification);
            AppendPair(builder, "reason", candidate.Reason);
            AppendPair(builder, "scopeViolation", candidate.ScopeViolation ? "True" : "False");
            AppendPair(builder, "commandIntent", "salvoTargetRecommendationDryRun");
            AppendPair(builder, "commandGranularity", "shipAllSalvoCapableWeapons");
            AppendPair(builder, "commandScopeSource", candidate.CommandScopeSource);
            AppendPair(builder, "commandScopeMissingReason", candidate.CommandScopeMissingReason);
            AppendPair(builder, "commandScopeShipCount", candidate.CommandScopeShipCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "launcherId", candidate.LauncherId);
            AppendPair(builder, "launcher", candidate.LauncherName);
            AppendPair(builder, "weaponId", candidate.WeaponId);
            AppendPair(builder, "missileProfileId", candidate.MissileProfileId);
            AppendPair(builder, "targetId", candidate.TargetId);
            AppendPair(builder, "target", candidate.TargetName);
            AppendPair(builder, "assignedShots", candidate.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "ammoGateBudgetShots", FormatCount(candidate.AmmoGateBudgetShots));
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteDryRunIntent(
            ControlledDryRunRequest request,
            int cycleId,
            ExtractedCombatSnapshot snapshot,
            TargetAllocation allocation)
        {
            if (request == null || allocation == null)
            {
                return;
            }

            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", "dryRunIntent");
            AppendPair(builder, "experimentId", request.ExperimentId);
            AppendPair(builder, "cycleId", cycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "decisionType", "allocation");
            AppendPair(builder, "commandIntent", "salvoTargetRecommendationDryRun");
            AppendPair(builder, "commandGranularity", "shipAllSalvoCapableWeapons");
            AppendPair(builder, "launcherId", snapshot == null || snapshot.Launcher == null ? "unknown" : snapshot.Launcher.Id);
            AppendPair(builder, "launcher", snapshot == null || snapshot.Launcher == null ? "unknown" : snapshot.Launcher.DisplayName);
            AppendPair(builder, "targetId", allocation.TargetId);
            AppendPair(builder, "target", allocation.TargetName);
            AppendPair(builder, "intendedShots", allocation.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "reason", allocation.Reason ?? "unknown");
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteDryRunResult(
            ControlledDryRunRequest request,
            int cycleId,
            int intendedCommands,
            int skippedCommands,
            int failedCommands,
            string resultReason)
        {
            if (request == null)
            {
                return;
            }

            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", "dryRunResult");
            AppendPair(builder, "experimentId", request.ExperimentId);
            AppendPair(builder, "cycleId", cycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "intendedCommands", intendedCommands.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "skippedCommands", skippedCommands.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "appliedCommands", "0");
            AppendPair(builder, "failedCommands", failedCommands.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "result", "dryRunOnly");
            AppendPair(builder, "resultReason", resultReason ?? "dryRunOnly");
            Log.Info("[AllocationLog] " + builder);
        }

        private static CommandScopeEvidence ResolveCommandScope(SelectedScopeEvidence selectedScope, ExtractedCombatSnapshot snapshot)
        {
            if (selectedScope != null && selectedScope.Count > 0)
            {
                return CommandScopeEvidence.FromSelectedScope(selectedScope);
            }

            CommandScopeEvidence launcherScope = TryResolveActivePlayerLauncherScope(snapshot);
            if (launcherScope.Count > 0 || launcherScope.MissingReason != "playerControlledScopeUnavailable")
            {
                return launcherScope;
            }

            return new CommandScopeEvidence
            {
                Source = "none",
                MissingReason = selectedScope == null ? "selectedScopeUnavailable" : selectedScope.MissingReason
            };
        }

        private static CommandScopeEvidence TryResolveActivePlayerLauncherScope(ExtractedCombatSnapshot snapshot)
        {
            CommandScopeEvidence evidence = new CommandScopeEvidence
            {
                Source = "activePlayerLauncher",
                MissingReason = "playerControlledScopeUnavailable"
            };

            if (snapshot == null || !HasConcreteIdentity(snapshot.Launcher, "launcher"))
            {
                evidence.MissingReason = "missingLauncherIdentity";
                return evidence;
            }

            object launcher = snapshot.LauncherRuntimeObject;
            if (launcher == null)
            {
                evidence.MissingReason = "launcherRuntimeObjectUnavailable";
                return evidence;
            }

            object activePlayer = ActivePlayer();
            if (activePlayer == null)
            {
                evidence.MissingReason = "activePlayerUnavailable";
                return evidence;
            }

            object activePlayerFaction = ReadMember(activePlayer, "faction")
                ?? ReadMember(activePlayer, "ref_faction")
                ?? activePlayer;

            object launcherFaction = ReadMember(launcher, "faction")
                ?? ReadMember(launcher, "ref_faction")
                ?? ReadMember(ReadMember(launcher, "fleet"), "faction");
            if (launcherFaction == null)
            {
                evidence.MissingReason = "launcherFactionUnavailable";
                return evidence;
            }

            if (!SameIdentity(launcherFaction, activePlayerFaction, "faction"))
            {
                evidence.MissingReason = "nonPlayerOrAIControlled";
                return evidence;
            }

            bool? combatAiControl = TryReadBool(launcher, "combatAIControl", "CombatAIControl")
                ?? TryReadBool(ReadMember(launcher, "ref_shipController"), "IsUnderAIControl", "isUnderAIControl")
                ?? TryReadBool(ReadMember(launcher, "fleet"), "IsUnderAIControl", "isUnderAIControl");
            if (!combatAiControl.HasValue)
            {
                evidence.MissingReason = "commandAuthorityUnavailable";
                return evidence;
            }

            if (combatAiControl.Value)
            {
                evidence.MissingReason = "nonPlayerOrAIControlled";
                return evidence;
            }

            bool? canPerformCommands = TryReadBool(launcher, "CanPerformShipCommands");
            bool? canFireMissiles = TryReadBool(launcher, "AnyOffensiveMissileWeaponCanFire");

            evidence.MissingReason = "none";
            evidence.Ids.Add(snapshot.Launcher.Id);
            evidence.Names.Add(snapshot.Launcher.DisplayName);
            evidence.TeamIds.Add(snapshot.Launcher.TeamId);
            evidence.CommandAuthorityKnown = canPerformCommands.HasValue;
            evidence.CanPerformCommands = canPerformCommands.GetValueOrDefault();
            evidence.MissileCommandKnown = canFireMissiles.HasValue;
            evidence.CanFireMissiles = canFireMissiles.GetValueOrDefault();
            return evidence;
        }

        private static CommandCandidateDecision BuildCommandCandidate(
            int cycleId,
            int allocationIndex,
            ExtractedCombatSnapshot snapshot,
            TargetAllocation allocation,
            CommandScopeEvidence commandScope)
        {
            CommandCandidateDecision candidate = new CommandCandidateDecision
            {
                CycleId = cycleId,
                CandidateId = "cycle-" + cycleId.ToString(CultureInfo.InvariantCulture)
                    + "-allocation-" + allocationIndex.ToString(CultureInfo.InvariantCulture),
                Classification = "eligible",
                Reason = "none",
                CommandScopeSource = commandScope == null ? "none" : commandScope.Source,
                CommandScopeMissingReason = commandScope == null ? "playerControlledScopeUnavailable" : commandScope.MissingReason,
                CommandScopeShipCount = commandScope == null ? 0 : commandScope.Count,
                LauncherId = snapshot == null || snapshot.Launcher == null ? "unknown" : snapshot.Launcher.Id,
                LauncherName = snapshot == null || snapshot.Launcher == null ? "unknown" : snapshot.Launcher.DisplayName,
                WeaponId = snapshot == null || snapshot.Inventory == null ? "unknown" : snapshot.Inventory.WeaponId,
                MissileProfileId = snapshot == null || snapshot.Missile == null ? "unknown" : snapshot.Missile.Id,
                TargetId = allocation == null ? "unknown" : allocation.TargetId,
                TargetName = allocation == null ? "unknown" : allocation.TargetName,
                AssignedShots = allocation == null ? 0 : allocation.AssignedShots,
                AmmoGateBudgetShots = AmmoGateBudgetShots(snapshot)
            };

            if (snapshot == null || !HasConcreteIdentity(snapshot.Launcher, "launcher"))
            {
                return candidate.Fail("wouldFail", "missingLauncherIdentity");
            }

            if (commandScope == null || commandScope.Count == 0)
            {
                return candidate.Fail("wouldSkip", ScopeUnavailableReason(commandScope));
            }

            if (!commandScope.ContainsShip(snapshot.Launcher.Id))
            {
                candidate.ScopeViolation = true;
                return candidate.Fail("wouldSkip", "outsidePlayerControlledScope");
            }

            if (!HasConcreteToken(candidate.WeaponId))
            {
                return candidate.Fail("wouldFail", "missingWeaponIdentity");
            }

            if (!HasConcreteToken(candidate.TargetId))
            {
                return candidate.Fail("wouldFail", "missingTargetIdentity");
            }

            if (candidate.AssignedShots <= 0 || candidate.AmmoGateBudgetShots < candidate.AssignedShots)
            {
                return candidate.Fail("wouldFail", "insufficientAmmo");
            }

            if (commandScope.CommandAuthorityKnown && !commandScope.CanPerformCommands)
            {
                return candidate.Fail("wouldFail", "ambiguousCommandPath");
            }

            if (!commandScope.CommandAuthorityKnown || !commandScope.MissileCommandKnown)
            {
                return candidate.Fail("wouldFail", "ambiguousCommandPath");
            }

            if (!commandScope.CanFireMissiles)
            {
                return candidate.Fail("wouldFail", "insufficientAmmo");
            }

            return candidate;
        }

        private static string ScopeUnavailableReason(CommandScopeEvidence commandScope)
        {
            if (commandScope == null || string.IsNullOrWhiteSpace(commandScope.MissingReason))
            {
                return "unsafeScope";
            }

            return commandScope.MissingReason == "nonPlayerOrAIControlled"
                ? "nonPlayerOrAIControlled"
                : "unsafeScope";
        }

        private static object ActivePlayer()
        {
            return ReadStaticMember("GameControl", "activePlayer")
                ?? ReadStaticMember("GameControl", "humanPlayer")
                ?? ReadStaticMember("PavonisInteractive.TerraInvicta.GameControl", "activePlayer")
                ?? ReadStaticMember("PavonisInteractive.TerraInvicta.GameControl", "humanPlayer");
        }

        private static bool? TryReadBool(object instance, params string[] memberNames)
        {
            object value = GameObjectReader.ReadFirstMember(instance, memberNames);
            if (value is bool boolValue)
            {
                return boolValue;
            }

            if (!(value is IConvertible))
            {
                return null;
            }

            string text = Convert.ToString(value, CultureInfo.InvariantCulture);
            bool parsed;
            if (bool.TryParse(text, out parsed))
            {
                return parsed;
            }

            try
            {
                return Convert.ToDouble(value, CultureInfo.InvariantCulture) != 0.0;
            }
            catch
            {
                return null;
            }
        }

        private static bool SameIdentity(object left, object right, string fallbackPrefix)
        {
            if (left == null || right == null)
            {
                return false;
            }

            if (ReferenceEquals(left, right) || left.Equals(right))
            {
                return true;
            }

            string leftId = GameObjectReader.StableId(left, fallbackPrefix);
            string rightId = GameObjectReader.StableId(right, fallbackPrefix);
            return HasConcreteToken(leftId) && string.Equals(leftId, rightId, StringComparison.Ordinal);
        }

        private static bool HasConcreteToken(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return false;
            }

            return !value.StartsWith("unknown", StringComparison.Ordinal);
        }

        private static SelectedScopeEvidence CaptureSelectedScopeEvidence()
        {
            SelectedScopeEvidence evidence = new SelectedScopeEvidence();
            foreach (SelectedScopeCandidate candidate in SelectedScopeCandidates())
            {
                if (candidate.Value == null)
                {
                    continue;
                }

                bool sawCandidate = AddSelectedShipEvidence(candidate.Value, evidence);
                if (!sawCandidate)
                {
                    evidence.Source = candidate.Source;
                    evidence.MissingReason = "selectedScopeEmpty";
                    continue;
                }

                evidence.Source = candidate.Source;
                evidence.MissingReason = evidence.Count == 0 ? "selectedScopeEmpty" : "none";
                return evidence;
            }

            if (string.IsNullOrWhiteSpace(evidence.Source))
            {
                evidence.Source = "none";
            }

            if (string.IsNullOrWhiteSpace(evidence.MissingReason))
            {
                evidence.MissingReason = "selectedScopeUnavailable";
            }

            return evidence;
        }

        private static IEnumerable<SelectedScopeCandidate> SelectedScopeCandidates()
        {
            foreach (string memberName in SelectedScopeMemberNames)
            {
                object value = ReadStaticMember("SpaceCombatCanvasController", memberName)
                    ?? ReadStaticMember("PavonisInteractive.TerraInvicta.SpaceCombatCanvasController", memberName);
                yield return new SelectedScopeCandidate("SpaceCombatCanvasController." + memberName, value);
            }

            foreach (string rootMemberName in new[] { "instance", "Instance", "current", "Current" })
            {
                object controller = ReadStaticMember("SpaceCombatCanvasController", rootMemberName)
                    ?? ReadStaticMember("PavonisInteractive.TerraInvicta.SpaceCombatCanvasController", rootMemberName);
                foreach (SelectedScopeCandidate candidate in SelectedScopeCandidatesFromRoot("SpaceCombatCanvasController." + rootMemberName, controller))
                {
                    yield return candidate;
                }
            }

            object spaceCombat = ReadStaticMember("GameControl", "spaceCombat")
                ?? ReadStaticMember("PavonisInteractive.TerraInvicta.GameControl", "spaceCombat");
            foreach (SelectedScopeCandidate candidate in SelectedScopeCandidatesFromRoot("GameControl.spaceCombat", spaceCombat))
            {
                yield return candidate;
            }

            foreach (string rootMemberName in CanvasControllerRootMemberNames)
            {
                object controller = ReadStaticMember("GameControl", rootMemberName)
                    ?? ReadStaticMember("PavonisInteractive.TerraInvicta.GameControl", rootMemberName);
                foreach (SelectedScopeCandidate candidate in SelectedScopeCandidatesFromRoot("GameControl." + rootMemberName, controller))
                {
                    yield return candidate;
                }
            }
        }

        private static IEnumerable<SelectedScopeCandidate> SelectedScopeCandidatesFromRoot(string rootName, object root)
        {
            if (root == null)
            {
                yield break;
            }

            foreach (string memberName in SelectedScopeMemberNames)
            {
                yield return new SelectedScopeCandidate(rootName + "." + memberName, ReadMember(root, memberName));
            }

            foreach (string controllerMemberName in CanvasControllerRootMemberNames)
            {
                object controller = ReadMember(root, controllerMemberName);
                if (controller == null || ReferenceEquals(controller, root))
                {
                    continue;
                }

                foreach (string memberName in SelectedScopeMemberNames)
                {
                    yield return new SelectedScopeCandidate(rootName + "." + controllerMemberName + "." + memberName, ReadMember(controller, memberName));
                }
            }
        }

        private static bool AddSelectedShipEvidence(object value, SelectedScopeEvidence evidence)
        {
            if (value == null)
            {
                return false;
            }

            if (value is string)
            {
                return false;
            }

            bool sawCandidate = false;
            if (value is IEnumerable enumerable)
            {
                foreach (object item in enumerable)
                {
                    sawCandidate = true;
                    AddSelectedShip(item, evidence);
                }

                return sawCandidate;
            }

            sawCandidate = true;
            AddSelectedShip(value, evidence);
            return sawCandidate;
        }

        private static void AddSelectedShip(object value, SelectedScopeEvidence evidence)
        {
            object ship = UnwrapSelectedShip(value);
            if (ship == null)
            {
                return;
            }

            string id = GameObjectReader.StableId(ship, "selectedShip");
            if (!evidence.SeenIds.Add(id))
            {
                return;
            }

            evidence.Ids.Add(id);
            evidence.Names.Add(GameObjectReader.Label(ship, "selectedShip"));
            evidence.TeamIds.Add(GameObjectReader.TeamId(ship));
        }

        private static object UnwrapSelectedShip(object value)
        {
            if (value == null)
            {
                return null;
            }

            object unwrapped = GameObjectReader.ReadFirstMember(
                value,
                "selectedFriendlyShipState",
                "shipState",
                "ShipState",
                "spaceShipState",
                "SpaceShipState",
                "combatTargetableState",
                "CombatTargetableState",
                "state",
                "State");
            return unwrapped ?? value;
        }

        private static AllocationRequest BuildRequest(ExtractedCombatSnapshot snapshot)
        {
            AllocationRequest request = new AllocationRequest
            {
                Missile = snapshot.Missile,
                MinimumLaunchWindowScore = Main.Settings == null ? 0.35 : Main.Settings.MinimumLaunchScore
            };

            request.FriendlyLaunchers.Add(snapshot.Launcher);
            request.EnemyTargets.Add(snapshot.Target);
            request.EnemyFleet.Add(snapshot.Target);
            request.MissileInventories.Add(new MissileInventorySnapshot
            {
                LauncherShipId = snapshot.Inventory == null ? snapshot.Launcher.Id : snapshot.Inventory.LauncherShipId,
                WeaponId = snapshot.Inventory == null ? "unknown" : snapshot.Inventory.WeaponId,
                MissileProfileId = snapshot.Missile.Id,
                AmmoGateBudgetShots = Math.Max(0, AmmoGateBudgetShots(snapshot)),
                RemainingShots = snapshot.Inventory == null ? -1 : snapshot.Inventory.RemainingShots,
                AmmoGateBudgetEvidenceSource = Evidence(snapshot, inventory => inventory.AmmoGateBudgetEvidenceSource, "unknown"),
                AmmoGateBudgetMissingReason = Evidence(snapshot, inventory => inventory.AmmoGateBudgetMissingReason, "unknown"),
                AmmoEvidenceSource = Evidence(snapshot, inventory => inventory.AmmoEvidenceSource, "unknown"),
                LiveWeaponState = Evidence(snapshot, inventory => inventory.LiveWeaponState, "unknown"),
                AmmoGateWeaponCount = snapshot.Inventory == null ? -1 : snapshot.Inventory.AmmoGateWeaponCount,
                UnknownAmmoGateWeaponCount = snapshot.Inventory == null ? 1 : snapshot.Inventory.UnknownAmmoGateWeaponCount
            });

            return request;
        }

        private static SalvoAllocator BuildAllocator()
        {
            PDScoreCalculator pdScoreCalculator = new PDScoreCalculator(new PdScoringOptions());
            TargetValueCalculator targetValueCalculator = new TargetValueCalculator(new TargetValueOptions(), pdScoreCalculator);
            return new SalvoAllocator(
                pdScoreCalculator,
                targetValueCalculator,
                new SalvoPackageCalculator(new SalvoPackageOptions()),
                new LaunchWindowEvaluator(new LaunchWindowOptions()));
        }

        private static List<string> MissingInputs(ExtractedCombatSnapshot snapshot)
        {
            List<string> missing = new List<string>();
            if (snapshot == null)
            {
                missing.Add("snapshot");
                return missing;
            }

            AddRange(missing, snapshot.MissingFields);

            if (!HasConcreteIdentity(snapshot.Launcher, "launcher"))
            {
                AddMissing(missing, "launcher");
            }

            if (!HasConcreteIdentity(snapshot.Target, "target"))
            {
                AddMissing(missing, "targetIdentity");
            }

            if (!snapshot.HasTargetVelocity)
            {
                AddMissing(missing, "targetVelocity");
            }

            if (AmmoGateBudgetShots(snapshot) < 0)
            {
                AddMissing(missing, "ammoGateBudgetShots");
            }

            if (!HasConcreteMissile(snapshot.Missile))
            {
                AddMissing(missing, "missileProfileData");
            }

            if (snapshot.PdWeightDefaulted)
            {
                AddMissing(missing, "pdWeightsDefaulted");
            }

            return missing;
        }

        private static void WriteCycleRecord(
            int cycleId,
            ExtractedCombatSnapshot snapshot,
            AllocationResult result,
            List<string> missingInputs,
            bool canAllocate)
        {
            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", "cycle");
            AppendPair(builder, "cycleId", cycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "status", canAllocate ? "evaluated" : "skipped");
            AppendPair(builder, "sourceHook", snapshot == null ? "unknown" : snapshot.Source);
            AppendPair(builder, "battle", BattleContext());
            AppendPair(builder, "friendlyLaunchers", HasConcreteIdentity(snapshot == null ? null : snapshot.Launcher, "launcher") ? "1" : "0");
            AppendPair(builder, "targetCount", snapshot == null || snapshot.Target == null ? "0" : "1");
            AppendPair(builder, "totalAmmoGateBudgetShots", AmmoGateBudgetShots(snapshot) < 0 ? "unknown" : AmmoGateBudgetShots(snapshot).ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "ammoGateBudgetEvidenceSource", Evidence(snapshot, inventory => inventory.AmmoGateBudgetEvidenceSource, "unknown"));
            AppendPair(builder, "ammoGateBudgetMissingReason", Evidence(snapshot, inventory => inventory.AmmoGateBudgetMissingReason, "unknown"));
            AppendPair(builder, "ammoEvidenceSource", Evidence(snapshot, inventory => inventory.AmmoEvidenceSource, "unknown"));
            AppendPair(builder, "liveWeaponState", Evidence(snapshot, inventory => inventory.LiveWeaponState, "unknown"));
            AppendPair(builder, "ammoGateWeaponCount", FormatCount(snapshot == null || snapshot.Inventory == null ? -1 : snapshot.Inventory.AmmoGateWeaponCount));
            AppendPair(builder, "unknownAmmoGateWeaponCount", FormatCount(snapshot == null || snapshot.Inventory == null ? -1 : snapshot.Inventory.UnknownAmmoGateWeaponCount));
            AppendPair(builder, "targetVelocityKps", snapshot != null && snapshot.HasTargetVelocity ? Format(snapshot.TargetVelocityKps) : "unknown");
            AppendPair(builder, "targetVelocityEvidenceSource", snapshot == null ? "unknown" : snapshot.TargetVelocityEvidenceSource ?? "unknown");
            AppendPair(builder, "targetVelocityMissingReason", snapshot == null ? "snapshotUnavailable" : snapshot.TargetVelocityMissingReason ?? "unknown");
            AppendPair(builder, "relativeVelocityKps", snapshot != null && snapshot.HasRelativeVelocity ? Format(snapshot.RelativeVelocityKps) : "unknown");
            AppendPair(builder, "relativeSpeedKps", snapshot != null && snapshot.HasRelativeVelocity ? Format(snapshot.RelativeSpeedKps) : "unknown");
            AppendPair(builder, "relativeVelocityEvidenceSource", snapshot == null ? "unknown" : snapshot.RelativeVelocityEvidenceSource ?? "unknown");
            AppendPair(builder, "relativeVelocityMissingReason", snapshot == null ? "snapshotUnavailable" : snapshot.RelativeVelocityMissingReason ?? "unknown");
            AppendPair(builder, "pdWeight", snapshot == null ? "unknown" : Format(snapshot.PdWeight));
            AppendPair(builder, "pdWeightEvidenceSource", snapshot == null ? "unknown" : snapshot.PdWeightEvidenceSource ?? "unknown");
            AppendPair(builder, "pdWeightDefaulted", snapshot == null ? "unknown" : snapshot.PdWeightDefaulted ? "True" : "False");
            AppendPair(builder, "pdWeightDefaultReason", snapshot == null ? "unknown" : snapshot.PdWeightDefaultReason ?? "none");
            AppendPair(builder, "pdWeightMissingReason", snapshot == null ? "snapshotUnavailable" : snapshot.PdWeightMissingReason ?? "unknown");
            AppendPair(builder, "pdEvidenceQuality", snapshot == null ? "unknown" : snapshot.PdEvidenceQuality ?? "unknown");
            AppendPair(builder, "pdCapabilityEvidenceSource", snapshot == null ? "unknown" : snapshot.PdCapabilityEvidenceSource ?? "unknown");
            AppendPair(builder, "pdCapabilityWeaponCount", snapshot == null ? "unknown" : FormatCount(snapshot.PdCapabilityWeaponCount));
            AppendPair(builder, "pdCapabilityRangeKm", snapshot == null ? "unknown" : Format(snapshot.PdCapabilityRangeKm));
            AppendPair(builder, "pdCapabilityCooldownSeconds", snapshot == null ? "unknown" : Format(snapshot.PdCapabilityCooldownSeconds));
            AppendPair(builder, "pdCapabilityObservedFields", snapshot == null ? "unknown" : snapshot.PdCapabilityObservedFields ?? "none");
            AppendPair(builder, "pdCapabilityMissingReason", snapshot == null ? "snapshotUnavailable" : snapshot.PdCapabilityMissingReason ?? "unknown");
            AppendPair(builder, "pdCapabilityLimitations", snapshot == null ? "snapshotUnavailable" : snapshot.PdCapabilityLimitations ?? "unknown");
            AppendPair(builder, "assignedShots", result == null ? "0" : result.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "unassignedShots", result == null || AmmoGateBudgetShots(snapshot) < 0 ? "unknown" : result.UnassignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missingInputs", missingInputs == null || missingInputs.Count == 0 ? "none" : string.Join(",", missingInputs.ToArray()));
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteTargetRecord(
            string recordType,
            int cycleId,
            ExtractedCombatSnapshot snapshot,
            TargetAllocation allocation,
            string reasonKey,
            string reason)
        {
            bool hasAllocationMetrics = allocation != null && recordType != "noOp";

            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", recordType);
            AppendPair(builder, "cycleId", cycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "targetId", allocation == null ? "unknown" : allocation.TargetId);
            AppendPair(builder, "ammoGateBudgetShots", AmmoGateBudgetShots(snapshot) < 0 ? "unknown" : AmmoGateBudgetShots(snapshot).ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "ammoGateBudgetEvidenceSource", Evidence(snapshot, inventory => inventory.AmmoGateBudgetEvidenceSource, "unknown"));
            AppendPair(builder, "ammoGateBudgetMissingReason", Evidence(snapshot, inventory => inventory.AmmoGateBudgetMissingReason, "unknown"));
            AppendPair(builder, "pdWeightEvidenceSource", snapshot == null ? "unknown" : snapshot.PdWeightEvidenceSource ?? "unknown");
            AppendPair(builder, "pdWeightDefaulted", snapshot == null ? "unknown" : snapshot.PdWeightDefaulted ? "True" : "False");
            AppendPair(builder, "pdWeightDefaultReason", snapshot == null ? "unknown" : snapshot.PdWeightDefaultReason ?? "none");
            AppendPair(builder, "pdWeightMissingReason", snapshot == null ? "snapshotUnavailable" : snapshot.PdWeightMissingReason ?? "unknown");
            AppendPair(builder, "pdEvidenceQuality", snapshot == null ? "unknown" : snapshot.PdEvidenceQuality ?? "unknown");
            AppendPair(builder, "pdCapabilityEvidenceSource", snapshot == null ? "unknown" : snapshot.PdCapabilityEvidenceSource ?? "unknown");
            AppendPair(builder, "pdCapabilityWeaponCount", snapshot == null ? "unknown" : FormatCount(snapshot.PdCapabilityWeaponCount));
            AppendPair(builder, "pdCapabilityRangeKm", snapshot == null ? "unknown" : Format(snapshot.PdCapabilityRangeKm));
            AppendPair(builder, "pdCapabilityCooldownSeconds", snapshot == null ? "unknown" : Format(snapshot.PdCapabilityCooldownSeconds));
            AppendPair(builder, "pdCapabilityObservedFields", snapshot == null ? "unknown" : snapshot.PdCapabilityObservedFields ?? "none");
            AppendPair(builder, "pdCapabilityMissingReason", snapshot == null ? "snapshotUnavailable" : snapshot.PdCapabilityMissingReason ?? "unknown");
            AppendPair(builder, "pdCapabilityLimitations", snapshot == null ? "snapshotUnavailable" : snapshot.PdCapabilityLimitations ?? "unknown");
            AppendPair(builder, "target", allocation == null ? "unknown" : allocation.TargetName);
            AppendPair(builder, "assignedShots", allocation == null ? "0" : allocation.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "pdScore", hasAllocationMetrics ? Format(allocation.PdScore) : "unknown");
            AppendPair(builder, "targetValue", hasAllocationMetrics ? Format(allocation.TargetValue) : "unknown");
            AppendPair(builder, "saturationSize", hasAllocationMetrics ? allocation.SaturationSize.ToString(CultureInfo.InvariantCulture) : "unknown");
            AppendPair(builder, "killSize", hasAllocationMetrics ? allocation.KillSize.ToString(CultureInfo.InvariantCulture) : "unknown");
            AppendPair(builder, "launchWindowScore", hasAllocationMetrics ? Format(allocation.LaunchWindowScore) : "unknown");
            AppendPair(builder, "scorePerShot", hasAllocationMetrics ? Format(allocation.ScorePerShot) : "unknown");
            AppendPair(builder, reasonKey, reason ?? "unknown");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteNoOp(int cycleId, ExtractedCombatSnapshot snapshot, string reason)
        {
            TargetAllocation noOp = new TargetAllocation
            {
                TargetId = snapshot == null || snapshot.Target == null ? "unknown" : snapshot.Target.Id,
                TargetName = snapshot == null || snapshot.Target == null ? "unknown" : snapshot.Target.DisplayName,
                AssignedShots = 0,
                Reason = reason
            };
            WriteTargetRecord("noOp", cycleId, snapshot, noOp, "noOpReason", reason);
        }

        private static string NoOpReason(ExtractedCombatSnapshot snapshot)
        {
            int ammoGateBudgetShots = AmmoGateBudgetShots(snapshot);
            if (ammoGateBudgetShots < 0)
            {
                return "missing ammoGateBudgetShots";
            }

            if (ammoGateBudgetShots == 0)
            {
                return "no ammo/gate budget shots";
            }

            return "no allocation decision emitted";
        }

        private static int AmmoGateBudgetShots(ExtractedCombatSnapshot snapshot)
        {
            return snapshot == null || snapshot.Inventory == null ? -1 : snapshot.Inventory.AmmoGateBudgetShots;
        }

        private static string Evidence(
            ExtractedCombatSnapshot snapshot,
            Func<MissileInventorySnapshot, string> read,
            string fallback)
        {
            if (snapshot == null || snapshot.Inventory == null || read == null)
            {
                return fallback;
            }

            string value = read(snapshot.Inventory);
            return string.IsNullOrWhiteSpace(value) ? fallback : value;
        }

        private static bool HasConcreteMissile(MissileProfile missile)
        {
            return missile != null
                && !string.IsNullOrWhiteSpace(missile.Id)
                && !missile.Id.StartsWith("unknown-", StringComparison.Ordinal)
                && missile.NominalRangeKm > 0.0
                && missile.EffectiveVelocityKps > 0.0;
        }

        private static bool HasConcreteIdentity(ShipSnapshot ship, string fallbackPrefix)
        {
            if (ship == null || string.IsNullOrWhiteSpace(ship.Id))
            {
                return false;
            }

            if (ship.Id.StartsWith("unknown-", StringComparison.Ordinal))
            {
                return false;
            }

            return !ship.Id.StartsWith(fallbackPrefix + ":", StringComparison.Ordinal);
        }

        private static void AddRange(List<string> values, IEnumerable<string> additions)
        {
            if (additions == null)
            {
                return;
            }

            foreach (string value in additions)
            {
                AddMissing(values, value);
            }
        }

        private static void AddMissing(List<string> values, string value)
        {
            if (string.IsNullOrWhiteSpace(value) || values.Contains(value))
            {
                return;
            }

            values.Add(value);
        }

        private static string BattleContext()
        {
            object spaceCombat = ReadStaticMember("GameControl", "spaceCombat")
                ?? ReadStaticMember("PavonisInteractive.TerraInvicta.GameControl", "spaceCombat");
            if (spaceCombat == null)
            {
                return "unavailable";
            }

            StringBuilder builder = new StringBuilder();
            AppendPair(builder, "combat", Describe(spaceCombat));
            AppendPair(builder, "initialized", Describe(ReadMember(spaceCombat, "initialized")));
            AppendPair(builder, "duration", Describe(ReadMember(spaceCombat, "combatDuration_s")));
            AppendPair(builder, "activeShips", DescribeCount(ReadMember(spaceCombat, "activeShips")));
            AppendPair(builder, "liveMissiles", DescribeCount(ReadMember(spaceCombat, "liveMissiles")));
            AppendPair(builder, "lastShot", Describe(ReadMember(spaceCombat, "timeOfLastShotFired")));
            return builder.ToString().Trim();
        }

        private static object ReadStaticMember(string typeName, string memberName)
        {
            Type type = AppDomain.CurrentDomain.GetAssemblies()
                .Select(assembly => assembly.GetType(typeName, throwOnError: false))
                .FirstOrDefault(candidate => candidate != null);
            if (type == null)
            {
                return null;
            }

            return ReadMember(type, null, memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
        }

        private static object ReadMember(object instance, string memberName)
        {
            if (instance == null || string.IsNullOrEmpty(memberName))
            {
                return null;
            }

            return ReadMember(instance.GetType(), instance, memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        }

        private static object ReadMember(Type type, object instance, string memberName, BindingFlags flags)
        {
            try
            {
                PropertyInfo property = type.GetProperty(memberName, flags);
                if (property != null && property.GetIndexParameters().Length == 0)
                {
                    return property.GetValue(instance, null);
                }

                FieldInfo field = type.GetField(memberName, flags);
                if (field != null)
                {
                    return field.GetValue(instance);
                }
            }
            catch
            {
                return null;
            }

            return null;
        }

        private static string Describe(object value)
        {
            if (value == null)
            {
                return "null";
            }

            if (value is string text)
            {
                return GameObjectReader.Clean(text);
            }

            Type type = value.GetType();
            if (type.IsPrimitive || value is decimal || value is DateTime || value is TimeSpan || type.IsEnum)
            {
                return GameObjectReader.Clean(Convert.ToString(value, CultureInfo.InvariantCulture));
            }

            return GameObjectReader.Clean(type.Name);
        }

        private static string DescribeCount(object value)
        {
            if (value == null)
            {
                return "null";
            }

            if (value is ICollection collection)
            {
                return collection.Count.ToString(CultureInfo.InvariantCulture);
            }

            object count = ReadMember(value, "Count");
            return count == null ? Describe(value) : Describe(count);
        }

        private static string Format(double value)
        {
            return value.ToString("0.###", CultureInfo.InvariantCulture);
        }

        private static string Format(Vector3d vector)
        {
            return GameObjectReader.FormatVector(vector);
        }

        private static string FormatCount(int value)
        {
            return value < 0 ? "unknown" : value.ToString(CultureInfo.InvariantCulture);
        }

        private static void AppendPair(StringBuilder builder, string key, string value)
        {
            if (builder.Length > 0)
            {
                builder.Append(' ');
            }

            builder.Append(key);
            builder.Append("=\"");
            builder.Append(GameObjectReader.Clean(value));
            builder.Append('"');
        }

        private sealed class ControlledDryRunRequest
        {
            public ControlledDryRunRequest(string experimentId, string requestedUtc)
            {
                ExperimentId = experimentId;
                RequestedUtc = requestedUtc;
            }

            public string ExperimentId { get; }

            public string RequestedUtc { get; }
        }

        private sealed class SelectedScopeCandidate
        {
            public SelectedScopeCandidate(string source, object value)
            {
                Source = source;
                Value = value;
            }

            public string Source { get; }

            public object Value { get; }
        }

        private sealed class SelectedScopeEvidence
        {
            public string Source { get; set; } = "none";

            public string MissingReason { get; set; } = "selectedScopeUnavailable";

            public List<string> Ids { get; } = new List<string>();

            public List<string> Names { get; } = new List<string>();

            public List<string> TeamIds { get; } = new List<string>();

            public HashSet<string> SeenIds { get; } = new HashSet<string>();

            public int Count => Ids.Count;
        }

        private sealed class CommandScopeEvidence
        {
            public string Source { get; set; } = "none";

            public string MissingReason { get; set; } = "playerControlledScopeUnavailable";

            public List<string> Ids { get; } = new List<string>();

            public List<string> Names { get; } = new List<string>();

            public List<string> TeamIds { get; } = new List<string>();

            public bool CommandAuthorityKnown { get; set; }

            public bool CanPerformCommands { get; set; }

            public bool MissileCommandKnown { get; set; }

            public bool CanFireMissiles { get; set; }

            public int Count => Ids.Count;

            public bool ContainsShip(string shipId)
            {
                return HasConcreteToken(shipId) && Ids.Contains(shipId);
            }

            public static CommandScopeEvidence FromSelectedScope(SelectedScopeEvidence selectedScope)
            {
                CommandScopeEvidence evidence = new CommandScopeEvidence
                {
                    Source = string.IsNullOrWhiteSpace(selectedScope.Source)
                        ? "selectedCommandPanel"
                        : selectedScope.Source,
                    MissingReason = "none",
                    CommandAuthorityKnown = true,
                    CanPerformCommands = true,
                    MissileCommandKnown = true,
                    CanFireMissiles = true
                };
                evidence.Ids.AddRange(selectedScope.Ids);
                evidence.Names.AddRange(selectedScope.Names);
                evidence.TeamIds.AddRange(selectedScope.TeamIds);
                return evidence;
            }
        }

        private sealed class CommandCandidateDecision
        {
            public int CycleId { get; set; }

            public string CandidateId { get; set; } = "unknown";

            public string Classification { get; set; } = "wouldSkip";

            public string Reason { get; set; } = "unsafeScope";

            public bool ScopeViolation { get; set; }

            public string CommandScopeSource { get; set; } = "none";

            public string CommandScopeMissingReason { get; set; } = "playerControlledScopeUnavailable";

            public int CommandScopeShipCount { get; set; }

            public string LauncherId { get; set; } = "unknown";

            public string LauncherName { get; set; } = "unknown";

            public string WeaponId { get; set; } = "unknown";

            public string MissileProfileId { get; set; } = "unknown";

            public string TargetId { get; set; } = "unknown";

            public string TargetName { get; set; } = "unknown";

            public int AssignedShots { get; set; }

            public int AmmoGateBudgetShots { get; set; } = -1;

            public CommandCandidateDecision Fail(string classification, string reason)
            {
                Classification = string.IsNullOrWhiteSpace(classification) ? "wouldFail" : classification;
                Reason = string.IsNullOrWhiteSpace(reason) ? "unknown" : reason;
                return this;
            }
        }
    }
}
