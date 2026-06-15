namespace MissileFireControl.Core.Calculators
{
    public sealed class SalvoPackageOptions
    {
        public SalvoPackageOptions()
        {
            BaseArmorDivisor = 4.0;
            MinimumRequiredLeakers = 1;
            MaximumRequiredLeakers = 12;
            SaturationLeakerBuffer = 1;
        }

        public double BaseArmorDivisor { get; set; }
        public int MinimumRequiredLeakers { get; set; }
        public int MaximumRequiredLeakers { get; set; }
        public int SaturationLeakerBuffer { get; set; }
    }
}
