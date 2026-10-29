"""
WALKER_MAIN.PY - starts the menu, the Map, the walkers and the pygame UI.
"""

from maspy import Admin, Percept, Any, Channel
from Walker_Ag import Walker
from threading import Thread

from Map_Env import Map
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
    env = Map(map_size, walls_perc)

    target = env.get(Percept("target", (Any, Any)))
    walls = env.get(Percept("wall", (Any, Any)), all=True)
    print("Map -> target:", target.values, "| walls:", len(walls))

    # State space = all free cells.
    position = env._states["position"][0].data
    print("state space ->", len(position), "positions (the free cells)")

    # One walker per agent.
    walkers = []
    for _ in range(num_walkers):
        wlk = Walker("wk", env, episodes)
        walkers.append(wlk)
        agt_pos = env.get(Percept("agt_position", (Any, Any), wlk.my_name), ck_group=True)
        print(f"Walker \"{wlk.my_name}\" connected - starts at {agt_pos.values}")

    # Start the system and the map window.
    Admin().slow_cycle_by(0.2)
    Thread(target=Admin().start_system, daemon=True).start()
    # Map window loop.
    vis = MapVisualizer(env)
    vis.loop()
