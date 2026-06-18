using System.Xml.Serialization;
using UnityModManagerNet;

namespace MissileFireControl.Mod
{
    [XmlRoot("MissileWarfareSettings")]
    [XmlType("MissileWarfareSettings")]
    public sealed class ModSettings : UnityModManager.ModSettings
    {
        public bool EnableDiagnostics = true;
        public bool EnableSnapshotDiagnostics = false;
        public bool EnableRecommendationOnlyMode = true;
        public bool EnableLaunchDiscipline = false;
        public double MinimumLaunchScore = 0.35;

        public override void Save(UnityModManager.ModEntry modEntry)
        {
            Save(this, modEntry);
        }
    }
}
