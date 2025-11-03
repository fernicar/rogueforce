from area import SingleTarget
from battleground import Battleground
from general import *
from window import *

import concepts
import pygame

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
    
    if DEBUG:
      sys.stdout.write("DEBUG: About to call super(BattleWindow, self).__init__\n")
    
    super(BattleWindow, self).__init__(battleground, side, host, port, window_id)
    
    if DEBUG:
      sys.stdout.write("DEBUG: BattleWindow.__init__ completed\n")

    self.render_all(0, 0)

  def ai_action(self, turn):
    ai_side = (self.side+1)%2
    return self.bg.generals[ai_side].ai_action(turn)

  def check_input(self, event):
    if event.type == pygame.KEYDOWN:
        key_char = event.unicode.upper()
        if key_char == 'S':
            return "stop\n"
        n = self.keymap_swap.find(key_char)
        if n != -1:
            return "swap{0}\n".format(n)
        n = self.keymap_skills.find(key_char)
        if n != -1:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                self.hover_function = self.bg.generals[self.side].skills[n].get_area_tiles
            else:
                x, y = pygame.mouse.get_pos()
                x = int(x / 10 - BG_OFFSET_X)
                y = int(y / 10 - BG_OFFSET_Y)
                self.hover_function = None
                return "skill{0} ({1},{2})\n".format(n, x, y)
        if event.key == pygame.K_SPACE:
            if self.bg.generals[self.side].tactics.index(self.bg.generals[self.side].selected_tactic) == 0:
                n = self.bg.generals[self.side].tactics.index(self.bg.generals[self.side].previous_tactic)
            else:
                self.bg.generals[self.side].previous_tactic = self.bg.generals[self.side].selected_tactic
                n = 0
        else:
            n = self.keymap_tactics.find(key_char)
        if n != -1:
            return "tactic{0}\n".format(n)
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 3: # Right click
            x, y = pygame.mouse.get_pos()
            x = int(x / 10 - BG_OFFSET_X)
            y = int(y / 10 - BG_OFFSET_Y)
            return "flag ({0},{1})\n".format(x, y)
    return None

  def check_winner(self):
    #TODO: detect draws
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
            self.render_side_panel_clear(i)
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


  def render_info(self, x, y):
    x = int(x)
    y = int(y)
    i = -1
    if -13 < x < -1:
        i = 0
    elif BG_WIDTH + 1 < x < BG_WIDTH + 13:
        i = 1
    
    if i != -1:
        nskills = len(self.bg.generals[i].skills)
        if (5 + nskills * 2) > y > 3:
            skill_index = (y - 5) // 2
            if 0 <= skill_index < len(self.bg.generals[i].skills):
                skill = self.bg.generals[i].skills[skill_index]
                self.draw_text(skill.description, INFO_OFFSET_X * 10, INFO_OFFSET_Y * 10, concepts.UI_TEXT)
                return
    super().render_info(x, y)

  def render_side_panel(self, i, bar_length, bar_offset_x):
    g = self.bg.generals[i]
    
    x_offset = (PANEL_WIDTH + BG_WIDTH) * i * 10

    self.draw_text(g.char, x_offset + (bar_offset_x - 1) * 10, 10, g.color)
    self.render_bar(x_offset + bar_offset_x * 10, 10, bar_length * 10, g.hp, g.max_hp, concepts.STATUS_HEALTH_LOW, concepts.STATUS_HEALTH_MEDIUM, concepts.UI_BACKGROUND)

    line = 3
    for j in range(len(g.skills)):
        skill = g.skills[j]
        self.draw_text(KEYMAP_SKILLS[j], x_offset + (bar_offset_x - 1) * 10, line * 10, concepts.STATUS_SELECTED)
        self.render_bar(x_offset + bar_offset_x * 10, line * 10, bar_length * 10, skill.cd, skill.max_cd, concepts.STATUS_PROGRESS_DARK, concepts.STATUS_PROGRESS_LIGHT, concepts.UI_BACKGROUND)
        line += 2

    self.draw_text(f"{g.minions_alive} {g.minion.name}s", x_offset + 30, (line + 1) * 10, concepts.UI_TEXT)

    line = self.render_tactics(i) + 1
    swap_ready = g.swap_cd >= g.swap_max_cd

    for r in self.bg.reserves[i]:
        self.draw_text(r.char, x_offset + (bar_offset_x - 1) * 10, line * 10, r.color)
        if swap_ready:
            self.render_bar(x_offset + bar_offset_x * 10, line * 10, bar_length * 10, r.hp, r.max_hp, concepts.STATUS_HEALTH_LOW, concepts.STATUS_HEALTH_MEDIUM, concepts.UI_BACKGROUND)
        else:
            self.render_bar(x_offset + bar_offset_x * 10, line * 10, bar_length * 10, g.swap_cd, g.swap_max_cd, concepts.STATUS_PROGRESS_DARK, concepts.STATUS_PROGRESS_LIGHT, concepts.UI_BACKGROUND)
        line += 2

  def render_tactics(self, i):
    bar_offset_x = 3
    x_offset = (PANEL_WIDTH + BG_WIDTH) * i * 10
    line = 7 + len(self.bg.generals[i].skills)*2
    for s in range(len(self.bg.generals[i].tactics)):
      fg_color = concepts.STATUS_HEALTH_LOW if self.bg.generals[i].tactics[s] == self.bg.generals[i].selected_tactic else concepts.STATUS_SELECTED
      self.draw_text(KEYMAP_TACTICS[s] + ": " + self.bg.generals[i].tactic_quotes[s], x_offset + bar_offset_x * 10, line * 10, fg_color)
      line += 2
    return line

from factions import doto
if __name__=="__main__":
  if DEBUG:
    sys.stdout.write("DEBUG: Starting main execution\n")
    sys.stdout.write(f"DEBUG: Command line args: {sys.argv}\n")
    
  bg = Battleground(BG_WIDTH, BG_HEIGHT)
  if DEBUG:
    sys.stdout.write("DEBUG: Battleground created\n")
    
  bg.generals = [doto.Pock(bg, 0, 3, 21), doto.Pock(bg, 1, 56, 21)]
  if DEBUG:
    sys.stdout.write("DEBUG: Generals created\n")
    
  for i in [0,1]:
    bg.reserves[i] = [doto.Rubock(bg, i), doto.Bloodrotter(bg, i), doto.Ox(bg, i)]
  if DEBUG:
    sys.stdout.write("DEBUG: Reserves created\n")
    
  for i in [0,1]:
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
