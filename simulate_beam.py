"""Offline simulator for tuning beam-search heuristics.

Goal: run the game automatically many times, record (hands, chosen sequences,
per-move deltas, final score) so you can inspect/tune heuristics.

Option A is assumed: each beam search plans only within the current hand.

Examples:
  python3 simulate_beam.py --games 50 --seed 0 --beam-width 25 --out runs.jsonl
  python3 simulate_beam.py --games 10 --seed 123 --beam-width 50 --mobility 0.2 --near-full-lines 1.5 --roughness -0.1

Pretty (multi-line) JSON output:
    python3 simulate_beam.py --games 1 --seed 0 --beam-width 25 --format json --out runs/one.json

Output format: JSON Lines (one JSON object per game).
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from beam1010.beam_search import beam_search_best_sequence
from beam1010.heuristics import HeuristicWeights, evaluate
from beam1010.moves import Move, any_legal_move
from beam1010.rules import simulate_move
from beam1010.state import GameState, empty_board

# Reuse the same piece catalog as the interactive game.
from game import PIECES, PIECES_IN_HAND


def _draw_hand(rng: random.Random, n: int) -> list[dict]:
    return [rng.choice(PIECES) for _ in range(n)]


def run_game(
    *,
    seed: int,
    beam_width: int,
    weights: HeuristicWeights,
    max_moves: Optional[int] = None,
) -> Dict[str, Any]:
    rng = random.Random(seed)

    state = GameState(board=empty_board(10), score=0, hand=())

    segments: List[Dict[str, Any]] = []
    move_count = 0

    while True:
        if max_moves is not None and move_count >= max_moves:
            break

        if state.is_hand_empty:
            hand = _draw_hand(rng, PIECES_IN_HAND)
            state = GameState.from_game_py(
                board=[list(r) for r in state.board], score=state.score, hand=hand
            )

        if not any_legal_move(state):
            break

        planned = beam_search_best_sequence(
            state,
            beam_width=beam_width,
            depth=len(state.hand),
            weights=weights,
        )
        if not planned:
            break

        segment: Dict[str, Any] = {
            "hand": [p.name for p in state.hand],
            "planned_moves": [],
            "moves": [],
            "start_score": state.score,
        }

        # Execute the planned sequence for this hand.
        for mv in planned:
            before_eval = evaluate(state, weights)
            next_state, delta, cleared_cells, rows_cleared, cols_cleared = (
                simulate_move(state, hand_index=mv.piece_index, row=mv.row, col=mv.col)
            )
            after_eval = evaluate(next_state, weights)

            segment["planned_moves"].append(_move_to_dict(state, mv))
            segment["moves"].append(
                {
                    "move": _move_to_dict(state, mv),
                    "delta": delta,
                    "cleared_cells": cleared_cells,
                    "rows_cleared": rows_cleared,
                    "cols_cleared": cols_cleared,
                    "score_after": next_state.score,
                    "eval_before": before_eval,
                    "eval_after": after_eval,
                }
            )

            state = next_state
            move_count += 1
            if max_moves is not None and move_count >= max_moves:
                break

        segment["end_score"] = state.score
        segments.append(segment)

        if max_moves is not None and move_count >= max_moves:
            break

    return {
        "seed": seed,
        "beam_width": beam_width,
        "weights": asdict(weights),
        "final_score": state.score,
        "moves": move_count,
        "segments": segments,
    }


def extract_executed_moves(game_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a flat list of executed move dicts for a single game.

    Each entry matches the move dict stored at:
        game_result['segments'][i]['moves'][j]['move']
    """

    out: List[Dict[str, Any]] = []
    for segment in game_result.get("segments", []):
        for move_info in segment.get("moves", []):
            mv = move_info.get("move")
            score_after = move_info.get("score_after")
            if isinstance(mv, dict):
                # Keep the sidecar compact: omit full piece shapes.
                entry = {
                    "piece_index": mv.get("piece_index"),
                    "piece_name": mv.get("piece_name"),
                    "row": mv.get("row"),
                    "col": mv.get("col"),
                }
                if score_after is not None:
                    entry["score_after"] = int(score_after)
                out.append(entry)
    return out


def _move_to_dict(state: GameState, m: Move) -> Dict[str, Any]:
    piece_dict: Optional[dict] = None
    piece_name: Optional[str] = None
    if 0 <= m.piece_index < len(state.hand):
        piece = state.hand[m.piece_index]
        piece_dict = piece.to_dict()
        piece_name = piece.name

    return {
        "piece_index": m.piece_index,
        "piece_name": piece_name,
        "piece": piece_dict,
        "row": m.row,
        "col": m.col,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=10)
    p.add_argument(
        "--seed", type=int, default=0, help="Base seed; each game uses seed+idx"
    )
    p.add_argument("--beam-width", type=int, default=25)
    p.add_argument("--max-moves", type=int, default=None)
    p.add_argument(
        "--out",
        type=str,
        default=None,
        help="Write output to this file (default: stdout)",
    )
    p.add_argument(
        "--format",
        choices=("jsonl", "json"),
        default="jsonl",
        help="Output format: jsonl (default) writes one compact JSON object per line; json writes a single pretty-printed JSON array.",
    )
    p.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indent level for --format json (ignored for jsonl).",
    )

    p.add_argument(
        "--moves-out",
        type=str,
        default=None,
        help=(
            "Optional sidecar output path for moves-only JSON. "
            "If omitted, no moves-only sidecar file is written."
        ),
    )

    p.add_argument(
        "--write-moves-sidecar",
        action="store_true",
        help=(
            "Write a moves-only sidecar next to --out (defaults to '<out_basename>.moves.json'). "
            "Ignored if --out is not provided."
        ),
    )

    # Simple weight overrides.
    p.add_argument("--mobility", type=float, default=None)
    p.add_argument("--near-full-lines", type=float, default=None)
    p.add_argument("--roughness", type=float, default=None)
    p.add_argument("--fragments", type=float, default=None)
    p.add_argument("--enclosed-empties", type=float, default=None)

    args = p.parse_args()

    weights = HeuristicWeights()
    weights = HeuristicWeights(
        mobility=weights.mobility if args.mobility is None else args.mobility,
        near_full_lines=(
            weights.near_full_lines
            if args.near_full_lines is None
            else args.near_full_lines
        ),
        roughness=weights.roughness if args.roughness is None else args.roughness,
        fragments=weights.fragments if args.fragments is None else args.fragments,
        enclosed_empties=(
            weights.enclosed_empties
            if args.enclosed_empties is None
            else args.enclosed_empties
        ),
    )

    out_f = open(args.out, "w", encoding="utf-8") if args.out else None

    moves_out_path: Optional[str] = None
    if args.moves_out is not None:
        moves_out_path = args.moves_out
    elif args.write_moves_sidecar and args.out:
        # Derive a stable sidecar name next to the main output.
        base = args.out
        if base.endswith(".jsonl"):
            base = base[: -len(".jsonl")]
        elif base.endswith(".json"):
            base = base[: -len(".json")]
        moves_out_path = base + ".moves.json"

    moves_out_f = (
        open(moves_out_path, "w", encoding="utf-8") if moves_out_path else None
    )
    try:
        results: List[Dict[str, Any]] = []
        for i in range(args.games):
            run_seed = args.seed + i
            results.append(
                run_game(
                    seed=run_seed,
                    beam_width=args.beam_width,
                    weights=weights,
                    max_moves=args.max_moves,
                )
            )

        if moves_out_f:
            # For 1 game, write a flat list of moves.
            # For N games, write a list of {seed, moves} objects.
            if len(results) == 1:
                payload = json.dumps(
                    extract_executed_moves(results[0]), indent=args.indent
                )
            else:
                payload = json.dumps(
                    [
                        {"seed": r.get("seed"), "moves": extract_executed_moves(r)}
                        for r in results
                    ],
                    indent=args.indent,
                )
            moves_out_f.write(payload + "\n")

        if args.format == "jsonl":
            for result in results:
                line = json.dumps(result)
                if out_f:
                    out_f.write(line + "\n")
                else:
                    print(line)
        else:
            payload = json.dumps(results, indent=args.indent)
            if out_f:
                out_f.write(payload + "\n")
            else:
                print(payload)
    finally:
        if out_f:
            out_f.close()
        if moves_out_f:
            moves_out_f.close()


if __name__ == "__main__":
    main()
