"""
ALOA Bottleneck Finder — Composite analysis to identify performance bottlenecks.
"""

import psutil
from core.parser import ParsedCommand
from utils.constants import (
    RAM_WARNING_PERCENT, RAM_CRITICAL_PERCENT,
    CPU_WARNING_PERCENT, CPU_CRITICAL_PERCENT,
    DISK_WARNING_PERCENT, DISK_CRITICAL_PERCENT,
    is_protected,
)
from utils.formatting import (
    console, make_table, info_panel, warning_panel, error_panel,
    print_header, format_bytes, severity_color, status_icon
)


def analyze_bottlenecks() -> dict:
    """Perform a composite performance analysis.

    Returns a dict with:
      - scores: dict of category → score (0–100, higher = worse)
      - primary_bottleneck: str (the category with the highest score)
      - explanation: str (human-readable explanation)
      - details: list of detail strings
      - top_offenders: list of (process_name, resource, usage) tuples
    """
    results = {
        "scores": {},
        "primary_bottleneck": None,
        "explanation": "",
        "details": [],
        "top_offenders": [],
    }

    # ── RAM Analysis ────────────────────────────────────────────
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    ram_score = mem.percent

    if swap.percent > 50:
        ram_score = min(100, ram_score + 10)  # Penalty for heavy swap usage

    results["scores"]["RAM"] = ram_score

    if ram_score >= RAM_CRITICAL_PERCENT:
        results["details"].append(
            f"RAM is critically high at {mem.percent:.1f}% "
            f"({format_bytes(mem.used)} / {format_bytes(mem.total)})"
        )

    # ── CPU Analysis ────────────────────────────────────────────
    cpu_percent = psutil.cpu_percent(interval=1.5)
    results["scores"]["CPU"] = cpu_percent

    if cpu_percent >= CPU_CRITICAL_PERCENT:
        results["details"].append(f"CPU is critically high at {cpu_percent:.1f}%")

    # ── Disk I/O Analysis ───────────────────────────────────────
    disk_io = psutil.disk_io_counters()
    # Use disk usage of the system drive as a base score
    try:
        sys_drive_path = __import__("os").environ.get("SYSTEMDRIVE", "C:") + "\\"
        if not __import__("os").path.exists(sys_drive_path):
            sys_drive_path = "C:\\"
        sys_drive = psutil.disk_usage(sys_drive_path)
        disk_score = sys_drive.percent
    except Exception:
        disk_score = 0

    results["scores"]["Disk"] = disk_score

    if disk_score >= DISK_CRITICAL_PERCENT:
        results["details"].append(
            f"System drive is {disk_score:.1f}% full — "
            f"only {format_bytes(sys_drive.free)} free"
        )

    # ── Swap Pressure ───────────────────────────────────────────
    swap_score = swap.percent
    results["scores"]["Swap"] = swap_score

    if swap_score > 60:
        results["details"].append(
            f"Swap usage is high at {swap.percent:.1f}% "
            f"({format_bytes(swap.used)} / {format_bytes(swap.total)}). "
            "System may be paging heavily."
        )

    # ── Find Primary Bottleneck ─────────────────────────────────
    if results["scores"]:
        primary = max(results["scores"], key=results["scores"].get)
        primary_score = results["scores"][primary]
        results["primary_bottleneck"] = primary

        # Generate human-readable explanation
        if primary_score < 60:
            results["explanation"] = (
                "Your system is running well — no significant bottlenecks detected."
            )
        else:
            results["explanation"] = _generate_explanation(primary, results)

    # ── Find Top Offenders ──────────────────────────────────────
    for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
        try:
            info = proc.info
            if info["memory_info"] is None:
                continue
            # Never flag essential / system processes as offenders
            if is_protected(info["name"] or ""):
                continue
            mem_mb = info["memory_info"].rss / (1024 * 1024)
            cpu = info["cpu_percent"] or 0

            if mem_mb > 200 or cpu > 10:
                results["top_offenders"].append({
                    "name": info["name"],
                    "pid": info["pid"],
                    "mem_mb": mem_mb,
                    "cpu": cpu,
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    results["top_offenders"].sort(
        key=lambda x: x["mem_mb"] + x["cpu"] * 10, reverse=True
    )
    results["top_offenders"] = results["top_offenders"][:5]

    return results


def _generate_explanation(primary: str, results: dict) -> str:
    """Generate a clear English explanation for the bottleneck."""
    score = results["scores"][primary]

    explanations = {
        "RAM": (
            f"Your laptop is slow because RAM is at {score:.0f}%. "
            "There isn't enough free memory, so the system is likely "
            "swapping data to disk, which is much slower."
        ),
        "CPU": (
            f"Your laptop is slow because the CPU is running at {score:.0f}%. "
            "One or more processes are consuming excessive processing power."
        ),
        "Disk": (
            f"Your system drive is {score:.0f}% full. "
            "Low disk space causes slowdowns because the OS needs free space "
            "for virtual memory, temp files, and caching."
        ),
        "Swap": (
            f"Your system is heavily using swap/page file ({score:.0f}%). "
            "This means real RAM is exhausted and the OS is using the much "
            "slower disk as memory, causing significant performance degradation."
        ),
    }

    base = explanations.get(primary, f"{primary} is the primary bottleneck at {score:.0f}%.")

    # Add top offender context
    if results["top_offenders"]:
        top = results["top_offenders"][0]
        if primary == "RAM":
            base += f"\n\nBiggest offender: {top['name']} is using {top['mem_mb']:.0f} MB of RAM."
        elif primary == "CPU":
            base += f"\n\nBiggest offender: {top['name']} is using {top['cpu']:.1f}% CPU."

    return base


# ── CLI Handler ─────────────────────────────────────────────────────

def handle_diagnose(cmd: ParsedCommand):
    """Handle the 'diagnose' command — identify why the system is slow."""
    print_header("System Diagnosis")

    console.print("[cyan]Analyzing system performance...[/cyan]\n")

    results = analyze_bottlenecks()

    # Scores overview
    score_rows = []
    for category, score in sorted(results["scores"].items(), key=lambda x: x[1], reverse=True):
        color = severity_color(score)
        bar_len = int(score / 5)
        bar = f"[{color}]{'█' * bar_len}{'░' * (20 - bar_len)}[/{color}]"

        if score >= 90:
            icon = status_icon("critical")
        elif score >= 70:
            icon = status_icon("warning")
        else:
            icon = status_icon("good")

        score_rows.append([f"{icon} {category}", bar, f"[{color}]{score:.1f}%[/{color}]"])

    table = make_table(
        "Performance Scores (higher = worse)",
        [("Resource", "left"), ("Pressure", "left"), ("Score", "right")],
        score_rows,
    )
    console.print(table)

    # Explanation
    console.print()
    if results["scores"].get(results["primary_bottleneck"], 0) >= 70:
        console.print(error_panel(
            f"[bold]Primary Bottleneck: {results['primary_bottleneck']}[/bold]\n\n"
            f"{results['explanation']}",
            title="Diagnosis"
        ))
    else:
        console.print(info_panel(
            results["explanation"],
            title="Diagnosis",
            border_style="green"
        ))

    # Top offenders
    if results["top_offenders"]:
        console.print()
        offender_rows = [
            [
                str(o["pid"]),
                o["name"],
                f"{o['mem_mb']:.0f} MB",
                f"{o['cpu']:.1f}%",
            ]
            for o in results["top_offenders"]
        ]

        otable = make_table(
            "Top Resource Consumers",
            [("PID", "right"), ("Process", "left"), ("RAM", "right"), ("CPU", "right")],
            offender_rows,
        )
        console.print(otable)

    # Hint
    console.print(
        f"\n  [bold cyan]Tip:[/bold cyan] Run [cyan]suggest[/cyan] "
        f"to get actionable optimization suggestions."
    )
