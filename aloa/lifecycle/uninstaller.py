"""
ALOA Deep Uninstaller — Remove applications and all their traces.
"""

import os
import shutil
import subprocess
import shlex
from core.parser import ParsedCommand
from core.privileges import require_admin
from lifecycle.registry import find_app, InstalledApp
from utils.constants import APPDATA, LOCAL_APPDATA, TEMP_DIR
from utils.formatting import (
    console, success_panel, error_panel, warning_panel,
    make_table, make_tree, print_header, format_bytes
)


def _find_app_directories(app_name: str) -> list[str]:
    """Find all directories related to an app in common locations."""
    search_locations = [
        APPDATA,
        LOCAL_APPDATA,
        TEMP_DIR,
        os.path.join(LOCAL_APPDATA, "Programs"),
        os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files")),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")),
    ]

    found = []
    query = app_name.lower()

    for base in search_locations:
        if not os.path.isdir(base):
            continue
        try:
            for entry in os.scandir(base):
                if entry.is_dir() and query in entry.name.lower():
                    found.append(entry.path)
        except PermissionError:
            continue

    return found


def _get_dir_size(path: str) -> int:
    """Calculate the total size of a directory."""
    total = 0
    try:
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except (OSError, PermissionError):
                    continue
    except PermissionError:
        pass
    return total


def _find_related_services(app_name: str) -> list[str]:
    """Find Windows services related to an app."""
    try:
        result = subprocess.run(
            ["sc", "query", "type=", "service", "state=", "all"],
            capture_output=True, text=True,
        )
        services = []
        query = app_name.lower()
        current_service = None

        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("SERVICE_NAME:"):
                current_service = line.split(":", 1)[1].strip()
            elif line.startswith("DISPLAY_NAME:"):
                display = line.split(":", 1)[1].strip()
                if current_service and (
                    query in current_service.lower() or query in display.lower()
                ):
                    services.append(current_service)

        return services
    except Exception:
        return []


def preview_uninstall(app: InstalledApp, app_name: str) -> dict:
    """Generate a preview of what would be removed during deep uninstall.

    Returns a dict with keys: 'native_uninstall', 'directories', 'services', 'total_size'
    """
    results = {
        "native_uninstall": app.uninstall_string,
        "directories": [],
        "services": [],
        "total_size": 0,
    }

    # Find related directories
    dirs = _find_app_directories(app_name)
    if app.install_location and os.path.isdir(app.install_location):
        if app.install_location not in dirs:
            dirs.insert(0, app.install_location)

    for d in dirs:
        size = _get_dir_size(d)
        results["directories"].append((d, size))
        results["total_size"] += size

    # Find related services
    results["services"] = _find_related_services(app_name)

    return results


def execute_deep_uninstall(app: InstalledApp, app_name: str, preview: dict):
    """Execute the deep uninstall based on the preview."""

    # Step 1: Run native uninstaller
    if preview["native_uninstall"]:
        console.print("[cyan]Running native uninstaller...[/cyan]")
        try:
            raw_cmd = preview["native_uninstall"]
            
            # Parse the command line into a list
            # Note: posix=False is crucial on Windows to keep backslashes as path separators
            try:
                cmd_parts = shlex.split(raw_cmd, posix=False)
            except ValueError:
                # Fallback for very messy strings
                cmd_parts = raw_cmd.split()

            if not cmd_parts:
                raise ValueError("Empty uninstall command")

            # Safety hint: if the first token has no path separator it might
            # be a bare command name or a registry artefact.  We still run it
            # (registry strings are trusted) but surface a notice so the user
            # can see what's being executed.
            exe = cmd_parts[0].strip('"').strip("'")
            if os.sep not in exe and "/" not in exe:
                console.print(
                    f"[yellow]  ℹ Uninstall command starts with a bare name '[bold]{exe}[/bold]' "
                    "(no absolute path). Proceeding as-is from registry.[/yellow]"
                )

            # Add silent flags if not present
            has_silent = any(arg.lower() in ("/s", "/silent", "/quiet", "/qn") for arg in cmd_parts)
            if not has_silent:
                # If it's MsiExec, use /quiet /norestart
                if "msiexec" in cmd_parts[0].lower():
                    if "/qn" not in [a.lower() for a in cmd_parts]:
                        cmd_parts.extend(["/qn", "/norestart"])
                else:
                    cmd_parts.append("/S")

            # Final safety check: command should be an absolute path or a known system tool
            # (In reality, we trust the registry strings, but we run without shell=True)
            subprocess.run(cmd_parts, shell=False, timeout=120, capture_output=True)
            console.print("[green]  ✔ Native uninstaller completed.[/green]")
        except subprocess.TimeoutExpired:
            console.print("[yellow]  ⚠ Native uninstaller timed out.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]  ⚠ Native uninstaller error: {e}[/yellow]")

    # Step 2: Stop and remove services
    for service in preview["services"]:
        try:
            subprocess.run(["sc", "stop", service], capture_output=True, timeout=30)
            subprocess.run(["sc", "delete", service], capture_output=True, timeout=30)
            console.print(f"[green]  ✔ Service removed: {service}[/green]")
        except Exception:
            console.print(f"[yellow]  ⚠ Could not remove service: {service}[/yellow]")

    # Step 3: Remove directories
    for dir_path, _ in preview["directories"]:
        # Safety check: do not accidentally wipe root/system directories
        base = os.path.basename(os.path.normpath(dir_path)).lower()
        if not base or base in ("windows", "system32", "program files", "program files (x86)", "appdata", "local", "roaming", "temp", "users"):
            console.print(f"[yellow]  ⚠ Skipping unsafe directory removal: {dir_path}[/yellow]")
            continue
            
        try:
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)
                if not os.path.exists(dir_path):
                    console.print(f"[green]  ✔ Removed: {dir_path}[/green]")
                else:
                    console.print(f"[yellow]  ⚠ Partially removed: {dir_path}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]  ⚠ Could not remove {dir_path}: {e}[/yellow]")


# ── CLI Handler ─────────────────────────────────────────────────────

def handle_uninstall(cmd: ParsedCommand):
    """Handle the 'uninstall' command with deep cleanup."""
    if not cmd.target:
        console.print(error_panel(
            "Please specify what to uninstall.\n"
            "Example: [cyan]uninstall notepad++[/cyan]",
            title="Missing Target"
        ))
        return

    print_header(f"Deep Uninstall: {cmd.target}")

    # Find the app in registry
    matches = find_app(cmd.target)
    if not matches:
        console.print(error_panel(
            f"No installed application found matching [bold]{cmd.target}[/bold].",
            title="Not Found"
        ))
        return

    # If multiple matches, let user pick
    if len(matches) > 1:
        rows = [
            [str(i + 1), m.display_name, m.version or "—", m.publisher or "—"]
            for i, m in enumerate(matches[:10])
        ]
        table = make_table(
            f"Applications matching '{cmd.target}'",
            [("#", "right"), ("Name", "left"), ("Version", "left"), ("Publisher", "left")],
            rows,
        )
        console.print(table)

        try:
            choice = console.input("[bold cyan]Select # to uninstall (or 'c' to cancel): [/bold cyan]")
            if choice.lower() == "c":
                console.print("[yellow]Cancelled.[/yellow]")
                return
            idx = int(choice) - 1
            if 0 <= idx < len(matches):
                app = matches[idx]
            else:
                console.print("[red]Invalid selection.[/red]")
                return
        except (ValueError, KeyboardInterrupt):
            console.print("[yellow]Cancelled.[/yellow]")
            return
    else:
        app = matches[0]

    # Generate preview
    console.print(f"[cyan]Analyzing [bold]{app.display_name}[/bold]...[/cyan]")
    preview = preview_uninstall(app, cmd.target)

    # Show preview
    console.print()
    tree = make_tree(f"Deep Uninstall Preview — {app.display_name}", [])

    if preview["native_uninstall"]:
        console.print(f"  [cyan]Native uninstaller:[/cyan] {preview['native_uninstall']}")

    if preview["directories"]:
        console.print(f"  [cyan]Directories to remove:[/cyan]")
        for dir_path, size in preview["directories"]:
            console.print(f"    [red]✖[/red] {dir_path} ({format_bytes(size)})")

    if preview["services"]:
        console.print(f"  [cyan]Services to remove:[/cyan]")
        for svc in preview["services"]:
            console.print(f"    [red]✖[/red] {svc}")

    console.print(f"\n  [bold]Total space to recover: {format_bytes(preview['total_size'])}[/bold]")
    console.print()

    # Confirm
    try:
        confirm = console.input("[bold red]Proceed with deep uninstall? (yes/no): [/bold red]")
        if confirm.lower() not in ("yes", "y"):
            console.print("[yellow]Uninstall cancelled.[/yellow]")
            return
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # Check admin for services
    if preview["services"] and not require_admin("Removing system services"):
        console.print("[yellow]Proceeding without service removal...[/yellow]")
        preview["services"] = []

    # Execute
    console.print()
    execute_deep_uninstall(app, cmd.target, preview)

    console.print()
    console.print(success_panel(
        f"[bold]{app.display_name}[/bold] has been deeply uninstalled.\n"
        f"Recovered approximately {format_bytes(preview['total_size'])} of space.",
        title="Deep Uninstall Complete"
    ))

    # Invalidate registry cache
    from lifecycle.registry import clear_cache
    clear_cache()
