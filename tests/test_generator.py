import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from generator import Generator, Difficulty
from solver import Solver
from verifier import Verifier


class TestGeneratorOutput(unittest.TestCase):
    """Tests that run a single generation per difficulty — kept fast by reusing
    the same instance so the solver is only initialised once."""

    @classmethod
    def setUpClass(cls):
        cls.gen = Generator()
        cls.solver = Solver()
        # Generate one puzzle per difficulty level up front
        cls.boards = {d: cls.gen.generate(d) for d in Difficulty}

    def _board(self, difficulty):
        return self.boards[difficulty]

    # --- Structural checks ---

    def test_easy_given_count_in_range(self):
        givens = 81 - len(self._board(Difficulty.EASY).empty_cells())
        self.assertGreaterEqual(givens, Difficulty.EASY.given_count - 5)
        self.assertLessEqual(givens, Difficulty.EASY.given_count + 5)

    def test_medium_given_count_in_range(self):
        givens = 81 - len(self._board(Difficulty.MEDIUM).empty_cells())
        self.assertGreaterEqual(givens, Difficulty.MEDIUM.given_count - 5)
        self.assertLessEqual(givens, Difficulty.MEDIUM.given_count + 5)

    def test_hard_given_count_in_range(self):
        givens = 81 - len(self._board(Difficulty.HARD).empty_cells())
        self.assertGreaterEqual(givens, Difficulty.HARD.given_count - 5)
        self.assertLessEqual(givens, Difficulty.HARD.given_count + 5)

    def test_expert_given_count_in_range(self):
        givens = 81 - len(self._board(Difficulty.EXPERT).empty_cells())
        self.assertGreaterEqual(givens, Difficulty.EXPERT.given_count - 5)
        self.assertLessEqual(givens, Difficulty.EXPERT.given_count + 5)

    def test_harder_difficulties_have_fewer_givens(self):
        easy_givens   = 81 - len(self._board(Difficulty.EASY).empty_cells())
        medium_givens = 81 - len(self._board(Difficulty.MEDIUM).empty_cells())
        hard_givens   = 81 - len(self._board(Difficulty.HARD).empty_cells())
        expert_givens = 81 - len(self._board(Difficulty.EXPERT).empty_cells())
        self.assertGreaterEqual(easy_givens, medium_givens)
        self.assertGreaterEqual(medium_givens, hard_givens)
        self.assertGreaterEqual(hard_givens, expert_givens)

    # --- Validity checks ---

    def test_generated_board_has_no_conflicts(self):
        for difficulty, board in self.boards.items():
            with self.subTest(difficulty=difficulty.value):
                result = Verifier.check(board)
                self.assertTrue(result.valid, f"{difficulty.value} puzzle has conflicts")

    def test_generated_board_is_not_already_complete(self):
        for difficulty, board in self.boards.items():
            with self.subTest(difficulty=difficulty.value):
                self.assertFalse(board.is_complete(),
                                 f"{difficulty.value} puzzle should have empty cells")

    # --- Solvability / uniqueness ---

    def test_generated_board_is_solvable(self):
        for difficulty, board in self.boards.items():
            with self.subTest(difficulty=difficulty.value):
                solution = self.solver.solve_copy(board)
                self.assertIsNotNone(solution,
                                     f"{difficulty.value} puzzle could not be solved")

    def test_generated_board_solution_is_valid(self):
        for difficulty, board in self.boards.items():
            with self.subTest(difficulty=difficulty.value):
                solution = self.solver.solve_copy(board)
                self.assertTrue(Verifier.check(solution).solved)

    def test_generated_board_has_unique_solution(self):
        for difficulty, board in self.boards.items():
            with self.subTest(difficulty=difficulty.value):
                count = self.solver.count_solutions(board, limit=2)
                self.assertEqual(count, 1,
                                 f"{difficulty.value} puzzle does not have a unique solution")

    # --- Given-cell protection ---

    def test_given_cells_cannot_be_overwritten(self):
        board = self._board(Difficulty.EASY)
        for r in range(9):
            for c in range(9):
                if board.is_given(r, c):
                    original = board.get(r, c)
                    result = board.set(r, c, (original % 9) + 1)
                    self.assertFalse(result)
                    self.assertEqual(board.get(r, c), original)
                    break  # one cell is enough per test
            else:
                continue
            break


if __name__ == "__main__":
    unittest.main()
