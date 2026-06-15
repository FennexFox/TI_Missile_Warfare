namespace MissileFireControl.Core.Calculators
{
    public sealed class LaunchWindowOptions
    {
        public LaunchWindowOptions()
        {
            MaxOverNominalRangeFactor = 1.25;
            RecedingPenaltyPerKps = 0.12;
            ApproachingBonusPerKps = 0.08;
            LateralPenaltyPerKps = 0.04;
            MinimumLaunchScore = 0.35;
        }

        public double MaxOverNominalRangeFactor { get; set; }
        public double RecedingPenaltyPerKps { get; set; }
        public double ApproachingBonusPerKps { get; set; }
        public double LateralPenaltyPerKps { get; set; }
        public double MinimumLaunchScore { get; set; }
    }
}
