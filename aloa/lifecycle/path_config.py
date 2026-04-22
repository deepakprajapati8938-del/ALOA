"""
ALOA PATH Configurator — Auto-detect and configure environment variables.
"""

import os
import winreg
import ctypes
from typing import Optional
from core.parser import ParsedCommand
from lifecycle.registry import get_install_location
from utils.constants import COMMON_BIN_SUBDIRS
from utils.formatting import (
    console, success_panel, warning_panel, info_panel,
    error_panel, make_table, print_header
)


# ── Core PATH Operations ───────────────────────────────────────────

def get_user_path() -> list[str]:
    """Read the current user-level PATH entries."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Environment", 0,
            winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, "Path")
            return [p.strip() for p in value.split(";") if p.strip()]
    except (FileNotFoundError, OSError):
        return []


def get_system_path() -> list[str]:
    """Read the current system-level PATH entries."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            0, winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, "Path")
            return [p.strip() for p in value.split(";") if p.strip()]
    except (FileNotFoundError, OSError):
        return []


def add_to_user_path(directory: str) -> bool:
    """Add a directory to the user-level PATH.

    Returns True on success, False on failure.
    """
    current = get_user_path()

    # Check if already on PATH
    dir_lower = directory.lower()
    if any(p.lower() == dir_lower for p in current):
        console.print(info_panel(
            f"[cyan]{directory}[/cyan] is already on your PATH.",
            title="Already Configured"
        ))
        return True

    current.append(directory)
    new_path = ";".join(current)

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Environment", 0,
            winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)

        # Broadcast WM_SETTINGCHANGE so the change takes effect immediately
        _broadcast_env_change()

        console.print(success_panel(
            f"Added [bold cyan]{directory}[/bold cyan] to user PATH.\n"
            "Environment refreshed — new terminals will see the change.",
            title="PATH Updated"
        ))
        return True

    except OSError as e:
        console.print(error_panel(
            f"Failed to update PATH: {e}",
            title="PATH Update Failed"
        ))
        return False


def _broadcast_env_change():
    """Broadcast WM_SETTINGCHANGE to notify all windows of env change."""
    try:
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.c_long()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0,
            "Environment", SMTO_ABORTIFHUNG, 5000,
            ctypes.byref(result)
        )
    except Exception:
        pass  # Non-critical — worst case user reopens terminal


def auto_configure_path(app_name: str) -> bool:
    """Auto-detect and add the correct bin directory for an app to PATH.

    Searches the registry for the install location, then checks common
    binary subdirectories (bin, Scripts, cmd, etc.).
    """
    install_dir = get_install_location(app_name)
    if not install_dir:
        return False

    # Check for common bin subdirectories
    candidates = []
    for subdir in COMMON_BIN_SUBDIRS:
        full_path = os.path.join(install_dir, subdir)
        if os.path.isdir(full_path):
            candidates.append(full_path)

    # Also check the install directory itself
    if os.path.isdir(install_dir):
        # Check if there are executables directly in the install dir
        exes = [f for f in os.listdir(install_dir)
                if f.endswith((".exe", ".cmd", ".bat"))]
        if exes:
            candidates.insert(0, install_dir)

    if not candidates:
        return False

    # Force absolute paths to avoid PATH injection via relative paths
    abs_candidates = [os.path.abspath(c) for c in candidates]

    # Add the best candidate (first match)
    return add_to_user_path(abs_candidates[0])


# ── CLI Handler ─────────────────────────────────────────────────────

def handle_path(cmd: ParsedCommand):
    """Handle the 'path' command."""
    if not cmd.target:
        # Show current PATH
        print_header("Current PATH Configuration")

        user_path = get_user_path()
        sys_path = get_system_path()

        rows = []
        for p in user_path:
            exists = "✔" if os.path.exists(p) else "✖"
            rows.append(["User", p, exists])
        for p in sys_path:
            exists = "✔" if os.path.exists(p) else "✖"
            rows.append(["System", p, exists])

        table = make_table(
            "PATH Entries",
            [("Scope", "center"), ("Path", "left"), ("Exists", "center")],
            rows,
        )
        console.print(table)
        return

    print_header(f"Configuring PATH for: {cmd.target}")

    if auto_configure_path(cmd.target):
        return

    # If auto-detect failed, ask user for a path
    console.print(warning_panel(
        f"Could not auto-detect the binary directory for [bold]{cmd.target}[/bold].\n"
        "Please provide the full path to add.",
        title="Manual Configuration Needed"
    ))

    try:
        path_input = console.input("[bold cyan]Enter path to add (or 'c' to cancel): [/bold cyan]")
        if path_input.lower() == "c":
            console.print("[yellow]Cancelled.[/yellow]")
            return

        if os.path.isdir(path_input):
            add_to_user_path(path_input)
        else:
            console.print(error_panel(
                f"Directory does not exist: [bold]{path_input}[/bold]",
                title="Invalid Path"
            ))
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled.[/yellow]")
