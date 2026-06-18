using System;
using System.Globalization;
using System.Text;
using MissileFireControl.Core.Models;
using MissileFireControl.Mod.Adapters;

namespace MissileFireControl.Mod.Diagnostics
{
    internal static class SnapshotDiagnostics
    {
        public static void LogProjectileFireSnapshot(object projectile, object[] args)
        {
            if (!ShouldLog())
            {
                return;
            }

            try
            {
                ExtractedCombatSnapshot snapshot = CombatSnapshotExtractor.FromProjectileMissileFire(projectile, args);
                StringBuilder builder = new StringBuilder(512);
                AppendPair(builder, "source", snapshot.Source);
                AppendPair(builder, "launcherId", snapshot.Launcher == null ? "unknown" : snapshot.Launcher.Id);
                AppendPair(builder, "launcher", snapshot.Launcher == null ? "unknown" : snapshot.Launcher.DisplayName);
                AppendPair(builder, "launcherTeam", snapshot.Launcher == null ? "unknown" : snapshot.Launcher.TeamId);
                AppendPair(builder, "targetId", snapshot.Target == null ? "unknown" : snapshot.Target.Id);
                AppendPair(builder, "target", snapshot.Target == null ? "unknown" : snapshot.Target.DisplayName);
                AppendPair(builder, "expectedTargetPosition", snapshot.HasExpectedTargetPosition ? Format(snapshot.ExpectedTargetPositionKm) : "unknown");
                AppendPair(builder, "missileId", snapshot.Missile == null ? "unknown" : snapshot.Missile.Id);
                AppendPair(builder, "missile", snapshot.Missile == null ? "unknown" : snapshot.Missile.DisplayName);
                AppendPair(builder, "rangeKm", snapshot.Missile == null ? "unknown" : Format(snapshot.Missile.NominalRangeKm));
                AppendPair(builder, "velocityKps", snapshot.Missile == null ? "unknown" : Format(snapshot.Missile.EffectiveVelocityKps));
                AppendPair(builder, "weaponRole", WeaponRole(snapshot));
                AppendPair(builder, "readyShots", FormatCount(snapshot.Inventory == null ? -1 : snapshot.Inventory.ReadyShots));
                AppendPair(builder, "remainingShots", FormatCount(snapshot.Inventory == null ? -1 : snapshot.Inventory.RemainingShots));
                AppendPair(builder, "originPosition", snapshot.HasOriginPosition ? Format(snapshot.OriginPositionKm) : "unknown");
                AppendPair(builder, "originVelocityKps", snapshot.HasOriginVelocity ? Format(snapshot.OriginVelocityKps) : "unknown");
                AppendPair(builder, "missing", snapshot.MissingFields.Count == 0 ? "none" : string.Join(",", snapshot.MissingFields.ToArray()));
                Log.Info("[SnapshotLog] " + builder);
            }
            catch (Exception ex)
            {
                Log.Warning($"Snapshot diagnostics failed: {ex.GetType().Name}: {ex.Message}");
            }
        }

        private static bool ShouldLog()
        {
            return Main.IsEnabled()
                && Main.Settings != null
                && Main.Settings.EnableDiagnostics
                && Main.Settings.EnableSnapshotDiagnostics;
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

        private static string Format(Vector3d vector)
        {
            return GameObjectReader.FormatVector(vector);
        }

        private static string WeaponRole(ExtractedCombatSnapshot snapshot)
        {
            if (snapshot == null || snapshot.Launcher == null || snapshot.Launcher.Weapons.Count == 0)
            {
                return "unknown";
            }

            return snapshot.Launcher.Weapons[0].Role.ToString();
        }

        private static string Format(double value)
        {
            return value.ToString("0.###", CultureInfo.InvariantCulture);
        }

        private static string FormatCount(int value)
        {
            return value < 0 ? "unknown" : value.ToString(CultureInfo.InvariantCulture);
        }
    }
}
