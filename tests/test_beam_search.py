import unittest

from beam1010.beam_search import beam_search_best_sequence, select_best_move
from beam1010.moves import legal_moves
from beam1010.pieces import Piece
from beam1010.rules import can_place
from beam1010.state import GameState, empty_board


class TestBeamSearch(unittest.TestCase):
    def test_select_best_move_is_legal_on_empty_board(self) -> None:
        state = GameState(
            board=empty_board(10),
            score=0,
            hand=(
                Piece(name="single", shape=((1,),)),
                Piece(name="line2_h", shape=((1, 1),)),
                Piece(name="line2_v", shape=((1,), (1,))),
            ),
        )

        move = select_best_move(state, beam_width=10)
        self.assertIsNotNone(move)
        assert move is not None
        piece = state.hand[move.piece_index]
        self.assertTrue(can_place(state.board, piece, move.row, move.col))

    def test_returns_empty_sequence_when_no_moves(self) -> None:
        # Board completely filled -> no move possible.
        filled = tuple(tuple(1 for _ in range(10)) for _ in range(10))
        state = GameState(
            board=filled,
            score=0,
            hand=(Piece(name="single", shape=((1,),)),),
        )

        self.assertEqual(list(legal_moves(state)), [])
        self.assertIsNone(select_best_move(state, beam_width=5))
        self.assertEqual(beam_search_best_sequence(state, beam_width=5), [])


if __name__ == "__main__":
    unittest.main()
