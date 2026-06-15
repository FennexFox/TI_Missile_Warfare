using System;
using MissileFireControl.Core.Models;

namespace MissileFireControl.Core.Calculators
{
    public sealed class LaunchWindowEvaluator
    {
        private readonly LaunchWindowOptions _options;

        public LaunchWindowEvaluator(LaunchWindowOptions options)
        {
            _options = options ?? new LaunchWindowOptions();
        }

        public LaunchWindowResult Evaluate(ShipSnapshot launcher, ShipSnapshot target, MissileProfile missile)
        {
            if (launcher == null || target == null)
            {
                return new LaunchWindowResult
                {
                    Score = 0.0,
                    IsAcceptable = false,
                    Reason = "missing launcher or target"
                };
            }

            double nominalRange = Math.Max(1.0, missile == null ? 800.0 : missile.NominalRangeKm);
            Vector3d relativePosition = target.PositionKm - launcher.PositionKm;
            Vector3d relativeVelocity = target.VelocityKps - launcher.VelocityKps;
            double distance = relativePosition.Length();
            Vector3d lineOfSight = relativePosition.Normalized();
            double radial = Vector3d.Dot(relativeVelocity, lineOfSight); // positive means target is receding.
            double relativeSpeedSq = relativeVelocity.X * relativeVelocity.X + relativeVelocity.Y * relativeVelocity.Y + relativeVelocity.Z * relativeVelocity.Z;
            double lateralSq = Math.Max(0.0, relativeSpeedSq - radial * radial);
            double lateral = Math.Sqrt(lateralSq);

            double maxUsefulRange = nominalRange * _options.MaxOverNominalRangeFactor;
            double rangeScore = 1.0 - (distance / maxUsefulRange);
            double radialAdjustment = radial >= 0.0
                ? -radial * _options.RecedingPenaltyPerKps
                : -radial * _options.ApproachingBonusPerKps;
            double lateralAdjustment = -lateral * _options.LateralPenaltyPerKps;
            double score = Clamp01(rangeScore + radialAdjustment + lateralAdjustment);

            return new LaunchWindowResult
            {
                Score = score,
                DistanceKm = distance,
                RadialVelocityKps = radial,
                LateralVelocityKps = lateral,
                IsAcceptable = score >= _options.MinimumLaunchScore,
                Reason = score >= _options.MinimumLaunchScore ? "acceptable" : "outside estimated launch window"
            };
        }

        private static double Clamp01(double value)
        {
            if (value < 0.0) return 0.0;
            if (value > 1.0) return 1.0;
            return value;
        }
    }
}
