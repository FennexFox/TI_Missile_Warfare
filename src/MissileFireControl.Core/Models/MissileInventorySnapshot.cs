namespace MissileFireControl.Core.Models
{
    public sealed class MissileInventorySnapshot
    {
        public string LauncherShipId { get; set; }
        public string WeaponId { get; set; }
        public string MissileProfileId { get; set; }
        public int ReadyShots { get; set; }
        public int RemainingShots { get; set; }
    }
}
