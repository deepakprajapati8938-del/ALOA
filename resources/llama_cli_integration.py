"""
Simplified Llama.cpp CLI Integration for ALOA
Direct CLI interface - works immediately with your existing installation
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional

class LlamaCLIIntegration:
    """Direct llama.cpp CLI integration for ALOA"""
    
    def __init__(self):
        self.llama_cli = Path("X:/ExternalSoftDAta/llama.cpp/build/bin/Release/llama-cli.exe")
        self.model_path = Path("X:/ExternalSoftDAta/llama.cpp/models/gemma-4-E2B-it-UD-Q3_K_XL.gguf")
        
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate text using llama-cli directly"""
        if not self.llama_cli.exists():
            return "Error: llama-cli.exe not found"
        
        if not self.model_path.exists():
            return "Error: Model file not found"
        
        try:
            cmd = [
                str(self.llama_cli),
                "-m", str(self.model_path),
                "-p", prompt,
                "-n", str(max_tokens),
                "--temp", str(temperature),
                "--gpu-layers", "-1",
                "-c", "2048",
                "--batch-size", "512",
                "--top-p", "0.9",
                "--repeat-penalty", "1.1"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.llama_cli.parent)
            )
            
            if result.returncode == 0:
                # Extract the generated text from output
                output_lines = result.stdout.strip().split('\n')
                # Skip the prompt if it's echoed back
                if output_lines and output_lines[0].strip() == prompt.strip():
                    output_lines = output_lines[1:]
                return '\n'.join(output_lines).strip()
            else:
                return f"CLI Error: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Error: Generation timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_info(self) -> Dict:
        """Get information about the CLI integration"""
        return {
            "integration_type": "CLI-based",
            "llama_cli": str(self.llama_cli),
            "model_path": str(self.model_path),
            "model_exists": self.model_path.exists(),
            "cli_exists": self.llama_cli.exists(),
            "model_size": f"{self.model_path.stat().st_size / (1024**3):.1f}GB" if self.model_path.exists() else "N/A",
            "optimization": "GTX 1650 4GB VRAM - Direct CLI"
        }

# Global instance
llama_cli = LlamaCLIIntegration()
