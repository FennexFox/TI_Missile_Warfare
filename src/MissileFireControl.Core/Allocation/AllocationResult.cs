using System.Collections.Generic;

namespace MissileFireControl.Core.Allocation
{
    public sealed class AllocationResult
    {
        public AllocationResult()
        {
            Allocations = new List<TargetAllocation>();
            Rejections = new List<TargetAllocation>();
        }

        public int TotalReadyShots { get; set; }
        public int AssignedShots { get; set; }
        public int UnassignedShots { get; set; }
        public List<TargetAllocation> Allocations { get; private set; }
        public List<TargetAllocation> Rejections { get; private set; }
    }
}
