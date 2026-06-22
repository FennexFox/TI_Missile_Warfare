using HarmonyLib;
using MissileFireControl.Mod.Diagnostics;
using MissileFireControl.Mod.Patches;
using UnityEngine;
using UnityModManagerNet;

namespace MissileFireControl.Mod
{
    public static class Main
    {
        internal static UnityModManager.ModEntry ModEntry { get; private set; }
        internal static ModSettings Settings { get; private set; }

        private static Harmony _harmony;
        private static bool _enabled;

        public static bool Load(UnityModManager.ModEntry modEntry)
        {
            ModEntry = modEntry;
            Log.Initialize(modEntry);
            Settings = ModSettings.Load<ModSettings>(modEntry);

            modEntry.OnToggle = OnToggle;
            modEntry.OnGUI = OnGUI;
            modEntry.OnSaveGUI = OnSaveGUI;

            _harmony = new Harmony(modEntry.Info.Id);
            _harmony.PatchAll(typeof(Main).Assembly);
            PatchBootstrap.Apply(_harmony);

            Log.Info("File log: " + Log.FileLogPath);
            Log.Info("MissileWarfare loaded. Current build is scaffold/logging-first only.");
            return true;
        }

        private static bool OnToggle(UnityModManager.ModEntry modEntry, bool value)
        {
            _enabled = value;
            Log.Info(value ? "MissileWarfare enabled." : "MissileWarfare disabled.");
            return true;
        }

        private static void OnGUI(UnityModManager.ModEntry modEntry)
        {
            GUILayout.Label("MissileWarfare - scaffold build");
            GUILayout.Label("Controlled command apply is default-off and requires an explicit one-shot trigger.");

            Settings.EnableDiagnostics = GUILayout.Toggle(Settings.EnableDiagnostics, "Enable diagnostic logging");
            Settings.EnableSnapshotDiagnostics = GUILayout.Toggle(
                Settings.EnableSnapshotDiagnostics,
                "Enable battle snapshot diagnostics");
            Settings.EnableShadowAllocationDiagnostics = GUILayout.Toggle(
                Settings.EnableShadowAllocationDiagnostics,
                "Enable shadow allocation diagnostics (log-only)");
            Settings.EnableControlledDryRunDiagnostics = GUILayout.Toggle(
                Settings.EnableControlledDryRunDiagnostics,
                "Enable controlled command experiment diagnostics");
            Settings.AllowCommandApply = GUILayout.Toggle(
                Settings.AllowCommandApply,
                "Allow controlled command apply (selected group, capped)");
            Settings.EnableRecommendationOnlyMode = GUILayout.Toggle(Settings.EnableRecommendationOnlyMode, "Recommendation-only mode");
            Settings.EnableLaunchDiscipline = GUILayout.Toggle(Settings.EnableLaunchDiscipline, "Enable launch-discipline checks (placeholder)");

            GUILayout.BeginHorizontal();
            GUILayout.Label("Launch score threshold", GUILayout.Width(180));
            string thresholdText = GUILayout.TextField(Settings.MinimumLaunchScore.ToString("0.00"), GUILayout.Width(80));
            if (double.TryParse(thresholdText, out double threshold))
            {
                Settings.MinimumLaunchScore = Clamp(threshold, 0.0, 1.0);
            }
            GUILayout.EndHorizontal();

            if (GUILayout.Button("Write diagnostic ping"))
            {
                Log.Info("Diagnostic ping from UMM panel.");
            }

            if (GUILayout.Button("Trigger controlled command experiment"))
            {
                Log.Info(ShadowAllocationDiagnostics.RequestControlledDryRun());
            }
        }

        private static void OnSaveGUI(UnityModManager.ModEntry modEntry)
        {
            Settings.Save(modEntry);
        }

        internal static bool IsEnabled()
        {
            return _enabled;
        }

        private static double Clamp(double value, double min, double max)
        {
            if (value < min) return min;
            if (value > max) return max;
            return value;
        }
    }
}
