from __future__ import annotations
from board import Board
from generator import Generator, Difficulty
from solver import Solver
from verifier import Verifier, VerificationResult
from display import Display
from player import Player, Action


_DIFFICULTIES = list(Difficulty)


class Game:
    def __init__(self):
        self._generator = Generator()
        self._solver = Solver()
        self._display = Display()
        self._player = Player()
        self._difficulty = Difficulty.MEDIUM
        self._board: Board = Board()
        self._result: VerificationResult | None = None
        self._show_help: bool = False
        self._status: str = ""
        self._status_kind: str = "info"

    def run(self) -> None:
        self._new_game()

        while True:
            self._render()
            action = self._player.get_action()
            self._handle(action)
            if action.kind == "quit":
                break

        self._display.clear()
        print("  Thanks for playing!")

    def _new_game(self) -> None:
        # Show a single generating screen without a full board render so there
        # is no empty-board frame left in the terminal scrollback.
        self._display.clear()
        self._display.print_banner()
        print(f"\n  Generating {self._difficulty.value} puzzle…", flush=True)
        self._board = self._generator.generate(self._difficulty)
        self._result = None
        self._player.row = 0
        self._player.col = 0
        self._set_status(
            f"New {self._difficulty.value} game. Press ? for help.", "info"
        )

    def _handle(self, action: Action) -> None:
        if action.kind == "quit":
            return

        if action.kind == "move":
            self._player.move(action.dr, action.dc)
            self._set_status("")
            return

        if action.kind == "place":
            r, c = self._player.position
            ok = self._board.set(r, c, action.value)
            if not ok:
                self._set_status("Cannot edit a given cell.", "warn")
            else:
                self._result = None  # Invalidate last check
                self._set_status("")
                result = Verifier.check(self._board)
                if result.solved:
                    self._result = result
                    self._set_status("Congratulations! Puzzle solved!", "success")
            return

        if action.kind == "clear":
            r, c = self._player.position
            ok = self._board.clear(r, c)
            if not ok:
                self._set_status("Cannot edit a given cell.", "warn")
            else:
                self._result = None
                self._set_status("")
            return

        if action.kind == "check":
            self._result = Verifier.check(self._board)
            if self._result.solved:
                self._set_status("Puzzle solved correctly!", "success")
            elif not self._result.valid:
                n = len(self._result.conflicts)
                self._set_status(f"{n} conflict(s) found — highlighted in red.", "error")
            elif not self._result.complete:
                self._set_status("Board is valid so far but not complete.", "info")
            return

        if action.kind == "solve":
            self._set_status("Auto-solve? Press Y to confirm or any other key to cancel.", "warn")
            self._render()
            confirm = self._player._reader.read_key()
            if confirm.lower() != "y":
                self._set_status("Auto-solve cancelled.", "info")
                return
            self._set_status("Solving…", "info")
            self._render()
            solution = self._solver.solve_copy(self._board)
            if solution is None:
                self._set_status("No solution exists for this board.", "error")
            else:
                self._board = solution
                self._result = Verifier.check(self._board)
                self._set_status("Board auto-solved.", "success")
            return

        if action.kind == "new":
            self._new_game()
            return

        if action.kind == "difficulty":
            idx = _DIFFICULTIES.index(self._difficulty)
            self._difficulty = _DIFFICULTIES[(idx + 1) % len(_DIFFICULTIES)]
            self._new_game()
            return

        if action.kind == "help":
            self._show_help = not self._show_help
            return

    def _render(self) -> None:
        self._display.clear()
        self._display.print_banner()
        print(f"  Difficulty: {self._difficulty.value.capitalize()}")
        self._display.render_board(
            self._board,
            result=self._result,
            cursor=self._player.position,
        )
        if self._status:
            self._display.print_status(self._status, self._status_kind)
        if self._show_help:
            self._display.print_help()
        else:
            if self._player._reader.line_mode:
                print("  Press ? for help  (line mode: Enter after each key)")
            else:
                print("  Press ? for help")
        print()

    def _set_status(self, message: str, kind: str = "info") -> None:
        self._status = message
        self._status_kind = kind
