# Cerebra

Terminal-based brain agent CLI with **SOUL**, **MEMORY**, **USER**, and **TOOLS**. ASCII visualization, init-before-use, and HTTP/WebSocket API for integration (e.g. Nanobot, OpenClawd).

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

1. **Initialize** (required before first use):

   ```bash
   cerebra init
   # or: cerebra init --name my-brain --llm openrouter
   ```

   Supported `--llm` providers: **openrouter** (default), openai, anthropic, ollama, local.

   **OpenRouter** (recommended): one API key for many models (Claude, GPT-4, etc.). Get a key at [openrouter.ai/keys](https://openrouter.ai/keys), then add to `~/.cerebra/config.yaml`:

   ```yaml
   providers:
     openrouter:
       api_key: "sk-or-v1-..."
   # Optional: override default model for a brain (e.g. anthropic/claude-3.5-sonnet)
   ```

2. **Chat** (terminal with ASCII brain view):

   ```bash
   cerebra chat
   cerebra chat --brain my-brain --no-visual   # terminal only
   ```

3. **API server** (for Nanobot / OpenClawd; default port 17971):

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

- `cerebra/core/` — Brain agent, emotional self, logical self (LLM), memory (short-term + optional ChromaDB long-term), inspiration engine
- `cerebra/cli/` — Typer CLI
- `cerebra/ui/` — ASCII visualization, consciousness stream, metrics dashboard
- `cerebra/api/` — HTTP server (POST /v1/chat uses brain agent)
- `cerebra/scripts/` — Init wizard, diagnostics
- `cerebra/utils/` — Config, persistence, natural randomness (ANU/random.org fallback)

**Optional:** `pip install cerebra[chromadb]` for long-term vector memory (self-contained ChromaDB).

Data and config: `~/.cerebra/` (workspace, brain_states, config.yaml).

### Configuration

Config file: `~/.cerebra/config.yaml`. Example with OpenRouter:

```yaml
default_brain: default

providers:
  openrouter:
    api_key: "sk-or-v1-..."
  openai:
    api_key: "sk-..."
  anthropic:
    api_key: "sk-ant-..."
```

Brains created with `--llm openrouter` use the OpenRouter endpoint and the model set at init (e.g. `anthropic/claude-3.5-sonnet`). The API key is read from `providers.openrouter.api_key`.

## License

MIT.
