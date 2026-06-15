using System;

namespace MissileFireControl.Mod
{
    internal static class Log
    {
        public static void Info(string message)
        {
            Main.ModEntry?.Logger.Log("[MFC] " + message);
        }

        public static void Warning(string message)
        {
            Main.ModEntry?.Logger.Warning("[MFC] " + message);
        }

        public static void Error(string message, Exception exception = null)
        {
            if (exception == null)
            {
                Main.ModEntry?.Logger.Error("[MFC] " + message);
                return;
            }

            Main.ModEntry?.Logger.Error("[MFC] " + message + "\n" + exception);
        }
    }
}
