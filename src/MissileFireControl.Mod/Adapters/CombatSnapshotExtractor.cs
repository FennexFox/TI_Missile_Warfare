using System.Collections.Generic;
using MissileFireControl.Core.Models;

namespace MissileFireControl.Mod.Adapters
{
    internal sealed class ExtractedCombatSnapshot
    {
        public ExtractedCombatSnapshot()
        {
            MissingFields = new List<string>();
        }

        public string Source { get; set; }
        public ShipSnapshot Launcher { get; set; }
        public ShipSnapshot Target { get; set; }
        public string TargetIdentitySource { get; set; }
        public MissileProfile Missile { get; set; }
        public MissileInventorySnapshot Inventory { get; set; }
        public Vector3d ExpectedTargetPositionKm { get; set; }
        public bool HasExpectedTargetPosition { get; set; }
        public Vector3d OriginPositionKm { get; set; }
        public bool HasOriginPosition { get; set; }
        public Vector3d OriginVelocityKps { get; set; }
        public bool HasOriginVelocity { get; set; }
        public List<string> MissingFields { get; private set; }
    }

    internal static class CombatSnapshotExtractor
    {
        public static ExtractedCombatSnapshot FromProjectileMissileFire(object projectile, object[] args)
        {
            object launcher = GetArg(args, 0);
            object missileTemplate = GetArg(args, 1);
            object originPosition = GetArg(args, 3);
            object expectedTargetPosition = GetArg(args, 4);
            object originVelocity = GetArg(args, 5);
            string targetIdentitySource;

            ExtractedCombatSnapshot snapshot = new ExtractedCombatSnapshot
            {
                Source = "TISpaceCombatProjectileState.Fire(missile)",
                Launcher = ExtractShip(launcher, "launcher"),
                Target = ExtractTarget(launcher, out targetIdentitySource),
                TargetIdentitySource = targetIdentitySource,
                Missile = ExtractMissileProfile(missileTemplate),
                HasExpectedTargetPosition = GameObjectReader.HasVector(expectedTargetPosition),
                ExpectedTargetPositionKm = GameObjectReader.ReadVector(expectedTargetPosition),
                HasOriginPosition = GameObjectReader.HasVector(originPosition),
                OriginPositionKm = GameObjectReader.ReadVector(originPosition),
                HasOriginVelocity = GameObjectReader.HasVector(originVelocity),
                OriginVelocityKps = GameObjectReader.ReadVector(originVelocity)
            };

            snapshot.Inventory = ExtractInventory(launcher, missileTemplate, snapshot.Launcher, snapshot.Missile);
            AddWeapon(snapshot.Launcher, missileTemplate, snapshot.Inventory);
            AddMissingFields(snapshot);
            return snapshot;
        }

        private static ShipSnapshot ExtractShip(object ship, string fallback)
        {
            ShipSnapshot snapshot = new ShipSnapshot
            {
                Id = GameObjectReader.StableId(ship, fallback),
                DisplayName = GameObjectReader.Label(ship, fallback),
                TeamId = GameObjectReader.TeamId(ship),
                HullClass = HullClass.Unknown,
                PositionKm = GameObjectReader.ReadVector(ship, "position", "Position", "centerOfMass", "CenterOfMass"),
                VelocityKps = GameObjectReader.ReadVector(ship, "velocityVector_kps", "velocity_kps", "VelocityKps", "velocity"),
                RemainingHullFraction = GameObjectReader.ReadDouble(ship, 1.0, "remainingHullFraction", "RemainingHullFraction"),
                IsDisabled = GameObjectReader.ReadBool(ship, false, "isDisabled", "IsDisabled", "disabled", "Disabled"),
                StrategicPriority = 1.0
            };

            return snapshot;
        }

        private static ShipSnapshot ExtractTarget(object launcher, out string source)
        {
            ShipSnapshot target = TryExtractTarget(
                launcher,
                "launcher",
                out source,
                "combatPrimaryTarget",
                "primaryTargetState",
                "primaryTarget",
                "target",
                "Target");
            if (target != null)
            {
                return target;
            }

            source = "none";
            return null;
        }

        private static ShipSnapshot TryExtractTarget(object owner, string ownerName, out string source, params string[] memberNames)
        {
            source = "none";
            object target = GameObjectReader.ReadFirstMember(owner, memberNames);
            target = NormalizeTarget(target);
            if (target == null)
            {
                return null;
            }

            source = ownerName;
            return ExtractShip(target, "target");
        }

        private static object NormalizeTarget(object target)
        {
            object current = target;
            for (int depth = 0; depth < 6 && current != null; depth++)
            {
                object next = GameObjectReader.ReadFirstMember(
                    current,
                    "combatTargetableState",
                    "GetCombatantState",
                    "GetTargetableState",
                    "ShipState",
                    "WeaponCarrierState");
                if (next == null || ReferenceEquals(next, current))
                {
                    return current;
                }

                current = next;
            }

            return current;
        }

        private static MissileProfile ExtractMissileProfile(object missileTemplate)
        {
            return new MissileProfile
            {
                Id = GameObjectReader.StableId(missileTemplate, "missile"),
                DisplayName = GameObjectReader.Label(missileTemplate, "missile"),
                NominalRangeKm = GameObjectReader.ReadDouble(missileTemplate, 800.0, "targetingRange_km", "range_km", "RangeKm"),
                EffectiveVelocityKps = GameObjectReader.ReadDouble(missileTemplate, 5.0, "deltaV_kps", "maxVelocity_kps", "effectiveVelocity_kps"),
                DamagePerLeaker = GameObjectReader.ReadDouble(missileTemplate, 1.0, "damage", "Damage", "warheadYield_MJ"),
                SafetyMargin = 2
            };
        }

        private static MissileInventorySnapshot ExtractInventory(
            object launcher,
            object missileTemplate,
            ShipSnapshot launcherSnapshot,
            MissileProfile missileProfile)
        {
            object weapon = GameObjectReader.ReadFirstMember(launcher, "weapon", "Weapon", "weaponData", "module", "Module");
            int readyShots = FirstKnownCount(weapon, launcher, missileTemplate, "readyShots", "ReadyShots", "loadedAmmo", "loadedMissiles", "readyMissiles");
            int remainingShots = FirstKnownCount(weapon, launcher, missileTemplate, "remainingShots", "RemainingShots", "ammo", "Ammo", "magazine", "missileCount", "remainingMissiles");

            return new MissileInventorySnapshot
            {
                LauncherShipId = launcherSnapshot == null ? "unknown-launcher" : launcherSnapshot.Id,
                WeaponId = GameObjectReader.StableId(weapon ?? missileTemplate, "weapon"),
                MissileProfileId = missileProfile == null ? "unknown-missile" : missileProfile.Id,
                ReadyShots = readyShots,
                RemainingShots = remainingShots
            };
        }

        private static void AddWeapon(ShipSnapshot launcher, object missileTemplate, MissileInventorySnapshot inventory)
        {
            if (launcher == null)
            {
                return;
            }

            launcher.Weapons.Add(new WeaponSnapshot
            {
                Id = inventory == null ? GameObjectReader.StableId(missileTemplate, "weapon") : inventory.WeaponId,
                DisplayName = GameObjectReader.Label(missileTemplate, "missile weapon"),
                Role = MapWeaponRole(missileTemplate),
                PointDefenseWeight = 0.0,
                ThreatWeight = 1.0,
                CanDefendOtherShips = false,
                SupportRangeKm = 0.0,
                ReadyShots = inventory == null ? -1 : inventory.ReadyShots,
                RemainingShots = inventory == null ? -1 : inventory.RemainingShots
            });
        }

        private static WeaponRole MapWeaponRole(object weaponTemplate)
        {
            bool isMissile = GameObjectReader.ReadBool(weaponTemplate, true, "isMissileWeapon", "IsMissileWeapon");
            return isMissile ? WeaponRole.Missile : WeaponRole.Unknown;
        }

        private static int FirstKnownCount(object first, object second, object third, params string[] memberNames)
        {
            int count = GameObjectReader.ReadCount(first, memberNames);
            if (count >= 0)
            {
                return count;
            }

            count = GameObjectReader.ReadCount(second, memberNames);
            if (count >= 0)
            {
                return count;
            }

            return GameObjectReader.ReadCount(third, memberNames);
        }

        private static object GetArg(object[] args, int index)
        {
            return args == null || index < 0 || index >= args.Length ? null : args[index];
        }

        private static void AddMissingFields(ExtractedCombatSnapshot snapshot)
        {
            if (!HasConcreteIdentity(snapshot.Launcher, "launcher"))
            {
                snapshot.MissingFields.Add("launcher");
            }

            if (!HasConcreteIdentity(snapshot.Target, "target"))
            {
                snapshot.MissingFields.Add("targetIdentity");
            }

            if (!snapshot.HasExpectedTargetPosition)
            {
                snapshot.MissingFields.Add("expectedTargetPosition");
            }

            if (snapshot.Inventory == null || snapshot.Inventory.ReadyShots < 0)
            {
                snapshot.MissingFields.Add("readyShots");
            }

            if (snapshot.Inventory == null || snapshot.Inventory.RemainingShots < 0)
            {
                snapshot.MissingFields.Add("remainingShots");
            }
        }

        private static bool HasConcreteIdentity(ShipSnapshot ship, string fallbackPrefix)
        {
            if (ship == null || string.IsNullOrWhiteSpace(ship.Id))
            {
                return false;
            }

            if (ship.Id.StartsWith("unknown-"))
            {
                return false;
            }

            return !ship.Id.StartsWith(fallbackPrefix + ":");
        }
    }
}
