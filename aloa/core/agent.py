"""
ALOA Agent — Central orchestrator that routes parsed commands to handlers.
"""

from core.parser import parse, ParsedCommand
from utils.formatting import console, error_panel, info_panel


class Agent:
    """The central ALOA agent — maps intents to handler functions."""

    def __init__(self):
        self._handlers: dict[str, callable] = {}
        self._register_all()

    # ── Handler Registration ────────────────────────────────────────

    def _register_all(self):
        """Register all command handlers from lifecycle and health modules."""

        # ── Lifecycle handlers ──
        from lifecycle.installer import handle_install, handle_search
        from lifecycle.uninstaller import handle_uninstall
        from lifecycle.verifier import handle_verify
        from lifecycle.path_config import handle_path

        self._handlers["install"] = handle_install
        self._handlers["uninstall"] = handle_uninstall
        self._handlers["search"] = handle_search
        self._handlers["verify"] = handle_verify
        self._handlers["path"] = handle_path

        # ── Health handlers ──
        from health.ram_monitor import handle_ram
        from health.cpu_monitor import handle_cpu
        from health.disk_inspector import handle_disk
        from health.startup_analyzer import handle_startup
        from health.unused_apps import handle_unused
        from health.bottleneck import handle_diagnose
        from health.suggestions import handle_suggest, handle_cleanup

        self._handlers["ram"] = handle_ram
        self._handlers["cpu"] = handle_cpu
        self._handlers["disk"] = handle_disk
        self._handlers["startup"] = handle_startup
        self._handlers["unused"] = handle_unused
        self._handlers["diagnose"] = handle_diagnose
        self._handlers["suggest"] = handle_suggest
        self._handlers["cleanup"] = handle_cleanup

        # ── Health overview ──
        self._handlers["health"] = self._handle_health_overview

        # ── Meta handlers ──
        self._handlers["help"] = self._handle_help
        self._handlers["exit"] = self._handle_exit

    # ── Execution ───────────────────────────────────────────────────

    def execute(self, user_input: str):
        """Parse and execute a user command."""
        cmd = parse(user_input)

        handler = self._handlers.get(cmd.intent)
        if handler:
            handler(cmd)
        else:
            console.print(error_panel(
                f"I didn't understand: [bold]{cmd.raw}[/bold]\n\n"
                "Type [cyan]help[/cyan] to see available commands.",
                title="Unknown Command"
            ))

    # ── Built-in Handlers ───────────────────────────────────────────

    def _handle_health_overview(self, cmd: ParsedCommand):
        """Run a full system health overview: RAM + CPU + Disk."""
        from health.ram_monitor import handle_ram
        from health.cpu_monitor import handle_cpu
        from health.disk_inspector import handle_disk

        console.print(info_panel(
            "[bold]Running full system health scan...[/bold]",
            title="System Health Overview"
        ))

        handle_ram(cmd)
        handle_cpu(cmd)
        handle_disk(cmd)

    def _handle_help(self, cmd: ParsedCommand):
        """Show available commands."""
        from utils.formatting import make_table

        rows = [
            ["install <app>", "Install an application silently via winget"],
            ["uninstall <app>", "Deep uninstall — remove app + all traces"],
            ["search <app>", "Search for an application in winget"],
            ["verify <app>", "Verify an app is installed & on PATH"],
            ["path <app>", "Auto-configure PATH for an application"],
            ["", ""],
            ["health", "Full system health overview (RAM + CPU + Disk)"],
            ["ram", "Show RAM usage and top memory consumers"],
            ["cpu", "Show CPU usage and detect spikes"],
            ["disk", "Show disk usage and clutter analysis"],
            ["startup", "Analyze startup programs and their impact"],
            ["unused", "Detect applications not used recently"],
            ["diagnose", "Identify why your system is slow"],
            ["suggest", "Get optimization suggestions"],
            ["cleanup", "Clean temp files and caches"],
            ["", ""],
            ["help", "Show this help message"],
            ["exit", "Exit ALOA"],
        ]

        table = make_table(
            "ALOA Commands",
            [("Command", "left"), ("Description", "left")],
            rows,
        )
        console.print(table)

    def _handle_exit(self, cmd: ParsedCommand):
        """Exit the ALOA agent."""
        from utils.formatting import success_panel
        console.print(success_panel(
            "[bold]Goodbye! ALOA signing off.[/bold] 👋",
            title="Exit"
        ))
        raise SystemExit(0)
