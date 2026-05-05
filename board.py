from __future__ import annotations
from typing import Optional


EMPTY = 0
SIZE = 9
BOX_SIZE = 3


class Cell:
    def __init__(self, value: int = EMPTY, given: bool = False):
        self.value = value
        self.given = given  # True if placed by puzzle generator (not editable)

    def __repr__(self) -> str:
        return f"Cell({self.value}, given={self.given})"


class Board:
    def __init__(self):
        self._grid: list[list[Cell]] = [
            [Cell() for _ in range(SIZE)] for _ in range(SIZE)
        ]

    @classmethod
    def from_grid(cls, values: list[list[int]], mark_given: bool = True) -> "Board":
        board = cls()
        for r in range(SIZE):
            for c in range(SIZE):
                v = values[r][c]
                board._grid[r][c] = Cell(v, given=(v != EMPTY and mark_given))
        return board

    def copy(self) -> "Board":
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
        """Set a cell value. Returns False if the cell is a given (read-only)."""
        if not (0 <= row < SIZE and 0 <= col < SIZE):
            raise IndexError(f"Position ({row},{col}) out of range")
        if not (EMPTY <= value <= SIZE):
            raise ValueError(f"Value {value} out of range (0-9)")
        cell = self._grid[row][col]
        if cell.given:
            return False
        cell.value = value
        return True

    def is_given(self, row: int, col: int) -> bool:
        return self._grid[row][col].given

    def clear(self, row: int, col: int) -> bool:
        return self.set(row, col, EMPTY)

    # --- Bulk queries ---

    def row(self, row: int) -> list[int]:
        return [self._grid[row][c].value for c in range(SIZE)]

    def col(self, col: int) -> list[int]:
        return [self._grid[r][col].value for r in range(SIZE)]

    def box(self, row: int, col: int) -> list[int]:
        r0 = (row // BOX_SIZE) * BOX_SIZE
        c0 = (col // BOX_SIZE) * BOX_SIZE
        return [
            self._grid[r0 + dr][c0 + dc].value
            for dr in range(BOX_SIZE)
            for dc in range(BOX_SIZE)
        ]

    def to_grid(self) -> list[list[int]]:
        return [[self._grid[r][c].value for c in range(SIZE)] for r in range(SIZE)]

    def empty_cells(self) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(SIZE)
            for c in range(SIZE)
            if self._grid[r][c].value == EMPTY
        ]

    def candidates(self, row: int, col: int) -> set[int]:
        used = set(self.row(row)) | set(self.col(col)) | set(self.box(row, col))
        return set(range(1, SIZE + 1)) - used

    def is_complete(self) -> bool:
        return all(
            self._grid[r][c].value != EMPTY
            for r in range(SIZE)
            for c in range(SIZE)
        )
