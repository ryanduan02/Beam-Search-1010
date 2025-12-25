# Beam-Search-1010

Beam search 1010! game implementation.

This repo contains:
- deterministic game engine in `beam1010/` (state, rules, move generation)
- beam-search planner in `beam1010/beam_search.py`
- An offline simulator in `simulate_beam.py` that repeatedly:
	1) draws a 3-piece hand
	2) runs beam search to plan the best sequence for that hand
	3) applies the planned moves and records rich telemetry to JSON

The simulator json output is meant for inspecting / tuning heuristic weights.

## Requirements

- Python 3.10+ (no third-party dependencies)

## Quick start

Run a single simulated game (beam search runs every hand):

```bash
python3 simulate_beam.py --games 1 --seed 0 --beam-width 10 --out runs/one.jsonl
```

If you want a multi-line, human-readable file, write JSON instead of JSONL:

```bash
python3 simulate_beam.py --games 1 --seed 0 --beam-width 10 --format json --out runs/one.json
```

Limit the run to a small number of placements (useful for debugging):

```bash
python3 simulate_beam.py --games 1 --seed 0 --beam-width 10 --max-moves 10 --format json --out runs/ten_moves.json
```

## What “running beam search” means here

Beam search is executed inside `simulate_beam.py` once per hand:

- It calls `beam1010.beam_search.beam_search_best_sequence(state, beam_width=..., depth=len(hand))`.
- “Option A” behavior: the search depth is limited to the current hand only (no lookahead into future random hands).

## Output format

### JSONL (default)

Default output is JSON Lines: **one JSON object per game per line** (compact / one line).
This is great for large runs and streaming.

### JSON (pretty)

With `--format json`, the simulator writes a single JSON array of game results (multi-line, indented).

### Game result schema (high level)

Each game result includes:
- `final_score`, `moves`, `segments` (one segment per hand)

Each segment includes:
- `hand`: piece names dealt for that hand
- `planned_moves`: the planned sequence for the hand
- `moves`: the executed moves with scoring + heuristic values

Each move object contains both the **hand index** and the **piece itself**:

```json
{
	"piece_index": 0,
	"piece_name": "plus",
	"piece": {"name": "plus", "shape": [[0,1,0],[1,1,1],[0,1,0]]},
	"row": 3,
	"col": 5
}
```

## Print a simple per-move log (move + score)

If you want a quick “turn-by-turn” log from a pretty JSON run:

```bash
python3 - <<'PY'
import json

game = json.load(open('runs/one.json','r',encoding='utf-8'))[0]
turn = 0
for seg in game['segments']:
		for m in seg['moves']:
				turn += 1
				mv = m['move']
				print(f"{turn:04d} {mv['piece_name']} @ ({mv['row']},{mv['col']}) score={m['score_after']}")
PY
```

## Tune heuristic weights

You can override heuristic weights from the CLI:

```bash
python3 simulate_beam.py --games 10 --seed 0 --beam-width 25 \
	--mobility 0.2 --near-full-lines 1.5 --roughness -0.1 \
	--format json --out runs/tuned.json
```

The heuristic function is in `beam1010/heuristics.py`.

## Run the interactive console game

There is also a simple console version (manual play):

```bash
python3 game.py
```

## Tests

Run all tests:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## Repo layout

- `beam1010/` — engine + beam search
	- `state.py` — immutable `GameState`
	- `rules.py` — placement, line clears, scoring, `simulate_move`
	- `moves.py` — legal move enumeration
	- `heuristics.py` — evaluation function + weights
	- `beam_search.py` — beam search implementation
- `simulate_beam.py` — offline simulator + JSON/JSONL output
- `game.py` — interactive console game + piece catalog used by the simulator

