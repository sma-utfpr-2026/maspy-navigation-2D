"""
WALKER_MAIN.PY - how the simulation starts

Starts the MASPY Admin, opens the setup menu, builds the Map and
the walkers (each constructor connects, and trains when episodes
> 0), starts the system thread, and shows the pygame screen with
everything on it.
"""

from maspy import Admin, Percept, Any, Channel
from Walker_Ag import Walker
from threading import Thread

from Map_Env import Map
from Pygame_Screens import MenuScreen, MapVisualizer

from gui.start import start_interface


if __name__ == '__main__':
    # the MASPY manager - must run BEFORE creating the Map
    # (the Map registers itself with the Admin when it is born)
    Admin(listener_log=True)
    Channel().show_exec = True

    # opens the menu and waits for the Start click
    menu = MenuScreen()
    settings = menu.loop()
    print("Settings:", settings)

    # unpack: ((width, height), walls %, number of agents, episodes)
    map_size, walls_perc, num_walkers, episodes = settings

    # the Map from Map_Env.py. Its data now lives in the percept bank,
    # so we have to ask for it (the same way the visualizer does)
    env = Map(map_size, walls_perc)

    target = env.get(Percept("target", (Any, Any)))
    walls = env.get(Percept("wall", (Any, Any)), all=True)
    print("Map -> target:", target.values, "| walls:", len(walls))

    # the "position" percept is the state space of the learning:
    # one single percept holding all the free cells
    position = env._states["position"][0].data
    print("state space ->", len(position), "positions (the free cells)")

    # create num_walkers walkers
    walkers = []
    for _ in range(num_walkers):
        wlk = Walker("wk", env, episodes)
        walkers.append(wlk)
        agt_pos = env.get(Percept("agt_position", (Any, Any), wlk.my_name), ck_group=True)
        print(f"Walker \"{wlk.my_name}\" connected - starts at {agt_pos.values}")

    # the system starts: the print/log buffer flushes and the
    # walkers begin their cycles - make_move drives them now
    Admin().slow_cycle_by(0.2)
    Thread(target=Admin().start_system, daemon=True).start()
    #Thread(target=start_interface, daemon=True).start()  # DEAD: nobody calls it (the sim runs on MapVisualizer)

    # opens the map window - the loop redraws until it is closed
    vis = MapVisualizer(env)
    vis.loop()
