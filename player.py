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


class InputReader:
    """Platform-aware single-keypress reader."""

    if os.name == "nt":
        import msvcrt as _msvcrt

        def read_key(self) -> str:
            import msvcrt
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):  # special / arrow prefix on Windows
                ch2 = msvcrt.getwch()
                return f"\x00{ch2}"
            return ch
    else:
        import tty as _tty
        import termios as _termios

        def read_key(self) -> str:
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
        k = key.lower()

        # Quit
        if k in ("q", "\x03"):
            return Action("quit")

        # Arrow keys — Windows
        if k == "\x00H" or k == "\x00\x48":  return Action("move", dr=-1, dc=0)
        if k == "\x00P" or k == "\x00\x50":  return Action("move", dr=1, dc=0)
        if k == "\x00K" or k == "\x00\x4b":  return Action("move", dr=0, dc=-1)
        if k == "\x00M" or k == "\x00\x4d":  return Action("move", dr=0, dc=1)

        # Arrow keys — ANSI escape
        if key == "\x1b[A":  return Action("move", dr=-1, dc=0)
        if key == "\x1b[B":  return Action("move", dr=1, dc=0)
        if key == "\x1b[D":  return Action("move", dr=0, dc=-1)
        if key == "\x1b[C":  return Action("move", dr=0, dc=1)

        # HJKL / WASD movement (d = right, w = up, a = left)
        # 's' is reserved for solve, so vertical WASD uses w only
        hjkl_map = {"k": (-1, 0), "h": (0, -1), "j": (1, 0), "l": (0, 1)}
        if k in hjkl_map:
            dr, dc = hjkl_map[k]
            return Action("move", dr=dr, dc=dc)

        if k == "w":  return Action("move", dr=-1, dc=0)
        if k == "a":  return Action("move", dr=0, dc=-1)
        if k == "d":  return Action("move", dr=0, dc=1)

        # Digits 1-9 → place
        if k in "123456789":
            return Action("place", value=int(k))

        # Clear cell
        if k in ("0", " ", "x", "\x7f", "\x08"):
            return Action("clear")

        # Commands
        if k == "s":   return Action("solve")
        if k == "n":   return Action("new")
        if k == "c":   return Action("check")
        if k == "f":   return Action("difficulty")
        if k == "?":   return Action("help")

        return Action("unknown")
