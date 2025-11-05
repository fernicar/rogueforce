from area import SingleTarget
from battleground import Battleground
from rendering.renderer import Renderer
from assets.asset_loader import asset_loader
import pygame
from config import (
    TILE_SIZE, DEBUG,
    BATTLEGROUND_OFFSET, PANEL_PIXEL_WIDTH, BATTLEGROUND_PIXEL_WIDTH
)
from concepts import UI_HOVER_VALID, UI_BACKGROUND

import socket
import sys
import textwrap
import time

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
    self.area_hover_color = UI_HOVER_VALID
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
      """
      Converts absolute screen coordinates to battleground grid coordinates.
      """
      # Subtract the battleground's top-left corner offset
      relative_x = mouse_x - BATTLEGROUND_OFFSET[0]
      relative_y = mouse_y - BATTLEGROUND_OFFSET[1]
      
      # Convert pixel coordinates to grid coordinates
      grid_x = relative_x // TILE_SIZE
      grid_y = relative_y // TILE_SIZE
      
      return grid_x, grid_y

  def message(self, new_msg, color=UI_HOVER_VALID):
    new_msg_lines = textwrap.wrap(new_msg, 58)  # Approximate MSG_WIDTH
    for line in new_msg_lines:
      if len(self.game_msgs) == 6:  # MSG_HEIGHT
        del self.game_msgs[0]
      self.game_msgs.append((line, color))

  def loop(self):
    if DEBUG:
      sys.stdout.write("DEBUG: Entering main game loop\n")
      
    turn = 0
    # The old code used a fixed time per turn. We'll use pygame's clock for a more stable loop.
    # The game logic will still advance one 'turn' per frame for simplicity.

    while not self.game_over:
      # --- Input Handling ---
      # We process all events at the start of the frame.
      s = None # Action string
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.game_over = True
          continue # Skip the rest of the loop for this frame
        if event.type == pygame.KEYDOWN:
          if event.key == pygame.K_ESCAPE:
            self.game_over = True
            continue

      # Get mouse state *after* processing events
      mouse_buttons = pygame.mouse.get_pressed()
      mouse_pos = pygame.mouse.get_pos()
      grid_x, grid_y = self.get_grid_coords(mouse_pos[0], mouse_pos[1])

      # Get keyboard state for check_input. We pass the event queue for single-press actions.
      keys_pressed = pygame.key.get_pressed()
      s = self.check_input(keys_pressed, mouse_buttons, grid_x, grid_y)
      if s is not None:
        self.messages[self.side][turn] = s

      # --- Network and Message Processing ---
      # This logic remains largely the same.
      if self.network:
        # Send our action for this turn
        if turn in self.messages[self.side]:
          self.network.send(str(turn) + "#"  + self.messages[self.side][turn])
        else:
          self.network.send("D") # Send dummy message to keep sync
        
        # Receive opponent's action
        received = self.network.recv()
      else:
        # Generate AI action if no network
        ai = self.ai_action(turn)
        received = str(turn) + "#" + ai if ai else "D"
      
      received_str = str(received) if received else ""
      split = received_str.split("#")
      if len(split) == 2 and split[0].isdigit():
        other_side = (self.side + 1) % 2
        self.messages[other_side][int(split[0])] = str(split[1])

      # --- Game State Update ---
      # Process messages from the turn before the lag period.
      self.process_messages(turn - TURN_LAG)
      self.update_all()
      winner = self.check_winner()

      if (turn % 100) == 0:
        self.clean_all()

      # --- Rendering ---
      self.do_hover(mouse_pos[0], mouse_pos[1])
      self.render_all(grid_x, grid_y)
      self.renderer.update() # This handles pygame.display.flip() and clock.tick()

      # --- Advance Turn ---
      turn += 1
      if DEBUG and (turn % 50 == 0):
        sys.stdout.write(f"DEBUG: Turn {turn} completed\n")

    if DEBUG:
      sys.stdout.write("DEBUG: Game loop ended\n")
    asset_loader.report_missing_assets() # Report any missing sprites at the end.
    self.renderer.quit()
    return winner

  def process_messages(self, turn):
    return False

  def render_all(self, grid_x, grid_y):
      self.renderer.clear()
      
      # --- Draw Battleground ---
      bg_off_x, bg_off_y = BATTLEGROUND_OFFSET

      # Draw hovered tile backgrounds first
      for tile in self.bg.hovered:
          rect = (
              bg_off_x + tile.x * TILE_SIZE,
              bg_off_y + tile.y * TILE_SIZE,
              TILE_SIZE, TILE_SIZE
          )
          pygame.draw.rect(self.renderer.screen, tile.bg_color, rect)

      # Draw tiles, entities, and effects
      for tile in self.bg.tiles.values():
          if not self.bg.is_inside(tile.x, tile.y):
              continue

          pixel_x = bg_off_x + tile.x * TILE_SIZE
          pixel_y = bg_off_y + tile.y * TILE_SIZE
          
          drawable = None
          if tile.effects:
              drawable = tile.effects[-1]
          elif tile.entity:
              drawable = tile.entity
          
          if drawable:
              # This is where we preserve your sprite rendering logic, but adapt it
              # to the corrected coordinate system.
              if drawable.animation:
                  sprite = drawable.animation.get_current_sprite()
                  # We calculate the center of the tile for centered drawing
                  center_pixel_x = pixel_x + TILE_SIZE // 2
                  center_pixel_y = pixel_y + TILE_SIZE // 2
                  self.renderer.draw_sprite(sprite, center_pixel_x, center_pixel_y)
              else:
                  # Fallback to text for entities without sprites
                  char_to_draw = drawable.char if hasattr(drawable, 'char') else '?'
                  self.renderer.draw_text(char_to_draw, pixel_x, pixel_y, drawable.color)
          elif not tile in self.bg.hovered:
              # Draw the floor/wall character if nothing is on the tile
              self.renderer.draw_text(tile.char, pixel_x, pixel_y, tile.color)

      # --- Draw UI Panels and Text ---
      # These methods will be fully implemented in the next phase.
      self.render_panels()
      self.render_info(grid_x, grid_y)
      self.render_msgs()

  def render_panels(self):
    pass

  def render_info(self, x, y):
    pass

  def render_bar(self, x, y, w, h, value, max_value, bar_fg_color, bar_bg_color, text_color):
    # Calculate bar width
    ratio = 0
    if max_value > 0:
        ratio = int(w * (float(value) / max_value))

    # Draw background
    self.renderer.draw_rect(x, y, w, h, bar_bg_color)
    # Draw foreground
    if ratio > 0:
        self.renderer.draw_rect(x, y, ratio, h, bar_fg_color)
    
    # Draw text
    text = f"{int(value):02d}/{int(max_value):02d}"
    self.renderer.draw_text(text, x + 5, y + 2, text_color)

  def render_msgs(self):
    y = 5  # MSG_LOG_OFFSET[1]
    for (line, color) in self.game_msgs:
        self.renderer.draw_text(line, BATTLEGROUND_OFFSET[0], y, color)
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
