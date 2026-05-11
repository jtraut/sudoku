from __future__ import annotations
from board import Board, SIZE, EMPTY
from verifier import Verifier


class Solver:
    def solve(self, board: Board) -> bool:
        # Modifies the board in place — use solve_copy if you need the original intact
        return self._backtrack(board)

    def solve_copy(self, board: Board) -> Board | None:
        # Makes a copy first so the player's current board is never touched.
        # Returns None if the puzzle has no valid solution
        copy = board.copy()
        if self._backtrack(copy):
            return copy
        return None

    def count_solutions(self, board: Board, limit: int = 2) -> int:
        # We only really need to know if there's 1 or more than 1 solution,
        # so capping at 2 keeps this from running forever on a sparse board
        copy = board.copy()
        counter = [0]  # list so _count can mutate it — Python closures can't rebind outer vars
        self._count(copy, counter, limit)
        return counter[0]

    def _backtrack(self, board: Board) -> bool:
        # Classic recursive backtracking — try a candidate value, recurse deeper,
        # undo (backtrack) if it leads to a dead end
        cell = self._pick_cell(board)
        if cell is None:
            return True  # no empty cells left, puzzle is solved

        row, col = cell
        for value in board.candidates(row, col):
            board._grid[row][col].value = value
            if self._backtrack(board):
                return True
            board._grid[row][col].value = EMPTY  # this value didn't pan out, undo it

        return False  # no value worked here, signal the caller to backtrack further up

    def _count(self, board: Board, counter: list[int], limit: int) -> None:
        cell = self._pick_cell(board)
        if cell is None:
            counter[0] += 1  # found a complete solution
            return

        row, col = cell
        for value in board.candidates(row, col):
            board._grid[row][col].value = value
            self._count(board, counter, limit)
            board._grid[row][col].value = EMPTY
            if counter[0] >= limit:
                return  # found enough solutions, no need to keep searching

    def _pick_cell(self, board: Board) -> tuple[int, int] | None:
        # Minimum Remaining Values (MRV) heuristic — always tackle the most
        # constrained empty cell first. Fewer candidates = less branching =
        # much smaller search tree compared to just picking in row/col order
        best: tuple[int, int] | None = None
        best_count = SIZE + 1

        for r in range(SIZE):
            for c in range(SIZE):
                if board._grid[r][c].value == EMPTY:
                    count = len(board.candidates(r, c))
                    if count == 0:
                        # No valid candidates at all — guaranteed dead end, bail immediately
                        # rather than finishing the scan. Returning here lets _backtrack
                        # skip straight to the undo step
                        return (r, c)
                    if count < best_count:
                        best_count = count
                        best = (r, c)

        return best
