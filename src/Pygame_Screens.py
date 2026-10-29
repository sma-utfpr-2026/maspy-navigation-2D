"""
PYGAME_SCREENS.PY - the two pygame screens of the project

MenuScreen shows the setup form (map size, walls %, agents,
episodes) and returns the settings tuple once Start is clicked.
MapVisualizer draws the map window - grid, target, walls and
agents, all read from the Map's Percepts - plus the sidebar
whose buttons act on the MASPY Admin itself: Pause/Resume
freezes/wakes every agent's cycle, More/Less Delay paces it
(+-1 second per click, floored at 0).

The shared widgets are Button (hover + click callback) and
TextInput (right-aligned label + editable field). The entry
point is Walker_Main.py.
"""

import os
import sys

import pygame

from maspy import Admin, Percept, Any

os.environ['SDL_VIDEO_CENTERED'] = '1'

pygame.init()
FONT = pygame.font.SysFont(None, 24)        # form text
# menu form colors
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (80, 80, 200)
BUTTON_HOVER = (100, 100, 250)

# map screen
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
SIDEBAR_WIDTH = 200
AGENT_COLOR = (0, 100, 255)
TARGET_COLOR = (255, 50, 50)
BG_COLOR = (240, 240, 240)
GRID_COLOR = (200, 200, 200)


# ============================================================
# Button - a clickable button. Draws itself, highlights on
# hover, and calls the callback when clicked.
# ============================================================
class Button:
    def __init__(self, rect, text, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.hover = False

    def draw(self, screen):
        color = BUTTON_HOVER if self.hover else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        text_surf = FONT.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.hover:
            self.callback()


# ============================================================
# TextInput - a labeled text field. Click to type; the default
# value clears on the first click and comes back if the field
# is left empty.
# ============================================================
class TextInput:
    def __init__(self, rect, label, default=""):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.placeholder = default
        self.text = default
        self.active = False
        self.cleared = False   # important
        self.active = False

    def draw(self, screen):
        color = (180, 180, 180) if not self.cleared else (255, 255, 255)
        pygame.draw.rect(screen, (70, 70, 70), self.rect, border_radius=5)
        if self.active:
            pygame.draw.rect(screen, (150, 150, 250), self.rect, 2)
        else:
            pygame.draw.rect(screen, (120, 120, 120), self.rect, 2)
        txt_surface = FONT.render(self.text, True, color)
        #txt_surface = FONT.render(self.text, True, TEXT_COLOR)
        label_surface = FONT.render(self.label, True, TEXT_COLOR)
        screen.blit(label_surface, (self.rect.x - 120, self.rect.y + 5))
        screen.blit(txt_surface, (self.rect.x + 10, self.rect.y + 5))

    def handle_event(self, event):
        # mouse click: inside -> activate the field (clearing the
        # default on the first click); outside -> deactivate
        # (and restore the default if left empty)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                if not self.cleared:
                    self.text = ""
                    self.cleared = True
            else:
                self.active = False
                if self.text == "":
                    self.text = self.placeholder
                    self.cleared = False
        # typing: Backspace erases, Enter confirms, anything else appends
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            else:
                self.text += event.unicode
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     self.active = self.rect.collidepoint(event.pos)
        # if event.type == pygame.KEYDOWN and self.active:
        #     if event.key == pygame.K_RETURN:
        #         self.active = False
        #     elif event.key == pygame.K_BACKSPACE:
        #         self.text = self.text[:-1]
        #     elif event.unicode.isdigit():
        #         self.text += event.unicode


# ============================================================
# MapVisualizer - the map screen. Draws the grid, the target
# (red X), the walls (black squares) and the AGENTS (the colored
# bodies), all read from the Map's Percepts. .draw() renders one
# frame; .loop() runs the window until it is closed.
# ============================================================
class MapVisualizer:
    def __init__(self, env) -> None:
        # opens the map window and keeps a reference to the Map
        # (the drawing asks the Map's Percepts, never plain attributes)
        pygame.init()
        self.env = env
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

        # cell size in pixels, so the whole grid fits the window
        self.map_area_width = WINDOW_WIDTH - SIDEBAR_WIDTH
        self.map_area_height = WINDOW_HEIGHT
        self.cell_size = min(
            self.map_area_width // env.map_size[0],
            self.map_area_height // env.map_size[1],
        )
        pygame.display.set_caption("Map Environment")
        self.clock = pygame.time.Clock()
        # the sidebar buttons (actions on the MASPY Admin, below):
        self.buttons: list[Button] = self._create_buttons()

    # --------------------------------------------------------
    # the sidebar buttons - the user's remote control over the
    # MASPY engine. Each button calls Admin():
    #   Pause/Resume -> Admin().pause_system()  (freezes/wakes
    #     EVERY agent's cycle in one shared event)
    #   More/Less Delay -> Admin().slower_cycle()/faster_cycle()
    #     (paces the cycle loop up and down)
    # The widgets are the same Button class the MenuScreen uses.
    # --------------------------------------------------------
    def _create_buttons(self):
        buttons = []
        x = self.env.map_size[0]*self.cell_size + 20
        y = 40
        spacing = 60
        actions = [self.action_1, self.action_2, self.action_3]
        names = ["Pause/Resume", "More Delay", "Less Delay"]
        for i, func in enumerate(actions):
            btn = Button(
                rect=(x, y + i*spacing, SIDEBAR_WIDTH-40, 40),
                text= names[i],
                callback=func
            )
            buttons.append(btn)
        return buttons

    def action_1(self): Admin().pause_system()
    def action_2(self): Admin().slower_cycle()
    def action_3(self): Admin().faster_cycle()

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(self.env.map_size[0]*self.cell_size, 0, SIDEBAR_WIDTH, self.env.map_size[1]*self.cell_size)
        pygame.draw.rect(self.screen, (30, 30, 60), sidebar_rect)
        for btn in self.buttons:
            btn.draw(self.screen)
    
    def draw_map(self):
        # one frame of the map itself: grid, then target, then walls

        # grid
        for x in range(0, self.env.map_size[0]*self.cell_size, self.cell_size):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, self.env.map_size[1]*self.cell_size))
        for y in range(0, self.env.map_size[1]*self.cell_size, self.cell_size):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (self.env.map_size[0]*self.cell_size, y))

        # draw the target: ask the environment for the "target" percept
        target = self.env.get(Percept("target", (Any, Any)))
        if target:
            tx, ty = target.values
            cx, cy = tx * self.cell_size, ty * self.cell_size
            pygame.draw.line(self.screen, TARGET_COLOR,
                            (cx + 4, cy + 4),
                            (cx + self.cell_size - 4, cy + self.cell_size - 4), 3)
            pygame.draw.line(self.screen, TARGET_COLOR,
                            (cx + self.cell_size - 4, cy + 4),
                            (cx + 4, cy + self.cell_size - 4), 3)

        # draw the walls: ask for ALL the "wall" percepts
        if self.env.has(Percept("wall", (Any, Any))):
            walls = self.env.get(Percept("wall", (Any, Any)), all=True)
            if not walls: walls = []
            for wall in walls:
                wx, wy = wall.values
                rect = pygame.Rect(wx * self.cell_size, wy * self.cell_size,
                                   self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, (0, 0, 0), rect)
        # draw agents - the colored bodies. The "agt_position" Percepts
        # exist because on_connect creates them when each agent
        # connects. The drawing reads the Percepts directly - no local
        # copy of any position lives on the screen side.
        for percept in self.env.get(Percept("agt_position", (Any, Any)), all=True):
            x, y = percept.values
            cx = x * self.cell_size + self.cell_size // 2
            cy = y * self.cell_size + self.cell_size // 2
            body = self.cell_size // 4

            # body
            pygame.draw.rect(self.screen, AGENT_COLOR,
                             (cx - body//2, cy - body//2, body, body))
            # body id
            agent_id = percept.group.split("_")[-1]
            font = pygame.font.SysFont(None, body)
            text = font.render(agent_id, True, (255, 255, 255))  # black text
            text_rect = text.get_rect(center=(cx, cy))

            self.screen.blit(text, text_rect)

            # legs
            leg_len = self.cell_size // 3
            # body bottom corners/sides
            bottom_left  = (cx - body//2, cy + body//2)
            bottom_right = (cx + body//2, cy + body//2)

            # left leg (angled left-down)
            pygame.draw.line(self.screen, AGENT_COLOR,
                            bottom_left,
                            (bottom_left[0] - leg_len//2, bottom_left[1] + leg_len), 2)

            # left-mid leg (straight down)
            pygame.draw.line(self.screen, AGENT_COLOR,
                            (cx - body//4, cy + body//2),
                            (cx - body//4, cy + body//2 + leg_len), 2)

            # right-mid leg (straight down)
            pygame.draw.line(self.screen, AGENT_COLOR,
                            (cx + body//4, cy + body//2),
                            (cx + body//4, cy + body//2 + leg_len), 2)

            # right leg (angled right-down)
            pygame.draw.line(self.screen, AGENT_COLOR,
                            bottom_right,
                            (bottom_right[0] + leg_len//2, bottom_right[1] + leg_len), 2)

    def draw(self):
        # one full frame: fill the background, draw the map, show it
        self.screen.fill(BG_COLOR)
        self.draw_map()
        self.draw_sidebar()
        pygame.display.flip()

    def loop(self):
        # the map window's event loop: handles events and redraws the
        # frame ~30 times per second, until the window is closed
        running = True
        while running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    for btn in self.buttons:
                        btn.handle_event(event)
            except Exception as e:
                print(e)
                sys.exit()

            self.draw()

            pygame.time.delay(10)
            self.clock.tick(30) 

        pygame.quit()


# ============================================================
# MenuScreen - the setup form. Draws the 5 fields and the Start
# button; .loop() runs until Start is clicked and returns
# ((width, height), walls_perc, agents, episodes)
# ============================================================
class MenuScreen:
    def __init__(self):
        self.screen = pygame.display.set_mode((400, 400))
        pygame.display.set_caption("Simulation Setup")
        self.clock = pygame.time.Clock()
        self.inputs = [
            TextInput((200, 60, 100, 25), "Map Width:", "10"),
            TextInput((200, 100, 100, 25), "Map Height:", "10"),
            TextInput((200, 140, 100, 25), "Walls %:", "20"),
            TextInput((200, 200, 100, 25), "Agents:", "6"),
            TextInput((200, 240, 100, 25), "Episodes:", "2000")
        ]
        self.start_button = Button((175, 300, 150, 50), "Start Simulation", self.start)
        self.done = False
        self.settings = None

    def start(self):
        # called when the Start button is clicked
        try:
            width = int(self.inputs[0].text)
            height = int(self.inputs[1].text)
            walls_perc = float(self.inputs[2].text) / 100
            agents = int(self.inputs[3].text)
            episodes = int(self.inputs[4].text)
        except ValueError:
            print("Invalid input: every field must be a number")
            return

        # agents < 1 is accepted here and opens an empty simulation;
        # fixed in the `fix/known-bugs` branch (menu requires at least 1).
        self.settings = ((width, height), walls_perc, agents, episodes)
        self.done = True

    def draw(self):
        self.screen.fill((20, 20, 50))
        for inp in self.inputs:
            inp.draw(self.screen)
        self.start_button.draw(self.screen)
        pygame.display.flip()

    def loop(self):
        # the menu's event loop: polls typing/clicks and redraws the
        # form until the Start button sets done = True
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                for inp in self.inputs:
                    inp.handle_event(event)

                self.start_button.handle_event(event)

            self.draw()
            self.clock.tick(30)

        return self.settings
