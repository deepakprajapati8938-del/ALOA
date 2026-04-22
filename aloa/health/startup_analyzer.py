"""
ALOA Startup Analyzer — Analyze startup programs and their impact.
"""

import os
import winreg
import subprocess
import psutil
from core.parser import ParsedCommand
from utils.constants import (
    REG_STARTUP_PATHS, STARTUP_FOLDER,
    STARTUP_HIGH_IMPACT_CPU, STARTUP_HIGH_IMPACT_MEM_MB,
    STARTUP_MEDIUM_IMPACT_CPU, STARTUP_MEDIUM_IMPACT_MEM_MB,
)
from utils.formatting import (
    console, make_table, info_panel, warning_panel, print_header,
    format_bytes, status_icon
)


def _get_registry_startups() -> list[dict]:
    """Read startup entries from registry Run keys."""
    entries = []
    hive_map = {
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
    }

    for hive_name, reg_path in REG_STARTUP_PATHS:
        hive = hive_map.get(hive_name)
        if not hive:
            continue
        try:
            with winreg.OpenKey(hive, reg_path, 0, winreg.KEY_READ) as key:
                num_values = winreg.QueryInfoKey(key)[1]
                for i in range(num_values):
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        entries.append({
                            "name": name,
                            "command": value,
                            "source": f"Registry ({hive_name}\\{reg_path.split(chr(92))[-1]})",
                            "scope": "User" if hive_name == "HKCU" else "System",
                        })
                    except OSError:
                        continue
        except OSError:
            continue

    return entries


def _get_folder_startups() -> list[dict]:
    """Read startup entries from the Startup folder."""
    entries = []
    if os.path.isdir(STARTUP_FOLDER):
        for item in os.listdir(STARTUP_FOLDER):
            full_path = os.path.join(STARTUP_FOLDER, item)
            entries.append({
                "name": item,
                "command": full_path,
                "source": "Startup Folder",
                "scope": "User",
            })
    return entries


def _get_scheduled_tasks() -> list[dict]:
    """Read scheduled tasks that run at boot/login."""
    entries = []
    # Keywords indicating a task fires at boot or logon
    _BOOT_KEYWORDS = {"logon", "boot", "startup", "at log on"}
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "CSV", "/v"],
            capture_output=True, text=True, timeout=15,
            # Suppress the console window that would otherwise flash briefly
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            return entries

        # Parse CSV header
        headers = [h.strip('"') for h in lines[0].split('","')]

        # Find relevant column indices
        name_idx = next((i for i, h in enumerate(headers) if "TaskName" in h), None)
        trigger_idx = next((i for i, h in enumerate(headers) if "Trigger" in h or "Start" in h), None)
        status_idx = next((i for i, h in enumerate(headers) if "Status" in h), None)

        for line in lines[1:]:
            cols = [c.strip('"') for c in line.split('","')]
            if name_idx is not None and name_idx < len(cols):
                task_name = cols[name_idx]
                trigger = cols[trigger_idx].lower() if trigger_idx and trigger_idx < len(cols) else ""

                # Only include boot/login related tasks — use set membership for speed
                if any(kw in trigger for kw in _BOOT_KEYWORDS):
                    entries.append({
                        "name": task_name.split("\\")[-1],
                        "command": task_name,
                        "source": "Scheduled Task",
                        "scope": "System",
                    })

    except (subprocess.TimeoutExpired, Exception):
        pass

    return entries


def _classify_impact(name: str, running_processes: dict[str, dict]) -> str:
    """Classify a startup program's impact based on known process behavior."""
    name_lower = name.lower()

    # Check the pre-computed process map for current resource usage
    # We check if the startup name is part of any running process name
    for proc_name, info in running_processes.items():
        if name_lower in proc_name:
            mem_mb = info["mem_mb"]
            if mem_mb >= STARTUP_HIGH_IMPACT_MEM_MB:
                return "🔴 High"
            elif mem_mb >= STARTUP_MEDIUM_IMPACT_MEM_MB:
                return "🟡 Medium"
            else:
                return "🟢 Low"

    # Default classification for non-running items
    high_impact_keywords = ["update", "antivirus", "defender", "onedrive", "teams", "discord", "spotify", "steam"]
    medium_impact_keywords = ["helper", "agent", "service", "tray", "notify"]

    for keyword in high_impact_keywords:
        if keyword in name_lower:
            return "🟡 Medium"

    for keyword in medium_impact_keywords:
        if keyword in name_lower:
            return "🟢 Low"

    return "🔵 Unknown"


def get_all_startup_entries() -> list[dict]:
    """Get all startup entries from all sources."""
    entries = []
    entries.extend(_get_registry_startups())
    entries.extend(_get_folder_startups())
    entries.extend(_get_scheduled_tasks())

    # Performance optimization: build a map of running processes once
    running_processes = {}
    for proc in psutil.process_iter(["name", "memory_info"]):
        try:
            name = proc.info["name"].lower()
            mem = proc.info["memory_info"].rss / (1024 * 1024) if proc.info["memory_info"] else 0
            # If multiple processes have same name, track the max usage
            if name not in running_processes or mem > running_processes[name]["mem_mb"]:
                running_processes[name] = {"mem_mb": mem}
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Classify impact using the map
    for entry in entries:
        entry["impact"] = _classify_impact(entry["name"], running_processes)

    return entries


# ── CLI Handler ─────────────────────────────────────────────────────

def handle_startup(cmd: ParsedCommand):
    """Handle the 'startup' command — analyze startup programs."""
    print_header("Startup Program Analysis")

    entries = get_all_startup_entries()

    if not entries:
        console.print(info_panel(
            "No startup programs detected.",
            title="Startup Analysis"
        ))
        return

    # Sort by impact (High first)
    impact_order = {"🔴 High": 0, "🟡 Medium": 1, "🟢 Low": 2, "🔵 Unknown": 3}
    entries.sort(key=lambda x: impact_order.get(x["impact"], 99))

    rows = [
        [
            e["name"],
            e["source"],
            e["scope"],
            e["impact"],
        ]
        for e in entries
    ]

    table = make_table(
        f"Startup Programs ({len(entries)} total)",
        [("Name", "left"), ("Source", "left"), ("Scope", "center"), ("Impact", "center")],
        rows,
    )
    console.print(table)

    # Count high-impact items
    high_count = sum(1 for e in entries if "High" in e["impact"])
    medium_count = sum(1 for e in entries if "Medium" in e["impact"])

    if high_count > 0:
        console.print(warning_panel(
            f"[bold]{high_count}[/bold] high-impact and [bold]{medium_count}[/bold] "
            f"medium-impact programs at startup.\n"
            "Consider disabling unnecessary startup programs to improve boot time.\n\n"
            "[cyan]Tip:[/cyan] Use Task Manager (Ctrl+Shift+Esc → Startup) to disable items.",
            title=f"{high_count + medium_count} Impact Items Found"
        ))
