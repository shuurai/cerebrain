"""Simple terminal chat: no fancy buffer/timer; normal input and reply. Booting is in commands."""

from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from cerebra.core.brain_agent import BrainAgent

console = Console()


class TerminalInterface:
    """Plain chat loop: You: / Cerebra: with normal input."""

    def __init__(self, agent: "BrainAgent", show_visual: bool = True) -> None:
        self.agent = agent
        self.show_visual = show_visual

    def run(self) -> None:
        """Simple loop: prompt, input, process, print reply. Ctrl+C to exit."""
        console.print(f"\n[bold]CEREBRA[/bold] - {self.agent.name}")
        console.print("[dim]Type a message and press Enter. Ctrl+C to exit.[/dim]\n")

        while True:
            try:
                user_input = console.input("[bold blue]You:[/bold blue] ").strip()
                if not user_input:
                    continue
                console.print(f"[bold blue]You:[/bold blue] {user_input}")
                reply = self.agent.process_message(user_input)
                console.print(f"[bold green]{self.agent.name}:[/bold green] {reply}\n")
            except KeyboardInterrupt:
                break

        console.print("\nGoodbye.")
