"""
MAP.PY - the navigation map: two targets with distinct values, random walls validated by BFS, and the move() action.
"""

from maspy import Any, Environment, Percept, action
from maspy.learning import listed
from collections import deque
import random
from random import randint

from .targets import TargetTracker


# generate_map_with_walls - random walls, retried until every free cell is reachable from a target (BFS). Returns: (walls, available).
def generate_map_with_walls(width, height, targets, wall_prob=0.1, max_attempts=2000):
    def neighbors(x, y):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny

    # Retry until the BFS reaches every free cell.
    for attempt in range(max_attempts):
        # Walls; targets are never walls.
        walls = {(x, y) for x in range(width) for y in range(height)
                 if random.random() < wall_prob and (x, y) not in targets}

        # Flood fill from the first target.
        queue = deque([next(iter(sorted(targets)))])
        reachable = set(queue)
        while queue:
            cx, cy = queue.popleft()
            for nx, ny in neighbors(cx, cy):
                if (nx, ny) not in walls and (nx, ny) not in reachable:
                    reachable.add((nx, ny))
                    queue.append((nx, ny))

        total_open = width * height - len(walls)
        attempts_used = attempt + 1

        # Accept only fully connected maps.
        if len(reachable) == total_open:
            available = sorted(reachable)
            # Only logs retried maps.
            if attempts_used > 1:
                print(f"  map accepted after {attempts_used} attempt(s) "
                      f"({len(walls)} walls)")
            return walls, available

    raise RuntimeError("Failed to generate a valid map.")


# Map - the game board; data lives in the percept bank.
class Map(TargetTracker, Environment):
    def __init__(self, map_size=(10, 10), walls_prob=0.1):
        super().__init__()
        self.map_size = map_size

        # Two targets placed at distinct positions.
        targets = {(randint(0, self.map_size[0] - 1),
                    randint(0, self.map_size[1] - 1))}
        while len(targets) < 2:
            targets.add((randint(0, self.map_size[0] - 1),
                         randint(0, self.map_size[1] - 1)))

        walls, available = generate_map_with_walls(
            self.map_size[0], self.map_size[1], targets, walls_prob, 2000)

        # Set distinct values for each target: Primary target (100 pts), Secondary target (40 pts).
        t_list = sorted(list(targets))
        self.target_values = {
            t_list[0]: 100,
            t_list[1]: 40
        }

        self.print(f"Targets created: {t_list[0]} (100 pts) and {t_list[1]} (40 pts)")

        # Percept bank: stores coordinates and point value for each target.
        for pos, val in self.target_values.items():
            self.create(Percept("target", (pos[0], pos[1], val)))

        for wall in walls:
            self.create(Percept("wall", wall))
        self.create(Percept("position", available, listed))

        self.targets_left = Percept("targets_left", len(targets), "public")
        self.create(self.targets_left)

        self.possible_starts = "off-policy"
        self.moves = {
            "up": (0, -1), "down": (0, 1),
            "right": (1, 0), "left": (-1, 0),
        }

    # move_transition() - rewards: -1 step, +value for target, -10 wall/edge.
    def move_transition(self, position, direction):
        reward = -1
        terminated = False

        new_position = self.moviment(position, direction)
        if new_position in self._target_positions():
            # Reward is proportional to the target's value (+100 or +40).
            val = self.target_values.get(new_position, 10)
            reward = val
            terminated = True
        elif self.has(Percept("wall", new_position)) or position == new_position:
            reward = -10
        return new_position, reward, terminated

    # move() - the @action called by agents.
    @action(listed, ["up", "down", "left", "right"], move_transition)
    def move(self, agt, direction):
        position = self.get(Percept("agt_position", (Any, Any), agt), ck_group=True)
        assert isinstance(position, Percept)

        wall_flag = False
        pos = position.values
        if direction == "stay":
            new_pos = pos
        else:
            new_pos = self.moviment(pos, direction)
            if self.has(Percept("wall", new_pos)):
                wall_flag = True
                new_pos = pos
            else:
                position.change(values=new_pos)

        n_pos = self.get(Percept("agt_position", (Any, Any), agt), ck_group=True).values

        if n_pos in self._remaining_target_positions():
            val = self.target_values.get(n_pos, 0)
            self.print(f"{agt} in {pos} moved {direction} and captured the TARGET at {n_pos} (+{val} pts)!")
            self.create(Percept("arrived_target", (n_pos[0], n_pos[1], val), agt))
            self._capture(n_pos, val, agt)
        elif n_pos in self._captured_target_positions():
            self.print(f"{agt} moved to {n_pos}, but the target was already captured!")
        elif wall_flag:
            self.print(f"{agt} in {pos} tried to move {direction} but bumped into a wall")
        else:
            self.print(f"{agt} in {pos} moved {direction} to {n_pos}")

    # on_connect() - automatically assigns a random free cell far from both targets.
    def on_connect(self, agt):
        targets = self._target_positions()  # Returns list of (x, y) tuples.
        attempts = 0
        while True:
            attempts += 1
            start_pos = (randint(0, self.map_size[0] - 1), randint(0, self.map_size[1] - 1))
            
            # Skip cells that contain walls.
            if self.has(Percept("wall", start_pos)):
                continue
                
            # Manhattan distance to targets.
            d = min(abs(start_pos[0] - t[0]) + abs(start_pos[1] - t[1]) for t in targets)
            if d > self.map_size[0] / 2 or attempts > 2000:
                break

        # Create the agt_position percept scoped to the connecting agent's group.
        self.create(Percept("agt_position", start_pos, agt))

    # moviment() - computes coordinate updates within grid bounds.
    def moviment(self, position, direction):
        dx, dy = self.moves[direction]
        new_x = max(0, min(position[0] + dx, self.map_size[0] - 1))
        new_y = max(0, min(position[1] + dy, self.map_size[1] - 1))
        return new_x, new_y
