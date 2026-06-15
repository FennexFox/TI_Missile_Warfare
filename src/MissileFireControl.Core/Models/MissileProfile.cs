namespace MissileFireControl.Core.Models
{
    public sealed class MissileProfile
    {
        public MissileProfile()
        {
            DamagePerLeaker = 1.0;
            NominalRangeKm = 800.0;
            EffectiveVelocityKps = 5.0;
            SafetyMargin = 2;
        }

        public string Id { get; set; }
        public string DisplayName { get; set; }
        public double NominalRangeKm { get; set; }
        public double EffectiveVelocityKps { get; set; }
        public double DamagePerLeaker { get; set; }
        public int SafetyMargin { get; set; }
    }
}
