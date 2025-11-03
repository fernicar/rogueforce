import entity
import pygame
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
          self.tiles[(x,y)] = Tile(x, y, False, sprite_name='wall')
        else: # Floor
          self.tiles[(x,y)] = Tile(x, y, True, sprite_name='floor')

  def draw(self, screen, font):
    from window import BG_OFFSET_X, BG_OFFSET_Y
    for y in range(self.height):
        for x in range(self.width):
            tile = self.tiles[(x, y)]
            tile.draw(screen, (x + BG_OFFSET_X) * 10, (y + BG_OFFSET_Y) * 10, font)

  def hover_tiles(self, l, color=pygame.Color('yellow')):
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
    y = 0
    for line in f:
        x = 0
        for c in line:
            if c in passables:
                self.tiles[(x,y)] = Tile(x, y, True, sprite_name='floor')
            else:
                self.tiles[(x,y)] = Tile(x, y, False, sprite_name='wall')
            if c == ':':
                forts.append((x,y))
            x += 1
        y += 1
    f.close()
    for f in forts:
      self.fortresses.append(entity.Fortress(self, entity.NEUTRAL_SIDE, f[0], f[1]))

  def unhover_tiles(self):
    for t in self.hovered:
      t.unhover()

class Tile(object):
  def __init__(self, x, y, passable=True, sprite_name='floor'):
    self.passable = passable
    self.sprite_name = sprite_name
    self.bg_original_color = pygame.Color('black')
    self.bg_color = self.bg_original_color
    self.entity = None
    self.effects = []
    self.x = x
    self.y = y
    self.hovered = False
    self.animator = None

  def is_passable(self, passenger):
    return self.passable and (self.entity == None or self.entity.is_ally(passenger))

  def draw(self, screen, px, py, font):
    from asset_manager import AssetManager

    # Draw background color
    pygame.draw.rect(screen, self.bg_color, (px, py, 10, 10))

    # Draw tile sprite
    if not self.animator:
        self.animator = AssetManager.get_animator(self.sprite_name)

    if self.animator:
        sprite = self.animator.get_current_sprite()
        if sprite:
            screen.blit(sprite, (px, py))

    # Draw entity sprite on top
    if self.entity and self.entity.animator:
        sprite = self.entity.animator.get_current_sprite()
        if sprite:
            screen.blit(sprite, (px, py))

  def hover(self, color=pygame.Color('yellow')):
    self.bg_color = color
    self.hovered = True

  def unhover(self):
    self.bg_color = self.bg_original_color
    self.hovered = False
