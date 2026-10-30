"""
WALKER_AG.PY - the Walker agent.

Untrained: exploration. Trained: learned policy until find the first target, then change to exploration. Notebooks are private.
"""
from maspy import *
from maspy.learning import *
from random import choice, randint
import heapq  # astar_explore's open set

# Nearest unexplored neighbor of the private notebook.
def pick_unexplored_neighbor(known, walls, position, k=3):
    known_cells = set(known)
    wall_cells = set(walls) if walls else set()
    candidates = set()
    for (x, y) in known_cells:
        for nxt in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if nxt not in known_cells and nxt not in wall_cells:
                candidates.add(nxt)
    if not candidates:
        return None
    scored = sorted(candidates,
                    key=lambda c: abs(c[0] - position[0]) + abs(c[1] - position[1]))
    return scored[randint(0, min(k, len(scored)) - 1)]

# One exploration step: A* toward an unexplored neighbor.
def next_explore_direction(ag, position, k=3):
    graph = ag.get(Belief("Path_Graph", Any)).values
    wall_list = ag.get(Belief("Wall_Set", Any)).values
    neighbor = pick_unexplored_neighbor(graph, wall_list, position, k)
    if neighbor is None:
        print(f"[explore {ag.my_name}] no unexplored neighbor left - random step")
        return choice(["up", "down", "left", "right"])
    return astar_direction(ag, position, neighbor)

# Debug drawing of the notebook ('.' = unknown).
def draw_ascii_map(graph, walls=None, target=None):
    walls = list(walls) if walls else []
    points_to_draw = set(graph) | set(walls)
    if target is not None:
        points_to_draw.add(target)
    if not points_to_draw:
        print("(empty graph)")
        return
    min_x = min(p[0] for p in points_to_draw)
    max_x = max(p[0] for p in points_to_draw)
    min_y = min(p[1] for p in points_to_draw)
    max_y = max(p[1] for p in points_to_draw)
    print("  ", end="")
    for x in range(min_x, max_x + 1):
        print(f"{x} ", end="")
    print()
    for y in range(min_y, max_y + 1):
        row = f"{y} "
        for x in range(min_x, max_x + 1):
            pos = (x, y)

            if pos == target:
                row += "X "
            elif pos in walls:
                row += "# "
            elif pos in graph:
                row += "o "   
            else:
                row += ". "      
        print(row)

# A* over the notebook; unknown cells cost 1.25.
def astar_explore(start, goal, known, walls, who=""):
    walls = set(walls)
    start = tuple(start)
    goal = tuple(goal)
    tag = f"[astar {who}]" if who else "[astar]"

    # open set (f, cell); came_from rebuilds the path.
    open_set = []
    heapq.heappush(open_set, (0, start))
    print(f"{tag} start {start} -> goal {goal} | known {len(known)} cells | walls {len(walls)}")

    came_from = {}
    g = {start: 0}
    expanded = 0

    def h(p):
        return abs(goal[0] - p[0]) + abs(goal[1] - p[1])

    def neighbors(node):
        x, y = node
        all_nbrs = [
            (x+1, y),
            (x-1, y),
            (x, y+1),
            (x, y-1),
        ]

        valid = []
        for nxt in all_nbrs:
            if nxt in walls:
                continue
            valid.append(nxt)
        return valid

    while open_set:
        f_cost, current = heapq.heappop(open_set)
        expanded += 1
        print(f"{tag} expand {current} g={g[current]} f={f_cost}")

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            print(f"{tag} goal reached: {len(path)} cells, {expanded} expansions | path {path}")
            return path

        known_neighbors = known.get(current, set())
        unknown_neighbors = [n for n in neighbors(current) if n not in known_neighbors]
        
        for nxt in known_neighbors:
            new_cost = g[current] + 1
            if nxt not in g or new_cost < g[nxt]:
                g[nxt] = new_cost
                came_from[nxt] = current
                heapq.heappush(open_set, (new_cost + h(nxt), nxt))

        for nxt in unknown_neighbors:
            new_cost = g[current] + 1.25
            if nxt not in g or new_cost < g[nxt]:
                g[nxt] = new_cost
                came_from[nxt] = current
                heapq.heappush(open_set, (new_cost + h(nxt), nxt))

    print(f"{tag} no route: {expanded} expansions")
    return None 

# One move from an A* path.
def astar_direction(ag, position, target):
    map_graph = ag.get(Belief("Path_Graph", Any))
    wall_set = ag.get(Belief("Wall_Set", Any))
    path = astar_explore(position, target, map_graph.values, wall_set.values, ag.my_name)
    if path is None:
        path = []
    if len(path) > 1:
        target = path[1]
        
    dx, dy = target[0] - position[0], target[1] - position[1]
    if dx == 0 and dy == 0:
        direction = "stay"
    elif abs(dy) >= abs(dx):
        direction = "down" if dy > 0 else "up"
    else:
        direction = "right" if dx > 0 else "left"
    print(f"[astar_direction {ag.my_name}] path {path} | next cell {path[1] if len(path) > 1 else None} | move {direction}")
    return direction

class Walker(Agent):
    def __init__(self, name, map: Environment, episodes: int | None):
        super().__init__(name, max_intentions=1)
        # Perceive only own position and the public state; add_policy also connects the map.
        self.filter_perceptions(add, focus, [self.my_name, "public"])
        #self.show_slct = True
        #self.show_cycle = True
        if episodes is not None:
            model = EnvModel(map, self, show_learning=True)
            self.add_policy(model)
            state = model.env.get(Percept("agt_position", (Any, Any), self.my_name), ck_group=True)
            assert isinstance(state, Percept)
            model.initial_states = {"position": [state.values]}
            print(f"Agent {self.my_name} starts at {state.values}")
            # Train synchronously, then use the learned policy.
            model.learn(qlearning, num_episodes=episodes)
            self.print("This process will use the trained model for execution")
            self.add(Belief("mode", "use_learn", adds_event=False))
        else:
            self.print("This process will not run the training")
            self.connect_to(map)
            # No training: explore from the first cycle.
            self.add(Belief("mode", "explore", adds_event=False))

        self.reset_knowledge()
    
    # Empty notebook + the Goal("move") trigger.
    def reset_knowledge(self):
        self.rm(Belief("Path_Graph", Any))
        self.add(Belief("Path_Graph", dict()))
        self.rm(Belief("Wall_Set", Any))
        self.add(Belief("Wall_Set", []))
        self.add(Goal("move"))

    # Private notebook: new edge, or wall bumped.
    def update_map(self, position, direction):
        map_graph = self.get(Belief("Path_Graph", Any))
        wall_list = self.get(Belief("Wall_Set", Any))
        new_pos = self.get(Belief("agt_position", (Any,Any), "Map"))
        assert (map_graph and wall_list and new_pos), f"{map_graph} | {wall_list} | {new_pos}"
        if new_pos.values not in map_graph.values:
            old_graph = map_graph.values
            old_graph.setdefault(position, set()).add(new_pos.values)
            old_graph.setdefault(new_pos.values, set()).add(position)
            map_graph.change(values=old_graph)
            # Remove sharing knowledge about freely discovered cells with other agents (because of competition mode)
            # self.send(broadcast, tell, Belief("Sent_Graph", old_graph))
        if new_pos.values == position and direction != "stay":
            match direction:
                case "up": wall_pos = (position[0],position[1]-1)
                case "down": wall_pos = (position[0],position[1]+1)
                case "left": wall_pos = (position[0]-1,position[1])
                case "right": wall_pos = (position[0]+1,position[1])
            walls = wall_list.values
            if wall_pos not in walls:
                walls.append(wall_pos)
                self.print(f"Driver {self.my_name} found a wall at {wall_pos} added to {walls}")
                # Remove sharing knowledge about discovered walls with other agents (because of competition mode)
                # self.send(broadcast, tell, Belief("Sent_Walls", walls))

    # One step per cycle: learned policy or exploration.
    @pl(gain, Goal("move"), Belief("agt_position", (Any,Any), "Map"))
    def make_move(self, src, position):
        if self.get(Belief("mode", "use_learn", adds_event=False)) is not None:
            direction, _ = self.get_best_action("Map",(position,))
            self.print(f"From {position} Moving on a Learned Direction ({direction})")
        else:
            direction = next_explore_direction(self, position)
            self.print(f"From {position} Exploring toward unexplored neighbor ({direction})")
        self.move(direction)

        self.perceive("Map")
        self.update_map(position, direction)

        if not self.has(Belief("arrived_target", (Any,Any), "Map")):
            return False

        target = self.get(Belief("arrived_target", (Any,Any), "Map"))
        self.print(f"Driver {self.my_name} arrived at {target}")
        map_graph = self.get(Belief("Path_Graph", Any))
        wall_list = self.get(Belief("Wall_Set", Any))
        print(f"\n=== notebook of {self.my_name} | "
              f"{len(map_graph.values)} cells | {len(wall_list.values)} walls found ===")
        draw_ascii_map(map_graph.values, wall_list.values)
        # The public state tells the capturer whether it took the last target.
        remaining = self.get(Belief("targets_left", Any, "Map"))
        if remaining is not None and remaining.values == 0:
            self.send(broadcast, tell, Belief("game_over", "over"))
            self.print("All targets captured - notifying the other walkers (game over)")
        else:
            self.send(broadcast, tell, Belief("target_lost", target.values))
            self.print(f"Target {target.values} captured - notifying the other walkers")
        self.stop_cycle()

    # Channel notification from the capturer: trained walkers switch to exploration.
    @pl(gain, Belief("target_lost", (Any,Any)), plan_type=atomic)
    def on_target_lost(self, src, *args):
        mode_belief = self.get(Belief("mode", "use_learn", adds_event=False))
        if mode_belief is not None:
            mode_belief.change("mode", "explore", adds_event=False)
            self.print(f"Target captured by {src} - switching to exploration")

    # Channel notification that every target was captured: stop the walker.
    @pl(gain, Belief("game_over", Any), plan_type=atomic)
    def on_game_over(self, src, *args):
        self.print("Game over - every target was captured, stopping")
        self.stop_cycle()
