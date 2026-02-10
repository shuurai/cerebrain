# Cerebra

Terminal-based **brain matrix** CLI: five parts (emotional, logical, memory, inspiration, consciousness) working as one. **SOUL**, **MEMORY**, **USER**, **TOOLS**. Init-before-use, simple terminal chat, self-awareness with live state, default **self-skills** (internal APIs), and HTTP/WebSocket API for integration (e.g. Nanobot, OpenClawd).

## Install

```bash
# PyPI (when published)
pip install cerebra

# uv
uv tool install cerebra

# From source
git clone https://github.com/yourusername/cerebra.cli.git && cd cerebra.cli
pip install -e .
```

**Platforms:** Linux, macOS. Python 3.11+.

### Test locally without installing

```bash
cd cerebra.cli
pip install typer rich pyyaml requests httpx
PYTHONPATH=. python -m cerebra --help
PYTHONPATH=. python -m cerebra init --name dev --llm openrouter
PYTHONPATH=. python -m cerebra chat
```

Or with a venv: `python -m venv .venv`, `source .venv/bin/activate`, then the same `pip install` and `PYTHONPATH=. python -m cerebra ...`. Editable install (`pip install -e .`) gives you the `cerebra` command on your PATH.

## Quick start

1. **Initialize** (required before first use):

   ```bash
   cerebra init
   ```

   You’ll be prompted for: brain name, LLM provider (openrouter, openai, anthropic, ollama, local), API key (when needed), model, max tokens, temperature, server port, and **Soul** (traits, values, communication style → SOUL.md). Config is written to `~/.cerebra/config.yaml`.

2. **Chat** (simple terminal; boot messages then prompt/response):

   ```bash
   cerebra chat
   cerebra chat --brain my-brain --no-visual
   ```

   On start you see “Booting ….” and “Loading into Cerebra Matrix Terminal ….” then a normal chat loop. Replies are kept short (terminal / ship-computer style).

3. **API server** (for Nanobot / OpenClawd). Port from config or 17971:

   ```bash
   cerebra serve
   cerebra serve --port 17971
   ```

   **HTTP:** `POST /v1/chat` with `{"content": "..."}`. **WebSocket:** `ws://host:17971/v1/stream` — send `{"content": "..."}`, receive `{"reply": "..."}`; one agent per connection. Requires FastAPI/uvicorn for full server features.

4. **Other commands:**

   ```bash
   cerebra status
   cerebra list
   cerebra diagnose --brain my-brain
   cerebra export --brain my-brain --format json
   ```

## How it works

- **Brain matrix:** One agent orchestrates five parts: **Emotional self** (mood), **Logical self** (LLM reasoning), **Memory** (short-term turns + optional ChromaDB long-term), **Inspiration** (randomness/sparks), **Consciousness** (integration; influenced by a pulse/heartbeat). The system prompt always includes a description of this and a **live state** line (mood, memory counts, inspiration, pulse, stream activity) so Cerebra can answer about itself and its current state.

- **System prompt:** Built from SOUL (identity), USER (context), TOOLS (from workspace TOOLS.md), relevant long-term memory, **brain matrix (what you are)**, **current state (live)**, **self skills (internal APIs)**, and a **response style** (1–3 short sentences, terse, terminal-style).

- **Self-skills (internal APIs):** Cerebra has default skills that interact with its own state. They are listed in the prompt and callable via `agent.run_skill(name, **kwargs)` (e.g. from your code or future tool-calling). Default skills:
  - **get_mood** — Current emotional/mood state.
  - **get_memory_summary** — Short-term and long-term memory counts.
  - **get_memory_recall** — Query long-term memory (`query`, `k`).
  - **spark_inspiration** — Trigger inspiration engine once; returns a spark if any.
  - **get_pulse** — Current heartbeat/pulse (0..1).
  - **get_consciousness_state** — Activity levels of all streams.
  - **get_thought_stream** — Recent thought lines from a stream (`stream`, `n`).

  Skills are defined in `cerebra/core/self_skills.py`; the agent can describe them and use results when tool-calling is enabled.

- **Response style:** Replies are kept concise (1–3 sentences, minimal words, no preamble), like a terminal or ship computer.

## Project layout

- **cerebra/core/** — Brain agent (orchestration), emotional self, logical self (LLM), memory (short-term + optional ChromaDB long-term), inspiration engine, **self_skills** (default internal APIs), consciousness (stub).
- **cerebra/cli/** — Typer CLI (init, chat, serve, status, list, diagnose, export).
- **cerebra/ui/** — Terminal chat UI (simple loop); optional buffer/managers code parked for future fancy terminal.
- **cerebra/api/** — HTTP server (POST /v1/chat, WebSocket /v1/stream).
- **cerebra/scripts/** — Init wizard, diagnostics.
- **cerebra/utils/** — Config, persistence, natural randomness (ANU/random.org fallback).

**Optional:** `pip install cerebra[chromadb]` for long-term vector memory (self-contained ChromaDB).

**Data and config:** `~/.cerebra/` (workspace, brain_states, config.yaml).

## Configuration

Config: `~/.cerebra/config.yaml`. After `cerebra init` it contains all supported keys. Example:

```yaml
default_brain: default
server:
  port: 17971
llm_defaults:
  max_tokens: 8192
  temperature: 0.7
providers:
  openrouter:
    api_key: "sk-or-v1-..."
    api_base: "https://openrouter.ai/api/v1"
  openai:
    api_key: ""
    api_base: "https://api.openai.com/v1"
  # ... anthropic, ollama, local
```

- **server.port** — Default for `cerebra serve`.
- **llm_defaults** — max_tokens and temperature (used as defaults for new brains).
- **providers.<name>.api_key** — Set at init or edit the file; the LLM client reads from here.

## License

MIT.
