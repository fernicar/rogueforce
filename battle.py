from area import SingleTarget
from battleground import Battleground
from general import *
from window import *

from config import COLOR_WHITE, COLOR_BLACK, COLOR_BACKGROUND

import copy
import re
import sys
import pygame

from config import DEBUG

KEYMAP_SKILLS = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t, pygame.K_y, pygame.K_u, pygame.K_i, pygame.K_o, pygame.K_p]
KEYMAP_SWAP = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
KEYMAP_TACTICS = [pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n, pygame.K_m]

FLAG_PATTERN = re.compile(r"flag \((-?\d+),(-?\d+)\)")
SKILL_PATTERN = re.compile(r"skill(\d) \((-?\d+),(-?\d+)\)")

class BattleWindow(Window):
  def __init__(self, battleground, side, host = None, port = None, window_id = 1):
    if DEBUG:
      sys.stdout.write("DEBUG: BattleWindow.__init__ started\n")
    
    for i in [0,1]:
      battleground.generals[i].start_battle()
      battleground.generals[i].formation.place_minions()
      for g in battleground.reserves[i]:
        g.start_battle()

    self.keymap_skills = KEYMAP_SKILLS[0:len(battleground.generals[side].skills)]
    self.keymap_swap = KEYMAP_SWAP[0:len(battleground.reserves[side])]
    self.keymap_tactics = KEYMAP_TACTICS[0:len(battleground.generals[side].tactics)]
    
    super(BattleWindow, self).__init__(battleground, side, host, port, window_id)
    
    if DEBUG:
      sys.stdout.write("DEBUG: BattleWindow.__init__ completed\n")

  def ai_action(self, turn):
    ai_side = (self.side+1)%2
    return self.bg.generals[ai_side].ai_action(turn)

  def check_input(self):
      keys = pygame.key.get_pressed()
      mouse = pygame.mouse.get_pressed()
      x, y = pygame.mouse.get_pos()

      if keys[pygame.K_s]:
          return "stop\n"
      if mouse[2]:  # Right mouse button
          return "flag ({0},{1})\n".format(x, y)

      for i, key in enumerate(self.keymap_swap):
          if keys[key]:
              return "swap{0}\n".format(i)

      for i, key in enumerate(self.keymap_skills):
          if keys[key]:
              if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                  self.hover_function = self.bg.generals[self.side].skills[i].get_area_tiles
              else:
                  self.hover_function = None
                  return "skill{0} ({1},{2})\n".format(i, x, y)

      if keys[pygame.K_SPACE]:
          if self.bg.generals[self.side].tactics.index(self.bg.generals[self.side].selected_tactic) == 0:
              n = self.bg.generals[self.side].tactics.index(self.bg.generals[self.side].previous_tactic)
          else:
              self.bg.generals[self.side].previous_tactic = self.bg.generals[self.side].selected_tactic
              n = 0
          return "tactic{0}\n".format(n)

      for i, key in enumerate(self.keymap_tactics):
          if keys[key]:
              if self.bg.generals[self.side].tactics.index(self.bg.generals[self.side].selected_tactic) != 0:
                  self.bg.generals[self.side].previous_tactic = self.bg.generals[self.side].selected_tactic
              return "tactic{0}\n".format(i)

      return None

  def check_winner(self):
    for i in [0,1]:
      if not self.bg.generals[i].alive:
        self.message(self.bg.generals[i].name + ": " + self.bg.generals[i].death_quote, self.bg.generals[i].original_color)
        self.message(self.bg.generals[i].name + " is dead!", self.bg.generals[i].original_color)
        self.game_over = True
        return self.bg.generals[(i+1)%2]
    return None

  def clean_all(self):
    for e in copy.copy(self.bg.effects):
      if not e.alive:
        self.bg.effects.remove(e)
    for m in copy.copy(self.bg.minions):
      if not m.alive:
        self.bg.minions.remove(m)

  def process_messages(self, turn):
    for i in [0,1]:
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
            pass # Re-rendering the side panel will be handled in the main loop
        else:
          match = FLAG_PATTERN.match(m)
          if match:
            self.bg.generals[i].place_flag(int(match.group(1)), int(match.group(2)))
          else:
            match = SKILL_PATTERN.match(m)
            if match:
              if self.bg.generals[i].use_skill(*map(int, match.groups())):
                self.message(self.bg.generals[i].name + ": " + self.bg.generals[i].skills[int(match.group(1))].quote,
                             self.bg.generals[i].color)

  def render_info(self):
    x, y = pygame.mouse.get_pos()
    grid_x, grid_y = self.get_grid_coords(x, y)

    if self.bg.is_inside(grid_x, grid_y):
      entity = self.bg.tiles[(grid_x, grid_y)].entity
      if entity:
        if(hasattr(entity, 'hp')):
          text = entity.name.capitalize() + ": HP %02d/%02d, PW %d" % (entity.hp, entity.max_hp, entity.power)
          self.renderer.draw_text(text, INFO_OFFSET_X, INFO_OFFSET_Y, entity.original_color)
        else:
          self.renderer.draw_text(entity.name.capitalize(), INFO_OFFSET_X, INFO_OFFSET_Y)

  def render_panels(self):
      self.render_side_panel(self.side, 0, 0)
      self.render_side_panel((self.side + 1) % 2, 0, SCREEN_WIDTH - PANEL_WIDTH * 16)

  def render_side_panel(self, i, bar_length, bar_offset_x):
    g = self.bg.generals[i]
    
    x_offset = i * (BG_WIDTH + PANEL_WIDTH)
    self.renderer.draw_text(g.name, x_offset, PANEL_OFFSET_Y)

    line = 3
    for j in range(0, len(g.skills)):
      skill = g.skills[j]
      text = f"{pygame.key.name(self.keymap_skills[j]).upper()}: {skill.name}"
      self.renderer.draw_text(text, x_offset, PANEL_OFFSET_Y + line * 15)
      line += 1

    text = f"{g.minions_alive} {g.minion.name}s"
    self.renderer.draw_text(text, x_offset, PANEL_OFFSET_Y + line * 15)
    line += 1

    line = self.render_tactics(i, x_offset, line) + 1

    swap_ready = g.swap_cd >= g.swap_max_cd
    for r_idx, r in enumerate(self.bg.reserves[i]):
      if swap_ready:
        text = f"{pygame.key.name(self.keymap_swap[r_idx])}: {r.name}: HP {r.hp}/{r.max_hp}"
        self.renderer.draw_text(text, x_offset, PANEL_OFFSET_Y + line * 15)
      else:
        text = f"Swap CD: {g.swap_cd}/{g.swap_max_cd}"
        self.renderer.draw_text(text, x_offset, PANEL_OFFSET_Y + line * 15)
      line += 1

  def render_tactics(self, i, x_offset, line):
    for s in range(0, len(self.bg.generals[i].tactics)):
      text = f"{pygame.key.name(self.keymap_tactics[s]).upper()}: {self.bg.generals[i].tactic_quotes[s]}"
      color = (255, 0, 0) if self.bg.generals[i].tactics[s] == self.bg.generals[i].selected_tactic else COLOR_WHITE
      self.renderer.draw_text(text, x_offset, PANEL_OFFSET_Y + line * 15, color)
      line += 1
    return line

from factions import doto
if __name__=="__main__":
  if DEBUG:
    sys.stdout.write("DEBUG: Starting main execution\n")
    sys.stdout.write(f"DEBUG: Command line args: {sys.argv}\n")
    
  bg = Battleground(BG_WIDTH, BG_HEIGHT)

  bg.generals = [doto.Pock(bg, 0, 3, 21), doto.Pock(bg, 1, 56, 21)]

  for i in [0,1]:
    bg.reserves[i] = [doto.Rubock(bg, i), doto.Bloodrotter(bg, i), doto.Ox(bg, i)]
    
  for i in [0,1]:
    bg.generals[i].start_scenario()
    for g in bg.reserves[i]:
      g.start_scenario()

  if len(sys.argv) == 4: 
    battle = BattleWindow(bg, int(sys.argv[1]), sys.argv[2], int(sys.argv[3]))
  elif len(sys.argv) == 2:
    battle = BattleWindow(bg, int(sys.argv[1]))
  else:
    battle = BattleWindow(bg, 0)
    
  battle.loop()
