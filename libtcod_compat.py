"""
Minimal libtcod compatibility layer using pygame
Provides only the essential functions needed by the project
"""

import pygame
import sys
from color_utils import Color

# Global screen surface
_screen = None
_console = None

def console_init_root(width, height, title="Rogue Force", renderer=None, fullscreen=False, vsync=False):
    """Initialize console root (pygame version)"""
    global _screen
    pygame.init()
    
    flags = 0
    if fullscreen:
        flags |= pygame.FULLSCREEN
    
    _screen = pygame.display.set_mode((width, height), flags)
    pygame.display.set_caption(title)
    
    # Create a simple console object
    _console = {
        'width': width,
        'height': height,
        'surface': _screen
    }
    
    return _console

def console_flush():
    """Update display"""
    if _screen:
        pygame.display.flip()

def console_set_default_foreground(color):
    """Set default foreground color"""
    pass  # Not implemented for pygame version

def console_set_default_background(color):
    """Set default background color"""
    pass  # Not implemented for pygame version

def console_is_key_pressed():
    """Check if any key is pressed"""
    keys = pygame.key.get_pressed()
    return any(keys)

def console_check_for_keypress():
    """Check for key press events"""
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            return event
        elif event.type == pygame.QUIT:
            return None
    return None

def console_wait_for_keypress(flush=False):
    """Wait for key press"""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                return event
            elif event.type == pygame.QUIT:
                return None

# Console class for compatibility
class Console:
    """Simple console compatibility class"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.chars = [[' ' for _ in range(width)] for _ in range(height)]
        self.fg_colors = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]
        self.bg_colors = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
    
    def clear(self):
        """Clear console"""
        self.chars = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.fg_colors = [[(255, 255, 255) for _ in range(self.width)] for _ in range(self.height)]
        self.bg_colors = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]
    
    def put_char(self, x, y, char, fg=None, bg=None):
        """Put character at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.chars[y][x] = char
            self.fg_colors[y][x] = fg if fg is not None else (255, 255, 255)
            self.bg_colors[y][x] = bg if bg is not None else (0, 0, 0)
    
    def put_char_ex(self, x, y, char, fg, bg):
        """Put character with explicit colors"""
        self.put_char(x, y, char, fg, bg)
    
    def print(self, x, y, text, fg=None, bg=None):
        """Print text at position"""
        for i, char in enumerate(text):
            if x + i < self.width:
                self.put_char(x + i, y, char, fg, bg)
    
    def draw(self, screen):
        """Draw console to screen"""
        if not screen:
            return
            
        # Simple font rendering
        try:
            font = pygame.font.Font(None, 16)
        except:
            font = pygame.font.SysFont('monospace', 12)
        
        char_width = 8
        char_height = 12
        
        for y in range(self.height):
            for x in range(self.width):
                char = self.chars[y][x]
                if char != ' ':
                    fg = self.fg_colors[y][x]
                    bg = self.bg_colors[y][x]
                    
                    # Convert color objects if needed
                    if hasattr(fg, 'as_tuple'):
                        fg = fg.as_tuple()
                    elif hasattr(fg, '__iter__') and not isinstance(fg, str):
                        fg = tuple(fg)[:3]
                    
                    if hasattr(bg, 'as_tuple'):
                        bg = bg.as_tuple()
                    elif hasattr(bg, '__iter__') and not isinstance(bg, str):
                        bg = tuple(bg)[:3]
                    
                    # Draw background
                    pygame.draw.rect(screen, bg, 
                                   (x * char_width, y * char_height, char_width, char_height))
                    
                    # Draw character
                    text_surface = font.render(char, True, fg)
                    screen.blit(text_surface, (x * char_width, y * char_height))

# Key constants
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_ENTER = pygame.K_RETURN
KEY_ESCAPE = pygame.K_ESCAPE
KEY_CHAR = 'char'

# Create a simple libtcod-like interface
libtcod = type('libtcod', (), {
    'console_init_root': console_init_root,
    'console_flush': console_flush,
    'console_set_default_foreground': console_set_default_foreground,
    'console_set_default_background': console_set_default_background,
    'console_is_key_pressed': console_is_key_pressed,
    'console_check_for_keypress': console_check_for_keypress,
    'console_wait_for_keypress': console_wait_for_keypress,
    'Console': Console,
    'KEY_UP': KEY_UP,
    'KEY_DOWN': KEY_DOWN,
    'KEY_LEFT': KEY_LEFT,
    'KEY_RIGHT': KEY_RIGHT,
    'KEY_ENTER': KEY_ENTER,
    'KEY_ESCAPE': KEY_ESCAPE,
    'KEY_CHAR': KEY_CHAR,
    'Color': Color
})