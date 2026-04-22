"""
ALOA pre-presentation regression test.
Tests all critical code paths without requiring Ollama to be running.
"""
import sys, time
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {name}")
        PASS += 1
    else:
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))
        FAIL += 1

print("=" * 60)
print("ALOA Regression Tests")
print("=" * 60)

# ── 1. Cache module ───────────────────────────────────────────────────────────
print("\n[1] Cache module")
from utils.cache import TTLCache, normalize_key, content_hash, STATIC, SEMI_STATIC, DYNAMIC, REALTIME

c = TTLCache("test")
c.set("a", "hello", 5)
check("set/get works", c.get("a") == "hello")
check("missing key returns None", c.get("missing") is None)
c.set("b", "bye", 1)
time.sleep(1.1)
check("entry expires after TTL", c.get("b") is None)
check("remaining_ttl on expired is None", c.remaining_ttl("b") is None)
rem = c.remaining_ttl("a")
check("remaining_ttl is positive int", isinstance(rem, int) and rem > 0, repr(rem))
check("purge_expired removes expired", c.purge_expired() == 0)  # already auto-deleted
check("normalize_key lowercases", normalize_key("  HELLO  ") == "hello")
check("content_hash is 12 chars", len(content_hash("test")) == 12)
check("STATIC > SEMI_STATIC > DYNAMIC > REALTIME",
      STATIC > SEMI_STATIC > DYNAMIC > REALTIME > 0)
try:
    from utils.cache import ANSWER_TTL
    check("ANSWER_TTL=None removed from module", False, "Still exported!")
except ImportError:
    check("ANSWER_TTL=None removed from module", True)

# ── 2. Shell output capture ───────────────────────────────────────────────────
print("\n[2] Shell capture + command cache")
from utils.shell import capture_shell_output

out, ok = capture_shell_output("Write-Output 'ALOA_TEST'", ttl=60)
check("basic capture works", ok and "ALOA_TEST" in out, repr(out))

t0 = time.monotonic()
out2, ok2 = capture_shell_output("Write-Output 'ALOA_TEST'", ttl=60)
hit_ms = (time.monotonic() - t0) * 1000
check("cache hit is near-instant (<10ms)", hit_ms < 10, f"{hit_ms:.1f}ms")
check("cache hit returns same value", out2 == out, repr(out2))

out3, ok3 = capture_shell_output("Write-Output 'FRESH_RUN'", ttl=0)
check("ttl=0 bypasses cache and runs fresh", "FRESH_RUN" in out3, repr(out3))

out_fail, ok_fail = capture_shell_output("exit 1", ttl=0)
check("failed command returns ok=False", not ok_fail)

out_timeout, ok_to = capture_shell_output("Start-Sleep -Seconds 20", ttl=0)
check("timeout returns False", not ok_to, repr(out_timeout))

# ── 3. Pre-match patterns ─────────────────────────────────────────────────────
print("\n[3] Quick pre-match")
from llm.planner import quick_pre_match

cases = [
    ("what is the host name of my laptop", STATIC),
    ("what is my ip address", DYNAMIC),
    ("how much RAM do I have", SEMI_STATIC),
    ("tell me my cpu model", STATIC),
    ("how much free disk space", SEMI_STATIC),
    ("what windows version am i on", STATIC),
    ("who am i", STATIC),
    ("how long has the pc been on", SEMI_STATIC),
    ("show running processes", REALTIME),
    ("what time is it", REALTIME),
    ("show battery", DYNAMIC),
]

for q, expected_ttl in cases:
    r = quick_pre_match(q)
    label = q[:40]
    check(
        f"pre_match: {label!r}",
        r is not None and r["_ttl"] == expected_ttl and r["safe"] is True,
        f"got {r}"
    )

no_match = quick_pre_match("install python please")
check("pre_match returns None for actions", no_match is None)

# ── 4. Return type of interpret_output (must be 2-tuple) ─────────────────────
print("\n[4] interpret_output return type")
from llm.planner import interpret_output
from utils.cache import answer_cache

# Manually prime the cache to avoid requiring Ollama
answer_cache.set("ans:test q:abc123456789", "Cached answer.", 60)
# Call with matching hash
import hashlib
fake_output = "fake_output_data"
fake_hash = hashlib.md5(fake_output.encode()).hexdigest()[:12]
answer_cache.set(f"ans:test q:{fake_hash}", "Mocked answer", 60)

result = interpret_output("test q", fake_output, ttl=60)
check("interpret_output returns a 2-tuple", isinstance(result, tuple) and len(result) == 2,
      repr(result))
check("interpret_output[0] is str", isinstance(result[0], str))
check("interpret_output[1] is bool (from_cache)", isinstance(result[1], bool))
check("returns from_cache=True on hit", result[1] is True)

# ── 5. classify_and_plan structure ───────────────────────────────────────────
print("\n[5] classify_and_plan structure")
from llm.planner import classify_and_plan

plan = classify_and_plan("what is my hostname")
check("plan has 'type' key", "type" in plan)
check("plan has 'safe' key", "safe" in plan)
check("plan has 'commands' key", "commands" in plan)
check("plan has '_ttl' key", "_ttl" in plan)
check("plan has '_source' key", "_source" in plan)
check("commands is list", isinstance(plan["commands"], list))
check("hostname plan is safe=True", plan["safe"] is True)
check("hostname _source is pre_match", plan["_source"] == "pre_match")

# ── 6. Agent imports without crashing ────────────────────────────────────────
print("\n[6] Agent import")
try:
    from core.agent import Agent
    a = Agent()
    check("Agent initialises without error", True)
except Exception as e:
    check("Agent initialises without error", False, str(e))

# ── 7. extract_commands regex ────────────────────────────────────────────────
print("\n[7] extract_commands")
from core.smart_executor import extract_commands

text = "Here is the plan:\n```powershell\nGet-Process\nStop-Service xyz\n```"
cmds = extract_commands(text)
check("extracts powershell block", len(cmds) == 1)
check("block contains commands", "Get-Process" in cmds[0])

text2 = "No code here."
check("returns empty list when no block", extract_commands(text2) == [])

# ── 8. RAM command unit check ────────────────────────────────────────────────
print("\n[8] RAM command sanity")
plan_ram = quick_pre_match("how much ram do i have")
check("RAM plan has 2 commands", len(plan_ram["commands"]) == 2)
check("RAM free command divides by 1024 not 1MB",
      "/ 1024" in plan_ram["commands"][1] and "1MB" not in plan_ram["commands"][1])

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
total = PASS + FAIL
print(f"Results: {PASS}/{total} PASSED  |  {FAIL} FAILED")
print("=" * 60)
if FAIL > 0:
    sys.exit(1)
