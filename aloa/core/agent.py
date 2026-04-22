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

        # ── Smart & Generic handlers ──
        from core.smart_executor import handle_smart_task
        self._handlers["smart_task"] = handle_smart_task
        self._handlers["git"] = handle_smart_task
        self._handlers["file"] = handle_smart_task
        self._handlers["task"] = handle_smart_task
        self._handlers["system_cmd"] = handle_smart_task

        # ── Meta handlers ──
        self._handlers["help"] = self._handle_help
        self._handlers["exit"] = self._handle_exit

    # ── Execution ───────────────────────────────────────────────────

    def execute(self, user_input: str):
        """Classify user input and route to query or action path."""
        # Fast path for meta commands
        stripped = user_input.strip().lower()
        if stripped in ["exit", "quit", "bye"]:
            self._handle_exit(None)
            return
        if stripped in ["help", "?", "commands"]:
            self._handle_help(None)
            return

        from llm.planner import classify_and_plan, interpret_output, generate_action_plan
        from utils.shell import capture_shell_output
        from utils.cache import answer_cache, normalize_key
        from core.smart_executor import extract_commands, handle_llm_result
        from rich.panel import Panel
        from rich.status import Status

        # ── Phase 1: Classify (instant for known patterns) ───────────
        plan = classify_and_plan(user_input)
        ttl  = plan.get("_ttl", 30)

        # ── Direct answer (no commands needed) ───────────────────────
        if plan.get("direct_answer"):
            console.print(Panel(
                f"[bold green]{plan['direct_answer']}[/bold green]",
                title="[bold magenta]ALOA[/bold magenta]",
                border_style="green",
            ))
            return

        # ── Query path (read-only, auto-execute) ─────────────────────
        if plan.get("type") == "query" and plan.get("safe"):
            commands = plan.get("commands", [])
            if not commands:
                # If there's no direct answer and no commands, it's just a conversational prompt.
                with Status("[bold cyan]Generating response...[/bold cyan]", spinner="dots"):
                    answer, _ = interpret_output(user_input, "No system commands needed. Just answer as an AI assistant.", ttl=ttl)
                console.print(Panel(
                    f"[bold white]{answer}[/bold white]",
                    title="[bold magenta]ALOA Answer[/bold magenta]",
                    border_style="magenta",
                ))
                return

            # ── Layer 1: answer cache (entire question cached) ────────
            ans_key = f"ans:{normalize_key(user_input)}"
            cached_answer = answer_cache.get(ans_key)
            if cached_answer is not None:
                remaining = answer_cache.remaining_ttl(ans_key)
                console.print(Panel(
                    f"[bold white]{cached_answer}[/bold white]",
                    title=f"[bold magenta]ALOA Answer[/bold magenta] [dim green](cached, {remaining}s left)[/dim green]",
                    border_style="magenta",
                ))
                return

            # ── Layer 2: run commands (each has its own command cache) ─
            console.print(Panel(
                f"[dim]{plan.get('description', 'Running query...')}[/dim]",
                title="[bold cyan]Query[/bold cyan]",
                border_style="cyan",
            ))

            all_output_parts = []
            for cmd in commands:
                output, ok = capture_shell_output(cmd, ttl=ttl)
                if output:
                    all_output_parts.append(output)

            raw_output = "\n".join(all_output_parts).strip()

            # ── Layer 3: LLM interpret (cached by output hash in planner)
            with Status("[bold cyan]Interpreting result...[/bold cyan]", spinner="dots"):
                answer, from_llm_cache = interpret_output(user_input, raw_output, ttl=ttl)

            # Also cache at the question level for next time (instant hit)
            answer_cache.set(ans_key, answer, ttl)

            badge = "[dim green](cached)[/dim green]" if from_llm_cache else ""
            console.print(Panel(
                f"[bold white]{answer}[/bold white]",
                title=f"[bold magenta]ALOA Answer[/bold magenta] {badge}",
                border_style="magenta",
            ))
            return


        # ── Action path (requires consent) ───────────────────────────
        commands = plan.get("commands", [])
        description = plan.get("description", "")

        # If the plan has no commands, generate a full markdown plan
        if not commands:
            with Status("[bold cyan]Planning...[/bold cyan]", spinner="dots"):
                plan_text = generate_action_plan(user_input)
            
            console.print(Panel(plan_text, title="[bold magenta]AI Implementation Plan[/bold magenta]", border_style="magenta"))
            
            extracted_cmds = extract_commands(plan_text)
            if not extracted_cmds:
                return
            
            consent = console.input("[bold yellow]Proceed? (y/n): [/bold yellow]").strip().lower()
            if consent in ["y", "yes", ""]:
                handle_llm_result("action", plan_text)
            else:
                console.print("[bold red]Action cancelled.[/bold red]")
            return

        # Show the plan clearly
        cmd_list = "\n".join(f"  • [cyan]{c}[/cyan]" for c in commands)
        console.print(Panel(
            f"[bold]{description}[/bold]\n\n[dim]Commands to run:[/dim]\n{cmd_list}",
            title="[bold magenta]AI Action Plan[/bold magenta]",
            border_style="magenta",
        ))

        consent = "y"
        if not (plan.get("instant") and plan.get("safe")):
            consent = console.input("[bold yellow]Approve and execute? (y/n): [/bold yellow]").strip().lower()

        if consent not in ["y", "yes", ""]:
            console.print("[bold red]Action cancelled by user.[/bold red]")
            return

        from utils.shell import run_shell_command
        success_count = 0
        for cmd in commands:
            if run_shell_command(cmd):
                success_count += 1
            else:
                keep_going = console.input("[bold red]Step failed. Continue? (y/n): [/bold red]").strip().lower()
                if keep_going != "y":
                    break

        from utils.formatting import success_panel
        console.print(success_panel(
            f"Done: {success_count}/{len(commands)} steps succeeded.",
            title="Execution Complete",
        ))


    def _handle_unknown(self, cmd: ParsedCommand):
        """Handle unknown commands."""
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
