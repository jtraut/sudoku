from __future__ import annotations
import os
from board import Board, SIZE, BOX_SIZE, EMPTY
from verifier import VerificationResult


# TODO: could add a theme system here — "high contrast" mode, or a light-background
# variant since not everyone uses a dark terminal. Right now everything assumes dark.
class _C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"    # dimmed text — used for grid lines and empty cell dots
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_BLUE = "\033[44m"   # cursor cell highlight
    BG_DARK = "\033[100m"  # unused right now, might find a use for this later


def _enable_windows_ansi() -> bool:
    # Windows 10+ has ANSI/VT support built in but it's not on by default —
    # we need to flip the ENABLE_VIRTUAL_TERMINAL_PROCESSING bit on the console handle
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if not k32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False  # not a real console (pipe, redirect, etc.)
        return bool(k32.SetConsoleMode(handle, mode.value | 0x0004))  # ENABLE_VT_PROCESSING
    except Exception:
        return False


def _supports_ansi() -> bool:
    # Non-Windows terminals support ANSI by default, nothing to do
    if os.name != "nt":
        return True
    # Check for known ANSI-capable Windows environments before making the
    # slower SetConsoleMode syscall
    if (
        "WT_SESSION" in os.environ       # Windows Terminal
        or "ANSICON" in os.environ       # ANSICON wrapper
        or "MSYSTEM" in os.environ       # Git Bash / MSYS2
        or os.environ.get("TERM", "").startswith("xterm")
        or os.environ.get("TERM_PROGRAM", "") == "mintty"
    ):
        return True
    # Plain CMD or PowerShell on Windows 10+ — try to enable VT processing
    return _enable_windows_ansi()


# Evaluated once at import time — no need to re-check on every render
USE_COLOR = _supports_ansi()


def _c(code: str, text: str) -> str:
    # No-op when the terminal doesn't support color so the rest of the rendering
    # code doesn't have to think about it
    if not USE_COLOR:
        return text
    return f"{code}{text}{_C.RESET}"


class Display:
    def clear(self) -> None:
        # ANSI escape clears the visible screen area and works in mintty and Windows Terminal.
        # os.system("cls") only clears the hidden ConHost buffer which mintty doesn't show —
        # learned this the hard way after the double-banner problem
        if USE_COLOR:
            print("\033[2J\033[H", end="", flush=True)
        else:
            os.system("cls" if os.name == "nt" else "clear")

    def render_board(
        self,
        board: Board,
        result: VerificationResult | None = None,
        cursor: tuple[int, int] | None = None,
        show_candidates: bool = False,
        # TODO: actually use show_candidates — would show small digit hints in empty
        # cells like pencil marks in a physical Sudoku puzzle. Probably toggle with P
    ) -> None:
        conflict_set = set(result.conflicts) if result else set()
        print()
        self._print_col_headers()
        self._print_h_border(top=True)

        for r in range(SIZE):
            self._print_row(board, r, conflict_set, cursor)
            if r < SIZE - 1:
                # Heavier border between 3x3 box rows, lighter separator within a box
                if (r + 1) % BOX_SIZE == 0:
                    self._print_h_border(mid=True)
                else:
                    self._print_h_separator()

        self._print_h_border(bottom=True)
        print()

    def _print_col_headers(self) -> None:
        # Column numbers along the top — adds a small visual gap between box columns
        parts = ["    "]
        for c in range(SIZE):
            if c > 0 and c % BOX_SIZE == 0:
                parts.append("  ")  # gap between box groups
            parts.append(f" {_c(_C.DIM, str(c + 1))} ")
        print("".join(parts))

    def _print_h_border(
        self, top: bool = False, mid: bool = False, bottom: bool = False
    ) -> None:
        # Box-drawing characters for thick borders (top, box-row boundaries, bottom)
        if top:
            left, cross, right, h = "┌", "┬", "┐", "─"
        elif mid:
            left, cross, right, h = "├", "┼", "┤", "─"
        else:
            left, cross, right, h = "└", "┴", "┘", "─"

        seg = h * 9
        line = f"    {left}{seg}{cross}{seg}{cross}{seg}{right}"
        print(_c(_C.DIM, line))

    def _print_h_separator(self) -> None:
        # Lighter thin separator between rows within the same 3x3 box
        seg = "─" * 9
        line = f"    │{seg}│{seg}│{seg}│"
        print(_c(_C.DIM, line))

    def _print_row(
        self,
        board: Board,
        row: int,
        conflicts: set[tuple[int, int]],
        cursor: tuple[int, int] | None,
    ) -> None:
        row_label = _c(_C.DIM, f" {row + 1}  ")
        parts = [row_label, _c(_C.DIM, "│")]

        for c in range(SIZE):
            if c > 0 and c % BOX_SIZE == 0:
                parts.append(_c(_C.DIM, "│"))  # vertical divider between box columns

            val = board.get(row, c)
            is_cursor = cursor == (row, c)
            is_conflict = (row, c) in conflicts
            is_given = board.is_given(row, c)

            cell_str = str(val) if val != EMPTY else "·"  # middle dot for empty cells

            # Priority order matters: cursor > conflict > given > player-filled > empty
            if is_cursor:
                if USE_COLOR:
                    cell_str = _c(_C.BG_BLUE + _C.BOLD + _C.WHITE, f" {cell_str} ")
                else:
                    cell_str = f"[{cell_str}]"  # ASCII bracket fallback when no colors
            elif is_conflict:
                if USE_COLOR:
                    cell_str = _c(_C.RED + _C.BOLD, f" {cell_str} ")
                else:
                    cell_str = f"!{cell_str}!"  # ASCII bang fallback for conflict cells
            elif is_given:
                # Givens are bold white — visually heavier than player-entered numbers
                cell_str = _c(_C.BOLD + _C.WHITE, f" {cell_str} ")
            elif val != EMPTY:
                # Player-entered number — cyan to distinguish from givens
                cell_str = _c(_C.CYAN, f" {cell_str} ")
            else:
                cell_str = _c(_C.DIM, f" {cell_str} ")  # empty, barely visible

            parts.append(cell_str)

        parts.append(_c(_C.DIM, "│"))
        print("".join(parts))

    def print_status(self, message: str, kind: str = "info") -> None:
        prefix = {
            "info": "",
            "success": _c(_C.GREEN, "✓ "),
            "error": _c(_C.RED, "✗ "),
            "warn": _c(_C.YELLOW, "! "),
        }.get(kind, "")
        print(f"  {prefix}{message}")

    def print_help(self) -> None:
        print()
        print(_c(_C.BOLD, "  Controls"))
        print("  ─────────────────────────────────")
        rows = [
            ("Arrow keys / WASD", "Move cursor"),
            ("1-9", "Place digit"),
            ("0 / Space / Delete / X", "Clear cell"),
            ("Tab", "Auto-solve (asks for confirmation)"),
            ("N", "New game (asks for confirmation)"),
            ("F", "Cycle difficulty and new game (asks for confirmation)"),
            ("C", "Check board for conflicts"),
            ("?", "Toggle this help"),
            ("Q / Ctrl+C", "Quit"),
        ]
        for key, desc in rows:
            print(f"  {_c(_C.CYAN, key.ljust(28))}  {desc}")
        print()

    def print_banner(self) -> None:
        banner = r"""
  ╔═══════════════════════════╗
  ║   S U D O K U             ║
  ╚═══════════════════════════╝"""
        print(_c(_C.BOLD + _C.CYAN, banner))
