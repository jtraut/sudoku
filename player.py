from __future__ import annotations
import sys
import os
from dataclasses import dataclass
from board import SIZE


@dataclass
class Action:
    # All possible things a player can do in a single "turn"
    kind: str          # "move" | "place" | "clear" | "solve" | "new" | "check" |
                       # "difficulty" | "help" | "quit" | "unknown"
    value: int = 0     # digit for "place" actions
    dr: int = 0        # row delta for "move" actions
    dc: int = 0        # col delta for "move" actions


def _has_windows_console() -> bool:
    # GetConsoleMode succeeds only when stdin is a real Windows console handle.
    # It fails on pipes (Git Bash / mintty without winpty, redirected stdin, etc.)
    # This is how we decide at runtime whether msvcrt single-keypress reading will work
    try:
        import ctypes
        mode = ctypes.c_ulong()
        return bool(
            ctypes.windll.kernel32.GetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-10), ctypes.byref(mode)
            )
        )
    except Exception:
        return False  # not Windows or ctypes unavailable, assume no real console


class InputReader:
    """Platform-aware single-keypress reader.

    Three modes detected at runtime:
      msvcrt  — real Windows console (CMD, Windows Terminal, winpty)
      termios — POSIX terminal (Linux, macOS)
      line    — mintty / pipe fallback: reads a full line, uses first character
    """

    def __init__(self):
        if os.name == "nt":
            # On Windows, line_mode means we're in a pipe environment (Git Bash etc.)
            # and can't read individual keypresses without winpty
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
            # Extended key prefix — read second byte and return both together so
            # _parse() can match the full sequence. Preserving the actual prefix byte
            # (\x00 vs \xe0) matters because arrow keys specifically use \xe0 in CMD
            return ch + msvcrt.getwch()
        return ch

    def _read_posix(self) -> str:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            # Raw mode disables line buffering and echo so keypresses arrive immediately
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                # Might be start of an escape sequence — arrow keys send \x1b[A etc.
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    return f"\x1b[{ch3}"
            return ch
        finally:
            # Always restore terminal settings even if something blows up
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _read_line(self) -> str:
        # Degraded fallback for mintty / Git Bash without winpty.
        #
        # Native Windows Python stdin is a pipe in cooked mode in this environment —
        # characters aren't available until the user presses Enter, so single-keypress
        # input just isn't possible without winpty wrapping the process.
        # Best we can do is take the first character of whatever line the user submits.
        #
        # Note: Ctrl+C cannot reliably reach a pipe-connected Windows process from mintty.
        # Use `winpty python main.py` for full signal and keypress support.
        try:
            sys.stdout.write("  > ")
            sys.stdout.flush()
            # os.read bypasses Python's text-layer buffering entirely and reads raw
            # bytes directly from the stdin file descriptor — more reliable in pipe envs
            raw = os.read(sys.stdin.fileno(), 256)
            if not raw:       # stdin closed / EOF
                return "q"
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                return ""
            if line[0] == "\x03":  # Ctrl+C piped through as a literal character
                return "q"
            return line[0]
        except (EOFError, KeyboardInterrupt, OSError):
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
        # Clamp to board boundaries — player can't move off the edge
        self.row = max(0, min(SIZE - 1, self.row + dr))
        self.col = max(0, min(SIZE - 1, self.col + dc))

    def get_action(self) -> Action:
        key = self._reader.read_key()
        return self._parse(key)

    def _parse(self, key: str) -> Action:
        # Arrow / special key sequences MUST be checked BEFORE lowercasing.
        # The second byte of a Windows arrow sequence is an uppercase letter
        # (H = up, P = down, K = left, M = right) — lowercasing would mangle it
        # and none of the checks would ever match. CMD uses \xe0 prefix for arrows;
        # older paths or alternate keyboards sometimes send \x00 instead
        if key in ("\x00H", "\x00\x48", "\xe0H", "\xe0\x48"):
            return Action("move", dr=-1, dc=0)  # up
        if key in ("\x00P", "\x00\x50", "\xe0P", "\xe0\x50"):
            return Action("move", dr=1,  dc=0)  # down
        if key in ("\x00K", "\x00\x4b", "\xe0K", "\xe0\x4b"):
            return Action("move", dr=0,  dc=-1) # left
        if key in ("\x00M", "\x00\x4d", "\xe0M", "\xe0\x4d"):
            return Action("move", dr=0,  dc=1)  # right

        # POSIX / mintty sends ANSI escape sequences for arrow keys instead
        if key == "\x1b[A":  return Action("move", dr=-1, dc=0)
        if key == "\x1b[B":  return Action("move", dr=1,  dc=0)
        if key == "\x1b[D":  return Action("move", dr=0,  dc=-1)
        if key == "\x1b[C":  return Action("move", dr=0,  dc=1)

        # Tab triggers auto-solve — moved off 'S' so full WASD movement works
        if key == "\t":  return Action("solve")

        k = key.lower()

        if k in ("q", "\x03"):  return Action("quit")  # Q or Ctrl+C character

        # Standard PC game movement — full WASD, all four directions
        _MOVE = {
            "w": (-1, 0), "a": (0, -1), "s": (1, 0), "d": (0, 1),
        }
        if k in _MOVE:
            dr, dc = _MOVE[k]
            return Action("move", dr=dr, dc=dc)

        if k in "123456789":  return Action("place", value=int(k))

        # Multiple ways to clear — 0, space, x, delete, backspace all feel natural
        if k in ("0", " ", "x", "\x7f", "\x08"):  return Action("clear")

        if k == "n":   return Action("new")
        if k == "c":   return Action("check")
        if k == "f":   return Action("difficulty")
        if k == "?":   return Action("help")

        return Action("unknown")  # anything unrecognised just gets silently ignored
