"""
ALOA Registry Scanner — Detect installed applications via Windows Registry.
"""

import winreg
import time
from dataclasses import dataclass
from typing import Optional, List
from utils.constants import REG_UNINSTALL_PATHS


@dataclass
class InstalledApp:
    """Represents a detected installed application."""
    display_name: str
    version: Optional[str]
    publisher: Optional[str]
    install_location: Optional[str]
    uninstall_string: Optional[str]
    install_date: Optional[str]
    estimated_size_kb: Optional[int]
    registry_key: str


# ── Registry Cache ──────────────────────────────────────────────────
_APP_CACHE: List[InstalledApp] = []
_LAST_SCAN_TIME: float = 0
_CACHE_TTL = 300  # 5 minutes


def clear_cache():
    """Force a re-scan on the next request."""
    global _LAST_SCAN_TIME
    _LAST_SCAN_TIME = 0


def _read_reg_value(key, name: str) -> Optional[str]:
    """Safely read a registry value, returning None if not found."""
    try:
        value, _ = winreg.QueryValueEx(key, name)
        return str(value) if value is not None else None
    except (FileNotFoundError, OSError):
        return None


def scan_installed_apps(refresh: bool = False) -> List[InstalledApp]:
    """Scan the Windows Registry for all installed applications.

    Uses a cache to avoid redundant scans unless refresh=True or TTL expired.
    """
    global _APP_CACHE, _LAST_SCAN_TIME

    now = time.time()
    if not refresh and _APP_CACHE and (now - _LAST_SCAN_TIME < _CACHE_TTL):
        return _APP_CACHE

    apps: List[InstalledApp] = []
    hives = [
        (winreg.HKEY_LOCAL_MACHINE, "HKLM"),
        (winreg.HKEY_CURRENT_USER, "HKCU"),
    ]

    for hive, hive_name in hives:
        for reg_path in REG_UNINSTALL_PATHS:
            try:
                with winreg.OpenKey(hive, reg_path) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                name = _read_reg_value(subkey, "DisplayName")
                                if not name:
                                    continue

                                size_str = _read_reg_value(subkey, "EstimatedSize")
                                size_kb = None
                                if size_str:
                                    try:
                                        size_kb = int(size_str)
                                    except ValueError:
                                        pass

                                app = InstalledApp(
                                    display_name=name,
                                    version=_read_reg_value(subkey, "DisplayVersion"),
                                    publisher=_read_reg_value(subkey, "Publisher"),
                                    install_location=_read_reg_value(subkey, "InstallLocation"),
                                    uninstall_string=_read_reg_value(subkey, "UninstallString"),
                                    install_date=_read_reg_value(subkey, "InstallDate"),
                                    estimated_size_kb=size_kb,
                                    registry_key=f"{hive_name}\\{reg_path}\\{subkey_name}",
                                )
                                apps.append(app)
                        except OSError:
                            continue
            except OSError:
                continue

    _APP_CACHE = apps
    _LAST_SCAN_TIME = time.time()
    return apps


def find_app(name: str) -> list[InstalledApp]:
    """Search for installed apps matching the given name (case-insensitive)."""
    all_apps = scan_installed_apps()
    query = name.lower()
    return [app for app in all_apps if query in app.display_name.lower()]


def get_install_location(name: str) -> Optional[str]:
    """Find the install location for an app by name."""
    matches = find_app(name)
    for app in matches:
        if app.install_location:
            return app.install_location
    return None
