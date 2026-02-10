"""Brain diagnostics (cerebra diagnose)."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from cerebra.utils.config_loader import get_brain_workspace
from cerebra.utils.persistence import load_brain_state

console = Console()


class BrainDiagnostics:
    """Run checks on a brain's workspace and state."""

    def __init__(self, brain_name: str) -> None:
        self.brain_name = brain_name

    def run_full_diagnostics(self) -> None:
        """Print diagnostic table."""
        table = Table(title=f"Diagnostics: {self.brain_name}")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")

        workspace = get_brain_workspace(self.brain_name)
        state = load_brain_state(self.brain_name)

        table.add_row("Workspace exists", "[green]✓" if workspace.exists() else "[red]✗")
        table.add_row("State file", "[green]✓" if state else "[red]✗")
        table.add_row("SOUL.md", "[green]✓" if (workspace / "SOUL.md").exists() else "[red]✗")
        table.add_row("USER.md", "[green]✓" if (workspace / "USER.md").exists() else "[red]✗")
        table.add_row("TOOLS.md", "[green]✓" if (workspace / "TOOLS.md").exists() else "[red]✗")

        if state:
            table.add_row("LLM provider", state.get("llm", {}).get("provider", "—"))

        console.print(table)
