"""
ALOA Installer — Silent software installation via winget and direct installers.
"""

import subprocess
import time
from core.parser import ParsedCommand
from utils.formatting import (
    console, spinner_progress, success_panel, error_panel,
    info_panel, make_table, print_header
)


def _run_winget(args: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Run a winget command and return the result."""
    cmd = ["winget"] + args
    return subprocess.run(
        cmd, capture_output=capture, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if capture else 0,
    )


def search_winget(query: str) -> list[dict]:
    """Search winget for packages matching the query."""
    result = _run_winget(["search", query, "--accept-source-agreements"])

    if result.returncode != 0:
        return []

    lines = result.stdout.strip().split("\n")

    # Find the header separator line (contains dashes)
    header_idx = -1
    for i, line in enumerate(lines):
        if set(line.strip()).issubset({"-", " "}):
            header_idx = i
            break

    if header_idx < 1:
        return []

    # Parse header to get column positions
    header_line = lines[header_idx - 1]
    sep_line = lines[header_idx]

    # Find column boundaries from separator
    cols = []
    start = 0
    in_dash = False
    for i, ch in enumerate(sep_line):
        if ch == "-" and not in_dash:
            start = i
            in_dash = True
        elif ch == " " and in_dash:
            cols.append((start, i))
            in_dash = False
    if in_dash:
        cols.append((start, len(sep_line)))

    packages = []
    for line in lines[header_idx + 1:]:
        if not line.strip():
            continue
        if len(cols) >= 2:
            name = line[cols[0][0]:cols[0][1]].strip() if len(cols) > 0 else ""
            pkg_id = line[cols[1][0]:cols[1][1]].strip() if len(cols) > 1 else ""
            version = line[cols[2][0]:cols[2][1]].strip() if len(cols) > 2 else ""

            if pkg_id:
                packages.append({
                    "name": name,
                    "id": pkg_id,
                    "version": version,
                })

    return packages


def install_package(package_id: str) -> bool:
    """Install a package via winget with silent flags.

    Returns True if installation succeeded.
    """
    console.print(info_panel(
        f"Installing [bold cyan]{package_id}[/bold cyan] via winget...\n"
        "This may take a few minutes.",
        title="Installing"
    ))

    with spinner_progress("Installing...") as progress:
        task = progress.add_task(f"Installing {package_id}", total=100)

        result = subprocess.run(
            [
                "winget", "install", package_id,
                "--silent",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            capture_output=True, text=True,
        )

        progress.update(task, completed=100)

    if result.returncode == 0:
        console.print(success_panel(
            f"[bold]{package_id}[/bold] installed successfully!",
            title="Installation Complete"
        ))

        # Trigger PATH configuration
        from lifecycle.path_config import auto_configure_path
        auto_configure_path(package_id)

        # Invalidate registry cache
        from lifecycle.registry import clear_cache
        clear_cache()

        # Verify installation
        from lifecycle.verifier import verify_installation
        verify_installation(package_id)

        return True
    else:
        error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        console.print(error_panel(
            f"Failed to install [bold]{package_id}[/bold]:\n{error_msg}",
            title="Installation Failed"
        ))
        return False


# ── CLI Handlers ────────────────────────────────────────────────────

def handle_install(cmd: ParsedCommand):
    """Handle the 'install' command."""
    if not cmd.target:
        console.print(error_panel(
            "Please specify what to install.\n"
            "Example: [cyan]install maven[/cyan]",
            title="Missing Target"
        ))
        return

    print_header(f"Installing: {cmd.target}")

    # Search for the package first
    packages = search_winget(cmd.target)

    if not packages:
        console.print(error_panel(
            f"No packages found for [bold]{cmd.target}[/bold] in winget.\n"
            "Try a different search term.",
            title="Not Found"
        ))
        return

    if len(packages) == 1:
        install_package(packages[0]["id"])
    else:
        # Show options and let user pick
        rows = [
            [str(i + 1), p["name"], p["id"], p["version"]]
            for i, p in enumerate(packages[:15])
        ]
        table = make_table(
            f"Packages matching '{cmd.target}'",
            [("#", "right"), ("Name", "left"), ("ID", "left"), ("Version", "left")],
            rows,
        )
        console.print(table)
        console.print()

        try:
            choice = console.input("[bold cyan]Enter number to install (or 'c' to cancel): [/bold cyan]")
            if choice.lower() == "c":
                console.print("[yellow]Installation cancelled.[/yellow]")
                return
            idx = int(choice) - 1
            if 0 <= idx < len(packages):
                install_package(packages[idx]["id"])
            else:
                console.print("[red]Invalid selection.[/red]")
        except (ValueError, KeyboardInterrupt):
            console.print("[yellow]Installation cancelled.[/yellow]")


def handle_search(cmd: ParsedCommand):
    """Handle the 'search' command."""
    if not cmd.target:
        console.print(error_panel(
            "Please specify what to search for.\n"
            "Example: [cyan]search python[/cyan]",
            title="Missing Target"
        ))
        return

    print_header(f"Searching: {cmd.target}")

    packages = search_winget(cmd.target)

    if not packages:
        console.print(error_panel(
            f"No packages found for [bold]{cmd.target}[/bold].",
            title="Not Found"
        ))
        return

    rows = [
        [p["name"], p["id"], p["version"]]
        for p in packages[:20]
    ]
    table = make_table(
        f"Results for '{cmd.target}'",
        [("Name", "left"), ("ID", "left"), ("Version", "left")],
        rows,
    )
    console.print(table)
