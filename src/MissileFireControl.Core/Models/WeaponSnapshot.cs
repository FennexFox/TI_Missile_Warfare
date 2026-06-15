namespace MissileFireControl.Core.Models
{
    public sealed class WeaponSnapshot
    {
        public string Id { get; set; }
        public string DisplayName { get; set; }
        public WeaponRole Role { get; set; }
        public double PointDefenseWeight { get; set; }
        public double ThreatWeight { get; set; }
        public bool CanDefendOtherShips { get; set; }
        public double SupportRangeKm { get; set; }
        public int ReadyShots { get; set; }
        public int RemainingShots { get; set; }
    }
}
