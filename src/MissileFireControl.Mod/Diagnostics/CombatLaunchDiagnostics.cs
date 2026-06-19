using System;
using System.Collections;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;

namespace MissileFireControl.Mod.Diagnostics
{
    internal static class CombatLaunchDiagnostics
    {
        private static int _sequence;

        public static void OnShipFireWeaponPostfix(object __instance, object[] __args)
        {
            if (!ShouldLog())
            {
                return;
            }

            object module = GetArg(__args, 0);
            object targetedProjectile = GetArg(__args, 1);

            WriteLaunchLine("TISpaceShipState.FireWeapon", builder =>
            {
                AppendPair(builder, "launcher", Describe(__instance));
                AppendPair(builder, "weapon", DescribeWeaponModule(module));
                AppendPair(builder, "primaryTarget", Describe(ReadMember(__instance, "combatPrimaryTarget")));
                AppendPair(builder, "targetedProjectile", DescribeProjectile(targetedProjectile));
                AppendPair(builder, "templateDefaultFireMode", DescribeDefaultFireModeFromModule(module));
                AppendPair(builder, "battle", BattleContext());
            });
        }

        public static void OnMissileTryFirePostfix(object __instance, object[] __args, bool __result)
        {
            if (!__result || !ShouldLog())
            {
                return;
            }

            WriteLaunchLine("MissileWeapon.TryFire", builder =>
            {
                object weaponData = ReadMember(__instance, "weaponData");
                object weaponTemplate = ReadMember(__instance, "weaponTemplate");
                object combatant = ReadMember(__instance, "combatant");
                object launcher = ReadMember(combatant, "WeaponCarrierState");

                AppendPair(builder, "weapon", DescribeWeapon(__instance));
                AppendPair(builder, "launcher", Describe(launcher));
                AppendPair(builder, "target", Describe(ReadMember(__instance, "target")));
                AppendPair(builder, "targetedPosition", DescribeVector(ReadMember(__instance, "targetedPosition")));
                AppendPair(builder, "fireMode", Describe(ReadMember(__instance, "currentFireMode")));
                AppendPair(builder, "currentTime", Describe(GetArg(__args, 0)));
                AppendLiveWeaponAmmoEvidence(builder, __instance, launcher, weaponData, weaponTemplate, GetArg(__args, 0));
                AppendPair(builder, "battle", BattleContext());
            });
        }

        public static void OnProjectileMissileFirePostfix(object __instance, object[] __args)
        {
            if (!ShouldLog())
            {
                return;
            }

            WriteLaunchLine("TISpaceCombatProjectileState.Fire(missile)", builder =>
            {
                AppendPair(builder, "projectile", DescribeProjectile(__instance));
                AppendPair(builder, "launcher", Describe(GetArg(__args, 0)));
                AppendPair(builder, "missile", DescribeWeaponTemplate(GetArg(__args, 1)));
                AppendPair(builder, "launchTime", Describe(GetArg(__args, 2)));
                AppendPair(builder, "originPosition", DescribeVector(GetArg(__args, 3)));
                AppendPair(builder, "expectedTargetPosition", DescribeVector(GetArg(__args, 4)));
                AppendPair(builder, "originVelocityKps", DescribeVector(GetArg(__args, 5)));
                AppendPair(builder, "battle", BattleContext());
            });
            SnapshotDiagnostics.LogProjectileFireSnapshot(__instance, __args);
        }

        private static bool ShouldLog()
        {
            return Main.IsEnabled() && Main.Settings != null && Main.Settings.EnableDiagnostics;
        }

        private static void WriteLaunchLine(string hook, Action<StringBuilder> appendDetails)
        {
            try
            {
                StringBuilder builder = new StringBuilder(512);
                int sequence = Interlocked.Increment(ref _sequence);
                AppendPair(builder, "seq", sequence.ToString(CultureInfo.InvariantCulture));
                AppendPair(builder, "hook", hook);
                AppendPair(builder, "utc", DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture));
                appendDetails(builder);
                Log.Info("[LaunchLog] " + builder);
            }
            catch (Exception ex)
            {
                Log.Warning($"Launch diagnostics failed in {hook}: {ex.GetType().Name}: {ex.Message}");
            }
        }

        private static string BattleContext()
        {
            object spaceCombat = ReadStaticMember("PavonisInteractive.TerraInvicta.GameControl", "spaceCombat");
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

        private static string DescribeWeapon(object weapon)
        {
            if (weapon == null)
            {
                return "null";
            }

            StringBuilder builder = new StringBuilder();
            AppendPair(builder, "runtime", Describe(weapon));
            AppendPair(builder, "module", DescribeWeaponModule(ReadMember(weapon, "weaponData")));
            AppendPair(builder, "template", DescribeWeaponTemplate(ReadMember(weapon, "weaponTemplate")));
            AppendPair(builder, "missileTemplate", DescribeWeaponTemplate(ReadMember(weapon, "missileTemplate")));
            return builder.ToString().Trim();
        }

        private static string DescribeWeaponModule(object module)
        {
            if (module == null)
            {
                return "null";
            }

            StringBuilder builder = new StringBuilder();
            AppendPair(builder, "module", Describe(module));
            AppendPair(builder, "slot", Describe(ReadMember(module, "slotIndex")));
            AppendPair(builder, "moduleTemplateName", Describe(ReadMember(module, "moduleTemplateName")));
            object moduleTemplate = ReadMember(module, "moduleTemplate");
            AppendPair(builder, "moduleTemplate", Describe(moduleTemplate));
            AppendPair(builder, "weaponTemplate", DescribeWeaponTemplate(ReadMember(moduleTemplate, "ref_weapon")));
            return builder.ToString().Trim();
        }

        private static string DescribeWeaponTemplate(object weaponTemplate)
        {
            if (weaponTemplate == null)
            {
                return "null";
            }

            StringBuilder builder = new StringBuilder();
            AppendPair(builder, "template", Describe(weaponTemplate));
            AppendPair(builder, "class", Describe(ReadMember(weaponTemplate, "weaponClass")));
            AppendPair(builder, "isMissile", Describe(ReadMember(weaponTemplate, "isMissileWeapon")));
            AppendPair(builder, "rangeKm", Describe(ReadMember(weaponTemplate, "targetingRange_km")));
            AppendPair(builder, "cooldownS", Describe(ReadMember(weaponTemplate, "cooldown_s")));
            AppendPair(builder, "deltaVKps", Describe(ReadMember(weaponTemplate, "deltaV_kps")));
            AppendPair(builder, "ammoKg", Describe(ReadMember(weaponTemplate, "ammoMass_kg")));
            return builder.ToString().Trim();
        }

        private static string DescribeProjectile(object projectile)
        {
            if (projectile == null)
            {
                return "null";
            }

            StringBuilder builder = new StringBuilder();
            AppendPair(builder, "state", Describe(projectile));
            AppendPair(builder, "origin", Describe(ReadMember(projectile, "origin")));
            AppendPair(builder, "originWeapon", DescribeWeaponTemplate(ReadMember(projectile, "originWeapon")));
            AppendPair(builder, "launchTime", Describe(ReadMember(projectile, "launchTime")));
            AppendPair(builder, "position", DescribeVector(ReadMember(projectile, "position")));
            AppendPair(builder, "velocityKps", DescribeVector(ReadMember(projectile, "velocityVector_kps")));
            AppendPair(builder, "shootingFaction", Describe(ReadMember(projectile, "shootingFaction")));
            AppendPair(builder, "shootingTeam", Describe(ReadMember(projectile, "shootingTeam")));
            return builder.ToString().Trim();
        }

        private static string DescribeDefaultFireModeFromModule(object module)
        {
            object moduleTemplate = ReadMember(module, "moduleTemplate");
            object weaponTemplate = ReadMember(moduleTemplate, "ref_weapon");
            object defaultFireMode = ReadMember(weaponTemplate, "DefaultFireMode");
            return Describe(defaultFireMode);
        }

        private static void AppendLiveWeaponAmmoEvidence(
            StringBuilder builder,
            object weapon,
            object launcher,
            object weaponData,
            object weaponTemplate,
            object currentTime)
        {
            object postFireRemaining;
            if (TryReadAmmoByModule(launcher, weaponData, out postFireRemaining))
            {
                AppendPair(builder, "ammoEvidenceSource", "shipAmmoByWeaponData");
                AppendPair(builder, "postFireRemaining", Describe(postFireRemaining));
            }
            else
            {
                AppendPair(builder, "ammoEvidenceSource", "none");
                AppendPair(builder, "postFireRemaining", "unknown");
            }

            AppendPair(builder, "postFireWeaponHasAmmo", Describe(InvokeMember(launcher, "WeaponHasAmmo", weaponData)));
            AppendPair(builder, "postFireWeaponCanFire", Describe(InvokeMember(launcher, "WeaponCanFire", weaponData)));
            AppendPair(builder, "postFireOnCooldown", Describe(InvokeMember(weapon, "OnCooldown", currentTime)));
            AppendPair(builder, "cooldownDuration", Describe(ReadInheritedInstanceMember(weapon, "currentCooldownDuration_s")));
            AppendPair(builder, "lastFiredAt", Describe(ReadMember(weapon, "lastFiredAt")));
            AppendPair(builder, "salvoShotsFired", Describe(ReadMember(weapon, "shotsFiredThisSalvo")));
            AppendPair(builder, "salvoShots", Describe(ReadMember(weaponTemplate, "salvo_shots")));
            AppendPair(builder, "intraSalvoCooldownS", Describe(ReadMember(weaponTemplate, "intraSalvoCooldown_s")));
            AppendCapacityEvidence(builder, launcher, weaponTemplate);
        }

        private static void AppendCapacityEvidence(StringBuilder builder, object launcher, object weaponTemplate)
        {
            object projectileWeapon = ReadMember(weaponTemplate, "ref_projectileWeapon");
            object shipTemplate = ReadMember(launcher, "template");
            AppendPair(builder, "templateMagazine", Describe(ReadMember(projectileWeapon, "magazine")));
            AppendPair(builder, "magazineCapacityCurrent", Describe(InvokeMember(projectileWeapon, "FullAmmoCount_Current", launcher)));
            AppendPair(builder, "magazineCapacityMax", Describe(InvokeMember(projectileWeapon, "FullAmmoCount_Max", shipTemplate)));
        }

        private static string DescribeVector(object value)
        {
            if (value == null)
            {
                return "null";
            }

            object x = ReadMember(value, "x");
            object y = ReadMember(value, "y");
            object z = ReadMember(value, "z");
            if (x == null || y == null || z == null)
            {
                return Describe(value);
            }

            return FormatNumber(x) + "," + FormatNumber(y) + "," + FormatNumber(z);
        }

        private static object GetArg(object[] args, int index)
        {
            if (args == null || index < 0 || index >= args.Length)
            {
                return null;
            }

            return args[index];
        }

        private static object ReadStaticMember(string typeName, string memberName)
        {
            Type type = FindType(typeName);
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

        private static object ReadInheritedInstanceMember(object instance, string memberName)
        {
            if (instance == null || string.IsNullOrEmpty(memberName))
            {
                return null;
            }

            Type current = instance.GetType();
            while (current != null)
            {
                object value;
                if (TryReadDeclaredMember(current, instance, memberName, out value))
                {
                    return value;
                }

                current = current.BaseType;
            }

            return null;
        }

        private static bool TryReadDeclaredMember(Type type, object instance, string memberName, out object value)
        {
            value = null;
            const BindingFlags flags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly;

            try
            {
                PropertyInfo property = type.GetProperty(memberName, flags);
                if (property != null && property.GetIndexParameters().Length == 0)
                {
                    value = property.GetValue(instance, null);
                    return true;
                }

                FieldInfo field = type.GetField(memberName, flags);
                if (field != null)
                {
                    value = field.GetValue(instance);
                    return true;
                }
            }
            catch
            {
                value = null;
                return false;
            }

            return false;
        }

        private static object InvokeMember(object instance, string methodName, params object[] args)
        {
            if (instance == null || string.IsNullOrEmpty(methodName))
            {
                return null;
            }

            try
            {
                MethodInfo method = FindMethod(instance.GetType(), methodName, args);
                return method == null ? null : method.Invoke(instance, args);
            }
            catch
            {
                return null;
            }
        }

        private static MethodInfo FindMethod(Type type, string methodName, object[] args)
        {
            BindingFlags flags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;
            foreach (MethodInfo method in type.GetMethods(flags).Where(candidate => candidate.Name == methodName))
            {
                ParameterInfo[] parameters = method.GetParameters();
                if (parameters.Length != (args == null ? 0 : args.Length))
                {
                    continue;
                }

                bool match = true;
                for (int i = 0; i < parameters.Length; i++)
                {
                    object arg = args[i];
                    Type parameterType = parameters[i].ParameterType;
                    if (arg == null)
                    {
                        if (parameterType.IsValueType)
                        {
                            match = false;
                            break;
                        }

                        continue;
                    }

                    if (!parameterType.IsInstanceOfType(arg))
                    {
                        match = false;
                        break;
                    }
                }

                if (match)
                {
                    return method;
                }
            }

            return null;
        }

        private static bool TryReadAmmoByModule(object launcher, object weaponData, out object value)
        {
            value = null;
            object ammo = ReadMember(launcher, "ammo");
            if (ammo == null || weaponData == null)
            {
                return false;
            }

            try
            {
                if (ammo is IDictionary dictionary && dictionary.Contains(weaponData))
                {
                    value = dictionary[weaponData];
                    return true;
                }
            }
            catch
            {
                value = null;
            }

            return false;
        }

        private static string Describe(object value)
        {
            if (value == null)
            {
                return "null";
            }

            if (value is string text)
            {
                return Clean(text);
            }

            Type type = value.GetType();
            if (type.IsPrimitive || value is decimal || value is DateTime || value is TimeSpan || type.IsEnum)
            {
                return Clean(Convert.ToString(value, CultureInfo.InvariantCulture));
            }

            string name = FirstNonEmptyMember(value, "displayName", "DisplayName", "fullName", "FullName", "name", "Name", "dataName", "templateName", "moduleTemplateName");
            string id = FirstNonEmptyMember(value, "id", "ID", "guid", "Guid", "gameStateID", "GameStateID");
            string typeName = type.Name;

            if (!string.IsNullOrEmpty(name) && !string.IsNullOrEmpty(id))
            {
                return Clean($"{typeName}:{name}#{id}");
            }

            if (!string.IsNullOrEmpty(name))
            {
                return Clean($"{typeName}:{name}");
            }

            if (!string.IsNullOrEmpty(id))
            {
                return Clean($"{typeName}#{id}");
            }

            return Clean(typeName);
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

        private static string FirstNonEmptyMember(object value, params string[] memberNames)
        {
            foreach (string memberName in memberNames)
            {
                object memberValue = ReadMember(value, memberName);
                if (memberValue == null)
                {
                    continue;
                }

                string text = Convert.ToString(memberValue, CultureInfo.InvariantCulture);
                if (!string.IsNullOrWhiteSpace(text))
                {
                    return text;
                }
            }

            return null;
        }

        private static Type FindType(string typeName)
        {
            return AppDomain.CurrentDomain.GetAssemblies()
                .Select(assembly => assembly.GetType(typeName, throwOnError: false))
                .FirstOrDefault(type => type != null);
        }

        private static void AppendPair(StringBuilder builder, string key, string value)
        {
            if (builder.Length > 0)
            {
                builder.Append(' ');
            }

            builder.Append(key);
            builder.Append('=');
            builder.Append('"');
            builder.Append(Clean(value));
            builder.Append('"');
        }

        private static string FormatNumber(object value)
        {
            try
            {
                return Convert.ToDouble(value, CultureInfo.InvariantCulture).ToString("0.###", CultureInfo.InvariantCulture);
            }
            catch
            {
                return Clean(Convert.ToString(value, CultureInfo.InvariantCulture));
            }
        }

        private static string Clean(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return "unknown";
            }

            return value.Replace("\r", " ").Replace("\n", " ").Replace("\"", "'");
        }
    }
}
