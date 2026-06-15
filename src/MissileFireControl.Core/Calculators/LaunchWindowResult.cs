namespace MissileFireControl.Core.Calculators
{
    public sealed class LaunchWindowResult
    {
        public double Score { get; set; }
        public double DistanceKm { get; set; }
        public double RadialVelocityKps { get; set; }
        public double LateralVelocityKps { get; set; }
        public bool IsAcceptable { get; set; }
        public string Reason { get; set; }
    }
}
