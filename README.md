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

The training episode ends on the first capture, so the learned policy covers goal-directed navigation to a target. The remaining target is found by exploration.

### Agent behavior

- `make_move`: when training is enabled, follows the learned policy until it captures a target; otherwise (training disabled) explores the nearest unexplored neighbor (random choice among the 3 nearest). Trained walkers that receive `target_lost` also switch to exploration.
- Notebook: `Path_Graph` (visited cells) and `Wall_Set` (bumped walls discovered), private per agent.
- After a capture, the capturer broadcasts through the default channel. It reads the public `targets_left` percept: `0` means it took the last target, so it broadcasts `game_over`; otherwise it broadcasts `target_lost`.
- Trained agents that receive `target_lost` switch to exploration; every walker that receives `game_over` stops.

### Percepts, beliefs and messages

MASPY separates what the environment exposes (`Percept`) from what each agent stores (`Belief`). The environment is the source of truth; each agent keeps a revised copy of only what its deliberative process needs, expressed in its own belief vocabulary. Visibility is controlled by the percept group and by `Walker.filter_perceptions(...)`, which here focuses on `[agent_name, "public"]`.

#### Environment percepts (`Map`)

| Percept | Values | Group | Seen by | Created / updated | Purpose |
|---|---|---|---|---|---|
| `target` | target cell | `none` | nobody | init | target cells; reward and termination |
| `wall` | wall cell | `none` | nobody | init | obstacles; agents discover them by bumping |
| `position` | list of free cells | `listed` | nobody | init | state space used by Q-learning |
| `captured_target` | `(cell, agent)` | `none` | nobody | on capture | authoritative capture history; rules and sidebar |
| `targets_left` | remaining count | `public` | all agents | init and each capture | public game state; detects game over |
| `agt_position` | agent cell | agent name | owner only | connect and each move | observable position for plans |
| `arrived_target` | target cell | agent name | capturer only | on capture | event that triggers capture handling |

Among these, only `targets_left`, `agt_position` and `arrived_target` reach an agent's beliefs. `target`, `wall`, `position` and `captured_target` are environment bookkeeping used by the rules and the pygame sidebar; agents do not perceive them.

#### Agent beliefs (`Walker`)

| Belief | Origin | Scope | Purpose |
|---|---|---|---|
| `agt_position` | `Map` perception | private | current cell; triggers `make_move` |
| `targets_left` | `Map` perception (`public`) | private | decide `game_over` vs `target_lost` |
| `arrived_target` | `Map` perception (capturer only) | private | handle a capture |
| `Path_Graph` | own exploration | private | visited cells / discovered graph |
| `Wall_Set` | own bumps | private | discovered walls |
| `mode` | `own configuration` or `target_lost` (trigger) | `private` | Indicates the current walker state:<br>• **`"use_learn"`** – the walker follows the trained policy.<br>• **`"explore"`** – the walker performs pure exploration (or switches to exploration after a `target_lost` event). |
| `target_lost` | channel message | private | switch trained walkers to exploration |
| `game_over` | channel message | private | stop the walker |

#### Messages (default channel)

| Message | From → To | Payload | Effect |
|---|---|---|---|
| `target_lost` | capturer → other walkers (broadcast) | captured cell | capturer stops after sending; trained walkers switch to exploration |
| `game_over` | last capturer → all walkers (broadcast) | `"over"` | every walker stops |

### Competition

- Two targets on the map.
- Agents do not cooperate: each keeps a private notebook of explored cells.
- The first agent to reach a target captures it, broadcasts `target_lost` through the channel and stops; the others keep searching.
- The game ends when both targets are captured. The last capturer sees `targets_left == 0`, broadcasts `game_over` and stops; the others stop when they receive it. The sidebar lists the captures and shows `GAME OVER`.

## Clean

```bash
make clean
```

Removes `.venv`.
