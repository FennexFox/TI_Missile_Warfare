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
        private const string CommandApplyGateName = "controlledCommandApplyGate";
        private const int MaxSelectedGroupShipCount = 3;
        private const int MaxLiveCommandsPerControlledExperiment = 3;
        private const int FleetReportOnlyGlobalCommandCap = 12;
        private const int FleetReportOnlyPerShipCommandCap = 3;
        private const int FleetReportOnlyPerTargetCommandCap = 3;
        private const int FleetReportOnlyPerTriggerCommandCap = 12;
        private const int FleetReportOnlyMaxCandidateRows = 64;

        private static int _cycleSequence;
        private static int _experimentSequence;
        private static readonly object DryRunLock = new object();
        private static ControlledDryRunRequest _pendingDryRun;
        private static FleetWideReportRequest _pendingFleetWideReport;

        private static readonly string[] SelectedScopeMemberNames =
        {
            "groupSelectedFriendlyShips",
            "GroupSelectedFriendlyShips",
            "selectedFriendlyShipState",
            "selectedFriendlyShip",
            "SelectedFriendlyShipState",
            "SelectedFriendlyShip"
        };

        private static readonly string[] CanvasControllerRootMemberNames =
        {
            "combatHUD",
            "CombatHUD",
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

        private static readonly string[] FleetWideSourceMemberNames =
        {
            "leftHandCombatants",
            "LeftHandCombatants",
            "activePlayerCombatants",
            "ActivePlayerCombatants"
        };

        private static readonly string[] ActiveShipMemberNames =
        {
            "activeShips",
            "ActiveShips",
            "combatants",
            "Combatants",
            "allCombatants",
            "AllCombatants"
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
                return "Controlled command experiment not armed: mod is disabled.";
            }

            if (Main.Settings == null || !Main.Settings.EnableDiagnostics)
            {
                return "Controlled command experiment not armed: diagnostics are disabled.";
            }

            if (!Main.Settings.EnableShadowAllocationDiagnostics)
            {
                return "Controlled command experiment not armed: shadow allocation diagnostics are disabled.";
            }

            if (!Main.Settings.EnableControlledDryRunDiagnostics)
            {
                return "Controlled command experiment not armed: controlled command experiment diagnostics are disabled.";
            }

            string requestedUtc = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ", CultureInfo.InvariantCulture);
            string compactUtc = DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ", CultureInfo.InvariantCulture);
            string experimentId = "dryrun-" + compactUtc + "-" + Interlocked.Increment(ref _experimentSequence).ToString(CultureInfo.InvariantCulture);
            lock (DryRunLock)
            {
                if (_pendingDryRun != null)
                {
                    return "Controlled command experiment already armed: experimentId=" + _pendingDryRun.ExperimentId + ". Waiting for the selected ship to produce an eligible missile allocation candidate.";
                }

                _pendingDryRun = new ControlledDryRunRequest(experimentId, requestedUtc);
            }

            return "Controlled experiment armed: experimentId=" + experimentId + ". The selected-group experiment can apply at most one command per selected ship and at most three commands total when command apply is explicitly allowed.";
        }

        public static string RequestFleetWideDryRunReport()
        {
            if (!Main.IsEnabled())
            {
                return "Fleet-wide dry-run report not armed: mod is disabled.";
            }

            if (Main.Settings == null || !Main.Settings.EnableDiagnostics)
            {
                return "Fleet-wide dry-run report not armed: diagnostics are disabled.";
            }

            if (!Main.Settings.EnableShadowAllocationDiagnostics)
            {
                return "Fleet-wide dry-run report not armed: shadow allocation diagnostics are disabled.";
            }

            if (!Main.Settings.EnableFleetWideDryRunReportDiagnostics)
            {
                return "Fleet-wide dry-run report not armed: fleet-wide dry-run report diagnostics are disabled.";
            }

            string requestedUtc = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ", CultureInfo.InvariantCulture);
            string compactUtc = DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ", CultureInfo.InvariantCulture);
            string experimentId = "fleetwide-dryrun-" + compactUtc + "-" + Interlocked.Increment(ref _experimentSequence).ToString(CultureInfo.InvariantCulture);
            lock (DryRunLock)
            {
                if (_pendingFleetWideReport != null)
                {
                    return "Fleet-wide dry-run report already armed: experimentId=" + _pendingFleetWideReport.ExperimentId + ". Waiting for the next missile allocation cycle.";
                }

                _pendingFleetWideReport = new FleetWideReportRequest(experimentId, requestedUtc);
            }

            return "Fleet-wide dry-run report armed: experimentId=" + experimentId + ". This #43.1 report-only trigger cannot apply commands.";
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
            FleetWideReportRequest fleetReport = ConsumePendingFleetWideReport();
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
            WriteFleetWideReport(fleetReport, cycleId, snapshot, result, missingInputs, canAllocate);
            if (dryRun != null)
            {
                WriteDryRunExperimentRecord(dryRun, cycleId, snapshot, missingInputs, canAllocate, selectedScope, commandScope);
            }

            if (!canAllocate)
            {
                WriteNoOp(cycleId, snapshot, "missing required allocation inputs");
                RequeueIfWaitingForSelectedCandidate(dryRun, "missing required allocation inputs");
                WriteDryRunResult(dryRun, cycleId, 0, 1, 0, 0, "missing required allocation inputs");
                return;
            }

            if (result == null)
            {
                WriteNoOp(cycleId, snapshot, "allocation result unavailable");
                RequeueIfWaitingForSelectedCandidate(dryRun, "allocation result unavailable");
                WriteDryRunResult(dryRun, cycleId, 0, 1, 0, 0, "allocation result unavailable");
                return;
            }

            int allocationIndex = 0;
            int safetyGateBlockedCommands = 0;

            int appliedCommands = 0;
            int liveSkippedCommands = 0;
            int liveFailedCommands = 0;
            foreach (TargetAllocation allocation in result.Allocations)
            {
                allocationIndex++;
                WriteTargetRecord("allocation", cycleId, snapshot, allocation, "reason", allocation.Reason);
                WriteDryRunIntent(dryRun, cycleId, snapshot, allocation);
                CommandCandidateDecision candidate = BuildCommandCandidate(
                    cycleId,
                    allocationIndex,
                    snapshot,
                    allocation,
                    commandScope,
                    "allocatorAllocation",
                    false);
                commandCandidates.Add(candidate);
                WriteDryRunCommandCandidate(dryRun, candidate);
                if (candidate.Classification == "eligible")
                {
                    CommandApplyGateDecision gateDecision = EvaluateCommandApplyGate();
                    if (gateDecision.Blocked)
                    {
                        safetyGateBlockedCommands++;
                    }

                    WriteDryRunApplyGate(dryRun, candidate, gateDecision);
                    if (!gateDecision.Blocked)
                    {
                        CommandApplyResult applyResult = ApplyControlledCandidate(dryRun, candidate, snapshot);

                        if (applyResult.AppliedCommands > 0)
                        {
                            appliedCommands += applyResult.AppliedCommands;
                        }
                        else if (applyResult.FailedCommands > 0)
                        {
                            liveFailedCommands += applyResult.FailedCommands;
                        }
                        else
                        {
                            liveSkippedCommands++;
                        }

                        WriteControlledApplyResult(dryRun, candidate, applyResult);
                    }
                }
            }

            foreach (TargetAllocation rejection in result.Rejections)
            {
                WriteTargetRecord("rejection", cycleId, snapshot, rejection, "rejectionReason", rejection.Reason);
            }

            if (dryRun != null && commandCandidates.Count == 0 && result.Rejections.Count > 0)
            {
                CommandCandidateDecision candidate = BuildCommandCandidate(
                    cycleId,
                    1,
                    snapshot,
                    result.Rejections[0],
                    commandScope,
                    "selectedShipRejectedTarget",
                    true);
                commandCandidates.Add(candidate);
                WriteDryRunCommandCandidate(dryRun, candidate);
                if (candidate.Classification == "eligible")
                {
                    CommandApplyGateDecision gateDecision = EvaluateCommandApplyGate();
                    if (gateDecision.Blocked)
                    {
                        safetyGateBlockedCommands++;
                    }

                    WriteDryRunApplyGate(dryRun, candidate, gateDecision);
                    if (!gateDecision.Blocked)
                    {
                        CommandApplyResult applyResult = ApplyControlledCandidate(dryRun, candidate, snapshot);

                        if (applyResult.AppliedCommands > 0)
                        {
                            appliedCommands += applyResult.AppliedCommands;
                        }
                        else if (applyResult.FailedCommands > 0)
                        {
                            liveFailedCommands += applyResult.FailedCommands;
                        }
                        else
                        {
                            liveSkippedCommands++;
                        }

                        WriteControlledApplyResult(dryRun, candidate, applyResult);
                    }
                }
            }

            if (result.Allocations.Count == 0 && result.Rejections.Count == 0)
            {
                string noOpReason = NoOpReason(snapshot);
                WriteNoOp(cycleId, snapshot, noOpReason);
                RequeueIfWaitingForSelectedCandidate(dryRun, noOpReason);
                WriteDryRunResult(dryRun, cycleId, 0, 1, 0, 0, noOpReason);
                return;
            }

            if (commandCandidates.Count == 0)
            {
                RequeueIfWaitingForSelectedCandidate(dryRun, "no command candidate emitted");
                WriteDryRunResult(dryRun, cycleId, 0, result.Allocations.Count == 0 ? 1 : 0, 0, 0, "dryRunOnly");
                return;
            }

            bool waitingForSelectedCandidate = ShouldWaitForSelectedCandidate(
                dryRun,
                commandCandidates,
                appliedCommands,
                liveSkippedCommands,
                liveFailedCommands,
                safetyGateBlockedCommands,
                commandScope);
            if (waitingForSelectedCandidate)
            {
                RequeueControlledDryRun(dryRun);
                Log.Info("Controlled command experiment still armed: experimentId=" + dryRun.ExperimentId + ". Waiting for the selected ship to produce an eligible missile allocation candidate.");
            }

            WriteDryRunResult(
                dryRun,
                cycleId,
                commandCandidates.Count(candidate => candidate.Classification == "eligible"),
                commandCandidates.Count(candidate => candidate.Classification == "wouldSkip") + liveSkippedCommands,
                commandCandidates.Count(candidate => candidate.Classification == "wouldFail") + liveFailedCommands,
                safetyGateBlockedCommands,
                appliedCommands,
                waitingForSelectedCandidate
                    ? "waitingForSelectedCandidate"
                    : ControlledResultStatus(appliedCommands, liveSkippedCommands, liveFailedCommands, safetyGateBlockedCommands),
                waitingForSelectedCandidate
                    ? "waitingForSelectedLauncherCandidate"
                    : ControlledResultReason(appliedCommands, liveSkippedCommands, liveFailedCommands, safetyGateBlockedCommands));
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

        private static FleetWideReportRequest ConsumePendingFleetWideReport()
        {
            lock (DryRunLock)
            {
                if (_pendingFleetWideReport == null)
                {
                    return null;
                }

                if (Main.Settings == null || !Main.Settings.EnableFleetWideDryRunReportDiagnostics)
                {
                    _pendingFleetWideReport = null;
                    return null;
                }

                FleetWideReportRequest request = _pendingFleetWideReport;
                _pendingFleetWideReport = null;
                return request;
            }
        }

        private static void WriteFleetWideReport(
            FleetWideReportRequest request,
            int cycleId,
            ExtractedCombatSnapshot snapshot,
            AllocationResult result,
            List<string> missingInputs,
            bool canAllocate)
        {
            if (request == null)
            {
                return;
            }

            FleetWideScopeEvidence scope = CaptureFleetWideScopeEvidence();
            List<FleetWideLauncherEvidence> eligibleLaunchers = scope.Launchers
                .Where(launcher => launcher.Classification == "eligible")
                .ToList();
            List<FleetWideTargetEvidence> hostileTargets = scope.Targets
                .Where(target => target.Classification == "visibleHostile")
                .ToList();
            Dictionary<string, TargetAllocation> allocationsByTarget = result == null
                ? new Dictionary<string, TargetAllocation>()
                : result.Allocations
                    .Where(allocation => allocation != null && HasConcreteToken(allocation.TargetId))
                    .GroupBy(allocation => allocation.TargetId)
                    .ToDictionary(group => group.Key, group => group.First());

            int evaluatedCandidateCount = 0;
            int emittedCandidateRows = 0;
            int eligibleCandidateCount = 0;
            int capWouldBlockCount = 0;
            int missingEvidenceCount = 0;
            Dictionary<string, int> perShipCounts = new Dictionary<string, int>();
            Dictionary<string, int> perTargetCounts = new Dictionary<string, int>();

            foreach (FleetWideLauncherEvidence launcher in eligibleLaunchers)
            {
                foreach (FleetWideTargetEvidence target in hostileTargets)
                {
                    evaluatedCandidateCount++;
                    perShipCounts[launcher.Id] = perShipCounts.ContainsKey(launcher.Id) ? perShipCounts[launcher.Id] + 1 : 1;
                    perTargetCounts[target.Id] = perTargetCounts.ContainsKey(target.Id) ? perTargetCounts[target.Id] + 1 : 1;

                    TargetAllocation allocation;
                    bool hasAllocatorEvidence = allocationsByTarget.TryGetValue(target.Id, out allocation)
                        && snapshot != null
                        && snapshot.Launcher != null
                        && string.Equals(snapshot.Launcher.Id, launcher.Id, StringComparison.Ordinal);
                    string capReason = FleetReportOnlyCapReason(evaluatedCandidateCount, perShipCounts[launcher.Id], perTargetCounts[target.Id]);
                    if (capReason != "none")
                    {
                        capWouldBlockCount++;
                    }

                    if (!hasAllocatorEvidence)
                    {
                        missingEvidenceCount++;
                    }

                    if (capReason == "none" && hasAllocatorEvidence)
                    {
                        eligibleCandidateCount++;
                    }

                    if (emittedCandidateRows < FleetReportOnlyMaxCandidateRows)
                    {
                        WriteFleetWideCommandCandidate(
                            request,
                            cycleId,
                            evaluatedCandidateCount,
                            launcher,
                            target,
                            allocation,
                            hasAllocatorEvidence,
                            capReason);
                        emittedCandidateRows++;
                    }
                }
            }

            WriteFleetWideExperimentRecord(
                request,
                cycleId,
                snapshot,
                canAllocate,
                missingInputs,
                scope,
                evaluatedCandidateCount,
                emittedCandidateRows,
                eligibleCandidateCount,
                capWouldBlockCount,
                missingEvidenceCount);

            foreach (FleetWideLauncherEvidence launcher in scope.Launchers)
            {
                WriteFleetWideLauncherRecord(request, cycleId, launcher);
            }

            foreach (FleetWideTargetEvidence target in scope.Targets)
            {
                WriteFleetWideTargetRecord(request, cycleId, target);
            }

            WriteFleetWideCapStateRecord(
                request,
                cycleId,
                evaluatedCandidateCount,
                eligibleCandidateCount,
                capWouldBlockCount,
                emittedCandidateRows);

            WriteFleetWideResultRecord(
                request,
                cycleId,
                evaluatedCandidateCount,
                eligibleCandidateCount,
                scope.Launchers.Count - eligibleLaunchers.Count,
                hostileTargets.Count == 0 ? 1 : 0,
                capWouldBlockCount,
                missingEvidenceCount,
                emittedCandidateRows);
        }

        private static void WriteFleetWideExperimentRecord(
            FleetWideReportRequest request,
            int cycleId,
            ExtractedCombatSnapshot snapshot,
            bool canAllocate,
            List<string> missingInputs,
            FleetWideScopeEvidence scope,
            int evaluatedCandidateCount,
            int emittedCandidateRows,
            int eligibleCandidateCount,
            int capWouldBlockCount,
            int missingEvidenceCount)
        {
            StringBuilder builder = FleetWideRecordBuilder("fleetWideDryRunExperiment", request, cycleId);
            AppendPair(builder, "requestedUtc", request.RequestedUtc);
            AppendPair(builder, "sourceHook", snapshot == null ? "unknown" : snapshot.Source);
            AppendPair(builder, "status", canAllocate ? "evaluated" : "skipped");
            AppendPair(builder, "fleetEligibilitySource", scope.Source);
            AppendPair(builder, "fleetEligibilityConfidence", scope.Confidence);
            AppendPair(builder, "fleetEligibilityMissingReason", scope.Launchers.Count == 0 ? "sourceUnavailable" : "none");
            AppendPair(builder, "fleetEligibilitySourceCount", scope.Launchers.Count.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "visibleTargetSource", scope.TargetSource);
            AppendPair(builder, "visibleTargetConfidence", scope.TargetConfidence);
            AppendPair(builder, "visibleTargetMissingReason", scope.Targets.Count == 0 ? "sourceUnavailable" : "none");
            AppendPair(builder, "visibleTargetSourceCount", scope.Targets.Count.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "eligibleLaunchers", scope.Launchers.Count(launcher => launcher.Classification == "eligible").ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "excludedLaunchers", scope.Launchers.Count(launcher => launcher.Classification != "eligible").ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "visibleHostileTargets", scope.Targets.Count(target => target.Classification == "visibleHostile").ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "candidateRows", evaluatedCandidateCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "emittedCandidateRows", emittedCandidateRows.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "eligibleCandidateRows", eligibleCandidateCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "capWouldBlockCandidates", capWouldBlockCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missingAllocatorEvidenceCandidates", missingEvidenceCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missingInputs", missingInputs == null || missingInputs.Count == 0 ? "none" : string.Join(",", missingInputs.ToArray()));
            AppendPair(builder, "canAllocateCurrentSnapshot", canAllocate ? "True" : "False");
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteFleetWideLauncherRecord(FleetWideReportRequest request, int cycleId, FleetWideLauncherEvidence launcher)
        {
            StringBuilder builder = FleetWideRecordBuilder("fleetWideLauncher", request, cycleId);
            AppendPair(builder, "classification", launcher.Classification);
            AppendPair(builder, "reason", launcher.Reason);
            AppendPair(builder, "fleetEligibilitySource", launcher.Source);
            AppendPair(builder, "fleetEligibilityConfidence", launcher.Confidence);
            AppendPair(builder, "launcherId", launcher.Id);
            AppendPair(builder, "launcher", launcher.Name);
            AppendPair(builder, "launcherTeam", launcher.TeamId);
            AppendPair(builder, "playerControlEvidence", FormatNullableBool(launcher.PlayerControlled));
            AppendPair(builder, "commandAuthorityKnown", launcher.CommandAuthorityKnown ? "True" : "False");
            AppendPair(builder, "canPerformCommands", FormatNullableBool(launcher.CanPerformCommands));
            AppendPair(builder, "missileReadinessKnown", launcher.MissileReadinessKnown ? "True" : "False");
            AppendPair(builder, "canFireMissiles", FormatNullableBool(launcher.CanFireMissiles));
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteFleetWideTargetRecord(FleetWideReportRequest request, int cycleId, FleetWideTargetEvidence target)
        {
            StringBuilder builder = FleetWideRecordBuilder("fleetWideTarget", request, cycleId);
            AppendPair(builder, "classification", target.Classification);
            AppendPair(builder, "reason", target.Reason);
            AppendPair(builder, "targetId", target.Id);
            AppendPair(builder, "target", target.Name);
            AppendPair(builder, "targetTeam", target.TeamId);
            AppendPair(builder, "visibleTargetSource", target.Source);
            AppendPair(builder, "visibleTargetConfidence", target.Confidence);
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteFleetWideCommandCandidate(
            FleetWideReportRequest request,
            int cycleId,
            int candidateIndex,
            FleetWideLauncherEvidence launcher,
            FleetWideTargetEvidence target,
            TargetAllocation allocation,
            bool hasAllocatorEvidence,
            string capReason)
        {
            StringBuilder builder = FleetWideRecordBuilder("fleetWideCommandCandidate", request, cycleId);
            string candidateId = "cycle-" + cycleId.ToString(CultureInfo.InvariantCulture)
                + "-fleetwide-" + candidateIndex.ToString(CultureInfo.InvariantCulture);
            string reason = capReason != "none"
                ? capReason
                : hasAllocatorEvidence ? "none" : "missingAllocatorSnapshotEvidence";
            string classification = capReason != "none" ? "wouldSkip" : hasAllocatorEvidence ? "eligible" : "wouldSkip";
            AppendPair(builder, "candidateId", candidateId);
            AppendPair(builder, "classification", classification);
            AppendPair(builder, "reason", reason);
            AppendPair(builder, "candidateSource", hasAllocatorEvidence ? "currentAllocatorSnapshot" : "visibleTargetOnlyMissingAllocatorEvidence");
            AppendPair(builder, "commandIntent", "fleetWideSalvoTargetReportOnly");
            AppendPair(builder, "commandGranularity", "shipAllSalvoCapableWeapons");
            AppendPair(builder, "launcherId", launcher.Id);
            AppendPair(builder, "launcher", launcher.Name);
            AppendPair(builder, "launcherTeam", launcher.TeamId);
            AppendPair(builder, "allocatorLauncherId", hasAllocatorEvidence ? launcher.Id : "none");
            AppendPair(builder, "targetId", target.Id);
            AppendPair(builder, "target", target.Name);
            AppendPair(builder, "targetTeam", target.TeamId);
            AppendPair(builder, "assignedShots", hasAllocatorEvidence && allocation != null ? allocation.AssignedShots.ToString(CultureInfo.InvariantCulture) : "unknown");
            AppendPair(builder, "allocatorEvidence", hasAllocatorEvidence ? "currentAllocatorSnapshot" : "missingAllocatorSnapshotEvidence");
            AppendPair(builder, "pdScore", hasAllocatorEvidence && allocation != null ? Format(allocation.PdScore) : "unknown");
            AppendPair(builder, "targetValue", hasAllocatorEvidence && allocation != null ? Format(allocation.TargetValue) : "unknown");
            AppendPair(builder, "saturationSize", hasAllocatorEvidence && allocation != null ? allocation.SaturationSize.ToString(CultureInfo.InvariantCulture) : "unknown");
            AppendPair(builder, "killSize", hasAllocatorEvidence && allocation != null ? allocation.KillSize.ToString(CultureInfo.InvariantCulture) : "unknown");
            AppendPair(builder, "launchWindowScore", hasAllocatorEvidence && allocation != null ? Format(allocation.LaunchWindowScore) : "unknown");
            AppendPair(builder, "scorePerShot", hasAllocatorEvidence && allocation != null ? Format(allocation.ScorePerShot) : "unknown");
            AppendPair(builder, "fleetReportOnlyGlobalCommandCap", FleetReportOnlyGlobalCommandCap.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "fleetReportOnlyPerShipCommandCap", FleetReportOnlyPerShipCommandCap.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "fleetReportOnlyPerTargetCommandCap", FleetReportOnlyPerTargetCommandCap.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "fleetReportOnlyPerTriggerCommandCap", FleetReportOnlyPerTriggerCommandCap.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "fleetReportOnlyGlobalCapWouldBlock", capReason == "fleetReportOnlyGlobalCapWouldBlock" ? "True" : "False");
            AppendPair(builder, "fleetReportOnlyPerShipCapWouldBlock", capReason == "fleetReportOnlyPerShipCapWouldBlock" ? "True" : "False");
            AppendPair(builder, "fleetReportOnlyPerTargetCapWouldBlock", capReason == "fleetReportOnlyPerTargetCapWouldBlock" ? "True" : "False");
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteFleetWideCapStateRecord(
            FleetWideReportRequest request,
            int cycleId,
            int evaluatedCandidateCount,
            int eligibleCandidateCount,
            int capWouldBlockCount,
            int emittedCandidateRows)
        {
            StringBuilder builder = FleetWideRecordBuilder("fleetWideCapState", request, cycleId);
            AppendPair(builder, "candidateRows", evaluatedCandidateCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "eligibleCandidateRows", eligibleCandidateCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "capWouldBlockCandidates", capWouldBlockCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "emittedCandidateRows", emittedCandidateRows.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "fleetReportOnlyGlobalCommandCap", FleetReportOnlyGlobalCommandCap.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "fleetReportOnlyPerShipCommandCap", FleetReportOnlyPerShipCommandCap.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "fleetReportOnlyPerTargetCommandCap", FleetReportOnlyPerTargetCommandCap.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "fleetReportOnlyPerTriggerCommandCap", FleetReportOnlyPerTriggerCommandCap.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteFleetWideResultRecord(
            FleetWideReportRequest request,
            int cycleId,
            int evaluatedCandidateCount,
            int eligibleCandidateCount,
            int excludedLauncherCount,
            int noHostileTargetCount,
            int capWouldBlockCount,
            int missingEvidenceCount,
            int emittedCandidateRows)
        {
            StringBuilder builder = FleetWideRecordBuilder("fleetWideResult", request, cycleId);
            AppendPair(builder, "candidateRows", evaluatedCandidateCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "eligibleCandidateRows", eligibleCandidateCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "excludedLaunchers", excludedLauncherCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "noHostileTargets", noHostileTargetCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "capWouldBlockCandidates", capWouldBlockCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missingEvidenceCandidates", missingEvidenceCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "emittedCandidateRows", emittedCandidateRows.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "result", "reportOnly");
            AppendPair(builder, "resultReason", noHostileTargetCount > 0 ? "noHostileTargets" : "fleetWideReportOnly");
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static StringBuilder FleetWideRecordBuilder(string recordType, FleetWideReportRequest request, int cycleId)
        {
            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", recordType);
            AppendPair(builder, "scopeMode", "fleetWideReportOnly");
            AppendPair(builder, "experimentId", request.ExperimentId);
            AppendPair(builder, "cycleId", cycleId.ToString(CultureInfo.InvariantCulture));
            return builder;
        }

        private static string FleetReportOnlyCapReason(int globalCount, int perShipCount, int perTargetCount)
        {
            if (globalCount > FleetReportOnlyGlobalCommandCap || globalCount > FleetReportOnlyPerTriggerCommandCap)
            {
                return "fleetReportOnlyGlobalCapWouldBlock";
            }

            if (perShipCount > FleetReportOnlyPerShipCommandCap)
            {
                return "fleetReportOnlyPerShipCapWouldBlock";
            }

            if (perTargetCount > FleetReportOnlyPerTargetCommandCap)
            {
                return "fleetReportOnlyPerTargetCapWouldBlock";
            }

            return "none";
        }

        private static FleetWideScopeEvidence CaptureFleetWideScopeEvidence()
        {
            object spaceCombat = CurrentSpaceCombat();
            FleetWideScopeEvidence scope = new FleetWideScopeEvidence();
            List<object> sideShips = FirstNonEmptyObjects(FleetWideSourceCandidates(spaceCombat), out string sideSource);
            if (sideShips.Count > 0)
            {
                scope.Source = sideSource;
                scope.Confidence = "activePlayerSideCombatants";
            }
            else
            {
                sideShips = ActiveShipObjects(spaceCombat);
                scope.Source = sideShips.Count > 0 ? "GameControl.spaceCombat.activeShips(activePlayerFiltered)" : "none";
                scope.Confidence = sideShips.Count > 0 ? "fallbackActiveShipsFiltered" : "unavailable";
            }

            foreach (object ship in sideShips)
            {
                AddFleetWideLauncher(ship, scope);
            }

            List<object> activeShips = ActiveShipObjects(spaceCombat);
            scope.TargetSource = activeShips.Count > 0 ? "GameControl.spaceCombat.activeShips" : "none";
            scope.TargetConfidence = activeShips.Count > 0 ? "visibleCombatants" : "unavailable";
            string friendlyTeam = scope.FirstConcreteEligibleTeam();
            foreach (object ship in activeShips)
            {
                AddFleetWideTarget(ship, friendlyTeam, scope);
            }

            return scope;
        }

        private static void AddFleetWideLauncher(object value, FleetWideScopeEvidence scope)
        {
            object ship = UnwrapSelectedShip(value);
            if (ship == null)
            {
                return;
            }

            string id = GameObjectReader.StableId(ship, "fleetWideLauncher");
            if (!scope.SeenLauncherIds.Add(id))
            {
                return;
            }

            FleetWideLauncherEvidence launcher = new FleetWideLauncherEvidence
            {
                Id = id,
                Name = GameObjectReader.Label(ship, "fleetWideLauncher"),
                TeamId = GameObjectReader.TeamId(ship),
                Source = scope.Source,
                Confidence = scope.Confidence,
                RuntimeShip = ship,
                PlayerControlled = IsPlayerControlledShip(ship),
                CanPerformCommands = TryReadBool(ship, "CanPerformShipCommands"),
                CanFireMissiles = TryReadBool(ship, "AnyOffensiveMissileWeaponCanFire")
            };
            launcher.CommandAuthorityKnown = launcher.CanPerformCommands.HasValue;
            launcher.MissileReadinessKnown = launcher.CanFireMissiles.HasValue;
            ClassifyFleetWideLauncher(launcher);
            scope.Launchers.Add(launcher);
        }

        private static void AddFleetWideTarget(object value, string friendlyTeam, FleetWideScopeEvidence scope)
        {
            object ship = UnwrapSelectedShip(value);
            if (ship == null)
            {
                return;
            }

            string id = GameObjectReader.StableId(ship, "fleetWideTarget");
            if (!scope.SeenTargetIds.Add(id))
            {
                return;
            }

            FleetWideTargetEvidence target = new FleetWideTargetEvidence
            {
                Id = id,
                Name = GameObjectReader.Label(ship, "fleetWideTarget"),
                TeamId = GameObjectReader.TeamId(ship),
                Source = scope.TargetSource,
                Confidence = scope.TargetConfidence
            };
            ClassifyFleetWideTarget(target, friendlyTeam);
            scope.Targets.Add(target);
        }

        private static void ClassifyFleetWideLauncher(FleetWideLauncherEvidence launcher)
        {
            if (!HasConcreteToken(launcher.Id))
            {
                launcher.Classification = "wouldFail";
                launcher.Reason = "ambiguousLauncherIdentity";
            }
            else if (!HasConcreteTeam(launcher.TeamId))
            {
                launcher.Classification = "wouldSkip";
                launcher.Reason = "unknownTeam";
            }
            else if (!launcher.PlayerControlled.HasValue)
            {
                launcher.Classification = "wouldSkip";
                launcher.Reason = "unknownControl";
            }
            else if (!launcher.PlayerControlled.Value)
            {
                launcher.Classification = "wouldSkip";
                launcher.Reason = "notPlayerControlled";
            }
            else if (launcher.CommandAuthorityKnown && !launcher.CanPerformCommands.GetValueOrDefault())
            {
                launcher.Classification = "wouldSkip";
                launcher.Reason = "nonCombatShip";
            }
            else if (!launcher.MissileReadinessKnown || !launcher.CanFireMissiles.GetValueOrDefault())
            {
                launcher.Classification = "wouldSkip";
                launcher.Reason = "noVisibleMissileReadiness";
            }
            else
            {
                launcher.Classification = "eligible";
                launcher.Reason = "none";
            }
        }

        private static void ClassifyFleetWideTarget(FleetWideTargetEvidence target, string friendlyTeam)
        {
            if (!HasConcreteToken(target.Id))
            {
                target.Classification = "wouldFail";
                target.Reason = "ambiguousTargetIdentity";
            }
            else if (!HasConcreteTeam(target.TeamId) || !HasConcreteTeam(friendlyTeam))
            {
                target.Classification = "wouldSkip";
                target.Reason = "unknownTeam";
            }
            else if (string.Equals(target.TeamId, friendlyTeam, StringComparison.Ordinal))
            {
                target.Classification = "wouldSkip";
                target.Reason = "sameTeamTargetBlocked";
            }
            else
            {
                target.Classification = "visibleHostile";
                target.Reason = "none";
            }
        }

        private static IEnumerable<SelectedScopeCandidate> FleetWideSourceCandidates(object spaceCombat)
        {
            foreach (SelectedScopeCandidate candidate in FleetWideSourceCandidatesFromRoot("GameControl.spaceCombat", spaceCombat))
            {
                yield return candidate;
            }

            foreach (string rootMemberName in CanvasControllerRootMemberNames)
            {
                object controller = ReadMember(spaceCombat, rootMemberName);
                foreach (SelectedScopeCandidate candidate in FleetWideSourceCandidatesFromRoot("GameControl.spaceCombat." + rootMemberName, controller))
                {
                    yield return candidate;
                }
            }
        }

        private static IEnumerable<SelectedScopeCandidate> FleetWideSourceCandidatesFromRoot(string rootName, object root)
        {
            if (root == null)
            {
                yield break;
            }

            foreach (string memberName in FleetWideSourceMemberNames)
            {
                yield return new SelectedScopeCandidate(rootName + "." + memberName, ReadMember(root, memberName));
            }
        }

        private static List<object> ActiveShipObjects(object spaceCombat)
        {
            string unused;
            return FirstNonEmptyObjects(ActiveShipCandidates(spaceCombat), out unused);
        }

        private static IEnumerable<SelectedScopeCandidate> ActiveShipCandidates(object spaceCombat)
        {
            if (spaceCombat == null)
            {
                yield break;
            }

            foreach (string memberName in ActiveShipMemberNames)
            {
                yield return new SelectedScopeCandidate("GameControl.spaceCombat." + memberName, ReadMember(spaceCombat, memberName));
            }
        }

        private static List<object> FirstNonEmptyObjects(IEnumerable<SelectedScopeCandidate> candidates, out string source)
        {
            source = "none";
            foreach (SelectedScopeCandidate candidate in candidates)
            {
                List<object> objects = EnumerateObjects(candidate.Value).ToList();
                if (objects.Count == 0)
                {
                    continue;
                }

                source = candidate.Source;
                return objects;
            }

            return new List<object>();
        }

        private static IEnumerable<object> EnumerateObjects(object value)
        {
            if (value == null || value is string)
            {
                yield break;
            }

            if (value is IDictionary dictionary)
            {
                foreach (DictionaryEntry entry in dictionary)
                {
                    object selected = SelectDictionaryCombatObject(entry);
                    if (selected != null)
                    {
                        yield return selected;
                    }
                }

                yield break;
            }

            IEnumerable enumerable = value as IEnumerable;
            if (enumerable == null)
            {
                yield return value;
                yield break;
            }

            foreach (object item in enumerable)
            {
                if (item is DictionaryEntry entry)
                {
                    object selected = SelectDictionaryCombatObject(entry);
                    if (selected != null)
                    {
                        yield return selected;
                    }
                }
                else
                {
                    yield return item;
                }
            }
        }

        private static object SelectDictionaryCombatObject(DictionaryEntry entry)
        {
            object keyObject = UnwrapSelectedShip(entry.Key);
            object valueObject = UnwrapSelectedShip(entry.Value);
            bool keyLooksLikeShip = LooksLikeCombatShipObject(keyObject);
            bool valueLooksLikeShip = LooksLikeCombatShipObject(valueObject);

            if (keyLooksLikeShip && !valueLooksLikeShip)
            {
                return keyObject;
            }

            if (valueLooksLikeShip && !keyLooksLikeShip)
            {
                return valueObject;
            }

            if (valueLooksLikeShip)
            {
                return valueObject;
            }

            if (keyLooksLikeShip)
            {
                return keyObject;
            }

            return valueObject ?? keyObject;
        }

        private static bool LooksLikeCombatShipObject(object value)
        {
            if (value == null || value is string)
            {
                return false;
            }

            string teamId = GameObjectReader.TeamId(value);
            if (HasConcreteTeam(teamId))
            {
                return true;
            }

            return TryReadBool(value, "CanPerformShipCommands").HasValue
                || TryReadBool(value, "AnyOffensiveMissileWeaponCanFire").HasValue;
        }

        private static object CurrentSpaceCombat()
        {
            return ReadStaticMember("GameControl", "spaceCombat")
                ?? ReadStaticMember("PavonisInteractive.TerraInvicta.GameControl", "spaceCombat");
        }

        private static string FormatNullableBool(bool? value)
        {
            if (!value.HasValue)
            {
                return "unknown";
            }

            return value.Value ? "True" : "False";
        }

        private static void RequeueIfWaitingForSelectedCandidate(ControlledDryRunRequest request, string reason)
        {
            if (request == null)
            {
                return;
            }

            RequeueControlledDryRun(request);
            Log.Info("Controlled command experiment still armed: experimentId=" + request.ExperimentId + ". Waiting for the selected ship to produce an eligible missile allocation candidate. Last cycle reason=" + (reason ?? "unknown") + ".");
        }

        private static void RequeueControlledDryRun(ControlledDryRunRequest request)
        {
            if (request == null)
            {
                return;
            }

            lock (DryRunLock)
            {
                if (_pendingDryRun == null)
                {
                    _pendingDryRun = request;
                }
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
            AppendPair(builder, "selectedGroupMaxShips", MaxSelectedGroupShipCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "commandTriggerCap", MaxLiveCommandsPerControlledExperiment.ToString(CultureInfo.InvariantCulture));
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
            AppendPair(builder, "candidateSource", candidate.CandidateSource);
            AppendPair(builder, "commandIntent", "salvoTargetRecommendationDryRun");
            AppendPair(builder, "commandGranularity", "shipAllSalvoCapableWeapons");
            AppendPair(builder, "commandScopeSource", candidate.CommandScopeSource);
            AppendPair(builder, "commandScopeMissingReason", candidate.CommandScopeMissingReason);
            AppendPair(builder, "commandScopeShipCount", candidate.CommandScopeShipCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "selectedGroupMaxShips", MaxSelectedGroupShipCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "commandTriggerCap", MaxLiveCommandsPerControlledExperiment.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "launcherId", candidate.LauncherId);
            AppendPair(builder, "launcher", candidate.LauncherName);
            AppendPair(builder, "launcherTeam", candidate.CommandLauncherTeamId);
            AppendPair(builder, "allocatorLauncherId", candidate.AllocatorLauncherId);
            AppendPair(builder, "allocatorLauncher", candidate.AllocatorLauncherName);
            AppendPair(builder, "allocatorLauncherTeam", candidate.AllocatorLauncherTeamId);
            AppendPair(builder, "weaponId", candidate.WeaponId);
            AppendPair(builder, "missileProfileId", candidate.MissileProfileId);
            AppendPair(builder, "targetId", candidate.TargetId);
            AppendPair(builder, "target", candidate.TargetName);
            AppendPair(builder, "targetTeam", candidate.TargetTeamId);
            AppendPair(builder, "assignedShots", candidate.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missilesAssigned", candidate.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missilesSpent", "unknown");
            AppendPair(builder, "ammoGateBudgetShots", FormatCount(candidate.AmmoGateBudgetShots));
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteDryRunApplyGate(
            ControlledDryRunRequest request,
            CommandCandidateDecision candidate,
            CommandApplyGateDecision gateDecision)
        {
            if (request == null || candidate == null || gateDecision == null)
            {
                return;
            }

            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", "dryRunApplyGate");
            AppendPair(builder, "experimentId", request.ExperimentId);
            AppendPair(builder, "cycleId", candidate.CycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "candidateId", candidate.CandidateId);
            AppendPair(builder, "commandResultId", ControlledCommandResultId(request, candidate));
            AppendPair(builder, "gateName", CommandApplyGateName);
            AppendPair(builder, "gateResult", gateDecision.Result);
            AppendPair(builder, "blockReason", gateDecision.Reason);
            AppendPair(builder, "controlledExperimentMode", gateDecision.ControlledExperimentMode ? "True" : "False");
            AppendPair(builder, "allowCommandApply", gateDecision.AllowCommandApply ? "True" : "False");
            AppendPair(builder, "recommendationOnlyMode", gateDecision.RecommendationOnlyMode ? "True" : "False");
            AppendPair(builder, "candidateSource", candidate.CandidateSource);
            AppendPair(builder, "commandIntent", "salvoTargetRecommendationDryRun");
            AppendPair(builder, "commandGranularity", "shipAllSalvoCapableWeapons");
            AppendPair(builder, "launcherId", candidate.LauncherId);
            AppendPair(builder, "launcher", candidate.LauncherName);
            AppendPair(builder, "launcherTeam", candidate.CommandLauncherTeamId);
            AppendPair(builder, "allocatorLauncherId", candidate.AllocatorLauncherId);
            AppendPair(builder, "allocatorLauncher", candidate.AllocatorLauncherName);
            AppendPair(builder, "allocatorLauncherTeam", candidate.AllocatorLauncherTeamId);
            AppendPair(builder, "weaponId", candidate.WeaponId);
            AppendPair(builder, "missileProfileId", candidate.MissileProfileId);
            AppendPair(builder, "targetId", candidate.TargetId);
            AppendPair(builder, "target", candidate.TargetName);
            AppendPair(builder, "targetTeam", candidate.TargetTeamId);
            AppendPair(builder, "assignedShots", candidate.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missilesAssigned", candidate.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missilesSpent", "unknown");
            AppendPair(builder, "ammoGateBudgetShots", FormatCount(candidate.AmmoGateBudgetShots));
            AppendPair(builder, "preStateVisible", "candidateIdentity");
            AppendPair(builder, "postState", gateDecision.Blocked ? "notApplied" : "pendingLiveAttempt");
            AppendPair(builder, "appliedCommands", "0");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteControlledApplyResult(
            ControlledDryRunRequest request,
            CommandCandidateDecision candidate,
            CommandApplyResult result)
        {
            if (request == null || candidate == null || result == null)
            {
                return;
            }

            string commandResultId = ControlledCommandResultId(request, candidate);
            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", result.RecordType);
            AppendPair(builder, "experimentId", request.ExperimentId);
            AppendPair(builder, "cycleId", candidate.CycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "candidateId", candidate.CandidateId);
            AppendPair(builder, "commandResultId", commandResultId);
            AppendPair(builder, "commandIntent", "salvoTargetRecommendationLiveApply");
            AppendPair(builder, "commandGranularity", "shipAllSalvoCapableWeapons");
            AppendPair(builder, "commandPath", "SelectSalvoTargetCommand.OnCommandExecute");
            AppendPair(builder, "candidateSource", candidate.CandidateSource);
            AppendPair(builder, "result", result.Result);
            AppendPair(builder, "reason", result.Reason);
            AppendPair(builder, "exceptionType", result.ExceptionType);
            AppendPair(builder, "commandScopeSource", candidate.CommandScopeSource);
            AppendPair(builder, "commandScopeMissingReason", candidate.CommandScopeMissingReason);
            AppendPair(builder, "commandScopeShipCount", candidate.CommandScopeShipCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "selectedGroupMaxShips", MaxSelectedGroupShipCount.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "commandTriggerCap", MaxLiveCommandsPerControlledExperiment.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "launcherId", candidate.LauncherId);
            AppendPair(builder, "launcher", candidate.LauncherName);
            AppendPair(builder, "launcherTeam", candidate.CommandLauncherTeamId);
            AppendPair(builder, "allocatorLauncherId", candidate.AllocatorLauncherId);
            AppendPair(builder, "allocatorLauncher", candidate.AllocatorLauncherName);
            AppendPair(builder, "allocatorLauncherTeam", candidate.AllocatorLauncherTeamId);
            AppendPair(builder, "weaponId", candidate.WeaponId);
            AppendPair(builder, "missileProfileId", candidate.MissileProfileId);
            AppendPair(builder, "targetId", candidate.TargetId);
            AppendPair(builder, "target", candidate.TargetName);
            AppendPair(builder, "targetTeam", candidate.TargetTeamId);
            AppendPair(builder, "assignedShots", candidate.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missilesAssigned", candidate.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missilesSpent", "unknown");
            AppendPair(builder, "ammoGateBudgetShots", FormatCount(candidate.AmmoGateBudgetShots));
            AppendPair(builder, "preStateVisible", result.PreStateVisible);
            AppendPair(builder, "postState", result.PostState);
            AppendPair(builder, "appliedCommands", result.AppliedCommands.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "failedCommands", result.FailedCommands.ToString(CultureInfo.InvariantCulture));
            Log.Info("[AllocationLog] " + builder);
        }

        private static string ControlledCommandResultId(ControlledDryRunRequest request, CommandCandidateDecision candidate)
        {
            string experimentId = request == null ? "unknown-experiment" : request.ExperimentId;
            string candidateId = candidate == null ? "unknown-candidate" : candidate.CandidateId;
            return experimentId + ":" + candidateId;
        }

        private static CommandApplyResult ApplyControlledCandidate(
            ControlledDryRunRequest dryRun,
            CommandCandidateDecision candidate,
            ExtractedCombatSnapshot snapshot)
        {
            if (dryRun == null || candidate == null)
            {
                return CommandApplyResult.Skipped("controlledExperimentUnavailable");
            }

            if (dryRun.HasReachedCommandCap(MaxLiveCommandsPerControlledExperiment))
            {
                return CommandApplyResult.Skipped("controlledGroupTriggerCapReached");
            }

            if (dryRun.HasAttempted(candidate.LauncherId))
            {
                return CommandApplyResult.Skipped("perShipCommandCapReached");
            }

            // #39 direct evidence showed duplicate selected-group kill packages
            // on the same target; cap the experiment's aggregate command budget
            // before invoking another ship-level vanilla salvo command.
            if (dryRun.WouldExceedTargetBudget(candidate.TargetId, candidate.AssignedShots))
            {
                dryRun.MarkAttempted(candidate.LauncherId);
                return CommandApplyResult.Skipped("targetAggregateControlledCommandCapReached");
            }

            dryRun.MarkAttempted(candidate.LauncherId);
            CommandApplyResult applyResult = TryApplyControlledCommand(
                dryRun,
                candidate,
                snapshot,
                ControlledCommandResultId(dryRun, candidate));
            if (applyResult.AppliedCommands > 0)
            {
                dryRun.MarkTargetBudget(candidate.TargetId, candidate.AssignedShots);
            }

            return applyResult;
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
            int safetyGateBlockedCommands,
            string resultReason)
        {
            WriteDryRunResult(
                request,
                cycleId,
                intendedCommands,
                skippedCommands,
                failedCommands,
                safetyGateBlockedCommands,
                0,
                "dryRunOnly",
                resultReason);
        }

        private static void WriteDryRunResult(
            ControlledDryRunRequest request,
            int cycleId,
            int intendedCommands,
            int skippedCommands,
            int failedCommands,
            int safetyGateBlockedCommands,
            int appliedCommands,
            string result,
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
            AppendPair(builder, "appliedCommands", appliedCommands.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "failedCommands", failedCommands.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "safetyGateBlockedCommands", safetyGateBlockedCommands.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "result", result ?? "dryRunOnly");
            AppendPair(builder, "resultReason", resultReason ?? "dryRunOnly");
            Log.Info("[AllocationLog] " + builder);
        }

        private static CommandApplyGateDecision EvaluateCommandApplyGate()
        {
            bool controlledExperimentMode = Main.Settings != null && Main.Settings.EnableControlledDryRunDiagnostics;
            bool allowCommandApply = Main.Settings != null && Main.Settings.AllowCommandApply;
            bool recommendationOnlyMode = Main.Settings == null || Main.Settings.EnableRecommendationOnlyMode;
            if (!controlledExperimentMode || !allowCommandApply)
            {
                return new CommandApplyGateDecision(
                    "blocked",
                    "blockedBySafetyToggle",
                    controlledExperimentMode,
                    allowCommandApply,
                    recommendationOnlyMode);
            }

            if (recommendationOnlyMode)
            {
                return new CommandApplyGateDecision(
                    "blocked",
                    "blockedByRecommendationOnlyMode",
                    controlledExperimentMode,
                    allowCommandApply,
                    recommendationOnlyMode);
            }

            return new CommandApplyGateDecision(
                "allowed",
                "none",
                controlledExperimentMode,
                allowCommandApply,
                recommendationOnlyMode);
        }

        private static CommandApplyResult TryApplyControlledCommand(
            ControlledDryRunRequest request,
            CommandCandidateDecision candidate,
            ExtractedCombatSnapshot snapshot,
            string commandResultId)
        {
            if (candidate == null || snapshot == null)
            {
                return CommandApplyResult.Failed("candidateOrSnapshotUnavailable");
            }

            if (!IsBoundedSelectedCommandScope(candidate))
            {
                return CommandApplyResult.Skipped("selectedBoundedGroupRequired");
            }

            if (!IsHostileSelectedCommandTarget(candidate))
            {
                return CommandApplyResult.Skipped("hostileTargetRequired");
            }

            object launcher = candidate.CommandLauncherRuntimeObject ?? snapshot.LauncherRuntimeObject;
            object target = snapshot.TargetRuntimeObject;
            if (launcher == null)
            {
                return CommandApplyResult.Failed("commandLauncherRuntimeObjectUnavailable");
            }

            if (target == null)
            {
                return CommandApplyResult.Failed("targetRuntimeObjectUnavailable");
            }

            if (!SameLoggedIdentity(launcher, candidate.LauncherId, "launcher"))
            {
                return CommandApplyResult.Failed("launcherIdentityMismatch");
            }

            if (!SameLoggedIdentity(target, candidate.TargetId, "target"))
            {
                return CommandApplyResult.Failed("targetIdentityMismatch");
            }

            Type commandType = ResolveType("SelectSalvoTargetCommand");
            if (commandType == null)
            {
                return CommandApplyResult.Failed("commandTypeUnavailable");
            }

            MethodInfo executeMethod = FindCompatibleMethod(commandType, "OnCommandExecute", launcher, target);
            if (executeMethod == null)
            {
                return CommandApplyResult.Failed("commandMethodUnavailable");
            }

            object command;
            try
            {
                command = Activator.CreateInstance(commandType);
            }
            catch (Exception ex)
            {
                return CommandApplyResult.Failed("commandCreateFailed", ex.GetType().Name);
            }

            try
            {
                CombatLaunchDiagnostics.RegisterControlledCommandContext(
                    commandResultId,
                    request == null ? "unknown" : request.ExperimentId,
                    candidate.CandidateId,
                    candidate.LauncherId,
                    candidate.LauncherName,
                    candidate.TargetId,
                    candidate.TargetName,
                    candidate.AssignedShots);
                executeMethod.Invoke(command, new[] { launcher, target });
            }
            catch (TargetInvocationException ex)
            {
                CombatLaunchDiagnostics.ClearControlledCommandContext(commandResultId);
                return CommandApplyResult.Failed(
                    "commandInvocationFailed",
                    ex.InnerException == null ? ex.GetType().Name : ex.InnerException.GetType().Name);
            }
            catch (Exception ex)
            {
                CombatLaunchDiagnostics.ClearControlledCommandContext(commandResultId);
                return CommandApplyResult.Failed("commandInvocationFailed", ex.GetType().Name);
            }

            return CommandApplyResult.Applied();
        }

        private static bool IsHostileSelectedCommandTarget(CommandCandidateDecision candidate)
        {
            return candidate != null
                && HasConcreteTeam(candidate.CommandLauncherTeamId)
                && HasConcreteTeam(candidate.AllocatorLauncherTeamId)
                && HasConcreteTeam(candidate.TargetTeamId)
                && string.Equals(candidate.CommandLauncherTeamId, candidate.AllocatorLauncherTeamId, StringComparison.Ordinal)
                && !string.Equals(candidate.CommandLauncherTeamId, candidate.TargetTeamId, StringComparison.Ordinal);
        }

        private static MethodInfo FindCompatibleMethod(Type type, string methodName, object firstArgument, object secondArgument)
        {
            if (type == null || firstArgument == null || secondArgument == null)
            {
                return null;
            }

            Type firstType = firstArgument.GetType();
            Type secondType = secondArgument.GetType();
            return type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
                .FirstOrDefault(method =>
                {
                    if (method.Name != methodName)
                    {
                        return false;
                    }

                    ParameterInfo[] parameters = method.GetParameters();
                    return parameters.Length == 2
                        && parameters[0].ParameterType.IsAssignableFrom(firstType)
                        && parameters[1].ParameterType.IsAssignableFrom(secondType);
                });
        }

        private static bool SameLoggedIdentity(object runtimeObject, string loggedId, string fallbackPrefix)
        {
            string runtimeId = GameObjectReader.StableId(runtimeObject, fallbackPrefix);
            return HasConcreteToken(runtimeId) && string.Equals(runtimeId, loggedId, StringComparison.Ordinal);
        }

        private static bool IsBoundedSelectedCommandScope(CommandCandidateDecision candidate)
        {
            return candidate != null
                && candidate.CommandScopeShipCount > 0
                && candidate.CommandScopeShipCount <= MaxSelectedGroupShipCount
                && IsSelectedCommandScopeSource(candidate.CommandScopeSource);
        }

        private static bool IsSelectedCommandScopeSource(string source)
        {
            if (string.IsNullOrWhiteSpace(source) || source == "activePlayerLauncher" || source == "none")
            {
                return false;
            }

            return source.IndexOf("selectedFriendlyShip", StringComparison.OrdinalIgnoreCase) >= 0
                || source.IndexOf("groupSelectedFriendlyShips", StringComparison.OrdinalIgnoreCase) >= 0;
        }

        private static string ControlledResultStatus(
            int appliedCommands,
            int skippedCommands,
            int failedCommands,
            int safetyGateBlockedCommands)
        {
            if (appliedCommands > 0)
            {
                return "firstLiveApply";
            }

            if (failedCommands > 0)
            {
                return "firstLiveApplyFailed";
            }

            if (skippedCommands > 0)
            {
                return "firstLiveApplySkipped";
            }

            return safetyGateBlockedCommands > 0 ? "dryRunOnly" : "dryRunOnly";
        }

        private static string ControlledResultReason(
            int appliedCommands,
            int skippedCommands,
            int failedCommands,
            int safetyGateBlockedCommands)
        {
            if (appliedCommands > 0)
            {
                return "applied";
            }

            if (failedCommands > 0)
            {
                return "commandApplyFailed";
            }

            if (skippedCommands > 0)
            {
                return "commandApplySkipped";
            }

            if (safetyGateBlockedCommands > 0)
            {
                bool recommendationOnlyMode = Main.Settings == null || Main.Settings.EnableRecommendationOnlyMode;
                bool allowCommandApply = Main.Settings != null && Main.Settings.AllowCommandApply;
                return allowCommandApply && recommendationOnlyMode
                    ? "blockedByRecommendationOnlyMode"
                    : "blockedBySafetyToggle";
            }

            return "dryRunOnly";
        }

        private static bool ShouldWaitForSelectedCandidate(
            ControlledDryRunRequest request,
            List<CommandCandidateDecision> candidates,
            int appliedCommands,
            int skippedCommands,
            int failedCommands,
            int safetyGateBlockedCommands,
            CommandScopeEvidence commandScope)
        {
            if (request == null || safetyGateBlockedCommands > 0)
            {
                return false;
            }

            if (request.HasReachedCommandCap(MaxLiveCommandsPerControlledExperiment)
                || request.HasAttemptedAll(commandScope))
            {
                return false;
            }

            if ((appliedCommands > 0 || skippedCommands > 0 || failedCommands > 0)
                && request.HasRemainingSelectedShips(commandScope))
            {
                return true;
            }

            if (candidates == null || candidates.Count == 0)
            {
                return true;
            }

            return candidates.All(candidate =>
                candidate != null
                && candidate.Classification == "wouldSkip"
                && IsWaitForSelectedCandidateReason(candidate.Reason));
        }

        private static bool IsWaitForSelectedCandidateReason(string reason)
        {
            return reason == "outsidePlayerControlledScope"
                || reason == "selectedScopeRequired"
                || reason == "requiresSingleSelectedShip"
                || reason == "allocatorLauncherOutsideSelectedShip"
                || reason == "allocatorLauncherOutsideSelectedGroup"
                || reason == "teamIdentityUnavailable"
                || reason == "allocatorLauncherOutsideSelectedTeam"
                || reason == "hostileTargetRequired"
                || reason == "unsafeScope";
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
            evidence.RuntimeShips.Add(launcher);
            evidence.PlayerControlById[snapshot.Launcher.Id] = true;
            evidence.CommandAuthorityById[snapshot.Launcher.Id] = canPerformCommands;
            evidence.MissileCommandById[snapshot.Launcher.Id] = canFireMissiles;
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
            CommandScopeEvidence commandScope,
            string candidateSource,
            bool allowRejectedTarget)
        {
            string allocatorLauncherId = snapshot == null || snapshot.Launcher == null ? "unknown" : snapshot.Launcher.Id;
            bool allocatorLauncherInSelectedScope = commandScope != null && commandScope.ContainsShip(allocatorLauncherId);

            string selectedLauncherId = allocatorLauncherInSelectedScope ? allocatorLauncherId : null;
            string selectedLauncherName = commandScope == null ? null : commandScope.NameFor(selectedLauncherId);
            string selectedLauncherTeam = commandScope == null ? "unknown" : commandScope.TeamFor(selectedLauncherId);
            CommandCandidateDecision candidate = new CommandCandidateDecision
            {
                CycleId = cycleId,
                CandidateId = "cycle-" + cycleId.ToString(CultureInfo.InvariantCulture)
                    + "-" + (allowRejectedTarget ? "rejected-target-" : "allocation-")
                    + allocationIndex.ToString(CultureInfo.InvariantCulture),
                CandidateSource = string.IsNullOrWhiteSpace(candidateSource) ? "allocatorAllocation" : candidateSource,
                Classification = "eligible",
                Reason = "none",
                CommandScopeSource = commandScope == null ? "none" : commandScope.Source,
                CommandScopeMissingReason = commandScope == null ? "playerControlledScopeUnavailable" : commandScope.MissingReason,
                CommandScopeShipCount = commandScope == null ? 0 : commandScope.Count,
                LauncherId = string.IsNullOrWhiteSpace(selectedLauncherId) ? "unknown" : selectedLauncherId,
                LauncherName = string.IsNullOrWhiteSpace(selectedLauncherName) ? "unknown" : selectedLauncherName,
                AllocatorLauncherId = allocatorLauncherId,
                AllocatorLauncherName = snapshot == null || snapshot.Launcher == null ? "unknown" : snapshot.Launcher.DisplayName,
                CommandLauncherTeamId = selectedLauncherTeam,
                AllocatorLauncherTeamId = snapshot == null || snapshot.Launcher == null ? "unknown" : snapshot.Launcher.TeamId,
                TargetTeamId = snapshot == null || snapshot.Target == null ? "unknown" : snapshot.Target.TeamId,
                CommandLauncherRuntimeObject = commandScope == null ? null : commandScope.RuntimeShipFor(selectedLauncherId),
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
                return candidate.Fail("wouldSkip", ScopeUnavailableReason(commandScope), true);
            }

            if (!IsSelectedCommandScopeSource(candidate.CommandScopeSource))
            {
                return candidate.Fail("wouldSkip", "selectedScopeRequired", true);
            }

            if (commandScope.Count > MaxSelectedGroupShipCount)
            {
                return candidate.Fail("wouldSkip", "selectedGroupTooBroad", true);
            }

            if (!commandScope.HasSingleConcreteTeam())
            {
                return candidate.Fail("wouldSkip", "mixedSelectedGroupTeam", true);
            }

            if (commandScope.Count == 1 && !allocatorLauncherInSelectedScope)
            {
                return candidate.Fail("wouldSkip", "allocatorLauncherOutsideSelectedShip", true);
            }

            if (commandScope.Count > 1 && !allocatorLauncherInSelectedScope)
            {
                return candidate.Fail("wouldSkip", "allocatorLauncherOutsideSelectedGroup", true);
            }

            if (!HasConcreteTeam(candidate.CommandLauncherTeamId)
                || !HasConcreteTeam(candidate.AllocatorLauncherTeamId)
                || !HasConcreteTeam(candidate.TargetTeamId))
            {
                return candidate.Fail("wouldSkip", "teamIdentityUnavailable", true);
            }

            if (!string.Equals(candidate.CommandLauncherTeamId, candidate.AllocatorLauncherTeamId, StringComparison.Ordinal))
            {
                return candidate.Fail("wouldSkip", "allocatorLauncherOutsideSelectedTeam", true);
            }

            if (string.Equals(candidate.CommandLauncherTeamId, candidate.TargetTeamId, StringComparison.Ordinal))
            {
                return candidate.Fail("wouldSkip", "hostileTargetRequired", true);
            }

            if (!HasConcreteToken(candidate.WeaponId))
            {
                return candidate.Fail("wouldFail", "missingWeaponIdentity");
            }

            if (!HasConcreteToken(candidate.TargetId))
            {
                return candidate.Fail("wouldFail", "missingTargetIdentity");
            }

            if (candidate.AssignedShots <= 0)
            {
                return candidate.Fail(
                    "wouldFail",
                    allowRejectedTarget ? "rejectedTargetNoPositiveAssignedShots" : "insufficientAmmo");
            }

            if (candidate.AmmoGateBudgetShots < candidate.AssignedShots)
            {
                return candidate.Fail("wouldFail", "insufficientAmmo");
            }

            if (commandScope.IsNonPlayerOrAiControlled(candidate.LauncherId))
            {
                return candidate.Fail("wouldSkip", "nonPlayerOrAIControlled", true);
            }

            if (!commandScope.PlayerControlKnownFor(candidate.LauncherId))
            {
                return candidate.Fail("wouldFail", "ambiguousCommandPath");
            }

            if (commandScope.CommandAuthorityKnownFor(candidate.LauncherId) && !commandScope.CanPerformCommandsFor(candidate.LauncherId))
            {
                return candidate.Fail("wouldFail", "ambiguousCommandPath");
            }

            if (!commandScope.CommandAuthorityKnownFor(candidate.LauncherId) || !commandScope.MissileCommandKnownFor(candidate.LauncherId))
            {
                return candidate.Fail("wouldFail", "ambiguousCommandPath");
            }

            if (!commandScope.CanFireMissilesFor(candidate.LauncherId))
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

        private static bool? IsPlayerControlledShip(object ship)
        {
            if (ship == null)
            {
                return null;
            }

            object activePlayer = ActivePlayer();
            if (activePlayer == null)
            {
                return null;
            }

            object activePlayerFaction = ReadMember(activePlayer, "faction")
                ?? ReadMember(activePlayer, "ref_faction")
                ?? activePlayer;

            object shipFaction = ReadMember(ship, "faction")
                ?? ReadMember(ship, "ref_faction")
                ?? ReadMember(ReadMember(ship, "fleet"), "faction");
            if (shipFaction == null)
            {
                return null;
            }

            if (!SameIdentity(shipFaction, activePlayerFaction, "faction"))
            {
                return false;
            }

            bool? combatAiControl = TryReadBool(ship, "combatAIControl", "CombatAIControl")
                ?? TryReadBool(ReadMember(ship, "ref_shipController"), "IsUnderAIControl", "isUnderAIControl")
                ?? TryReadBool(ReadMember(ship, "fleet"), "IsUnderAIControl", "isUnderAIControl");
            if (!combatAiControl.HasValue)
            {
                return null;
            }

            return !combatAiControl.Value;
        }

        private static object ActivePlayer()
        {
            object gameControl = ReadStaticMember("GameControl", "control")
                ?? ReadStaticMember("PavonisInteractive.TerraInvicta.GameControl", "control");

            return ReadMember(gameControl, "activePlayer")
                ?? ReadMember(gameControl, "humanPlayer")
                ?? ReadStaticMember("GameControl", "activePlayer")
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

        private static bool HasConcreteTeam(string value)
        {
            return HasConcreteToken(value) && value != "none";
        }

        private static string SingleTeamId(CommandScopeEvidence evidence)
        {
            return evidence != null && evidence.TeamIds.Count == 1 ? evidence.TeamIds[0] : "unknown";
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
            evidence.RuntimeShips.Add(ship);
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
            Type type = ResolveType(typeName);
            if (type == null)
            {
                return null;
            }

            return ReadMember(type, null, memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
        }

        private static Type ResolveType(string typeName)
        {
            if (string.IsNullOrWhiteSpace(typeName))
            {
                return null;
            }

            string terraInvictaTypeName = "PavonisInteractive.TerraInvicta." + typeName;
            return AppDomain.CurrentDomain.GetAssemblies()
                .Select(assembly => assembly.GetType(typeName, throwOnError: false)
                    ?? assembly.GetType(terraInvictaTypeName, throwOnError: false))
                .FirstOrDefault(candidate => candidate != null);
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

        private sealed class FleetWideReportRequest
        {
            public FleetWideReportRequest(string experimentId, string requestedUtc)
            {
                ExperimentId = experimentId;
                RequestedUtc = requestedUtc;
            }

            public string ExperimentId { get; }

            public string RequestedUtc { get; }
        }

        private sealed class FleetWideScopeEvidence
        {
            public string Source { get; set; } = "none";

            public string Confidence { get; set; } = "unavailable";

            public string TargetSource { get; set; } = "none";

            public string TargetConfidence { get; set; } = "unavailable";

            public List<FleetWideLauncherEvidence> Launchers { get; } = new List<FleetWideLauncherEvidence>();

            public List<FleetWideTargetEvidence> Targets { get; } = new List<FleetWideTargetEvidence>();

            public HashSet<string> SeenLauncherIds { get; } = new HashSet<string>();

            public HashSet<string> SeenTargetIds { get; } = new HashSet<string>();

            public string FirstConcreteEligibleTeam()
            {
                FleetWideLauncherEvidence launcher = Launchers.FirstOrDefault(candidate =>
                    candidate.Classification == "eligible" && HasConcreteTeam(candidate.TeamId));
                return launcher == null ? "unknown" : launcher.TeamId;
            }
        }

        private sealed class FleetWideLauncherEvidence
        {
            public string Id { get; set; } = "unknown";

            public string Name { get; set; } = "unknown";

            public string TeamId { get; set; } = "unknown";

            public string Source { get; set; } = "none";

            public string Confidence { get; set; } = "unavailable";

            public string Classification { get; set; } = "wouldSkip";

            public string Reason { get; set; } = "unknown";

            public object RuntimeShip { get; set; }

            public bool? PlayerControlled { get; set; }

            public bool? CanPerformCommands { get; set; }

            public bool? CanFireMissiles { get; set; }

            public bool CommandAuthorityKnown { get; set; }

            public bool MissileReadinessKnown { get; set; }
        }

        private sealed class FleetWideTargetEvidence
        {
            public string Id { get; set; } = "unknown";

            public string Name { get; set; } = "unknown";

            public string TeamId { get; set; } = "unknown";

            public string Source { get; set; } = "none";

            public string Classification { get; set; } = "wouldSkip";

            public string Reason { get; set; } = "unknown";

            public string Confidence { get; set; } = "unavailable";
        }

        private sealed class ControlledDryRunRequest
        {
            private readonly HashSet<string> _attemptedShipIds = new HashSet<string>();
            private readonly Dictionary<string, TargetBudget> _targetBudgets = new Dictionary<string, TargetBudget>();

            public ControlledDryRunRequest(string experimentId, string requestedUtc)
            {
                ExperimentId = experimentId;
                RequestedUtc = requestedUtc;
            }

            public string ExperimentId { get; }

            public string RequestedUtc { get; }

            public int AttemptedCommandCount => _attemptedShipIds.Count;

            public bool HasAttempted(string shipId)
            {
                return HasConcreteToken(shipId) && _attemptedShipIds.Contains(shipId);
            }

            public void MarkAttempted(string shipId)
            {
                if (HasConcreteToken(shipId))
                {
                    _attemptedShipIds.Add(shipId);
                }
            }

            public bool HasReachedCommandCap(int commandCap)
            {
                return commandCap > 0 && _attemptedShipIds.Count >= commandCap;
            }

            public bool WouldExceedTargetBudget(string targetId, int assignedShots)
            {
                if (!HasConcreteToken(targetId) || assignedShots <= 0)
                {
                    return false;
                }

                TargetBudget budget;
                if (!_targetBudgets.TryGetValue(targetId, out budget))
                {
                    return false;
                }

                int targetShotBudget = Math.Max(budget.MaxAssignedShots, assignedShots);
                return budget.AppliedAssignedShots + assignedShots > targetShotBudget;
            }

            public void MarkTargetBudget(string targetId, int assignedShots)
            {
                if (!HasConcreteToken(targetId) || assignedShots <= 0)
                {
                    return;
                }

                TargetBudget budget;
                if (!_targetBudgets.TryGetValue(targetId, out budget))
                {
                    budget = new TargetBudget();
                    _targetBudgets[targetId] = budget;
                }

                budget.MaxAssignedShots = Math.Max(budget.MaxAssignedShots, assignedShots);
                budget.AppliedAssignedShots += assignedShots;
            }

            public bool HasAttemptedAll(CommandScopeEvidence commandScope)
            {
                return commandScope != null
                    && commandScope.Count > 0
                    && commandScope.Count <= MaxSelectedGroupShipCount
                    && commandScope.Ids.All(HasAttempted);
            }

            public bool HasRemainingSelectedShips(CommandScopeEvidence commandScope)
            {
                return commandScope != null
                    && commandScope.Count > 0
                    && commandScope.Count <= MaxSelectedGroupShipCount
                    && commandScope.Ids.Any(id => !HasAttempted(id));
            }

            private sealed class TargetBudget
            {
                public int AppliedAssignedShots { get; set; }

                public int MaxAssignedShots { get; set; }
            }
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

            public List<object> RuntimeShips { get; } = new List<object>();

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

            public List<object> RuntimeShips { get; } = new List<object>();

            public bool CommandAuthorityKnown { get; set; }

            public bool CanPerformCommands { get; set; }

            public bool MissileCommandKnown { get; set; }

            public bool CanFireMissiles { get; set; }

            public Dictionary<string, bool?> PlayerControlById { get; } = new Dictionary<string, bool?>();

            public Dictionary<string, bool?> CommandAuthorityById { get; } = new Dictionary<string, bool?>();

            public Dictionary<string, bool?> MissileCommandById { get; } = new Dictionary<string, bool?>();

            public int Count => Ids.Count;

            public bool ContainsShip(string shipId)
            {
                return HasConcreteToken(shipId) && Ids.Contains(shipId);
            }

            public object RuntimeShipFor(string shipId)
            {
                int index = IndexOfShip(shipId);
                return index >= 0 && index < RuntimeShips.Count ? RuntimeShips[index] : null;
            }

            public string NameFor(string shipId)
            {
                int index = IndexOfShip(shipId);
                return index >= 0 && index < Names.Count ? Names[index] : null;
            }

            public string TeamFor(string shipId)
            {
                int index = IndexOfShip(shipId);
                return index >= 0 && index < TeamIds.Count ? TeamIds[index] : "unknown";
            }

            public bool HasSingleConcreteTeam()
            {
                if (TeamIds.Count == 0)
                {
                    return false;
                }

                string teamId = null;
                foreach (string candidate in TeamIds)
                {
                    if (!HasConcreteTeam(candidate))
                    {
                        return false;
                    }

                    if (teamId == null)
                    {
                        teamId = candidate;
                    }
                    else if (!string.Equals(teamId, candidate, StringComparison.Ordinal))
                    {
                        return false;
                    }
                }

                return true;
            }

            public bool PlayerControlKnownFor(string shipId)
            {
                bool? value;
                return PlayerControlById.TryGetValue(shipId ?? string.Empty, out value) && value.HasValue;
            }

            public bool IsNonPlayerOrAiControlled(string shipId)
            {
                bool? value;
                return PlayerControlById.TryGetValue(shipId ?? string.Empty, out value) && value.HasValue && !value.Value;
            }

            public bool CommandAuthorityKnownFor(string shipId)
            {
                bool? value;
                return CommandAuthorityById.TryGetValue(shipId ?? string.Empty, out value) && value.HasValue;
            }

            public bool CanPerformCommandsFor(string shipId)
            {
                bool? value;
                return CommandAuthorityById.TryGetValue(shipId ?? string.Empty, out value) && value.GetValueOrDefault();
            }

            public bool MissileCommandKnownFor(string shipId)
            {
                bool? value;
                return MissileCommandById.TryGetValue(shipId ?? string.Empty, out value) && value.HasValue;
            }

            public bool CanFireMissilesFor(string shipId)
            {
                bool? value;
                return MissileCommandById.TryGetValue(shipId ?? string.Empty, out value) && value.GetValueOrDefault();
            }

            private int IndexOfShip(string shipId)
            {
                return HasConcreteToken(shipId) ? Ids.IndexOf(shipId) : -1;
            }

            public static CommandScopeEvidence FromSelectedScope(SelectedScopeEvidence selectedScope)
            {
                CommandScopeEvidence evidence = new CommandScopeEvidence
                {
                    Source = string.IsNullOrWhiteSpace(selectedScope.Source)
                        ? "selectedCommandPanel"
                        : selectedScope.Source,
                    MissingReason = "none"
                };
                evidence.Ids.AddRange(selectedScope.Ids);
                evidence.Names.AddRange(selectedScope.Names);
                evidence.TeamIds.AddRange(selectedScope.TeamIds);
                evidence.RuntimeShips.AddRange(selectedScope.RuntimeShips);

                List<bool?> playerControl = new List<bool?>();
                List<bool?> commandAuthority = new List<bool?>();
                List<bool?> missileCommand = new List<bool?>();
                for (int index = 0; index < evidence.Ids.Count; index++)
                {
                    string shipId = evidence.Ids[index];
                    object ship = index < evidence.RuntimeShips.Count ? evidence.RuntimeShips[index] : null;
                    bool? playerControlled = IsPlayerControlledShip(ship);
                    bool? canPerformCommands = TryReadBool(ship, "CanPerformShipCommands");
                    bool? canFireMissiles = TryReadBool(ship, "AnyOffensiveMissileWeaponCanFire");
                    evidence.PlayerControlById[shipId] = playerControlled;
                    evidence.CommandAuthorityById[shipId] = canPerformCommands;
                    evidence.MissileCommandById[shipId] = canFireMissiles;
                    playerControl.Add(playerControlled);
                    commandAuthority.Add(canPerformCommands);
                    missileCommand.Add(canFireMissiles);
                }

                evidence.CommandAuthorityKnown = commandAuthority.Count > 0 && commandAuthority.All(value => value.HasValue);
                evidence.CanPerformCommands = evidence.CommandAuthorityKnown && commandAuthority.All(value => value.GetValueOrDefault());
                evidence.MissileCommandKnown = missileCommand.Count > 0 && missileCommand.All(value => value.HasValue);
                evidence.CanFireMissiles = evidence.MissileCommandKnown && missileCommand.All(value => value.GetValueOrDefault());
                if (playerControl.Any(value => value.HasValue && !value.Value))
                {
                    evidence.MissingReason = "nonPlayerOrAIControlled";
                }
                else if (playerControl.Any(value => !value.HasValue))
                {
                    evidence.MissingReason = "commandAuthorityUnavailable";
                }

                return evidence;
            }
        }

        private sealed class CommandCandidateDecision
        {
            public int CycleId { get; set; }

            public string CandidateId { get; set; } = "unknown";

            public string CandidateSource { get; set; } = "allocatorAllocation";

            public string Classification { get; set; } = "wouldSkip";

            public string Reason { get; set; } = "unsafeScope";

            public bool ScopeViolation { get; set; }

            public string CommandScopeSource { get; set; } = "none";

            public string CommandScopeMissingReason { get; set; } = "playerControlledScopeUnavailable";

            public int CommandScopeShipCount { get; set; }

            public string LauncherId { get; set; } = "unknown";

            public string LauncherName { get; set; } = "unknown";

            public string CommandLauncherTeamId { get; set; } = "unknown";

            public string AllocatorLauncherId { get; set; } = "unknown";

            public string AllocatorLauncherName { get; set; } = "unknown";

            public string AllocatorLauncherTeamId { get; set; } = "unknown";

            public string TargetTeamId { get; set; } = "unknown";

            public object CommandLauncherRuntimeObject { get; set; }

            public string WeaponId { get; set; } = "unknown";

            public string MissileProfileId { get; set; } = "unknown";

            public string TargetId { get; set; } = "unknown";

            public string TargetName { get; set; } = "unknown";

            public int AssignedShots { get; set; }

            public int AmmoGateBudgetShots { get; set; } = -1;

            public CommandCandidateDecision Fail(string classification, string reason, bool scopeViolation = false)
            {
                Classification = string.IsNullOrWhiteSpace(classification) ? "wouldFail" : classification;
                Reason = string.IsNullOrWhiteSpace(reason) ? "unknown" : reason;
                ScopeViolation = scopeViolation;
                return this;
            }
        }

        private sealed class CommandApplyGateDecision
        {
            public CommandApplyGateDecision(
                string result,
                string reason,
                bool controlledExperimentMode,
                bool allowCommandApply,
                bool recommendationOnlyMode)
            {
                Result = string.IsNullOrWhiteSpace(result) ? "blocked" : result;
                Reason = string.IsNullOrWhiteSpace(reason) ? "unknown" : reason;
                ControlledExperimentMode = controlledExperimentMode;
                AllowCommandApply = allowCommandApply;
                RecommendationOnlyMode = recommendationOnlyMode;
            }

            public string Result { get; }

            public string Reason { get; }

            public bool ControlledExperimentMode { get; }

            public bool AllowCommandApply { get; }

            public bool RecommendationOnlyMode { get; }

            public bool Blocked => Result == "blocked";
        }

        private sealed class CommandApplyResult
        {
            private CommandApplyResult(
                string recordType,
                string result,
                string reason,
                string exceptionType,
                string preStateVisible,
                string postState,
                int appliedCommands,
                int failedCommands)
            {
                RecordType = recordType;
                Result = result;
                Reason = string.IsNullOrWhiteSpace(reason) ? "unknown" : reason;
                ExceptionType = string.IsNullOrWhiteSpace(exceptionType) ? "none" : exceptionType;
                PreStateVisible = string.IsNullOrWhiteSpace(preStateVisible) ? "unknown" : preStateVisible;
                PostState = string.IsNullOrWhiteSpace(postState) ? "unknown" : postState;
                AppliedCommands = appliedCommands;
                FailedCommands = failedCommands;
            }

            public string RecordType { get; }

            public string Result { get; }

            public string Reason { get; }

            public string ExceptionType { get; }

            public string PreStateVisible { get; }

            public string PostState { get; }

            public int AppliedCommands { get; }

            public int FailedCommands { get; }

            public static CommandApplyResult Applied()
            {
                return new CommandApplyResult(
                    "appliedDecision",
                    "applied",
                    "none",
                    "none",
                    "runtimeObjects",
                    "commandInvoked",
                    1,
                    0);
            }

            public static CommandApplyResult Skipped(string reason)
            {
                return new CommandApplyResult(
                    "skippedDecision",
                    "skipped",
                    reason,
                    "none",
                    "candidateIdentity",
                    "notApplied",
                    0,
                    0);
            }

            public static CommandApplyResult Failed(string reason)
            {
                return Failed(reason, "none");
            }

            public static CommandApplyResult Failed(string reason, string exceptionType)
            {
                return new CommandApplyResult(
                    "failedCommand",
                    "failed",
                    reason,
                    exceptionType,
                    "candidateIdentity",
                    "notApplied",
                    0,
                    1);
            }
        }
    }
}
