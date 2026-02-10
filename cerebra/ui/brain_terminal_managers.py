"""Managers that update the terminal buffer: heartbeat, chat history, chat cursor."""

import threading
import time
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from cerebra.ui.terminal_buffer import TerminalBuffer

# Layout (0-based row indices)


def _wrap_text(text: str, width: int) -> list[str]:
    """Break text into lines of at most `width` chars. Breaks at spaces when possible; breaks long words if needed."""
    if width <= 0:
        return [text] if text else []
    lines: list[str] = []
    for paragraph in text.split("\n"):
        while paragraph:
            if len(paragraph) <= width:
                lines.append(paragraph)
                break
            # Find last space in the first `width` chars
            chunk = paragraph[: width + 1]
            last_space = chunk.rfind(" ")
            if last_space > 0:
                lines.append(paragraph[:last_space].rstrip())
                paragraph = paragraph[last_space + 1 :].lstrip()
            else:
                # No space; break the word
                lines.append(paragraph[:width])
                paragraph = paragraph[width:]
    return lines


TABLE_START = 0
TABLE_HEIGHT = 9
DIVIDER_ROW = 9
CHAT_START_ROW = 10
CHAT_END_ROW = 56   # inclusive; 47 lines for history
PROMPT_ROW = 57     # "You: " + input fixed at bottom
LEFT_PANEL_WIDTH = 34


def _bar(v: float, width: int = 8) -> str:
    v = max(0.0, min(1.0, v))
    n = int(v * width)
    return "█" * n + "░" * (width - n)


class HeartbeatAnimationManager:
    """Tracks pulse and updates the heartbeat bar in the table (row 6)."""

    def __init__(self, brain_name: str, get_activities: Callable[[], dict]) -> None:
        self.brain_name = brain_name
        self.get_activities = get_activities

    def _heartbeat_phase(self) -> int:
        """Time-based phase 0..8; triangle wave (fill then empty)."""
        t = time.monotonic() * 2
        cycle = t % 16
        phase = int(cycle) if cycle < 8 else int(16 - cycle)
        return min(8, max(0, phase))

    def update_buffer(self, buffer: "TerminalBuffer") -> None:
        """Write the full CEREBRA table (rows 0..8) into the buffer."""
        activities = self.get_activities()
        heartbeat_phase = self._heartbeat_phase()
        labels = [
            ("Emotional", activities.get("emotional", 0.5)),
            ("Logical", activities.get("logical", 0.5)),
            ("Memory", activities.get("memory", 0.0)),
            ("Inspiration", activities.get("inspiration", 0.5)),
            ("Consciousness", activities.get("consciousness", 0.5)),
            ("♥ Heartbeat", 0.0),
        ]
        w = LEFT_PANEL_WIDTH
        lines = [
            "╔" + "═" * (w - 2) + "╗",
            ("║ CEREBRA - " + self.brain_name)[: w - 1].ljust(w - 1) + "║",
            "╠" + "═" * (w - 2) + "╣",
        ]
        bar_width = 8
        for i, (label, val) in enumerate(labels):
            if label == "♥ Heartbeat":
                bar = "█" * heartbeat_phase + "░" * (bar_width - heartbeat_phase)
            else:
                bar = _bar(val, bar_width)
            line = f"║ {label[:14]:14} [{bar}]"
            lines.append((line[: w - 1].ljust(w - 1) + "║")[:w])
        lines.append("╚" + "═" * (w - 2) + "╝")

        cols = buffer.get_cols()
        for r, line in enumerate(lines):
            if r < TABLE_HEIGHT:
                buffer.write_line(r, (line + " " * cols)[:cols])
        # Divider row
        buffer.write_line(DIVIDER_ROW, "─" * cols)


class ChatHistoryManager:
    """Tracks chat history and writes it to the buffer. Newer messages at bottom; long lines wrap to the next buffer row."""

    def __init__(self) -> None:
        self._messages: list[tuple[str, str, str]] = []  # (role, text, name)

    def append_message(self, role: str, text: str, name: str = "Cerebra") -> None:
        """Add a message (stored raw; wrapped when writing to buffer)."""
        self._messages.append((role, text, name))

    def _get_wrapped_lines(self, cols: int) -> list[str]:
        """Build flat list of display lines with word-wrap at cols. Newest at end."""
        lines: list[str] = []
        for role, text, name in self._messages:
            if role == "user":
                prefix = "You: "
            elif role == "assistant" and name:
                prefix = f"{name}: "
            else:
                prefix = ""
            block = prefix + text
            for line in _wrap_text(block, cols):
                lines.append(line)
        return lines

    def update_buffer(self, buffer: "TerminalBuffer") -> None:
        """Write chat history into the chat region (CHAT_START_ROW..CHAT_END_ROW). Long sentences wrap to next line."""
        cols = buffer.get_cols()
        num_rows = CHAT_END_ROW - CHAT_START_ROW + 1
        all_lines = self._get_wrapped_lines(cols)
        visible = all_lines[-num_rows:] if all_lines else []
        for i, row in enumerate(range(CHAT_START_ROW, CHAT_END_ROW + 1)):
            text = visible[i] if i < len(visible) else ""
            buffer.write_line(row, (text + " " * cols)[:cols])


class ChatCursorManager:
    """Manages the fixed input line at the bottom. Writes 'You: ' + current_input to PROMPT_ROW. Thread-safe for timer + main."""

    YOU_PREFIX = "You: "

    def __init__(self) -> None:
        self._current_input: str = ""
        self._lock = threading.Lock()

    def set_current_input(self, text: str) -> None:
        with self._lock:
            self._current_input = text

    def get_current_input(self) -> str:
        with self._lock:
            return self._current_input

    def get_cursor_col(self) -> int:
        """1-based column for cursor (after 'You: ' + current_input)."""
        with self._lock:
            return len(self.YOU_PREFIX) + len(self._current_input) + 1

    def update_buffer(self, buffer: "TerminalBuffer") -> None:
        """Write the prompt line at PROMPT_ROW from the dictionary; no manual terminal print."""
        with self._lock:
            line = self.YOU_PREFIX + self._current_input
        buffer.write_line(PROMPT_ROW, (line + " " * buffer.get_cols())[: buffer.get_cols()])
