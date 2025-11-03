from area import SingleTarget
from battleground import Battleground

import concepts
import pygame

import socket
import sys
import textwrap
import time

# Import DEBUG from config module to avoid circular imports
from config import DEBUG
import config

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

    pygame.init()
    self.screen = pygame.display.set_mode((SCREEN_WIDTH * 10, SCREEN_HEIGHT * 10))
    pygame.display.set_caption('Rogue Force')
    self.font = pygame.font.Font('JetBrainsMono-Regular.ttf', 12)

    self.messages = [{}, {}]

    self.game_msgs = []
    self.game_over = False
    self.area_hover_color = concepts.UI_HOVER_VALID
    self.area_hover_color_invalid = concepts.UI_HOVER_INVALID
    self.default_hover_color = concepts.UI_HOVER_DEFAULT
    self.default_hover_function = SingleTarget(self.bg).get_all_tiles
    self.hover_function = None

    if DEBUG:
      sys.stdout.write("DEBUG: Window.__init__ completed\n")
    
  def ai_action(self, turn):
    return None

  def check_input(self, event):
    return None

  def check_winner(self):
    return None

  def clean_all(self):
    return False

  def do_hover(self, x, y):
    if self.hover_function:
        tiles = self.hover_function(x, y)
        if tiles is None:
            self.bg.hover_tiles(self.default_hover_function(x,y), self.area_hover_color)
        elif tiles:
            self.bg.hover_tiles(tiles, self.area_hover_color)
        else:
            self.bg.hover_tiles(self.default_hover_function(x, y), self.area_hover_color_invalid)
    else:
        self.bg.hover_tiles(self.default_hover_function(x, y), self.default_hover_color)

  def message(self, new_msg, color=concepts.UI_TEXT):
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
    for line in new_msg_lines:
      #if the buffer is full, remove the first line to make room for the new one
      if len(self.game_msgs) == MSG_HEIGHT:
        del self.game_msgs[0]
      #add the new line as a tuple, with the text and the color
      self.game_msgs.append((line, color))

  def loop(self):
    if DEBUG:
      sys.stdout.write("DEBUG: Entering main game loop\n")
      
    turn = 0
    turn_time = 0.1

    while not self.game_over:
      start = time.time()

      # Input handling
      for event in pygame.event.get():
          if event.type == pygame.QUIT:
              self.game_over = True
              return None
          if event.type == pygame.KEYDOWN:
              if event.key == pygame.K_ESCAPE:
                  self.game_over = True
                  return None

          # Pass event to subclass for handling
          s = self.check_input(event)
          if s is not None:
              self.messages[self.side][turn] = s

      # Network and AI
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

      if self.network:
        if turn in self.messages[self.side]:
          self.network.send(str(turn) + "#"  + self.messages[self.side][turn])
        else:
          self.network.send("D")

      self.process_messages(turn - TURN_LAG)
      self.update_all()
      winner = self.check_winner()
      if (turn % 100) == 0: self.clean_all()

      # Hover
      x, y = pygame.mouse.get_pos()
      self.do_hover(x / 10 - BG_OFFSET_X, y / 10 - BG_OFFSET_Y)

      turn +=1
      
      if DEBUG and (turn % 10 == 0):
        sys.stdout.write(f"DEBUG: Turn {turn} completed\n")
        
      self.render_all(x, y)

      # Cap framerate
      elapsed = time.time() - start
      if elapsed < turn_time:
          time.sleep(turn_time - elapsed)

      if turn == 1:
        pygame.image.save(self.screen, "screenshot.png")

    if DEBUG:
      sys.stdout.write("DEBUG: Game loop ended\n")
    return winner

  def process_messages(self, turn):
    return False

  def render_all(self, x, y):
    self.screen.fill(concepts.UI_BACKGROUND)
    
    self.render_sprites()
    self.bg.draw(self.screen, self.font)
    
    self.render_info(x, y)
    self.render_msgs()
    self.render_panels()
    
    pygame.display.flip()

  def render_bar(self, x, y, w, value, max_value, bar_bg_color, bar_fg_color, text_color):
    self.draw_bar(x, y, w, 10, value, max_value, bar_bg_color, bar_fg_color)
    self.draw_text("%03d / %03d" % (value, max_value), x + 10, y, text_color)
 
  def render_info(self, x, y):
    x = int(x)
    y = int(y)
    if self.bg.is_inside(x, y):
      self.draw_text("%02d/%02d" % (x, y), (INFO_WIDTH-7) * 10, INFO_OFFSET_Y * 10, concepts.UI_TEXT)
      entity = self.bg.tiles[(x, y)].entity
      if entity:
        if(hasattr(entity, 'hp')):
          self.draw_text(entity.name.capitalize() + ": HP %02d/%02d, PW %d" %
            (entity.hp, entity.max_hp, entity.power), INFO_OFFSET_X * 10, INFO_OFFSET_Y * 10, entity.original_color)
        else:
          self.draw_text(entity.name.capitalize(), INFO_OFFSET_X * 10, INFO_OFFSET_Y * 10, concepts.UI_TEXT)
    
  def render_msgs(self):
    y = 0
    for (line, color) in self.game_msgs:
      self.draw_text(line, MSG_OFFSET_X * 10, (MSG_OFFSET_Y + y) * 10, color)
      y += 1

  def render_panels(self):
    bar_length = 11
    bar_offset_x = 4
    for i in [0,1]:
      self.render_side_panel(i, bar_length, bar_offset_x)

  def render_side_panel(self, i, bar_length, bar_offset_x):
    pass

  def draw_text(self, text, x, y, color):
    """Draw text to the screen"""
    surface = self.font.render(text, True, color)
    self.screen.blit(surface, (x, y))

  def draw_bar(self, x, y, w, h, value, max_value, bar_bg_color, bar_fg_color):
    """Draw a bar to the screen"""
    # Background
    pygame.draw.rect(self.screen, bar_bg_color, (x, y, w, h))
    # Foreground
    ratio = float(value) / max_value
    pygame.draw.rect(self.screen, bar_fg_color, (x, y, w * ratio, h))

  def render_sprites(self):
    """Render all sprites to the pygame screen"""
    if not config.USE_SPRITES:
        return

    # Get all entities with sprites
    entities = self.bg.generals + self.bg.minions

    for entity in entities:
        if hasattr(entity, 'has_sprites') and entity.has_sprites:
            sprite = entity.get_current_sprite()
            if sprite:
                # Calculate screen position
                x = (entity.x + BG_OFFSET_X) * 10
                y = (entity.y + BG_OFFSET_Y) * 10
                self.screen.blit(sprite, (x, y))

  def update_all(self):
    for g in self.bg.generals:
      g.update()
    for e in self.bg.effects:
      e.update()
    for m in self.bg.minions:
      m.update()

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
