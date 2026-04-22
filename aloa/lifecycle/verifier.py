"""
ALOA Installation Verifier — Confirm apps are properly installed and usable.
"""

import shutil
import subprocess
from core.parser import ParsedCommand
from lifecycle.registry import find_app
from utils.formatting import (
    console, success_panel, error_panel, warning_panel,
    make_table, print_header, status_icon
)


# ── Common version flags by app ─────────────────────────────────────

VERSION_FLAGS = {
    "python": ["python", "--version"],
    "node": ["node", "--version"],
    "npm": ["npm", "--version"],
    "git": ["git", "--version"],
    "java": ["java", "-version"],
    "javac": ["javac", "-version"],
    "maven": ["mvn", "--version"],
    "mvn": ["mvn", "--version"],
    "gradle": ["gradle", "--version"],
    "docker": ["docker", "--version"],
    "go": ["go", "version"],
    "rust": ["rustc", "--version"],
    "cargo": ["cargo", "--version"],
    "ruby": ["ruby", "--version"],
    "php": ["php", "--version"],
    "dotnet": ["dotnet", "--version"],
    "cmake": ["cmake", "--version"],
    "gcc": ["gcc", "--version"],
    "g++": ["g++", "--version"],
    "make": ["make", "--version"],
    "curl": ["curl", "--version"],
    "wget": ["wget", "--version"],
    "powershell": ["powershell", "-Command", "$PSVersionTable.PSVersion"],
}


def _get_exe_name(app_name: str) -> str:
    """Convert an app name to its likely executable name."""
    exe_map = {
        "maven": "mvn",
        "gradle": "gradle",
        "visual studio code": "code",
        "vscode": "code",
        "notepad++": "notepad++",
        "python3": "python",
        "nodejs": "node",
        "golang": "go",
    }
    return exe_map.get(app_name.lower(), app_name.lower())


def verify_installation(app_name: str) -> dict:
    """Verify that an application is properly installed.

    Returns a dict with keys:
      - in_registry: bool
      - on_path: bool
      - version: str or None
      - exe_path: str or None
      - registry_info: InstalledApp or None
    """
    result = {
        "in_registry": False,
        "on_path": False,
        "version": None,
        "exe_path": None,
        "registry_info": None,
    }

    # Check registry
    matches = find_app(app_name)
    if matches:
        result["in_registry"] = True
        result["registry_info"] = matches[0]

    # Check PATH
    exe_name = _get_exe_name(app_name)
    exe_path = shutil.which(exe_name)
    if not exe_path:
        exe_path = shutil.which(exe_name + ".exe")
    if exe_path:
        result["on_path"] = True
        result["exe_path"] = exe_path

    # Try to get version
    version_cmd = VERSION_FLAGS.get(exe_name)
    if not version_cmd:
        version_cmd = [exe_name, "--version"]

    try:
        proc = subprocess.run(
            version_cmd, capture_output=True, text=True, timeout=10,
        )
        output = (proc.stdout + proc.stderr).strip()
        if output:
            # Take first non-empty line as version
            for line in output.split("\n"):
                line = line.strip()
                if line:
                    result["version"] = line
                    break
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return result


# ── CLI Handler ─────────────────────────────────────────────────────

def handle_verify(cmd: ParsedCommand):
    """Handle the 'verify' command."""
    if not cmd.target:
        console.print(error_panel(
            "Please specify what to verify.\n"
            "Example: [cyan]verify maven[/cyan]",
            title="Missing Target"
        ))
        return

    print_header(f"Verifying: {cmd.target}")

    info = verify_installation(cmd.target)

    rows = [
        [
            "Registry Entry",
            status_icon("good") if info["in_registry"] else status_icon("critical"),
            info["registry_info"].display_name if info["registry_info"] else "Not found",
        ],
        [
            "On PATH",
            status_icon("good") if info["on_path"] else status_icon("critical"),
            info["exe_path"] or "Not found",
        ],
        [
            "Version",
            status_icon("good") if info["version"] else status_icon("warning"),
            info["version"] or "Could not determine",
        ],
    ]

    table = make_table(
        f"Verification: {cmd.target}",
        [("Check", "left"), ("Status", "center"), ("Details", "left")],
        rows,
    )
    console.print(table)

    # Overall verdict
    if info["in_registry"] and info["on_path"] and info["version"]:
        console.print(success_panel(
            f"[bold]{cmd.target}[/bold] is fully installed and ready to use!",
            title="Fully Verified"
        ))
    elif info["in_registry"] and not info["on_path"]:
        console.print(warning_panel(
            f"[bold]{cmd.target}[/bold] is installed but NOT on your PATH.\n"
            f"Run [cyan]path {cmd.target}[/cyan] to fix this.",
            title="PATH Issue"
        ))
    elif not info["in_registry"]:
        console.print(error_panel(
            f"[bold]{cmd.target}[/bold] does not appear to be installed.\n"
            f"Run [cyan]install {cmd.target}[/cyan] to install it.",
            title="Not Installed"
        ))
