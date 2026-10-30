# maspy-navigation-2D

Navigation 2D implementation using [MASPY](https://github.com/laca-is/MASPY), based on the official [`2D-Navigation-Learn` example](https://github.com/laca-is/MASPY/tree/main/examples/2D-Navigation-Learn).

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.12+

## Setup

```bash
make setup
```

Creates `.venv` and installs the dependencies.

## Run

```bash
make run
```

The setup menu configures map size, wall percentage, number of agents and training episodes. `make help` lists all commands.

## How it works

### Map generation

1. The target cell is placed at random.
2. Each cell becomes a wall with probability `walls %`; the target is never a wall.
3. A BFS from the target visits every reachable free cell.
4. A map with an unreachable free cell is discarded and regenerated (up to 2000 attempts).
5. The console logs how many attempts were needed.

### Learning

Each `Walker` trains Q-learning for the menu's episodes (`0` = no training). When training runs, the learned policy is stored and `make_move` follows it while `Belief("use_learn")` exists.

### Agent behavior

- `make_move`: random direction each cycle, or the learned policy when training ran.
- Notebook: `Path_Graph` (visited cells) and `Wall_Set` (bumped walls).
- Sharing: after each step the agent broadcasts its notebook; the others merge it.
- Finding the target: the first agent to reach it broadcasts the target and stops.
- `best_move`: once the target is known, A* over the notebook, one step per cycle and replanned each step. Unknown cells cost more.

## Dead code

Never called, kept for reference:

- `reconstruct_path` and `reconstruct_path_known` (`Walker_Ag.py`)
- `reset_positions` (`Map_Env.py`)

## Clean

```bash
make clean
```

Removes `.venv`.
