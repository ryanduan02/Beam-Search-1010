from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

from .rules import can_place
from .state import GameState


@dataclass(frozen=True, slots=True)
class Move:
    """A move: choose a piece from hand and place it at (row, col)."""

    piece_index: int
    row: int
    col: int


def legal_moves(state: GameState) -> Iterator[Move]:
    """Yield all legal moves from this state.

    A legal move is (piece_index, row, col) such that the piece fits and does not
    overlap occupied cells.

    Note: This enumerates *placements* only; it does not apply them.
    """

    board = state.board
    size_r = len(board)
    size_c = len(board[0])

    for piece_index, piece in enumerate(state.hand):
        # Bounding-box iteration reduces useless can_place calls.
        max_row = size_r - piece.height
        max_col = size_c - piece.width
        if max_row < 0 or max_col < 0:
            continue

        for row in range(max_row + 1):
            for col in range(max_col + 1):
                if can_place(board, piece, row, col):
                    yield Move(piece_index=piece_index, row=row, col=col)


def any_legal_move(state: GameState) -> bool:
    """Fast check: True if at least one legal move exists."""
    try:
        next(legal_moves(state))
        return True
    except StopIteration:
        return False


def filter_moves(moves: Iterable[Move], *, piece_index: int) -> Iterator[Move]:
    """Utility to filter an iterator of moves by piece_index."""
    for move in moves:
        if move.piece_index == piece_index:
            yield move
