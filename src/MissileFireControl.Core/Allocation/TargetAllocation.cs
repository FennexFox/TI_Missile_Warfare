namespace MissileFireControl.Core.Allocation
{
    public sealed class TargetAllocation
    {
        public string TargetId { get; set; }
        public string TargetName { get; set; }
        public int AssignedShots { get; set; }
        public double ScorePerShot { get; set; }
        public double TargetValue { get; set; }
        public double PdScore { get; set; }
        public int SaturationSize { get; set; }
        public int KillSize { get; set; }
        public double LaunchWindowScore { get; set; }
        public string Reason { get; set; }
    }
}
