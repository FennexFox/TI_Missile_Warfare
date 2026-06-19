using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;
using MissileFireControl.Core.Allocation;
using MissileFireControl.Core.Calculators;
using MissileFireControl.Core.Models;
using MissileFireControl.Mod.Adapters;

namespace MissileFireControl.Mod.Diagnostics
{
    internal static class ShadowAllocationDiagnostics
    {
        private static int _cycleSequence;

        public static void LogProjectileFireShadowAllocation(object projectile, object[] args)
        {
            if (!ShouldLog())
            {
                return;
            }

            try
            {
                ExtractedCombatSnapshot snapshot = CombatSnapshotExtractor.FromProjectileMissileFire(projectile, args);
                LogShadowCycle(snapshot);
            }
            catch (Exception ex)
            {
                Log.Warning($"Shadow allocation diagnostics failed: {ex.GetType().Name}: {ex.Message}");
            }
        }

        private static bool ShouldLog()
        {
            return Main.IsEnabled()
                && Main.Settings != null
                && Main.Settings.EnableDiagnostics
                && Main.Settings.EnableShadowAllocationDiagnostics;
        }

        private static void LogShadowCycle(ExtractedCombatSnapshot snapshot)
        {
            int cycleId = Interlocked.Increment(ref _cycleSequence);
            List<string> missingInputs = MissingInputs(snapshot);
            bool canAllocate = HasConcreteIdentity(snapshot == null ? null : snapshot.Launcher, "launcher")
                && snapshot.Target != null
                && HasConcreteMissile(snapshot == null ? null : snapshot.Missile);

            AllocationResult result = null;
            if (canAllocate)
            {
                AllocationRequest request = BuildRequest(snapshot);
                result = BuildAllocator().Allocate(request);
            }

            WriteCycleRecord(cycleId, snapshot, result, missingInputs, canAllocate);

            if (!canAllocate)
            {
                WriteSyntheticRejection(cycleId, snapshot, "missing required allocation inputs");
                return;
            }

            if (result == null)
            {
                WriteSyntheticRejection(cycleId, snapshot, "allocation result unavailable");
                return;
            }

            foreach (TargetAllocation allocation in result.Allocations)
            {
                WriteTargetRecord("allocation", cycleId, allocation, "reason", allocation.Reason);
            }

            foreach (TargetAllocation rejection in result.Rejections)
            {
                WriteTargetRecord("rejection", cycleId, rejection, "rejectionReason", rejection.Reason);
            }

            if (result.Allocations.Count == 0 && result.Rejections.Count == 0 && ReadyShots(snapshot) < 0)
            {
                WriteSyntheticRejection(cycleId, snapshot, "missing readyShots");
            }
        }

        private static AllocationRequest BuildRequest(ExtractedCombatSnapshot snapshot)
        {
            AllocationRequest request = new AllocationRequest
            {
                Missile = snapshot.Missile,
                MinimumLaunchWindowScore = Main.Settings == null ? 0.35 : Main.Settings.MinimumLaunchScore
            };

            request.FriendlyLaunchers.Add(snapshot.Launcher);
            request.EnemyTargets.Add(snapshot.Target);
            request.EnemyFleet.Add(snapshot.Target);
            request.MissileInventories.Add(new MissileInventorySnapshot
            {
                LauncherShipId = snapshot.Inventory == null ? snapshot.Launcher.Id : snapshot.Inventory.LauncherShipId,
                WeaponId = snapshot.Inventory == null ? "unknown" : snapshot.Inventory.WeaponId,
                MissileProfileId = snapshot.Missile.Id,
                ReadyShots = Math.Max(0, ReadyShots(snapshot)),
                RemainingShots = snapshot.Inventory == null ? -1 : snapshot.Inventory.RemainingShots
            });

            return request;
        }

        private static SalvoAllocator BuildAllocator()
        {
            PDScoreCalculator pdScoreCalculator = new PDScoreCalculator(new PdScoringOptions());
            TargetValueCalculator targetValueCalculator = new TargetValueCalculator(new TargetValueOptions(), pdScoreCalculator);
            return new SalvoAllocator(
                pdScoreCalculator,
                targetValueCalculator,
                new SalvoPackageCalculator(new SalvoPackageOptions()),
                new LaunchWindowEvaluator(new LaunchWindowOptions()));
        }

        private static List<string> MissingInputs(ExtractedCombatSnapshot snapshot)
        {
            List<string> missing = new List<string>();
            if (snapshot == null)
            {
                missing.Add("snapshot");
                return missing;
            }

            AddRange(missing, snapshot.MissingFields);

            if (!HasConcreteIdentity(snapshot.Launcher, "launcher"))
            {
                AddMissing(missing, "launcher");
            }

            if (!HasConcreteIdentity(snapshot.Target, "target"))
            {
                AddMissing(missing, "targetIdentity");
            }

            if (snapshot.Target == null || IsZero(snapshot.Target.VelocityKps))
            {
                AddMissing(missing, "targetVelocity");
            }

            if (ReadyShots(snapshot) < 0)
            {
                AddMissing(missing, "readyShots");
            }

            if (!HasConcreteMissile(snapshot.Missile))
            {
                AddMissing(missing, "missileProfileData");
            }

            AddMissing(missing, "pdWeightsDefaulted");
            return missing;
        }

        private static void WriteCycleRecord(
            int cycleId,
            ExtractedCombatSnapshot snapshot,
            AllocationResult result,
            List<string> missingInputs,
            bool canAllocate)
        {
            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", "cycle");
            AppendPair(builder, "cycleId", cycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "status", canAllocate ? "evaluated" : "skipped");
            AppendPair(builder, "sourceHook", snapshot == null ? "unknown" : snapshot.Source);
            AppendPair(builder, "battle", BattleContext());
            AppendPair(builder, "friendlyLaunchers", HasConcreteIdentity(snapshot == null ? null : snapshot.Launcher, "launcher") ? "1" : "0");
            AppendPair(builder, "targetCount", snapshot == null || snapshot.Target == null ? "0" : "1");
            AppendPair(builder, "totalReadyShots", ReadyShots(snapshot) < 0 ? "unknown" : ReadyShots(snapshot).ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "assignedShots", result == null ? "0" : result.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "unassignedShots", result == null || ReadyShots(snapshot) < 0 ? "unknown" : result.UnassignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "missingInputs", missingInputs == null || missingInputs.Count == 0 ? "none" : string.Join(",", missingInputs.ToArray()));
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteTargetRecord(
            string recordType,
            int cycleId,
            TargetAllocation allocation,
            string reasonKey,
            string reason)
        {
            StringBuilder builder = new StringBuilder(512);
            AppendPair(builder, "recordType", recordType);
            AppendPair(builder, "cycleId", cycleId.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "targetId", allocation == null ? "unknown" : allocation.TargetId);
            AppendPair(builder, "target", allocation == null ? "unknown" : allocation.TargetName);
            AppendPair(builder, "assignedShots", allocation == null ? "0" : allocation.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "pdScore", allocation == null ? "unknown" : Format(allocation.PdScore));
            AppendPair(builder, "targetValue", allocation == null ? "unknown" : Format(allocation.TargetValue));
            AppendPair(builder, "saturationSize", allocation == null ? "unknown" : allocation.SaturationSize.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "killSize", allocation == null ? "unknown" : allocation.KillSize.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "launchWindowScore", allocation == null ? "unknown" : Format(allocation.LaunchWindowScore));
            AppendPair(builder, "scorePerShot", allocation == null ? "unknown" : Format(allocation.ScorePerShot));
            AppendPair(builder, reasonKey, reason ?? "unknown");
            Log.Info("[AllocationLog] " + builder);
        }

        private static void WriteSyntheticRejection(int cycleId, ExtractedCombatSnapshot snapshot, string reason)
        {
            TargetAllocation rejection = new TargetAllocation
            {
                TargetId = snapshot == null || snapshot.Target == null ? "unknown" : snapshot.Target.Id,
                TargetName = snapshot == null || snapshot.Target == null ? "unknown" : snapshot.Target.DisplayName,
                AssignedShots = 0,
                Reason = reason
            };
            WriteTargetRecord("rejection", cycleId, rejection, "rejectionReason", reason);
        }

        private static int ReadyShots(ExtractedCombatSnapshot snapshot)
        {
            return snapshot == null || snapshot.Inventory == null ? -1 : snapshot.Inventory.ReadyShots;
        }

        private static bool HasConcreteMissile(MissileProfile missile)
        {
            return missile != null
                && !string.IsNullOrWhiteSpace(missile.Id)
                && !missile.Id.StartsWith("unknown-", StringComparison.Ordinal)
                && missile.NominalRangeKm > 0.0
                && missile.EffectiveVelocityKps > 0.0;
        }

        private static bool HasConcreteIdentity(ShipSnapshot ship, string fallbackPrefix)
        {
            if (ship == null || string.IsNullOrWhiteSpace(ship.Id))
            {
                return false;
            }

            if (ship.Id.StartsWith("unknown-", StringComparison.Ordinal))
            {
                return false;
            }

            return !ship.Id.StartsWith(fallbackPrefix + ":", StringComparison.Ordinal);
        }

        private static bool IsZero(Vector3d vector)
        {
            return Math.Abs(vector.X) < 1e-9 && Math.Abs(vector.Y) < 1e-9 && Math.Abs(vector.Z) < 1e-9;
        }

        private static void AddRange(List<string> values, IEnumerable<string> additions)
        {
            if (additions == null)
            {
                return;
            }

            foreach (string value in additions)
            {
                AddMissing(values, value);
            }
        }

        private static void AddMissing(List<string> values, string value)
        {
            if (string.IsNullOrWhiteSpace(value) || values.Contains(value))
            {
                return;
            }

            values.Add(value);
        }

        private static string BattleContext()
        {
            object spaceCombat = ReadStaticMember("GameControl", "spaceCombat")
                ?? ReadStaticMember("PavonisInteractive.TerraInvicta.GameControl", "spaceCombat");
            if (spaceCombat == null)
            {
                return "unavailable";
            }

            StringBuilder builder = new StringBuilder();
            AppendPair(builder, "combat", Describe(spaceCombat));
            AppendPair(builder, "initialized", Describe(ReadMember(spaceCombat, "initialized")));
            AppendPair(builder, "duration", Describe(ReadMember(spaceCombat, "combatDuration_s")));
            AppendPair(builder, "activeShips", DescribeCount(ReadMember(spaceCombat, "activeShips")));
            AppendPair(builder, "liveMissiles", DescribeCount(ReadMember(spaceCombat, "liveMissiles")));
            AppendPair(builder, "lastShot", Describe(ReadMember(spaceCombat, "timeOfLastShotFired")));
            return builder.ToString().Trim();
        }

        private static object ReadStaticMember(string typeName, string memberName)
        {
            Type type = AppDomain.CurrentDomain.GetAssemblies()
                .Select(assembly => assembly.GetType(typeName, throwOnError: false))
                .FirstOrDefault(candidate => candidate != null);
            if (type == null)
            {
                return null;
            }

            return ReadMember(type, null, memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
        }

        private static object ReadMember(object instance, string memberName)
        {
            if (instance == null || string.IsNullOrEmpty(memberName))
            {
                return null;
            }

            return ReadMember(instance.GetType(), instance, memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        }

        private static object ReadMember(Type type, object instance, string memberName, BindingFlags flags)
        {
            try
            {
                PropertyInfo property = type.GetProperty(memberName, flags);
                if (property != null && property.GetIndexParameters().Length == 0)
                {
                    return property.GetValue(instance, null);
                }

                FieldInfo field = type.GetField(memberName, flags);
                if (field != null)
                {
                    return field.GetValue(instance);
                }
            }
            catch
            {
                return null;
            }

            return null;
        }

        private static string Describe(object value)
        {
            if (value == null)
            {
                return "null";
            }

            if (value is string text)
            {
                return GameObjectReader.Clean(text);
            }

            Type type = value.GetType();
            if (type.IsPrimitive || value is decimal || value is DateTime || value is TimeSpan || type.IsEnum)
            {
                return GameObjectReader.Clean(Convert.ToString(value, CultureInfo.InvariantCulture));
            }

            return GameObjectReader.Clean(type.Name);
        }

        private static string DescribeCount(object value)
        {
            if (value == null)
            {
                return "null";
            }

            if (value is ICollection collection)
            {
                return collection.Count.ToString(CultureInfo.InvariantCulture);
            }

            object count = ReadMember(value, "Count");
            return count == null ? Describe(value) : Describe(count);
        }

        private static string Format(double value)
        {
            return value.ToString("0.###", CultureInfo.InvariantCulture);
        }

        private static void AppendPair(StringBuilder builder, string key, string value)
        {
            if (builder.Length > 0)
            {
                builder.Append(' ');
            }

            builder.Append(key);
            builder.Append("=\"");
            builder.Append(GameObjectReader.Clean(value));
            builder.Append('"');
        }
    }
}
