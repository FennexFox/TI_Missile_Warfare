using System;
using System.Linq;
using System.Reflection;
using HarmonyLib;
using MissileFireControl.Mod.Diagnostics;

namespace MissileFireControl.Mod.Patches
{
    internal static class PatchBootstrap
    {
        private static bool _applied;

        public static void Apply(Harmony harmony)
        {
            if (_applied)
            {
                return;
            }

            if (harmony == null)
            {
                Log.Warning("Harmony patch bootstrap skipped: Harmony instance was null.");
                return;
            }

            _applied = true;
            int patched = 0;
            int skipped = 0;

            TryPatch(
                harmony,
                "primary ship fire hook",
                "PavonisInteractive.TerraInvicta.TISpaceShipState",
                "FireWeapon",
                new[] { "ModuleDataEntry", "PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState" },
                null,
                nameof(CombatLaunchDiagnostics.OnShipFireWeaponPostfix),
                ref patched,
                ref skipped);

            TryPatch(
                harmony,
                "secondary missile try-fire hook",
                "PavonisInteractive.TerraInvicta.Ship.MissileWeapon",
                "TryFire",
                new[] { "System.DateTime" },
                nameof(CombatLaunchDiagnostics.OnMissileTryFirePrefix),
                nameof(CombatLaunchDiagnostics.OnMissileTryFirePostfix),
                ref patched,
                ref skipped);

            TryPatch(
                harmony,
                "secondary missile projectile fire hook",
                "PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState",
                "Fire",
                new[]
                {
                    "PavonisInteractive.TerraInvicta.CombatWeaponCarrierState",
                    "TIMissileTemplate",
                    "TIDateTime",
                    "UnityEngine.Vector3",
                    "UnityEngine.Vector3",
                    "UnityEngine.Vector3"
                },
                null,
                nameof(CombatLaunchDiagnostics.OnProjectileMissileFirePostfix),
                ref patched,
                ref skipped);

            TryPatch(
                harmony,
                "outcome missile damage hook",
                "PavonisInteractive.TerraInvicta.SpaceCombat.MissileController",
                "ApplyDamage",
                new[] { "PavonisInteractive.TerraInvicta.Ship.DamageSource" },
                null,
                nameof(OutcomeDiagnostics.OnMissileApplyDamagePostfix),
                ref patched,
                ref skipped);

            TryPatch(
                harmony,
                "outcome missile lifecycle hook",
                "PavonisInteractive.TerraInvicta.SpaceCombat.MissileController",
                "Destruct",
                new[] { "System.Boolean" },
                null,
                nameof(OutcomeDiagnostics.OnMissileDestructPostfix),
                ref patched,
                ref skipped);

            TryPatch(
                harmony,
                "outcome ship damage hook",
                "PavonisInteractive.TerraInvicta.SpaceCombat.CombatShipController",
                "ApplyDamage",
                new[] { "PavonisInteractive.TerraInvicta.Ship.DamageSource" },
                null,
                nameof(OutcomeDiagnostics.OnShipApplyDamagePostfix),
                ref patched,
                ref skipped);

            TryPatch(
                harmony,
                "outcome ship destruction hook",
                "PavonisInteractive.TerraInvicta.SpaceCombat.CombatShipController",
                "TriggerShipDestruction",
                new[] { "TIGameState", "TIShipWeaponTemplate" },
                null,
                nameof(OutcomeDiagnostics.OnShipDestructionPostfix),
                ref patched,
                ref skipped);

            Log.Info($"Combat launch diagnostics patch bootstrap complete. patched={patched}, skipped={skipped}");
        }

        private static void TryPatch(
            Harmony harmony,
            string description,
            string targetTypeName,
            string targetMethodName,
            string[] parameterTypeNames,
            string prefixName,
            string postfixName,
            ref int patched,
            ref int skipped)
        {
            try
            {
                Type targetType = AccessTools.TypeByName(targetTypeName);
                if (targetType == null)
                {
                    Skip(description, $"target type not found: {targetTypeName}", ref skipped);
                    return;
                }

                Type[] parameterTypes = ResolveParameterTypes(parameterTypeNames);
                if (parameterTypes == null)
                {
                    Skip(description, "one or more parameter types were not found", ref skipped);
                    return;
                }

                MethodInfo target = AccessTools.Method(targetType, targetMethodName, parameterTypes);
                if (target == null)
                {
                    Skip(description, $"method not found: {targetTypeName}.{targetMethodName}({string.Join(", ", parameterTypeNames)})", ref skipped);
                    return;
                }

                MethodInfo prefix = string.IsNullOrEmpty(prefixName)
                    ? null
                    : FindPatchMethod(prefixName);
                if (!string.IsNullOrEmpty(prefixName) && prefix == null)
                {
                    Skip(description, $"prefix method not found: {prefixName}", ref skipped);
                    return;
                }

                MethodInfo postfix = FindPatchMethod(postfixName);
                if (postfix == null)
                {
                    Skip(description, $"postfix method not found: {postfixName}", ref skipped);
                    return;
                }

                harmony.Patch(
                    target,
                    prefix: prefix == null ? null : new HarmonyMethod(prefix),
                    postfix: new HarmonyMethod(postfix));
                patched++;
                Log.Info($"Patched {description}: {target.DeclaringType.FullName}.{target.Name}");
            }
            catch (Exception ex)
            {
                skipped++;
                Log.Warning($"Skipped {description}: {ex.GetType().Name}: {ex.Message}");
            }
        }

        private static Type[] ResolveParameterTypes(string[] typeNames)
        {
            Type[] result = new Type[typeNames.Length];
            for (int i = 0; i < typeNames.Length; i++)
            {
                result[i] = ResolveType(typeNames[i]);
                if (result[i] == null)
                {
                    Log.Warning($"Launch diagnostics parameter type not found: {typeNames[i]}");
                    return null;
                }
            }

            return result;
        }

        private static MethodInfo FindPatchMethod(string methodName)
        {
            return AccessTools.Method(typeof(CombatLaunchDiagnostics), methodName)
                ?? AccessTools.Method(typeof(OutcomeDiagnostics), methodName);
        }

        private static Type ResolveType(string typeName)
        {
            switch (typeName)
            {
                case "System.Boolean":
                    return typeof(bool);
                case "System.DateTime":
                    return typeof(DateTime);
                case "UnityEngine.Vector3":
                    return typeof(UnityEngine.Vector3);
                default:
                    return AccessTools.TypeByName(typeName) ?? AppDomain.CurrentDomain.GetAssemblies()
                        .Select(assembly => assembly.GetType(typeName, throwOnError: false))
                        .FirstOrDefault(type => type != null);
            }
        }

        private static void Skip(string description, string reason, ref int skipped)
        {
            skipped++;
            Log.Warning($"Skipped {description}: {reason}");
        }
    }
}
