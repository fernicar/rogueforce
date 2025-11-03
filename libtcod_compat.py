"""
Complete pygame-based console replacement for libtcod
Provides all essential libtcod functionality using pygame
"""

import pygame
import sys
from color_utils import Color

class Console:
    """Pygame-based console that fully replaces libtcod.console"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.char_width = 8
        self.char_height = 12
        
        # Create surface for this console
        self.surface = pygame.Surface(
            (width * self.char_width, height * self.char_height),
            pygame.SRCALPHA
        )
        
        # Character and color buffers
        self.char_buffer = [[' ' for _ in range(width)] for _ in range(height)]
        self.fg_buffer = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]
        self.bg_buffer = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        
        # Default colors
        self.default_bg = (0, 0, 0)
        self.default_fg = (255, 255, 255)
        
        # Font for text rendering
        try:
            self.font = pygame.font.Font(None, 16)
        except:
            self.font = pygame.font.SysFont('monospace', 12)
    
    def clear(self):
        """Clear the console"""
        self.char_buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.fg_buffer = [[self.default_fg for _ in range(self.width)] for _ in range(self.height)]
        self.bg_buffer = [[self.default_bg for _ in range(self.width)] for _ in range(self.height)]
    
    def put_char(self, x, y, char, fg=None, bg=None):
        """Put a character at specified position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.char_buffer[y][x] = char
            self.fg_buffer[y][x] = fg if fg is not None else self.default_fg
            self.bg_buffer[y][x] = bg if bg is not None else self.default_bg
    
    def put_char_ex(self, x, y, char, fg, bg):
        """Put a character with explicit foreground and background colors"""
        self.put_char(x, y, char, fg, bg)
    
    def print(self, x, y, text, fg=None, bg=None):
        """Print a string starting at specified position"""
        for i, char in enumerate(text):
            if x + i < self.width:
                self.put_char(x + i, y, char, fg, bg)
    
    def set_default_foreground(self, color):
        """Set default foreground color"""
        self.default_fg = color
    
    def set_default_background(self, color):
        """Set default background color"""
        self.default_bg = color
    
    def draw(self, target_surface=None):
        """Draw console to screen"""
        if target_surface is None:
            target_surface = pygame.display.get_surface()
        
        # Clear the area where we'll draw
        for y in range(self.height):
            for x in range(self.width):
                bg = self.bg_buffer[y][x]
                # Convert color objects if needed
                if hasattr(bg, 'as_tuple'):
                    bg = bg.as_tuple()
                elif hasattr(bg, '__iter__') and not isinstance(bg, str):
                    bg = tuple(bg)[:3]
                
                pygame.draw.rect(
                    target_surface,
                    bg,
                    (x * self.char_width, y * self.char_height, self.char_width, self.char_height)
                )
        
        # Draw characters
        for y in range(self.height):
            for x in range(self.width):
                char = self.char_buffer[y][x]
                if char != ' ':
                    fg = self.fg_buffer[y][x]
                    # Convert color objects if needed
                    if hasattr(fg, 'as_tuple'):
                        fg = fg.as_tuple()
                    elif hasattr(fg, '__iter__') and not isinstance(fg, str):
                        fg = tuple(fg)[:3]
                    
                    # Draw character
                    text_surface = self.font.render(char, True, fg)
                    text_rect = text_surface.get_rect()
                    text_rect.topleft = (x * self.char_width, y * self.char_height)
                    target_surface.blit(text_surface, text_rect)

# Global screen reference
_screen = None

def console_init_root(width, height, title="Rogue Force", renderer=None, fullscreen=False, vsync=False):
    """Initialize root console (pygame version)"""
    global _screen
    pygame.init()
    
    flags = 0
    if fullscreen:
        flags |= pygame.FULLSCREEN
    
    _screen = pygame.display.set_mode((width, height), flags)
    pygame.display.set_caption(title)
    
    return _screen

def console_flush():
    """Update display"""
    if _screen:
        pygame.display.flip()

def console_is_key_pressed():
    """Check if any key is pressed"""
    keys = pygame.key.get_pressed()
    return any(keys)

def console_check_for_keypress():
    """Get key press event"""
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

# Key constants
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_ENTER = pygame.K_RETURN
KEY_ESCAPE = pygame.K_ESCAPE
KEY_CHAR = 'char'

# Create libtcod-like interface
libtcod = type('libtcod', (), {
    'console_init_root': console_init_root,
    'console_flush': console_flush,
    'console_is_key_pressed': console_is_key_pressed,
    'console_check_for_keypress': console_check_for_keypress,
    'console_wait_for_keypress': console_wait_for_keypress,
    'Console': Console,
    'Color': Color,
    'KEY_UP': KEY_UP,
    'KEY_DOWN': KEY_DOWN,
    'KEY_LEFT': KEY_LEFT,
    'KEY_RIGHT': KEY_RIGHT,
    'KEY_ENTER': KEY_ENTER,
    'KEY_ESCAPE': KEY_ESCAPE,
    'KEY_CHAR': KEY_CHAR
})