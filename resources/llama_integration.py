"""
Llama.cpp Integration for ALOA
Optimized for GTX 1650 4GB VRAM - Using native llama.cpp executable
"""

import os
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Generator
import requests

class LlamaALOA:
    """Native llama.cpp integration optimized for ALOA features"""
    
    def __init__(self):
        self.llama_executable = Path("X:/ExternalSoftDAta/llama.cpp/build/bin/Release/llama-cli.exe")
        self.llama_server = Path("X:/ExternalSoftDAta/llama.cpp/build/bin/Release/llama-server.exe")
        self.model_configs = self._get_gtx1650_configs()
        self.models_dir = Path("X:/ExternalSoftDAta/llama.cpp/models")
        self.models_dir.mkdir(exist_ok=True)
        self.server_process = None
        self.server_port = 8080
        self.server_url = f"http://localhost:{self.server_port}"
        
    def _get_gtx1650_configs(self) -> Dict[str, Dict]:
        """Optimized model configurations for GTX 1650 4GB VRAM"""
        return {
            # Existing model - already available!
            "gemma-2b": {
                "filename": "gemma-4-E2B-it-UD-Q3_K_XL.gguf",
                "n_ctx": 2048,
                "n_batch": 512,
                "n_gpu_layers": -1,  # Use all GPU layers
                "max_tokens": 1024,
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "use_case": ["app_manager", "quick_commands", "system_status", "general"]
            },
            # Lightweight models for fast responses
            "llama3.2-1b": {
                "filename": "llama-3.2-1b-instruct.Q4_K_M.gguf",
                "n_ctx": 2048,
                "n_batch": 512,
                "n_gpu_layers": -1,  # Use all GPU layers
                "max_tokens": 512,
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "use_case": ["app_manager", "quick_commands", "system_status"]
            },
            # Medium model for complex tasks
            "qwen2.5-3b": {
                "filename": "qwen2.5-3b-instruct.Q4_K_M.gguf", 
                "n_ctx": 4096,
                "n_batch": 256,
                "n_gpu_layers": -1,
                "max_tokens": 1024,
                "temperature": 0.6,
                "top_p": 0.8,
                "repeat_penalty": 1.1,
                "use_case": ["code_healer", "cloud_healer", "exam_pilot"]
            },
            # Small model for text processing
            "phi3-mini": {
                "filename": "phi-3-mini-4k-instruct.Q4_K_M.gguf",
                "n_ctx": 4096,
                "n_batch": 256,
                "n_gpu_layers": -1,
                "max_tokens": 1024,
                "temperature": 0.5,
                "top_p": 0.8,
                "repeat_penalty": 1.1,
                "use_case": ["attendance_hub", "lecture_notes", "resume_engine"]
            }
        }
    
    def start_server(self, model_name: str) -> bool:
        """Start llama.cpp server with specified model"""
        if self.server_process and self.server_process.poll() is None:
            # Server already running
            return True
            
        if model_name not in self.model_configs:
            return False
            
        config = self.model_configs[model_name]
        model_path = self.models_dir / config["filename"]
        
        if not model_path.exists():
            print(f"Model file not found: {model_path}")
            return False
        
        try:
            print(f"Starting llama.cpp server with {model_name}...")
            cmd = [
                str(self.llama_server),
                "-m", str(model_path),
                "--host", "127.0.0.1",
                "--port", str(self.server_port),
                "-c", str(config["n_ctx"]),
                "--gpu-layers", str(config["n_gpu_layers"]),
                "--batch-size", str(config["n_batch"]),
                "--temp", str(config["temperature"]),
                "--top-p", str(config["top_p"]),
                "--repeat-penalty", str(config["repeat_penalty"])
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is responsive
            try:
                response = requests.get(f"{self.server_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"Server started successfully with {model_name}")
                    return True
            except:
                pass
            
            print("Server failed to start")
            return False
            
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop the llama.cpp server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
            print("Server stopped")
    
    def download_model(self, model_name: str) -> bool:
        """Download a model if not exists"""
        if model_name not in self.model_configs:
            return False
            
        config = self.model_configs[model_name]
        model_path = self.models_dir / config["filename"]
        
        if model_path.exists():
            return True
            
        print(f"Please download {config['filename']} from HuggingFace and place in {self.models_dir}")
        return False
    
    def load_model(self, model_name: str) -> bool:
        """Load a model via server"""
        return self.start_server(model_name)
    
    def get_best_model_for_task(self, task: str) -> Optional[str]:
        """Get the best model for a specific ALOA feature"""
        # Check if gemma-2b is available (it's already there!)
        gemma_path = self.models_dir / "gemma-4-E2B-it-UD-Q3_K_XL.gguf"
        if gemma_path.exists() and task in self.model_configs["gemma-2b"]["use_case"]:
            return "gemma-2b"
            
        for model_name, config in self.model_configs.items():
            if task in config["use_case"]:
                return model_name
        return "gemma-2b"  # Default fallback
    
    def generate(self, prompt: str, task: str = "general", **kwargs) -> str:
        """Generate text using the best model for the task"""
        model_name = self.get_best_model_for_task(task)
        
        if not self.load_model(model_name):
            return f"Error: Could not load model {model_name}"
        
        config = self.model_configs[model_name]
        
        try:
            payload = {
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", config["max_tokens"]),
                "temperature": kwargs.get("temperature", config["temperature"]),
                "top_p": kwargs.get("top_p", config["top_p"]),
                "repeat_penalty": kwargs.get("repeat_penalty", config["repeat_penalty"]),
                "stop": ["<|end|>", "<|eot_id|>", "\n\n\n"],
                "echo": False
            }
            
            response = requests.post(f"{self.server_url}/completion", json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("content", "").strip()
            
        except Exception as e:
            return f"Generation error: {e}"
    
    def stream_generate(self, prompt: str, task: str = "general", **kwargs) -> Generator[str, None, None]:
        """Stream generation for real-time responses"""
        model_name = self.get_best_model_for_task(task)
        
        if not self.load_model(model_name):
            yield f"Error: Could not load model {model_name}"
            return
        
        config = self.model_configs[model_name]
        
        try:
            payload = {
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", config["max_tokens"]),
                "temperature": kwargs.get("temperature", config["temperature"]),
                "top_p": kwargs.get("top_p", config["top_p"]),
                "repeat_penalty": kwargs.get("repeat_penalty", config["repeat_penalty"]),
                "stop": ["<|end|>", "<|eot_id|>", "\n\n\n"],
                "echo": False,
                "stream": True
            }
            
            response = requests.post(f"{self.server_url}/completion", json=payload, stream=True, timeout=30)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if "content" in data:
                            yield data["content"]
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            yield f"Generation error: {e}"
    
    def unload_model(self, model_name: str):
        """Unload a model to free VRAM"""
        self.stop_server()
        print(f"Unloaded {model_name}")
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        server_running = self.server_process and self.server_process.poll() is None
        
        info = {
            "loaded_models": ["gemma-2b"] if server_running else [],
            "available_models": list(self.model_configs.keys()),
            "models_directory": str(self.models_dir),
            "gpu_layers": -1,  # Using all GPU layers
            "optimization": "GTX 1650 4GB VRAM - Native llama.cpp",
            "server_running": server_running,
            "server_port": self.server_port,
            "llama_executable": str(self.llama_executable),
            "existing_model": "gemma-4-E2B-it-UD-Q3_K_XL.gguf (2.7GB)"
        }
        return info

# Global instance
llama_aloa = LlamaALOA()
