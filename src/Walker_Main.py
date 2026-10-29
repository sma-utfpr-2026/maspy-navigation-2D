"""
WALKER_MAIN.PY - starts the menu, the Map, the walkers and the pygame UI.
"""

from maspy import Admin, Percept, Any, Channel
from Walker_Ag import Walker
from threading import Thread

from env import Map
from Pygame_Screens import MenuScreen, MapVisualizer

from gui.start import start_interface


if __name__ == '__main__':
    # Admin must exist before the Map.
    Admin(listener_log=True)
    Channel().show_exec = True

    # Setup menu.
    menu = MenuScreen()
    settings = menu.loop()
    print("Settings:", settings)

    map_size, walls_perc, num_walkers, episodes = settings

    # Map; targets and walls are percepts.
    game_map = Map(map_size, walls_perc)

    targets = game_map.get(Percept("target", (Any, Any)), all=True)
    walls = game_map.get(Percept("wall", (Any, Any)), all=True)
    print("Map -> targets:", [t.values for t in targets], f"| walls: {len(walls)}")

    # State space = all free cells.
    position = game_map._states["position"][0].data
    print("state space ->", len(position), "positions (the free cells)")

    # One walker per agent.
    walkers = []
    for i in range(num_walkers):
        wlk = Walker(f"wk{i}", game_map, episodes)
        walkers.append(wlk)
        agt_pos = game_map.get(Percept("agt_position", (Any, Any), wlk.my_name), ck_group=True)
        print(f"Walker \"{wlk.my_name}\" connected - starts at {agt_pos.values}")

    # Start the system and the map window.
    Admin().slow_cycle_by(0.2)
    Thread(target=Admin().start_system, daemon=True).start()
    # Map window loop.
    vis = MapVisualizer(game_map)
    vis.loop()
