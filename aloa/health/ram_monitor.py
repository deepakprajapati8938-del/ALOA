"""
ALOA RAM Monitor — Real-time memory usage analysis.
"""

import psutil
from core.parser import ParsedCommand
from utils.constants import RAM_WARNING_PERCENT, RAM_CRITICAL_PERCENT, is_protected
from utils.formatting import (
    console, make_table, info_panel, print_header,
    format_bytes, severity_color, status_icon
)


def get_ram_info() -> dict:
    """Get comprehensive RAM usage information."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "percent": mem.percent,
        "swap_total": swap.total,
        "swap_used": swap.used,
        "swap_percent": swap.percent,
    }


def get_top_memory_processes(n: int = 10) -> list[dict]:
    """Get the top N non-system processes by memory usage."""
    processes = []
    for proc in psutil.process_iter(["pid", "name", "memory_info", "memory_percent"]):
        try:
            info = proc.info
            if info["memory_info"] is None:
                continue
            # Skip essential Windows/system/security processes
            if is_protected(info["name"] or ""):
                continue
            processes.append({
                "pid": info["pid"],
                "name": info["name"],
                "rss": info["memory_info"].rss,
                "percent": info["memory_percent"] or 0,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda x: x["rss"], reverse=True)
    return processes[:n]


# ── CLI Handler ─────────────────────────────────────────────────────

def handle_ram(cmd: ParsedCommand):
    """Handle the 'ram' command — display RAM usage and top consumers."""
    print_header("RAM Usage")

    info = get_ram_info()
    color = severity_color(info["percent"], RAM_WARNING_PERCENT, RAM_CRITICAL_PERCENT)

    # Summary Panel
    if info["percent"] >= RAM_CRITICAL_PERCENT:
        icon = status_icon("critical")
        level = "CRITICAL"
    elif info["percent"] >= RAM_WARNING_PERCENT:
        icon = status_icon("warning")
        level = "WARNING"
    else:
        icon = status_icon("good")
        level = "HEALTHY"

    summary = (
        f"{icon} RAM Status: [{color}]{level}[/{color}]\n\n"
        f"  Total:     [bold]{format_bytes(info['total'])}[/bold]\n"
        f"  Used:      [{color}]{format_bytes(info['used'])}[/{color}] "
        f"([{color}]{info['percent']:.1f}%[/{color}])\n"
        f"  Available: [green]{format_bytes(info['available'])}[/green]\n"
    )

    if info["swap_total"] > 0:
        swap_color = severity_color(info["swap_percent"])
        summary += (
            f"\n  Swap Used: [{swap_color}]{format_bytes(info['swap_used'])}[/{swap_color}] "
            f"/ {format_bytes(info['swap_total'])} "
            f"([{swap_color}]{info['swap_percent']:.1f}%[/{swap_color}])"
        )

    console.print(info_panel(summary, title="Memory Overview", border_style=color))

    # Top memory consumers
    top_procs = get_top_memory_processes(10)
    rows = [
        [
            str(p["pid"]),
            p["name"],
            format_bytes(p["rss"]),
            f"[{severity_color(p['percent'], 5, 15)}]{p['percent']:.1f}%[/{severity_color(p['percent'], 5, 15)}]",
        ]
        for p in top_procs
    ]

    table = make_table(
        "Top Memory Consumers",
        [("PID", "right"), ("Process", "left"), ("Memory", "right"), ("% RAM", "right")],
        rows,
    )
    console.print(table)
