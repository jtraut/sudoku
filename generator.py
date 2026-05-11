from __future__ import annotations
import random
from enum import Enum
from board import Board, SIZE, BOX_SIZE, EMPTY
from solver import Solver


# TODO: might want to re-evaluate these given counts...
# "expert" at 22 givens feels brutal, but that's kind of the point.
# Could also add a "custom" mode where the player picks their own target given count
class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

    # Number of pre-filled cells shown to the player at game start
    @property
    def given_count(self) -> int:
        return {
            Difficulty.EASY: 36,    # roughly 45% filled — comfortable for beginners
            Difficulty.MEDIUM: 30,  # around 37% — requires some deduction
            Difficulty.HARD: 25,    # around 31% — more backtracking / logic needed
            Difficulty.EXPERT: 22,  # around 27% — good luck!
        }[self]


class Generator:
    def __init__(self):
        self._solver = Solver()

    def generate(self, difficulty: Difficulty = Difficulty.MEDIUM) -> Board:
        # Two-phase approach: build a complete valid solution first,
        # then carve cells out one at a time until we hit the target given count
        full = self._generate_full_board()
        puzzle = self._remove_cells(full, difficulty.given_count)
        return puzzle

    def _generate_full_board(self) -> Board:
        # Same backtracking as the solver but with shuffled candidates so every
        # run produces a different board layout
        board = Board()
        self._fill(board)
        # Mark every cell as given so _remove_cells knows to start from a fully-locked state
        for r in range(SIZE):
            for c in range(SIZE):
                board._grid[r][c].given = True
        return board

    def _fill(self, board: Board) -> bool:
        cell = self._solver._pick_cell(board)
        if cell is None:
            return True  # board is completely filled

        row, col = cell
        candidates = list(board.candidates(row, col))
        random.shuffle(candidates)  # shuffle so we get a different board layout every time

        for value in candidates:
            board._grid[row][col].value = value
            if self._fill(board):
                return True
            board._grid[row][col].value = EMPTY  # backtrack

        return False

    def _remove_cells(self, full: Board, target_givens: int) -> Board:
        # Remove cells one at a time in random order, but only keep the removal
        # if the puzzle still has exactly one solution — this guarantees the player
        # can always reach a unique answer through logic alone, no guessing required
        puzzle = full.copy()
        cells = [(r, c) for r in range(SIZE) for c in range(SIZE)]
        random.shuffle(cells)

        removed = 0
        goal = SIZE * SIZE - target_givens  # how many cells need to become empty

        for row, col in cells:
            if removed >= goal:
                break

            saved = puzzle._grid[row][col].value
            puzzle._grid[row][col].value = EMPTY
            puzzle._grid[row][col].given = False

            if self._solver.count_solutions(puzzle, limit=2) == 1:
                # Still uniquely solvable — this removal is safe
                removed += 1
            else:
                # Removing this cell broke uniqueness, put it back.
                # TODO: this means we might not always hit the exact target given count
                # if too many cells are "load-bearing" for uniqueness. Should probably
                # track how close we got and warn or retry if we're way off target
                puzzle._grid[row][col].value = saved
                puzzle._grid[row][col].given = True

        return puzzle
