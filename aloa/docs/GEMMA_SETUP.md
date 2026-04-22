# Gemma-4 Local Setup Guide for ALOA

Integrating Gemma-4 locally allows ALOA to rank as one of the most private and powerful autonomous agents on your machine.

## 1. Local LLM Options

ALOA supports multiple ways to run Gemma locally. **Ollama** is the recommended method for ease of use.

### Option A: Ollama (Recommended)
1. Install [Ollama](https://ollama.com/).
2. Pull the Gemma model (example uses `gemma4:e2b`):
   ```bash
   ollama pull gemma4:e2b
   ```
3. Ensure Ollama is running.

### Option B: llama.cpp
1. **Requirements**: [GitHub Repository](https://github.com/ggerganov/llama.cpp)
2. **Gemma GGUF**: Download quantization from HuggingFace.
3. **Start Server**:
   ```bash
   ./server -m models/gemma-4-it.gguf --port 8080 -c 4096
   ```

## 2. Configure ALOA

1. Copy `.env.example` to `.env` in the `aloa/` directory.
2. Set the following variables:
   ```env
   # For Ollama (Preferred)
   OLLAMA_URL=http://localhost:11434/v1/chat/completions
   OLLAMA_MODEL=gemma4:e2b

   # For llama.cpp (Alternative)
   LLAMA_CPP_URL=http://localhost:8080/v1/chat/completions
   LOCAL_LLM_MODEL=gemma-4
   ```

## 4. Verification

Run ALOA:
```powershell
python aloa/main.py
```
Type any command (e.g., `health`). ALOA will now use your local Gemma-4 instance to analyze the request and draft the implementation plan.

> [!IMPORTANT]
> If your local server is under heavy load, you might see a timeout. ALOA will automatically fail-over to **OpenRouter** or **Groq** if configured.
