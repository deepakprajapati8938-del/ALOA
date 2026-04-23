import os
import re
import subprocess
import tempfile
import tkinter as tk
from tkinter import messagebox

from utils.providers import call_llm

# --- MASTER PROMPT ---
SYSTEM_PROMPT = """
You are "The ALOA", a Windows System Assistant.
Output ONLY the raw command. No markdown. No explanation.

RULES:
1. OPEN APPS: Use `start <app_name>`
   - Examples: `start instagram`, `start chrome`, `start whatsapp`, `start notepad`
   - DO NOT add colons, paths, or complex IDs. Just the simple name.

2. INSTALLATION / DOWNLOAD: Use winget
   - Command: `winget install "<App Name>" -e --silent --accept-package-agreements --accept-source-agreements`
   - If Store App (Instagram, WhatsApp, Netflix, etc): Add `--source msstore`

3. UNINSTALL: 
   - Command: `winget uninstall "<App Name>" --silent`

4. CLOSE / KILL APP:
   - Command: `taskkill /IM <process_name>.exe /F`

EXAMPLES:
User: "Open Instagram"
Output: start instagram

User: "Download VLC"
Output: winget install "VLC media player" -e --silent --accept-package-agreements --accept-source-agreements

User: "Download Instagram"
Output: winget install "Instagram" --source msstore -e --silent --accept-package-agreements --accept-source-agreements

User: "Chrome band kar do"
Output: taskkill /IM chrome.exe /F

User: "Open MS Word"
Output: start winword

User: "Download Cursor AI"
Output: winget install "Cursor" -e --silent --accept-package-agreements --accept-source-agreements
"""


class UnifiedCommandChain:
    """Wraps the shared call_llm() to provide the same .invoke() interface."""
    def invoke(self, inputs):
        user_input = inputs.get("input", "")
        return call_llm(prompt=user_input, system=SYSTEM_PROMPT, ttl=60, use_memory=True)


command_chain = UnifiedCommandChain()


# ============================================================
# PowerShell script template for launching apps
# This is a STATIC string — NO Python f-string to avoid $_ issues
# We replace only the placeholder "APP_NAME_PLACEHOLDER" safely.
# ============================================================
PS_LAUNCH_SCRIPT = r'''
param([string]$appName)

$found = $false

# --- STRATEGY 1: Search Start Menu Shortcuts (.lnk files) ---
$startPaths = @(
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
)

foreach ($dir in $startPaths) {
    if (Test-Path $dir) {
        $shortcut = Get-ChildItem -Path $dir -Recurse -Filter "*.lnk" -ErrorAction SilentlyContinue |
            Where-Object { $_.BaseName -like "*$appName*" } |
            Select-Object -First 1
        if ($shortcut) {
            Write-Host "Found shortcut: $($shortcut.BaseName)"
            Start-Process $shortcut.FullName
            $found = $true
            break
        }
    }
}

# --- STRATEGY 2: Search Store Apps (AppxPackage) ---
if (-not $found) {
    $pkg = Get-AppxPackage | Where-Object { $_.Name -like "*$appName*" } | Select-Object -First 1
    if ($pkg) {
        Write-Host "Found Store App: $($pkg.Name)"
        try {
            $manifest = Get-AppxPackageManifest $pkg
            $appId = $manifest.Package.Applications.Application.Id
            if ($appId -is [array]) { $appId = $appId[0] }
            Start-Process "shell:AppsFolder\$($pkg.PackageFamilyName)!$appId"
        } catch {
            Start-Process "shell:AppsFolder\$($pkg.PackageFamilyName)!App"
        }
        $found = $true
    }
}

# --- STRATEGY 3: Direct Start-Process (built-in apps like notepad, calc, mspaint) ---
if (-not $found) {
    try {
        Start-Process "$appName" -ErrorAction Stop
        Write-Host "Launched directly: $appName"
        $found = $true
    } catch {
        # silent
    }
}

# --- STRATEGY 4: Search common install paths ---
if (-not $found) {
    $searchDirs = @(
        "$env:LOCALAPPDATA",
        "$env:APPDATA",
        "$env:ProgramFiles",
        "${env:ProgramFiles(x86)}"
    )
    foreach ($dir in $searchDirs) {
        if (Test-Path $dir) {
            $exe = Get-ChildItem -Path $dir -Recurse -Filter "$appName.exe" -Depth 3 -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($exe) {
                Write-Host "Found exe: $($exe.FullName)"
                Start-Process $exe.FullName
                $found = $true
                break
            }
        }
    }
}

if (-not $found) {
    Write-Host "APP_NOT_FOUND"
}
'''


def get_user_confirmation(command):
    """User se permission lene ke liye popup"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        response = messagebox.askyesno("ALOA Agent", f"Execute this command?\n\n{command}")
        root.destroy()
        return response
    except Exception:
        # Fallback to CLI if tkinter fails
        ans = input(f"\n  Execute this command?\n  >>> {command}\n  (y/n): ").strip().lower()
        return ans == "y"


from utils.memory import aloa_memory

def launch_app(app_name):
    """
    PowerShell se app launch karta hai — 4 strategies use karta hai:
    1. Start Menu shortcuts (.lnk) — Desktop apps (Spotify, VLC)
    2. AppxPackage — Store apps (Instagram, WhatsApp)
    3. Direct Start-Process — Built-in (notepad, calc)
    4. EXE search in common dirs — Fallback
    """
    app_name = app_name.strip().replace(":", "").replace('"', '')
    print(f"  [Launcher] Searching for: {app_name}...")

    script_path = None
    try:
        # Write the static PS script to a temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
            f.write(PS_LAUNCH_SCRIPT)
            script_path = f.name

        # Run the script and pass app_name as a PARAMETER (safe, no escaping issues)
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path, app_name],
            capture_output=True, text=True, timeout=45
        )

        output = result.stdout.strip()
        if output:
            for line in output.splitlines():
                print(f"  [Launcher] {line}")

        if "APP_NOT_FOUND" in (output or ""):
            print(f"  [Launcher] ❌ Could not find '{app_name}' on this system.")
            return False
        return True

    except subprocess.TimeoutExpired:
        print("  [Launcher] Timeout — app may have opened.")
        return True
    except Exception as e:
        print(f"  [Launcher] Error: {e}")
        return False
    finally:
        if script_path:
            try:
                os.unlink(script_path)
            except:
                pass


def extract_app_name_from_winget(command):
    """Winget command se app ka naam nikalta hai"""
    # Match: winget install "App Name"
    match = re.search(r'winget\s+install\s+"([^"]+)"', command)
    if match:
        return match.group(1)
    # Without quotes
    match = re.search(r'winget\s+install\s+(\S+)', command)
    if match:
        return match.group(1)
    return None


def execute_command(command):
    """Main execution logic"""
    print(f"Executing: {command}")

    # --- CASE 1: OPEN APP ---
    if command.lower().startswith("start "):
        app_name = command[6:].strip()
        launch_app(app_name)
        aloa_memory.add_fact("User", "launched", app_name)
        print()

    # --- CASE 2: INSTALL APP (winget install) ---
    elif "winget install" in command.lower():
        app_name = extract_app_name_from_winget(command)
        print(f"  [Installer] Installing via winget... (this may take a while)")

        # Run winget — wait for it to finish
        result = subprocess.run(command, shell=True, text=True)

        if result.returncode == 0:
            print(f"\n  ✅ Installation complete!")
        else:
            print(f"\n  ⚠️ Install finished (exit code: {result.returncode})")

        # AUTO-OPEN after install regardless of exit code
        if app_name:
            print(f"  [Auto-Launch] Opening {app_name}...")
            launch_app(app_name)

    # --- CASE 3: OTHER COMMANDS (uninstall, taskkill, etc.) ---
    else:
        os.system(f'start "ALOA Task" cmd /k "{command}"')
        print("  Command sent to new window.\n")


def run():
    """App Manager Feature — main loop"""
    print("=" * 50)
    print("  THE ALOA - App Manager")
    print("  Smart Launcher + Auto-Open Active")
    print("=" * 50)
    print("  Type 'back' to return to menu, 'exit' to quit.\n")

    # API availability check (handled by call_llm fallback chain)
    if not any(os.environ.get(k) for k in ["GROQ_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY_1"]):
        print("  ⚠️  WARNING: No LLM API keys configured.")
        print("  Set GROQ_API_KEY, OPENROUTER_API_KEY, or GEMINI_API_KEY_1 in .env\n")

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower().strip() in ["exit", "quit", "band kar"]:
                print("Goodbye!")
                return "exit"
            if user_input.lower().strip() == "back":
                return "back"
            if not user_input.strip():
                continue

            # DualModelChain handles its own keys so we just proceed
            print("Thinking...")
            raw_cmd = command_chain.invoke({"input": user_input})
            # Cleanup markdown junk
            final_cmd = raw_cmd.strip()
            final_cmd = final_cmd.replace("```bash", "").replace("```powershell", "").replace("```", "")
            final_cmd = final_cmd.strip()

            print(f"Generated: {final_cmd}")

            if get_user_confirmation(final_cmd):
                execute_command(final_cmd)
            else:
                print("Cancelled.\n")

        except KeyboardInterrupt:
            print("\nReturning to menu...")
            return "back"
        except Exception as e:
            print(f"Error: {e}\n")
