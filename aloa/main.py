"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║                       T H E   A L O A                            ║
║              Autonomous Laptop Operating Agent                   ║
║                                                                  ║
║              Phase 1 — System Control Foundation                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

Entry point for the ALOA interactive CLI.
"""

import sys
import os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
# Ensure UTF-8 output for Rich console icons, especially on Windows cmd/powershell
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from core.agent import Agent
from core.privileges import is_admin

console = Console()

BANNER = r"""
[bold cyan]
     █████╗  ██╗      ██████╗   █████╗ 
    ██╔══██╗ ██║     ██╔═══██╗ ██╔══██╗
    ███████║ ██║     ██║   ██║ ███████║
    ██╔══██║ ██║     ██║   ██║ ██╔══██║
    ██║  ██║ ███████╗╚██████╔╝ ██║  ██║
    ╚═╝  ╚═╝ ╚══════╝ ╚═════╝  ╚═╝  ╚═╝
[/bold cyan]
[dim]    Autonomous Laptop Operating Agent[/dim]
[dim]    Phase 1 — System Control Foundation[/dim]
"""


def print_banner():
    """Print the ALOA startup banner."""
    console.print(BANNER)

    admin_status = (
        "[green]✔ Running as Administrator[/green]"
        if is_admin()
        else "[yellow]⚠ Running without Admin privileges (some features limited)[/yellow]"
    )

    console.print(Panel(
        f"  {admin_status}\n\n"
        "  [bold]Commands:[/bold]\n"
        "    [cyan]install <app>[/cyan]    — Install software silently\n"
        "    [cyan]uninstall <app>[/cyan]  — Deep uninstall with full cleanup\n"
        "    [cyan]verify <app>[/cyan]     — Check if an app is properly installed\n"
        "    [cyan]health[/cyan]           — Full system health overview\n"
        "    [cyan]diagnose[/cyan]         — Find out why your system is slow\n"
        "    [cyan]suggest[/cyan]          — Get optimization suggestions\n"
        "    [cyan]help[/cyan]             — See all available commands\n",
        title="[bold magenta]Welcome to ALOA[/bold magenta]",
        border_style="cyan",
        box=box.DOUBLE,
    ))
    console.print()


def main():
    """Main REPL loop for ALOA."""
    print_banner()

    agent = Agent()

    while True:
        try:
            user_input = console.input("[bold magenta]ALOA ❯ [/bold magenta]").strip()

            if not user_input:
                continue

            agent.execute(user_input)
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit ALOA.[/yellow]")

        except SystemExit:
            break

        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}")
            console.print("[dim]If this persists, please report the issue.[/dim]\n")


if __name__ == "__main__":
    main()
