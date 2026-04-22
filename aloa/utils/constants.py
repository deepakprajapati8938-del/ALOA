"""
ALOA Constants — Thresholds, known paths, and configuration values.
"""

import os

# ── Performance Thresholds ──────────────────────────────────────────
RAM_WARNING_PERCENT = 75
RAM_CRITICAL_PERCENT = 90
CPU_WARNING_PERCENT = 70
CPU_CRITICAL_PERCENT = 90
CPU_SPIKE_DURATION_SECONDS = 5
DISK_WARNING_PERCENT = 80
DISK_CRITICAL_PERCENT = 95

# ── Unused App Detection ────────────────────────────────────────────
UNUSED_APP_DAYS_THRESHOLD = 90

# ── Large File Threshold ────────────────────────────────────────────
LARGE_FILE_SIZE_MB = 500

# ── Clutter Directories (Windows) ───────────────────────────────────
TEMP_DIR = os.environ.get("TEMP", r"C:\Users\Default\AppData\Local\Temp")
LOCAL_APPDATA = os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local")
APPDATA = os.environ.get("APPDATA", r"C:\Users\Default\AppData\Roaming")

CLUTTER_DIRECTORIES = [
    TEMP_DIR,
    os.path.join(LOCAL_APPDATA, "Temp"),
    os.path.join(LOCAL_APPDATA, r"Google\Chrome\User Data\Default\Cache"),
    os.path.join(LOCAL_APPDATA, r"Microsoft\Edge\User Data\Default\Cache"),
    os.path.join(LOCAL_APPDATA, r"Mozilla\Firefox\Profiles"),
    os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), r"Temp"),
    os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), r"SoftwareDistribution\Download"),
    os.path.join(LOCAL_APPDATA, r"CrashDumps"),
]

# ── Registry Keys ───────────────────────────────────────────────────
REG_UNINSTALL_PATHS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
]

REG_STARTUP_PATHS = [
    (r"HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (r"HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
    (r"HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (r"HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
]

# ── Common Binary Subdirectories ────────────────────────────────────
COMMON_BIN_SUBDIRS = ["bin", "Scripts", "cmd", "usr\\bin"]

# ── Startup Folder ──────────────────────────────────────────────────
STARTUP_FOLDER = os.path.join(
    APPDATA, r"Microsoft\Windows\Start Menu\Programs\Startup"
)

# ── Impact Classification Thresholds ────────────────────────────────
STARTUP_HIGH_IMPACT_CPU = 5.0      # % CPU at boot
STARTUP_HIGH_IMPACT_MEM_MB = 100   # MB RAM at boot
STARTUP_MEDIUM_IMPACT_CPU = 2.0
STARTUP_MEDIUM_IMPACT_MEM_MB = 50

# ── Protected Processes (must never be killed during cleanup) ────────
# Covers: Windows kernel & subsystems, security, drivers, shell, system
PROTECTED_PROCESSES: set[str] = {
    # ── Windows Kernel & Core Subsystems ────────────────────────
    "system",
    "system idle process",
    "smss.exe",          # Session Manager
    "csrss.exe",         # Client/Server Runtime
    "wininit.exe",       # Windows Initialisation
    "winlogon.exe",      # Windows Logon
    "lsass.exe",         # Local Security Authority
    "lsaiso.exe",        # Isolated LSA (Credential Guard)
    "services.exe",      # Service Control Manager
    "svchost.exe",       # Generic Service Host
    "ntoskrnl.exe",      # NT Kernel
    "hal.dll",
    "dwm.exe",           # Desktop Window Manager
    "explorer.exe",      # Windows Shell
    "taskhostw.exe",     # Task Host
    "taskeng.exe",
    "conhost.exe",       # Console Host
    "fontdrvhost.exe",   # Font Driver Host
    "sihost.exe",        # Shell Infrastructure Host
    "ctfmon.exe",        # Text Services Framework
    "userinit.exe",

    # ── Windows Security ─────────────────────────────────────────
    "msmpeng.exe",       # Windows Defender Antimalware
    "mssense.exe",       # Windows Defender Advanced Threat
    "securityhealthservice.exe",
    "securityhealthsystray.exe",
    "nissrv.exe",        # Defender Network Inspection
    "mpcmdrun.exe",
    "smartscreen.exe",

    # ── Hardware & Driver Services ────────────────────────────────
    "audiodg.exe",       # Audio Device Graph
    "spoolsv.exe",       # Print Spooler
    "ibmpmsvc.exe",
    "igfxem.exe",        # Intel Graphics
    "igfxpers.exe",
    "igfxtray.exe",
    "nvdisplay.container.exe",  # NVIDIA Display
    "nvvsvc.exe",
    "amdow.exe",

    # ── Power, Networking & Storage ──────────────────────────────
    "wlanext.exe",
    "netsh.exe",
    "dllhost.exe",
    "msdtc.exe",
    "searchindexer.exe",
    "searchhost.exe",
    "antimalware service executable",

    # ── Windows Update & Maintenance ─────────────────────────────
    "wuauclt.exe",
    "trustedinstaller.exe",
    "musnotifyicon.exe",
    "tiworker.exe",

    # ── ALOA Itself ───────────────────────────────────────────────
    "python.exe",
    "python3.exe",
    "pythonw.exe",
    "cmd.exe",
    "powershell.exe",
    "pwsh.exe",
}


def is_protected(process_name: str) -> bool:
    """Return True if the process should never be killed by ALOA.

    Comparison is case-insensitive and strips whitespace.
    """
    return process_name.strip().lower() in PROTECTED_PROCESSES
