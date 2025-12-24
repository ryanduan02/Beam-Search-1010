from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, Tuple

Shape = Tuple[Tuple[int, ...], ...]

@dataclass(frozen=True, slots=True)
class Piece:
    """A placeable piece.

    Matches the existing `game.py` piece dict format:
    - name: str
    - shape: 2D 0/1 grid (1 = occupied)
    """

    name: str
    shape: Shape

    @property
    def height(self) -> int:
        return len(self.shape)

    @property
    def width(self) -> int:
        return len(self.shape[0]) if self.shape else 0

    @property
    def block_count(self) -> int:
        return sum(sum(row) for row in self.shape)

    @staticmethod
    def from_dict(piece: Mapping) -> "Piece":
        name = str(piece.get("name", ""))
        raw_shape = piece.get("shape")
        if raw_shape is None:
            raise ValueError("piece dict must include 'shape'")
        return Piece(name=name, shape=_to_shape(raw_shape))

    def to_dict(self) -> dict:
        return {"name": self.name, "shape": [list(row) for row in self.shape]}


def _to_shape(shape: Sequence[Sequence[int]]) -> Shape:
    if len(shape) == 0:
        raise ValueError("shape must have at least one row")
    row_lengths = {len(r) for r in shape}
    if len(row_lengths) != 1:
        raise ValueError("shape must be rectangular")
    if 0 in row_lengths:
        raise ValueError("shape must have at least one column")

    normalized: list[tuple[int, ...]] = []
    for row in shape:
        normalized_row = []
        for cell in row:
            if cell not in (0, 1):
                raise ValueError("shape cells must be 0 or 1")
            normalized_row.append(int(cell))
        normalized.append(tuple(normalized_row))
    return tuple(normalized)


def pieces_from_dicts(pieces: Iterable[Mapping]) -> Tuple[Piece, ...]:
    return tuple(Piece.from_dict(p) for p in pieces)
