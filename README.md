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

## Clean

```bash
make clean
```

Removes the `.venv` virtual environment.
