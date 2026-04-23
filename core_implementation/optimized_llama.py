"""
Optimized Llama.cpp Integration for ALOA
High-performance configuration for GTX 1650 4GB VRAM
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Generator
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from llama_cpp import Llama
from performance_config import performance_config, performance_monitor

class OptimizedLlamaALOA:
    """High-performance llama.cpp integration"""
    
    def __init__(self):
        self.model = None
        self.model_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.model_config = performance_config.get_optimized_llama_settings()
        self.gpu_config = performance_config.get_gpu_optimization()
        self.models_dir = Path(os.getenv("LLM_MODELS_DIR", "X:/ExternalSoftDAta/llama.cpp/models"))
        self.cache_enabled = True
        self.response_cache = {}
        
    def load_model_async(self, model_name: str = "gemma-2b") -> bool:
        """Asynchronous model loading with optimized settings"""
        if self.model is not None:
            return True
            
        config = self.model_config
        model_path = self.models_dir / config["filename"]
        
        if not model_path.exists():
            print(f"Model not found: {model_path}")
            return False
        
        try:
            print(f"Loading optimized model: {model_name}")
            start_time = time.time()
            
            # Optimized model loading
            self.model = Llama(
                model_path=str(model_path),
                n_ctx=config["n_ctx"],
                n_batch=config["n_batch"],
                n_gpu_layers=self.gpu_config["gpu_layers"],
                n_threads=config["n_threads"],
                n_threads_batch=config["n_threads_batch"],
                use_mmap=config["use_mmap"],
                use_mlock=config["use_mlock"],
                embedding=config["embedding"],
                rope_scaling_type=config["rope_scaling_type"],
                rope_freq_base=config["rope_freq_base"],
                rope_freq_scale=config["rope_freq_scale"],
                verbose=False
            )
            
            load_time = time.time() - start_time
            print(f"Model loaded in {load_time:.2f}s")
            performance_monitor.record_response_time("model_load", load_time)
            return True
            
        except Exception as e:
            print(f"Model loading failed: {e}")
            return False
    
    def generate_optimized(self, prompt: str, task: str = "general", **kwargs) -> str:
        """Optimized text generation with caching"""
        # Check cache first
        cache_key = f"{hash(prompt)}_{task}_{kwargs.get('max_tokens', 512)}"
        if self.cache_enabled and cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            if time.time() - cached_response["timestamp"] < performance_config.CACHE_CONFIG["ttl_settings"]["llama_responses"]:
                return cached_response["response"]
        
        if not self.model:
            if not self.load_model_async():
                return "Error: Model not loaded"
        
        # Optimized generation parameters
        config = self.model_config
        max_tokens = min(kwargs.get("max_tokens", config["max_tokens"]), config["max_tokens"])
        
        try:
            start_time = time.time()
            
            with self.model_lock:
                response = self.model(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=kwargs.get("temperature", config["temperature"]),
                    top_p=kwargs.get("top_p", config["top_p"]),
                    repeat_penalty=kwargs.get("repeat_penalty", config["repeat_penalty"]),
                    stop=["<|end|>", "<|eot_id|>", "\n\n\n", "User:", "Human:"],
                    echo=False,
                    stream=False
                )
            
            generation_time = time.time() - start_time
            result = response["choices"][0]["text"].strip()
            
            # Cache the response
            if self.cache_enabled:
                self.response_cache[cache_key] = {
                    "response": result,
                    "timestamp": time.time()
                }
            
            # Record performance metrics
            performance_monitor.record_response_time("llama_generate", generation_time)
            
            return result
            
        except Exception as e:
            return f"Generation error: {e}"
    
    def generate_stream_optimized(self, prompt: str, task: str = "general", **kwargs) -> Generator[str, None, None]:
        """Optimized streaming generation"""
        if not self.model:
            if not self.load_model_async():
                yield "Error: Model not loaded"
                return
        
        config = self.model_config
        max_tokens = min(kwargs.get("max_tokens", config["max_tokens"]), config["max_tokens"])
        
        try:
            with self.model_lock:
                for chunk in self.model(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=kwargs.get("temperature", config["temperature"]),
                    top_p=kwargs.get("top_p", config["top_p"]),
                    repeat_penalty=kwargs.get("repeat_penalty", config["repeat_penalty"]),
                    stop=["<|end|>", "<|eot_id|>", "\n\n\n", "User:", "Human:"],
                    echo=False,
                    stream=True
                ):
                    yield chunk["choices"][0]["text"]
                    
        except Exception as e:
            yield f"Generation error: {e}"
    
    def unload_model(self):
        """Unload model to free VRAM"""
        with self.model_lock:
            if self.model:
                del self.model
                self.model = None
                print("Model unloaded - VRAM freed")
    
    def clear_cache(self):
        """Clear response cache"""
        self.response_cache.clear()
        print("Response cache cleared")
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            "model_loaded": self.model is not None,
            "cache_size": len(self.response_cache),
            "cache_enabled": self.cache_enabled,
            "model_config": self.model_config,
            "gpu_config": self.gpu_config,
            "performance_metrics": performance_monitor.get_performance_summary()
        }
    
    def optimize_for_task(self, task: str) -> Dict[str, Any]:
        """Get task-specific optimizations"""
        task_configs = {
            "app_manager": {
                "max_tokens": 256,
                "temperature": 0.3,
                "top_p": 0.8,
                "cache_ttl": 600  # 10 minutes
            },
            "quick_commands": {
                "max_tokens": 128,
                "temperature": 0.2,
                "top_p": 0.7,
                "cache_ttl": 300  # 5 minutes
            },
            "system_status": {
                "max_tokens": 512,
                "temperature": 0.5,
                "top_p": 0.9,
                "cache_ttl": 60   # 1 minute
            },
            "general": {
                "max_tokens": 1024,
                "temperature": 0.7,
                "top_p": 0.9,
                "cache_ttl": 1800 # 30 minutes
            }
        }
        
        return task_configs.get(task, task_configs["general"])

# Global optimized instance
optimized_llama = OptimizedLlamaALOA()
