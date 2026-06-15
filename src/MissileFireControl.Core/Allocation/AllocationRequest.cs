using System.Collections.Generic;
using MissileFireControl.Core.Models;

namespace MissileFireControl.Core.Allocation
{
    public sealed class AllocationRequest
    {
        public AllocationRequest()
        {
            FriendlyLaunchers = new List<ShipSnapshot>();
            EnemyTargets = new List<ShipSnapshot>();
            EnemyFleet = new List<ShipSnapshot>();
            MissileInventories = new List<MissileInventorySnapshot>();
            AllowPartialSaturation = true;
        }

        public List<ShipSnapshot> FriendlyLaunchers { get; private set; }
        public List<ShipSnapshot> EnemyTargets { get; private set; }
        public List<ShipSnapshot> EnemyFleet { get; private set; }
        public List<MissileInventorySnapshot> MissileInventories { get; private set; }
        public MissileProfile Missile { get; set; }
        public bool AllowPartialSaturation { get; set; }
        public double MinimumLaunchWindowScore { get; set; }
    }
}
