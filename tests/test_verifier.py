import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from board import Board, EMPTY
from verifier import Verifier

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

# Classic Wikipedia Sudoku puzzle (0 = empty)
_PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

# Unique solution to the puzzle above
_SOLUTION = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


def _make_board(rows):
    return Board.from_grid(rows)


# ---------------------------------------------------------------------------
# Success cases — board is valid
# ---------------------------------------------------------------------------

class TestVerifierSuccess(unittest.TestCase):
    def test_empty_board_is_valid(self):
        board = Board()
        result = Verifier.check(board)
        self.assertTrue(result.valid)
        self.assertFalse(result.complete)
        self.assertFalse(result.solved)
        self.assertEqual(result.conflicts, [])

    def test_partial_puzzle_no_conflicts(self):
        board = _make_board(_PUZZLE)
        result = Verifier.check(board)
        self.assertTrue(result.valid)
        self.assertFalse(result.complete)
        self.assertEqual(result.conflicts, [])

    def test_fully_solved_board_is_valid_and_complete(self):
        board = _make_board(_SOLUTION)
        result = Verifier.check(board)
        self.assertTrue(result.valid)
        self.assertTrue(result.complete)
        self.assertTrue(result.solved)
        self.assertEqual(result.conflicts, [])

    def test_solved_property_requires_both_valid_and_complete(self):
        # A complete but invalid board must not report solved
        grid = [row[:] for row in _SOLUTION]
        grid[0][0] = grid[0][1]  # duplicate value in row 0
        board = _make_board(grid)
        result = Verifier.check(board)
        self.assertFalse(result.solved)


# ---------------------------------------------------------------------------
# Failure cases — board has conflicts
# ---------------------------------------------------------------------------

class TestVerifierFailures(unittest.TestCase):
    def _board_with_row_conflict(self):
        grid = [[0] * 9 for _ in range(9)]
        grid[0][0] = 5
        grid[0][5] = 5  # duplicate 5 in row 0
        return Board.from_grid(grid)

    def _board_with_col_conflict(self):
        grid = [[0] * 9 for _ in range(9)]
        grid[0][3] = 4
        grid[7][3] = 4  # duplicate 4 in col 3
        return Board.from_grid(grid)

    def _board_with_box_conflict(self):
        grid = [[0] * 9 for _ in range(9)]
        grid[0][0] = 6
        grid[2][2] = 6  # both in top-left 3×3 box
        return Board.from_grid(grid)

    def test_row_conflict_is_invalid(self):
        result = Verifier.check(self._board_with_row_conflict())
        self.assertFalse(result.valid)

    def test_row_conflict_cells_identified(self):
        result = Verifier.check(self._board_with_row_conflict())
        self.assertIn((0, 0), result.conflicts)
        self.assertIn((0, 5), result.conflicts)

    def test_col_conflict_is_invalid(self):
        result = Verifier.check(self._board_with_col_conflict())
        self.assertFalse(result.valid)

    def test_col_conflict_cells_identified(self):
        result = Verifier.check(self._board_with_col_conflict())
        self.assertIn((0, 3), result.conflicts)
        self.assertIn((7, 3), result.conflicts)

    def test_box_conflict_is_invalid(self):
        result = Verifier.check(self._board_with_box_conflict())
        self.assertFalse(result.valid)

    def test_box_conflict_cells_identified(self):
        result = Verifier.check(self._board_with_box_conflict())
        self.assertIn((0, 0), result.conflicts)
        self.assertIn((2, 2), result.conflicts)

    def test_multiple_independent_conflicts_all_reported(self):
        grid = [[0] * 9 for _ in range(9)]
        grid[0][0] = 3
        grid[0][8] = 3  # row 0 conflict
        grid[1][1] = 7
        grid[7][1] = 7  # col 1 conflict
        board = Board.from_grid(grid)
        result = Verifier.check(board)
        self.assertFalse(result.valid)
        self.assertIn((0, 0), result.conflicts)
        self.assertIn((0, 8), result.conflicts)
        self.assertIn((1, 1), result.conflicts)
        self.assertIn((7, 1), result.conflicts)

    def test_conflict_does_not_affect_complete_flag(self):
        # A board can be "complete" (no empty cells) but still invalid
        grid = [row[:] for row in _SOLUTION]
        grid[0][0] = grid[0][1]  # introduce a duplicate
        board = _make_board(grid)
        result = Verifier.check(board)
        self.assertTrue(result.complete)
        self.assertFalse(result.valid)


# ---------------------------------------------------------------------------
# is_valid_placement
# ---------------------------------------------------------------------------

class TestIsValidPlacement(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_placement_on_empty_board_is_valid(self):
        self.assertTrue(Verifier.is_valid_placement(self.board, 0, 0, 5))

    def test_placing_empty_value_always_valid(self):
        self.board.set(0, 1, 5)
        self.assertTrue(Verifier.is_valid_placement(self.board, 0, 0, EMPTY))

    def test_row_conflict_is_invalid(self):
        self.board.set(0, 4, 7)
        self.assertFalse(Verifier.is_valid_placement(self.board, 0, 0, 7))

    def test_col_conflict_is_invalid(self):
        self.board.set(5, 0, 2)
        self.assertFalse(Verifier.is_valid_placement(self.board, 0, 0, 2))

    def test_box_conflict_is_invalid(self):
        self.board.set(2, 2, 9)
        self.assertFalse(Verifier.is_valid_placement(self.board, 0, 0, 9))

    def test_no_conflict_is_valid(self):
        self.board.set(0, 1, 1)
        self.board.set(1, 0, 2)
        self.board.set(2, 2, 3)
        # 4 doesn't appear in row 0, col 0, or top-left box
        self.assertTrue(Verifier.is_valid_placement(self.board, 0, 0, 4))

    def test_same_value_in_different_box_row_col_is_valid(self):
        # Value 5 placed far away — no constraint on (0,0)
        self.board.set(5, 5, 5)
        self.assertTrue(Verifier.is_valid_placement(self.board, 0, 0, 5))


if __name__ == "__main__":
    unittest.main()
