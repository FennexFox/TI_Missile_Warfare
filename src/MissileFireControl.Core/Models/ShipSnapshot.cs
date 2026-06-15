using System.Collections.Generic;

namespace MissileFireControl.Core.Models
{
    public sealed class ShipSnapshot
    {
        public ShipSnapshot()
        {
            Weapons = new List<WeaponSnapshot>();
            StrategicPriority = 1.0;
            RemainingHullFraction = 1.0;
        }

        public string Id { get; set; }
        public string DisplayName { get; set; }
        public string TeamId { get; set; }
        public HullClass HullClass { get; set; }
        public Vector3d PositionKm { get; set; }
        public Vector3d VelocityKps { get; set; }
        public double FrontArmorScore { get; set; }
        public double SideArmorScore { get; set; }
        public double RearArmorScore { get; set; }
        public double RemainingHullFraction { get; set; }
        public bool IsDisabled { get; set; }
        public double StrategicPriority { get; set; }
        public List<WeaponSnapshot> Weapons { get; private set; }
    }
}
