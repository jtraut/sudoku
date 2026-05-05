from __future__ import annotations
from dataclasses import dataclass, field
from board import Board, SIZE, EMPTY


@dataclass
class VerificationResult:
    valid: bool
    complete: bool
    conflicts: list[tuple[int, int]] = field(default_factory=list)

    @property
    def solved(self) -> bool:
        return self.valid and self.complete


class Verifier:
    @staticmethod
    def check(board: Board) -> VerificationResult:
        conflicts: list[tuple[int, int]] = []

        for i in range(SIZE):
            conflicts.extend(Verifier._group_conflicts(board.row(i), "row", i))
            conflicts.extend(Verifier._group_conflicts(board.col(i), "col", i))

        for br in range(3):
            for bc in range(3):
                r0, c0 = br * 3, bc * 3
                box_vals = board.box(r0, c0)
                conflicts.extend(Verifier._group_conflicts(box_vals, "box", br * 3 + bc))

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
        seen: dict[int, list[int]] = {}
        for pos, v in enumerate(values):
            if v == EMPTY:
                continue
            seen.setdefault(v, []).append(pos)

        conflicts: list[tuple[int, int]] = []
        for positions in seen.values():
            if len(positions) > 1:
                for pos in positions:
                    if kind == "row":
                        conflicts.append((index, pos))
                    elif kind == "col":
                        conflicts.append((pos, index))
                    else:
                        r0, c0 = (index // 3) * 3, (index % 3) * 3
                        conflicts.append((r0 + pos // 3, c0 + pos % 3))
        return conflicts

    @staticmethod
    def is_valid_placement(board: Board, row: int, col: int, value: int) -> bool:
        if value == EMPTY:
            return True
        if value in board.row(row):
            return False
        if value in board.col(col):
            return False
        if value in board.box(row, col):
            return False
        return True
