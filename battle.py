from area import SingleTarget
from battleground import Battleground
from general import *
from window import *

from config import COLOR_WHITE, COLOR_BACKGROUND, WINDOW_WIDTH, WINDOW_HEIGHT

import copy
import re
import sys

from config import DEBUG

KEYMAP_SKILLS = "QWERTYUIOP"
KEYMAP_SWAP = "123456789"
KEYMAP_TACTICS = "ZXCVBNM"

FLAG_PATTERN = re.compile(r"flag \((-?\d+),(-?\d+)\)")
SKILL_PATTERN = re.compile(r"skill(\d) \((-?\d+),(-?\d+)\)")


class BattleWindow(Window):
    def __init__(self, battleground, side, host=None, port=None, window_id=1):
        if DEBUG:
            sys.stdout.write("DEBUG: BattleWindow.__init__ started\n")

        for i in [0, 1]:
            battleground.generals[i].start_battle()
            battleground.generals[i].formation.place_minions()
            for g in battleground.reserves[i]:
                g.start_battle()

        self.keymap_skills = KEYMAP_SKILLS[0:len(battleground.generals[side].skills)]
        self.keymap_swap = KEYMAP_SWAP[0:len(battleground.reserves[side])]
        self.keymap_tactics = KEYMAP_TACTICS[0:len(battleground.generals[side].tactics)]

        if DEBUG:
            sys.stdout.write("DEBUG: About to call super(BattleWindow, self).__init__\n")

        super(BattleWindow, self).__init__(battleground, side, host, port, window_id)

        if DEBUG:
            sys.stdout.write("DEBUG: BattleWindow.__init__ completed\n")

    def ai_action(self, turn):
        ai_side = (self.side + 1) % 2
        return self.bg.generals[ai_side].ai_action(turn)

    def check_input(self, keys, mouse, x, y):
        # mouse[0] is left, mouse[1] is middle, mouse[2] is right
        if mouse[2]: # Right-click to place flag
            return "flag ({0},{1})\n".format(x, y)

        # We need to handle key presses carefully to avoid them firing every frame.
        # A simple way is to check them inside the event loop, but for this structure,
        # we'll assume the main loop runs fast enough that a turn-based check is okay.
        # For a better implementation, you'd track keydown events.

        if keys[pygame.K_s]:
            return "stop\n"

        # Swap Reserves (1-9)
        swap_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
        for i in range(len(self.keymap_swap)):
            if keys[swap_keys[i]]:
                return f"swap{i}\n"

        # Use Skills (Q-P)
        skill_keys = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t, pygame.K_y, pygame.K_u, pygame.K_i, pygame.K_o, pygame.K_p]
        for i in range(len(self.keymap_skills)):
            if keys[skill_keys[i]]:
                # Check for SHIFT key modifier to preview skill area (like original)
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    self.hover_function = self.bg.generals[self.side].skills[i].get_area_tiles
                else:  # No shift, use the skill
                    self.hover_function = None
                    return "skill{0} ({1},{2})\n".format(i, x, y)
                # Return None if we are only previewing so we don't send a network message
                return None

        # Switch Tactic (Spacebar)
        if keys[pygame.K_SPACE]:
            gen = self.bg.generals[self.side]
            if gen.tactics.index(gen.selected_tactic) == 0:
                n = gen.tactics.index(gen.previous_tactic)
            else:
                gen.previous_tactic = gen.selected_tactic
                n = 0
            return f"tactic{n}\n"

        # Select Tactic (Z-M)
        tactic_keys = [pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n, pygame.K_m]
        for i in range(len(self.keymap_tactics)):
            if keys[tactic_keys[i]]:
                gen = self.bg.generals[self.side]
                if gen.tactics.index(gen.selected_tactic) != 0:
                    gen.previous_tactic = gen.selected_tactic
                return f"tactic{i}\n"

        return None

    def check_winner(self):
        # TODO: detect draws
        for i in [0, 1]:
            if not self.bg.generals[i].alive:
                self.message(
                    self.bg.generals[i].name + ": " + self.bg.generals[i].death_quote,
                    self.bg.generals[i].original_color,
                )
                self.message(self.bg.generals[i].name + " is dead!", self.bg.generals[i].original_color)
                self.game_over = True
                return self.bg.generals[(i + 1) % 2]
        return None

    def clean_all(self):
        for e in copy.copy(self.bg.effects):
            if not e.alive:
                self.bg.effects.remove(e)
        for m in copy.copy(self.bg.minions):
            if not m.alive:
                self.bg.minions.remove(m)

    def process_messages(self, turn):
        for i in [0, 1]:
            if turn in self.messages[i]:
                m = self.messages[i][turn]
                if DEBUG:
                    sys.stdout.write(str(i) + "," + str(turn) + "#" + m)
                if m.startswith("stop"):
                    self.bg.generals[i].place_flag(-1, -1)
                elif m.startswith("tactic"):
                    self.bg.generals[i].command_tactic(int(m[6]))
                elif m.startswith("swap"):
                    if self.bg.generals[i].swap(int(m[4])):
                        self.render_panels()
                else:
                    match = FLAG_PATTERN.match(m)
                    if match:
                        self.bg.generals[i].place_flag(int(match.group(1)), int(match.group(2)))
                    else:
                        match = SKILL_PATTERN.match(m)
                        if match:
                            if self.bg.generals[i].use_skill(*map(int, match.groups())):
                                self.message(
                                    self.bg.generals[i].name
                                    + ": "
                                    + self.bg.generals[i].skills[int(match.group(1))].quote,
                                    self.bg.generals[i].color,
                                )

    def render_msgs(self):
        y = 0
        for (line, color) in self.game_msgs:
            self.renderer.draw_text(line, 0, y * 20, color)
            y += 1

def render_info(self, x, y):
    # Clear the info area at the bottom of the screen
    info_rect = (0, SCREEN_HEIGHT - 20, WINDOW_WIDTH, 20)
    self.renderer.draw_rect(info_rect[0], info_rect[1], info_rect[2], info_rect[3], COLOR_BACKGROUND)

    # Base entity info (if hovering over the battleground)
    if self.bg.is_inside(x, y):
        entity = self.bg.tiles[(x, y)].entity
        if entity:
            if hasattr(entity, "hp"):
                text = f"{entity.name.capitalize()}: HP {entity.hp}/{entity.max_hp}, PW {entity.power}"
                self.renderer.draw_text(text, 250, WINDOW_HEIGHT - 60, entity.original_color)
            else:
                self.renderer.draw_text(entity.name.capitalize(), 250, WINDOW_HEIGHT - 60)
        # Display coordinates
        self.renderer.draw_text(f"{x}/{y}", WINDOW_WIDTH - 50, WINDOW_HEIGHT - 60)

    # Check for hovering over side panels to show skill descriptions
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Left Panel (Side 0)
    if 0 < mouse_x < PANEL_WIDTH * TILE_SIZE:
        i = 0
    # Right Panel (Side 1)
    elif (BG_WIDTH + PANEL_WIDTH) * TILE_SIZE < mouse_x < WINDOW_WIDTH:
        i = 1
    else:
        return

    g = self.bg.generals[i]
    nskills = len(g.skills)
    # Check if mouse_y is in the skill list area (adjust Y offset as needed)
    start_y = 60
    if (start_y) < mouse_y < (start_y + nskills * 30):
        skill_index = (mouse_y - start_y) // 30
        if 0 <= skill_index < len(g.skills):
            skill = g.skills[skill_index]
            self.renderer.draw_text(skill.description, 250, WINDOW_HEIGHT - 40, COLOR_WHITE)


def render_panels(self):
    # Left Panel
    self.render_side_panel(0, 120, 10)
    # Right Panel
    self.render_side_panel(1, 120, (PANEL_WIDTH + BG_WIDTH) * TILE_SIZE + 10)


def render_side_panel(self, i, bar_length, x_offset):
    g = self.bg.generals[i]
    y_offset = 30
    
    # General HP Bar
    self.renderer.draw_text(g.name, x_offset, y_offset, g.color)
    y_offset += 15
    self.render_bar(x_offset, y_offset, bar_length, 15, g.hp, g.max_hp, (0, 150, 0), (150, 0, 0), COLOR_WHITE)
    y_offset += 25

    # Skills and Cooldown Bars
    skill_keys = "QWERTYUIOP"
    for j, skill in enumerate(g.skills):
        self.renderer.draw_text(f"{skill_keys[j]}: {skill.quote}", x_offset, y_offset)
        y_offset += 15
        self.render_bar(x_offset, y_offset, bar_length, 15, skill.cd, skill.max_cd, (0, 100, 200), (50, 50, 50), COLOR_WHITE)
        y_offset += 25

    # Minion Count
    self.renderer.draw_text(f"{g.minions_alive} {g.minion.name}s", x_offset, y_offset, COLOR_WHITE)
    y_offset += 25
    
    # Tactics
    y_offset = self.render_tactics(i, x_offset, y_offset)
    
    # Reserves
    swap_ready = g.swap_cd >= g.swap_max_cd
    swap_keys = "123456789"
    for r_idx, r in enumerate(self.bg.reserves[i]):
        if swap_ready:
            self.renderer.draw_text(f"{swap_keys[r_idx]}: {r.name}", x_offset, y_offset, r.color)
            y_offset += 15
            self.render_bar(x_offset, y_offset, bar_length, 15, r.hp, r.max_hp, (0, 150, 0), (150, 0, 0), COLOR_WHITE)
        else:
            self.renderer.draw_text(f"Swap CD:", x_offset, y_offset, COLOR_WHITE)
            y_offset += 15
            self.render_bar(x_offset, y_offset, bar_length, 15, g.swap_cd, g.swap_max_cd, (0, 100, 200), (50, 50, 50), COLOR_WHITE)
        y_offset += 25


def render_tactics(self, i, x_offset, y_offset):
    tactic_keys = "ZXCVBNM"
    g = self.bg.generals[i]
    for s_idx, quote in enumerate(g.tactic_quotes):
        color = (255, 100, 100) if g.tactics[s_idx] == g.selected_tactic else COLOR_WHITE
        self.renderer.draw_text(f"{tactic_keys[s_idx]}: {quote}", x_offset, y_offset, color)
        y_offset += 20
    return y_offset


def render_msgs(self):
    y = 5 # Small offset from top
    for (line, color) in self.game_msgs:
        self.renderer.draw_text(line, (PANEL_WIDTH * TILE_SIZE) + 10, y, color)
        y += 15



from factions import doto

if __name__ == "__main__":
    if DEBUG:
        sys.stdout.write("DEBUG: Starting main execution\n")
        sys.stdout.write(f"DEBUG: Command line args: {sys.argv}\n")

    bg = Battleground(BG_WIDTH, BG_HEIGHT)
    if DEBUG:
        sys.stdout.write("DEBUG: Battleground created\n")

    bg.generals = [doto.Pock(bg, 0, 3, 21), doto.Pock(bg, 1, 56, 21)]
    if DEBUG:
        sys.stdout.write("DEBUG: Generals created\n")

    for i in [0, 1]:
        bg.reserves[i] = [doto.Rubock(bg, i), doto.Bloodrotter(bg, i), doto.Ox(bg, i)]
    if DEBUG:
        sys.stdout.write("DEBUG: Reserves created\n")

    for i in [0, 1]:
        bg.generals[i].start_scenario()
        for g in bg.reserves[i]:
            g.start_scenario()

    if DEBUG:
        sys.stdout.write("DEBUG: Scenarios started\n")

    if len(sys.argv) == 4:
        battle = BattleWindow(bg, int(sys.argv[1]), sys.argv[2], int(sys.argv[3]))
    elif len(sys.argv) == 2:
        battle = BattleWindow(bg, int(sys.argv[1]))
    else:
        battle = BattleWindow(bg, 0)

    if DEBUG:
        sys.stdout.write("DEBUG: BattleWindow created, about to start loop\n")

    battle.loop()

    if DEBUG:
        sys.stdout.write("DEBUG: Loop ended\n")
