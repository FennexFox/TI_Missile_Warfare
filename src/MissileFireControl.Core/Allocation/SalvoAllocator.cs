using System;
using System.Collections.Generic;
using System.Linq;
using MissileFireControl.Core.Calculators;
using MissileFireControl.Core.Models;

namespace MissileFireControl.Core.Allocation
{
    public sealed class SalvoAllocator
    {
        private readonly PDScoreCalculator _pdScoreCalculator;
        private readonly TargetValueCalculator _targetValueCalculator;
        private readonly SalvoPackageCalculator _salvoPackageCalculator;
        private readonly LaunchWindowEvaluator _launchWindowEvaluator;

        public SalvoAllocator(
            PDScoreCalculator pdScoreCalculator,
            TargetValueCalculator targetValueCalculator,
            SalvoPackageCalculator salvoPackageCalculator,
            LaunchWindowEvaluator launchWindowEvaluator)
        {
            _pdScoreCalculator = pdScoreCalculator;
            _targetValueCalculator = targetValueCalculator;
            _salvoPackageCalculator = salvoPackageCalculator;
            _launchWindowEvaluator = launchWindowEvaluator;
        }

        public AllocationResult Allocate(AllocationRequest request)
        {
            AllocationResult result = new AllocationResult();
            if (request == null)
            {
                return result;
            }

            int ammoGateBudgetShots = request.MissileInventories.Sum(x => Math.Max(0, x.AmmoGateBudgetShots));
            result.TotalAmmoGateBudgetShots = ammoGateBudgetShots;
            result.UnassignedShots = ammoGateBudgetShots;

            if (ammoGateBudgetShots <= 0 || request.EnemyTargets.Count == 0)
            {
                return result;
            }

            double remainingMissileFactor = Math.Min(2.0, Math.Max(0.25, ammoGateBudgetShots / 24.0));
            List<TargetCandidate> candidates = new List<TargetCandidate>();

            foreach (ShipSnapshot target in request.EnemyTargets)
            {
                double pdScore = _pdScoreCalculator.Calculate(target, request.EnemyFleet);
                double value = _targetValueCalculator.Calculate(target, remainingMissileFactor);
                SalvoPackage package = _salvoPackageCalculator.Calculate(target, request.Missile, pdScore);
                LaunchWindowResult launchWindow = BestLaunchWindow(request.FriendlyLaunchers, target, request.Missile);

                double launchThreshold = request.MinimumLaunchWindowScore > 0.0
                    ? request.MinimumLaunchWindowScore
                    : 0.35;

                TargetAllocation allocation = new TargetAllocation
                {
                    TargetId = target.Id,
                    TargetName = target.DisplayName,
                    TargetValue = value,
                    PdScore = pdScore,
                    SaturationSize = package.SaturationSize,
                    KillSize = package.KillSize,
                    LaunchWindowScore = launchWindow.Score
                };

                if (!launchWindow.IsAcceptable || launchWindow.Score < launchThreshold)
                {
                    allocation.Reason = launchWindow.Reason;
                    result.Rejections.Add(allocation);
                    continue;
                }

                if (package.KillSize <= 0)
                {
                    allocation.Reason = "invalid package size";
                    result.Rejections.Add(allocation);
                    continue;
                }

                double scorePerShot = value * Math.Max(0.1, launchWindow.Score) / package.KillSize;
                allocation.ScorePerShot = scorePerShot;
                allocation.Reason = "candidate";

                candidates.Add(new TargetCandidate
                {
                    Ship = target,
                    Allocation = allocation,
                    Package = package,
                    ScorePerShot = scorePerShot
                });
            }

            foreach (TargetCandidate candidate in candidates.OrderByDescending(x => x.ScorePerShot))
            {
                if (ammoGateBudgetShots <= 0)
                {
                    break;
                }

                int assigned = 0;
                if (ammoGateBudgetShots >= candidate.Package.KillSize)
                {
                    assigned = candidate.Package.KillSize;
                }
                else if (request.AllowPartialSaturation && ammoGateBudgetShots >= candidate.Package.SaturationSize)
                {
                    assigned = ammoGateBudgetShots;
                }

                if (assigned <= 0)
                {
                    candidate.Allocation.Reason = "not enough ammo/gate budget shots to form a useful package";
                    result.Rejections.Add(candidate.Allocation);
                    continue;
                }

                candidate.Allocation.AssignedShots = assigned;
                candidate.Allocation.Reason = assigned >= candidate.Package.KillSize ? "kill package" : "partial saturation package";
                result.Allocations.Add(candidate.Allocation);
                ammoGateBudgetShots -= assigned;
            }

            result.AssignedShots = result.Allocations.Sum(x => x.AssignedShots);
            result.UnassignedShots = Math.Max(0, result.TotalAmmoGateBudgetShots - result.AssignedShots);
            return result;
        }

        private LaunchWindowResult BestLaunchWindow(IEnumerable<ShipSnapshot> launchers, ShipSnapshot target, MissileProfile missile)
        {
            LaunchWindowResult best = null;
            foreach (ShipSnapshot launcher in launchers)
            {
                LaunchWindowResult candidate = _launchWindowEvaluator.Evaluate(launcher, target, missile);
                if (best == null || candidate.Score > best.Score)
                {
                    best = candidate;
                }
            }

            return best ?? new LaunchWindowResult
            {
                Score = 0.0,
                IsAcceptable = false,
                Reason = "no launcher"
            };
        }

        private sealed class TargetCandidate
        {
            public ShipSnapshot Ship { get; set; }
            public TargetAllocation Allocation { get; set; }
            public SalvoPackage Package { get; set; }
            public double ScorePerShot { get; set; }
        }
    }
}
