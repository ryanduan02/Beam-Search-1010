from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, Tuple

from .pieces import Piece


Board = Tuple[Tuple[int, ...], ...]  # 0 = empty, non-zero = filled


def empty_board(size: int = 10) -> Board:
    if size <= 0:
        raise ValueError("size must be positive")
    return tuple(tuple(0 for _ in range(size)) for _ in range(size))


def board_from_rows(rows: Sequence[Sequence[int]]) -> Board:
    if len(rows) == 0:
        raise ValueError("board must have at least one row")
    width_set = {len(r) for r in rows}
    if len(width_set) != 1:
        raise ValueError("board must be rectangular")
    width = next(iter(width_set))
    if width == 0:
        raise ValueError("board must have at least one column")

    normalized: list[tuple[int, ...]] = []
    for row in rows:
        normalized_row = []
        for cell in row:
            if int(cell) != cell:
                cell = int(cell)
            if cell < 0:
                raise ValueError("board cells must be >= 0")
            normalized_row.append(int(cell))
        normalized.append(tuple(normalized_row))
    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class GameState:
    """A deterministic search state (Option A).

    State includes everything that affects future legality and score:
    - board: 10x10 grid (0 empty, non-zero filled)
    - score: accumulated score
    - hand: remaining pieces in the current hand (0–3)

    This state intentionally does NOT include RNG/upcoming hands.
    """

    board: Board
    score: int
    hand: Tuple[Piece, ...]

    def __post_init__(self) -> None:
        if self.score < 0:
            raise ValueError("score must be >= 0")
        if len(self.hand) > 3:
            raise ValueError("hand must have 0–3 pieces")
        _validate_board(self.board)

    @property
    def size(self) -> int:
        return len(self.board)

    @property
    def is_hand_empty(self) -> bool:
        return len(self.hand) == 0

    def with_hand(self, hand: Iterable[Piece]) -> "GameState":
        return GameState(board=self.board, score=self.score, hand=tuple(hand))

    def remove_hand_index(self, index: int) -> "GameState":
        if index < 0 or index >= len(self.hand):
            raise IndexError("hand index out of range")
        new_hand = self.hand[:index] + self.hand[index + 1 :]
        return GameState(board=self.board, score=self.score, hand=new_hand)

    @staticmethod
    def from_game_py(board: Sequence[Sequence[int]], score: int, hand: Sequence[Mapping]) -> "GameState":
        """Convert from the existing `game.py` structures.

        - board: list[list[int]]
        - hand: list[dict] where each dict has keys {name, shape}
        """
        return GameState(
            board=board_from_rows(board),
            score=int(score),
            hand=tuple(Piece.from_dict(p) for p in hand),
        )

    def to_game_py(self) -> tuple[list[list[int]], int, list[dict]]:
        """Convert back to the existing `game.py` structures."""
        board_list = [list(row) for row in self.board]
        hand_list = [p.to_dict() for p in self.hand]
        return board_list, int(self.score), hand_list


def _validate_board(board: Board) -> None:
    if len(board) == 0:
        raise ValueError("board must have at least one row")
    width = len(board[0])
    if width == 0:
        raise ValueError("board must have at least one column")
    for row in board:
        if len(row) != width:
            raise ValueError("board must be rectangular")
        for cell in row:
            if cell < 0:
                raise ValueError("board cells must be >= 0")
