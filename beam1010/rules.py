from __future__ import annotations

from typing import Tuple

from .pieces import Piece
from .state import Board, GameState


def can_place(board: Board, piece: Piece, row: int, col: int) -> bool:
    """True if `piece` fits at (row, col) without overlap."""
    for i in range(piece.height):
        for j in range(piece.width):
            if piece.shape[i][j] != 1:
                continue
            br = row + i
            bc = col + j
            if br < 0 or br >= len(board):
                return False
            if bc < 0 or bc >= len(board[0]):
                return False
            if board[br][bc] != 0:
                return False
    return True


def place_piece(
    board: Board, piece: Piece, row: int, col: int, value: int = 1
) -> Board:
    """Return a new board with `piece` placed at (row, col)."""
    if not can_place(board, piece, row, col):
        raise ValueError("Invalid placement")

    grid = [list(r) for r in board]
    for i in range(piece.height):
        for j in range(piece.width):
            if piece.shape[i][j] == 1:
                grid[row + i][col + j] = value
    return tuple(tuple(r) for r in grid)


def clear_lines(board: Board) -> tuple[Board, int, int, int]:
    """Clear full rows/cols. Returns (new_board, cells, rows, cols)."""
    height = len(board)
    width = len(board[0])

    full_rows = [
        r for r in range(height) if all(board[r][c] != 0 for c in range(width))
    ]
    full_cols = [
        c for c in range(width) if all(board[r][c] != 0 for r in range(height))
    ]

    if not full_rows and not full_cols:
        return board, 0, 0, 0

    grid = [list(r) for r in board]
    cells_cleared = 0

    for r in full_rows:
        for c in range(width):
            if grid[r][c] != 0:
                grid[r][c] = 0
                cells_cleared += 1

    for c in full_cols:
        for r in range(height):
            if grid[r][c] != 0:
                grid[r][c] = 0
                cells_cleared += 1

    new_board = tuple(tuple(r) for r in grid)
    return new_board, cells_cleared, len(full_rows), len(full_cols)


def score_delta(piece: Piece, cleared_cells: int) -> int:
    """Matches `game.py`: placed blocks + cleared cells."""
    return piece.block_count + cleared_cells


def simulate_move(
    state: GameState, hand_index: int, row: int, col: int
) -> Tuple[GameState, int, int, int, int]:
    """Pure move simulation (backbone for beam search).

    Validates legality, creates a new board, places the selected piece,
    clears completed lines, updates score, and removes the used piece
    from the returned state's hand.

    Returns:
        (new_state, delta, cleared_cells, rows_cleared, cols_cleared)
    """
    piece = state.hand[hand_index]
    new_board = place_piece(state.board, piece, row, col)
    new_board, cleared_cells, rows_cleared, cols_cleared = clear_lines(new_board)
    delta = score_delta(piece, cleared_cells)

    new_hand = state.hand[:hand_index] + state.hand[hand_index + 1 :]
    new_state = GameState(board=new_board, score=state.score + delta, hand=new_hand)
    return new_state, delta, cleared_cells, rows_cleared, cols_cleared


def apply_move(
    state: GameState, hand_index: int, row: int, col: int
) -> Tuple[GameState, int, int, int]:
    """Apply placing `state.hand[hand_index]` at (row, col).

    Returns (new_state, cleared_cells, rows_cleared, cols_cleared).

    Note: does NOT draw a new hand when empty (Option A). Caller controls that.
    """
    new_state, _delta, cleared_cells, rows_cleared, cols_cleared = simulate_move(
        state, hand_index=hand_index, row=row, col=col
    )
    return new_state, cleared_cells, rows_cleared, cols_cleared
