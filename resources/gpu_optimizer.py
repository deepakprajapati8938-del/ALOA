"""
NVIDIA GTX 1650 GPU Optimization for ALOA
Maximize performance for 4GB VRAM
"""

import subprocess
import time
from pathlib import Path

class GPUOptimizer:
    """Optimize NVIDIA GTX 1650 settings for ALOA"""
    
    def __init__(self):
        self.nvidia_smi = "nvidia-smi"
        self.target_gpu = 0  # GTX 1650
    
    def check_gpu_status(self):
        """Check current GPU status"""
        try:
            result = subprocess.run([
                self.nvidia_smi,
                "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 7:
                        return {
                            "name": parts[0],
                            "memory_total": int(parts[1]),
                            "memory_used": int(parts[2]),
                            "memory_free": int(parts[3]),
                            "gpu_utilization": int(parts[4]),
                            "temperature": int(parts[5]),
                            "power_draw": float(parts[6])
                        }
            return None
        except Exception as e:
            print(f"GPU status check failed: {e}")
            return None
    
    def set_power_mode(self, mode="prefer maximum performance"):
        """Set GPU power mode for maximum performance"""
        try:
            result = subprocess.run([
                self.nvidia_smi,
                "-i", str(self.target_gpu),
                "-pm", "1"  # 1 = maximum performance
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("GPU power mode set to maximum performance")
                return True
            else:
                print(f"Power mode setting failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Power mode setting error: {e}")
            return False
    
    def set_clocks(self, memory_clock=None, graphics_clock=None):
        """Set GPU clock speeds (if supported)"""
        try:
            commands = []
            
            if memory_clock:
                commands.extend(["-ac", str(memory_clock)])
            if graphics_clock:
                commands.extend(["-gc", str(graphics_clock)])
            
            if commands:
                cmd = [self.nvidia_smi, "-i", str(self.target_gpu)] + commands
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"GPU clocks set successfully")
                    return True
                else:
                    print(f"Clock setting failed: {result.stderr}")
                    return False
            return True
        except Exception as e:
            print(f"Clock setting error: {e}")
            return False
    
    def optimize_for_llama(self):
        """Apply GTX 1650 optimizations for llama.cpp"""
        print("=== Optimizing GTX 1650 for ALOA ===")
        
        # Check current status
        status = self.check_gpu_status()
        if status:
            print(f"GPU: {status['name']}")
            print(f"Memory: {status['memory_used']}MB / {status['memory_total']}MB ({status['memory_free']}MB free)")
            print(f"Utilization: {status['gpu_utilization']}%")
            print(f"Temperature: {status['temperature']}°C")
            print(f"Power: {status['power_draw']}W")
        
        # Set power mode
        print("\n1. Setting power mode to maximum performance...")
        self.set_power_mode()
        
        # GTX 1650 specific optimizations
        print("\n2. Applying GTX 1650 optimizations...")
        
        # Set optimal memory clock (if supported)
        self.set_clocks(memory_clock=5000)  # 5000 MHz for GTX 1650
        
        # Wait for settings to apply
        time.sleep(2)
        
        # Check optimized status
        print("\n3. Checking optimized status...")
        optimized_status = self.check_gpu_status()
        if optimized_status:
            print(f"Optimized Memory Usage: {optimized_status['memory_used']}MB / {optimized_status['memory_total']}MB")
            print(f"Available for Llama.cpp: {optimized_status['memory_free']}MB")
            
            # Calculate optimal GPU layers for 4GB VRAM
            available_vram = optimized_status['memory_free']
            optimal_layers = min(35, max(20, available_vram // 100))  # ~100MB per layer
            
            print(f"\nRecommended GPU Layers: {optimal_layers}")
            print(f"VRAM Allocation: ~{optimal_layers * 100}MB for model")
            print(f"Remaining VRAM: {available_vram - (optimal_layers * 100)}MB for system")
            
            return {
                "optimal_gpu_layers": optimal_layers,
                "available_vram": available_vram,
                "recommended_batch_size": min(512, available_vram // 8),
                "recommended_context": min(4096, available_vram // 2)
            }
        
        return None
    
    def create_windows_power_profile(self):
        """Create Windows power profile for maximum performance"""
        print("\n=== Windows Power Optimization ===")
        
        try:
            # Set power plan to High Performance
            result = subprocess.run([
                "powercfg",
                "/setactive",
                "SCHEME_MIN"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("Windows power plan set to High Performance")
                return True
            else:
                print(f"Power plan setting failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Power plan error: {e}")
            return False
    
    def disable_gpu_throttling(self):
        """Disable GPU throttling for consistent performance"""
        print("\n=== Disabling GPU Throttling ===")
        
        try:
            # Set GPU performance level
            result = subprocess.run([
                self.nvidia_smi,
                "-i", str(self.target_gpu),
                "-ac", "875",  # Memory clock
                "-gc", "1920"   # Graphics clock for GTX 1650
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("GPU throttling disabled - clocks set to maximum")
                return True
            else:
                print(f"Throttling disable failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Throttling disable error: {e}")
            return False

def run_gpu_optimization():
    """Run complete GPU optimization"""
    optimizer = GPUOptimizer()
    
    # Optimize GPU
    gpu_settings = optimizer.optimize_for_llama()
    
    # Optimize Windows power
    optimizer.create_windows_power_profile()
    
    # Disable throttling
    optimizer.disable_gpu_throttling()
    
    print("\n=== GPU Optimization Complete ===")
    if gpu_settings:
        print("Optimized settings:")
        for key, value in gpu_settings.items():
            print(f"  {key}: {value}")
    
    return gpu_settings

if __name__ == "__main__":
    run_gpu_optimization()
