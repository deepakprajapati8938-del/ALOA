import re
from core.parser import ParsedCommand
from llm.planner import generate_plan
from utils.shell import run_shell_command
from utils.formatting import console, info_panel, success_panel, error_panel
from rich.panel import Panel

def handle_smart_task(cmd: ParsedCommand):
    """Legacy handler for ParsedCommand (deprecated in favor of handle_llm_result)."""
    plan_text = generate_plan(cmd)
    handle_llm_result("smart_task", plan_text)

def handle_llm_result(intent: str, result_text: str):
    """Execute commands from a semantically analyzed LLM result."""
    commands = extract_commands(result_text)
    
    if not commands:
        console.print(info_panel("This action is purely informational. No commands to execute."))
        return

    # In Semantic mode, consent is already obtained in Agent.execute()
    # but we list the commands again for absolute clarity.
    success_count = 0
    all_cmds = []
    for block in commands:
        all_cmds.extend([c.strip() for c in block.split('\n') if c.strip()])

    console.print(f"[bold cyan]Executing {len(all_cmds)} multi-step actions...[/bold cyan]")
    
    for c in all_cmds:
        if run_shell_command(c):
            success_count += 1
        else:
            if not console.input("[bold red]Step failed. Force continue to next step? (y/n): [/bold red]").strip().lower() == 'y':
                break
    
    console.print(success_panel(f"Semantic task finished: {success_count}/{len(all_cmds)} successful steps.", title="Execution Complete"))

def extract_commands(text: str) -> list[str]:
    """Helper to extract powershell/shell code blocks from text."""
    return re.findall(r'```(?:powershell|bash|cmd|shell)?\s*(.*?)\s*```', text, re.DOTALL)
