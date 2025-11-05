from area import SingleTarget
from battleground import Battleground
from rendering.renderer import Renderer
from assets.asset_loader import asset_loader
import pygame
from config import COLOR_WHITE, COLOR_BACKGROUND, COLOR_BLACK, TILE_SIZE

import socket
import sys
import textwrap
import time

from config import DEBUG

BG_WIDTH = 60
BG_HEIGHT = 43
PANEL_WIDTH = 16
PANEL_HEIGHT = BG_HEIGHT
INFO_WIDTH = BG_WIDTH
INFO_HEIGHT = 1
MSG_WIDTH = BG_WIDTH - 2
MSG_HEIGHT = 6
SCREEN_WIDTH = BG_WIDTH + PANEL_WIDTH*2
SCREEN_HEIGHT = BG_HEIGHT + INFO_HEIGHT + MSG_HEIGHT + 1

BG_OFFSET_X = PANEL_WIDTH
BG_OFFSET_Y = MSG_HEIGHT + 1
PANEL_OFFSET_X = 0
PANEL_OFFSET_Y = BG_OFFSET_Y + 3
MSG_OFFSET_X = BG_OFFSET_X
MSG_OFFSET_Y = 1
INFO_OFFSET_X = PANEL_WIDTH + 1
INFO_OFFSET_Y = BG_OFFSET_Y + BG_HEIGHT

TURN_LAG = 1

class Window(object):
  def __init__(self, battleground, side, host = None, port = None, window_id = 0):
    if DEBUG:
      sys.stdout.write("DEBUG: Window.__init__ started\n")
      
    if host is not None:
      if DEBUG:
        sys.stdout.write(f"DEBUG: Creating network connection to {host}:{port}\n")
      self.network = Network(host, port)
    else:
      if DEBUG:
        sys.stdout.write("DEBUG: No network connection\n")
      self.network = None
    self.bg = battleground
    self.side = side
    self.window_id = window_id

    self.renderer = Renderer()

    # Load sprites after pygame display is initialized
    if DEBUG:
      sys.stdout.write("DEBUG: Loading sprites for all entities\n")
    self.load_all_sprites()

    self.messages = [{}, {}]

    self.game_msgs = []
    self.game_over = False
    self.area_hover_color = COLOR_WHITE
    self.area_hover_color_invalid = (255, 0, 0) # Red for invalid
    self.default_hover_color = (200, 200, 200) # Light grey for default
    self.default_hover_function = SingleTarget(self.bg).get_all_tiles
    self.hover_function = None

    if DEBUG:
      sys.stdout.write("DEBUG: Window.__init__ completed\n")

  def ai_action(self, turn):
    return None

  def check_input(self, keys, mouse, x, y):
    return None

  def check_winner(self):
    return None

  def clean_all(self):
    return False

  def do_hover(self, x, y):
    grid_x, grid_y = self.get_grid_coords(x, y)

    if self.hover_function:
      tiles = self.hover_function(grid_x, grid_y)
      if tiles is None:
        self.bg.hover_tiles(self.default_hover_function(grid_x, grid_y), self.area_hover_color)
      elif tiles:
        self.bg.hover_tiles(tiles, self.area_hover_color)
      else:
        self.bg.hover_tiles(self.default_hover_function(grid_x, grid_y), self.area_hover_color_invalid)
    else:
      self.bg.hover_tiles(self.default_hover_function(grid_x, grid_y), self.default_hover_color)

  def get_grid_coords(self, mouse_x, mouse_y):
      grid_x = (mouse_x - BG_OFFSET_X) // TILE_SIZE
      grid_y = (mouse_y - BG_OFFSET_Y) // TILE_SIZE
      return grid_x, grid_y

  def message(self, new_msg, color=COLOR_WHITE):
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
    for line in new_msg_lines:
      if len(self.game_msgs) == MSG_HEIGHT:
        del self.game_msgs[0]
      self.game_msgs.append((line, color))

  def loop(self):
    if DEBUG:
      sys.stdout.write("DEBUG: Entering main game loop\n")
      
    turn = 0
    while not self.game_over:
      if turn > 0:
        if self.network:
          received = self.network.recv()
        else:
          ai = self.ai_action(turn)
          if ai:
            received = str(turn) + "#" + ai
          else:
            received = "D"
        received_str = str(received) if received else ""
        split = received_str.split("#")
        if len(split) == 2:
          self.messages[not self.side][int(split[0])] = str(split[1])

      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.game_over = True
        elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_ESCAPE:
            self.game_over = True

      keys = pygame.key.get_pressed()
      mouse = pygame.mouse.get_pressed()
      mouse_x, mouse_y = pygame.mouse.get_pos()
      grid_x, grid_y = self.get_grid_coords(mouse_x, mouse_y)
      s = self.check_input(keys, mouse, grid_x, grid_y)
      if s is not None:
        self.messages[self.side][turn] = s

      if self.network:
        if turn in self.messages[self.side]:
          self.network.send(str(turn) + "#"  + self.messages[self.side][turn])
        else:
          self.network.send("D")
      self.process_messages(turn - TURN_LAG)
      self.update_all()
      winner = self.check_winner()
      if (turn % 100) == 0: self.clean_all()

      self.do_hover(mouse_x, mouse_y)
      turn +=1
      
      if DEBUG and (turn % 10 == 0):
        sys.stdout.write(f"DEBUG: Turn {turn} completed\n")
        
      self.render_all(grid_x, grid_y)
      self.renderer.update()

    if DEBUG:
      sys.stdout.write("DEBUG: Game loop ended\n")
    return winner

  def process_messages(self, turn):
    return False

  def render_all(self, x, y):
    self.renderer.clear()
    self.renderer.draw_tile_grid()
    
    # Draw the battleground entities
    for tile in self.bg.tiles.values():
        if tile.entity:
            if tile.entity.animation:
                sprite = tile.entity.animation.get_current_sprite()
                self.renderer.draw_sprite(sprite, tile.x, tile.y)
            else:
                # Fallback to text rendering if no animation is available
                self.renderer.draw_text(tile.entity.character_name, tile.x * 16 + BG_OFFSET_X, tile.y * 16 + BG_OFFSET_Y, tile.entity.color)

    self.render_panels()
    self.render_info(x, y)
    self.render_msgs()

  def render_panels(self):
    pass

  def render_info(self, x, y):
    pass

  def render_msgs(self):
    y = MSG_OFFSET_Y
    for (line, color) in self.game_msgs:
        self.renderer.draw_text(line, MSG_OFFSET_X, y, color)
        y += 15 # Line height

  def update_all(self):
    for g in self.bg.generals:
      g.update()
    for e in self.bg.effects:
      e.update()
    for m in self.bg.minions:
      m.update()

  def load_all_sprites(self):
    """Load sprites for all entities after pygame display is initialized"""
    # Load sprites for generals
    for g in self.bg.generals:
      if hasattr(g, 'load_sprites'):
        g.load_sprites()
    
    # Load sprites for reserves
    for reserves in self.bg.reserves:
      for g in reserves:
        if hasattr(g, 'load_sprites'):
          g.load_sprites()
    
    # Load sprites for minions
    for m in self.bg.minions:
      if hasattr(m, 'load_sprites'):
        m.load_sprites()
    
    # Load sprites for effects
    for e in self.bg.effects:
      if hasattr(e, 'load_sprites'):
        e.load_sprites()
    
    # Load sprites for entities on tiles
    for tile in self.bg.tiles.values():
      if tile.entity and hasattr(tile.entity, 'load_sprites'):
        tile.entity.load_sprites()
        # Also load sprites for the entity's minion if it has one
        if hasattr(tile.entity, 'minion') and tile.entity.minion and hasattr(tile.entity.minion, 'load_sprites'):
          tile.entity.minion.load_sprites()

class Network(object):
  def __init__(self, host, port):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.s.connect((host, port))

  def recv(self):
    data = self.s.recv(1024)
    return data.decode('utf-8') if isinstance(data, bytes) else data

  def send(self, data):
    if isinstance(data, str):
      data = data.encode('utf-8')
    self.s.send(data)
