from area import SingleTarget
from battleground import Battleground
from general import *
from window import *

from config import COLOR_WHITE, COLOR_BACKGROUND

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
        # Use key codes for S, not characters
        if keys[pygame.K_s]:
            return "stop\n"

        # mouse[2] is the right mouse button in Pygame
        if mouse[2]:
            return "flag ({0},{1})\n".format(x, y)

        # Handle number keys for swapping reserves
        for i, key_char in enumerate(self.keymap_swap):
            if keys[ord(key_char)]:
                return "swap{0}\n".format(i)

        # Handle letter keys for skills
        for i, key_char in enumerate(self.keymap_skills):
            if keys[ord(key_char)]:
                # Check for SHIFT key modifier to preview skill area
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.hover_function = self.bg.generals[self.side].skills[i].get_area_tiles
                else:  # No shift, use the skill
                    self.hover_function = None
                    return "skill{0} ({1},{2})\n".format(i, x, y)

        # Handle spacebar for toggling tactics
        if keys[pygame.K_SPACE]:
            if self.bg.generals[self.side].tactics.index(self.bg.generals[self.side].selected_tactic) == 0:
                n = self.bg.generals[self.side].tactics.index(self.bg.generals[self.side].previous_tactic)
            else:
                self.bg.generals[self.side].previous_tactic = self.bg.generals[self.side].selected_tactic
                n = 0
            return "tactic{0}\n".format(n)

        # Handle letter keys for selecting tactics
        for i, key_char in enumerate(self.keymap_tactics):
            if keys[ord(key_char)]:
                if self.bg.generals[self.side].tactics.index(self.bg.generals[self.side].selected_tactic) != 0:
                    self.bg.generals[self.side].previous_tactic = self.bg.generals[self.side].selected_tactic
                return "tactic{0}\n".format(i)

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
                        self.render_side_panel(i, 0, 0)
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
        # Base entity info (if hovering over the battleground)
        if self.bg.is_inside(x, y):
            entity = self.bg.tiles[(x, y)].entity
            if entity:
                if hasattr(entity, "hp"):
                    text = entity.name.capitalize() + ": HP %02d/%02d, PW %d" % (
                        entity.hp,
                        entity.max_hp,
                        entity.power,
                    )
                    self.renderer.draw_text(text, 0, SCREEN_HEIGHT - 20, entity.original_color)
                else:
                    self.renderer.draw_text(entity.name.capitalize(), 0, SCREEN_HEIGHT - 20)

        # Check for hovering over side panels to show skill descriptions
        # Note: These coordinates are rough estimates and might need tweaking.
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Left Panel (Side 0)
        if 0 < mouse_x < PANEL_WIDTH * 16:
            i = 0
            g = self.bg.generals[i]
            nskills = len(g.skills)
            # Check if mouse_y is in the skill list area
            if (PANEL_OFFSET_Y + 3 * 20) < mouse_y < (PANEL_OFFSET_Y + (3 + nskills * 2) * 20):
                skill_index = (mouse_y - (PANEL_OFFSET_Y + 3 * 20)) // 40
                if 0 <= skill_index < len(g.skills):
                    skill = g.skills[skill_index]
                    self.renderer.draw_text(skill.description, 0, SCREEN_HEIGHT - 20, COLOR_WHITE)
                    return  # Prevent entity info from overwriting skill info

        # Right Panel (Side 1)
        if (BG_WIDTH + PANEL_WIDTH) * 16 < mouse_x < SCREEN_WIDTH * 16:
            i = 1
            g = self.bg.generals[i]
            nskills = len(g.skills)
            if (PANEL_OFFSET_Y + 3 * 20) < mouse_y < (PANEL_OFFSET_Y + (3 + nskills * 2) * 20):
                skill_index = (mouse_y - (PANEL_OFFSET_Y + 3 * 20)) // 40
                if 0 <= skill_index < len(g.skills):
                    skill = g.skills[skill_index]
                    self.renderer.draw_text(skill.description, 0, SCREEN_HEIGHT - 20, COLOR_WHITE)
                    return

    def render_side_panel(self, i, bar_length, bar_offset_x):
        g = self.bg.generals[i]
        x_offset = i * (BG_WIDTH + PANEL_WIDTH) * 16

        # General Name and HP Bar
        self.renderer.draw_text(g.name, x_offset, 0, g.original_color)
        self.render_bar(
            x_offset, 20, 150, 15, g.hp, g.max_hp, (0, 255, 0), (255, 0, 0), COLOR_WHITE
        )

        line = 3
        # Skills and Cooldown Bars
        for j in range(0, len(g.skills)):
            skill = g.skills[j]
            text = f"{self.keymap_skills[j]}: {skill.quote}"
            self.renderer.draw_text(text, x_offset, line * 20, COLOR_WHITE)
            self.render_bar(
                x_offset,
                (line + 1) * 20,
                150,
                15,
                skill.cd,
                skill.max_cd,
                (135, 206, 235),
                (0, 0, 128),
                COLOR_WHITE,
            )
            line += 2

        # Minion Count
        text = f"{g.minions_alive} {g.minion.name}s"
        self.renderer.draw_text(text, x_offset, line * 20)
        line += 1

        # Tactics
        line = self.render_tactics(i, x_offset, line) + 1

        # Reserves and Swap Cooldown
        swap_ready = g.swap_cd >= g.swap_max_cd
        for j, r in enumerate(self.bg.reserves[i]):
            key = self.keymap_swap[j]
            if swap_ready:
                text = f"{key}: {r.name}"
                self.renderer.draw_text(text, x_offset, line * 20, r.original_color)
                self.render_bar(
                    x_offset,
                    (line + 1) * 20,
                    150,
                    15,
                    r.hp,
                    r.max_hp,
                    (0, 255, 0),
                    (255, 0, 0),
                    COLOR_WHITE,
                )
            else:
                text = f"Swap CD:"
                self.renderer.draw_text(text, x_offset, line * 20)
                self.render_bar(
                    x_offset,
                    (line + 1) * 20,
                    150,
                    15,
                    g.swap_cd,
                    g.swap_max_cd,
                    (135, 206, 235),
                    (0, 0, 128),
                    COLOR_WHITE,
                )
            line += 2

    def render_tactics(self, i, x_offset, line):
        COLOR_RED = (255, 0, 0)
        g = self.bg.generals[i]
        tactics_count = min(len(g.tactics), len(self.keymap_tactics))
        for s in range(tactics_count):
            text = f"{self.keymap_tactics[s]}: {g.tactic_quotes[s]}"
            # Highlight the selected tactic in red, like the original
            color = COLOR_RED if g.tactics[s] == g.selected_tactic else COLOR_WHITE
            self.renderer.draw_text(text, x_offset, line * 20, color)
            line += 1
        return line


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
