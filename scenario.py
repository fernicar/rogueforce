from battle import BattleWindow
from battleground import Battleground
from entity import *
from general import *
from faction import *
from window import *
import pygame
from typing import cast, List, TYPE_CHECKING

if TYPE_CHECKING:
    from general import General
    from faction import Faction

from config import WINDOW_WIDTH, PANEL_WIDTH, PANEL_OFFSET_Y, BG_WIDTH, BG_HEIGHT
from concepts import UI_TEXT as COLOR_WHITE, UI_BACKGROUND as COLOR_BLACK, UI_BACKGROUND as COLOR_BACKGROUND

import re

KEYMAP_GENERALS = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t, pygame.K_y, pygame.K_u, pygame.K_i, pygame.K_o, pygame.K_p]
MOVEGEN_PATTERN = re.compile(r"move_gen(\d) \((-?\d+),(-?\d+)\)")

class Scenario(Window):
    def __init__(self, battleground: Battleground, side: int, factions: List['Faction'], host = None, port = None, window_id: int = 0) -> None:
        super(Scenario, self).__init__(battleground, side, host, port, window_id)
        self.factions = factions
        self.requisition = [999, 300]
        self.max_requisition = 999
        self.keymap_generals = KEYMAP_GENERALS[0:len(factions[side].generals)]
        self.selected_general = None
        for f in factions:
            for g in f.generals:
                g.start_scenario()
 
        #TODO: remove, just for testing purposes
        self.i = 0
        self.deploy_general(factions[1].generals[2])
        self.i += 1
        self.deploy_general(factions[1].generals[1])
        self.i += 1
        self.deploy_general(factions[1].generals[0])

    def apply_requisition(self, general: 'General') -> None:
        if general.deployed: return
        req = general.requisition or 0
        cost = general.cost or 0
        side = general.side
        if side < 0 or side >= len(self.requisition): return
        current_requisition = self.requisition[side] or 0
        if req + current_requisition >= cost:
            if self.deploy_general(general):
                self.requisition[side] = current_requisition - (cost - req)
                general.requisition = cost
            else:
                self.requisition[side] = current_requisition - (cost - req - 1)
                general.requisition = cost - 1
        else:
            general.requisition = req + current_requisition
            self.requisition[side] = 0

    def check_input(self, keys, mouse, grid_x, grid_y):
        for i, key in enumerate(self.keymap_generals):
            if keys[key]:
                g = self.factions[self.side].generals[i]
                if g.deployed:
                    self.selected_general = g
                    if not self.bg.is_inside(grid_x, grid_y):
                            return
                    return "move_gen{0} ({1},{2})\n".format(i, grid_x, grid_y)
                else:
                    self.selected_general = None
                    return "apply_req{0}\n".format(i)
        return None

    def deploy_general(self, general: 'General') -> bool:
        if general.teleport(1 if general.side == 0 else 56+self.i, 21):
            general.target = (4,21) if general.side == 0 else (52,21)
            general.home = general.target
            general.deployed = True
            general.alive = True
            self.bg.generals.append(general)
            name = general.name or "Unknown General"
            self.message(name + " has been deployed on the " + ("left" if general.side == 0 else "right")
                    + " side.", general.color)
            return True
        return False

    def get_next_tile(self, general: 'General'):
        if not general.target:
            return None
        for t in [(general.x+i, general.y+j) for i in range(-1,2) for j in range(-1,2)]:
            if self.bg.tiles[t].entity == self.bg.tiles[general.target].entity:
                return t
        starting_tiles = general.get_passable_neighbours()
        checked = [(general.x, general.y)]
        for starting in starting_tiles:
            tiles = [starting]
            while tiles:
                (x, y) = tiles.pop()
                checked.append((x, y))
                for t in [(x+i, y+j) for i in range(-1,2) for j in range(-1,2)]:
                    if self.bg.tiles[t].entity == self.bg.tiles[general.target].entity:
                        return starting
                    if self.bg.tiles[t].passable and t not in checked:
                        tiles.append(t)
        return None

    def increment_requisition(self):
        for f in self.bg.fortresses:
            if f.side != NEUTRAL_SIDE:
                self.requisition[f.side] += f.requisition_production
        for i in [0,1]:
            if self.requisition[i] > self.max_requisition:
                self.requisition[i] = self.max_requisition

    def process_messages(self, turn: int) -> None:
        for i in [0,1]:
            if turn in self.messages[i]:
                if self.messages[i][turn].startswith("apply_req"):
                    self.apply_requisition(self.factions[i].generals[int(self.messages[i][turn][9])])
                else:
                    match = MOVEGEN_PATTERN.match(self.messages[i][turn])
                    if match:
                        g = self.factions[i].generals[int(match.group(1))]
                        (x, y) = (int(match.group(2)), int(match.group(3)))
                        if not self.bg.is_inside(x, y):
                            return
                        target = self.bg.tiles[(x, y)].entity
                        home = self.bg.tiles[(g.x, g.y)].entity
                        if (target in self.bg.fortresses and home in self.bg.fortresses and g in cast(Fortress, home).guests):
                            for (f, tile) in cast(Fortress, home).connected_fortresses:
                                if f == target:
                                    (g.x, g.y) = tile
                                    g.home = (cast(Fortress, home).x, cast(Fortress, home).y)
                                    g.target = (cast(Fortress, target).x, cast(Fortress, target).y)
                                    cast(Fortress, home).unhost(g)
                                    return

    def render_panels(self):
        self.render_side_panel(self.side, 0, 0)
        self.render_side_panel((self.side + 1) % 2, 0, WINDOW_WIDTH - PANEL_WIDTH * 16)

    def render_side_panel(self, i: int, bar_length: int, bar_offset_x: int) -> None:
        x_offset = i * (BG_WIDTH + PANEL_WIDTH)
        self.renderer.draw_text("Requisition", x_offset, PANEL_OFFSET_Y)

        line = 4
        for j in range(0, len(self.factions[i].generals)):
            g = self.factions[i].generals[j]
            fg_color = g.color if g == self.selected_general else COLOR_WHITE
            name = g.name or "Unknown"
            if i == self.side:
                text = f"{pygame.key.name(self.keymap_generals[j]).upper()}: {name}"
            else:
                text = name
            self.renderer.draw_text(text, x_offset, PANEL_OFFSET_Y + line * 15, fg_color)
            if not g.deployed:
                cost = g.cost or 0
                self.renderer.draw_text(f"Cost: {cost}", x_offset, PANEL_OFFSET_Y + (line + 1) * 15)
            else:
                hp = g.hp or 0
                max_hp = g.max_hp or 1
                self.renderer.draw_text(f"HP: {hp}/{max_hp}", x_offset, PANEL_OFFSET_Y + (line + 1) * 15)
            line += 2

    def start_battle(self, generals: List['General']) -> None:
        if generals[0].side != 0:
            (generals[0], generals[1]) = (generals[1], generals[0])
        return self.start_battle_thread(generals)

    def start_battle_thread(self, generals):
        battleground = Battleground(BG_WIDTH, BG_HEIGHT)
        battleground.generals = generals
        scenario_pos = []
        for g in generals:
            scenario_pos.append((g.x, g.y))
            g.change_battleground(battleground, 3 if g.side == 0 else 56, g.y)
        battle = BattleWindow(battleground, 0)
        winner = battle.loop()
        for i in [0,1]:
            generals[i].change_battleground(self.bg, *(scenario_pos[i]))
            if not generals[i].alive:
                generals[i].die()
                generals[i].start_scenario()
                winner_name = generals[(i+1)%2].name or "Unknown"
                loser_name = generals[i].name or "Unknown"
                self.message(winner_name + " defeated " + loser_name + " on a battle.", generals[(i+1)%2].color)
     
    def update_all(self):
        self.increment_requisition()
        for g in self.bg.generals:
            if not g.deployed:
                continue
            enemy = g.enemy_reachable(diagonals=True)
            if enemy is not None and enemy.side != NEUTRAL_SIDE:
                if enemy in self.bg.fortresses:
                    fortress_enemy = cast(Fortress, enemy)
                    if fortress_enemy.guests:
                        e = fortress_enemy.guests[-1]
                        self.start_battle([g, cast('General', e)])
                        if not e.alive:
                            fortress_enemy.unhost(e)
                else:
                    self.start_battle([g, cast('General', enemy)])
            else:
                t = self.get_next_tile(g)
                if t:
                    entity = self.bg.tiles[t].entity
                    if entity in self.bg.fortresses:
                        cast(Fortress, entity).host(g)
                    elif g.can_move(t[0]-g.x, t[1]-g.y):
                        g.move(t[0]-g.x, t[1]-g.y)
                    else:
                        g.target = g.home


if __name__=="__main__":
    battleground = Battleground(BG_WIDTH, BG_HEIGHT, "map.txt")
    factions = []
    factions.append(Mechanics(battleground, 0))
    factions.append(Oracles(battleground, 1))
    scenario = Scenario(battleground, 0, factions) 
    scenario.loop()
