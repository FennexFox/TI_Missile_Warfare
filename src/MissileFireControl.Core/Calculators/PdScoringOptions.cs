namespace MissileFireControl.Core.Calculators
{
    public sealed class PdScoringOptions
    {
        public PdScoringOptions()
        {
            DefaultSupportRangeKm = 600.0;
            MinimumDistanceWeight = 0.1;
            SupportPdMultiplier = 0.75;
            DisabledShipMultiplier = 0.25;
        }

        public double DefaultSupportRangeKm { get; set; }
        public double MinimumDistanceWeight { get; set; }
        public double SupportPdMultiplier { get; set; }
        public double DisabledShipMultiplier { get; set; }
    }
}
