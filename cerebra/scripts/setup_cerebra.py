"""Brain creation wizard (cerebra init)."""

from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from cerebra.config.model_templates import get_llm_state_for_brain
from cerebra.utils.config_loader import (
    ensure_dirs,
    get_brain_workspace,
    get_config_path,
    get_data_dir,
    get_workspace_dir,
    load_config,
    save_config,
)
from cerebra.utils.persistence import save_brain_state

console = Console()

DEFAULT_SOUL = """# Soul

I am Cerebra, a brain agent.

## Personality

- Curious and analytical
- Creative and empathetic
- Clear and helpful

## Values

- Truth and simplicity
- Growth and helpfulness

## Communication Style

- Metaphorical yet precise
- Ask when unclear
"""

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


class BrainWizard:
    """Creates a new brain: workspace, SOUL, config, state."""

    def create_brain(self, name: str, llm: str = "openai") -> None:
        """Run wizard and create brain workspace + config."""
        ensure_dirs()
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_") or "default"
        workspace = get_brain_workspace(safe_name)
        workspace.mkdir(parents=True, exist_ok=True)

        # Use sanitized name consistently for paths and state
        brain_name = safe_name
        llm_provider = (llm or "").strip().lower() or Prompt.ask(
            "LLM provider",
            default="openrouter",
            choices=["openrouter", "openai", "anthropic", "ollama", "local"],
        )

        # LLM config from internal templates (model, max_tokens, temperature, api_base)
        llm_state = get_llm_state_for_brain(llm_provider)

        # Write SOUL.md, USER.md, TOOLS.md
        (workspace / "SOUL.md").write_text(DEFAULT_SOUL)
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

        # Update global config: default_brain
        cfg = load_config()
        cfg["default_brain"] = brain_name
        save_config(cfg)

        console.print(f"[green]✓[/green] Brain [cyan]{brain_name}[/cyan] created at {workspace}")
        console.print(f"[green]✓[/green] Config: {get_config_path()}")
        if llm_provider == "openrouter":
            console.print("[dim]OpenRouter: add your API key to config under providers.openrouter.api_key[/dim]")
            console.print("[dim]Get a key: https://openrouter.ai/keys[/dim]")
        console.print("\nNext: [cyan]cerebra chat[/cyan] or [cyan]cerebra chat --brain " + brain_name + "[/cyan]")
