from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from .heuristics import DEFAULT_WEIGHTS, HeuristicWeights, evaluate
from .moves import Move, legal_moves
from .rules import simulate_move
from .state import GameState


@dataclass(frozen=True, slots=True)
class BeamSearchParams:
    """Beam search parameters.

    For Option A (current hand only), the natural maximum depth is len(hand).
    """

    beam_width: int = 25
    depth: Optional[int] = None
    weights: HeuristicWeights = DEFAULT_WEIGHTS


@dataclass(frozen=True, slots=True)
class _Node:
    state: GameState
    parent: int
    move: Optional[Move]
    value: float


def beam_search_best_sequence(
    initial: GameState,
    *,
    beam_width: int = 25,
    depth: Optional[int] = None,
    weights: HeuristicWeights = DEFAULT_WEIGHTS,
) -> list[Move]:
    """Run beam search and return the best move sequence found.

    Option A behavior: search is limited to the current hand only.

    Returns an empty list if no legal moves exist.
    """

    if beam_width <= 0:
        raise ValueError("beam_width must be >= 1")

    max_depth = len(initial.hand) if depth is None else int(depth)
    if max_depth < 0:
        raise ValueError("depth must be >= 0")

    nodes: list[_Node] = [
        _Node(state=initial, parent=-1, move=None, value=evaluate(initial, weights))
    ]
    beam: list[int] = [0]

    for _d in range(max_depth):
        candidates: list[int] = []

        for node_index in beam:
            state = nodes[node_index].state
            for move in legal_moves(state):
                child_state, _delta, _cleared, _rows, _cols = simulate_move(
                    state, hand_index=move.piece_index, row=move.row, col=move.col
                )
                v = evaluate(child_state, weights)
                nodes.append(
                    _Node(state=child_state, parent=node_index, move=move, value=v)
                )
                candidates.append(len(nodes) - 1)

        if not candidates:
            break

        # Sort best-first; add deterministic tie-breakers to stabilize search.
        candidates.sort(
            key=lambda i: (
                nodes[i].value,
                nodes[i].state.score,
                -len(nodes[i].state.hand),
            ),
            reverse=True,
        )
        beam = candidates[:beam_width]

    # Choose the best leaf in the final beam.
    best = max(beam, key=lambda i: (nodes[i].value, nodes[i].state.score))
    return _reconstruct_moves(nodes, best)


def select_best_move(
    initial: GameState,
    *,
    beam_width: int = 25,
    depth: Optional[int] = None,
    weights: HeuristicWeights = DEFAULT_WEIGHTS,
) -> Optional[Move]:
    """Convenience: run beam search and return only the first move."""

    seq = beam_search_best_sequence(
        initial, beam_width=beam_width, depth=depth, weights=weights
    )
    return seq[0] if seq else None


def _reconstruct_moves(nodes: Sequence[_Node], leaf_index: int) -> list[Move]:
    moves: list[Move] = []
    i = leaf_index
    while i != -1:
        node = nodes[i]
        if node.move is not None:
            moves.append(node.move)
        i = node.parent
    moves.reverse()
    return moves
