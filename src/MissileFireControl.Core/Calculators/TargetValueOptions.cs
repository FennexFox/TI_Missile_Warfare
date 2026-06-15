namespace MissileFireControl.Core.Calculators
{
    public sealed class TargetValueOptions
    {
        public TargetValueOptions()
        {
            ThreatMultiplier = 8.0;
            PdRemovalMultiplier = 5.0;
            HullClassMultiplier = 10.0;
            DamagedVulnerabilityBonus = 6.0;
            DisabledPenaltyMultiplier = 0.15;
            MinimumValue = 1.0;
        }

        public double ThreatMultiplier { get; set; }
        public double PdRemovalMultiplier { get; set; }
        public double HullClassMultiplier { get; set; }
        public double DamagedVulnerabilityBonus { get; set; }
        public double DisabledPenaltyMultiplier { get; set; }
        public double MinimumValue { get; set; }
    }
}
