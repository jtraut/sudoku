import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from board import Board, Cell, EMPTY, SIZE


class TestCell(unittest.TestCase):
    def test_default_value_and_not_given(self):
        cell = Cell()
        self.assertEqual(cell.value, EMPTY)
        self.assertFalse(cell.given)

    def test_custom_value_and_given_flag(self):
        cell = Cell(7, given=True)
        self.assertEqual(cell.value, 7)
        self.assertTrue(cell.given)


class TestBoardConstruction(unittest.TestCase):
    def test_new_board_all_empty(self):
        board = Board()
        self.assertEqual(len(board.empty_cells()), 81)

    def test_from_grid_sets_values(self):
        grid = [[0] * 9 for _ in range(9)]
        grid[0][0] = 5
        grid[4][4] = 9
        board = Board.from_grid(grid)
        self.assertEqual(board.get(0, 0), 5)
        self.assertEqual(board.get(4, 4), 9)

    def test_from_grid_marks_nonzero_as_given(self):
        grid = [[0] * 9 for _ in range(9)]
        grid[1][2] = 3
        board = Board.from_grid(grid)
        self.assertTrue(board.is_given(1, 2))
        self.assertFalse(board.is_given(0, 0))

    def test_from_grid_zero_cells_not_given(self):
        grid = [[0] * 9 for _ in range(9)]
        board = Board.from_grid(grid)
        for r in range(SIZE):
            for c in range(SIZE):
                self.assertFalse(board.is_given(r, c))

    def test_copy_is_independent(self):
        board = Board()
        board.set(0, 0, 3)
        copy = board.copy()
        copy.set(0, 0, 9)
        self.assertEqual(board.get(0, 0), 3)
        self.assertEqual(copy.get(0, 0), 9)

    def test_copy_preserves_given_flag(self):
        grid = [[0] * 9 for _ in range(9)]
        grid[5][5] = 7
        board = Board.from_grid(grid)
        copy = board.copy()
        self.assertTrue(copy.is_given(5, 5))


class TestBoardSetGet(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_set_and_get_round_trip(self):
        self.board.set(3, 7, 6)
        self.assertEqual(self.board.get(3, 7), 6)

    def test_set_returns_true_for_editable_cell(self):
        self.assertTrue(self.board.set(0, 0, 4))

    def test_set_given_cell_returns_false_and_unchanged(self):
        grid = [[0] * 9 for _ in range(9)]
        grid[0][0] = 7
        board = Board.from_grid(grid)
        result = board.set(0, 0, 5)
        self.assertFalse(result)
        self.assertEqual(board.get(0, 0), 7)

    def test_set_out_of_bounds_raises_index_error(self):
        with self.assertRaises(IndexError):
            self.board.set(9, 0, 1)
        with self.assertRaises(IndexError):
            self.board.set(0, 9, 1)

    def test_set_value_above_nine_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.board.set(0, 0, 10)

    def test_set_value_below_zero_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.board.set(0, 0, -1)

    def test_clear_removes_value(self):
        self.board.set(2, 2, 5)
        self.board.clear(2, 2)
        self.assertEqual(self.board.get(2, 2), EMPTY)

    def test_clear_given_cell_returns_false(self):
        grid = [[0] * 9 for _ in range(9)]
        grid[0][0] = 4
        board = Board.from_grid(grid)
        self.assertFalse(board.clear(0, 0))
        self.assertEqual(board.get(0, 0), 4)


class TestBoardQueries(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_row_returns_correct_values(self):
        for c in range(9):
            self.board.set(2, c, c + 1)
        self.assertEqual(self.board.row(2), list(range(1, 10)))

    def test_col_returns_correct_values(self):
        for r in range(9):
            self.board.set(r, 4, r + 1)
        self.assertEqual(self.board.col(4), list(range(1, 10)))

    def test_box_returns_nine_values(self):
        vals = list(range(1, 10))
        for i, v in enumerate(vals):
            self.board.set(i // 3, i % 3, v)
        self.assertEqual(sorted(self.board.box(0, 0)), vals)

    def test_box_top_right_corner(self):
        # box anchored at row=0, col=6
        for dr in range(3):
            for dc in range(3):
                self.board.set(dr, 6 + dc, dr * 3 + dc + 1)
        self.assertEqual(sorted(self.board.box(0, 8)), list(range(1, 10)))

    def test_candidates_full_on_empty_board(self):
        self.assertEqual(self.board.candidates(0, 0), set(range(1, 10)))

    def test_candidates_excludes_row_value(self):
        self.board.set(0, 1, 5)
        self.assertNotIn(5, self.board.candidates(0, 0))

    def test_candidates_excludes_col_value(self):
        self.board.set(1, 0, 8)
        self.assertNotIn(8, self.board.candidates(0, 0))

    def test_candidates_excludes_box_value(self):
        self.board.set(2, 2, 3)
        self.assertNotIn(3, self.board.candidates(0, 0))

    def test_empty_cells_decreases_on_set(self):
        self.assertEqual(len(self.board.empty_cells()), 81)
        self.board.set(0, 0, 1)
        self.board.set(1, 1, 2)
        self.assertEqual(len(self.board.empty_cells()), 79)

    def test_is_complete_false_on_new_board(self):
        self.assertFalse(self.board.is_complete())

    def test_is_complete_true_when_all_filled(self):
        for r in range(SIZE):
            for c in range(SIZE):
                self.board._grid[r][c].value = 1
        self.assertTrue(self.board.is_complete())

    def test_to_grid_matches_set_values(self):
        self.board.set(4, 4, 7)
        grid = self.board.to_grid()
        self.assertEqual(grid[4][4], 7)
        self.assertEqual(grid[0][0], EMPTY)


if __name__ == "__main__":
    unittest.main()
