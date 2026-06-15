using System;
using MissileFireControl.Core.Models;

namespace MissileFireControl.Core.Calculators
{
    public sealed class TargetValueCalculator
    {
        private readonly TargetValueOptions _options;
        private readonly PDScoreCalculator _pdScoreCalculator;

        public TargetValueCalculator(TargetValueOptions options, PDScoreCalculator pdScoreCalculator)
        {
            _options = options ?? new TargetValueOptions();
            _pdScoreCalculator = pdScoreCalculator;
        }

        public double Calculate(ShipSnapshot target, double remainingFriendlyMissileFactor)
        {
            if (target == null)
            {
                return 0.0;
            }

            double threat = WeaponThreat(target) * _options.ThreatMultiplier;
            double ownPd = _pdScoreCalculator == null ? 0.0 : _pdScoreCalculator.OwnPd(target);
            double pdRemoval = ownPd * _options.PdRemovalMultiplier * Math.Max(0.0, remainingFriendlyMissileFactor);
            double hullValue = HullValue(target.HullClass) * _options.HullClassMultiplier;
            double vulnerability = (1.0 - Clamp01(target.RemainingHullFraction)) * _options.DamagedVulnerabilityBonus;
            double value = (threat + pdRemoval + hullValue + vulnerability) * Math.Max(0.25, target.StrategicPriority);

            if (target.IsDisabled)
            {
                value *= _options.DisabledPenaltyMultiplier;
            }

            return Math.Max(_options.MinimumValue, value);
        }

        private static double WeaponThreat(ShipSnapshot ship)
        {
            if (ship == null || ship.Weapons == null)
            {
                return 0.0;
            }

            double score = 0.0;
            foreach (WeaponSnapshot weapon in ship.Weapons)
            {
                if (weapon == null)
                {
                    continue;
                }

                score += Math.Max(0.0, weapon.ThreatWeight);
            }

            return score;
        }

        private static double HullValue(HullClass hullClass)
        {
            switch (hullClass)
            {
                case HullClass.Small:
                    return 1.0;
                case HullClass.Medium:
                    return 2.0;
                case HullClass.Large:
                    return 3.5;
                case HullClass.Capital:
                    return 5.0;
                default:
                    return 2.0;
            }
        }

        private static double Clamp01(double value)
        {
            if (value < 0.0) return 0.0;
            if (value > 1.0) return 1.0;
            return value;
        }
    }
}
