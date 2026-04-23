"""
Performance Configuration for ALOA Backend
Defines caching TTLs, GPU limits, and system thresholds
"""
import time
from typing import Dict, Any

class PerformanceConfig:
    def __init__(self):
        self.CACHE_CONFIG = {
            "ttl_settings": {
                "llama_responses": 1800,  # 30 min cache for common questions
                "system_stats": 60,       # 1 minute cache for stats
                "radar_brief": 300,       # 5 min cache for radar
            }
        }
        
    def get_gpu_optimization(self) -> Dict[str, int]:
        """Return GTX 1650 4GB specific config"""
        return {
            "gpu_layers": 20,         # Safe limit for 4GB VRAM
            "max_vram_mb": 3500,      # Leave 500MB for OS display
        }
        
    def get_optimized_llama_settings(self) -> Dict[str, Any]:
        """Settings for loading llama-cpp-python"""
        import os
        return {
            "filename": os.getenv("LLM_MODEL_FILENAME", "gemma-4-E2B-it-UD-Q3_K_XL.gguf"),
            "n_ctx": 2048,
            "n_batch": 512,
            "n_threads": 4,
            "n_threads_batch": 4,
            "use_mmap": True,
            "use_mlock": False,
            "embedding": False,
            "rope_scaling_type": -1,
            "rope_freq_base": 10000.0,
            "rope_freq_scale": 1.0,
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {"response_times": {}}
        
    def record_response_time(self, operation: str, duration: float):
        if operation not in self.metrics["response_times"]:
            self.metrics["response_times"][operation] = []
        self.metrics["response_times"][operation].append(duration)
        
    def get_performance_summary(self) -> Dict[str, Any]:
        summary = {}
        for op, times in self.metrics["response_times"].items():
            if times:
                summary[op] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times)
                }
        return summary

performance_config = PerformanceConfig()
performance_monitor = PerformanceMonitor()
