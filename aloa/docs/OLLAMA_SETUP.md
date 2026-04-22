# Ollama Setup Guide for ALOA

Ollama provides an incredibly easy way to run large language models locally. ALOA is pre-configured to work with Ollama's OpenAI-compatible API.

## 1. Install Ollama
Download and install Ollama from [ollama.com](https://ollama.com).

## 2. Download a Model
For the best experience with ALOA's planning phase, we recommend **Gemma** or **Llama 3**.

```bash
ollama run gemma:7b
```

## 3. Configure ALOA

1. Copy `.env.example` to `.env` in the `aloa/` directory.
2. Set the following variables:
   ```env
   OLLAMA_URL=http://localhost:11434/v1/chat/completions
   OLLAMA_MODEL=gemma:7b
   ```

## 4. Why use Ollama with ALOA?
- **Speed**: Ollama's server is highly optimized for local inference.
- **Ease of Use**: No need to manage GGUF files manually; Ollama handles model versions for you.
- **Privacy**: All processing happens entirely on your machine.

## 5. Troubleshooting
If ALOA fails to connect to Ollama:
- Ensure Ollama is running (`ollama list` should show your models).
- Verify the URL is correct (default is `http://localhost:11434/v1/chat/completions`).
- If you see timeouts, your machine might be under heavy load. ALOA will automatically fall back to cloud providers if configured.
