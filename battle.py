from area import SingleTarget
from battleground import Battleground
from general import *
from window import *

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE, DEBUG,
    PANEL_PIXEL_WIDTH, BATTLEGROUND_OFFSET, MSG_LOG_OFFSET, INFO_BAR_OFFSET, BG_WIDTH, BG_HEIGHT
    
)
from concepts import (
    STATUS_HEALTH_LOW, STATUS_HEALTH_MEDIUM, STATUS_PROGRESS_DARK, 
    STATUS_PROGRESS_LIGHT, UI_TEXT, UI_BACKGROUND,
)

import copy
import re
import sys
import pygame
import random  # Import the random module
from faction_data import ALL_GENERALS  # Import the generals list

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

    def render_panels(self):
        """Draws the left and right UI panels."""
        # Left Panel (Side 0)
        self.render_side_panel(0)
        # Right Panel (Side 1)
        self.render_side_panel(1)

    def render_side_panel(self, i):
        """Renders a single side panel for the player or opponent."""
        g = self.bg.generals[i]
        is_player_side = (i == self.side)
        
        # Determine panel's top-left corner
        if i == 0: # Left panel
            x_offset = 10
        else: # Right panel
            x_offset = BATTLEGROUND_OFFSET[0] + (60 * TILE_SIZE) + 10  # 60 is GRID_WIDTH

        y_offset = 20
        bar_length = PANEL_PIXEL_WIDTH - 20
        
        # General's Name and HP Bar
        self.renderer.draw_text(g.name, x_offset, y_offset, g.color, large=True)
        y_offset += 30
        self.render_bar(x_offset, y_offset, bar_length, 20, g.hp, g.max_hp, STATUS_HEALTH_LOW, STATUS_HEALTH_MEDIUM, UI_TEXT)
        y_offset += 35

        # Skills List
        skill_keys = "QWERTYUIOP"
        for j, skill in enumerate(g.skills):
            key_text = f"{skill_keys[j]}: " if is_player_side else ""
            self.renderer.draw_text(f"{key_text}{skill.quote}", x_offset, y_offset, UI_TEXT)
            y_offset += 20
            self.render_bar(x_offset, y_offset, bar_length, 15, skill.cd, skill.max_cd, STATUS_PROGRESS_DARK, STATUS_PROGRESS_LIGHT, UI_TEXT)
            y_offset += 30

        # Minion Count
        self.renderer.draw_text(f"{g.minions_alive} {g.minion.name}s", x_offset, y_offset, UI_TEXT)
        y_offset += 30

        # Tactics
        y_offset = self.render_tactics(i, x_offset, y_offset, is_player_side)
        y_offset += 15

        # Reserves
        swap_ready = g.swap_cd >= g.swap_max_cd
        swap_keys = "123456789"
        for r_idx, r in enumerate(self.bg.reserves[i]):
            key_text = f"{swap_keys[r_idx]}: " if is_player_side and swap_ready else ""
            self.renderer.draw_text(f"{key_text}{r.name}", x_offset, y_offset, r.color)
            y_offset += 20
            if swap_ready:
                self.render_bar(x_offset, y_offset, bar_length, 15, r.hp, r.max_hp, STATUS_HEALTH_LOW, STATUS_HEALTH_MEDIUM, UI_TEXT)
            else:
                self.render_bar(x_offset, y_offset, bar_length, 15, g.swap_cd, g.swap_max_cd, STATUS_PROGRESS_DARK, STATUS_PROGRESS_LIGHT, UI_TEXT)
            y_offset += 30

    def render_tactics(self, i, x_offset, y_offset, is_player_side):
        """Renders the tactics list for a general."""
        tactic_keys = "ZXCVBNM"
        g = self.bg.generals[i]
        self.renderer.draw_text("Tactics:", x_offset, y_offset, UI_TEXT)
        y_offset += 25
        for s_idx, quote in enumerate(g.tactic_quotes):
            color = (255, 100, 100) if g.tactics[s_idx] == g.selected_tactic else UI_TEXT
            key_text = f"{tactic_keys[s_idx]}: " if is_player_side else ""
            self.renderer.draw_text(f"{key_text}{quote}", x_offset + 10, y_offset, color)
            y_offset += 20
        return y_offset

    def render_info(self, grid_x, grid_y):
        """Renders the info bar at the bottom and skill descriptions."""
        info_x, info_y = INFO_BAR_OFFSET
        
        # Clear the info area
        self.renderer.draw_rect(info_x, info_y - 5, 60 * TILE_SIZE, 60, UI_BACKGROUND)  # 60 is GRID_WIDTH

        # Hovered tile entity info
        if self.bg.is_inside(grid_x, grid_y):
            entity = self.bg.tiles[(grid_x, grid_y)].entity
            if entity:
                if hasattr(entity, "hp"):
                    text = f"{entity.name.capitalize()}: HP {entity.hp}/{entity.max_hp}, PW {entity.power}"
                    self.renderer.draw_text(text, info_x, info_y, entity.original_color)
                else:
                    self.renderer.draw_text(entity.name.capitalize(), info_x, info_y)
            
            # Display coordinates
            self.renderer.draw_text(f"{grid_x}/{grid_y}", info_x + (60 * TILE_SIZE) - 60, info_y)  # 60 is GRID_WIDTH

        # Skill description from hovering over side panels
        mouse_x, mouse_y = pygame.mouse.get_pos()
        panel_index = -1
        if 0 < mouse_x < PANEL_PIXEL_WIDTH:
            panel_index = 0
        elif BATTLEGROUND_OFFSET[0] + (60 * TILE_SIZE) < mouse_x < self.renderer.screen.get_width():  # 60 is GRID_WIDTH
            panel_index = 1
        
        if panel_index != -1:
            g = self.bg.generals[panel_index]
            # Approximate Y check for skills area
            skill_start_y = 65
            skill_area_height = len(g.skills) * 50
            if skill_start_y < mouse_y < skill_start_y + skill_area_height:
                skill_index = (mouse_y - skill_start_y) // 50
                if 0 <= skill_index < len(g.skills):
                    skill = g.skills[skill_index]
                    self.renderer.draw_text(skill.description, info_x, info_y + 20, UI_TEXT)

    def render_msgs(self):
        """Renders the message log."""
        msg_x, msg_y = MSG_LOG_OFFSET
        
        # Clear the message area
        self.renderer.draw_rect(msg_x, 0, 60 * TILE_SIZE, BATTLEGROUND_OFFSET[1] - 5, UI_BACKGROUND)  # 60 is GRID_WIDTH

        y = msg_y
        for (line, color) in self.game_msgs:
            self.renderer.draw_text(line, msg_x, y, color)
            y += 15 # Line height


if __name__ == "__main__":
    if DEBUG:
        sys.stdout.write("DEBUG: Starting main execution\n")
        sys.stdout.write(f"DEBUG: Command line args: {sys.argv}\n")

    bg = Battleground(BG_WIDTH, BG_HEIGHT)
    if DEBUG:
        sys.stdout.write("DEBUG: Battleground created\n")
    
    # --- Random General and Reserve Selection Logic ---
    available_generals = list(ALL_GENERALS)
    random.shuffle(available_generals)
    
    if len(available_generals) < 2:
        raise ValueError("Not enough unique generals to start a battle!")

    # Select main generals
    gen0_class = available_generals.pop()
    gen1_class = available_generals.pop()
    
    gen0 = gen0_class(bg, 0, 3, 21)
    gen1 = gen1_class(bg, 1, 56, 21)
    bg.generals = [gen0, gen1]
    
    print(f"BATTLE: {gen0.name} (Side 0) vs {gen1.name} (Side 1)")

    # Select reserves
    num_reserves = min(len(available_generals) // 2, 3) # Up to 3 reserves per side
    
    bg.reserves = [[], []]
    for i in range(num_reserves):
        if available_generals:
            reserve0_class = available_generals.pop()
            bg.reserves[0].append(reserve0_class(bg, 0))
        if available_generals:
            reserve1_class = available_generals.pop()
            bg.reserves[1].append(reserve1_class(bg, 1))

    if DEBUG:
        sys.stdout.write(f"DEBUG: Side 0 General: {gen0.name}, Reserves: {[g.name for g in bg.reserves[0]]}\n")
        sys.stdout.write(f"DEBUG: Side 1 General: {gen1.name}, Reserves: {[g.name for g in bg.reserves[1]]}\n")

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
