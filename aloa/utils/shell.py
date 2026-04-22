import subprocess
from utils.formatting import console, info_panel, error_panel


def capture_shell_output(cmd: str, ttl: int = 30) -> tuple[str, bool]:
    """Run a PowerShell command silently and return (output, success).

    Results are cached for `ttl` seconds so repeated calls are instant.
    Pass ttl=0 to bypass the cache (force a fresh run).
    """
    from utils.cache import command_cache, normalize_key

    cache_key = f"cmd:{normalize_key(cmd)}"

    # Cache hit — instant return
    if ttl > 0:
        cached = command_cache.get(cache_key)
        if cached is not None:
            return cached  # already a (output, success) tuple

    # Cache miss — run the command
    try:
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output = (output + "\n" + result.stderr.strip()).strip()
        success = result.returncode == 0
        if ttl > 0 and success:
            command_cache.set(cache_key, (output, success), ttl)
        return output, success
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds.", False
    except Exception as e:
        return str(e), False


def run_shell_command(cmd: str) -> bool:
    """Run a shell command and display output in real-time."""
    console.print(info_panel(f"Executing: [cyan]{cmd}[/cyan]", title="Shell Executor"))
    
    try:
        # Use shell=True for complex commands (pipes, redirects) on Windows
        # We use powershell for better consistency
        process = subprocess.Popen(
            ["powershell", "-Command", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )

        for line in process.stdout:
            console.print(f"[dim]{line.strip()}[/dim]")
            
        process.wait()
        
        if process.returncode != 0:
            stderr = process.stderr.read()
            if stderr:
                console.print(error_panel(stderr, title="Command Error"))
            return False
            
        return True
        
    except Exception as e:
        console.print(error_panel(str(e), title="Execution Exception"))
        return False
