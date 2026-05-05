import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from board import Board, EMPTY
from solver import Solver
from verifier import Verifier

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


def _puzzle_board():
    return Board.from_grid(_PUZZLE)


def _solved_board():
    return Board.from_grid(_SOLUTION)


def _unsolvable_board():
    # Row 0 cols 1-8 hold values 1-8, so the only missing value for (0,0) is 9.
    # Col 0 row 1 holds 9, removing 9 as a candidate for (0,0).
    # Result: cell (0,0) has zero candidates → no solution exists.
    grid = [[0] * 9 for _ in range(9)]
    for c, v in enumerate(range(1, 9), start=1):
        grid[0][c] = v   # row 0 contains 1-8 (9 is the only gap)
    grid[1][0] = 9       # col 0 already contains 9
    return Board.from_grid(grid)


class TestSolveCopy(unittest.TestCase):
    def setUp(self):
        self.solver = Solver()

    def test_returns_solved_board_for_valid_puzzle(self):
        solution = self.solver.solve_copy(_puzzle_board())
        self.assertIsNotNone(solution)
        result = Verifier.check(solution)
        self.assertTrue(result.solved)

    def test_solution_matches_known_answer(self):
        solution = self.solver.solve_copy(_puzzle_board())
        self.assertEqual(solution.to_grid(), _SOLUTION)

    def test_does_not_modify_original_board(self):
        original = _puzzle_board()
        original_grid = original.to_grid()
        self.solver.solve_copy(original)
        self.assertEqual(original.to_grid(), original_grid)

    def test_returns_none_for_unsolvable_board(self):
        solution = self.solver.solve_copy(_unsolvable_board())
        self.assertIsNone(solution)

    def test_already_solved_board_returns_copy(self):
        board = _solved_board()
        solution = self.solver.solve_copy(board)
        self.assertIsNotNone(solution)
        self.assertTrue(Verifier.check(solution).solved)


class TestSolveInPlace(unittest.TestCase):
    def setUp(self):
        self.solver = Solver()

    def test_returns_true_and_modifies_board(self):
        board = _puzzle_board()
        result = self.solver.solve(board)
        self.assertTrue(result)
        self.assertTrue(Verifier.check(board).solved)

    def test_returns_false_for_unsolvable_board(self):
        board = _unsolvable_board()
        result = self.solver.solve(board)
        self.assertFalse(result)


class TestCountSolutions(unittest.TestCase):
    def setUp(self):
        self.solver = Solver()

    def test_unique_puzzle_has_one_solution(self):
        self.assertEqual(self.solver.count_solutions(_puzzle_board(), limit=2), 1)

    def test_already_solved_board_has_one_solution(self):
        self.assertEqual(self.solver.count_solutions(_solved_board(), limit=2), 1)

    def test_empty_board_has_multiple_solutions(self):
        # An empty board has far more than 2 solutions
        count = self.solver.count_solutions(Board(), limit=2)
        self.assertEqual(count, 2)

    def test_sparse_board_has_multiple_solutions(self):
        # Only one given cell — definitely ambiguous
        grid = [[0] * 9 for _ in range(9)]
        grid[0][0] = 1
        board = Board.from_grid(grid)
        self.assertEqual(self.solver.count_solutions(board, limit=2), 2)

    def test_unsolvable_board_has_zero_solutions(self):
        self.assertEqual(self.solver.count_solutions(_unsolvable_board(), limit=2), 0)


if __name__ == "__main__":
    unittest.main()
