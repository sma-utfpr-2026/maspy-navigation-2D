# maspy-navigation-2D

Navigation 2D implementation using [MASPY](https://github.com/laca-is/MASPY).

This project is based on a copy of the official [`2D-Navigation-Learn` example](https://github.com/laca-is/MASPY/tree/main/examples/2D-Navigation-Learn) from the [laca-is/MASPY](https://github.com/laca-is/MASPY) repository.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (used to create the virtual environment and install dependencies)
- Python 3.12+

## Setup

```bash
make setup
```

This creates the `.venv` virtual environment and installs the project dependencies.

## Run

```bash
make run
```

The simulation opens a setup menu where you can configure the map width and height, wall percentage, number of agents, and training episodes. Click **Start Simulation** to launch the visualization.

`make help` lists all available commands.

## How it works

### Map generation at start

When you click **Start Simulation**, the menu settings build the `Map`:

1. The target cell is placed at random.
2. Each cell becomes a wall with probability `walls %`. The target is never a wall.
3. A BFS flood fill starts at the target and visits every reachable free cell.
4. If any free cell was not reached, the map has an unreachable pocket that would trap an agent. The map is discarded and a new one is generated.
5. The loop repeats up to 2000 attempts. If none is valid, the program stops with an error.

The console reports how many attempts were needed when a map was discarded.

### Learning mode

Each `Walker` builds an `EnvModel` and runs Q-learning for the number of episodes chosen in the menu, during its constructor. The menu treats `0` episodes as "no training": those agents just wander randomly. When the training runs, the learned policy is stored and `make_move` reads it while `Belief("use_learn")` exists - the belief is added by the constructor when the training finishes (see the `chore/equalize-class-presentation-from-author` branch).

### Agent behavior

- **Wandering (`make_move`)**: each agent picks a random direction every cycle. It has no memory of where it has already been, so it can revisit the same cells many times.
- **Notebook**: each agent records the cells it walks to in `Path_Graph` and the walls it finds by bumping into them in `Wall_Set`.
- **Sharing**: after each step the agent broadcasts its notebook. Other agents merge the cells and walls they receive. This shares discoveries, but it does not tell agents which routes were already walked.
- **Finding the target**: the first agent to reach the target broadcasts it and stops.
- **Planning (`best_move`)**: once an agent knows the target, it stops wandering. It uses A\* over its notebook to find a path, takes one step, and recalculates the path on every step. Unknown cells cost more than known ones, so the agent prefers known routes but can still explore.

## Known bugs

These bugs were found and documented here first. They were fixed in the `fix/known-bugs` branch, already integrated in the stable version (`stabilize-project`):

- ~~`draw_ascii_map`: the drawn frame only covers cells the agent walked, so the target and walls outside that area are not drawn. Passing `walls=None` also crashes.~~ Fixed: the frame now covers every known cell and `walls=None` is handled.
- ~~`update_walls`: reads `sent_graph[0]`, which is always the sender's first wall. Only that wall is transferred from each sender.~~ Fixed: it reads `sent_graph[-1]`, the wall the sender just added.
- ~~Menu: accepts `0` agents, which opens an empty simulation.~~ Fixed: the menu requires at least 1 agent.

## Dead code

These parts are kept for reference and are never called:

- `reconstruct_path` and `reconstruct_path_known` (`Walker_Ag.py`)
- `reset_positions` (`Map_Env.py`)

(The `use_learn` branch of `make_move` used to be listed here too; it is
active since the learning-mode integration on `stabilize-project`.)

## Clean

```bash
make clean
```

Removes the `.venv` virtual environment.
