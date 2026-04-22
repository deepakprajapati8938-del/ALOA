"""
ALOA Disk Inspector — Disk usage analysis and clutter detection.
"""

import os
import psutil
from core.parser import ParsedCommand
from utils.constants import (
    CLUTTER_DIRECTORIES, DISK_WARNING_PERCENT, DISK_CRITICAL_PERCENT,
    LARGE_FILE_SIZE_MB
)
from utils.formatting import (
    console, make_table, info_panel, warning_panel, print_header,
    format_bytes, severity_color, status_icon
)


def get_disk_usage() -> list[dict]:
    """Get usage information for all disk partitions."""
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except (PermissionError, OSError):
            continue
    return disks


# Directories known to be very deep but contain only small files.
# We limit their traversal depth to avoid millions of stat() calls.
_SHALLOW_CLUTTER_DIRS: tuple[str, ...] = (
    "Firefox",
    "Profiles",
)
_MAX_CLUTTER_DEPTH = 2


def scan_clutter() -> list[dict]:
    """Scan known clutter directories and report their sizes.

    For directories that are excessively deep (e.g. Firefox Profiles), we
    cap traversal depth at ``_MAX_CLUTTER_DEPTH`` to keep performance
    acceptable.
    """
    results = []
    for clutter_dir in CLUTTER_DIRECTORIES:
        if not os.path.isdir(clutter_dir):
            continue
        total_size = 0
        file_count = 0

        # Determine if this clutter dir should be depth-limited
        is_shallow = any(marker in clutter_dir for marker in _SHALLOW_CLUTTER_DIRS)
        base_depth = clutter_dir.count(os.sep)

        try:
            for dirpath, dirnames, filenames in os.walk(clutter_dir):
                # Prune traversal beyond max depth for deep directories
                if is_shallow:
                    current_depth = dirpath.count(os.sep) - base_depth
                    if current_depth >= _MAX_CLUTTER_DEPTH:
                        del dirnames[:]  # prevent os.walk from descending further

                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        total_size += os.path.getsize(fp)
                        file_count += 1
                    except (OSError, PermissionError):
                        continue
        except PermissionError:
            continue

        if total_size > 0:
            results.append({
                "path": clutter_dir,
                "size": total_size,
                "file_count": file_count,
            })

    results.sort(key=lambda x: x["size"], reverse=True)
    return results


def find_large_files(root: str = None, threshold_mb: int = None, max_results: int = 15) -> list[dict]:
    """Find files larger than the threshold on the given drive."""
    if root is None:
        root = os.environ.get("SYSTEMDRIVE", "C:") + "\\"
    if threshold_mb is None:
        threshold_mb = LARGE_FILE_SIZE_MB

    threshold_bytes = threshold_mb * 1024 * 1024
    large_files = []

    # Only scan user-accessible directories to avoid permission issues
    scan_dirs = [
        os.path.expanduser("~"),
        os.path.join(root, "Users"),
    ]

    # Subdirectory names (lowercase) that should never be entered
    _SKIP_DIRS = {"windows", "$recycle.bin", "system volume information",
                  "appdata", ".git", ".gradle", ".m2"}

    for scan_dir in scan_dirs:
        if not os.path.isdir(scan_dir):
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(scan_dir):
                # Prune dirnames IN-PLACE so os.walk never descends into
                # skipped subtrees (much faster than checking dirpath after descent)
                dirnames[:] = [
                    d for d in dirnames
                    if d.lower() not in _SKIP_DIRS
                ]

                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        size = os.path.getsize(fp)
                        if size >= threshold_bytes:
                            large_files.append({"path": fp, "size": size})
                    except (OSError, PermissionError):
                        continue

                if len(large_files) >= max_results:
                    break
        except PermissionError:
            continue

    large_files.sort(key=lambda x: x["size"], reverse=True)
    return large_files[:max_results]


# ── CLI Handler ─────────────────────────────────────────────────────

def handle_disk(cmd: ParsedCommand):
    """Handle the 'disk' command — disk usage and clutter analysis."""
    print_header("Disk Usage")

    # Drive overview
    disks = get_disk_usage()
    rows = []
    for d in disks:
        color = severity_color(d["percent"], DISK_WARNING_PERCENT, DISK_CRITICAL_PERCENT)
        bar_len = int(d["percent"] / 5)
        bar = f"[{color}]{'█' * bar_len}{'░' * (20 - bar_len)}[/{color}]"

        if d["percent"] >= DISK_CRITICAL_PERCENT:
            icon = status_icon("critical")
        elif d["percent"] >= DISK_WARNING_PERCENT:
            icon = status_icon("warning")
        else:
            icon = status_icon("good")

        rows.append([
            f"{icon} {d['mountpoint']}",
            d["fstype"],
            format_bytes(d["total"]),
            f"[{color}]{format_bytes(d['used'])}[/{color}]",
            f"[green]{format_bytes(d['free'])}[/green]",
            bar,
            f"[{color}]{d['percent']:.1f}%[/{color}]",
        ])

    table = make_table(
        "Drive Overview",
        [
            ("Drive", "left"), ("Type", "center"),
            ("Total", "right"), ("Used", "right"), ("Free", "right"),
            ("Usage", "left"), ("%", "right"),
        ],
        rows,
    )
    console.print(table)

    # Clutter scan
    console.print()
    print_header("Clutter Analysis")

    clutter = scan_clutter()
    if clutter:
        total_clutter = sum(c["size"] for c in clutter)
        clutter_rows = [
            [
                c["path"],
                format_bytes(c["size"]),
                str(c["file_count"]),
            ]
            for c in clutter[:10]
        ]

        ctable = make_table(
            f"Recoverable Clutter — {format_bytes(total_clutter)} total",
            [("Location", "left"), ("Size", "right"), ("Files", "right")],
            clutter_rows,
        )
        console.print(ctable)
        console.print(f"\n  [bold cyan]Tip:[/bold cyan] Run [cyan]cleanup[/cyan] to clear these files.")
    else:
        console.print(info_panel(
            "No significant clutter detected. Your system is clean! 🎉",
            title="Clutter Scan"
        ))
