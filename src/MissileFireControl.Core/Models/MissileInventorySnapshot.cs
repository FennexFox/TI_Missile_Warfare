namespace MissileFireControl.Core.Models
{
    public sealed class MissileInventorySnapshot
    {
        public string LauncherShipId { get; set; }
        public string WeaponId { get; set; }
        public string MissileProfileId { get; set; }
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
