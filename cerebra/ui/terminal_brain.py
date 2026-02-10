"""ASCII brain visualization and terminal chat interface."""

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from cerebra.core.brain_agent import BrainAgent

console = Console()


def _brain_frame(name: str, left_label: str = "Thinking...", right_label: str = "Emotional") -> str:
    """Build ASCII brain layout with dynamic labels."""
    return f"""
╔══════════════════════════════════════════════════════════╗
║ CEREBRA - {name}
╠══════════════════════════════╦════════════════════════════╣
║ LEFT BRAIN (Logical)         ║ RIGHT BRAIN (Creative)     ║
║ ┌──────────────────────────┐ ║ ┌────────────────────────┐ ║
║ │ [██░░░░] {left_label[:20]:<20} │ ║ │ [░░██░░] {right_label[:18]:<18} │ ║
║ │ [░░██░░] Memory Access   │ ║ │ [██░░██] Inspiration   │ ║
║ └──────────────────────────┘ ║ └────────────────────────┘ ║
╠══════════════════════════════╩════════════════════════════╣
║ CONSCIOUSNESS STREAM
║ » (awaiting input)
╠═══════════════════════════════════════════════════════════╣
║ CHAT >
╚═══════════════════════════════════════════════════════════╝
""".strip()


def _stream_lines(agent: "BrainAgent") -> list[str]:
    """Current consciousness stream lines (mood, inspiration hint)."""
    metrics = agent.get_current_metrics()
    mood = metrics.get("emotional", {})
    top = sorted(mood.items(), key=lambda x: -x[1])[:2]
    lines = [f"» Feeling {top[0][0]} ({top[0][1]:.1f})" if top else "» Ready."]
    insp = metrics.get("inspiration", {})
    if insp.get("active"):
        lines.append("» Inspiration active")
    return lines


class TerminalInterface:
    """Runs interactive chat with optional ASCII brain view."""

    def __init__(self, agent: "BrainAgent", show_visual: bool = True) -> None:
        self.agent = agent
        self.show_visual = show_visual

    def run(self) -> None:
        """Main loop: print header, then prompt for input and echo responses."""
        if self.show_visual:
            frame = _brain_frame(self.agent.name)
            console.print(Panel(Text(frame, style="dim"), title="CEREBRA", border_style="blue"))
        else:
            console.print(f"\n[bold]CEREBRA[/bold] - {self.agent.name} (no visual)\n")

        console.print("[dim]Type a message and press Enter. Ctrl+C to exit. F2 = metrics (future)[/dim]\n")
        while True:
            try:
                user_input = console.input("[bold blue]You:[/bold blue] ").strip()
                if not user_input:
                    continue
                if self.show_visual:
                    console.print("[dim]» Thinking...[/dim]")
                reply = self.agent.process_message(user_input)
                if self.show_visual:
                    for line in _stream_lines(self.agent):
                        console.print(f"[dim]{line}[/dim]")
                console.print(f"\n[bold green]{self.agent.name}:[/bold green] {reply}\n")
            except KeyboardInterrupt:
                console.print("\nGoodbye.")
                break
