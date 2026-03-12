"""
ALOA Unused App Detector — Find applications not used recently.
"""

import os
import time
from datetime import datetime, timedelta
from core.parser import ParsedCommand
from lifecycle.registry import scan_installed_apps
from utils.constants import UNUSED_APP_DAYS_THRESHOLD
from utils.formatting import (
    console, make_table, info_panel, print_header, format_bytes
)


def _get_last_access_time(path: str) -> float:
    """Get the last access time of a file or directory."""
    try:
        return os.path.getatime(path)
    except (OSError, PermissionError):
        return 0


def detect_unused_apps(days_threshold: int = None) -> list[dict]:
    """Detect installed applications that haven't been used recently.

    Checks the last access time of the application's install directory
    and executable files.
    """
    if days_threshold is None:
        days_threshold = UNUSED_APP_DAYS_THRESHOLD

    cutoff_time = time.time() - (days_threshold * 86400)
    # Use cached scan results for performance
    apps = scan_installed_apps()
    unused = []

    for app in apps:
        install_dir = app.install_location
        if not install_dir or not os.path.isdir(install_dir):
            continue

        # Find the most recent access in the install directory
        most_recent = 0
        exe_found = False

        try:
            for item in os.listdir(install_dir):
                full_path = os.path.join(install_dir, item)
                if item.endswith((".exe", ".cmd", ".bat")):
                    exe_found = True
                    access_time = _get_last_access_time(full_path)
                    most_recent = max(most_recent, access_time)
        except (PermissionError, OSError):
            continue

        if not exe_found:
            continue

        if most_recent < cutoff_time and most_recent > 0:
            last_used_dt = datetime.fromtimestamp(most_recent)
            days_ago = (datetime.now() - last_used_dt).days

            size_kb = app.estimated_size_kb or 0

            unused.append({
                "name": app.display_name,
                "version": app.version or "—",
                "last_used": last_used_dt.strftime("%Y-%m-%d"),
                "days_ago": days_ago,
                "size_kb": size_kb,
                "install_location": install_dir,
            })

    # Sort by days since last use (most unused first)
    unused.sort(key=lambda x: x["days_ago"], reverse=True)
    return unused


# ── CLI Handler ─────────────────────────────────────────────────────

def handle_unused(cmd: ParsedCommand):
    """Handle the 'unused' command — detect unused applications."""
    print_header("Unused Application Detection")

    console.print("[cyan]Scanning installed applications...[/cyan]")
    unused = detect_unused_apps()

    if not unused:
        console.print(info_panel(
            "No clearly unused applications detected.\n"
            "All installed apps appear to have been used recently. 🎉",
            title="Unused Apps"
        ))
        return

    total_size = sum(a["size_kb"] for a in unused) * 1024

    rows = [
        [
            a["name"],
            a["version"],
            a["last_used"],
            f"[yellow]{a['days_ago']} days[/yellow]",
            format_bytes(a["size_kb"] * 1024) if a["size_kb"] else "—",
        ]
        for a in unused[:20]
    ]

    table = make_table(
        f"Unused Applications ({len(unused)} found — {format_bytes(total_size)} recoverable)",
        [
            ("Application", "left"), ("Version", "left"),
            ("Last Used", "center"), ("Days Ago", "right"), ("Size", "right"),
        ],
        rows,
    )
    console.print(table)

    console.print(
        f"\n  [bold cyan]Tip:[/bold cyan] Run [cyan]uninstall <app name>[/cyan] "
        f"to deep-uninstall any of these applications."
    )
