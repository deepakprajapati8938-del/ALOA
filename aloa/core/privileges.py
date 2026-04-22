"""
ALOA Privilege Manager — Detect and handle Windows admin elevation.
"""

import ctypes
import sys
import os


def is_admin() -> bool:
    """Check if the current process is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (AttributeError, OSError):
        return False


def require_admin(action: str = "this action") -> bool:
    """Check admin rights and print a warning if not elevated.

    Returns True if running as admin, False otherwise.
    """
    if is_admin():
        return True

    from utils.formatting import console, warning_panel
    console.print(warning_panel(
        f"[yellow]{action}[/yellow] requires Administrator privileges.\n\n"
        "Please re-run ALOA as Administrator:\n"
        "  [bold]Right-click Terminal → Run as Administrator[/bold]\n"
        "  Then run: [cyan]python main.py[/cyan]",
        title="Elevation Required"
    ))
    return False


def elevate_and_rerun():
    """Attempt to re-launch the current script with admin privileges."""
    if is_admin():
        return

    try:
        script = os.path.abspath(sys.argv[0])
        params = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        sys.exit(0)
    except Exception as e:
        from utils.formatting import console, error_panel
        console.print(error_panel(
            f"Failed to elevate privileges: {e}\n"
            "Please manually run as Administrator.",
            title="Elevation Failed"
        ))
        sys.exit(1)
