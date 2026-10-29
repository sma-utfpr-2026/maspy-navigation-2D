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

The setup menu configures map size, wall percentage, number of agents and training episodes. The competition needs at least 2 agents. `make help` lists all commands.

## How it works

### Map generation

1. Two distinct targets are placed at random.
2. Each cell becomes a wall with probability `walls %`; targets are never walls.
3. A BFS from a target visits every reachable free cell.
4. A map with an unreachable free cell is discarded and regenerated (up to 2000 attempts).
5. The console logs how many attempts were needed.

### Learning

Each `Walker` trains Q-learning for the menu's episodes (`0` = no training). The reward accepts either target. When training is enabled, the walker's movement follows the learned policy.

### Agent behavior

- `make_move`: when training is enabled, follows the learned policy before the first target capture; otherwise (training disabled or second target capture) explores the nearest unexplored neighbor (random choice among the 3 nearest).
- Notebook: `Path_Graph` (visited cells) and `Wall_Set` (bumped walls discovered), private per agent.
- After a capture, the capturer broadcasts through the default channel. It reads the public `targets_left` percept: `0` means it took the last target, so it broadcasts `game_over`; otherwise it broadcasts `target_lost`.
- Trained agents that receive `target_lost` switch to exploration; every walker that receives `game_over` stops.

### Competition

- Two targets on the map.
- Agents do not cooperate: each keeps a private notebook of explored cells.
- The first agent to reach a target captures it, broadcasts `target_lost` through the channel and stops; the others keep searching.
- The game ends when both targets are captured. The last capturer sees `targets_left == 0`, broadcasts `game_over` and stops; the others stop when they receive it. The sidebar lists the captures and shows `GAME OVER`.

## Dead code

Marked in the source with `# DEAD CODE (never called).`

- `best_move`, `update_graph`, `update_walls` (`Walker_Ag.py`, commented out so MASPY does not register the plans)
- `reconstruct_path`, `reconstruct_path_known` (`Walker_Ag.py`, still defined)
- `reset_positions` (`env/map.py`, still defined)

## Clean

```bash
make clean
```

Removes `.venv`.
