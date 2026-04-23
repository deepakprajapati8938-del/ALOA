"""
ALOA LLM Provider Chain — single fallback chain used by ALL features.

Priority order:
  1. Groq  (fastest, free tier)
  2. OpenRouter (cloud fallback)
  3. Gemini (for features that need it)

Usage:
    from utils.providers import call_llm
    answer = call_llm("Your prompt here")
"""
import os
import json
import requests
from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> Optional[str]:
        pass


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, prompt: str, system: str = "") -> Optional[str]:
        if not self.api_key:
            return None
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            r = requests.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages, "temperature": 0.2},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            return None


class OpenRouterProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "google/gemini-2.0-flash-001"):
        self.api_key = api_key
        self.model = model
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str, system: str = "") -> Optional[str]:
        if not self.api_key:
            return None
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            r = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://aloa.local",
                },
                json={"model": self.model, "messages": messages, "temperature": 0.2},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            return None


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str, system: str = "") -> Optional[str]:
        if not self.api_key:
            return None
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}",
                json={"contents": [{"parts": [{"text": full_prompt}]}]},
                timeout=20,
            )
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return None


def _build_chain() -> list[LLMProvider]:
    chain = []
    groq_key = os.getenv("GROQ_API_KEY", "")
    or_key   = os.getenv("OPENROUTER_API_KEY", "")
    gem_key  = os.getenv("GEMINI_API_KEY_1", "")

    if groq_key:
        chain.append(GroqProvider(groq_key))
    if or_key:
        chain.append(OpenRouterProvider(or_key))
    if gem_key:
        chain.append(GeminiProvider(gem_key))
    return chain


def call_llm(prompt: str, system: str = "", use_cache: bool = True, ttl: int = 60, use_memory: bool = False) -> str:
    """
    Call the LLM fallback chain. Caches results by prompt hash.

    Args:
        prompt:     The user/task prompt.
        system:     Optional system instruction.
        use_cache:  Set False to force a fresh LLM call.
        ttl:        Cache TTL in seconds.
        use_memory: If True, queries ALOAMemory for relevant context.

    Returns:
        LLM response string, or an error message if all providers fail.
    """
    from utils.cache import llm_cache, content_hash
    from utils.memory import aloa_memory

    # 1. Memory Injection (Context Retrieval)
    if use_memory:
        mem_context = aloa_memory.get_semantic_context(prompt)
        if mem_context:
            system = f"{system}\n{mem_context}"

    cache_key = f"llm:{content_hash(system + prompt)}"

    if use_cache:
        cached = llm_cache.get(cache_key)
        if cached is not None:
            return cached

    chain = _build_chain()
    for provider in chain:
        result = provider.generate(prompt, system)
        if result:
            if use_cache:
                llm_cache.set(cache_key, result, ttl)
            return result

    return "⚠️ All LLM providers failed or are unconfigured. Check your .env keys."
