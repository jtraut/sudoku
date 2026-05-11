from __future__ import annotations
from dataclasses import dataclass, field
from board import Board, SIZE, EMPTY


# TODO: might want to add a "hints_used" field here eventually — if we add a
# hint system that reveals one correct cell per request, the scoreboard could
# distinguish "clean" wins from ones where hints were needed
@dataclass
class VerificationResult:
    valid: bool
    complete: bool
    conflicts: list[tuple[int, int]] = field(default_factory=list)

    @property
    def solved(self) -> bool:
        # Both conditions required — a complete board with duplicates isn't solved,
        # and a valid but unfinished board isn't solved either
        return self.valid and self.complete


class Verifier:
    @staticmethod
    def check(board: Board) -> VerificationResult:
        conflicts: list[tuple[int, int]] = []

        # Check all rows and columns in one pass
        for i in range(SIZE):
            conflicts.extend(Verifier._group_conflicts(board.row(i), "row", i))
            conflicts.extend(Verifier._group_conflicts(board.col(i), "col", i))

        # Check all nine 3x3 boxes — iterate by box index (0-8) rather than
        # cell coordinates so we visit each box exactly once
        for br in range(3):
            for bc in range(3):
                r0, c0 = br * 3, bc * 3
                box_vals = board.box(r0, c0)
                conflicts.extend(Verifier._group_conflicts(box_vals, "box", br * 3 + bc))

        # A cell might appear in conflicts from multiple groups (e.g. bad row AND bad box),
        # dict.fromkeys strips duplicates while preserving insertion order
        unique_conflicts = list(dict.fromkeys(conflicts))
        return VerificationResult(
            valid=len(unique_conflicts) == 0,
            complete=board.is_complete(),
            conflicts=unique_conflicts,
        )

    @staticmethod
    def _group_conflicts(
        values: list[int], kind: str, index: int
    ) -> list[tuple[int, int]]:
        # Map each value to the positions where it appears within this group.
        # Any value showing up more than once is a conflict
        seen: dict[int, list[int]] = {}
        for pos, v in enumerate(values):
            if v == EMPTY:
                continue  # blank cells can't conflict with anything
            seen.setdefault(v, []).append(pos)

        conflicts: list[tuple[int, int]] = []
        for positions in seen.values():
            if len(positions) > 1:
                for pos in positions:
                    # Convert the group-local position back to (row, col) board coordinates
                    if kind == "row":
                        conflicts.append((index, pos))
                    elif kind == "col":
                        conflicts.append((pos, index))
                    else:
                        # box: index is 0-8 (top-left to bottom-right reading order),
                        # pos is 0-8 within the box (also row-major)
                        r0, c0 = (index // 3) * 3, (index % 3) * 3
                        conflicts.append((r0 + pos // 3, c0 + pos % 3))
        return conflicts

    @staticmethod
    def is_valid_placement(board: Board, row: int, col: int, value: int) -> bool:
        # Clearing a cell is always valid — no constraint checking needed
        if value == EMPTY:
            return True
        if value in board.row(row):
            return False
        if value in board.col(col):
            return False
        if value in board.box(row, col):
            return False
        return True
