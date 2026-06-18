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

            _applied = true;
            if (harmony == null)
            {
                Log.Warning("Harmony patch bootstrap skipped: Harmony instance was null.");
                return;
            }

            int patched = 0;
            int skipped = 0;

            TryPatchPostfix(
                harmony,
                "primary ship fire hook",
                "PavonisInteractive.TerraInvicta.TISpaceShipState",
                "FireWeapon",
                new[] { "ModuleDataEntry", "PavonisInteractive.TerraInvicta.TISpaceCombatProjectileState" },
                nameof(CombatLaunchDiagnostics.OnShipFireWeaponPostfix),
                ref patched,
                ref skipped);

            TryPatchPostfix(
                harmony,
                "secondary missile try-fire hook",
                "PavonisInteractive.TerraInvicta.Ship.MissileWeapon",
                "TryFire",
                new[] { "System.DateTime" },
                nameof(CombatLaunchDiagnostics.OnMissileTryFirePostfix),
                ref patched,
                ref skipped);

            TryPatchPostfix(
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
                nameof(CombatLaunchDiagnostics.OnProjectileMissileFirePostfix),
                ref patched,
                ref skipped);

            Log.Info($"Combat launch diagnostics patch bootstrap complete. patched={patched}, skipped={skipped}");
        }

        private static void TryPatchPostfix(
            Harmony harmony,
            string description,
            string targetTypeName,
            string targetMethodName,
            string[] parameterTypeNames,
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

                MethodInfo postfix = AccessTools.Method(typeof(CombatLaunchDiagnostics), postfixName);
                if (postfix == null)
                {
                    Skip(description, $"postfix method not found: {postfixName}", ref skipped);
                    return;
                }

                harmony.Patch(target, postfix: new HarmonyMethod(postfix));
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

        private static Type ResolveType(string typeName)
        {
            switch (typeName)
            {
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
