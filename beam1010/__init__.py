"""Core types for 1010 + beam search.

This package intentionally keeps state deterministic (Option A): a search state only
covers the current hand (0–3 pieces). When the hand is empty, the caller can draw a
new random hand and run search again.
"""

from .pieces import Piece
from .state import GameState
from .moves import Move, legal_moves
from .heuristics import DEFAULT_WEIGHTS, HeuristicWeights, evaluate
from .beam_search import BeamSearchParams, beam_search_best_sequence, select_best_move

__all__ = [
    "GameState",
    "Piece",
    "Move",
    "legal_moves",
    "HeuristicWeights",
    "DEFAULT_WEIGHTS",
    "evaluate",
    "BeamSearchParams",
    "beam_search_best_sequence",
    "select_best_move",
]
