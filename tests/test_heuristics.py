import unittest

from beam1010.heuristics import mobility, near_full_lines, roughness
from beam1010.pieces import Piece
from beam1010.state import GameState, empty_board


class TestHeuristics(unittest.TestCase):
    def test_mobility_empty_board(self) -> None:
        state = GameState(
            board=empty_board(10),
            score=0,
            hand=(
                Piece(name="single", shape=((1,),)),
                Piece(name="line2_h", shape=((1, 1),)),
            ),
        )
        # single: 100, line2_h: 90
        self.assertEqual(mobility(state), 190)

    def test_near_full_lines_counts_9_filled(self) -> None:
        board = [list(r) for r in empty_board(10)]
        # Make first row have 9 filled cells.
        for c in range(9):
            board[0][c] = 1
        state = GameState.from_game_py(board=board, score=0, hand=[])
        self.assertEqual(near_full_lines(state.board), 1)

    def test_roughness_empty_board_is_zero(self) -> None:
        self.assertEqual(roughness(empty_board(10)), 0)


if __name__ == "__main__":
    unittest.main()
