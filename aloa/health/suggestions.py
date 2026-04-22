"""
ALOA Suggestion Engine — Generate and optionally execute optimization suggestions.
"""

import os
import shutil
import psutil
from core.parser import ParsedCommand
from health.bottleneck import analyze_bottlenecks
from health.startup_analyzer import get_all_startup_entries
from utils.constants import CLUTTER_DIRECTORIES, is_protected
from utils.formatting import (
    console, make_table, success_panel, warning_panel, info_panel,
    print_header, format_bytes
)


def generate_suggestions() -> list[dict]:
    """Generate ranked optimization suggestions based on system analysis.

    Each suggestion has:
      - priority: int (1 = highest)
      - category: str (RAM / CPU / Disk / Startup)
      - action: str (human-readable suggestion)
      - command: str or None (shell command to execute, if applicable)
      - impact: str (estimated impact description)
      - auto_executable: bool (whether ALOA can execute it automatically)
    """
    suggestions = []
    bottleneck = analyze_bottlenecks()

    # ── RAM Suggestions ─────────────────────────────────────────
    ram_score = bottleneck["scores"].get("RAM", 0)

    if ram_score >= 70:
        # Find memory-hungry processes — skip protected/system ones
        for offender in bottleneck["top_offenders"]:
            if offender["mem_mb"] > 300 and not is_protected(offender["name"]):
                suggestions.append({
                    "priority": 1,
                    "category": "RAM",
                    "action": f"Close {offender['name']} (using {offender['mem_mb']:.0f} MB RAM)",
                    "command": f"taskkill /IM \"{offender['name']}\" /F",
                    "impact": f"Free ~{offender['mem_mb']:.0f} MB of RAM",
                    "auto_executable": True,
                })

    if ram_score >= 50:
        suggestions.append({
            "priority": 3,
            "category": "RAM",
            "action": "Close unnecessary browser tabs (browsers use ~100–500 MB per tab)",
            "command": None,
            "impact": "Could free significant RAM",
            "auto_executable": False,
        })

    # ── CPU Suggestions ─────────────────────────────────────────
    cpu_score = bottleneck["scores"].get("CPU", 0)

    if cpu_score >= 70:
        # Skip protected/system processes even if they spike CPU
        for offender in bottleneck["top_offenders"]:
            if offender["cpu"] > 20 and not is_protected(offender["name"]):
                suggestions.append({
                    "priority": 1,
                    "category": "CPU",
                    "action": f"Stop {offender['name']} (using {offender['cpu']:.1f}% CPU)",
                    "command": f"taskkill /IM \"{offender['name']}\" /F",
                    "impact": f"Free ~{offender['cpu']:.1f}% CPU",
                    "auto_executable": True,
                })

    # ── Disk Suggestions ────────────────────────────────────────
    disk_score = bottleneck["scores"].get("Disk", 0)

    # Calculate clutter size
    total_clutter = 0
    for clutter_dir in CLUTTER_DIRECTORIES:
        if os.path.isdir(clutter_dir):
            try:
                for dirpath, _, filenames in os.walk(clutter_dir):
                    for f in filenames:
                        try:
                            total_clutter += os.path.getsize(os.path.join(dirpath, f))
                        except (OSError, PermissionError):
                            continue
            except PermissionError:
                continue

    if total_clutter > 100 * 1024 * 1024:  # > 100 MB
        suggestions.append({
            "priority": 2 if disk_score >= 70 else 4,
            "category": "Disk",
            "action": f"Clear temp files and caches ({format_bytes(total_clutter)})",
            "command": "__cleanup__",
            "impact": f"Free {format_bytes(total_clutter)} of disk space",
            "auto_executable": True,
        })

    if disk_score >= 80:
        suggestions.append({
            "priority": 2,
            "category": "Disk",
            "action": "Run Windows Disk Cleanup for deeper cleaning",
            "command": "cleanmgr /d C",
            "impact": "Free additional disk space",
            "auto_executable": True,
        })

    # ── Startup Suggestions ─────────────────────────────────────
    startup_entries = get_all_startup_entries()
    high_impact = [e for e in startup_entries if "High" in e.get("impact", "")]

    if high_impact:
        for entry in high_impact[:3]:
            suggestions.append({
                "priority": 3,
                "category": "Startup",
                "action": f"Disable '{entry['name']}' from startup (high impact)",
                "command": None,
                "impact": "Faster boot time",
                "auto_executable": False,
            })

    # Sort by priority
    suggestions.sort(key=lambda x: x["priority"])

    return suggestions


def execute_cleanup():
    """Execute temp file and cache cleanup."""
    total_freed = 0
    cleaned_dirs = 0

    for clutter_dir in CLUTTER_DIRECTORIES:
        if not os.path.isdir(clutter_dir):
            continue

        dir_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(clutter_dir, topdown=False):
                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        size = os.path.getsize(fp)
                        os.remove(fp)
                        dir_size += size
                    except (OSError, PermissionError):
                        continue

                # Try to remove empty directories
                for d in dirnames:
                    try:
                        os.rmdir(os.path.join(dirpath, d))
                    except (OSError, PermissionError):
                        continue

            if dir_size > 0:
                total_freed += dir_size
                cleaned_dirs += 1
                console.print(
                    f"  [green]✔[/green] Cleaned {clutter_dir} "
                    f"— freed {format_bytes(dir_size)}"
                )
        except PermissionError:
            console.print(f"  [yellow]⚠[/yellow] Skipped {clutter_dir} (permission denied)")

    return total_freed, cleaned_dirs


# ── CLI Handlers ────────────────────────────────────────────────────

def handle_suggest(cmd: ParsedCommand):
    """Handle the 'suggest' command — generate optimization suggestions."""
    print_header("Optimization Suggestions")

    console.print("[cyan]Analyzing system for optimization opportunities...[/cyan]\n")

    suggestions = generate_suggestions()

    if not suggestions:
        console.print(info_panel(
            "Your system is running optimally — no suggestions at this time. 🎉",
            title="All Good"
        ))
        return

    rows = [
        [
            str(i + 1),
            s["category"],
            s["action"],
            s["impact"],
            "[green]Yes[/green]" if s["auto_executable"] else "[dim]Manual[/dim]",
        ]
        for i, s in enumerate(suggestions)
    ]

    table = make_table(
        f"Optimization Suggestions ({len(suggestions)} found)",
        [
            ("#", "right"), ("Category", "center"),
            ("Suggestion", "left"), ("Impact", "left"),
            ("Auto", "center"),
        ],
        rows,
    )
    console.print(table)

    # Offer to execute
    executable = [s for s in suggestions if s["auto_executable"]]
    if executable:
        console.print(
            f"\n  [bold cyan]{len(executable)}[/bold cyan] suggestions can be "
            f"executed automatically."
        )
        try:
            choice = console.input(
                "\n[bold cyan]Execute a suggestion? Enter # (or 'all' / 'c' to cancel): [/bold cyan]"
            )

            if choice.lower() == "c":
                return

            if choice.lower() == "all":
                for s in executable:
                    _execute_suggestion(s)
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(suggestions) and suggestions[idx]["auto_executable"]:
                    _execute_suggestion(suggestions[idx])
                else:
                    console.print("[yellow]Invalid or non-executable selection.[/yellow]")

        except (ValueError, KeyboardInterrupt):
            console.print("[yellow]Cancelled.[/yellow]")


def _execute_suggestion(suggestion: dict):
    """Execute a single suggestion."""
    console.print(f"\n[cyan]Executing: {suggestion['action']}[/cyan]")

    if suggestion["command"] == "__cleanup__":
        freed, dirs = execute_cleanup()
        console.print(success_panel(
            f"Cleaned {dirs} directories, freed {format_bytes(freed)}.",
            title="Cleanup Complete"
        ))
    elif suggestion["command"]:
        import subprocess
        import shlex
        try:
            try:
                cmd_parts = shlex.split(suggestion["command"], posix=False)
            except ValueError:
                cmd_parts = suggestion["command"].split()
            subprocess.run(cmd_parts, shell=False, timeout=30, capture_output=True)
            console.print(f"[green]  ✔ Done.[/green]")
        except subprocess.TimeoutExpired:
            console.print(f"[yellow]  ⚠ Command timed out.[/yellow]")
        except Exception as e:
            console.print(f"[red]  ✖ Failed: {e}[/red]")


def handle_cleanup(cmd: ParsedCommand):
    """Handle the 'cleanup' command — clean temp files and caches."""
    print_header("System Cleanup")

    console.print("[cyan]Cleaning temp files and caches...[/cyan]\n")

    try:
        confirm = console.input(
            "[bold yellow]This will delete temp files and caches. Proceed? (yes/no): [/bold yellow]"
        )
        if confirm.lower() not in ("yes", "y"):
            console.print("[yellow]Cleanup cancelled.[/yellow]")
            return
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    freed, dirs = execute_cleanup()

    console.print()
    console.print(success_panel(
        f"Cleanup complete!\n\n"
        f"  Directories cleaned: [bold]{dirs}[/bold]\n"
        f"  Space freed:         [bold green]{format_bytes(freed)}[/bold green]",
        title="Cleanup Complete"
    ))
