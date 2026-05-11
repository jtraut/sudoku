from __future__ import annotations
from typing import Optional


# 0 means empty — easy to check falsy and plays nice with default int values
EMPTY = 0
SIZE = 9
BOX_SIZE = 3  # 3x3 sub-grids (boxes) within the 9x9 grid


class Cell:
    def __init__(self, value: int = EMPTY, given: bool = False):
        self.value = value
        # given = pre-filled by the puzzle generator, player cannot overwrite these
        self.given = given

    def __repr__(self) -> str:
        return f"Cell({self.value}, given={self.given})"


class Board:
    def __init__(self):
        # 9x9 grid of Cells, all empty to start
        self._grid: list[list[Cell]] = [
            [Cell() for _ in range(SIZE)] for _ in range(SIZE)
        ]

    @classmethod
    def from_grid(cls, values: list[list[int]], mark_given: bool = True) -> "Board":
        # Handy for loading a puzzle from a plain 2D list of ints
        # Non-zero cells are treated as locked givens by default
        board = cls()
        for r in range(SIZE):
            for c in range(SIZE):
                v = values[r][c]
                board._grid[r][c] = Cell(v, given=(v != EMPTY and mark_given))
        return board

    def copy(self) -> "Board":
        # Deep copy — solver and generator both need to work on isolated boards
        # without touching the original
        new = Board()
        for r in range(SIZE):
            for c in range(SIZE):
                cell = self._grid[r][c]
                new._grid[r][c] = Cell(cell.value, cell.given)
        return new

    # --- Cell access ---

    def get(self, row: int, col: int) -> int:
        return self._grid[row][col].value

    def set(self, row: int, col: int, value: int) -> bool:
        # Returns False instead of raising if the cell is locked — lets the game
        # give the player a friendly warning rather than blowing up
        if not (0 <= row < SIZE and 0 <= col < SIZE):
            raise IndexError(f"Position ({row},{col}) out of range")
        if not (EMPTY <= value <= SIZE):
            raise ValueError(f"Value {value} out of range (0-9)")
        cell = self._grid[row][col]
        if cell.given:
            return False  # can't touch the pre-filled numbers
        cell.value = value
        return True

    def is_given(self, row: int, col: int) -> bool:
        return self._grid[row][col].given

    def clear(self, row: int, col: int) -> bool:
        # Clearing is just setting to EMPTY — reuses all the same guard logic
        return self.set(row, col, EMPTY)

    # --- Bulk queries ---

    def row(self, row: int) -> list[int]:
        return [self._grid[row][c].value for c in range(SIZE)]

    def col(self, col: int) -> list[int]:
        return [self._grid[r][col].value for r in range(SIZE)]

    def box(self, row: int, col: int) -> list[int]:
        # Find the top-left corner of whichever 3x3 box this cell belongs to,
        # then collect all 9 values from that box
        r0 = (row // BOX_SIZE) * BOX_SIZE
        c0 = (col // BOX_SIZE) * BOX_SIZE
        return [
            self._grid[r0 + dr][c0 + dc].value
            for dr in range(BOX_SIZE)
            for dc in range(BOX_SIZE)
        ]

    def to_grid(self) -> list[list[int]]:
        # Flatten back to a plain 2D int list — useful for tests and serialization
        return [[self._grid[r][c].value for c in range(SIZE)] for r in range(SIZE)]

    def empty_cells(self) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(SIZE)
            for c in range(SIZE)
            if self._grid[r][c].value == EMPTY
        ]

    def candidates(self, row: int, col: int) -> set[int]:
        # Collect everything already used in the row, column, and box,
        # then whatever's left from 1-9 is fair game for this cell.
        # Called a LOT by the solver on every recursive step so keeping it simple matters
        used = set(self.row(row)) | set(self.col(col)) | set(self.box(row, col))
        return set(range(1, SIZE + 1)) - used

    def is_complete(self) -> bool:
        # Just checks if anything is still empty — doesn't verify correctness,
        # that's the Verifier's job
        return all(
            self._grid[r][c].value != EMPTY
            for r in range(SIZE)
            for c in range(SIZE)
        )
