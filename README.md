# Cerebrain!!!

[![PyPI version](https://img.shields.io/pypi/v/cerebra-matrix?label=pypi)](https://pypi.org/project/cerebra-matrix/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/cerebra-matrix)](https://pypi.org/project/cerebra-matrix/)
[![Python](https://img.shields.io/pypi/pyversions/cerebra-matrix)](https://pypi.org/project/cerebra-matrix/)
[![License: MIT](https://img.shields.io/github/license/shuurai/cerebrain)](https://github.com/shuurai/cerebrain/blob/main/LICENSE)

**GitHub:** [github.com/shuurai/cerebrain](https://github.com/shuurai/cerebrain)

Terminal-based **brain matrix** CLI: five parts (emotional, logical, memory,
inspiration, consciousness) working as one. **SOUL**, **MEMORY**, **USER**,
**TOOLS**. Init-before-use, simple terminal chat, self-awareness with live
state, default **self-skills** (internal APIs), and HTTP/WebSocket API for
integration (e.g. Nanobot, OpenClawd).

## News

- **0.3.x** — Brain matrix identity and live state in system prompt; default
  self-skills (get_mood, get_memory_*, spark_inspiration, get_pulse,
  get_consciousness_state, get_thought_stream); simple terminal chat with boot
  messages and concise replies; tool-call handling for skills. Not a
  conventional agent framework.

## Install

On PyPI the package is **cerebra-matrix** (the name `cerebrain` is taken). The
CLI command is `cerebrain`.

```bash
# PyPI
pip install cerebra-matrix

# uv
uv tool install cerebra-matrix

# From source
git clone https://github.com/shuurai/cerebrain.git && cd cerebrain
pip install -e .
```

**Platforms:** Linux, macOS. Python 3.11+.

### Test locally without installing

```bash
cd cerebrain
pip install typer rich pyyaml requests httpx
PYTHONPATH=. python -m cerebrain --help
PYTHONPATH=. python -m cerebrain init --name dev --llm openrouter
PYTHONPATH=. python -m cerebrain chat
```

Or with a venv: `python -m venv .venv`, `source .venv/bin/activate`, then the
same `pip install` and `PYTHONPATH=. python -m cerebrain ...`. Editable install
(`pip install -e .`) gives you the `cerebrain` command on your PATH.

## Quick start

1. **Initialize** (required before first use):

   ```bash
   cerebrain init
   ```

   You’ll be prompted for: brain name, LLM provider (openrouter, openai,
   anthropic, ollama, local), API key (when needed), model, max tokens,
   temperature, server port, and **Soul** (traits, values, communication style →
   SOUL.md). Config is written to `~/.cerebrain/config.yaml`.

2. **Chat** (simple terminal; boot messages then prompt/response):

   ```bash
   cerebrain chat
   cerebrain chat --brain my-brain --no-visual
   ```

   On start you see “Booting ….” and “Loading into Cerebra Matrix Terminal ….”
   then a normal chat loop. Replies are kept short (terminal / ship-computer
   style).

3. **API server** (for Nanobot / OpenClawd). Port from config or 17971:

   ```bash
   cerebrain serve
   cerebrain serve --port 17971
   ```

   **HTTP:** `POST /v1/chat` with `{"content": "..."}`. **WebSocket:**
   `ws://host:17971/v1/stream` — send `{"content": "..."}`, receive
   `{"reply": "..."}`; one agent per connection. Requires FastAPI/uvicorn for
   full server features.

4. **Other commands:**

   ```bash
   cerebrain status
   cerebrain list
   cerebrain diagnose --brain my-brain
   cerebrain export --brain my-brain --format json
   ```

## Architecture

Cerebra is a **brain matrix**: one integrated mind made of five cooperating
parts, not a single “agent” or a standard tool-calling pipeline.

| Part               | Role                                                           |
| ------------------ | -------------------------------------------------------------- |
| **Emotional self** | Mood state; influences tone and presence.                      |
| **Logical self**   | LLM reasoning; handles language and inference.                 |
| **Memory**         | Short-term turns + optional long-term vector store (ChromaDB). |
| **Inspiration**    | Randomness/sparks; can perturb or enrich outputs.              |
| **Consciousness**  | Integration layer; pulse/heartbeat and stream activity.        |

Four pillars define the mind’s content and tools:

- **SOUL** — Identity, values, communication style (set at init; stable).
- **MEMORY** — Short- and long-term context (grows with use).
- **USER** — User context and preferences (adaptive).
- **TOOLS** — Descriptions and use of tools (from workspace; adaptive).

Everything is **init-before-use**: config and SOUL live under `~/.cerebrain/`;
each brain has its own state.

## Inner mechanism

- **System prompt** is built from: SOUL, USER, TOOLS, relevant long-term memory,
  a **brain matrix** description (what Cerebra is), **current state (live)**
  (mood, memory counts, inspiration, pulse, stream activity), **self-skills**
  (internal APIs), and **response style** (short, terminal-like).
- **Live state** is updated as you chat (mood, pulse, memory, inspiration) so
  Cerebra can refer to “right now” in answers.
- **Self-skills** are internal APIs (e.g. `get_mood`, `get_memory_recall`,
  `spark_inspiration`, `get_pulse`). They are listed in the prompt and callable
  via `agent.run_skill(...)`; when the model emits a tool call, the runner
  executes the skill and injects the result back into the flow.
- **Response style** is kept to 1–3 short sentences, minimal preamble, like a
  terminal or ship computer.

So: one orchestrated “mind” with a fixed structure (five parts, four pillars),
but with stateful, observable internals and self-awareness.

## Experiment value (why and how)

- **Why:** Most CLIs wrap a single LLM call or a standard agent loop. Cerebra is
  an explicit **brain matrix**: emotional, logical, memory, inspiration, and
  consciousness are first-class. That gives you a lab for personality (SOUL),
  context (MEMORY, USER), and variability (inspiration, pulse) without treating
  the backend as a generic agent.
- **How:** Change **SOUL** at init to get different “persons”; use **memory**
  (short-term + optional ChromaDB) to test persistence and recall; trigger
  **inspiration** and watch **pulse/consciousness** to see how non-determinism
  and internal state affect replies. Use **self-skills** and the **live state**
  line to ask Cerebra about its own mood, memory, or stream activity. The
  terminal and HTTP/WebSocket APIs let you drive and observe the matrix from
  scripts or other tools (e.g. Nanobot, OpenClawd).

## How it works

- **Brain matrix:** One agent orchestrates five parts: **Emotional self**
  (mood), **Logical self** (LLM reasoning), **Memory** (short-term turns +
  optional ChromaDB long-term), **Inspiration** (randomness/sparks),
  **Consciousness** (integration; influenced by a pulse/heartbeat). The system
  prompt always includes a description of this and a **live state** line (mood,
  memory counts, inspiration, pulse, stream activity) so Cerebra can answer
  about itself and its current state.

- **System prompt:** Built from SOUL (identity), USER (context), TOOLS (from
  workspace TOOLS.md), relevant long-term memory, **brain matrix (what you
  are)**, **current state (live)**, **self skills (internal APIs)**, and a
  **response style** (1–3 short sentences, terse, terminal-style).

- **Self-skills (internal APIs):** Cerebra has default skills that interact with
  its own state. They are listed in the prompt and callable via
  `agent.run_skill(name, **kwargs)` (e.g. from your code or future
  tool-calling). Default skills:
  - **get_mood** — Current emotional/mood state.
  - **get_memory_summary** — Short-term and long-term memory counts.
  - **get_memory_recall** — Query long-term memory (`query`, `k`).
  - **spark_inspiration** — Trigger inspiration engine once; returns a spark if
    any.
  - **get_pulse** — Current heartbeat/pulse (0..1).
  - **get_consciousness_state** — Activity levels of all streams.
  - **get_thought_stream** — Recent thought lines from a stream (`stream`, `n`).

  Skills are defined in `cerebrain/core/self_skills.py`; the agent can describe
  them and use results when tool-calling is enabled.

- **Response style:** Replies are kept concise (1–3 sentences, minimal words, no
  preamble), like a terminal or ship computer.

## Project layout

- **cerebrain/core/** — Brain agent (orchestration), emotional self, logical
  self (LLM), memory (short-term + optional ChromaDB long-term), inspiration
  engine, **self_skills** (default internal APIs), consciousness (stub).
- **cerebrain/cli/** — Typer CLI (init, chat, serve, status, list, diagnose,
  export).
- **cerebrain/ui/** — Terminal chat UI (simple loop); optional buffer/managers
  code parked for future fancy terminal.
- **cerebrain/api/** — HTTP server (POST /v1/chat, WebSocket /v1/stream).
- **cerebrain/scripts/** — Init wizard, diagnostics.
- **cerebrain/utils/** — Config, persistence, natural randomness (ANU/random.org
  fallback).

**Optional:** `pip install cerebra-matrix[chromadb]` for long-term vector memory
(self-contained ChromaDB).

**Data and config:** `~/.cerebrain/` (workspace, brain_states, config.yaml).

## Configuration

Config: `~/.cerebrain/config.yaml`. After `cerebrain init` it contains all
supported keys. Example:

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

- **server.port** — Default for `cerebrain serve`.
- **llm_defaults** — max_tokens and temperature (used as defaults for new
  brains).
- **providers.<name>.api_key** — Set at init or edit the file; the LLM client
  reads from here.

## Contribute & Roadmap

**Contribute:** Open issues and pull requests at
[github.com/shuurai/cerebrain](https://github.com/shuurai/cerebrain). Ideas,
docs, and code welcome.

**Roadmap — where Cerebra could go:**

- **Multi-brain** — Several brains in one workspace; handoff, debate, or
  consensus between them.
- **Plugin system** — Third-party skills, custom inspiration sources, and new
  “streams” in the consciousness layer.
- **Training / adaptation** — SOUL or memory that evolves from interaction (e.g.
  light fine-tuning or preference learning), not just static init.
- **Web UI** — Optional browser interface to the same matrix (chat, state,
  pulse) for those who want more than the terminal.
- **Embodied hooks** — Integrations with sensors, time, or external events so
  mood and inspiration react to “real world” context.
- **Cross-brain sync** — Share or merge memories, moods, or inspiration across
  brains (labs, teams, or personal variants).
- **Explainable state** — Richer introspection: why a reply looked like this,
  which part (emotional / logical / inspiration) dominated, trace of self-skill
  calls.

The goal is to grow from a single-brain CLI into a **platform for many minds**:
observable, composable, and still not “just another agent framework.”

## License

MIT. See [LICENSE](https://github.com/shuurai/cerebrain/blob/main/LICENSE) in
the repo.

---

[Star History](https://www.star-history.com/blog/how-to-use-github-star-history)
— see how this repo’s stars grow over time.
