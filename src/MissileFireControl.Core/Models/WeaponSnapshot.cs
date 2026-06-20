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
        public int AmmoGateBudgetShots { get; set; }
        public int RemainingShots { get; set; }
        public string AmmoGateBudgetEvidenceSource { get; set; }
        public string AmmoGateBudgetMissingReason { get; set; }
        public string AmmoEvidenceSource { get; set; }
        public string LiveWeaponState { get; set; }
        public int AmmoGateWeaponCount { get; set; } = -1;
        public int UnknownAmmoGateWeaponCount { get; set; }
    }
}
