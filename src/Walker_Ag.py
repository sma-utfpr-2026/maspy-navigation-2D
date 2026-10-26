"""
WALKER_AG.PY - the Walker agent (a random wanderer that becomes an A*
planner once it knows the target).

Behavior:
    - Training: EnvModel + Q-learning run in the constructor. The learned
      policy is not used by the wandering (see make_move).
    - make_move: random walk until the target is found; the agent that
      reaches it first broadcasts Belief("target") and stops.
    - best_move: once Belief("target") exists, moves along an A* path over
      the agent's notebook (Path_Graph / Wall_Set), replanning every step.
    - update_map / update_graph / update_walls: the notebook, and its
      sharing between walkers by broadcast.

"""
from maspy import *
from maspy.learning import *
from random import choice      # the random direction of make_move's wandering
from collections import deque  # used only by reconstruct_path_known (DEAD CODE)
import heapq  # astar_explore's open set

# Debug drawing of the notebook: '.' = not walked and not a known wall
# (it may still hide undiscovered walls). Known bugs in this original
# version, to be fixed separately:
#   - the frame comes from graph keys only, so the target and walls outside
#     the walked area are not drawn;
#   - walls=None (its own default) crashes on 'pos in walls'.
def draw_ascii_map(graph, walls=None, target=None):
    if not graph:
        print("(empty graph)")
        return
    ys = [x for x, _ in graph.keys()]
    xs = [y for _, y in graph.keys()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    print("  ", end="")
    for x in range(min_y, max_y + 1):
        print(f"{x} ", end="")
    print()
    for y in range(min_x, max_x + 1):
        row = f"{y} "
        for x in range(min_y, max_y + 1):
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


    # reconstruct_path() - DEAD CODE: nobody calls it. Its only caller,
    # reconstruct_path_known, is never called either (A* uses astar_explore).
def reconstruct_path(came_from, current):
    path = []
    while current is not None:
        path.append(current)
        current = came_from[current]
    return path[::-1]

    # reconstruct_path_known() - DEAD CODE: BFS over the known graph. Nobody
    # calls it, not even in the final version. Kept for reference.
def reconstruct_path_known(start, target, known):
    q = deque([start])
    prev = {start: None}

    while q:
        cur = q.popleft()
        if cur == target:
            return reconstruct_path(prev, cur)
        if cur not in known:
            continue
        for nxt in known[cur]:
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    return None

# A* search over the agent's notebook. Returns the cell list from start to
# goal (inclusive), or None when there is no route.
def astar_explore(start, goal, known, walls, who=""):
    walls = set(walls)
    start = tuple(start)
    goal = tuple(goal)
    tag = f"[astar {who}]" if who else "[astar]"

    # open_set: min-heap of (f, cell), the cheapest-looking cell pops first.
    # g: real cost so far. came_from: parent of each cell, to rebuild the path.
    open_set = []
    heapq.heappush(open_set, (0, start))
    print(f"{tag} start {start} -> goal {goal} | known {len(known)} cells | walls {len(walls)}")

    came_from = {}
    g = {start: 0}
    expanded = 0

    # h = Manhattan distance to the goal, ignoring walls (never overestimates).
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

        # Neighbors the agent has walked from cost 1; neighbors it has not
        # walked yet (and are not known walls) cost 1.25 - the risk premium.
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

# Turns the A* path into one move: "up", "down", "left", "right" or "stay".
def astar_direction(ag, position, target):
    map_graph = ag.get(Belief("Path_Graph", Any))
    wall_set = ag.get(Belief("Wall_Set", Any))
    # Recomputed on every call, so each cycle replans with the latest notebook.
    path = astar_explore(position, target, map_graph.values, wall_set.values, ag.my_name)
    if path is None:
        path = []
    # path[0] is the cell we stand on; path[1] is the next cell to step into.
    # No route -> path is [], so we aim straight at the goal as a fallback.
    if len(path) > 1:
        target = path[1]
        
    # The step between position and next cell becomes one direction word.
    # Vertical wins ties (abs(dy) >= abs(dx)); (0, 0) means already there.
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
    def __init__(self, name, map: Environment, episodes: int):
        super().__init__(name, max_intentions=1)
        # The agent only perceives its own position (agt_position); walls,
        # target and the other walkers stay out of its beliefs.
        # add_policy also connects the agent to the map (env.on_connect).
        self.filter_perceptions(add, focus, self.my_name)
        #self.show_slct = True
        #self.show_cycle = True
        model = EnvModel(map, self, True)
        self.add_policy(model)
        state = model.env.get(Percept("agt_position", (Any, Any), self.my_name), ck_group=True)
        assert isinstance(state, Percept)
        model.initial_states = {"position": [state.values]}
        #print(f"Agent {self.my_name} starts at {state.values}")
        # Q-learning training runs synchronously here (episodes = the
        # menu's value). It fills model.q_table; the wandering ignores it.
        model.learn(qlearning, num_episodes=episodes)
        self.reset_knowledge()
    
    # Empties the notebook (Path_Graph, Wall_Set) and adds Goal("move"),
    # the trigger the @pl plans wait for.
    def reset_knowledge(self):
        self.rm(Belief("Path_Graph", Any))
        self.add(Belief("Path_Graph", dict()))
        self.rm(Belief("Wall_Set", Any))
        self.add(Belief("Wall_Set", []))
        self.add(Goal("move"))

    # The notebook, written after every step. Path_Graph gets an edge when
    # the agent walks to a new cell. Wall_Set gets the cell in front when
    # the step lands back on the same cell (walls are known only by bumping).
    # The sends share the notebook with the other walkers.
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
            # shares the WHOLE notebook with every co-walker (broadcast
            # reaches all channel members except the sender)
            self.send(broadcast, tell, Belief("Sent_Graph", old_graph))
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
                self.send(broadcast, tell, Belief("Sent_Walls", walls))

    # The "Professor": once Belief("target") exists, each cycle takes one
    # A* step (astar_direction), moves, updates the notebook and stops on
    # arrival. It returns False so the cycle retries. It is registered
    # before make_move, so it wins whenever the target is known.
    @pl(gain, Goal("move"), Belief("target", (Any,Any)) & Belief("agt_position", (Any,Any), "Map"))
    def best_move(self, src, target, position):
        direction = astar_direction(self, position, target)
        self.print(f'Knowing target {target} and my position {position}  - moving {direction}')
        if direction != "stay": self.move(direction)
        
        self.perceive("Map") # Manual Perception of Map
        self.update_map(position, direction) # Update of Map/Wall Beliefs
        
        if not self.has(Belief("arrived_target", (Any,Any), "Map")):
            return False # Retries current event
        else:
            self.print(f"Driver {self.my_name} arrived at {target}")
            self.stop_cycle()
        return False
            
    # The wandering plan: each cycle picks a random direction and moves.
    # The learned branch is dead code: nothing creates Belief("use_learn"),
    # so the wandering is always random. Returns False until the target
    # is reached (MASPY retries the plan every cycle).
    @pl(gain, Goal("move"), Belief("agt_position", (Any,Any), "Map"))
    def make_move(self, src, position):
        if self.has(Belief("use_learn")):
            direction, _ = self.get_best_action("Map",(position,))
            self.print(f"From {position} Moving on a Learned Direction ({direction})")
        else:
            direction = choice(["up", "down", "left", "right"])
            self.print(f"From {position} Moving on a Random Direction ({direction})")
        self.move(direction) # Move Action

        self.perceive("Map") # Manual Perception of Map
        self.update_map(position, direction) # Update of Map/Wall Beliefs
            
        if not self.has(Belief("arrived_target", (Any,Any), "Map")):
            return False # Retries current event 
        
        target = self.get(Belief("arrived_target", (Any,Any), "Map"))
        self.print(f"Driver {self.my_name} arrived at {target} first, sending target")
        # The notebook is drawn once, on arrival (the original never drew it).
        # Plain print, not self.print: the drawing needs end="" and must stay
        # visible even after stop_cycle empties the agent's buffer.
        map_graph = self.get(Belief("Path_Graph", Any))
        wall_list = self.get(Belief("Wall_Set", Any))
        print(f"\n=== notebook of {self.my_name} | "
              f"{len(map_graph.values)} cells | {len(wall_list.values)} walls found ===")
        draw_ascii_map(map_graph.values, wall_list.values)
        # The only way the target reaches the other walkers. The finder
        # keeps just its own arrived_target: broadcast excludes the sender.
        self.send(broadcast, tell, Belief("target", target.values))
        self.print(f"Driver {self.my_name} finished broadcast")
        self.stop_cycle()

    
    # Receivers of the notebooks shared by the other walkers. atomic: the
    # body runs without interruption. update_graph merges every node and
    # its neighbors into this agent's notebook.
    @pl(gain, Belief("Sent_Graph", Any), plan_type=atomic)
    def update_graph(self, src, sent_graph):
        map_graph = self.get(Belief("Path_Graph", Any))
        old_graph = map_graph.values
        for node, neighbors in sent_graph.items():
            if node not in old_graph:
                old_graph[node] = set(neighbors)
            else:
                old_graph[node] |= neighbors
        map_graph.change(values=old_graph)

    # Known bug, to be fixed separately: sent_graph[0] is the sender's first
    # wall forever (the sender resends its whole list), so only that one
    # wall ever transfers from each sender.
    @pl(gain, Belief("Sent_Walls", Any), plan_type=atomic)
    def update_walls(self, src, sent_graph):
        wall_set = self.get(Belief("Wall_Set", Any))
        old_set = wall_set.values
        if sent_graph[0] not in old_set:
            old_set.append(sent_graph[0])
            wall_set.change(values=old_set)

