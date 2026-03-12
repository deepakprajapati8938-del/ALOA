"""
ALOA CPU Monitor — CPU usage analysis and spike detection.
"""

import time
import psutil
from core.parser import ParsedCommand
from utils.constants import CPU_WARNING_PERCENT, CPU_CRITICAL_PERCENT, CPU_SPIKE_DURATION_SECONDS
from utils.formatting import (
    console, make_table, info_panel, warning_panel, print_header,
    severity_color, status_icon
)


def get_cpu_info() -> dict:
    """Get comprehensive CPU information."""
    cpu_percent = psutil.cpu_percent(interval=1)
    per_cpu = psutil.cpu_percent(interval=0.5, percpu=True)
    freq = psutil.cpu_freq()

    return {
        "overall_percent": cpu_percent,
        "per_cpu": per_cpu,
        "core_count": psutil.cpu_count(logical=False) or 0,
        "thread_count": psutil.cpu_count(logical=True) or 0,
        "freq_current": freq.current if freq else 0,
        "freq_max": freq.max if freq else 0,
    }


def detect_cpu_spike(duration: int = None) -> bool:
    """Monitor CPU for sustained spikes.

    Returns True if a spike is detected (>80% for >5s sustained).
    """
    if duration is None:
        duration = CPU_SPIKE_DURATION_SECONDS

    console.print(f"[cyan]Monitoring CPU for {duration} seconds...[/cyan]")
    spike_start = None

    for _ in range(duration):
        usage = psutil.cpu_percent(interval=1)
        if usage > CPU_CRITICAL_PERCENT:
            if spike_start is None:
                spike_start = time.time()
            elif time.time() - spike_start >= 3:
                return True
        else:
            spike_start = None

    return False


def get_top_cpu_processes(n: int = 10) -> list[dict]:
    """Get the top N processes by CPU usage."""
    # First call to initialize CPU percent tracking
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            proc.cpu_percent()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    time.sleep(1)  # Wait for measurement interval

    processes = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            cpu = proc.cpu_percent()
            if cpu > 0:
                processes.append({
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "cpu_percent": cpu,
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return processes[:n]


# ── CLI Handler ─────────────────────────────────────────────────────

def handle_cpu(cmd: ParsedCommand):
    """Handle the 'cpu' command — display CPU usage and top consumers."""
    print_header("CPU Usage")

    info = get_cpu_info()
    color = severity_color(info["overall_percent"], CPU_WARNING_PERCENT, CPU_CRITICAL_PERCENT)

    # Status level
    if info["overall_percent"] >= CPU_CRITICAL_PERCENT:
        icon = status_icon("critical")
        level = "CRITICAL"
    elif info["overall_percent"] >= CPU_WARNING_PERCENT:
        icon = status_icon("warning")
        level = "WARNING"
    else:
        icon = status_icon("good")
        level = "HEALTHY"

    # Summary
    summary = (
        f"{icon} CPU Status: [{color}]{level}[/{color}]\n\n"
        f"  Overall:   [{color}]{info['overall_percent']:.1f}%[/{color}]\n"
        f"  Cores:     [bold]{info['core_count']}[/bold] physical, "
        f"[bold]{info['thread_count']}[/bold] logical\n"
    )

    if info["freq_current"]:
        summary += (
            f"  Frequency: [bold]{info['freq_current']:.0f} MHz[/bold]"
        )
        if info["freq_max"]:
            summary += f" / {info['freq_max']:.0f} MHz max"

    console.print(info_panel(summary, title="CPU Overview", border_style=color))

    # Per-core usage
    if info["per_cpu"]:
        core_rows = []
        for i, usage in enumerate(info["per_cpu"]):
            c = severity_color(usage, CPU_WARNING_PERCENT, CPU_CRITICAL_PERCENT)
            bar_len = int(usage / 5)  # 20-char bar for 100%
            bar = f"[{c}]{'█' * bar_len}{'░' * (20 - bar_len)}[/{c}]"
            core_rows.append([f"Core {i}", bar, f"[{c}]{usage:.1f}%[/{c}]"])

        table = make_table(
            "Per-Core Usage",
            [("Core", "left"), ("Load", "left"), ("%", "right")],
            core_rows,
        )
        console.print(table)

    # Top CPU consumers
    top_procs = get_top_cpu_processes(10)
    if top_procs:
        rows = [
            [
                str(p["pid"]),
                p["name"],
                f"[{severity_color(p['cpu_percent'], 10, 30)}]"
                f"{p['cpu_percent']:.1f}%"
                f"[/{severity_color(p['cpu_percent'], 10, 30)}]",
            ]
            for p in top_procs
        ]

        table = make_table(
            "Top CPU Consumers",
            [("PID", "right"), ("Process", "left"), ("CPU %", "right")],
            rows,
        )
        console.print(table)

    # Spike detection
    if info["overall_percent"] >= CPU_WARNING_PERCENT:
        console.print(warning_panel(
            f"CPU is at [{color}]{info['overall_percent']:.1f}%[/{color}].\n"
            "Consider closing resource-heavy processes.",
            title="High CPU Usage"
        ))
