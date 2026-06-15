using MissileFireControl.Core.Allocation;

namespace MissileFireControl.Mod.Diagnostics
{
    internal static class DecisionLogSink
    {
        public static void LogAllocationResult(AllocationResult result)
        {
            if (result == null || Main.Settings == null || !Main.Settings.EnableDiagnostics)
            {
                return;
            }

            Log.Info($"Allocation result: ready={result.TotalReadyShots}, assigned={result.AssignedShots}, unassigned={result.UnassignedShots}");
            foreach (TargetAllocation allocation in result.Allocations)
            {
                Log.Info($"  assign {allocation.AssignedShots} -> {allocation.TargetName} ({allocation.Reason}); score={allocation.ScorePerShot:0.00}, pd={allocation.PdScore:0.0}, kill={allocation.KillSize}, launch={allocation.LaunchWindowScore:0.00}");
            }

            foreach (TargetAllocation rejection in result.Rejections)
            {
                Log.Info($"  reject {rejection.TargetName}: {rejection.Reason}; pd={rejection.PdScore:0.0}, kill={rejection.KillSize}, launch={rejection.LaunchWindowScore:0.00}");
            }
        }
    }
}
