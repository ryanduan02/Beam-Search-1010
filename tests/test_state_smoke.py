import unittest

from beam1010.pieces import Piece
from beam1010.moves import legal_moves
from beam1010.rules import apply_move, can_place, simulate_move
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

        original_board = state.board
        original_hand_names = [p.name for p in state.hand]

        self.assertTrue(can_place(state.board, state.hand[1], 0, 0))

        simulated_state, delta, cleared_cells, rows_cleared, cols_cleared = (
            simulate_move(state, hand_index=1, row=0, col=0)
        )
        self.assertEqual((cleared_cells, rows_cleared, cols_cleared), (0, 0, 0))
        self.assertEqual(delta, 2)
        self.assertEqual(simulated_state.score, 2)
        self.assertEqual([p.name for p in simulated_state.hand], ["single"])

        new_state, cleared_cells, rows_cleared, cols_cleared = apply_move(
            state, hand_index=1, row=0, col=0
        )

        self.assertEqual((cleared_cells, rows_cleared, cols_cleared), (0, 0, 0))
        self.assertEqual(new_state.score, 2)  # 2 blocks placed, 0 cleared
        self.assertEqual(
            [p.name for p in new_state.hand], ["single"]
        )  # removed used piece

        # Ensure parent state was not mutated.
        self.assertIs(state.board, original_board)
        self.assertEqual([p.name for p in state.hand], original_hand_names)

    def test_legal_moves_enumerates_all_positions(self) -> None:
        state = GameState(
            board=empty_board(10),
            score=0,
            hand=(
                Piece(name="single", shape=((1,),)),
                Piece(name="line2_h", shape=((1, 1),)),
            ),
        )

        moves = list(legal_moves(state))

        # On an empty 10x10:
        # - single: 10*10 = 100 placements
        # - horizontal length-2: 10*9 = 90 placements
        self.assertEqual(len(moves), 190)

        # Every enumerated move must be legal.
        for move in moves:
            piece = state.hand[move.piece_index]
            self.assertTrue(can_place(state.board, piece, move.row, move.col))


if __name__ == "__main__":
    unittest.main()
