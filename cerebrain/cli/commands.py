"""CLI commands for cerebrain."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cerebrain import __logo__, __version__

app = typer.Typer(
    name="cerebrain",
    help=f"{__logo__} - Brain Matrix CLI",
    no_args_is_help=True,
)

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"{__logo__} v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=_version_callback, is_eager=True
    ),
) -> None:
    """Cerebrain - Terminal-based brain matrix (SOUL, MEMORY, USER, TOOLS)."""
    pass


# -----------------------------------------------------------------------------
# Init / Onboard
# -----------------------------------------------------------------------------


@app.command("init")
def init_cmd(
    name: str = typer.Option(None, "--name", "-n", help="Brain name (prompted if not set)"),
    llm: str = typer.Option(
        None,
        "--llm",
        "-l",
        help="LLM provider: openrouter, openai, anthropic, ollama, local (prompted if not set)",
    ),
) -> None:
    """Initialize a new brain: interactive wizard for provider, API key, model, port, soul."""
    from cerebrain.scripts.setup_cerebraai import BrainWizard

    wizard = BrainWizard()
    wizard.create_brain(name=name, llm=llm)


@app.command("onboard")
def onboard_cmd(
    name: str = typer.Option(None, "--name", "-n", help="Brain name"),
    llm: str = typer.Option(None, "--llm", "-l", help="LLM provider"),
) -> None:
    """Alias for init: initialize a new brain."""
    init_cmd(name=name, llm=llm)


# -----------------------------------------------------------------------------
# Chat
# -----------------------------------------------------------------------------


@app.command()
def chat(
    brain: str = typer.Option(None, "--brain", "-b", help="Brain to load (default: first)"),
    no_visual: bool = typer.Option(False, "--no-visual", help="Terminal chat only, no ASCII"),
) -> None:
    """Start interactive chat; default shows ASCII visualization."""
    from cerebrain.core.brain_agent import BrainAgent
    from cerebrain.ui.terminal_brain import TerminalInterface

    console.print("Booting ....")
    agent = BrainAgent.load(brain)
    console.print("Loading into Cerebra Matrix Terminal ....")
    TerminalInterface(agent, show_visual=not no_visual).run()


# -----------------------------------------------------------------------------
# Serve (API)
# -----------------------------------------------------------------------------


@app.command()
def serve(
    brain: str = typer.Option(None, "--brain", "-b", help="Brain to load"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port (default from config or 17971)"),
) -> None:
    """Run HTTP + WebSocket API server."""
    from cerebrain.api.server import run_server
    from cerebrain.utils.config_loader import get_default_port

    run_server(brain_name=brain, port=port if port is not None else get_default_port())


# -----------------------------------------------------------------------------
# Status & List
# -----------------------------------------------------------------------------


@app.command()
def status() -> None:
    """Show config path, workspace, brains, API keys status."""
    from cerebrain.utils.config_loader import get_config_path, get_data_dir
    from cerebrain.utils.persistence import list_brains

    config_path = get_config_path()
    data_dir = get_data_dir()
    brains = list_brains()

    console.print(f"\n{__logo__} Status\n")
    console.print(f"Config:   {config_path} {'[green]✓' if config_path.exists() else '[red]✗'}")
    console.print(f"Data:    {data_dir} {'[green]✓' if data_dir.exists() else '[yellow]—'}")
    console.print(f"Brains:   {len(brains)}")
    if brains:
        for b in brains:
            console.print(f"  - [cyan]{b}[/cyan]")
    else:
        console.print("  [dim]None (run cerebrain init first)[/dim]")


@app.command("list")
def list_cmd() -> None:
    """List created brains."""
    from cerebrain.utils.persistence import list_brains

    brains = list_brains()
    if not brains:
        console.print("[dim]No brains. Run cerebrain init first.[/dim]")
        return
    table = Table(title="Brains")
    table.add_column("Name", style="cyan")
    for b in brains:
        table.add_row(b)
    console.print(table)


@app.command("list-brains")
def list_brains_cmd() -> None:
    """Alias for list."""
    list_cmd()


# -----------------------------------------------------------------------------
# Diagnose & Export
# -----------------------------------------------------------------------------


@app.command()
def diagnose(
    brain: str = typer.Argument(..., help="Brain name"),
) -> None:
    """Run brain diagnostics."""
    from cerebrain.scripts.brain_diagnostics import BrainDiagnostics

    diag = BrainDiagnostics(brain)
    diag.run_full_diagnostics()


@app.command()
def export(
    brain: str = typer.Argument(..., help="Brain name"),
    format: str = typer.Option("json", "--format", "-f", help="Export format: json, yaml, txt"),
) -> None:
    """Export brain state."""
    from cerebrain.utils.persistence import export_brain

    path = export_brain(brain, fmt=format)
    if path:
        console.print(f"[green]✓[/green] Exported to {path}")
    else:
        console.print(f"[red]Brain '{brain}' not found.[/red]")
        raise typer.Exit(1)
