from __future__ import annotations
import os
from board import Board, SIZE, BOX_SIZE, EMPTY
from verifier import VerificationResult


# ANSI colour codes
class _C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_BLUE = "\033[44m"
    BG_DARK = "\033[100m"


def _enable_windows_ansi() -> bool:
    """Enable VT/ANSI processing on the Windows console stdout handle."""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.GetStdHandle(-11)          # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if not k32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(k32.SetConsoleMode(handle, mode.value | 0x0004))  # ENABLE_VT_PROCESSING
    except Exception:
        return False


def _supports_ansi() -> bool:
    if os.name != "nt":
        return True
    # Already-known ANSI environments
    if (
        "WT_SESSION" in os.environ
        or "ANSICON" in os.environ
        or "MSYSTEM" in os.environ
        or os.environ.get("TERM", "").startswith("xterm")
        or os.environ.get("TERM_PROGRAM", "") == "mintty"
    ):
        return True
    # Regular CMD / PowerShell on Windows 10+: try to enable VT processing
    return _enable_windows_ansi()


USE_COLOR = _supports_ansi()


def _c(code: str, text: str) -> str:
    if not USE_COLOR:
        return text
    return f"{code}{text}{_C.RESET}"


class Display:
    def clear(self) -> None:
        # ANSI clear works in mintty and Windows Terminal.
        # os.system("cls") clears the hidden ConHost buffer, not mintty's screen.
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
    ) -> None:
        conflict_set = set(result.conflicts) if result else set()
        print()
        self._print_col_headers()
        self._print_h_border(top=True)

        for r in range(SIZE):
            self._print_row(board, r, conflict_set, cursor)
            if r < SIZE - 1:
                if (r + 1) % BOX_SIZE == 0:
                    self._print_h_border(mid=True)
                else:
                    self._print_h_separator()
        self._print_h_border(bottom=True)
        print()

    def _print_col_headers(self) -> None:
        parts = ["    "]
        for c in range(SIZE):
            if c > 0 and c % BOX_SIZE == 0:
                parts.append("  ")
            parts.append(f" {_c(_C.DIM, str(c + 1))} ")
        print("".join(parts))

    def _print_h_border(
        self, top: bool = False, mid: bool = False, bottom: bool = False
    ) -> None:
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
                parts.append(_c(_C.DIM, "│"))

            val = board.get(row, c)
            is_cursor = cursor == (row, c)
            is_conflict = (row, c) in conflicts
            is_given = board.is_given(row, c)

            cell_str = str(val) if val != EMPTY else "·"

            if is_cursor:
                if USE_COLOR:
                    cell_str = _c(_C.BG_BLUE + _C.BOLD + _C.WHITE, f" {cell_str} ")
                else:
                    cell_str = f"[{cell_str}]"   # ASCII cursor indicator
            elif is_conflict:
                if USE_COLOR:
                    cell_str = _c(_C.RED + _C.BOLD, f" {cell_str} ")
                else:
                    cell_str = f"!{cell_str}!"   # ASCII conflict indicator
            elif is_given:
                cell_str = _c(_C.BOLD + _C.WHITE, f" {cell_str} ")
            elif val != EMPTY:
                cell_str = _c(_C.CYAN, f" {cell_str} ")
            else:
                cell_str = _c(_C.DIM, f" {cell_str} ")

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
            ("N", "New game"),
            ("F", "Cycle difficulty then new game"),
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
