from __future__ import annotations
from board import Board, SIZE, EMPTY
from verifier import Verifier


class Solver:
    def solve(self, board: Board) -> bool:
        """Solve in-place using backtracking. Returns True if a solution was found."""
        return self._backtrack(board)

    def solve_copy(self, board: Board) -> Board | None:
        """Return a solved copy, leaving the original unchanged. Returns None if unsolvable."""
        copy = board.copy()
        # Temporarily unlock all non-given cells for solving
        if self._backtrack(copy):
            return copy
        return None

    def count_solutions(self, board: Board, limit: int = 2) -> int:
        """Count solutions up to `limit` to check uniqueness."""
        copy = board.copy()
        counter = [0]
        self._count(copy, counter, limit)
        return counter[0]

    def _backtrack(self, board: Board) -> bool:
        cell = self._pick_cell(board)
        if cell is None:
            return True  # All cells filled

        row, col = cell
        for value in board.candidates(row, col):
            board._grid[row][col].value = value
            if self._backtrack(board):
                return True
            board._grid[row][col].value = EMPTY

        return False

    def _count(self, board: Board, counter: list[int], limit: int) -> None:
        cell = self._pick_cell(board)
        if cell is None:
            counter[0] += 1
            return

        row, col = cell
        for value in board.candidates(row, col):
            board._grid[row][col].value = value
            self._count(board, counter, limit)
            board._grid[row][col].value = EMPTY
            if counter[0] >= limit:
                return

    def _pick_cell(self, board: Board) -> tuple[int, int] | None:
        """Minimum Remaining Values heuristic — pick the most constrained empty cell."""
        best: tuple[int, int] | None = None
        best_count = SIZE + 1

        for r in range(SIZE):
            for c in range(SIZE):
                if board._grid[r][c].value == EMPTY:
                    count = len(board.candidates(r, c))
                    if count == 0:
                        return (r, c)  # Dead end — return immediately
                    if count < best_count:
                        best_count = count
                        best = (r, c)

        return best
