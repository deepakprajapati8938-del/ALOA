import os
from llama_cpp import Llama
from pathlib import Path

models_dir = Path("X:/ExternalSoftDAta/llama.cpp/models")
model_path = models_dir / "gemma-4-E2B-it-UD-Q3_K_XL.gguf"

if not model_path.exists():
    print(f"Model not found: {model_path}")
    exit(1)

print(f"Attempting to load model from {model_path}")
print("Configuring with n_gpu_layers=20 (GTX 1650 4GB optimization)...")

try:
    llm = Llama(
        model_path=str(model_path),
        n_gpu_layers=20,
        verbose=True
    )
    print("\nSUCCESS: Model loaded successfully.")
    print(f"Model detail: {llm.model_path}")
    
    # Check if GPU is actually used
    # In llama-cpp-python, if verbose=True, it prints to stderr.
    
    response = llm("Hii! How are you?", max_tokens=10)
    print(f"Response: {response['choices'][0]['text']}")

except Exception as e:
    print(f"\nFAILURE: Could not load model. Error: {e}")
