import unittest

from beam1010.pieces import Piece
from beam1010.rules import apply_move, can_place
from beam1010.state import GameState, empty_board


class TestStateSmoke(unittest.TestCase):
    def test_apply_move_updates_score_and_hand(self) -> None:
        state = GameState(
            board=empty_board(10),
            score=0,
            hand=(
                Piece(name="single", shape=((1,),)),
                Piece(name="line2_h", shape=((1, 1),)),
            ),
        )

        self.assertTrue(can_place(state.board, state.hand[1], 0, 0))
        new_state, cleared_cells, rows_cleared, cols_cleared = apply_move(
            state, hand_index=1, row=0, col=0
        )

        self.assertEqual((cleared_cells, rows_cleared, cols_cleared), (0, 0, 0))
        self.assertEqual(new_state.score, 2)  # 2 blocks placed, 0 cleared
        self.assertEqual([p.name for p in new_state.hand], ["single"])  # removed used piece


if __name__ == "__main__":
    unittest.main()
