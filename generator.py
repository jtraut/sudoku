from __future__ import annotations
import random
from enum import Enum
from board import Board, SIZE, BOX_SIZE, EMPTY
from solver import Solver


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

    # Number of givens (filled cells) for each difficulty
    @property
    def given_count(self) -> int:
        return {
            Difficulty.EASY: 36,
            Difficulty.MEDIUM: 30,
            Difficulty.HARD: 25,
            Difficulty.EXPERT: 22,
        }[self]


class Generator:
    def __init__(self):
        self._solver = Solver()

    def generate(self, difficulty: Difficulty = Difficulty.MEDIUM) -> Board:
        """Generate a puzzle with a unique solution at the requested difficulty."""
        full = self._generate_full_board()
        puzzle = self._remove_cells(full, difficulty.given_count)
        return puzzle

    def _generate_full_board(self) -> Board:
        """Build a complete, valid Sudoku solution using randomised backtracking."""
        board = Board()
        self._fill(board)
        # Mark all cells as given so we can strip them selectively later
        for r in range(SIZE):
            for c in range(SIZE):
                board._grid[r][c].given = True
        return board

    def _fill(self, board: Board) -> bool:
        cell = self._solver._pick_cell(board)
        if cell is None:
            return True

        row, col = cell
        candidates = list(board.candidates(row, col))
        random.shuffle(candidates)

        for value in candidates:
            board._grid[row][col].value = value
            if self._fill(board):
                return True
            board._grid[row][col].value = EMPTY

        return False

    def _remove_cells(self, full: Board, target_givens: int) -> Board:
        """Remove cells one at a time, keeping the puzzle uniquely solvable."""
        puzzle = full.copy()
        cells = [(r, c) for r in range(SIZE) for c in range(SIZE)]
        random.shuffle(cells)

        removed = 0
        goal = SIZE * SIZE - target_givens

        for row, col in cells:
            if removed >= goal:
                break

            saved = puzzle._grid[row][col].value
            puzzle._grid[row][col].value = EMPTY
            puzzle._grid[row][col].given = False

            if self._solver.count_solutions(puzzle, limit=2) == 1:
                removed += 1
            else:
                # Restoring this cell is necessary to maintain uniqueness
                puzzle._grid[row][col].value = saved
                puzzle._grid[row][col].given = True

        return puzzle
