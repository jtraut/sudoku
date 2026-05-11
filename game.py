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
        self._result: VerificationResult | None = None  # last check result, or None if stale
        self._show_help: bool = False
        self._status: str = ""
        self._status_kind: str = "info"
        # TODO: add a timer here — start on _new_game(), stop on solved, store elapsed seconds
        # TODO: add a scoreboard dict keyed by Difficulty that tracks wins and best times.
        #       could persist to a small JSON file in the user's home dir so it survives sessions.
        #       something like: {"easy": {"wins": 3, "best": 142}, "medium": {...}, ...}

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
        # TODO: print a goodbye summary here — total wins this session, best times per difficulty

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
        # TODO: reset and start the timer here

    def _handle(self, action: Action) -> None:
        if action.kind == "quit":
            return

        if action.kind == "move":
            self._player.move(action.dr, action.dc)
            # Clear the status message so old check results don't persist after moving
            self._set_status("")
            return

        if action.kind == "place":
            r, c = self._player.position
            ok = self._board.set(r, c, action.value)
            if not ok:
                self._set_status("Cannot edit a given cell.", "warn")
            else:
                # Invalidate the last check result — it refers to the old board state.
                # We don't want red highlights from a previous check lingering after a fix.
                self._result = None
                self._set_status("")
                # Auto-check every placement so the player gets instant feedback on a solve.
                # We only surface the result if the board is actually finished though —
                # popping conflict warnings on every keystroke would be really annoying.
                result = Verifier.check(self._board)
                if result.solved:
                    self._result = result
                    self._set_status("Congratulations! Puzzle solved!", "success")
                    # TODO: stop the timer, record win + elapsed time to the scoreboard here
            return

        if action.kind == "clear":
            r, c = self._player.position
            ok = self._board.clear(r, c)
            if not ok:
                self._set_status("Cannot edit a given cell.", "warn")
            else:
                self._result = None  # same as place — stale check results need to go
                self._set_status("")
            return

        if action.kind == "check":
            self._result = Verifier.check(self._board)
            if self._result.solved:
                self._set_status("Puzzle solved correctly!", "success")
                # TODO: record win here too in case they somehow reached solved without placing last
            elif not self._result.valid:
                n = len(self._result.conflicts)
                self._set_status(f"{n} conflict(s) found — highlighted in red.", "error")
            elif not self._result.complete:
                self._set_status("Board is valid so far but not complete.", "info")
            return

        if action.kind == "solve":
            # Two-step confirmation — render after setting status so the player sees the prompt
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
                # This only happens if the player has placed digits that make the board
                # unsolvable — the generator always produces a valid unique puzzle to start
                self._set_status("No solution exists for this board.", "error")
            else:
                self._board = solution
                self._result = Verifier.check(self._board)
                self._set_status("Board auto-solved.", "success")
                # Intentionally not recording a win here — auto-solve doesn't count!
            return

        if action.kind == "new":
            self._set_status("Start a new game? Press Y to confirm or any other key to cancel.", "warn")
            self._render()
            if self._player._reader.read_key().lower() == "y":
                self._new_game()
            else:
                self._set_status("New game cancelled.", "info")
            return

        if action.kind == "difficulty":
            # Cycles through the difficulty enum in order and wraps back around
            next_idx = (_DIFFICULTIES.index(self._difficulty) + 1) % len(_DIFFICULTIES)
            next_diff = _DIFFICULTIES[next_idx]
            self._set_status(f"Switch to {next_diff.value} and start a new game? Press Y to confirm or any other key to cancel.", "warn")
            self._render()
            if self._player._reader.read_key().lower() == "y":
                self._difficulty = next_diff
                self._new_game()
            else:
                self._set_status("Difficulty change cancelled.", "info")
            return

        if action.kind == "help":
            # Toggle — same key shows and hides the help panel
            self._show_help = not self._show_help
            return

        # TODO: add "hint" action — reveal one correct cell chosen from the solution.
        #       would need to solve_copy the current board state and pick a random empty cell.
        #       probably map to H and track how many hints were used per game.

        # TODO: add "undo" action — keep a stack of (row, col, old_value) tuples and pop on U.
        #       only player-entered cells can be undone — givens are immutable so no-ops there.

    def _render(self) -> None:
        self._display.clear()
        self._display.print_banner()
        print(f"  Difficulty: {self._difficulty.value.capitalize()}")
        # TODO: print elapsed time here once the timer is implemented, e.g. "  Time: 2:34"
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
            # Remind line-mode players that they need to press Enter — easy to forget
            if self._player._reader.line_mode:
                print("  Press ? for help  (line mode: Enter after each key)")
            else:
                print("  Press ? for help")
        print()

    def _set_status(self, message: str, kind: str = "info") -> None:
        self._status = message
        self._status_kind = kind
