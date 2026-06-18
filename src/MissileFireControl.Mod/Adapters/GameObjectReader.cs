using System;
using System.Collections;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using MissileFireControl.Core.Models;

namespace MissileFireControl.Mod.Adapters
{
    internal static class GameObjectReader
    {
        public static object ReadFirstMember(object instance, params string[] memberNames)
        {
            if (instance == null || memberNames == null)
            {
                return null;
            }

            foreach (string memberName in memberNames)
            {
                object value = ReadMember(instance, memberName);
                if (value != null)
                {
                    return value;
                }
            }

            return null;
        }

        public static object ReadMember(object instance, string memberName)
        {
            if (instance == null || string.IsNullOrEmpty(memberName))
            {
                return null;
            }

            return ReadMember(instance.GetType(), instance, memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        }

        public static string StableId(object instance, string fallbackPrefix)
        {
            if (instance == null)
            {
                return Missing(fallbackPrefix);
            }

            string id = FirstNonEmptyString(instance, "id", "ID", "guid", "Guid", "gameStateID", "GameStateID", "templateName", "dataName");
            if (!string.IsNullOrEmpty(id))
            {
                return Clean(id);
            }

            string prefix = string.IsNullOrWhiteSpace(fallbackPrefix) ? instance.GetType().Name : fallbackPrefix;
            return Clean(prefix + ":" + instance.GetType().Name + "#" + RuntimeHelpers.GetHashCode(instance).ToString(CultureInfo.InvariantCulture));
        }

        public static string Label(object instance, string fallback)
        {
            if (instance == null)
            {
                return Missing(fallback);
            }

            string label = FirstNonEmptyString(instance, "displayName", "DisplayName", "fullName", "FullName", "name", "Name", "dataName", "templateName", "moduleTemplateName");
            return string.IsNullOrEmpty(label) ? Clean(instance.GetType().Name) : Clean(label);
        }

        public static string TeamId(object instance)
        {
            object team = ReadFirstMember(instance, "team", "Team", "teamID", "teamId", "shootingTeam", "faction", "shootingFaction");
            if (team == null)
            {
                return "unknown";
            }

            string id = FirstNonEmptyString(team, "id", "ID", "guid", "Guid", "name", "Name", "displayName", "DisplayName");
            return string.IsNullOrEmpty(id) ? Describe(team) : Clean(id);
        }

        public static int ReadCount(object instance, params string[] memberNames)
        {
            object value = ReadFirstMember(instance, memberNames);
            if (value == null)
            {
                return -1;
            }

            if (value is ICollection collection)
            {
                return collection.Count;
            }

            int parsed;
            if (TryInt(value, out parsed))
            {
                return parsed;
            }

            object count = ReadMember(value, "Count");
            return TryInt(count, out parsed) ? parsed : -1;
        }

        public static double ReadDouble(object instance, double fallback, params string[] memberNames)
        {
            object value = ReadFirstMember(instance, memberNames);
            double parsed;
            return TryDouble(value, out parsed) ? parsed : fallback;
        }

        public static bool ReadBool(object instance, bool fallback, params string[] memberNames)
        {
            object value = ReadFirstMember(instance, memberNames);
            if (value is bool boolValue)
            {
                return boolValue;
            }

            if (value is IConvertible)
            {
                try
                {
                    return Convert.ToDouble(value, CultureInfo.InvariantCulture) != 0.0;
                }
                catch
                {
                    // Fall through to string parse.
                }
            }

            string text = Convert.ToString(value, CultureInfo.InvariantCulture);
            bool parsed;
            return bool.TryParse(text, out parsed) ? parsed : fallback;
        }

        public static Vector3d ReadVector(object instance, params string[] memberNames)
        {
            object value = memberNames == null || memberNames.Length == 0 ? instance : ReadFirstMember(instance, memberNames);
            Vector3d vector;
            return TryVector(value, out vector) ? vector : Vector3d.Zero;
        }

        public static bool HasVector(object instance, params string[] memberNames)
        {
            object value = memberNames == null || memberNames.Length == 0 ? instance : ReadFirstMember(instance, memberNames);
            Vector3d ignored;
            return TryVector(value, out ignored);
        }

        public static string Describe(object value)
        {
            if (value == null)
            {
                return "unknown";
            }

            if (value is string text)
            {
                return Clean(text);
            }

            Type type = value.GetType();
            if (type.IsPrimitive || value is decimal || value is DateTime || type.IsEnum)
            {
                return Clean(Convert.ToString(value, CultureInfo.InvariantCulture));
            }

            string label = Label(value, type.Name);
            string id = StableId(value, type.Name);
            return Clean(label + "#" + id);
        }

        public static string FormatVector(Vector3d vector)
        {
            return vector.X.ToString("0.###", CultureInfo.InvariantCulture) + ","
                + vector.Y.ToString("0.###", CultureInfo.InvariantCulture) + ","
                + vector.Z.ToString("0.###", CultureInfo.InvariantCulture);
        }

        public static string Clean(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return "unknown";
            }

            return value.Replace("\r", " ").Replace("\n", " ").Replace("\"", "'");
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

        private static string FirstNonEmptyString(object instance, params string[] memberNames)
        {
            foreach (string memberName in memberNames)
            {
                object value = ReadMember(instance, memberName);
                if (value == null)
                {
                    continue;
                }

                string text = Convert.ToString(value, CultureInfo.InvariantCulture);
                if (!string.IsNullOrWhiteSpace(text))
                {
                    return text;
                }
            }

            return null;
        }

        private static bool TryVector(object value, out Vector3d vector)
        {
            vector = Vector3d.Zero;
            if (value == null)
            {
                return false;
            }

            object x = ReadMember(value, "x") ?? ReadMember(value, "X");
            object y = ReadMember(value, "y") ?? ReadMember(value, "Y");
            object z = ReadMember(value, "z") ?? ReadMember(value, "Z");

            double parsedX;
            double parsedY;
            double parsedZ;
            if (!TryDouble(x, out parsedX) || !TryDouble(y, out parsedY) || !TryDouble(z, out parsedZ))
            {
                return false;
            }

            vector = new Vector3d(parsedX, parsedY, parsedZ);
            return true;
        }

        private static bool TryDouble(object value, out double parsed)
        {
            if (value is IConvertible)
            {
                try
                {
                    parsed = Convert.ToDouble(value, CultureInfo.InvariantCulture);
                    return true;
                }
                catch
                {
                    parsed = 0;
                    return false;
                }
            }

            parsed = 0;
            return false;
        }

        private static bool TryInt(object value, out int parsed)
        {
            if (value is IConvertible)
            {
                try
                {
                    parsed = Convert.ToInt32(value, CultureInfo.InvariantCulture);
                    return true;
                }
                catch
                {
                    parsed = 0;
                    return false;
                }
            }

            parsed = 0;
            return false;
        }

        private static string Missing(string label)
        {
            return string.IsNullOrWhiteSpace(label) ? "unknown" : "unknown-" + label;
        }
    }
}
