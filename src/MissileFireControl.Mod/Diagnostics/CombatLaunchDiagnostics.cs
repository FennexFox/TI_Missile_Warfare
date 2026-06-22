using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;
using MissileFireControl.Core.Models;
using MissileFireControl.Mod.Adapters;

namespace MissileFireControl.Mod.Diagnostics
{
    internal static class CombatLaunchDiagnostics
    {
        private const int MaxControlledCommandContexts = 16;
        private const int MaxControlledCommandLaunchMatches = 16;

        private static int _sequence;
        private static readonly object ControlledCommandContextLock = new object();
        private static readonly List<ControlledCommandLaunchContext> ControlledCommandContexts =
            new List<ControlledCommandLaunchContext>();

        [ThreadStatic]
        private static ReadinessEvidenceSnapshot _currentMissileTryFireReadiness;

        public static void RegisterControlledCommandContext(
            string commandResultId,
            string experimentId,
            string candidateId,
            string launcherId,
            string launcherName,
            string targetId,
            string targetName,
            int assignedShots)
        {
            if (!HasConcreteToken(commandResultId)
                || !HasConcreteToken(experimentId)
                || !HasConcreteToken(launcherId)
                || !HasConcreteToken(targetId))
            {
                return;
            }

            lock (ControlledCommandContextLock)
            {
                ControlledCommandContexts.RemoveAll(context => string.Equals(context.CommandResultId, commandResultId, StringComparison.Ordinal));
                ControlledCommandContexts.Add(new ControlledCommandLaunchContext
                {
                    CommandResultId = commandResultId,
                    ExperimentId = experimentId,
                    CandidateId = Clean(candidateId),
                    LauncherId = launcherId,
                    LauncherName = Clean(launcherName),
                    TargetId = targetId,
                    TargetName = Clean(targetName),
                    AssignedShots = assignedShots,
                    RegisteredUtc = DateTime.UtcNow
                });

                while (ControlledCommandContexts.Count > MaxControlledCommandContexts)
                {
                    ControlledCommandContexts.RemoveAt(0);
                }
            }
        }

        public static void ClearControlledCommandContext(string commandResultId)
        {
            if (!HasConcreteToken(commandResultId))
            {
                return;
            }

            lock (ControlledCommandContextLock)
            {
                ControlledCommandContexts.RemoveAll(context => string.Equals(context.CommandResultId, commandResultId, StringComparison.Ordinal));
            }
        }

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

        public static void OnMissileTryFirePrefix(object __instance, object[] __args, out object __state)
        {
            __state = null;
            if (!ShouldLog())
            {
                _currentMissileTryFireReadiness = null;
                return;
            }

            try
            {
                TryFireObservation observation = CaptureTryFireObservation(__instance, GetArg(__args, 0));
                __state = observation;
                _currentMissileTryFireReadiness = ToReadinessEvidence(observation);
            }
            catch (Exception ex)
            {
                _currentMissileTryFireReadiness = null;
                Log.Warning($"Pre-fire missile diagnostics failed: {ex.GetType().Name}: {ex.Message}");
            }
        }

        public static void OnMissileTryFirePostfix(object __instance, object[] __args, bool __result, object __state)
        {
            if (!__result || !ShouldLog())
            {
                _currentMissileTryFireReadiness = null;
                return;
            }

            WriteLaunchLine("MissileWeapon.TryFire", builder =>
            {
                TryFireObservation observation = __state as TryFireObservation;
                object weaponData = ReadMember(__instance, "weaponData");
                object weaponTemplate = ReadMember(__instance, "weaponTemplate");
                object combatant = ReadMember(__instance, "combatant");
                object launcher = ReadMember(combatant, "WeaponCarrierState");
                object target = ReadMember(__instance, "target");

                AppendPair(builder, "weapon", DescribeWeapon(__instance));
                AppendPair(builder, "launcher", Describe(launcher));
                AppendPair(builder, "launcherId", StableIdOrUnknown(launcher, "launcher"));
                string targetId = StableIdOrUnknown(target, "target");
                string targetStateId = TargetStateIdOrUnknown(target);
                AppendPair(builder, "target", Describe(target));
                AppendPair(builder, "targetId", targetId);
                AppendPair(builder, "targetStateId", targetStateId);
                AppendPair(builder, "targetedPosition", DescribeVector(ReadMember(__instance, "targetedPosition")));
                AppendPreFireTargetVelocityEvidence(builder, observation);
                AppendPair(builder, "fireMode", Describe(ReadMember(__instance, "currentFireMode")));
                AppendPair(builder, "currentTime", Describe(GetArg(__args, 0)));
                AppendPreFireWeaponAmmoEvidence(builder, observation);
                string postFireRemaining = AppendLiveWeaponAmmoEvidence(
                    builder,
                    __instance,
                    launcher,
                    weaponData,
                    weaponTemplate,
                    GetArg(__args, 0));
                AppendVisibleAmmoDelta(builder, observation, postFireRemaining);
                AppendControlledCommandContext(builder, launcher, target, observation, postFireRemaining);
                AppendPair(builder, "battle", BattleContext());
            });
            _currentMissileTryFireReadiness = null;
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
            SnapshotDiagnostics.LogProjectileFireSnapshot(__instance, __args, _currentMissileTryFireReadiness);
            ShadowAllocationDiagnostics.LogProjectileFireShadowAllocation(__instance, __args, _currentMissileTryFireReadiness);
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

        private static string AppendLiveWeaponAmmoEvidence(
            StringBuilder builder,
            object weapon,
            object launcher,
            object weaponData,
            object weaponTemplate,
            object currentTime)
        {
            string postFireRemainingText = "unknown";
            object postFireRemaining;
            if (TryReadAmmoByModule(launcher, weaponData, out postFireRemaining))
            {
                AppendPair(builder, "ammoEvidenceSource", "shipAmmoByWeaponData");
                AppendPair(builder, "postFireRemaining", Describe(postFireRemaining));
                postFireRemainingText = Describe(postFireRemaining);
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
            return postFireRemainingText;
        }

        private static void AppendVisibleAmmoDelta(
            StringBuilder builder,
            TryFireObservation observation,
            string postFireRemaining)
        {
            int delta;
            if (TryAmmoDelta(observation, postFireRemaining, out delta))
            {
                AppendPair(builder, "visibleAmmoDelta", delta.ToString(CultureInfo.InvariantCulture));
                AppendPair(builder, "visibleAmmoDeltaEvidenceSource", "tryFirePrePostAmmo");
                return;
            }

            AppendPair(builder, "visibleAmmoDelta", "unknown");
            AppendPair(builder, "visibleAmmoDeltaEvidenceSource", "unavailable");
        }

        private static void AppendControlledCommandContext(
            StringBuilder builder,
            object launcher,
            object target,
            TryFireObservation observation,
            string postFireRemaining)
        {
            string launcherId = StableIdOrUnknown(launcher, "launcher");
            string targetId = StableIdOrUnknown(target, "target");
            string targetStateId = TargetStateIdOrUnknown(target);
            ControlledCommandLaunchMatch match = FindControlledCommandContext(launcherId, targetId, targetStateId, observation, postFireRemaining);
            AppendPair(builder, "experimentId", match.ExperimentId);
            AppendPair(builder, "commandResultId", match.CommandResultId);
            AppendPair(builder, "candidateId", match.CandidateId);
            AppendPair(builder, "controlledCommandCorrelation", match.Correlation);
            AppendPair(builder, "controlledCommandCorrelationReason", match.Reason);
            AppendPair(builder, "commandAssignedShots", match.AssignedShots < 0 ? "unknown" : match.AssignedShots.ToString(CultureInfo.InvariantCulture));
            AppendPair(builder, "controlledCommandObservedSpentShots", match.ObservedSpentShots < 0 ? "unknown" : match.ObservedSpentShots.ToString(CultureInfo.InvariantCulture));
        }

        private static ControlledCommandLaunchMatch FindControlledCommandContext(
            string launcherId,
            string targetId,
            string targetStateId,
            TryFireObservation observation,
            string postFireRemaining)
        {
            if (!HasConcreteToken(launcherId) || (!HasConcreteToken(targetId) && !HasConcreteToken(targetStateId)))
            {
                return ControlledCommandLaunchMatch.None("launcherOrTargetIdentityUnavailable");
            }

            int ammoDelta;
            bool hasAmmoDelta = TryAmmoDelta(observation, postFireRemaining, out ammoDelta);
            lock (ControlledCommandContextLock)
            {
                // Prefer the newest matching controlled command context so repeated
                // same-launcher/same-target diagnostics do not attribute launches
                // to a stale earlier command result.
                ControlledCommandLaunchContext context = ControlledCommandContexts
                    .Where(candidate =>
                        string.Equals(candidate.LauncherId, launcherId, StringComparison.Ordinal)
                        && TargetIdentityMatches(candidate, targetId, targetStateId)
                        && candidate.AssociatedLaunchCount < MaxControlledCommandLaunchMatches
                        && (candidate.AssignedShots < 0 || candidate.ObservedSpentShots < candidate.AssignedShots))
                    .OrderByDescending(candidate => candidate.RegisteredUtc)
                    .FirstOrDefault();

                if (context == null)
                {
                    return ControlledCommandLaunchMatch.None("noMatchingAppliedControlledCommandContext");
                }

                context.AssociatedLaunchCount++;
                if (hasAmmoDelta && ammoDelta > 0)
                {
                    context.ObservedSpentShots += ammoDelta;
                }

                int observedSpentShots = context.ObservedSpentShots;
                if (context.AssignedShots >= 0 && observedSpentShots >= context.AssignedShots)
                {
                    ControlledCommandContexts.Remove(context);
                }

                return new ControlledCommandLaunchMatch
                {
                    ExperimentId = context.ExperimentId,
                    CommandResultId = context.CommandResultId,
                    CandidateId = context.CandidateId,
                    Correlation = "directRuntimeContext",
                    Reason = hasAmmoDelta ? "sameLauncherTargetWithPrePostAmmoDelta" : "sameLauncherTargetNoNumericAmmoDelta",
                    AssignedShots = context.AssignedShots,
                    ObservedSpentShots = hasAmmoDelta || observedSpentShots > 0
                        ? observedSpentShots
                        : -1
                };
            }
        }

        private static bool TryAmmoDelta(TryFireObservation observation, string postFireRemaining, out int delta)
        {
            delta = 0;
            if (observation == null || observation.AmmoEvidenceSource != "shipAmmoByWeaponData")
            {
                return false;
            }

            int preFire;
            int postFire;
            if (!int.TryParse(observation.Remaining, NumberStyles.Integer, CultureInfo.InvariantCulture, out preFire)
                || !int.TryParse(postFireRemaining, NumberStyles.Integer, CultureInfo.InvariantCulture, out postFire))
            {
                return false;
            }

            delta = preFire - postFire;
            return true;
        }

        private static TryFireObservation CaptureTryFireObservation(object weapon, object currentTime)
        {
            object weaponData = ReadMember(weapon, "weaponData");
            object weaponTemplate = ReadMember(weapon, "weaponTemplate");
            object combatant = ReadMember(weapon, "combatant");
            object launcher = ReadMember(combatant, "WeaponCarrierState");
            TryFireObservation observation = new TryFireObservation();

            object remaining;
            if (TryReadAmmoByModule(launcher, weaponData, out remaining))
            {
                observation.AmmoEvidenceSource = "shipAmmoByWeaponData";
                observation.Remaining = Describe(remaining);
            }
            else
            {
                observation.AmmoEvidenceSource = "none";
                observation.Remaining = "unknown";
            }

            observation.WeaponHasAmmo = Describe(InvokeMember(launcher, "WeaponHasAmmo", weaponData));
            observation.WeaponCanFire = Describe(InvokeMember(launcher, "WeaponCanFire", weaponData));
            observation.OnCooldown = Describe(InvokeMember(weapon, "OnCooldown", currentTime));
            observation.SalvoShotsFired = Describe(ReadMember(weapon, "shotsFiredThisSalvo"));
            observation.SalvoShots = Describe(ReadMember(weaponTemplate, "salvo_shots"));
            CaptureTargetVelocityObservation(weapon, currentTime, observation);
            return observation;
        }

        private static void AppendPreFireWeaponAmmoEvidence(StringBuilder builder, TryFireObservation observation)
        {
            if (observation == null)
            {
                AppendPair(builder, "preFireAmmoEvidenceSource", "unavailable");
                AppendPair(builder, "preFireRemaining", "unknown");
                AppendPair(builder, "preFireWeaponHasAmmo", "unknown");
                AppendPair(builder, "preFireWeaponCanFire", "unknown");
                AppendPair(builder, "preFireOnCooldown", "unknown");
                AppendPair(builder, "preFireSalvoShotsFired", "unknown");
                AppendPair(builder, "preFireSalvoShots", "unknown");
                return;
            }

            AppendPair(builder, "preFireAmmoEvidenceSource", observation.AmmoEvidenceSource);
            AppendPair(builder, "preFireRemaining", observation.Remaining);
            AppendPair(builder, "preFireWeaponHasAmmo", observation.WeaponHasAmmo);
            AppendPair(builder, "preFireWeaponCanFire", observation.WeaponCanFire);
            AppendPair(builder, "preFireOnCooldown", observation.OnCooldown);
            AppendPair(builder, "preFireSalvoShotsFired", observation.SalvoShotsFired);
            AppendPair(builder, "preFireSalvoShots", observation.SalvoShots);
        }

        private static void AppendPreFireTargetVelocityEvidence(StringBuilder builder, TryFireObservation observation)
        {
            if (observation == null)
            {
                AppendPair(builder, "preFireTargetVelocityKps", "unknown");
                AppendPair(builder, "preFireTargetVelocityEvidenceSource", "unavailable");
                AppendPair(builder, "preFireTargetVelocityMissingReason", "missing live weapon correlation");
                return;
            }

            AppendPair(
                builder,
                "preFireTargetVelocityKps",
                observation.HasTargetVelocity ? GameObjectReader.FormatVector(observation.TargetVelocityKps) : "unknown");
            AppendPair(builder, "preFireTargetVelocityEvidenceSource", observation.TargetVelocityEvidenceSource);
            AppendPair(builder, "preFireTargetVelocityMissingReason", observation.TargetVelocityMissingReason);
        }

        private static ReadinessEvidenceSnapshot ToReadinessEvidence(TryFireObservation observation)
        {
            if (observation == null)
            {
                return null;
            }

            int ammoGateBudgetShots = TryFireAmmoGateBudgetShots(observation);
            return new ReadinessEvidenceSnapshot
            {
                AmmoGateBudgetShots = ammoGateBudgetShots,
                AmmoGateBudgetEvidenceSource = ammoGateBudgetShots >= 0
                    ? "shipAmmoByWeaponData+TryFireCommonGates"
                    : "unknown",
                AmmoGateBudgetMissingReason = ammoGateBudgetShots >= 0
                    ? "none"
                    : MissingAmmoGateBudgetReason(observation),
                AmmoEvidenceSource = observation.AmmoEvidenceSource,
                LiveWeaponState = "preFireWeaponHasAmmo=" + observation.WeaponHasAmmo
                    + ";preFireWeaponCanFire=" + observation.WeaponCanFire
                    + ";preFireOnCooldown=" + observation.OnCooldown
                    + ";preFireSalvoShotsFired=" + observation.SalvoShotsFired
                    + ";preFireSalvoShots=" + observation.SalvoShots,
                AmmoGateWeaponCount = ammoGateBudgetShots >= 0 ? 1 : -1,
                UnknownAmmoGateWeaponCount = ammoGateBudgetShots >= 0 ? 0 : 1,
                HasTargetVelocity = observation.HasTargetVelocity,
                TargetVelocityKps = observation.TargetVelocityKps,
                TargetVelocityEvidenceSource = observation.TargetVelocityEvidenceSource,
                TargetVelocityMissingReason = observation.TargetVelocityMissingReason,
                TargetRuntimeObject = observation.TargetRuntimeObject,
                TargetIdentityEvidenceSource = observation.TargetRuntimeObject == null ? "unknown" : "tryFireTarget"
            };
        }

        private static int TryFireAmmoGateBudgetShots(TryFireObservation observation)
        {
            if (observation == null || observation.AmmoEvidenceSource != "shipAmmoByWeaponData")
            {
                return -1;
            }

            if (!IsTextTrue(observation.WeaponHasAmmo)
                || !IsTextTrue(observation.WeaponCanFire)
                || !IsTextFalse(observation.OnCooldown))
            {
                return -1;
            }

            int remaining;
            if (!int.TryParse(observation.Remaining, NumberStyles.Integer, CultureInfo.InvariantCulture, out remaining))
            {
                return -1;
            }

            return remaining < 0 ? -1 : remaining;
        }

        private static string MissingAmmoGateBudgetReason(TryFireObservation observation)
        {
            if (observation == null)
            {
                return "missing live weapon correlation";
            }

            if (observation.AmmoEvidenceSource != "shipAmmoByWeaponData")
            {
                return "missing module-keyed ammo evidence";
            }

            if (!HasLiveGateEvidence(observation))
            {
                return "missing ammo/gate evidence";
            }

            return "ammo/gate evidence not currently fireable";
        }

        private static bool IsTextTrue(string value)
        {
            return string.Equals(value, "true", StringComparison.OrdinalIgnoreCase);
        }

        private static bool IsTextFalse(string value)
        {
            return string.Equals(value, "false", StringComparison.OrdinalIgnoreCase);
        }

        private static bool HasLiveGateEvidence(TryFireObservation observation)
        {
            return observation != null
                && observation.WeaponHasAmmo != "unknown"
                && observation.WeaponCanFire != "unknown"
                && observation.OnCooldown != "unknown";
        }

        private static void CaptureTargetVelocityObservation(
            object weapon,
            object currentTime,
            TryFireObservation observation)
        {
            object target = ReadMember(weapon, "target");
            observation.TargetRuntimeObject = target;
            if (target == null)
            {
                observation.HasTargetVelocity = false;
                observation.TargetVelocityEvidenceSource = "unknown";
                observation.TargetVelocityMissingReason = "tryFireTargetUnavailable";
                return;
            }

            if (TryReadVector(target, out Vector3d directVelocity, "velocityVector_kps"))
            {
                observation.HasTargetVelocity = true;
                observation.TargetVelocityKps = directVelocity;
                observation.TargetVelocityEvidenceSource = "tryFireTargetDamageableVelocity";
                observation.TargetVelocityMissingReason = "none";
                return;
            }

            if (TryDeriveTargetVelocityFromPositionAtTime(target, currentTime, out Vector3d derivedVelocity))
            {
                observation.HasTargetVelocity = true;
                observation.TargetVelocityKps = derivedVelocity;
                observation.TargetVelocityEvidenceSource = "tryFireTargetPositionAtTimeDelta";
                observation.TargetVelocityMissingReason = "none";
                return;
            }

            observation.HasTargetVelocity = false;
            observation.TargetVelocityEvidenceSource = "unknown";
            observation.TargetVelocityMissingReason = "tryFireTargetVelocityUnavailable";
        }

        private static bool TryDeriveTargetVelocityFromPositionAtTime(
            object target,
            object currentTime,
            out Vector3d velocityKps)
        {
            velocityKps = Vector3d.Zero;
            if (!(currentTime is DateTime time))
            {
                return false;
            }

            const double seconds = 1.0;
            object currentPosition = InvokeMember(target, "positionAtTime", time);
            object futurePosition = InvokeMember(target, "positionAtTime", time.AddSeconds(seconds));
            if (!TryReadVector(currentPosition, out Vector3d current)
                || !TryReadVector(futurePosition, out Vector3d future))
            {
                return false;
            }

            Vector3d deltaScaleUnits = future - current;
            velocityKps = deltaScaleUnits * (1.0 / (seconds * 0.05));
            return true;
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

        private static bool TryReadVector(object value, out Vector3d vector, params string[] memberNames)
        {
            vector = Vector3d.Zero;
            object source = memberNames == null || memberNames.Length == 0 ? value : ReadFirstMember(value, memberNames);
            if (!GameObjectReader.HasVector(source))
            {
                return false;
            }

            vector = GameObjectReader.ReadVector(source);
            return true;
        }

        private static object ReadFirstMember(object instance, params string[] memberNames)
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

        private static string StableIdOrUnknown(object value, string fallbackPrefix)
        {
            string id = GameObjectReader.StableId(value, fallbackPrefix);
            return HasConcreteToken(id) ? id : "unknown";
        }

        private static string TargetStateIdOrUnknown(object target)
        {
            string memberId = FirstNonEmptyMember(
                target,
                "id",
                "ID",
                "gameStateID",
                "GameStateID");
            if (HasConcreteToken(memberId))
            {
                return Clean(memberId);
            }

            string describedId = IdSuffixOrUnknown(Describe(target));
            if (HasConcreteToken(describedId))
            {
                return describedId;
            }

            string labelId = FirstNonEmptyMember(
                target,
                "displayName",
                "DisplayName",
                "fullName",
                "FullName",
                "name",
                "Name");
            return HasConcreteToken(labelId) ? Clean(labelId) : "unknown";
        }

        private static bool TargetIdentityMatches(
            ControlledCommandLaunchContext candidate,
            string targetId,
            string targetStateId)
        {
            if (candidate == null || string.IsNullOrWhiteSpace(candidate.TargetId))
            {
                return false;
            }

            return string.Equals(candidate.TargetId, targetId, StringComparison.Ordinal)
                || string.Equals(candidate.TargetId, targetStateId, StringComparison.Ordinal);
        }

        private static string IdSuffixOrUnknown(string text)
        {
            if (string.IsNullOrWhiteSpace(text))
            {
                return "unknown";
            }

            int hashIndex = text.LastIndexOf('#');
            if (hashIndex >= 0 && hashIndex < text.Length - 1)
            {
                return Clean(text.Substring(hashIndex + 1));
            }

            int colonIndex = text.LastIndexOf(':');
            if (colonIndex >= 0 && colonIndex < text.Length - 1)
            {
                return Clean(text.Substring(colonIndex + 1));
            }

            return "unknown";
        }

        private static bool HasConcreteToken(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return false;
            }

            return !value.StartsWith("unknown", StringComparison.Ordinal);
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

        private sealed class TryFireObservation
        {
            public string AmmoEvidenceSource { get; set; }

            public string Remaining { get; set; }

            public string WeaponHasAmmo { get; set; }

            public string WeaponCanFire { get; set; }

            public string OnCooldown { get; set; }

            public string SalvoShotsFired { get; set; }

            public string SalvoShots { get; set; }

            public bool HasTargetVelocity { get; set; }

            public Vector3d TargetVelocityKps { get; set; }

            public string TargetVelocityEvidenceSource { get; set; }

            public string TargetVelocityMissingReason { get; set; }

            public object TargetRuntimeObject { get; set; }
        }

        private sealed class ControlledCommandLaunchContext
        {
            public string CommandResultId { get; set; }

            public string ExperimentId { get; set; }

            public string CandidateId { get; set; }

            public string LauncherId { get; set; }

            public string LauncherName { get; set; }

            public string TargetId { get; set; }

            public string TargetName { get; set; }

            public int AssignedShots { get; set; }

            public int ObservedSpentShots { get; set; }

            public int AssociatedLaunchCount { get; set; }

            public DateTime RegisteredUtc { get; set; }
        }

        private sealed class ControlledCommandLaunchMatch
        {
            public string ExperimentId { get; set; } = "none";

            public string CommandResultId { get; set; } = "none";

            public string CandidateId { get; set; } = "none";

            public string Correlation { get; set; } = "none";

            public string Reason { get; set; } = "unknown";

            public int AssignedShots { get; set; } = -1;

            public int ObservedSpentShots { get; set; } = -1;

            public static ControlledCommandLaunchMatch None(string reason)
            {
                return new ControlledCommandLaunchMatch
                {
                    Reason = string.IsNullOrWhiteSpace(reason) ? "unknown" : reason
                };
            }
        }
    }
}
