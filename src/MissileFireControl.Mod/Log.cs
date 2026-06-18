using System;
using System.IO;
using System.Text;
using UnityEngine;
using UnityModManagerNet;

namespace MissileFireControl.Mod
{
    internal static class Log
    {
        private static readonly object FileLock = new object();

        private static UnityModManager.ModEntry _modEntry;
        private static bool _fileLoggingDisabled;

        public static string FileLogPath { get; private set; }

        public static void Initialize(UnityModManager.ModEntry modEntry)
        {
            _modEntry = modEntry;
            _fileLoggingDisabled = false;

            try
            {
                FileLogPath = ResolveFileLogPath();
                WriteFile("Info", "[MFC] --- MissileWarfare session start ---");
            }
            catch (Exception ex)
            {
                FileLogPath = null;
                _fileLoggingDisabled = true;
                modEntry?.Logger.Warning("[MFC] File logging disabled: " + ex.GetType().Name + ": " + ex.Message);
            }
        }

        public static void Info(string message)
        {
            string formatted = "[MFC] " + message;
            Logger?.Log(formatted);
            WriteFile("Info", formatted);
        }

        public static void Warning(string message)
        {
            string formatted = "[MFC] " + message;
            Logger?.Warning(formatted);
            WriteFile("Warning", formatted);
        }

        public static void Error(string message, Exception exception = null)
        {
            string formatted = "[MFC] " + message;
            if (exception == null)
            {
                Logger?.Error(formatted);
                WriteFile("Error", formatted);
                return;
            }

            Logger?.Error(formatted + "\n" + exception);
            WriteFile("Error", formatted, exception);
        }

        private static UnityModManager.ModEntry.ModLogger Logger
        {
            get { return (_modEntry ?? Main.ModEntry)?.Logger; }
        }

        private static string ResolveFileLogPath()
        {
            string root = null;
            try
            {
                root = Application.persistentDataPath;
            }
            catch
            {
                root = null;
            }

            if (string.IsNullOrWhiteSpace(root))
            {
                root = _modEntry?.Path ?? AppDomain.CurrentDomain.BaseDirectory;
            }

            string directory = Path.Combine(root, "MissileWarfare");
            Directory.CreateDirectory(directory);
            return Path.Combine(directory, "MissileWarfare.log");
        }

        private static void WriteFile(string level, string message, Exception exception = null)
        {
            if (_fileLoggingDisabled || string.IsNullOrWhiteSpace(FileLogPath))
            {
                return;
            }

            try
            {
                string text = DateTime.UtcNow.ToString("O") + " [" + level + "] " + message;
                if (exception != null)
                {
                    text += Environment.NewLine + exception;
                }

                lock (FileLock)
                {
                    File.AppendAllText(FileLogPath, text + Environment.NewLine, Encoding.UTF8);
                }
            }
            catch (Exception ex)
            {
                _fileLoggingDisabled = true;
                Logger?.Warning("[MFC] File logging disabled: " + ex.GetType().Name + ": " + ex.Message);
            }
        }
    }
}
