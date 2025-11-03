import entity

import concepts

# Import libtcod compatibility layer
try:
    import libtcod_compat as libtcod
    LIBTCOD_AVAILABLE = True
except ImportError:
    LIBTCOD_AVAILABLE = False

# Import color utilities for compatibility
try:
    from color_utils import Color
    COLOR_UTILS_AVAILABLE = True
except ImportError:
    COLOR_UTILS_AVAILABLE = False

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
          self.tiles[(x,y)].color = concepts.UI_TEXT  # White walls for visibility
        else: # Floor
          self.tiles[(x,y)] = Tile(x, y)
          self.tiles[(x,y)].char = '.'  # Keep dot but make it brighter
          self.tiles[(x,y)].color = (200, 200, 200)  # Light grey for better visibility

  def draw(self, con):
    from config import DEBUG
    tile_count = 0
    for pos in self.tiles:
      tile = self.tiles[pos]
      if DEBUG:
        if tile_count < 5:  # Only debug first few tiles to avoid spam
          sys.stdout.write(f"DEBUG: Drawing tile at ({tile.x},{tile.y}) char='{tile.char}' color={tile.color}\n")
      tile.draw(con)
      tile_count += 1
    if DEBUG:
      sys.stdout.write(f"DEBUG: Total tiles drawn: {tile_count}\n")

  def hover_tiles(self, l, color=concepts.UI_HOVER_DEFAULT):
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
      self.fortresses.append(entity.Fortress(self, entity.NEUTRAL_SIDE, f[0], f[1], [self.tiles[f].char]*4, [concepts.ENTITY_DEFAULT]*4))

  def unhover_tiles(self):
    for t in self.hovered:
      t.unhover()

class Tile(object):
  def __init__(self, x, y, char='.', passable=True):
    self.passable = passable
    self.char = char
    self.color = concepts.UI_TILE_NEUTRAL
    self.bg_original_color = concepts.UI_BACKGROUND
    self.bg_color = concepts.UI_BACKGROUND
    self.entity = None
    self.effects = []
    self.x = x
    self.y = y

  def get_char(self, x, y):
    return self.char

  def is_passable(self, passenger):
    return self.passable and (self.entity == None or self.entity.is_ally(passenger))

  def draw(self, con):
    if len(self.effects) > 0 and self.effects[-1].char:
      drawable = self.effects[-1]
    elif self.entity:
      drawable = self.entity
    else:
      drawable = self
    libtcod.console_put_char_ex(con, self.x, self.y, drawable.get_char(drawable.x-self.x,drawable.y-self.y), drawable.color, self.bg_color)
  
  def hover(self, color=concepts.UI_HOVER_DEFAULT):
    self.bg_color = color

  def unhover(self):
    self.bg_color = self.bg_original_color
