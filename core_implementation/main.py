"""
ALOA Core Implementation — Intelligent CLI Entry Point
Replaces number-menu with natural language intent matching.
"""
import sys
import os
import re
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

# ── Feature imports ──────────────────────────────────────────────────────────
from features import feature_1
from features.feature_2  import runner as feature_2_runner
from features.feature_3  import runner as feature_3_runner
from features.feature_4  import runner as feature_4_runner
from features.feature_5  import runner as feature_5_runner
from features.feature_6  import runner as feature_6_runner
from features.feature_7  import runner as feature_7_runner
from features.feature_8  import runner as feature_8_runner
from features.feature_9  import runner as feature_9_runner
from features.feature_10 import runner as feature_10_runner

from utils.memory import aloa_memory

# ── NLP pre-match table ──────────────────────────────────────────────────────
# (regex_pattern, feature_number, runner_callable, display_name)
FEATURE_PATTERNS: list[tuple[str, int, callable, str]] = [
    (r"app|install|uninstall|open|launch|software",          1,  lambda: feature_1.run(),         "App Manager"),
    (r"system|doctor|health|junk|clean|ram|cpu|memory|disk", 2,  feature_2_runner.run,            "System Doctor"),
    (r"attend|excel|sheet|absent|student|class",             3,  feature_3_runner.run,            "Attendance Automator"),
    (r"youtube|lecture|note|video|transcript",               4,  feature_4_runner.run,            "YouTube Note Generator"),
    (r"exam|quiz|question|mcq|pilot|solve",                  5,  feature_5_runner.run,            "Exam Pilot"),
    (r"code|debug|fix|error|heal|bug",                       6,  feature_6_runner.run,            "Code Healer"),
    (r"cloud|github|repo|remote|ci|deploy",                  7,  feature_7_runner.run,            "Cloud Healer"),
    (r"deploy|vercel|render|push|release",                   8,  feature_8_runner.run,            "Auto-Deployer"),
    (r"resume|cv|profile|job|apply|generate",                9,  feature_9_runner.run,            "Resume Engine"),
    (r"radar|news|intel|brief|daily|trend",                  10, feature_10_runner.run,           "ALOA Radar"),
]


def match_feature(user_input: str) -> tuple[int, callable, str] | None:
    """Match natural language input to a feature. Returns (number, runner, name)."""
    text = user_input.strip().lower()
    # Direct number selection still works
    if text.isdigit():
        n = int(text)
        if 1 <= n <= 10:
            _, num, runner, name = next(
                ((p, i, r, nm) for p, i, r, nm in FEATURE_PATTERNS if i == n), (None,)*4
            )
            return (n, runner, name) if runner else None

    for pattern, num, runner, name in FEATURE_PATTERNS:
        if re.search(pattern, text):
            return num, runner, name
    return None


def show_menu():
    print("\n" + "=" * 60)
    print("  ALOA — Available Features")
    print("=" * 60)
    for _, num, _, name in FEATURE_PATTERNS:
        print(f"  [{num:>2}] {name}")
    print("  [ X] Exit")
    print("-" * 60)
    print("  Tip: Type a number OR describe what you want naturally.")
    print('  e.g. "fix my code", "check attendance", "deploy to vercel"')
    print()


def main():
    print()
    print("=" * 60)
    print("      THE ALOA — Agentic AI Assistant (v2.1)")
    print("      Phase 2: Intelligence Layer Active")
    print("=" * 60)

    while True:
        show_menu()
        try:
            user_input = input("  ALOA ❯ ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  [Force Exit] ALOA Terminated by User.")
            sys.exit()

        if not user_input:
            continue

        if user_input.upper() == "X":
            print("  Goodbye! Shutting down ALOA...")
            break

        if user_input.lower() == "memory":
            print("\n  [Semantic Memory - Current Facts]")
            facts = aloa_memory.query_related("User") + aloa_memory.query_related("ALOA")
            if not facts:
                print("  (Empty memory)")
            for f in set(facts):
                print(f"  • {f}")
            continue

        if user_input.lower() == "forget":
            import networkx as nx
            aloa_memory.graph = nx.MultiDiGraph()
            aloa_memory.save()
            print("  ✅ Memory cleared.")
            continue

        match = match_feature(user_input)
        if match:
            num, runner, name = match
            print(f"\n  ▶ Launching: {name}\n")
            try:
                result = runner()
                if result == "exit":
                    break
            except KeyboardInterrupt:
                print(f"\n  [{name}] Interrupted. Returning to menu...")
            except Exception as e:
                print(f"\n  ❌ {name} crashed: {e}")
        else:
            print(f"\n  ❌ Didn't understand '{user_input}'.")
            print("  Try typing a number (1–10) or a keyword like 'install', 'notes', 'radar'.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  [Force Exit] ALOA Terminated by User.")
        sys.exit()
