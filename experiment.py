"""Run many independent beam-search simulations and write one file per seed.

This is a lightweight wrapper around `simulate_beam.run_game`.

Example:
  python3 experiment.py --games 3 --seed 0 --beam-width 10 --out-dir runs/exp --sidecar true

Outputs:
  runs/exp/Seed00000.json
  runs/exp/Seed00000.moves.json   (if --sidecar true)
  runs/exp/Seed00001.json
  ...

Notes:
- Each output JSON is a single game result object (not a JSON array).
- The sidecar is a moves-only JSON array (same schema as simulate_beam for 1 game).
"""

from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path
from typing import Optional

from simulate_beam import extract_executed_moves, run_game
from beam1010.heuristics import HeuristicWeights


def _str2bool(v: str) -> bool:
    s = v.strip().lower()
    if s in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("Expected a boolean (true/false)")


def _seed_filename(seed: int) -> str:
    return f"Seed{seed:05d}.json"


def _moves_filename(seed: int) -> str:
    return f"Seed{seed:05d}.moves.json"


def main() -> None:
    p = argparse.ArgumentParser(
        description="Run experiments: one JSON output per seed."
    )
    p.add_argument("--games", type=int, default=10, help="Number of games to run.")
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Base seed; game i uses seed+i. If omitted, each game uses a random seed."
        ),
    )
    p.add_argument("--beam-width", type=int, default=25)
    p.add_argument("--max-moves", type=int, default=None)
    p.add_argument(
        "--out-dir",
        type=str,
        default="runs/experiment",
        help="Directory to write SeedXXXXX.json outputs.",
    )
    p.add_argument(
        "--sidecar",
        type=_str2bool,
        default=False,
        help="Write SeedXXXXX.moves.json per game (true/false).",
    )
    p.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indent level for written JSON files.",
    )

    # Optional weight overrides (same names as simulate_beam.py).
    p.add_argument("--mobility", type=float, default=None)
    p.add_argument("--near-full-lines", type=float, default=None)
    p.add_argument("--roughness", type=float, default=None)
    p.add_argument("--fragments", type=float, default=None)
    p.add_argument("--enclosed-empties", type=float, default=None)

    args = p.parse_args()

    if args.games <= 0:
        raise SystemExit("--games must be > 0")
    if args.beam_width <= 0:
        raise SystemExit("--beam-width must be > 0")

    base_seed: Optional[int]
    if args.seed is None:
        base_seed = None
    else:
        base_seed = int(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    defaults = HeuristicWeights()
    weights = HeuristicWeights(
        mobility=defaults.mobility if args.mobility is None else args.mobility,
        near_full_lines=(
            defaults.near_full_lines
            if args.near_full_lines is None
            else args.near_full_lines
        ),
        roughness=defaults.roughness if args.roughness is None else args.roughness,
        fragments=defaults.fragments if args.fragments is None else args.fragments,
        enclosed_empties=(
            defaults.enclosed_empties
            if args.enclosed_empties is None
            else args.enclosed_empties
        ),
    )

    used_seeds: set[int] = set()

    for i in range(args.games):
        if base_seed is None:
            # Random seed per game. Keep them unique within a batch so filenames
            # don't collide.
            seed = secrets.randbelow(1_000_000_000)
            while seed in used_seeds:
                seed = secrets.randbelow(1_000_000_000)
        else:
            seed = base_seed + i

        used_seeds.add(seed)

        result = run_game(
            seed=seed,
            beam_width=int(args.beam_width),
            weights=weights,
            max_moves=args.max_moves,
        )

        out_path = out_dir / _seed_filename(seed)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=args.indent)
            f.write("\n")

        if args.sidecar:
            moves = extract_executed_moves(result)
            moves_path = out_dir / _moves_filename(seed)
            with open(moves_path, "w", encoding="utf-8") as f:
                json.dump(moves, f, indent=args.indent)
                f.write("\n")

        final_score: Optional[int] = result.get("final_score")  # type: ignore[assignment]
        print(f"seed={seed} score={final_score} -> {out_path}")


if __name__ == "__main__":
    main()
