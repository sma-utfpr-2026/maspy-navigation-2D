"""
MAP_ENV.PY - the Navigation Map (the world of the simulation)

A grid of cells: random walls validated by BFS; target, walls and
free cells stored in the MASPY percept bank; agents moved by the
@action move().
"""

from maspy import *
from maspy.learning import *
from collections import deque

import random
from random import randint


# ============================================================
# generate_map_with_walls - draws the walls by the coin flip,
# then throws the map away until every free cell is reachable
# from the target (BFS flood fill).
# Returns: (walls, available) -> the walls set + free cells list.
# ============================================================
def generate_map_with_walls(width, height, target, wall_prob=0.1, max_attempts=2000):
    # the four neighbors of a cell, as (dx, dy) offsets.
    # `yield` makes this a generator: it hands out one neighbor at a time
    def neighbors(x, y):
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny

    # the retry loop: a map is generated and checked; if it is bad,
    # it is thrown away and another one is generated (up to max_attempts)
    for attempt in range(max_attempts):
        # the coin flip: each cell of the grid becomes a wall with
        # probability wall_prob (the target cell can never be a wall)
        # {} builds a SET (no duplicates, no order) instead of a list
        walls = {(x, y) for x in range(width) for y in range(height)
                 if random.random() < wall_prob and (x, y) != target}

        # the flood fill: start at the target and walk to every free cell
        queue = deque([target])
        reachable = {target}
        while queue:
            cx, cy = queue.popleft()
            for nx, ny in neighbors(cx, cy):
                if (nx, ny) not in walls and (nx, ny) not in reachable:
                    reachable.add((nx, ny))
                    queue.append((nx, ny))

        # how many cells are free (not walls)?
        total_open = width * height - len(walls)

        # how many maps were thrown away until this one
        attempts_used = attempt + 1

        # if every free cell was reached, the map is good
        if len(reachable) == total_open:
            available = sorted(reachable)
            # LOG: only speaks when a map was thrown away
            if attempts_used > 1:
                print(f"  map accepted after {attempts_used} attempt(s) "
                      f"({len(walls)} walls)")
            return walls, available

    raise RuntimeError("Failed to generate a valid map.")


# ============================================================
# class Map - the game board. Inherits from Environment,
# so its data lives in the percept bank: .create() stores,
# .get() reads back, .has() asks, .delete() removes.
# ============================================================
class Map(Environment):
    def __init__(self, map_size=(10, 10), walls_prob=0.1):
        # the Environment machinery - registers this Map in the Admin
        super().__init__()

        self.map_size = map_size

        # the random target - randint() includes both ends, so we ask
        # from 0 to map_size-1 (never outside the grid)
        target = (randint(0, self.map_size[0] - 1),
                  randint(0, self.map_size[1] - 1))

        # the walls, using the generator above
        # available = the free positions - now guaranteed connected by
        # the BFS validation inside it
        walls, available = generate_map_with_walls(
            self.map_size[0], self.map_size[1], target, walls_prob, 2000)

        # the Environment log
        self.print(f"Target is at {target}")

        # the percept bank: one percept for the target...
        self.create(Percept("target", target))
        # ...and one percept for each wall
        for wall in walls:
            self.create(Percept("wall", wall))
        # ...and ONE percept for all the free positions.
        # The `listed` group marks it as "this percept holds a list",
        # so MASPY registers it as a state for the learning part.
        self.create(Percept("position", available, listed))

        # "off-policy" means: the agent may start from ANY state.
        # It also stops MASPY from overwriting the "position" percept
        # with a single random start cell (see Environment._post_init).
        self.possible_starts = "off-policy"

        # the four possible moves, as (dx, dy) offsets - the same idea
        # as the BFS neighbors() generator.
        # NOTE: y grows DOWNWARDS on the screen (like in pygame), so
        # "up" DECREASES y, and "left" DECREASES x.
        self.moves = {
            "up": (0, -1),"down": (0, 1),
            "right": (1, 0), "left": (-1, 0),
        }

    # --------------------------------------------------------
    # reset_positions() - DEAD CODE: nobody calls it in this
    # project (not Walker_Ag, not Walker_Main, not MASPY), and its
    # argument og_pos (agent -> start position) is built by nobody
    # either.
    # --------------------------------------------------------
    def reset_positions(self, og_pos):
        found_pos = self.get(Percept("arrived_target", (Any, Any)), all=True)
        assert isinstance(found_pos, list)
        self.delete(found_pos)
        new_pos_prcpts = self.get(Percept("agt_position", (Any, Any)), all=True)
        assert isinstance(new_pos_prcpts, list)
        for pos_prcpt in new_pos_prcpts:
            pos_prcpt.change(values=og_pos[pos_prcpt.group])

    # --------------------------------------------------------
    # on_connect()
    # Runs when an agent connects to the Map. It picks a random
    # starting cell that is not a wall and is far from the target,
    # then stores it as the agent's position.
    # WHO calls it: MASPY, automatically - the chain is
    #   agent.add_policy(model) -> agent.connect_to(env)
    #   -> env.add_agents(agent) -> on_connect(agent_name)
    # (maspy agent.py:697, environment.py:433)
    # --------------------------------------------------------
    def on_connect(self, agt):
        target = self.get(Percept("target", (Any,Any))).values
        while True:
            start_pos = (randint(0, self.map_size[0]-1), randint(0, self.map_size[1]-1))
            if not self.has(Percept("wall", start_pos)) and (abs(start_pos[0] - target[0]) + abs(start_pos[1] - target[1])) > self.map_size[0]/2:
                break
        self.create(Percept("agt_position", start_pos, agt))
        #print(f"MAP> Agent {agt} starts at {start_pos}")

    # --------------------------------------------------------
    # moviment()
    # Where the agent ends up after one step. max/min keep the
    # new position inside the grid (an agent at the edge trying
    # to go further stays in place).
    # NOTE: this is pure GEOMETRY - walls are NOT checked here
    # (that is the job of move_transition() and move()).
    # --------------------------------------------------------
    def moviment(self, position, direction):
        dx, dy = self.moves[direction]
        new_x = max(0, min(position[0] + dx, self.map_size[0] - 1))
        new_y = max(0, min(position[1] + dy, self.map_size[1] - 1))
        return new_x, new_y

    # --------------------------------------------------------
    # move_transition()
    # The reward of a step - the "lesson plan" the Q-learning will
    # chase. It only REPORTS what would happen (new position,
    # reward, terminated) - it does NOT move anybody.
    #     -1  for every normal step (the agent should hurry)
    #     +10 for reaching the target
    #     -10 for hitting a wall or bumping into the edge
    # --------------------------------------------------------
    def move_transition(self, position, direction):
        reward = -1
        terminated = False

        new_position = self.moviment(position, direction)
        target = self.get(Percept("target", (Any, Any)))
        if new_position == target.values:
            reward = 10
            terminated = True
        elif self.has(Percept("wall", new_position)) or position == new_position:
            reward = -10
        return new_position, reward, terminated

    # --------------------------------------------------------
    # move() + @action - the action the agents actually call.
    # @action tells MASPY: "this method is an action, these are its
    # parameters, and this is the function that computes the
    # transition" (so move_transition() is the transition table the
    # learning part simulates; move() is the real execution).
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
        target = self.get(Percept("target", (Any, Any)))
        if isinstance(target, Percept) and n_pos == target.values:
            self.print(f"{agt} in {pos} moves {direction} and arrived at {target.values}")
            self.create(Percept("arrived_target", n_pos, agt))
        elif wall_flag:
            self.print(f"{agt} in {pos} moves {direction} but hits a wall")
        else:
            self.print(f"{agt} in {pos} moves {direction} to {n_pos}")
