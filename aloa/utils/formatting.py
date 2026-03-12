"""
ALOA Formatting Utilities — Rich-based pretty output for all modules.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich import box

console = Console()


# ── Status Helpers ──────────────────────────────────────────────────

def status_icon(level: str) -> str:
    """Return a colored status icon for a given level."""
    icons = {
        "good": "[bold green]✔[/bold green]",
        "ok": "[green]●[/green]",
        "warning": "[yellow]⚠[/yellow]",
        "critical": "[bold red]✖[/bold red]",
        "info": "[cyan]ℹ[/cyan]",
    }
    return icons.get(level, "[white]•[/white]")


def severity_color(percent: float, warn: float = 75, crit: float = 90) -> str:
    """Return a Rich color string based on percentage thresholds."""
    if percent >= crit:
        return "bold red"
    elif percent >= warn:
        return "yellow"
    return "green"


# ── Tables ──────────────────────────────────────────────────────────

def make_table(title: str, columns: list[tuple[str, str]], rows: list[list[str]],
               box_style=box.ROUNDED) -> Table:
    """Create a Rich Table with the given columns and rows.

    columns: list of (header, justify) tuples
    rows:    list of rows, each row is a list of strings
    """
    table = Table(title=title, box=box_style, show_lines=True,
                  title_style="bold cyan", header_style="bold magenta")
    for header, justify in columns:
        table.add_column(header, justify=justify)
    for row in rows:
        table.add_row(*row)
    return table


# ── Panels ──────────────────────────────────────────────────────────

def info_panel(content: str, title: str = "Info", border_style: str = "cyan") -> Panel:
    """Create an info panel."""
    return Panel(content, title=title, border_style=border_style, box=box.ROUNDED)


def warning_panel(content: str, title: str = "Warning") -> Panel:
    """Create a warning panel."""
    return Panel(content, title=f"⚠ {title}", border_style="yellow", box=box.HEAVY)


def error_panel(content: str, title: str = "Error") -> Panel:
    """Create an error panel."""
    return Panel(content, title=f"✖ {title}", border_style="red", box=box.DOUBLE)


def success_panel(content: str, title: str = "Success") -> Panel:
    """Create a success panel."""
    return Panel(content, title=f"✔ {title}", border_style="green", box=box.ROUNDED)


# ── Progress ────────────────────────────────────────────────────────

def spinner_progress(description: str = "Working...") -> Progress:
    """Create a spinner-style progress bar."""
    return Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )


# ── Trees ───────────────────────────────────────────────────────────

def make_tree(label: str, items: list[str], style: str = "cyan") -> Tree:
    """Create a simple Rich Tree."""
    tree = Tree(f"[bold {style}]{label}[/bold {style}]")
    for item in items:
        tree.add(item)
    return tree


# ── Helpers ─────────────────────────────────────────────────────────

def format_bytes(num_bytes: int) -> str:
    """Human-readable byte size (e.g., 3.2 GB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def print_header(text: str):
    """Print a styled section header."""
    console.print()
    console.print(f"[bold cyan]━━━ {text} ━━━[/bold cyan]")
    console.print()


def print_divider():
    """Print a thin divider line."""
    console.print("[dim]─" * 60 + "[/dim]")
