"""Brain terminal: 100ms timer loop; buffer is the only source of drawn content; input from buffer at PROMPT_ROW."""

import sys
import threading
import time
from typing import TYPE_CHECKING

from rich.console import Console

from cerebra.ui.brain_terminal_managers import (
    ChatCursorManager,
    ChatHistoryManager,
    HeartbeatAnimationManager,
    PROMPT_ROW,
)
from cerebra.ui.terminal_buffer import TerminalBuffer, get_terminal_size

if TYPE_CHECKING:
    from cerebra.core.brain_agent import BrainAgent

console = Console()
TIMER_MS = 100


def _timer_loop(
    agent: "BrainAgent",
    buffer: TerminalBuffer,
    heartbeat: HeartbeatAnimationManager,
    chat_history: ChatHistoryManager,
    chat_cursor: ChatCursorManager,
    stop: threading.Event,
) -> None:
    """Every 100ms: update buffer from all managers (including prompt row), flush entire display, reposition cursor."""
    try:
        while not stop.is_set():
            agent.tick_idle_thoughts()
            heartbeat.update_buffer(buffer)
            chat_history.update_buffer(buffer)
            chat_cursor.update_buffer(buffer)
            buffer.flush(start_row=0, end_row=PROMPT_ROW + 1)
            col = chat_cursor.get_cursor_col()
            sys.stdout.write(f"\033[{PROMPT_ROW + 1};{col}H")
            sys.stdout.flush()
            stop.wait(timeout=TIMER_MS / 1000.0)
    except Exception:
        pass


def _raw_input_line(chat_cursor: ChatCursorManager) -> str | None:
    """Read one line key-by-key; update buffer via chat_cursor (timer draws it). Returns line or None on Ctrl+C."""
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        line: list[str] = []
        while True:
            ch = sys.stdin.read(1)
            if ch in ("\r", "\n"):
                return "".join(line)
            if ch == "\x7f" or ch == "\x08":  # Backspace
                if line:
                    line.pop()
            elif ch == "\x03":  # Ctrl+C
                return None
            elif ch.isprintable() or ch == " ":
                line.append(ch)
            chat_cursor.set_current_input("".join(line))
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


class TerminalInterface:
    """All display from buffer only; 100ms timer updates buffer and flushes; input line in buffer at PROMPT_ROW."""

    def __init__(self, agent: "BrainAgent", show_visual: bool = True) -> None:
        self.agent = agent
        self.show_visual = show_visual
        cols, rows = get_terminal_size()
        self._buffer = TerminalBuffer(rows=rows, cols=cols)
        self._heartbeat = HeartbeatAnimationManager(
            agent.name, agent.get_stream_activities
        )
        self._chat_history = ChatHistoryManager()
        self._chat_cursor = ChatCursorManager()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def run(self) -> None:
        """Main: start timer (buffer is only source of draw); raw input updates buffer via chat_cursor."""
        if not self.show_visual:
            console.print(f"\n[bold]CEREBRA[/bold] - {self.agent.name} (no visual)\n")
            console.print("[dim]Type a message and press Enter. Ctrl+C to exit.[/dim]\n")
            self._run_no_visual()
            return

        self._buffer.clear()
        self._thread = threading.Thread(
            target=_timer_loop,
            args=(
                self.agent,
                self._buffer,
                self._heartbeat,
                self._chat_history,
                self._chat_cursor,
                self._stop,
            ),
            daemon=True,
        )
        self._thread.start()
        self._chat_history.append_message(
            "system",
            "Type a message and press Enter. Ctrl+C to exit.",
            name="",
        )
        self._chat_cursor.set_current_input("")

        while True:
            try:
                user_input = _raw_input_line(self._chat_cursor)
                if user_input is None:
                    break
                user_input = user_input.strip()
                if not user_input:
                    self._chat_cursor.set_current_input("")
                    continue
                self._chat_history.append_message("user", user_input)
                self._chat_cursor.set_current_input("")

                reply_holder: list[str | None] = [None]

                def do_process():
                    reply_holder[0] = self.agent.process_message(user_input)

                th = threading.Thread(target=do_process, daemon=True)
                th.start()
                dots = 0
                while th.is_alive():
                    self._chat_cursor.set_current_input("Thinking" + "." * (1 + (dots % 3)))
                    dots += 1
                    time.sleep(0.35)
                    th.join(timeout=0.05)
                reply = reply_holder[0]
                if reply is None:
                    th.join(timeout=2.0)
                    reply = reply_holder[0] or "(no response)"
                self._chat_history.append_message("assistant", reply, name=self.agent.name)
                self._chat_cursor.set_current_input("")
            except KeyboardInterrupt:
                break

        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        sys.stdout.write("\r\nGoodbye.\n")
        sys.stdout.flush()

    def _run_no_visual(self) -> None:
        """No buffer; plain console input/reply."""
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
