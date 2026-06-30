using System;
using System.Globalization;
using System.Text;
using System.Threading;
using MissileFireControl.Core.Models;
using MissileFireControl.Mod.Adapters;

namespace MissileFireControl.Mod.Diagnostics
{
    internal static class OutcomeDiagnostics
    {
        private static int _sequence;

        public static void OnMissileApplyDamagePostfix(object __instance, object[] __args, float __result)
        {
            if (!ShouldLog())
            {
                return;
            }

            object source = GetArg(__args, 0);
            WriteOutcomeLine("missileDamage", "projectileDamage", "projectileDamageSource", builder =>
            {
                AppendPair(builder, "sourceHook", "MissileController.ApplyDamage");
                AppendProjectileFields(builder, "projectile", __instance);
                AppendTargetFields(builder, "target", ReadMember(__instance, "target"));
                AppendDamageSourceFields(builder, source);
                AppendPair(builder, "appliedDamage", FormatNumber(__result));
                AppendPair(builder, "identityBridge", "projectileController+damageSource");
                AppendPair(builder, "battle", BattleContext());
            });
        }

        public static void OnMissileDestructPostfix(object __instance, object[] __args)
        {
            if (!ShouldLog())
            {
                return;
            }

            WriteOutcomeLine("missileLifecycle", "projectileLifecycle", "projectileStateOnly", builder =>
            {
                AppendPair(builder, "sourceHook", "MissileController.Destruct");
                AppendProjectileFields(builder, "projectile", __instance);
                AppendTargetFields(builder, "target", ReadMember(__instance, "target"));
                AppendPair(builder, "hasHit", Describe(ReadMember(__instance, "hasHit")));
                AppendPair(builder, "beenDestroyed", Describe(ReadMember(__instance, "beenDestroyed")));
                AppendPair(builder, "alreadyRemovedFromLiveProjectiles", Describe(GetArg(__args, 0)));
                AppendPair(builder, "identityBridge", "projectileControllerState");
                AppendPair(builder, "battle", BattleContext());
            });
        }

        public static void OnShipApplyDamagePostfix(object __instance, object[] __args, float __result)
        {
            if (!ShouldLog())
            {
                return;
            }

            object source = GetArg(__args, 0);
            WriteOutcomeLine("shipDamage", "damageApplication", AttributionLevelForDamageSource(source), builder =>
            {
                AppendPair(builder, "sourceHook", "CombatShipController.ApplyDamage");
                object shipState = ReadMember(__instance, "ShipState");
                AppendTargetFields(builder, "target", shipState ?? __instance);
                AppendDamageSourceFields(builder, source);
                AppendPair(builder, "appliedDamage", FormatNumber(__result));
                AppendPair(builder, "shipDamageTargetDestructionTriggered", Describe(ReadMember(__instance, "destructionTriggered")));
                AppendPair(builder, "identityBridge", IdentityBridgeForDamageSource(source));
                AppendPair(builder, "battle", BattleContext());
            });
        }

        public static void OnShipDestructionPostfix(object __instance, object[] __args)
        {
            if (!ShouldLog())
            {
                return;
            }

            WriteOutcomeLine("shipDestroyed", "shipDestruction", "destroyedStateWithKillerWeapon", builder =>
            {
                AppendPair(builder, "sourceHook", "CombatShipController.TriggerShipDestruction");
                object shipState = ReadMember(__instance, "ShipState");
                AppendTargetFields(builder, "target", shipState ?? __instance);
                object gameState = GetArg(__args, 0);
                object killerWeapon = GetArg(__args, 1);
                AppendPair(builder, "gameState", Describe(gameState));
                AppendPair(builder, "killerWeapon", Describe(killerWeapon));
                AppendPair(builder, "killerWeaponId", StableIdOrUnknown(killerWeapon, "killerWeapon"));
                AppendPair(builder, "killerWeaponIsMissile", Describe(ReadMember(killerWeapon, "isMissileWeapon")));
                AppendPair(builder, "killerWeaponClass", Describe(ReadMember(killerWeapon, "weaponClass")));
                AppendPair(builder, "identityBridge", "killerWeaponNoProjectileId");
                AppendPair(builder, "battle", BattleContext());
            });
        }

        private static bool ShouldLog()
        {
            return Main.IsEnabled()
                && Main.Settings != null
                && Main.Settings.EnableDiagnostics
                && Main.Settings.EnableOutcomeDiagnostics;
        }

        private static void WriteOutcomeLine(string recordType, string eventLevel, string attributionLevel, Action<StringBuilder> appendDetails)
        {
            try
            {
                StringBuilder builder = new StringBuilder(512);
                int sequence = Interlocked.Increment(ref _sequence);
                AppendPair(builder, "seq", sequence.ToString(CultureInfo.InvariantCulture));
                AppendPair(builder, "recordType", recordType);
                AppendPair(builder, "eventLevel", eventLevel);
                AppendPair(builder, "attributionLevel", attributionLevel);
                AppendPair(builder, "utc", DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture));
                appendDetails(builder);
                Log.Info("[OutcomeLog] " + builder);
            }
            catch (Exception ex)
            {
                Log.Warning($"Outcome diagnostics failed in {recordType}: {ex.GetType().Name}: {ex.Message}");
            }
        }

        private static void AppendProjectileFields(StringBuilder builder, string prefix, object projectile)
        {
            object projectileState = ReadMember(projectile, "projectileState") ?? ReadMember(projectile, "ref_projectile");
            AppendPair(builder, prefix, Describe(projectile));
            AppendPair(builder, prefix + "Id", StableIdOrUnknown(projectileState ?? projectile, prefix));
            AppendPair(builder, prefix + "State", Describe(projectileState));
            AppendPair(builder, prefix + "Origin", Describe(ReadMember(projectileState, "origin")));
            AppendPair(builder, prefix + "OriginId", StableIdOrUnknown(ReadMember(projectileState, "origin"), prefix + "Origin"));
            AppendPair(builder, prefix + "Weapon", Describe(ReadMember(projectileState, "originWeapon")));
            AppendPair(builder, prefix + "ShootingFaction", Describe(ReadMember(projectileState, "shootingFaction")));
            AppendPair(builder, prefix + "ShootingTeam", Describe(ReadMember(projectileState, "shootingTeam")));
            AppendPair(builder, prefix + "Position", FormatVector(ReadMember(projectile, "position")));
            AppendPair(builder, prefix + "VelocityKps", FormatVector(ReadMember(projectile, "velocityVector_kps")));
        }

        private static void AppendTargetFields(StringBuilder builder, string prefix, object target)
        {
            AppendPair(builder, prefix, Describe(target));
            AppendPair(builder, prefix + "Id", StableIdOrUnknown(target, prefix));
            AppendPair(builder, prefix + "Team", GameObjectReader.TeamId(target));
            AppendPair(builder, prefix + "Type", Describe(ReadMember(target, "damageableType")));
            AppendPair(builder, prefix + "Destroyed", Describe(ReadMember(target, "isDestroyed") ?? ReadMember(target, "destructionTriggered") ?? ReadMember(target, "destroyed")));
        }

        private static void AppendDamageSourceFields(StringBuilder builder, object source)
        {
            object damage = ReadMember(source, "damage");
            object attacker = ReadMember(source, "attacker");
            object weapon = ReadMember(damage, "weapon");

            AppendPair(builder, "damageSource", Describe(source));
            AppendPair(builder, "damageSourceType", source == null ? "unknown" : source.GetType().FullName);
            AppendPair(builder, "damageAttacker", Describe(attacker));
            AppendPair(builder, "damageAttackerId", StableIdOrUnknown(attacker, "damageAttacker"));
            AppendPair(builder, "damageAttackerTeam", GameObjectReader.TeamId(attacker));
            AppendPair(builder, "damageWeapon", Describe(weapon));
            AppendPair(builder, "damageWeaponId", StableIdOrUnknown(weapon, "damageWeapon"));
            AppendPair(builder, "damageWeaponIsMissile", Describe(ReadMember(weapon, "isMissileWeapon")));
            AppendPair(builder, "damageWeaponClass", Describe(ReadMember(weapon, "weaponClass")));
            AppendPair(builder, "damageType", Describe(ReadMember(damage, "type")));
            AppendPair(builder, "damageAmount", Describe(ReadMember(damage, "amount")));
            AppendPair(builder, "damageChippingAmount", Describe(ReadMember(damage, "chippingAmount")));
            AppendPair(builder, "damageShreddingAmount", Describe(ReadMember(damage, "shreddingAmount")));
            AppendPair(builder, "damageApplyingFaction", Describe(ReadMember(damage, "applyingFaction")));
            AppendPair(builder, "hitPosition", FormatVector(ReadMember(source, "hitPosition")));
            AppendPair(builder, "warheadMassKg", Describe(ReadMember(source, "warheadMass_kg")));
        }

        private static string AttributionLevelForDamageSource(object source)
        {
            string sourceType = source == null ? string.Empty : source.GetType().FullName;
            if (sourceType.IndexOf("MissileController", StringComparison.Ordinal) >= 0)
            {
                return "missileDamageSource";
            }

            if (sourceType.IndexOf("ProjectileDamage", StringComparison.Ordinal) >= 0)
            {
                return "projectileDamageSource";
            }

            return "damageSource";
        }

        private static string IdentityBridgeForDamageSource(object source)
        {
            string sourceType = source == null ? string.Empty : source.GetType().FullName;
            if (sourceType.IndexOf("MissileController", StringComparison.Ordinal) >= 0)
            {
                return "damageSourceAttackerWeaponNoProjectileId";
            }

            return "damageSourceAttackerWeapon";
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
            return builder.ToString().Trim();
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

            return ReadMember(type, null, memberName, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);
        }

        private static object ReadMember(object instance, string memberName)
        {
            return GameObjectReader.ReadMember(instance, memberName);
        }

        private static object ReadMember(Type type, object instance, string memberName, System.Reflection.BindingFlags flags)
        {
            try
            {
                System.Reflection.PropertyInfo property = type.GetProperty(memberName, flags);
                if (property != null && property.GetIndexParameters().Length == 0)
                {
                    return property.GetValue(instance, null);
                }

                System.Reflection.FieldInfo field = type.GetField(memberName, flags);
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
                return "unknown";
            }

            return GameObjectReader.Describe(value);
        }

        private static string StableIdOrUnknown(object value, string fallbackPrefix)
        {
            string id = GameObjectReader.StableId(value, fallbackPrefix);
            return HasConcreteToken(id) ? id : "unknown";
        }

        private static string FormatVector(object value)
        {
            if (!GameObjectReader.HasVector(value))
            {
                return Describe(value);
            }

            Vector3d vector = GameObjectReader.ReadVector(value);
            return GameObjectReader.FormatVector(vector);
        }

        private static string FormatNumber(float value)
        {
            return value.ToString("0.###", CultureInfo.InvariantCulture);
        }

        private static string DescribeCount(object value)
        {
            if (value == null)
            {
                return "null";
            }

            System.Collections.ICollection collection = value as System.Collections.ICollection;
            if (collection != null)
            {
                return collection.Count.ToString(CultureInfo.InvariantCulture);
            }

            object count = ReadMember(value, "Count");
            return count == null ? Describe(value) : Describe(count);
        }

        private static Type FindType(string typeName)
        {
            foreach (System.Reflection.Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type type = assembly.GetType(typeName, throwOnError: false);
                if (type != null)
                {
                    return type;
                }
            }

            return null;
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

        private static bool HasConcreteToken(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return false;
            }

            return !value.StartsWith("unknown", StringComparison.Ordinal);
        }
    }
}
