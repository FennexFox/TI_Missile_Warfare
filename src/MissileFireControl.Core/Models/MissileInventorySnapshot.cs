namespace MissileFireControl.Core.Models
{
    public sealed class MissileInventorySnapshot
    {
        public string LauncherShipId { get; set; }
        public string WeaponId { get; set; }
        public string MissileProfileId { get; set; }
        public int ReadyShots { get; set; }
        public int RemainingShots { get; set; }
        public string ReadyShotEvidenceSource { get; set; }
        public string ReadinessMissingReason { get; set; }
        public string AmmoEvidenceSource { get; set; }
        public string LiveWeaponState { get; set; }
        public int ReadyWeaponCount { get; set; } = -1;
        public int UnknownReadinessWeaponCount { get; set; }
    }
}
