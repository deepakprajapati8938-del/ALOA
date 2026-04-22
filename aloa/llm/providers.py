import os
import requests
import json
from abc import ABC, abstractmethod
from typing import Optional

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> Optional[str]:
        pass

class LlamaCppProvider(LLMProvider):
    def __init__(self, url: str, model_name: str = "local-model", api_key: str = "no-key"):
        self.url = url
        self.model_name = model_name
        self.api_key = api_key

    def generate(self, prompt: str) -> Optional[str]:
        try:
            response = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,  # Lower temperature for planning
                },
                timeout=180  # Increased timeout for local processing on CPU
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return None

class OpenRouterProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            response = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "google/gemini-2.0-flash-001", # High quality efficient model
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return None

class GroqProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, prompt: str) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            response = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return None

class OllamaProvider(LlamaCppProvider):
    """Specialized provider for Ollama's OpenAI-compatible endpoint."""
    def __init__(self, url: str = "http://localhost:11434/v1/chat/completions", model_name: str = "gemma:7b"):
        super().__init__(url, model_name=model_name, api_key="ollama")

def get_fallback_chain() -> list[LLMProvider]:
    """Initialize the fallback chain based on environment variables."""
    chain = []
    
    # 1. Ollama (Higher priority local if configured)
    ollama_url = os.getenv("OLLAMA_URL")
    if ollama_url:
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma:7b")
        chain.append(OllamaProvider(url=ollama_url, model_name=ollama_model))

    # 2. Local llama.cpp / Generic Local
    llama_url = os.getenv("LLAMA_CPP_URL")
    if llama_url:
        llama_model = os.getenv("LOCAL_LLM_MODEL", "gemma-4")
        llama_key = os.getenv("LOCAL_LLM_API_KEY", "no-key")
        chain.append(LlamaCppProvider(llama_url, model_name=llama_model, api_key=llama_key))
        
    # 3. OpenRouter
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        chain.append(OpenRouterProvider(or_key))
        
    # 4. Groq (Fail-safe)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        chain.append(GroqProvider(groq_key))
        
    return chain
