"""Brain creation wizard (cerebra init)."""

from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from cerebra.config.model_templates import get_llm_state_for_brain
from cerebra.utils.config_loader import (
    ensure_dirs,
    get_brain_workspace,
    get_config_path,
    load_config,
    save_config,
)
from cerebra.utils.persistence import save_brain_state

console = Console()

# OpenRouter models for interactive selection
OPENROUTER_MODELS = [
    "minimax/minimax-m2",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
]

DEFAULT_USER = """# User

Information about the user goes here.

## Preferences

- Communication style: (casual/formal)
- Timezone: (your timezone)
- Language: (your preferred language)
"""

DEFAULT_TOOLS = """# Tools

Tools available to this brain. Extended over time via config and TOOLS.md.
"""


def _build_soul(traits: str, values: str, style: str, name: str) -> str:
    """Build SOUL.md content from user inputs."""
    traits_list = ", ".join(t.strip() for t in traits.split(",") if t.strip()) or "curious, helpful"
    values_list = ", ".join(v.strip() for v in values.split(",") if v.strip()) or "truth, simplicity"
    return f"""# Soul

I am {name}, a brain matrix — emotional, logical, memory, and inspiration parts working as one.

## Personality

- {traits_list}

## Values

- {values_list}

## Communication Style

- {style.strip() or "Clear and helpful"}
"""


class BrainWizard:
    """Interactive wizard: LLM provider, API key, model, port, name, soul, then create brain and config."""

    def create_brain(self, name: str | None = None, llm: str | None = None) -> None:
        """Run interactive wizard; use name/llm as defaults when provided."""
        ensure_dirs()
        config_path = get_config_path()
        cfg = load_config()

        # ----- 1. Brain name -----
        default_name = (name or "").strip() or "default"
        brain_name = Prompt.ask("Brain name", default=default_name).strip() or default_name
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in brain_name).strip("_") or "default"
        brain_name = safe_name

        # ----- 2. LLM provider -----
        default_llm = (llm or "").strip().lower() or "openrouter"
        llm_provider = Prompt.ask(
            "LLM provider",
            default=default_llm,
            choices=["openrouter", "openai", "anthropic", "ollama", "local"],
        )

        # ----- 3. Provider-specific: API key and model -----
        api_key = ""
        model_override = None
        if llm_provider == "openrouter":
            console.print("[dim]Get an API key at https://openrouter.ai/keys[/dim]")
            api_key = Prompt.ask("OpenRouter API key", password=True, default="").strip()
            console.print("Select a model:")
            for i, m in enumerate(OPENROUTER_MODELS, 1):
                console.print(f"  [cyan]{i}[/cyan]. {m}")
            choice = Prompt.ask("Model number or full model id", default="1").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(OPENROUTER_MODELS):
                model_override = OPENROUTER_MODELS[int(choice) - 1]
            elif choice:
                model_override = choice
        elif llm_provider == "openai":
            api_key = Prompt.ask("OpenAI API key (optional, can add later in config)", default="").strip()
        elif llm_provider == "anthropic":
            api_key = Prompt.ask("Anthropic API key (optional, can add later in config)", default="").strip()

        # ----- 4. max_tokens and temperature -----
        llm_defaults = cfg.get("llm_defaults") or {}
        max_tokens_default = str(llm_defaults.get("max_tokens") or 8192)
        temp_default = str(llm_defaults.get("temperature") or 0.7)
        max_tokens_str = Prompt.ask("Max tokens per reply", default=max_tokens_default).strip()
        temp_str = Prompt.ask("Temperature (0.0–1.0)", default=temp_default).strip()
        try:
            max_tokens = int(max_tokens_str) if max_tokens_str else 8192
        except ValueError:
            max_tokens = 8192
        try:
            temperature = float(temp_str) if temp_str else 0.7
            temperature = max(0.0, min(1.0, temperature))
        except ValueError:
            temperature = 0.7

        # ----- 5. Port -----
        port_default = str(cfg.get("server", {}).get("port") or cfg.get("port") or 17971)
        port_str = Prompt.ask("API server default port", default=port_default).strip()
        try:
            server_port = int(port_str) if port_str else 17971
        except ValueError:
            server_port = 17971

        # ----- 6. Soul: traits, values, style -----
        console.print("\n[bold]Soul (personality)[/bold] — short answers are fine.")
        traits = Prompt.ask("Primary traits (comma-separated)", default="curious, analytical, creative, empathetic").strip()
        values = Prompt.ask("Values (comma-separated)", default="truth, simplicity, growth, helpfulness").strip()
        style = Prompt.ask("Communication style", default="metaphorical yet precise").strip()

        # ----- 7. Build config and workspace -----
        workspace = get_brain_workspace(brain_name)
        workspace.mkdir(parents=True, exist_ok=True)

        llm_state = get_llm_state_for_brain(llm_provider)
        if model_override:
            llm_state["model"] = model_override
        llm_state["max_tokens"] = max_tokens
        llm_state["temperature"] = temperature

        if llm_provider == "openrouter" and api_key:
            cfg.setdefault("providers", {})["openrouter"] = {"api_key": api_key}
        if llm_provider == "openai" and api_key:
            cfg.setdefault("providers", {})["openai"] = {"api_key": api_key}
        if llm_provider == "anthropic" and api_key:
            cfg.setdefault("providers", {})["anthropic"] = {"api_key": api_key}

        cfg["default_brain"] = brain_name
        cfg["server"] = cfg.get("server") or {}
        cfg["server"]["port"] = server_port
        cfg["llm_defaults"] = {"max_tokens": max_tokens, "temperature": temperature}
        save_config(cfg)

        soul_content = _build_soul(traits, values, style, brain_name)
        (workspace / "SOUL.md").write_text(soul_content)
        (workspace / "USER.md").write_text(DEFAULT_USER)
        (workspace / "TOOLS.md").write_text(DEFAULT_TOOLS)
        (workspace / "memory").mkdir(exist_ok=True)
        (workspace / "memory" / "MEMORY.md").write_text("# Long-term Memory\n\n(Important facts and preferences)\n")

        save_brain_state(
            brain_name,
            {
                "name": brain_name,
                "workspace": str(workspace),
                "llm": llm_state,
                "memory": {"short_term_capacity": 7},
            },
        )

        console.print(f"\n[green]✓[/green] Brain [cyan]{brain_name}[/cyan] created at {workspace}")
        console.print(f"[green]✓[/green] Config saved to {config_path}")
        if llm_provider == "openrouter" and not api_key:
            console.print("[yellow]Add OpenRouter API key to config and get a key: https://openrouter.ai/keys[/yellow]")
        console.print(f"\nNext: [cyan]cerebra chat[/cyan]  or  [cyan]cerebra serve[/cyan] (port {server_port})")
