namespace MissileFireControl.Core.Calculators
{
    public sealed class SalvoPackage
    {
        public double PdScore { get; set; }
        public int RequiredLeakers { get; set; }
        public int SaturationSize { get; set; }
        public int KillSize { get; set; }
        public int OverkillSize { get; set; }
    }
}
