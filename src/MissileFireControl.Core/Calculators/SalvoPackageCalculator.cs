using System;
using MissileFireControl.Core.Models;

namespace MissileFireControl.Core.Calculators
{
    public sealed class SalvoPackageCalculator
    {
        private readonly SalvoPackageOptions _options;

        public SalvoPackageCalculator(SalvoPackageOptions options)
        {
            _options = options ?? new SalvoPackageOptions();
        }

        public SalvoPackage Calculate(ShipSnapshot target, MissileProfile missile, double pdScore)
        {
            int requiredLeakers = EstimateRequiredLeakers(target, missile);
            int saturation = Math.Max(1, (int)Math.Ceiling(pdScore) + _options.SaturationLeakerBuffer);
            int kill = Math.Max(saturation, (int)Math.Ceiling(pdScore) + requiredLeakers + Math.Max(0, missile == null ? 2 : missile.SafetyMargin));
            int overkill = Math.Max(kill + 1, kill + requiredLeakers + Math.Max(2, requiredLeakers / 2));

            return new SalvoPackage
            {
                PdScore = pdScore,
                RequiredLeakers = requiredLeakers,
                SaturationSize = saturation,
                KillSize = kill,
                OverkillSize = overkill
            };
        }

        private int EstimateRequiredLeakers(ShipSnapshot target, MissileProfile missile)
        {
            if (target == null)
            {
                return _options.MinimumRequiredLeakers;
            }

            double hullDurability = HullDurability(target.HullClass);
            double armorScore = Math.Max(0.0, Math.Max(target.FrontArmorScore, Math.Max(target.SideArmorScore, target.RearArmorScore)));
            double armorContribution = armorScore / Math.Max(1.0, _options.BaseArmorDivisor);
            double remaining = Math.Max(0.1, target.RemainingHullFraction);
            double damagePerLeaker = Math.Max(0.25, missile == null ? 1.0 : missile.DamagePerLeaker);

            int estimate = (int)Math.Ceiling((hullDurability + armorContribution) * remaining / damagePerLeaker);
            if (estimate < _options.MinimumRequiredLeakers)
            {
                estimate = _options.MinimumRequiredLeakers;
            }

            if (estimate > _options.MaximumRequiredLeakers)
            {
                estimate = _options.MaximumRequiredLeakers;
            }

            return estimate;
        }

        private static double HullDurability(HullClass hullClass)
        {
            switch (hullClass)
            {
                case HullClass.Small:
                    return 1.5;
                case HullClass.Medium:
                    return 3.0;
                case HullClass.Large:
                    return 5.0;
                case HullClass.Capital:
                    return 8.0;
                default:
                    return 3.0;
            }
        }
    }
}
