import entity

from config import UI_BACKGROUND, UI_HOVER_DEFAULT, UI_TEXT, UI_TILE_NEUTRAL
import sys

import os

class Battleground(object):
  def __init__(self, width, height, tilefile=None):
    self.height = height
    self.width = width
    self.effects = []
    self.minions = []
    self.generals = []
    self.reserves = [[], []]
    self.fortresses = []
    self.tiles = {}
    if tilefile:
      self.load_tiles(tilefile)
    else:
      self.default_tiles()
    self.tiles[(-1, -1)] = Tile(-1, -1)
    self.hovered = []
    self.connect_fortresses()

  def connect_fortresses(self):
    for f in self.fortresses:
      f.get_connections()

  def default_tiles(self):
    for x in range(self.width):
      for y in range(self.height):
        if x in [0, self.width-1] or y in [0, self.height-1]: # Walls
          self.tiles[(x,y)] = Tile(x, y, "#", False)
          self.tiles[(x,y)].color = UI_TEXT  # White walls for visibility
        else: # Floor
          self.tiles[(x,y)] = Tile(x, y)
          self.tiles[(x,y)].char = '.'  # Keep dot but make it brighter
          self.tiles[(x,y)].color = (200, 200, 200)  # Light grey for better visibility

  def hover_tiles(self, l, color=UI_HOVER_DEFAULT):
    self.unhover_tiles()
    for t in l:
      t.hover(color)
    self.hovered = l

  def is_inside(self, x, y):
    return 0 <= x < self.width and 0 <= y < self.height

  def load_tiles(self, tilefile):
    forts = []
    passables = ['.']
    f = open(os.path.join("data", tilefile), 'r')
    for y in range(self.height):
      x = 0
      for c in f.readline():
        self.tiles[(x,y)] = Tile(x, y, c, c in passables)
        if c == ':':
          forts.append((x,y))
        x += 1
    f.close()
    for f in forts:
      self.fortresses.append(entity.Fortress(self, entity.NEUTRAL_SIDE, f[0], f[1], [self.tiles[f].char]*4, [UI_BACKGROUND]*4))

  def unhover_tiles(self):
    for t in self.hovered:
      t.unhover()

class Tile(object):
  def __init__(self, x, y, char='.', passable=True):
    self.passable = passable
    self.char = char
    self.color = UI_TILE_NEUTRAL
    self.bg_original_color = UI_BACKGROUND
    self.bg_color = UI_BACKGROUND
    self.entity = None
    self.effects = []
    self.x = x
    self.y = y

  def get_char(self, x, y):
    return self.char

  def is_passable(self, passenger):
    return self.passable and (self.entity == None or self.entity.is_ally(passenger))

  def hover(self, color=UI_HOVER_DEFAULT):
    self.bg_color = color

  def unhover(self):
    self.bg_color = self.bg_original_color
