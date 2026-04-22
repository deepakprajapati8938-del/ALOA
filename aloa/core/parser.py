"""
ALOA Command Parser — Extracts intent and target from user input.

Supports natural-language-like commands:
  "install maven"         → intent=install, target=maven
  "why is my laptop slow" → intent=diagnose
  "uninstall notepad++"   → intent=uninstall, target=notepad++
  "health"                → intent=health
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedCommand:
    """Parsed representation of a user command."""
    intent: str              # e.g., install, uninstall, search, health, diagnose, etc.
    target: Optional[str]    # e.g., app name like "maven"
    raw: str                 # original user input
    flags: dict              # optional flags extracted


# ── Intent Keyword Maps ────────────────────────────────────────────

INTENT_PATTERNS: list[tuple[str, list[str]]] = [
    # Application Lifecycle
    ("install",    ["install", "setup", "set up", "add", "get"]),
    ("uninstall",  ["uninstall", "remove", "delete app", "deep uninstall", "deep remove"]),
    ("search",     ["search", "find app", "find software", "look for"]),
    ("verify",     ["verify", "check install", "is installed", "check if"]),
    ("path",       ["add to path", "fix path", "path config", "update path", "configure path"]),

    # System Health
    ("health",     ["health", "system health", "overview", "status", "system status"]),
    ("ram",        ["ram", "memory", "memory usage"]),
    ("cpu",        ["cpu", "processor", "cpu usage"]),
    ("disk",       ["disk", "storage", "disk usage", "disk space", "space"]),
    ("startup",    ["startup", "boot", "startup programs", "boot programs"]),
    ("unused",     ["unused", "unused apps", "unused programs", "bloat", "bloatware"]),
    ("diagnose",   ["diagnose", "why is", "why my", "slow", "lagging", "freezing",
                    "performance", "bottleneck", "what's wrong", "whats wrong"]),
    ("suggest",    ["suggest", "suggestions", "recommend", "optimize", "fix it", "fix"]),
    ("cleanup",    ["cleanup", "clean up", "clean", "clear cache", "clear temp"]),

    # General Task & Development
    ("git",        ["git", "clone", "pull", "push", "commit", "checkout", "branch"]),
    ("file",       ["file", "folder", "directory", "mkdir", "ls", "list", "copy", "move", "rename"]),
    ("task",       ["task", "do", "run", "execute", "perform", "make", "create", "initialize"]),
    ("system_cmd", ["ipconfig", "ping", "netstat", "tasklist", "whoami", "hostname"]),

    # General Meta
    ("help",       ["help", "commands", "what can you do", "?"],),
    ("exit",       ["exit", "quit", "bye", "close"]),
]


def parse(user_input: str) -> ParsedCommand:
    """Parse a user input string into a structured command.

    Uses keyword matching to determine intent, then extracts the target.
    If no static intent matches, the command is treated as a `smart_task`
    for the LLM to handle.
    """
    raw = user_input.strip()
    if not raw:
        return ParsedCommand(intent="unknown", target=None, raw="", flags={})

    text = raw.lower()

    # Try to match intent patterns
    matched_intent = "smart_task"  # Default to smart_task instead of unknown
    matched_phrase = ""

    for intent, phrases in INTENT_PATTERNS:
        for phrase in phrases:
            if phrase in text and len(phrase) > len(matched_phrase):
                matched_intent = intent
                matched_phrase = phrase

    # Extract target: preserve original casing from `raw`
    # We locate the matched phrase in the lowercased `text`, then strip the
    # corresponding slice from `raw` so the target keeps the user's casing
    # (e.g. "install Visual Studio Code" → target = "Visual Studio Code").
    target = None
    if matched_phrase:
        phrase_start = text.find(matched_phrase)
        if phrase_start != -1:
            # Rebuild raw without the matched phrase, preserving case
            raw_remainder = (raw[:phrase_start] + raw[phrase_start + len(matched_phrase):]).strip()
        else:
            raw_remainder = raw
        # Remove common filler words (case-insensitive)
        raw_remainder = re.sub(
            r"(?i)\b(please|for me|now|properly|correctly|my|the|a|an|is|it|on|this|"
            r"laptop|computer|pc|system|machine|can you|could you)\b",
            "", raw_remainder
        ).strip()
        # Clean up extra spaces
        raw_remainder = re.sub(r"\s+", " ", raw_remainder).strip()
        if raw_remainder:
            target = raw_remainder

    # Extract flags (e.g., --force, --deep)
    flags = {}
    flag_matches = re.findall(r"--([\w-]+)", raw)
    for flag in flag_matches:
        flags[flag] = True

    return ParsedCommand(
        intent=matched_intent,
        target=target,
        raw=raw,
        flags=flags,
    )
