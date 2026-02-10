"""Simple terminal chat: no fancy buffer/timer; normal input and reply. Booting is in commands."""

import sys
import threading
import time
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from cerebra.core.brain_agent import BrainAgent

console = Console()


class TerminalInterface:
    """Plain chat loop: You: / Cerebra: with normal input; thinking dots and status stream while waiting."""

    def __init__(self, agent: "BrainAgent", show_visual: bool = True) -> None:
        self.agent = agent
        self.show_visual = show_visual

    def run(self) -> None:
        """Simple loop: prompt, input, process (with thinking animation), print reply. Ctrl+C to exit."""
        console.print(f"\n[bold]CEREBRA[/bold] - {self.agent.name}")
        console.print("[dim]Type a message and press Enter. Ctrl+C to exit.[/dim]\n")
        greeting = self.agent.get_greeting()
        console.print(f"[bold green]{self.agent.name}:[/bold green] {greeting}\n")

        while True:
            try:
                user_input = console.input("[bold blue]You:[/bold blue] ").strip()
                if not user_input:
                    continue

                reply_holder: list = [None]

                def do_process():
                    reply_holder[0] = self.agent.process_message(user_input)

                th = threading.Thread(target=do_process, daemon=True)
                th.start()
                dots = 0
                while th.is_alive():
                    while True:
                        status = self.agent.get_next_thinking_status()
                        if status is None:
                            break
                        console.print(f"  [dim]{status}[/dim]")
                    thinking = "  Thinking" + "." * (1 + (dots % 3))
                    sys.stdout.write("\r" + thinking + "   ")
                    sys.stdout.flush()
                    dots += 1
                    time.sleep(0.28)
                    th.join(timeout=0.02)
                while True:
                    status = self.agent.get_next_thinking_status()
                    if status is None:
                        break
                    console.print(f"  [dim]{status}[/dim]")
                sys.stdout.write("\r\033[K")
                sys.stdout.flush()
                reply = reply_holder[0]
                console.print(f"[bold green]{self.agent.name}:[/bold green] {reply}\n")
            except KeyboardInterrupt:
                break

        console.print("\nGoodbye.")
