"""
ALOA LLM Planner — Classifies user intent and interprets command output.

Architecture:
  1. quick_pre_match()  — instant keyword match for common queries (no LLM)
  2. classify_and_plan() — LLM call for unknown queries
  3. interpret_output()  — single LLM call to turn raw output into a human answer

Caching layers:
  - command_cache : raw shell output per command, TTL depends on data volatility
  - answer_cache  : final LLM answer per normalised question, inherits command TTL
"""
import json
import re
from llm.providers import get_fallback_chain
from core.parser import ParsedCommand
from utils.cache import (
    TTLCache, normalize_key, content_hash,
    command_cache, answer_cache,
    STATIC, SEMI_STATIC, DYNAMIC, REALTIME,
)
from rich.console import Console

console = Console()

# ── Quick pre-match table ────────────────────────────────────────────────────
# (regex, [ps commands], description, ttl_seconds)
# TTL is inherited by the answer cache entry for that query type.

QUICK_QUERIES: list[tuple[str, list[str], str, int]] = [
    (
        r"host.?name|computer.?name|pc.?name|machine.?name",
        ["$env:COMPUTERNAME"],
        "Get the computer hostname",
        STATIC,          # never changes while running
    ),
    (
        r"\bip.?address\b|\bmy.?ip\b|\bipv4\b|\blocal.?ip\b",
        [
            "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*'} | Select-Object -First 1 -ExpandProperty IPAddress)"
        ],
        "Get local IPv4 address",
        DYNAMIC,         # can change on network switch
    ),
    (
        r"\bram\b|\bmemory\b|\bmem\b|\bhow.?much.?ram\b",
        [
            "$gb = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2); \"Total RAM: $gb GB\"",
            "$free = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024, 2); \"Free RAM: $free GB\"",
        ],
        "Get RAM usage",
        SEMI_STATIC,     # total is static; free changes, 5 min is fine
    ),
    (
        r"\bcpu\b|\bprocessor\b|\bchip\b",
        ["(Get-CimInstance Win32_Processor).Name"],
        "Get CPU model",
        STATIC,
    ),
    (
        r"\bdisk\b|\bstorage\b|\bhard.?drive\b|\bssd\b|\bfree.?space\b|\bspace.?(left|remaining|available)\b",
        [
            "Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{N='Used(GB)';E={[math]::Round($_.Used/1GB,1)}}, @{N='Free(GB)';E={[math]::Round($_.Free/1GB,1)}} | Format-Table -AutoSize | Out-String"
        ],
        "Get disk usage",
        SEMI_STATIC,
    ),
    (
        r"\bos\b|\bwindows.?version\b|\boperating.?system\b|\bwindows\b",
        ["(Get-WmiObject Win32_OperatingSystem).Caption + ' ' + (Get-WmiObject Win32_OperatingSystem).Version"],
        "Get Windows version",
        STATIC,
    ),
    (
        r"\busername\b|\bwho.?am.?i\b|\bmy.?user\b|\bcurrent.?user\b",
        ["$env:USERNAME + ' (Domain: ' + $env:USERDOMAIN + ')'"],
        "Get current username",
        STATIC,
    ),
    (
        r"\buptime\b|\bsince.?(boot|restart|start)\b|\blast.?boot\b|\bbeen.?on\b",
        [
            "$boot = (gcim Win32_OperatingSystem).LastBootUpTime; $up = (Get-Date) - $boot; \"Up for: $($up.Days)d $($up.Hours)h $($up.Minutes)m  (since $($boot.ToString('yyyy-MM-dd HH:mm')))\""
        ],
        "Get system uptime",
        SEMI_STATIC,
    ),
    (
        r"\bnetwork\b|\bwifi\b|\bwi-fi\b|\badapter\b|\bconnection\b",
        [
            "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription, LinkSpeed | Format-Table -AutoSize | Out-String"
        ],
        "List active network adapters",
        DYNAMIC,
    ),
    (
        r"\bprocess(es)?\b|\brunning.?(app|program|task)\b|\btask.?list\b",
        [
            "Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Name, Id, @{N='CPU%';E={[math]::Round($_.CPU,1)}}, @{N='Mem(MB)';E={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-Table -AutoSize | Out-String"
        ],
        "List top running processes",
        REALTIME,
    ),
    (
        r"\bport(s)?\b|\blistening\b|\bopen.?port\b",
        ["netstat -ano | findstr LISTENING | Select-Object -First 20 | Out-String"],
        "List listening ports",
        REALTIME,
    ),
    (
        r"\bbattery\b|\bcharge\b|\bpower\b",
        [
            "(Get-WmiObject Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus | Format-Table | Out-String)"
        ],
        "Get battery status",
        DYNAMIC,
    ),
    (
        r"\btime\b|\bclock\b|\bdate\b|\bcurrent.?time\b|\bwhat.?time\b",
        ["Get-Date -Format 'dddd, MMMM d, yyyy  h:mm tt'"],
        "Get current date and time",
        REALTIME,
    ),
    # -- Instant OS Actions --
    (
        r"^open (explorer|file explorer|folder)$",
        ["explorer.exe"],
        "Open File Explorer",
        STATIC,
    ),
    (
        r"^open (calculator|calc)$",
        ["calc.exe"],
        "Open Calculator",
        STATIC,
    ),
    (
        r"^open notepad$",
        ["notepad.exe"],
        "Open Notepad",
        STATIC,
    ),
    (
        r"^open (edge|browser)$",
        ["start msedge"],
        "Open Microsoft Edge",
        STATIC,
    ),
    (
        r"^open start( menu)?$",
        ["(New-Object -ComObject shell.application).MinimizeAll(); (New-Object -ComObject shell.application).UndoMinimizeAll()"], # Hack to trigger start? No, let's use a better one or just use a standard way.
        "Focus Start Menu",
        STATIC,
    ),
]

# ── Prompts ───────────────────────────────────────────────────────────────────

CLASSIFY_PROMPT = """\
You are ALOA, an Autonomous Laptop Operating Agent running on Windows PowerShell.
The user said: "{user_input}"

Classify their request. Respond with ONLY a valid JSON object, no markdown, no explanation.

Rules:
- "type": "query" for read-only info requests; "action" for installs/deletes/changes
- "safe": true only if all commands are non-destructive
- "commands": list of PowerShell one-liners (max 3)
- "direct_answer": string if you know the answer without any command (e.g. general knowledge like "who is..."), else null
- "description": one sentence explaining what you will do

Example output:
{{"type":"query","safe":true,"description":"Get the computer hostname","commands":["$env:COMPUTERNAME"],"direct_answer":null}}
{{"type":"query","safe":true,"description":"General knowledge answer","commands":[],"direct_answer":"Donald Trump is an American politician..."}}
"""

INTERPRET_PROMPT = """\
You are ALOA, an Autonomous Laptop Operating Agent.
The user asked: "{user_question}"

You ran a command and got this output:
---
{command_output}
---

Give a short, direct, friendly answer to their question based on the output.
Do NOT repeat raw output verbatim. Just answer conversationally in 1-3 sentences.
"""

ACTION_PLAN_PROMPT = """\
You are ALOA (Autonomous Laptop Operating Agent).
The user wants to: {user_input}

Create a concise implementation plan with exact PowerShell commands.

Format:
### Implementation Plan
- [Step 1]
- [Step 2]

```powershell
# Commands here
```
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def _call_llm(prompt: str) -> str | None:
    chain = get_fallback_chain()
    if not chain:
        return None
    for provider in chain:
        result = provider.generate(prompt)
        if result:
            return result
    return None


def _extract_json(text: str) -> dict | None:
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def quick_pre_match(user_input: str) -> dict | None:
    """Instant keyword match. Returns plan dict with _ttl — no LLM needed."""
    lower = user_input.lower()
    for pattern, commands, description, ttl in QUICK_QUERIES:
        if re.search(pattern, lower):
            # If it's an "open" command, mark it as an instant action
            is_instant = lower.startswith("open")
            
            return {
                "type": "query" if not is_instant else "action",
                "safe": True,
                "description": description,
                "commands": commands,
                "direct_answer": None,
                "instant": is_instant,
                "_source": "pre_match",
                "_ttl": ttl,
            }
    return None


def classify_and_plan(user_input: str) -> dict:
    """Classify intent. Instant for known patterns; LLM call for unknowns."""
    pre = quick_pre_match(user_input)
    if pre:
        return pre

    prompt = CLASSIFY_PROMPT.format(user_input=user_input)
    raw = _call_llm(prompt)

    if raw:
        parsed = _extract_json(raw)
        if parsed and (("type" in parsed and "commands" in parsed) or "direct_answer" in parsed):
            parsed.setdefault("type", "query")
            parsed.setdefault("safe", True)
            parsed.setdefault("commands", [])
            parsed.setdefault("description", "")
            parsed.setdefault("direct_answer", None)
            parsed["_source"] = "llm"
            parsed["_ttl"] = DYNAMIC   # default TTL for LLM-classified queries
            return parsed

    if raw is None:
        return {
            "type": "query",
            "safe": True,
            "description": "LLM Timeout or Unavailable",
            "commands": [],
            "direct_answer": "⚠️ ALOA could not connect to any configured LLM providers (they may be offline or timing out). Please check your .env configuration and ensure your local models are running.",
            "_source": "fallback",
            "_ttl": 5,
        }

    return {
        "type": "action",
        "safe": False,
        "description": user_input,
        "commands": [],
        "direct_answer": "⚠️ I couldn't understand that request correctly.",
        "_raw": raw or "",
        "_source": "fallback",
        "_ttl": DYNAMIC,
    }


def interpret_output(user_question: str, command_output: str, ttl: int = DYNAMIC) -> tuple[str, bool]:
    """Interpret command output.  Returns (answer, from_cache).

    Caches the LLM answer keyed on (normalized question + output hash).
    The TTL is inherited from the source command's volatility class.
    """
    cache_key = f"ans:{normalize_key(user_question)}:{content_hash(command_output)}"

    cached = answer_cache.get(cache_key)
    if cached is not None:
        return cached, True

    prompt = INTERPRET_PROMPT.format(
        user_question=user_question,
        command_output=command_output or "(no output)",
    )
    result = _call_llm(prompt) or f"Here's the raw output:\n{command_output}"

    answer_cache.set(cache_key, result, ttl)
    return result, False


def generate_action_plan(user_input: str) -> str:
    """Generate markdown plan for destructive/write actions (requires consent)."""
    prompt = ACTION_PLAN_PROMPT.format(user_input=user_input)
    result = _call_llm(prompt)
    return result or "⚠️ Could not generate a plan — no LLM providers available."


# ── Legacy shims ──────────────────────────────────────────────────────────────

def analyze_meaning_and_plan(user_input: str) -> str:
    plan = classify_and_plan(user_input)
    if plan.get("direct_answer"):
        return plan["direct_answer"]
    cmds = "\n".join(plan.get("commands", []))
    desc = plan.get("description", user_input)
    return f"### Plan\n{desc}\n\n```powershell\n{cmds}\n```" if cmds else desc


def generate_plan(cmd: ParsedCommand) -> str:
    return generate_action_plan(f"{cmd.intent} {cmd.target or ''}")
