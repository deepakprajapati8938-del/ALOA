# ALOA — Autonomous Laptop Operating Agent

```
     █████╗  ██╗      ██████╗   █████╗
    ██╔══██╗ ██║     ██╔═══██╗ ██╔══██╗
    ███████║ ██║     ██║   ██║ ███████║
    ██╔══██║ ██║     ██║   ██║ ██╔══██║
    ██║  ██║ ███████╗╚██████╔╝ ██║  ██║
    ╚═╝  ╚═╝ ╚══════╝ ╚═════╝  ╚═╝  ╚═╝
```

> **Phase 1 — System Control Foundation**
>
> ALOA is a Python-powered interactive CLI agent that gives you OS-level control over your Windows laptop. It can silently install and deep-uninstall applications, auto-configure your PATH, and continuously monitor system health to diagnose slowdowns and suggest optimizations — all from a single, elegant terminal interface.

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation & Setup](#installation--setup)
4. [Running ALOA](#running-aloa)
5. [Command Reference](#command-reference)
   - [Application Lifecycle](#application-lifecycle-commands)
   - [System Health](#system-health-commands)
   - [General](#general-commands)
6. [Natural Language Input](#natural-language-input)
7. [Project Structure](#project-structure)
8. [Module Reference](#module-reference)
   - [core/](#core)
   - [lifecycle/](#lifecycle)
   - [health/](#health)
   - [utils/](#utils)
9. [Configuration & Thresholds](#configuration--thresholds)
10. [Security & Safety](#security--safety)
11. [Known Limitations](#known-limitations)

---

## Features

### 🗂 Intelligent Application Lifecycle Manager
| Feature | Description |
|---|---|
| **Silent Install** | Search winget, pick a package, install silently — no UAC prompts mid-flow |
| **Deep Uninstall** | Runs native uninstaller + removes leftover directories + stops/deletes related services |
| **Install Verification** | Checks Windows Registry entry, PATH availability, and live version output |
| **Auto PATH Config** | Detects the binary directory after install and adds it to user PATH automatically |
| **App Search** | Query winget directly without leaving ALOA |

### 🩺 Autonomous System Health & Performance Engine
| Feature | Description |
|---|---|
| **RAM Monitor** | Real-time usage, swap pressure, top memory consumers |
| **CPU Monitor** | Overall + per-core usage, frequency, spike detection, top CPU consumers |
| **Disk Inspector** | All-drive usage bars, clutter scan (temp/cache directories), large file finder |
| **Startup Analyzer** | Lists startup programs with High / Medium / Low impact classification |
| **Unused App Detector** | Finds applications not used in the last 90 days |
| **Bottleneck Finder** | Composite RAM/CPU/Disk/Swap score → pinpoints the #1 reason your laptop is slow |
| **Suggestion Engine** | Ranked, actionable optimizations you can auto-execute with a single keystroke |
| **Temp Cleanup** | Wipes temp dirs, browser caches, Windows Update download cache |

---

## Requirements

- **OS**: Windows 10 / 11 (64-bit)
- **Python**: 3.10 or later
- **winget**: Pre-installed on Windows 11; available via Microsoft Store on Windows 10
- **Dependencies** (`requirements.txt`):

```
psutil>=5.9.0
rich>=13.0.0
```

---

## Installation & Setup

```bash
# 1. Clone or place the project
cd e:\miniproject\aloa

# 2. (Recommended) Create a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

> **Admin Tip**: Some features (service removal, system PATH changes, Windows Disk Cleanup) require Administrator privileges. Right-click your terminal → **Run as Administrator** for full functionality.

---

## Running ALOA

```bash
python main.py
```

ALOA starts an interactive REPL. You will see the ASCII banner and an `ALOA ❯` prompt. Type any command or a natural-language phrase and press Enter.

To exit at any time:
```
ALOA ❯ exit
```
or press `Ctrl+C` (you will be reminded to type `exit`).

---

## Command Reference

### Application Lifecycle Commands

| Command | Example | Description |
|---|---|---|
| `install <app>` | `install maven` | Search winget for `<app>`, present matches, install silently. Auto-configures PATH and verifies after install. |
| `uninstall <app>` | `uninstall notepad++` | Looks up the app in the Windows Registry, generates a preview of all files/services to be removed, asks for confirmation, then deep-removes everything. |
| `search <app>` | `search python` | Queries winget and displays a table of matching packages (Name, ID, Version). |
| `verify <app>` | `verify git` | Checks the Registry entry, PATH availability, and runs the version command. Reports a clear verdict. |
| `path <app>` | `path java` | Auto-detects the install directory and adds the correct `bin/` subfolder to the user PATH. Run without an app name to view all current PATH entries. |

#### Install Flow
```
install maven
  └─ search winget for "maven"
  └─ if 1 result  → install immediately
  └─ if multiple  → show numbered table, user picks
  └─ install silently (--silent --accept-package-agreements)
  └─ auto-configure PATH
  └─ verify installation
  └─ invalidate registry cache
```

#### Deep Uninstall Flow
```
uninstall notepad++
  └─ scan Windows Registry for matching app
  └─ if multiple matches → user picks
  └─ preview: native uninstaller + directories + services + total size
  └─ confirm (yes/no)
  └─ run native uninstaller (silent flags added automatically)
  └─ stop & delete related Windows services (requires admin)
  └─ rmtree all leftover directories
  └─ invalidate registry cache
```

---

### System Health Commands

| Command | Description |
|---|---|
| `health` | Full overview: runs `ram` + `cpu` + `disk` in sequence |
| `ram` | Memory usage panel, swap info, top 10 non-system memory consumers |
| `cpu` | Overall + per-core usage bar chart, frequency, top 10 CPU consumers |
| `disk` | Per-drive usage bar chart, clutter directory scan |
| `startup` | Lists all startup programs (Registry + Startup folder) with impact classification |
| `unused` | Detects apps not launched in the last 90 days |
| `diagnose` | Scores RAM / CPU / Disk / Swap (0–100), identifies the primary bottleneck, names the top offending process |
| `suggest` | Generates ranked optimization suggestions. Offers to auto-execute applicable ones |
| `cleanup` | Wipes temp files from all known clutter directories |

#### Severity Levels

| Threshold | RAM | CPU | Disk |
|---|---|---|---|
| 🟢 Healthy | < 75% | < 70% | < 80% |
| 🟡 Warning | 75 – 89% | 70 – 89% | 80 – 94% |
| 🔴 Critical | ≥ 90% | ≥ 90% | ≥ 95% |

---

### General Commands

| Command | Description |
|---|---|
| `help` | Display the full command table |
| `exit` / `quit` / `bye` | Gracefully shut down ALOA |

---

## Natural Language Input

ALOA understands plain English — you don't need to memorise exact command names:

| What you type | Interpreted as |
|---|---|
| `"why is my laptop so slow"` | `diagnose` |
| `"get me python"` | `install python` |
| `"deep remove notepad++"` | `uninstall notepad++` |
| `"what's eating my RAM?"` | `ram` |
| `"show startup programs"` | `startup` |
| `"clear my temp files"` | `cleanup` |
| `"fix my path for java"` | `path java` |
| `"check if git is installed"` | `verify git` |

The parser matches the **longest keyword phrase** in your input to an intent, strips filler words, and extracts the target app name from the remainder.

---

## Project Structure

```
aloa/
├── main.py                  # Entry point — banner, REPL loop
│
├── core/
│   ├── agent.py             # Central orchestrator — routes commands to handlers
│   ├── parser.py            # NL command parser — intent + target extraction
│   └── privileges.py        # Windows admin elevation detection & UAC helpers
│
├── lifecycle/
│   ├── installer.py         # winget search + silent install
│   ├── uninstaller.py       # Deep uninstall with preview & confirmation
│   ├── verifier.py          # Registry + PATH + version verification
│   ├── registry.py          # Windows Registry scanner with 5-minute cache
│   └── path_config.py       # User PATH read/write + WM_SETTINGCHANGE broadcast
│
├── health/
│   ├── ram_monitor.py       # RAM / swap usage + top memory consumers
│   ├── cpu_monitor.py       # CPU usage, per-core, frequency, spike detection
│   ├── disk_inspector.py    # Drive usage, clutter scan, large file finder
│   ├── startup_analyzer.py  # Startup program listing + impact classification
│   ├── unused_apps.py       # Unused application detection
│   ├── bottleneck.py        # Composite performance scoring + explanation
│   └── suggestions.py       # Ranked suggestion engine + cleanup executor
│
├── utils/
│   ├── constants.py         # Thresholds, paths, protected process list
│   └── formatting.py        # Rich console helpers (panels, tables, icons)
│
└── requirements.txt
```

---

## Module Reference

### `core/`

#### `core/agent.py` — `Agent`
Central command dispatcher. Registers handler functions from `lifecycle` and `health` modules at startup and routes parsed commands to the correct handler.

| Method | Description |
|---|---|
| `execute(user_input)` | Parse raw input and call the matched handler |
| `_handle_health_overview(cmd)` | Sequentially runs RAM → CPU → Disk |
| `_handle_help(cmd)` | Prints the full command table |
| `_handle_exit(cmd)` | Prints goodbye message and raises `SystemExit` |

#### `core/parser.py` — `parse(user_input) → ParsedCommand`
Keyword-based NL parser. Iterates `INTENT_PATTERNS`, finds the longest matching phrase, strips filler words, and extracts flags (`--force`, `--deep`).

```python
@dataclass
class ParsedCommand:
    intent: str          # e.g. "install", "diagnose"
    target: str | None   # e.g. "maven", "python"
    raw: str             # original user input
    flags: dict          # e.g. {"force": True}
```

#### `core/privileges.py`
| Function | Description |
|---|---|
| `is_admin() → bool` | Calls `shell32.IsUserAnAdmin()` |
| `require_admin(action) → bool` | Prints a warning panel if not elevated; returns `False` |
| `elevate_and_rerun()` | Re-launches current script via `ShellExecuteW("runas", ...)` |

---

### `lifecycle/`

#### `lifecycle/registry.py` — Registry Scanner
Scans `HKLM` and `HKCU` uninstall registry keys. Results are cached for **5 minutes** to avoid repeated scans.

| Function | Description |
|---|---|
| `scan_installed_apps(refresh=False)` | Returns `List[InstalledApp]`; uses TTL cache |
| `find_app(name)` | Case-insensitive substring search across display names |
| `get_install_location(name)` | Returns the first matching install path |
| `clear_cache()` | Forces a re-scan on the next call |

```python
@dataclass
class InstalledApp:
    display_name: str
    version: str | None
    publisher: str | None
    install_location: str | None
    uninstall_string: str | None
    install_date: str | None
    estimated_size_kb: int | None
    registry_key: str
```

#### `lifecycle/installer.py`
| Function | Description |
|---|---|
| `search_winget(query)` | Parses winget output into `List[{name, id, version}]` |
| `install_package(package_id)` | Runs `winget install --silent`, then triggers PATH config + verify |
| `handle_install(cmd)` | CLI handler: search → pick → install |
| `handle_search(cmd)` | CLI handler: search → display table |

#### `lifecycle/uninstaller.py`
| Function | Description |
|---|---|
| `preview_uninstall(app, name)` | Builds a preview dict: `{native_uninstall, directories, services, total_size}` |
| `execute_deep_uninstall(app, name, preview)` | Runs uninstaller → stop/delete services → `shutil.rmtree` dirs |
| `handle_uninstall(cmd)` | CLI handler with full confirm flow |

#### `lifecycle/verifier.py`
| Function | Description |
|---|---|
| `verify_installation(app_name)` | Returns `{in_registry, on_path, version, exe_path, registry_info}` |
| `handle_verify(cmd)` | Displays a 3-row check table + verdict panel |

Pre-built `VERSION_FLAGS` map covers: Python, Node, npm, Git, Java, Maven, Gradle, Docker, Go, Rust, Cargo, Ruby, PHP, .NET, CMake, GCC, G++, Make, curl, wget, PowerShell.

#### `lifecycle/path_config.py`
| Function | Description |
|---|---|
| `get_user_path()` | Reads `HKCU\Environment\Path` |
| `get_system_path()` | Reads `HKLM\...\Environment\Path` |
| `add_to_user_path(directory)` | Appends to user PATH, broadcasts `WM_SETTINGCHANGE` |
| `auto_configure_path(app_name)` | Finds install dir → checks `bin/`, `Scripts/`, `cmd/` subdirs → adds first match |
| `handle_path(cmd)` | CLI handler; shows current PATH if no target given |

---

### `health/`

#### `health/ram_monitor.py`
| Function | Description |
|---|---|
| `get_ram_info()` | Returns `{total, available, used, percent, swap_*}` via `psutil` |
| `get_top_memory_processes(n)` | Top N non-protected processes by RSS |
| `handle_ram(cmd)` | Displays overview panel + top consumers table |

#### `health/cpu_monitor.py`
| Function | Description |
|---|---|
| `get_cpu_info()` | Overall %, per-core %, core/thread count, frequency |
| `detect_cpu_spike(duration)` | Returns `True` if CPU > 90% sustained for ≥ 3 s in the window |
| `get_top_cpu_processes(n)` | Two-pass measurement (1 s interval) for accurate CPU% |
| `handle_cpu(cmd)` | Overview panel + per-core bar chart + top consumers |

#### `health/disk_inspector.py`
| Function | Description |
|---|---|
| `get_disk_usage()` | Info for all non-virtual partitions |
| `scan_clutter()` | Sizes of temp, cache, crash dump directories |
| `find_large_files(root, threshold_mb)` | Walks user directories; skips `AppData`, `.git`, `.m2`, `.gradle` |
| `handle_disk(cmd)` | Drive overview table + clutter report |

#### `health/bottleneck.py`
| Function | Description |
|---|---|
| `analyze_bottlenecks()` | Returns scores dict (RAM/CPU/Disk/Swap 0–100), primary bottleneck, explanation, top offenders |
| `handle_diagnose(cmd)` | Shows scored bar chart, primary bottleneck panel, top resource consumers |

Scoring:
- **RAM**: `mem.percent` + 10 penalty if swap > 50%
- **CPU**: `cpu_percent(interval=1.5)`
- **Disk**: System drive usage percent
- **Swap**: `swap.percent`

#### `health/suggestions.py`
| Function | Description |
|---|---|
| `generate_suggestions()` | Analyses bottleneck + startup data; returns sorted `List[suggestion_dict]` |
| `execute_cleanup()` | Deletes files in all `CLUTTER_DIRECTORIES`; returns `(bytes_freed, dirs_count)` |
| `handle_suggest(cmd)` | Shows suggestion table; offers selective or bulk auto-execution |
| `handle_cleanup(cmd)` | Confirms, then runs `execute_cleanup()` |

Suggestion dict fields: `priority`, `category`, `action`, `command`, `impact`, `auto_executable`.

---

### `utils/`

#### `utils/constants.py` — Key Values

| Constant | Default | Purpose |
|---|---|---|
| `RAM_WARNING_PERCENT` | 75 | Yellow alert threshold |
| `RAM_CRITICAL_PERCENT` | 90 | Red alert threshold |
| `CPU_WARNING_PERCENT` | 70 | Yellow alert threshold |
| `CPU_CRITICAL_PERCENT` | 90 | Red alert threshold |
| `DISK_WARNING_PERCENT` | 80 | Yellow alert threshold |
| `DISK_CRITICAL_PERCENT` | 95 | Red alert threshold |
| `UNUSED_APP_DAYS_THRESHOLD` | 90 | Days without use → flagged as unused |
| `LARGE_FILE_SIZE_MB` | 500 | File size → flagged as large |
| `CPU_SPIKE_DURATION_SECONDS` | 5 | Spike detection window |

`PROTECTED_PROCESSES` — a set of ~40 Windows kernel, security, driver, and shell process names that ALOA will **never** kill or flag as offenders. Includes `smss.exe`, `lsass.exe`, `explorer.exe`, `msmpeng.exe`, `python.exe`, `powershell.exe`, and more.

`is_protected(process_name) → bool` — case-insensitive lookup into the protected set.

#### `utils/formatting.py` — Rich Console Helpers

Wraps the `rich` library with consistent ALOA-branded styling:

| Helper | Description |
|---|---|
| `console` | Shared `rich.Console` instance |
| `info_panel(text, title, border_style)` | Blue-bordered informational panel |
| `success_panel(text, title)` | Green-bordered success panel |
| `warning_panel(text, title)` | Yellow-bordered warning panel |
| `error_panel(text, title)` | Red-bordered error panel |
| `make_table(title, columns, rows)` | Styled `rich.Table` with cyan header |
| `make_tree(label, items)` | `rich.Tree` for hierarchical display |
| `print_header(text)` | Horizontal rule with bold centered title |
| `format_bytes(n)` | `1234567 → "1.18 MB"` |
| `severity_color(value, warn, crit)` | `green` / `yellow` / `red` |
| `status_icon(level)` | `✔` / `⚠` / `✖` with appropriate color |
| `spinner_progress(desc)` | Context manager wrapping `rich.Progress` |

---

## Configuration & Thresholds

All configurable values live in `utils/constants.py`. Editing that file lets you tune:

- **Alert thresholds** for RAM, CPU, and Disk
- **Clutter directories** — add extra cache paths to `CLUTTER_DIRECTORIES`
- **Protected processes** — extend `PROTECTED_PROCESSES` to protect additional critical processes
- **Unused app threshold** — change `UNUSED_APP_DAYS_THRESHOLD`
- **Large file threshold** — change `LARGE_FILE_SIZE_MB`

---

## Security & Safety

| Concern | How ALOA handles it |
|---|---|
| **Process killing** | `PROTECTED_PROCESSES` guardrail prevents ALOA from ever killing kernel, security, driver, or shell processes |
| **Uninstall safety** | Requires explicit `yes` confirmation before any file deletion |
| **Command injection** | All subprocess calls use `shell=False` with parsed argument lists (`shlex.split`) |
| **Uninstaller timeout** | Native uninstallers are killed after **120 seconds** to prevent hangs |
| **Suggestion commands** | `taskkill` commands also use `shell=False`; only flagged non-protected processes are targeted |
| **Admin elevation** | Explicitly requested only where needed (service removal); all other features work without it |
| **Registry access** | Read-only registry access for scanning; write access only for PATH modifications under `HKCU\Environment` |

---

## Known Limitations

- **Windows only** — uses `winreg`, `ctypes.windll`, `winget`, and `sc` (Service Control). Not portable to macOS/Linux.
- **winget required** — installation commands depend on winget being available and having internet access.
- **PATH changes need a new terminal** — the `WM_SETTINGCHANGE` broadcast refreshes the environment for *new* processes; the current terminal session must be restarted to see the change.
- **Registry scan speed** — initial scan of all installed applications may take 1–2 seconds on systems with many apps. Results are cached for 5 minutes.
- **Large file scan** — intentionally skips `AppData`, `.git`, `.gradle`, and `.m2` to keep the scan fast; files inside those directories are not reported.
- **Startup impact scores** — impact classification uses estimated CPU/RAM figures from the registry (where available) and may not reflect real-world boot impact precisely.
