using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
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
        public object LauncherRuntimeObject { get; set; }
        public ShipSnapshot Launcher { get; set; }
        public object TargetRuntimeObject { get; set; }
        public ShipSnapshot Target { get; set; }
        public string TargetIdentitySource { get; set; }
        public MissileProfile Missile { get; set; }
        public MissileInventorySnapshot Inventory { get; set; }
        public Vector3d ExpectedTargetPositionKm { get; set; }
        public bool HasExpectedTargetPosition { get; set; }
        public bool HasTargetVelocity { get; set; }
        public Vector3d TargetVelocityKps { get; set; }
        public string TargetVelocityEvidenceSource { get; set; }
        public string TargetVelocityMissingReason { get; set; }
        public Vector3d RelativeVelocityKps { get; set; }
        public double RelativeSpeedKps { get; set; }
        public bool HasRelativeVelocity { get; set; }
        public string RelativeVelocityEvidenceSource { get; set; }
        public string RelativeVelocityMissingReason { get; set; }
        public double PdWeight { get; set; }
        public string PdWeightEvidenceSource { get; set; }
        public bool PdWeightDefaulted { get; set; }
        public string PdWeightDefaultReason { get; set; }
        public string PdWeightMissingReason { get; set; }
        public string PdEvidenceQuality { get; set; }
        public string PdCapabilityEvidenceSource { get; set; }
        public int PdCapabilityWeaponCount { get; set; } = -1;
        public double PdCapabilityRangeKm { get; set; }
        public double PdCapabilityCooldownSeconds { get; set; }
        public string PdCapabilityObservedFields { get; set; }
        public string PdCapabilityMissingReason { get; set; }
        public string PdCapabilityLimitations { get; set; }
        public Vector3d OriginPositionKm { get; set; }
        public bool HasOriginPosition { get; set; }
        public Vector3d OriginVelocityKps { get; set; }
        public bool HasOriginVelocity { get; set; }
        public List<string> MissingFields { get; private set; }
    }

    internal sealed class ReadinessEvidenceSnapshot
    {
        public int AmmoGateBudgetShots { get; set; } = -1;
        public string AmmoGateBudgetEvidenceSource { get; set; }
        public string AmmoGateBudgetMissingReason { get; set; }
        public string AmmoEvidenceSource { get; set; }
        public string LiveWeaponState { get; set; }
        public int AmmoGateWeaponCount { get; set; } = -1;
        public int UnknownAmmoGateWeaponCount { get; set; } = 1;
        public bool HasTargetVelocity { get; set; }
        public Vector3d TargetVelocityKps { get; set; }
        public string TargetVelocityEvidenceSource { get; set; }
        public string TargetVelocityMissingReason { get; set; }
        public object TargetRuntimeObject { get; set; }
        public string TargetIdentityEvidenceSource { get; set; }
    }

    internal static class CombatSnapshotExtractor
    {
        public static ShipSnapshot ExtractTargetShipForDiagnostics(object targetObject, string fallback)
        {
            object normalized = NormalizeTarget(targetObject);
            if (normalized == null)
            {
                return null;
            }

            ExtractedCombatSnapshot snapshot = new ExtractedCombatSnapshot
            {
                TargetRuntimeObject = normalized,
                Target = ExtractShip(normalized, fallback)
            };
            AddTargetVelocityEvidence(snapshot);
            AddPdWeightEvidence(snapshot, normalized);
            return snapshot.Target;
        }

        public static ExtractedCombatSnapshot FromProjectileMissileFire(
            object projectile,
            object[] args,
            ReadinessEvidenceSnapshot readinessEvidence)
        {
            object launcher = GetArg(args, 0);
            object missileTemplate = GetArg(args, 1);
            object originPosition = GetArg(args, 3);
            object expectedTargetPosition = GetArg(args, 4);
            object originVelocity = GetArg(args, 5);
            string targetIdentitySource;
            object targetObject = ExtractTargetObject(launcher, out targetIdentitySource);
            if (targetObject == null)
            {
                targetObject = ExtractReadinessTargetObject(readinessEvidence, out targetIdentitySource);
            }

            ExtractedCombatSnapshot snapshot = new ExtractedCombatSnapshot
            {
                Source = "TISpaceCombatProjectileState.Fire(missile)",
                LauncherRuntimeObject = launcher,
                Launcher = ExtractShip(launcher, "launcher"),
                TargetRuntimeObject = targetObject,
                Target = targetObject == null ? null : ExtractShip(targetObject, "target"),
                TargetIdentitySource = targetIdentitySource,
                Missile = ExtractMissileProfile(missileTemplate),
                HasExpectedTargetPosition = GameObjectReader.HasVector(expectedTargetPosition),
                ExpectedTargetPositionKm = GameObjectReader.ReadVector(expectedTargetPosition),
                HasOriginPosition = GameObjectReader.HasVector(originPosition),
                OriginPositionKm = GameObjectReader.ReadVector(originPosition),
                HasOriginVelocity = GameObjectReader.HasVector(originVelocity),
                OriginVelocityKps = GameObjectReader.ReadVector(originVelocity)
            };

            if (snapshot.Launcher != null && snapshot.HasOriginVelocity)
            {
                snapshot.Launcher.VelocityKps = snapshot.OriginVelocityKps;
                snapshot.Launcher.HasVelocityEvidence = true;
            }

            snapshot.Inventory = ExtractInventory(launcher, missileTemplate, snapshot.Launcher, snapshot.Missile, readinessEvidence);
            AddWeapon(snapshot.Launcher, missileTemplate, snapshot.Inventory);
            ApplyTryFireTargetVelocityEvidence(snapshot, readinessEvidence);
            AddTargetVelocityEvidence(snapshot);
            AddRelativeVelocityEvidence(snapshot);
            AddPdWeightEvidence(snapshot, targetObject);
            AddMissingFields(snapshot);
            return snapshot;
        }

        private static ShipSnapshot ExtractShip(object ship, string fallback)
        {
            bool hasVelocity = GameObjectReader.HasVector(ship, "velocityVector_kps", "velocity_kps", "VelocityKps", "velocity");
            ShipSnapshot snapshot = new ShipSnapshot
            {
                Id = GameObjectReader.StableId(ship, fallback),
                DisplayName = GameObjectReader.Label(ship, fallback),
                TeamId = GameObjectReader.TeamId(ship),
                HullClass = HullClass.Unknown,
                PositionKm = GameObjectReader.ReadVector(ship, "position", "Position", "centerOfMass", "CenterOfMass"),
                VelocityKps = GameObjectReader.ReadVector(ship, "velocityVector_kps", "velocity_kps", "VelocityKps", "velocity"),
                HasVelocityEvidence = hasVelocity,
                RemainingHullFraction = GameObjectReader.ReadDouble(ship, 1.0, "remainingHullFraction", "RemainingHullFraction"),
                IsDisabled = GameObjectReader.ReadBool(ship, false, "isDisabled", "IsDisabled", "disabled", "Disabled"),
                StrategicPriority = 1.0
            };

            return snapshot;
        }

        private static object ExtractTargetObject(object launcher, out string source)
        {
            object target = TryExtractTargetObject(
                launcher,
                "launcher",
                out source,
                "combatPrimaryTarget",
                "primaryTargetState",
                "primaryTarget",
                "target",
                "Target");
            source = target == null ? "none" : source;
            return target;
        }

        private static object TryExtractTargetObject(object owner, string ownerName, out string source, params string[] memberNames)
        {
            source = "none";
            object target = GameObjectReader.ReadFirstMember(owner, memberNames);
            target = NormalizeTarget(target);
            if (target == null)
            {
                return null;
            }

            source = ownerName;
            return target;
        }

        private static object ExtractReadinessTargetObject(ReadinessEvidenceSnapshot readinessEvidence, out string source)
        {
            source = "none";
            if (readinessEvidence == null || readinessEvidence.TargetRuntimeObject == null)
            {
                return null;
            }

            object target = NormalizeTarget(readinessEvidence.TargetRuntimeObject);
            if (target == null)
            {
                return null;
            }

            source = string.IsNullOrWhiteSpace(readinessEvidence.TargetIdentityEvidenceSource)
                ? "tryFireTarget"
                : readinessEvidence.TargetIdentityEvidenceSource;
            return target;
        }

        private static object NormalizeTarget(object target)
        {
            object current = target;
            for (int depth = 0; depth < 6 && current != null; depth++)
            {
                object next = GameObjectReader.ReadFirstMember(
                    current,
                    "combatTargetableState",
                    "CombatTargetableState",
                    "GetCombatantState",
                    "GetTargetableState",
                    "combatantState",
                    "CombatantState",
                    "shipState",
                    "ShipState",
                    "weaponCarrierState",
                    "WeaponCarrierState",
                    "ref_ship",
                    "RefShip");
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
            MissileProfile missileProfile,
            ReadinessEvidenceSnapshot readinessEvidence)
        {
            object weapon = GameObjectReader.ReadFirstMember(launcher, "weapon", "Weapon", "weaponData", "module", "Module");
            int remainingShots = FirstKnownCount(weapon, launcher, missileTemplate, "remainingShots", "RemainingShots", "ammo", "Ammo", "magazine", "missileCount", "remainingMissiles");
            ReadinessEvidenceSnapshot evidence = BuildInventoryReadinessEvidence(readinessEvidence, remainingShots);

            return new MissileInventorySnapshot
            {
                LauncherShipId = launcherSnapshot == null ? "unknown-launcher" : launcherSnapshot.Id,
                WeaponId = GameObjectReader.StableId(weapon ?? missileTemplate, "weapon"),
                MissileProfileId = missileProfile == null ? "unknown-missile" : missileProfile.Id,
                AmmoGateBudgetShots = evidence.AmmoGateBudgetShots,
                RemainingShots = remainingShots,
                AmmoGateBudgetEvidenceSource = evidence.AmmoGateBudgetEvidenceSource,
                AmmoGateBudgetMissingReason = evidence.AmmoGateBudgetMissingReason,
                AmmoEvidenceSource = evidence.AmmoEvidenceSource,
                LiveWeaponState = evidence.LiveWeaponState,
                AmmoGateWeaponCount = evidence.AmmoGateWeaponCount,
                UnknownAmmoGateWeaponCount = evidence.UnknownAmmoGateWeaponCount
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
                AmmoGateBudgetShots = inventory == null ? -1 : inventory.AmmoGateBudgetShots,
                RemainingShots = inventory == null ? -1 : inventory.RemainingShots,
                AmmoGateBudgetEvidenceSource = inventory == null ? "unknown" : inventory.AmmoGateBudgetEvidenceSource,
                AmmoGateBudgetMissingReason = inventory == null ? "missing inventory" : inventory.AmmoGateBudgetMissingReason,
                AmmoEvidenceSource = inventory == null ? "unknown" : inventory.AmmoEvidenceSource,
                LiveWeaponState = inventory == null ? "unknown" : inventory.LiveWeaponState,
                AmmoGateWeaponCount = inventory == null ? -1 : inventory.AmmoGateWeaponCount,
                UnknownAmmoGateWeaponCount = inventory == null ? 1 : inventory.UnknownAmmoGateWeaponCount
            });
        }

        private static ReadinessEvidenceSnapshot BuildInventoryReadinessEvidence(
            ReadinessEvidenceSnapshot readinessEvidence,
            int remainingShots)
        {
            if (readinessEvidence != null)
            {
                return new ReadinessEvidenceSnapshot
                {
                    AmmoGateBudgetShots = readinessEvidence.AmmoGateBudgetShots,
                    AmmoGateBudgetEvidenceSource = CleanEvidence(readinessEvidence.AmmoGateBudgetEvidenceSource, "unknown"),
                    AmmoGateBudgetMissingReason = CleanEvidence(readinessEvidence.AmmoGateBudgetMissingReason, "unknown"),
                    AmmoEvidenceSource = CleanEvidence(readinessEvidence.AmmoEvidenceSource, "unknown"),
                    LiveWeaponState = CleanEvidence(readinessEvidence.LiveWeaponState, "unknown"),
                    AmmoGateWeaponCount = readinessEvidence.AmmoGateWeaponCount,
                    UnknownAmmoGateWeaponCount = readinessEvidence.UnknownAmmoGateWeaponCount,
                    HasTargetVelocity = readinessEvidence.HasTargetVelocity,
                    TargetVelocityKps = readinessEvidence.TargetVelocityKps,
                    TargetVelocityEvidenceSource = CleanEvidence(readinessEvidence.TargetVelocityEvidenceSource, "unknown"),
                    TargetVelocityMissingReason = CleanEvidence(readinessEvidence.TargetVelocityMissingReason, "unknown"),
                    TargetRuntimeObject = readinessEvidence.TargetRuntimeObject,
                    TargetIdentityEvidenceSource = CleanEvidence(readinessEvidence.TargetIdentityEvidenceSource, "unknown")
                };
            }

            if (remainingShots >= 0)
            {
                return new ReadinessEvidenceSnapshot
                {
                    AmmoGateBudgetEvidenceSource = "unknown",
                    AmmoGateBudgetMissingReason = "ammo-only projectile snapshot evidence",
                    AmmoEvidenceSource = "projectileSnapshotCount",
                    LiveWeaponState = "missing live weapon correlation",
                    UnknownAmmoGateWeaponCount = 1,
                    TargetVelocityEvidenceSource = "unknown",
                    TargetVelocityMissingReason = "missing live weapon correlation"
                };
            }

            return new ReadinessEvidenceSnapshot
            {
                AmmoGateBudgetEvidenceSource = "unknown",
                AmmoGateBudgetMissingReason = "missing live weapon correlation",
                AmmoEvidenceSource = "none",
                LiveWeaponState = "missing live weapon correlation",
                UnknownAmmoGateWeaponCount = 1,
                TargetVelocityEvidenceSource = "unknown",
                TargetVelocityMissingReason = "missing live weapon correlation"
            };
        }

        private static WeaponRole MapWeaponRole(object weaponTemplate)
        {
            bool isMissile = GameObjectReader.ReadBool(weaponTemplate, true, "isMissileWeapon", "IsMissileWeapon");
            return isMissile ? WeaponRole.Missile : WeaponRole.Unknown;
        }

        private static void AddTargetVelocityEvidence(ExtractedCombatSnapshot snapshot)
        {
            if (snapshot.HasTargetVelocity)
            {
                if (string.IsNullOrWhiteSpace(snapshot.TargetVelocityEvidenceSource))
                {
                    snapshot.TargetVelocityEvidenceSource = "targetCombatState";
                }

                snapshot.TargetVelocityMissingReason = "none";
                return;
            }

            if (snapshot.Target == null)
            {
                snapshot.HasTargetVelocity = false;
                snapshot.TargetVelocityEvidenceSource = "unknown";
                snapshot.TargetVelocityMissingReason = "targetObjectUnavailable";
                return;
            }

            if (!HasConcreteIdentity(snapshot.Target, "target"))
            {
                snapshot.HasTargetVelocity = false;
                snapshot.TargetVelocityEvidenceSource = "unknown";
                snapshot.TargetVelocityMissingReason = "targetIdentityUnavailable";
                return;
            }

            if (!snapshot.Target.HasVelocityEvidence)
            {
                snapshot.HasTargetVelocity = false;
                snapshot.TargetVelocityEvidenceSource = "unknown";
                snapshot.TargetVelocityMissingReason = string.IsNullOrWhiteSpace(snapshot.TargetVelocityMissingReason)
                    ? "targetVelocityMemberUnavailable"
                    : snapshot.TargetVelocityMissingReason;
                return;
            }

            snapshot.HasTargetVelocity = true;
            snapshot.TargetVelocityKps = snapshot.Target.VelocityKps;
            snapshot.TargetVelocityEvidenceSource = "targetCombatState";
            snapshot.TargetVelocityMissingReason = "none";
        }

        private static void ApplyTryFireTargetVelocityEvidence(
            ExtractedCombatSnapshot snapshot,
            ReadinessEvidenceSnapshot readinessEvidence)
        {
            if (snapshot == null || readinessEvidence == null)
            {
                return;
            }

            if (!string.IsNullOrWhiteSpace(readinessEvidence.TargetVelocityEvidenceSource))
            {
                snapshot.TargetVelocityEvidenceSource = readinessEvidence.TargetVelocityEvidenceSource;
            }

            if (!string.IsNullOrWhiteSpace(readinessEvidence.TargetVelocityMissingReason))
            {
                snapshot.TargetVelocityMissingReason = readinessEvidence.TargetVelocityMissingReason;
            }

            if (!readinessEvidence.HasTargetVelocity)
            {
                return;
            }

            if (snapshot.Target != null)
            {
                snapshot.Target.VelocityKps = readinessEvidence.TargetVelocityKps;
                snapshot.Target.HasVelocityEvidence = true;
            }

            snapshot.HasTargetVelocity = true;
            snapshot.TargetVelocityKps = readinessEvidence.TargetVelocityKps;
            snapshot.TargetVelocityEvidenceSource = readinessEvidence.TargetVelocityEvidenceSource;
            snapshot.TargetVelocityMissingReason = "none";
        }

        private static void AddRelativeVelocityEvidence(ExtractedCombatSnapshot snapshot)
        {
            if (!snapshot.HasTargetVelocity)
            {
                snapshot.HasRelativeVelocity = false;
                snapshot.RelativeVelocityEvidenceSource = "unknown";
                snapshot.RelativeVelocityMissingReason = snapshot.TargetVelocityMissingReason;
                return;
            }

            if (!snapshot.HasOriginVelocity)
            {
                snapshot.HasRelativeVelocity = false;
                snapshot.RelativeVelocityEvidenceSource = "unknown";
                snapshot.RelativeVelocityMissingReason = "launcherVelocityUnavailable";
                return;
            }

            snapshot.RelativeVelocityKps = snapshot.TargetVelocityKps - snapshot.OriginVelocityKps;
            snapshot.RelativeSpeedKps = snapshot.RelativeVelocityKps.Length();
            snapshot.HasRelativeVelocity = true;
            snapshot.RelativeVelocityEvidenceSource = "targetAndLauncherVelocity";
            snapshot.RelativeVelocityMissingReason = "none";
        }

        private static void AddPdWeightEvidence(ExtractedCombatSnapshot snapshot, object targetObject)
        {
            if (snapshot == null)
            {
                return;
            }

            if (targetObject == null || snapshot.Target == null || !HasConcreteIdentity(snapshot.Target, "target"))
            {
                SetDefaultPdWeight(snapshot, targetObject == null ? "targetObjectUnavailable" : "targetIdentityUnavailable");
                return;
            }

            PdWeaponEvidence evidence = ExtractPdWeaponEvidence(targetObject);
            if (!evidence.HasWeaponTemplateSource)
            {
                SetDefaultPdWeight(snapshot, "targetWeaponTemplatesUnavailable");
                return;
            }

            if (evidence.InspectedWeaponCount == 0 && evidence.ObservedWeaponCount > 0)
            {
                SetDefaultPdWeight(snapshot, "targetWeaponDefenseModeUnavailable");
                return;
            }

            snapshot.PdWeight = evidence.PointDefenseWeight;
            snapshot.PdWeightEvidenceSource = "observedTargetWeaponTemplates";
            snapshot.PdWeightDefaulted = false;
            snapshot.PdWeightDefaultReason = "none";
            snapshot.PdWeightMissingReason = "none";
            snapshot.PdEvidenceQuality = evidence.HasTemplateCapability
                ? "observedTemplateCapability"
                : "observedPresenceOnly";
            snapshot.PdCapabilityEvidenceSource = evidence.HasTemplateCapability
                ? "observedTargetWeaponTemplateCapability"
                : "observedTargetWeaponTemplates";
            snapshot.PdCapabilityWeaponCount = evidence.PointDefenseWeapons.Count;
            snapshot.PdCapabilityRangeKm = evidence.MaxCapabilityRangeKm;
            snapshot.PdCapabilityCooldownSeconds = evidence.AverageCapabilityCooldownSeconds;
            snapshot.PdCapabilityObservedFields = evidence.ObservedFields;
            snapshot.PdCapabilityMissingReason = evidence.HasTemplateCapability ? "none" : "templateCapabilityFieldsUnavailable";
            snapshot.PdCapabilityLimitations = evidence.HasTemplateCapability
                ? "templateCapabilityOnly,noLiveReadiness,noGeometry,noArcCoverage"
                : "defenseModePresenceOnly,noTemplateCapability,noLiveReadiness,noGeometry";

            foreach (WeaponSnapshot weapon in evidence.PointDefenseWeapons)
            {
                snapshot.Target.Weapons.Add(weapon);
            }
        }

        private static void SetDefaultPdWeight(ExtractedCombatSnapshot snapshot, string missingReason)
        {
            snapshot.PdWeight = 0.0;
            snapshot.PdWeightEvidenceSource = "defaultModel";
            snapshot.PdWeightDefaulted = true;
            snapshot.PdWeightDefaultReason = "pdEvidenceUnavailable";
            snapshot.PdWeightMissingReason = string.IsNullOrWhiteSpace(missingReason) ? "unknown" : missingReason;
            snapshot.PdEvidenceQuality = "defaultModel";
            snapshot.PdCapabilityEvidenceSource = "none";
            snapshot.PdCapabilityWeaponCount = 0;
            snapshot.PdCapabilityRangeKm = 0.0;
            snapshot.PdCapabilityCooldownSeconds = 0.0;
            snapshot.PdCapabilityObservedFields = "none";
            snapshot.PdCapabilityMissingReason = snapshot.PdWeightMissingReason;
            snapshot.PdCapabilityLimitations = "targetPdEvidenceUnavailable";
        }

        private static PdWeaponEvidence ExtractPdWeaponEvidence(object targetObject)
        {
            PdWeaponEvidence evidence = new PdWeaponEvidence();
            foreach (object weaponTemplate in ReadTargetWeaponTemplates(targetObject))
            {
                object template = NormalizeWeaponTemplate(weaponTemplate);
                if (template == null)
                {
                    continue;
                }

                evidence.HasWeaponTemplateSource = true;
                evidence.ObservedWeaponCount++;

                bool defenseMode;
                if (!TryReadBool(template, out defenseMode, "defenseMode", "DefenseMode"))
                {
                    continue;
                }

                evidence.InspectedWeaponCount++;
                if (!defenseMode)
                {
                    continue;
                }

                double supportRange = ReadNonNegativeDouble(
                    template,
                    "EffectiveRangeAgainstProjectiles_km",
                    "effectiveRangeAgainstProjectiles_km",
                    "targetingRange_km",
                    "TargetingRangeKm");
                double cooldownSeconds = ReadNonNegativeDouble(
                    template,
                    "averageCooldown_s",
                    "AverageCooldownSeconds",
                    "cooldown_s",
                    "CooldownSeconds");
                int salvoShots = ReadPositiveInt(template, "salvo_shots", "SalvoShots");
                int magazine = ReadPositiveInt(template, "magazine", "Magazine");

                evidence.PointDefenseWeight += 1.0;
                evidence.AddCapability(supportRange, cooldownSeconds, salvoShots > 0 || magazine > 0);

                evidence.PointDefenseWeapons.Add(new WeaponSnapshot
                {
                    Id = GameObjectReader.StableId(template, "target-pd-weapon"),
                    DisplayName = GameObjectReader.Label(template, "target PD weapon"),
                    Role = WeaponRole.PointDefense,
                    PointDefenseWeight = 1.0,
                    ThreatWeight = 0.0,
                    CanDefendOtherShips = supportRange > 0.0,
                    SupportRangeKm = supportRange,
                    AmmoGateBudgetShots = -1,
                    RemainingShots = -1,
                    AmmoGateBudgetEvidenceSource = "notObservedForTargetPd",
                    AmmoGateBudgetMissingReason = "targetPdEvidenceOnly",
                    AmmoEvidenceSource = "notObservedForTargetPd",
                    LiveWeaponState = "notObservedForTargetPd",
                    AmmoGateWeaponCount = -1,
                    UnknownAmmoGateWeaponCount = 1
                });
            }

            return evidence;
        }

        private static int ReadPositiveInt(object instance, params string[] memberNames)
        {
            int count = GameObjectReader.ReadCount(instance, memberNames);
            return count > 0 ? count : 0;
        }

        private static IEnumerable<object> ReadTargetWeaponTemplates(object targetObject)
        {
            List<object> templates = ReadTemplatesFromMembers(
                targetObject,
                "allWeaponTemplates",
                "AllWeaponTemplates",
                "weaponTemplates",
                "WeaponTemplates");
            if (templates.Count > 0)
            {
                return templates;
            }

            object targetTemplate = GameObjectReader.ReadFirstMember(targetObject, "template", "Template");
            templates = ReadTemplatesFromMembers(
                targetTemplate,
                "allWeaponTemplates",
                "AllWeaponTemplates",
                "weaponTemplates",
                "WeaponTemplates");
            if (templates.Count > 0)
            {
                return templates;
            }

            templates = ReadTemplatesFromMembers(targetObject, "AllWeaponModuleData", "allWeapons", "noseWeapons", "hullWeapons");
            if (templates.Count > 0)
            {
                return templates;
            }

            return ReadTemplatesFromMembers(targetTemplate, "allWeapons", "AllWeapons", "noseWeapons", "hullWeapons");
        }

        private static List<object> ReadTemplatesFromMembers(object owner, params string[] memberNames)
        {
            List<object> templates = new List<object>();
            if (owner == null)
            {
                return templates;
            }

            foreach (string memberName in memberNames)
            {
                object value = GameObjectReader.ReadFirstMember(owner, memberName);
                AddTemplates(templates, value);
                if (templates.Count > 0)
                {
                    return templates;
                }
            }

            return templates;
        }

        private static void AddTemplates(List<object> templates, object value)
        {
            if (templates == null || value == null || value is string)
            {
                return;
            }

            IEnumerable enumerable = value as IEnumerable;
            if (enumerable == null)
            {
                templates.Add(value);
                return;
            }

            foreach (object item in enumerable)
            {
                if (item != null)
                {
                    templates.Add(item);
                }
            }
        }

        private static object NormalizeWeaponTemplate(object candidate)
        {
            if (candidate == null)
            {
                return null;
            }

            object moduleTemplate = GameObjectReader.ReadFirstMember(candidate, "moduleTemplate", "ModuleTemplate");
            object weaponTemplate = GameObjectReader.ReadFirstMember(
                moduleTemplate ?? candidate,
                "ref_weapon",
                "RefWeapon",
                "weaponTemplate",
                "WeaponTemplate");
            return weaponTemplate ?? candidate;
        }

        private static double ReadNonNegativeDouble(object instance, params string[] memberNames)
        {
            double value;
            return TryReadDouble(instance, out value, memberNames) && value > 0.0 ? value : 0.0;
        }

        private static bool TryReadDouble(object instance, out double parsed, params string[] memberNames)
        {
            parsed = 0.0;
            object value = GameObjectReader.ReadFirstMember(instance, memberNames);
            if (!(value is IConvertible))
            {
                return false;
            }

            try
            {
                parsed = Convert.ToDouble(value, CultureInfo.InvariantCulture);
                return true;
            }
            catch
            {
                parsed = 0.0;
                return false;
            }
        }

        private static bool TryReadBool(object instance, out bool parsed, params string[] memberNames)
        {
            parsed = false;
            object value = GameObjectReader.ReadFirstMember(instance, memberNames);
            if (value is bool boolValue)
            {
                parsed = boolValue;
                return true;
            }

            if (!(value is IConvertible))
            {
                return false;
            }

            string text = Convert.ToString(value, CultureInfo.InvariantCulture);
            if (bool.TryParse(text, out parsed))
            {
                return true;
            }

            try
            {
                parsed = Convert.ToDouble(value, CultureInfo.InvariantCulture) != 0.0;
                return true;
            }
            catch
            {
                parsed = false;
                return false;
            }
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

        private static string CleanEvidence(string value, string fallback)
        {
            return string.IsNullOrWhiteSpace(value) ? fallback : value;
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

            if (!snapshot.HasTargetVelocity)
            {
                snapshot.MissingFields.Add("targetVelocity");
            }

            if (snapshot.Inventory == null || snapshot.Inventory.AmmoGateBudgetShots < 0)
            {
                snapshot.MissingFields.Add("ammoGateBudgetShots");
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

        private sealed class PdWeaponEvidence
        {
            public PdWeaponEvidence()
            {
                PointDefenseWeapons = new List<WeaponSnapshot>();
            }

            public bool HasWeaponTemplateSource { get; set; }
            public int ObservedWeaponCount { get; set; }
            public int InspectedWeaponCount { get; set; }
            public double PointDefenseWeight { get; set; }
            public bool HasTemplateCapability { get; set; }
            public double MaxCapabilityRangeKm { get; private set; }
            public string ObservedFields
            {
                get
                {
                    List<string> fields = new List<string>();
                    if (_hasRange)
                    {
                        fields.Add("range");
                    }

                    if (_hasCooldown)
                    {
                        fields.Add("cooldown");
                    }

                    if (_hasAmmoCapacity)
                    {
                        fields.Add("ammoCapacity");
                    }

                    return fields.Count == 0 ? "none" : string.Join(",", fields.ToArray());
                }
            }

            public double AverageCapabilityCooldownSeconds
            {
                get
                {
                    return _cooldownCount == 0 ? 0.0 : _cooldownSumSeconds / _cooldownCount;
                }
            }

            public List<WeaponSnapshot> PointDefenseWeapons { get; private set; }

            private double _cooldownSumSeconds;
            private int _cooldownCount;
            private bool _hasRange;
            private bool _hasCooldown;
            private bool _hasAmmoCapacity;

            public void AddCapability(double rangeKm, double cooldownSeconds, bool hasAmmoCapacity)
            {
                if (rangeKm > 0.0)
                {
                    HasTemplateCapability = true;
                    _hasRange = true;
                    if (rangeKm > MaxCapabilityRangeKm)
                    {
                        MaxCapabilityRangeKm = rangeKm;
                    }
                }

                if (cooldownSeconds > 0.0)
                {
                    HasTemplateCapability = true;
                    _hasCooldown = true;
                    _cooldownSumSeconds += cooldownSeconds;
                    _cooldownCount++;
                }

                if (hasAmmoCapacity)
                {
                    HasTemplateCapability = true;
                    _hasAmmoCapacity = true;
                }
            }
        }
    }
}
