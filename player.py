from __future__ import annotations
import sys
import os
from dataclasses import dataclass
from board import SIZE


@dataclass
class Action:
    kind: str          # "move" | "place" | "clear" | "solve" | "new" | "check" |
                       # "difficulty" | "help" | "quit" | "unknown"
    value: int = 0     # digit for "place", direction encoded for "move"
    dr: int = 0
    dc: int = 0


def _has_windows_console() -> bool:
    """Return True only when stdin is a real Windows console (not mintty/pipe)."""
    try:
        import ctypes
        mode = ctypes.c_ulong()
        # GetStdHandle(-10) = STD_INPUT_HANDLE; GetConsoleMode fails on pipes
        return bool(
            ctypes.windll.kernel32.GetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-10), ctypes.byref(mode)
            )
        )
    except Exception:
        return False


class InputReader:
    """Platform-aware single-keypress reader.

    Three modes detected at runtime:
      msvcrt  — real Windows console (CMD, Windows Terminal)
      termios — POSIX terminal (Linux, macOS)
      line    — mintty / pipe fallback: reads a full line, uses first character
    """

    def __init__(self):
        if os.name == "nt":
            self.line_mode = not _has_windows_console()
        else:
            self.line_mode = False

    def read_key(self) -> str:
        if self.line_mode:
            return self._read_line()
        if os.name == "nt":
            return self._read_msvcrt()
        return self._read_posix()

    def _read_msvcrt(self) -> str:
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            # Preserve the actual prefix so _parse() can match \xe0 arrow sequences
            return ch + msvcrt.getwch()
        return ch

    def _read_posix(self) -> str:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    return f"\x1b[{ch3}"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _read_line(self) -> str:
        """Fallback for mintty/GitBash: read a full line, return first character.

        Uses input() rather than sys.stdin.readline() so that Ctrl+C raises
        KeyboardInterrupt even while the call is blocking in the C layer.
        """
        try:
            line = input("  > ").strip()
            return line[0] if line else ""
        except (EOFError, KeyboardInterrupt):
            return "q"


class Player:
    def __init__(self):
        self._reader = InputReader()
        self.row: int = 0
        self.col: int = 0

    @property
    def position(self) -> tuple[int, int]:
        return self.row, self.col

    def move(self, dr: int, dc: int) -> None:
        self.row = max(0, min(SIZE - 1, self.row + dr))
        self.col = max(0, min(SIZE - 1, self.col + dc))

    def get_action(self) -> Action:
        key = self._reader.read_key()
        return self._parse(key)

    def _parse(self, key: str) -> Action:
        # --- Arrow / special sequences must be checked BEFORE lowercasing ---
        # CMD sends \xe0 prefix for arrows; POSIX sends \x1b[ escape sequences.
        # Both \x00 and \xe0 are treated as extended-key prefixes on Windows.
        if key in ("\x00H", "\x00\x48", "\xe0H", "\xe0\x48"):
            return Action("move", dr=-1, dc=0)
        if key in ("\x00P", "\x00\x50", "\xe0P", "\xe0\x50"):
            return Action("move", dr=1,  dc=0)
        if key in ("\x00K", "\x00\x4b", "\xe0K", "\xe0\x4b"):
            return Action("move", dr=0,  dc=-1)
        if key in ("\x00M", "\x00\x4d", "\xe0M", "\xe0\x4d"):
            return Action("move", dr=0,  dc=1)

        if key == "\x1b[A":  return Action("move", dr=-1, dc=0)
        if key == "\x1b[B":  return Action("move", dr=1,  dc=0)
        if key == "\x1b[D":  return Action("move", dr=0,  dc=-1)
        if key == "\x1b[C":  return Action("move", dr=0,  dc=1)

        # Tab → auto-solve (confirmation handled by Game)
        if key == "\t":  return Action("solve")

        k = key.lower()

        if k in ("q", "\x03"):  return Action("quit")

        # WASD movement
        _MOVE = {
            "w": (-1, 0), "a": (0, -1), "s": (1, 0), "d": (0, 1),
        }
        if k in _MOVE:
            dr, dc = _MOVE[k]
            return Action("move", dr=dr, dc=dc)

        if k in "123456789":  return Action("place", value=int(k))
        if k in ("0", " ", "x", "\x7f", "\x08"):  return Action("clear")

        if k == "n":   return Action("new")
        if k == "c":   return Action("check")
        if k == "f":   return Action("difficulty")
        if k == "?":   return Action("help")

        return Action("unknown")
