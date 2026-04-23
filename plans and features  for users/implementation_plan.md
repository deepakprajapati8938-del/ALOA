# Integrating Memory & Caching into ALOA Generation

You are completely right—having the features is one thing, but right now they aren't actively being injected into the Llama generation cycle! To make your AI truly context-aware and efficient, I will integrate Semantic Memory, Working Memory (Conversation History), and the Caching layers directly into the `llama_generate` and `llama_stream` endpoints.

## Proposed Changes

### 1. Enable Working Memory (Conversation History)
Currently, every request to `/api/llama/generate` is treated as a brand new interaction. We will add a simple in-memory session tracker in `server.py`.
- **Change:** Update `LlamaGenerateRequest` to accept an optional `session_id`.
- **Change:** Maintain a rolling buffer of the last 5 interactions for each `session_id`.
- **Benefit:** ALOA will remember what you asked 2 minutes ago within the same chat session.

### 2. Inject Semantic Memory (Long-term Knowledge)
The `aloa_memory` graph exists but is dormant. We will hook it into the prompt pipeline.
- **Change:** Before sending `req.prompt` to Llama.cpp, we will run `aloa_memory.get_semantic_context(req.prompt)`.
- **Change:** If relevant facts (like "User prefers Python") are found based on keywords in the prompt, they will be quietly injected at the top of the system prompt.
- **Benefit:** ALOA gets long-term persistent context without needing to read the entire memory graph every time.

### 3. Elevate the Caching Layer
While `optimized_llama.py` has an internal cache, it's more efficient to cache at the FastAPI level to avoid processing the request entirely.
- **Change:** Add an `api_cache` lookup in `/api/llama/generate`.
- **Benefit:** Instant sub-millisecond responses for repeated queries, bypassing the Llama lock entirely.

## User Review Required

> [!IMPORTANT]
> - For **Semantic Memory**, currently facts have to be added manually via `aloa_memory.add_fact(...)`. Would you like me to also implement an auto-extraction feature where the LLM automatically saves facts it learns about you into the graph, or should we keep it manual for now to prevent junk data?
> - For **Working Memory**, I plan to keep it in-memory (RAM) for now. If the server restarts, short-term history is cleared, but Semantic Memory (saved to JSON) persists. Does this sound good?

Please approve this plan and I will wire these memory systems into the core generation logic immediately!
