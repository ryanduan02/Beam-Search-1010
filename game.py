import argparse
import json
import random
from typing import Any, Dict, Iterable, List, Optional, Tuple

BOARD_SIZE = 10
# pieces.py

# Each piece is a dict with:
# - "name": for debugging/printing
# - "shape": a 2D list of 0/1 values
#
# 1 means the cell is part of the piece, 0 means empty (padding).

PIECES_IN_HAND = 3
DEFAULT_VALUE = 1

PIECES = [
    # 1-block
    {"name": "single", "shape": [[1]]},
    # 2-block line
    {"name": "line2_h", "shape": [[1, 1]]},
    {"name": "line2_v", "shape": [[1], [1]]},
    # 3-block line
    {"name": "line3_h", "shape": [[1, 1, 1]]},
    {"name": "line3_v", "shape": [[1], [1], [1]]},
    # 4-block line
    {"name": "line4_h", "shape": [[1, 1, 1, 1]]},
    {"name": "line4_v", "shape": [[1], [1], [1], [1]]},
    # 5-block line (very 1010-style)
    {"name": "line5_h", "shape": [[1, 1, 1, 1, 1]]},
    {"name": "line5_v", "shape": [[1], [1], [1], [1], [1]]},
    # 2x2 square
    {"name": "square2", "shape": [[1, 1], [1, 1]]},
    # 3x3 square
    {"name": "square3", "shape": [[1, 1, 1], [1, 1, 1], [1, 1, 1]]},
    # L-shape (3 blocks)
    {"name": "L3_down_right", "shape": [[1, 0], [1, 0], [1, 1]]},
    # Another L-shape (rotated)
    {"name": "L3_down_left", "shape": [[0, 1], [0, 1], [1, 1]]},
    # Plus shape (cross)
    {"name": "plus", "shape": [[0, 1, 0], [1, 1, 1], [0, 1, 0]]},
]


def main():
    board = create_empty_board()
    score = 0
    hand = generate_hand(PIECES_IN_HAND, PIECES)

    print("Welcome to 1010 (console version)!")
    print("Fill rows/columns completely to clear them.")
    print("Type 'q' when choosing a piece to quit.\n")

    while True:
        print("Current board:")
        print_board(board)
        print(f"Score: {score}")
        print_hand(hand)

        # Check for game over BEFORE asking for a move
        if not any_move_possible(board, hand):
            print("No more possible moves. Game over!")
            print("Final score:", score)
            break

        move = get_player_move(hand)
        if move is None:
            print("You quit the game.")
            print("Final score:", score)
            break

        piece_index, row, col = move
        piece = hand[piece_index]

        if not can_place(board, piece, row, col):
            print("You can't place that piece there. Try again.\n")
            continue

        # Place the piece
        place_piece(board, piece, row, col)

        # Scoring: blocks placed + bonus for cleared cells
        blocks = piece_block_count(piece)
        cleared_cells, rows_cleared, cols_cleared = clear_lines(board)

        score += calculate_score(piece, cleared_cells)

        print(f"Placed '{piece['name']}' at ({row}, {col}).")
        if rows_cleared or cols_cleared:
            print(f"Cleared {rows_cleared} rows and {cols_cleared} columns!")
        print(
            f"+{blocks} for blocks, +{cleared_cells} for clears. New score: {score}\n"
        )

        # Remove used piece from hand
        del hand[piece_index]

        # If hand is empty, deal new 3 pieces
        if not hand:
            print("All pieces used. Dealing new hand...\n")
            hand = generate_hand(PIECES_IN_HAND, PIECES)


def _piece_by_name(name: str) -> dict:
    for p in PIECES:
        if p.get("name") == name:
            return p
    raise KeyError(f"Unknown piece name: {name!r}")


def _load_json_or_jsonl(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        raise ValueError("Replay file is empty")

    # Prefer JSON if it parses; fall back to JSONL.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        out: List[Any] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
        return out


def _extract_steps_from_game_result(
    game_result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    for segment in game_result.get("segments", []) or []:
        hand_names = segment.get("hand")
        for move_info in segment.get("moves", []) or []:
            mv = move_info.get("move") or {}
            steps.append(
                {
                    "hand": list(hand_names) if isinstance(hand_names, list) else None,
                    "piece_index": mv.get("piece_index"),
                    "piece_name": mv.get("piece_name"),
                    "piece": mv.get("piece"),
                    "row": mv.get("row"),
                    "col": mv.get("col"),
                    "delta": move_info.get("delta"),
                    "cleared_cells": move_info.get("cleared_cells"),
                    "rows_cleared": move_info.get("rows_cleared"),
                    "cols_cleared": move_info.get("cols_cleared"),
                    "score_after": move_info.get("score_after"),
                }
            )
    return steps


def _extract_steps(payload: Any, game_index: int = 0) -> List[Dict[str, Any]]:
    # Case 1: list[game_result]
    if (
        isinstance(payload, list)
        and payload
        and isinstance(payload[0], dict)
        and "segments" in payload[0]
    ):
        if game_index < 0 or game_index >= len(payload):
            raise IndexError("game_index out of range")
        return _extract_steps_from_game_result(payload[game_index])

    # Case 2: single game_result dict
    if isinstance(payload, dict) and "segments" in payload:
        return _extract_steps_from_game_result(payload)

    # Case 3: moves-only list (best effort)
    if isinstance(payload, list) and (not payload or isinstance(payload[0], dict)):
        steps: List[Dict[str, Any]] = []
        for mv in payload:
            if not isinstance(mv, dict):
                continue
            steps.append(
                {
                    "hand": None,
                    "piece_index": mv.get("piece_index"),
                    "piece_name": mv.get("piece_name"),
                    "piece": mv.get("piece"),
                    "row": mv.get("row"),
                    "col": mv.get("col"),
                    "delta": mv.get("delta"),
                    "cleared_cells": mv.get("cleared_cells"),
                    "rows_cleared": mv.get("rows_cleared"),
                    "cols_cleared": mv.get("cols_cleared"),
                    "score_after": mv.get("score_after"),
                }
            )
        return steps

    raise ValueError(
        "Unrecognized replay JSON format. Expected simulate_beam output (game results) or a moves list."
    )


def _coerce_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def replay(path: str, *, game_index: int = 0) -> None:
    payload = _load_json_or_jsonl(path)
    steps = _extract_steps(payload, game_index=game_index)
    if not steps:
        print("No moves found in replay file.")
        return

    board = create_empty_board()
    score = 0

    print(f"Replay loaded: {len(steps)} moves")
    print("Controls: Enter/next = advance, q = quit, ? = help\n")
    print("Initial board:")
    print_board(board)

    last_hand: Optional[List[str]] = None

    i = 0
    while i < len(steps):
        cmd = input("[enter]=next, q=quit, ?=help > ").strip().lower()
        if cmd in ("q", "quit", "exit"):
            print("Exiting replay.")
            return
        if cmd in ("?", "help"):
            print("Commands: Enter | n | next (advance), q (quit), ? (help)\n")
            continue
        if cmd not in ("", "n", "next"):
            print("Unknown command. Type ? for help.\n")
            continue

        step = steps[i]
        row = _coerce_int(step.get("row"))
        col = _coerce_int(step.get("col"))
        if row is None or col is None:
            raise ValueError(f"Move {i} missing row/col")

        hand = step.get("hand")
        if isinstance(hand, list) and hand != last_hand:
            print(f"New hand: {hand}")
            last_hand = hand

        piece: Optional[dict] = None
        piece_dict = step.get("piece")
        if isinstance(piece_dict, dict) and "shape" in piece_dict:
            piece = piece_dict
        else:
            piece_name = step.get("piece_name")
            if isinstance(piece_name, str):
                piece = _piece_by_name(piece_name)

        if piece is None:
            raise ValueError(f"Move {i} missing piece information")

        print(f"Move {i+1}/{len(steps)}: place '{piece.get('name')}' at ({row}, {col})")
        print_piece(piece)

        if not can_place(board, piece, row, col):
            raise ValueError(
                f"Illegal placement at move {i+1}: {piece.get('name')} @ ({row},{col})"
            )

        place_piece(board, piece, row, col)
        cleared_cells, rows_cleared, cols_cleared = clear_lines(board)
        score += calculate_score(piece, cleared_cells)

        print_board(board)
        if rows_cleared or cols_cleared:
            print(
                f"Cleared {rows_cleared} rows and {cols_cleared} columns (+{cleared_cells} cells)"
            )
        expected = _coerce_int(step.get("score_after"))
        if expected is not None and expected != score:
            print(f"Score: {score} (note: file says {expected})\n")
        else:
            print(f"Score: {score}\n")

        i += 1

    print(f"Replay complete. Final score: {score}")


def calculate_score(piece, cleared_cells):
    return sum(map(sum, piece["shape"])) + cleared_cells


def print_hand(hand):
    """Show the current hand with indexes."""
    print("Current hand:")
    for i, piece in enumerate(hand):
        print(f"[{i}] {piece['name']}")
        print_piece(piece)


def get_player_move(hand):
    """
    Ask the player which piece to place and where.
    Returns (piece_index, row, col) or None if player quits.
    """
    while True:
        choice = input("Choose piece index (or 'q' to quit): ").strip()
        if choice.lower() == "q":
            return None

        # Validate piece index
        if not choice.isdigit():
            print("Please enter a number for the piece index.")
            continue

        piece_index = int(choice)
        if piece_index < 0 or piece_index >= len(hand):
            print("Invalid index. Try again.")
            continue

        # Get row
        row_str = input("Row (0-9): ").strip()
        col_str = input("Col (0-9): ").strip()

        if not (row_str.isdigit() and col_str.isdigit()):
            print("Row and column must be numbers. Try again.")
            continue

        row = int(row_str)
        col = int(col_str)

        return piece_index, row, col


def generate_hand(num_pieces: int, pieces):
    """
    Generate a list of random pieces (the 'hand' the player can choose from).
    Pieces can repeat, which is fine for a simple version.
    """
    all_pieces = get_all_pieces(pieces)
    hand = [random.choice(all_pieces) for _ in range(num_pieces)]
    return hand


def get_all_pieces(pieces):
    """Return the list of all defined pieces."""
    return pieces


def piece_block_count(piece):
    """Return how many '1' cells are in this piece."""
    shape = piece["shape"]
    return sum(sum(row) for row in shape)


def print_piece(piece):
    """Print a piece shape nicely for debugging."""
    print(piece["name"])
    for row in piece["shape"]:
        print(" ".join("#" if cell == 1 else "." for cell in row))
    print()


def any_move_possible(board, pieces):
    """
    Return True if at least one of the given pieces can be placed
    somewhere on the board. Otherwise, return False.
    """
    height = len(board)
    width = len(board[0]) if height > 0 else 0

    for piece in pieces:
        shape = piece["shape"]
        piece_h = len(shape)
        piece_w = len(shape[0])

        # Try every possible top-left position
        for row in range(height):
            for col in range(width):
                if can_place(board, piece, row, col):
                    return True  # found at least one legal move

    # No placement worked for any piece
    return False


def can_place(board, piece, row, col):
    """
    Return True if the piece can be legally placed on the board
    with its top-left corner at (row, col).
    """
    shape = piece["shape"]
    piece_h = len(shape)
    piece_w = len(shape[0])

    for i in range(piece_h):  # i = row in piece shape
        for j in range(piece_w):  # j = col in piece shape
            if shape[i][j] == 1:

                # Board coordinates this block would occupy
                br = row + i
                bc = col + j

                # Check bounds
                if br < 0 or br >= len(board):
                    return False
                if bc < 0 or bc >= len(board[0]):
                    return False

                # Check if board cell is empty
                if board[br][bc] != 0:
                    return False

    # All checks passed!
    return True


def clear_lines(board):
    """
    Clear all completely filled rows and columns.

    Mutates the board in place.
    Returns:
        cells_cleared, rows_cleared, cols_cleared
    """
    height = len(board)
    width = len(board[0]) if height > 0 else 0

    full_rows = []
    full_cols = []

    # 1) Find full rows
    for r in range(height):
        if all(board[r][c] != 0 for c in range(width)):
            full_rows.append(r)

    # 2) Find full columns
    for c in range(width):
        if all(board[r][c] != 0 for r in range(height)):
            full_cols.append(c)

    cells_cleared = 0

    # 3) Clear full rows
    for r in full_rows:
        for c in range(width):
            if board[r][c] != 0:
                board[r][c] = 0
                cells_cleared += 1

    # 4) Clear full columns
    for c in full_cols:
        for r in range(height):
            if board[r][c] != 0:
                board[r][c] = 0
                cells_cleared += 1

    return cells_cleared, len(full_rows), len(full_cols)


def place_piece(board, piece, row, col, value=DEFAULT_VALUE):
    """
    Place the piece on the board with its top-left corner at (row, col).

    Mutates the board in place.
    Assumes the move is valid (can_place == True).
    If it's not valid, raises a ValueError.
    """

    if not can_place(board, piece, row, col):
        raise ValueError("Invalid placement: piece does not fit at the given position")

    shape = piece["shape"]
    piece_h = len(shape)
    piece_w = len(shape[0])

    for i in range(piece_h):
        for j in range(piece_w):
            if shape[i][j] == 1:
                br = row + i
                bc = col + j
                board[br][bc] = value  # default is 1 (filled)


def create_empty_board():
    """Return a 10x10 board filled with 0s (empty cells)."""
    return [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def print_board(board):
    """Print the board in a simple text form."""
    for row in board:
        # '.' for empty, '#' for filled (later we'll use 1 instead of 0)
        print(" ".join("." if cell == 0 else "#" for cell in row))
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--replay",
        type=str,
        default=None,
        help="Path to a simulate_beam JSON/JSONL output file to replay interactively.",
    )
    parser.add_argument(
        "--game-index",
        type=int,
        default=0,
        help="When replaying a JSON array of games, choose which game to replay.",
    )
    args = parser.parse_args()

    if args.replay:
        replay(args.replay, game_index=args.game_index)
    else:
        main()
