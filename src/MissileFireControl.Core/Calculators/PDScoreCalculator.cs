using System;
using System.Collections.Generic;
using MissileFireControl.Core.Models;

namespace MissileFireControl.Core.Calculators
{
    public sealed class PDScoreCalculator
    {
        private readonly PdScoringOptions _options;

        public PDScoreCalculator(PdScoringOptions options)
        {
            _options = options ?? new PdScoringOptions();
        }

        public double Calculate(ShipSnapshot target, IEnumerable<ShipSnapshot> sameSideShips)
        {
            if (target == null)
            {
                return 0.0;
            }

            double score = OwnPd(target);

            if (sameSideShips == null)
            {
                return score;
            }

            foreach (ShipSnapshot supporter in sameSideShips)
            {
                if (supporter == null || supporter.Id == target.Id)
                {
                    continue;
                }

                double support = OwnPd(supporter);
                if (support <= 0.0)
                {
                    continue;
                }

                double rangeKm = MaxSupportRange(supporter);
                double distanceKm = Vector3d.Distance(target.PositionKm, supporter.PositionKm);
                double distanceWeight = DistanceWeight(distanceKm, rangeKm);
                if (distanceWeight <= 0.0)
                {
                    continue;
                }

                score += support * _options.SupportPdMultiplier * distanceWeight;
            }

            return Math.Max(0.0, score);
        }

        public double OwnPd(ShipSnapshot ship)
        {
            if (ship == null || ship.Weapons == null)
            {
                return 0.0;
            }

            double multiplier = ship.IsDisabled ? _options.DisabledShipMultiplier : 1.0;
            double score = 0.0;
            foreach (WeaponSnapshot weapon in ship.Weapons)
            {
                if (weapon == null)
                {
                    continue;
                }

                score += Math.Max(0.0, weapon.PointDefenseWeight);
            }

            return score * multiplier;
        }

        private double MaxSupportRange(ShipSnapshot ship)
        {
            double range = _options.DefaultSupportRangeKm;
            if (ship == null || ship.Weapons == null)
            {
                return range;
            }

            foreach (WeaponSnapshot weapon in ship.Weapons)
            {
                if (weapon == null || !weapon.CanDefendOtherShips)
                {
                    continue;
                }

                if (weapon.SupportRangeKm > range)
                {
                    range = weapon.SupportRangeKm;
                }
            }

            return Math.Max(1.0, range);
        }

        private double DistanceWeight(double distanceKm, double rangeKm)
        {
            if (distanceKm >= rangeKm)
            {
                return 0.0;
            }

            double t = 1.0 - (distanceKm / rangeKm);
            return Math.Max(_options.MinimumDistanceWeight, t);
        }
    }
}
