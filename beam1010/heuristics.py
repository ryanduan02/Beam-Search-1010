from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Iterable

from .moves import legal_moves
from .state import Board, GameState


@dataclass(frozen=True, slots=True)
class HeuristicWeights:
    """Weights for heuristic evaluation.

    Defaults are intentionally conservative and simple:
    - prioritize current score
    - prefer states with more remaining placements (mobility)
    - slightly prefer boards close to clearing lines
    - penalize rough/fragmented boards

    You should expect to tune these.
    """

    mobility: float = 0.10
    near_full_lines: float = 1.00
    roughness: float = -0.05

    # Optional features (off by default).
    fragments: float = 0.0
    enclosed_empties: float = 0.0


DEFAULT_WEIGHTS = HeuristicWeights()


def evaluate(state: GameState, weights: HeuristicWeights = DEFAULT_WEIGHTS) -> float:
    """Evaluate how promising a state is for beam search.

    Higher is better.

    Temporary baseline:
        state.score
        + w_mobility * mobility(state)
        + w_near_full * near_full_lines(board)
        + w_roughness * roughness(board)

    Note: Optional features can be enabled by setting non-zero weights.
    """

    value = float(state.score)
    value += weights.mobility * mobility(state)
    value += weights.near_full_lines * near_full_lines(state.board)
    value += weights.roughness * roughness(state.board)

    if weights.fragments:
        value += weights.fragments * empty_fragments(state.board)
    if weights.enclosed_empties:
        value += weights.enclosed_empties * enclosed_empties(state.board)

    return value


def mobility(state: GameState) -> int:
    """Count of legal placements across the remaining hand."""
    return sum(1 for _ in legal_moves(state))


def near_full_lines(board: Board, *, lo: int = 8, hi: int = 9) -> int:
    """Count rows/cols that are close to full.

    By default counts lines with 8–9 filled cells (on a 10-wide board).
    """

    height = len(board)
    width = len(board[0])

    score = 0

    for r in range(height):
        filled = sum(1 for c in range(width) if board[r][c] != 0)
        if lo <= filled <= hi:
            score += 1

    for c in range(width):
        filled = sum(1 for r in range(height) if board[r][c] != 0)
        if lo <= filled <= hi:
            score += 1

    return score


def roughness(board: Board) -> int:
    """A simple fragmentation/"jaggedness" metric.

    Counts transitions between empty/filled across adjacent cells in rows and cols.
    More transitions usually means more irregular shapes (worse).
    """

    height = len(board)
    width = len(board[0])

    transitions = 0

    for r in range(height):
        for c in range(width - 1):
            a = board[r][c] != 0
            b = board[r][c + 1] != 0
            if a != b:
                transitions += 1

    for c in range(width):
        for r in range(height - 1):
            a = board[r][c] != 0
            b = board[r + 1][c] != 0
            if a != b:
                transitions += 1

    return transitions


def empty_fragments(board: Board) -> int:
    """Number of connected components of empty space (4-neighborhood)."""

    height = len(board)
    width = len(board[0])

    visited = [[False for _ in range(width)] for _ in range(height)]

    def neighbors(r: int, c: int) -> Iterable[tuple[int, int]]:
        if r > 0:
            yield r - 1, c
        if r + 1 < height:
            yield r + 1, c
        if c > 0:
            yield r, c - 1
        if c + 1 < width:
            yield r, c + 1

    fragments = 0
    for r in range(height):
        for c in range(width):
            if visited[r][c]:
                continue
            if board[r][c] != 0:
                visited[r][c] = True
                continue

            fragments += 1
            q: deque[tuple[int, int]] = deque([(r, c)])
            visited[r][c] = True
            while q:
                cr, cc = q.popleft()
                for nr, nc in neighbors(cr, cc):
                    if visited[nr][nc]:
                        continue
                    if board[nr][nc] != 0:
                        visited[nr][nc] = True
                        continue
                    visited[nr][nc] = True
                    q.append((nr, nc))

    return fragments


def enclosed_empties(board: Board) -> int:
    """Count empty cells not connected to the border through empty cells.

    This approximates "holes" / enclosed cavities.
    """

    height = len(board)
    width = len(board[0])

    reachable = [[False for _ in range(width)] for _ in range(height)]

    def push_if_empty(r: int, c: int, q: deque[tuple[int, int]]) -> None:
        if reachable[r][c]:
            return
        if board[r][c] != 0:
            return
        reachable[r][c] = True
        q.append((r, c))

    q: deque[tuple[int, int]] = deque()

    # Seed from border empties.
    for c in range(width):
        push_if_empty(0, c, q)
        push_if_empty(height - 1, c, q)
    for r in range(height):
        push_if_empty(r, 0, q)
        push_if_empty(r, width - 1, q)

    while q:
        r, c = q.popleft()
        if r > 0:
            push_if_empty(r - 1, c, q)
        if r + 1 < height:
            push_if_empty(r + 1, c, q)
        if c > 0:
            push_if_empty(r, c - 1, q)
        if c + 1 < width:
            push_if_empty(r, c + 1, q)

    enclosed = 0
    for r in range(height):
        for c in range(width):
            if board[r][c] == 0 and not reachable[r][c]:
                enclosed += 1

    return enclosed
