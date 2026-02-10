"""Terminal write tool: 2D buffer (X x Y) with cell/line write and flush to terminal."""

import sys
from typing import Optional

# Default dimensions when detection fails or for preset
DEFAULT_COLS = 200
DEFAULT_ROWS = 60


def get_terminal_size() -> tuple[int, int]:
    """Return (cols, rows); use defaults if detection fails."""
    try:
        import shutil
        size = shutil.get_terminal_size()
        return (size.columns, size.lines)
    except Exception:
        return (DEFAULT_COLS, DEFAULT_ROWS)


class TerminalBuffer:
    """
    A 2D character grid representing the terminal. Write to cells or full lines,
    then flush to the real terminal. Dimensions can be detected or preset (e.g. 200x60).
    """

    def __init__(
        self,
        rows: Optional[int] = None,
        cols: Optional[int] = None,
    ) -> None:
        c, r = get_terminal_size()
        self._cols = cols if cols is not None else c
        self._rows = rows if rows is not None else r
        self._grid: list[str] = []
        self.clear()

    def get_rows(self) -> int:
        return self._rows

    def get_cols(self) -> int:
        return self._cols

    def clear(self, char: str = " ") -> None:
        """Fill the entire buffer with the given character (default space)."""
        line = (char * self._cols)[: self._cols]
        self._grid = [line[:] for _ in range(self._rows)]

    def write_cell(self, row: int, col: int, char: str) -> None:
        """Write a single character at (row, col). 0-based. Out of range is no-op."""
        if not (0 <= row < self._rows and 0 <= col < self._cols):
            return
        if len(char) != 1:
            char = char[0] if char else " "
        line = self._grid[row]
        self._grid[row] = line[:col] + char + line[col + 1 :]

    def write_line(self, row: int, text: str, truncate: bool = True) -> None:
        """
        Write text at the given row. Pads with spaces to full width.
        If truncate is True, text longer than cols is cut; otherwise it can extend (still one row).
        """
        if row < 0 or row >= self._rows:
            return
        if truncate:
            text = (text + " " * self._cols)[: self._cols]
        else:
            text = text[: self._cols]
        self._grid[row] = text.ljust(self._cols)[: self._cols]

    def get_line(self, row: int) -> str:
        """Return the current content of a row (0-based)."""
        if 0 <= row < self._rows:
            return self._grid[row]
        return ""

    def flush(self, start_row: int = 0, end_row: Optional[int] = None) -> None:
        """
        Write buffer to the real terminal. Outputs rows [start_row, end_row).
        Move cursor to the first row being written (1-based) so partial flush doesn't overwrite from (1,1).
        """
        r_end = end_row if end_row is not None else self._rows
        r_end = min(r_end, self._rows)
        # Move to (start_row+1, 1) in 1-based terminal coordinates
        sys.stdout.write(f"\033[{start_row + 1};1H")
        for r in range(start_row, r_end):
            sys.stdout.write(self._grid[r] + "\n")
        sys.stdout.flush()
