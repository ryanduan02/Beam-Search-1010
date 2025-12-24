import random

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
    {
        "name": "single",
        "shape": [
            [1]
        ]
    },

    # 2-block line
    {
        "name": "line2_h",
        "shape": [
            [1, 1]
        ]
    },
    {
        "name": "line2_v",
        "shape": [
            [1],
            [1]
        ]
    },

    # 3-block line
    {
        "name": "line3_h",
        "shape": [
            [1, 1, 1]
        ]
    },
    {
        "name": "line3_v",
        "shape": [
            [1],
            [1],
            [1]
        ]
    },

    # 4-block line
    {
        "name": "line4_h",
        "shape": [
            [1, 1, 1, 1]
        ]
    },
    {
        "name": "line4_v",
        "shape": [
            [1],
            [1],
            [1],
            [1]
        ]
    },

    # 5-block line (very 1010-style)
    {
        "name": "line5_h",
        "shape": [
            [1, 1, 1, 1, 1]
        ]
    },
    {
        "name": "line5_v",
        "shape": [
            [1],
            [1],
            [1],
            [1],
            [1]
        ]
    },

    # 2x2 square
    {
        "name": "square2",
        "shape": [
            [1, 1],
            [1, 1]
        ]
    },

    # 3x3 square
    {
        "name": "square3",
        "shape": [
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
        ]
    },

    # L-shape (3 blocks)
    {
        "name": "L3_down_right",
        "shape": [
            [1, 0],
            [1, 0],
            [1, 1]
        ]
    },

    # Another L-shape (rotated)
    {
        "name": "L3_down_left",
        "shape": [
            [0, 1],
            [0, 1],
            [1, 1]
        ]
    },

    # Plus shape (cross)
    {
        "name": "plus",
        "shape": [
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0]
        ]
    },
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
        print(f"+{blocks} for blocks, +{cleared_cells} for clears. New score: {score}\n")

        # Remove used piece from hand
        del hand[piece_index]

        # If hand is empty, deal new 3 pieces
        if not hand:
            print("All pieces used. Dealing new hand...\n")
            hand = generate_hand(PIECES_IN_HAND, PIECES)
            
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
        if choice.lower() == 'q':
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

def print_hand(hand):
    """Print all pieces in the current hand."""
    print("Current hand:")
    for i, piece in enumerate(hand):
        print(f"Piece {i}:")
        print_piece(piece)

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
        print(" ".join('#' if cell == 1 else '.' for cell in row))
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

    for i in range(piece_h):          # i = row in piece shape
        for j in range(piece_w):      # j = col in piece shape
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
                board[br][bc] = value   # default is 1 (filled)

def create_empty_board():
    """Return a 10x10 board filled with 0s (empty cells)."""
    return [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def print_board(board):
    """Print the board in a simple text form."""
    for row in board:
        # '.' for empty, '#' for filled (later we'll use 1 instead of 0)
        print(" ".join('.' if cell == 0 else '#' for cell in row))
    print()

if __name__ == "__main__":
    main()
