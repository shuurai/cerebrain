# Cerebra

Terminal-based **brain matrix** CLI: multiple brain parts (emotional, logical, memory, inspiration) working as one — **SOUL**, **MEMORY**, **USER**, **TOOLS**. ASCII visualization, init-before-use, and HTTP/WebSocket API for integration (e.g. Nanobot, OpenClawd).

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

Run from the repo root without registering the package with pip:

```bash
cd cerebra.cli

# Install only dependencies (no cerebra package install)
pip install typer rich pyyaml requests httpx

# Run the CLI via the module; PYTHONPATH points Python at the package
PYTHONPATH=. python -m cerebra --help
PYTHONPATH=. python -m cerebra init --name dev --llm openrouter
PYTHONPATH=. python -m cerebra chat
```

Or use a venv and the same pattern:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install typer rich pyyaml requests httpx
PYTHONPATH=. python -m cerebra status
```

Editable install (`pip install -e .`) is still useful if you want the `cerebra` command on your PATH and live code reload while developing.

## Quick start

1. **Initialize** (required before first use). Run the interactive wizard:

   ```bash
   cerebra init
   ```

   You will be asked (with sensible defaults):

   - **Brain name** — e.g. `default`
   - **LLM provider** — `openrouter`, `openai`, `anthropic`, `ollama`, or `local`
   - **If OpenRouter:** API key (masked), then model choice (e.g. minimax/minimax-m2, anthropic/claude-3.5-sonnet)
   - **If OpenAI/Anthropic:** optional API key (can add later in config)
   - **Max tokens per reply** — default `8192`
   - **Temperature** — default `0.7` (0.0–1.0)
   - **API server port** — default `17971` (used by `cerebra serve`)
   - **Soul:** primary traits, values, communication style (used to build SOUL.md)

   Config (`~/.cerebra/config.yaml`) is written with `default_brain`, `providers.<name>.api_key`, `llm_defaults` (max_tokens, temperature), and `server.port`. You can re-run `cerebra init` to create another brain or pass `--name` / `--llm` to pre-fill those answers.

2. **Chat** (terminal with ASCII brain view):

   ```bash
   cerebra chat
   cerebra chat --brain my-brain --no-visual   # terminal only
   ```

3. **API server** (for Nanobot / OpenClawd). Port comes from config (set at init) or 17971:

   ```bash
   cerebra serve
   # or: cerebra serve --port 17971
   ```

   **HTTP:** `POST /v1/chat` with `{"content": "..."}`. **WebSocket:** `ws://host:17971/v1/stream` — send JSON `{"content": "..."}`, receive `{"reply": "..."}`; one agent per connection (stateful). Requires FastAPI/uvicorn (install with `pip install fastapi uvicorn` for full server features).

4. **Other commands:**

   ```bash
   cerebra status
   cerebra list
   cerebra diagnose --brain my-brain
   cerebra export --brain my-brain --format json
   ```

## Project layout

- `cerebra/core/` — Brain matrix (orchestration), emotional self, logical self (LLM), memory (short-term + optional ChromaDB long-term), inspiration engine
- `cerebra/cli/` — Typer CLI
- `cerebra/ui/` — ASCII visualization, consciousness stream, metrics dashboard
- `cerebra/api/` — HTTP server (POST /v1/chat uses brain matrix)
- `cerebra/scripts/` — Init wizard, diagnostics
- `cerebra/utils/` — Config, persistence, natural randomness (ANU/random.org fallback)

**Optional:** `pip install cerebra[chromadb]` for long-term vector memory (self-contained ChromaDB).

Data and config: `~/.cerebra/` (workspace, brain_states, config.yaml).

### Configuration

Config file: `~/.cerebra/config.yaml`. After `cerebra init` it is written with **all** supported keys (so you can edit anything manually). Example shape:

```yaml
# Cerebra config — edit any value. All supported keys are listed.

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
  anthropic:
    api_key: ""
    api_base: "https://api.anthropic.com"
  ollama:
    api_key: ""
    api_base: "http://localhost:11434"
  local:
    api_key: ""
    api_base: "http://localhost:5000"
```

- **server.port** — default port for `cerebra serve` (set during init).
- **llm_defaults** — max_tokens and temperature (set during init; used as defaults for new brains and as fallback).
- **providers.<name>.api_key** — set during init when you enter an API key; you can also edit the file later.
- Brains use the model, max_tokens, and temperature chosen at init; the LLM client reads the API key from `providers.<provider>.api_key`.

## License

MIT.
