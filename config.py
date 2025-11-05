"""
Global configuration for Rogue Force
"""

# Development flags
DEBUG = True  # Set to False for production

# Display settings
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60

# Grid settings (logical game units)
GRID_WIDTH = 60
GRID_HEIGHT = 43
TILE_SIZE = 16  # Pixels per tile

# Asset paths
ASSET_ROOT = 'assets'
SPRITE_PATH = f'{ASSET_ROOT}/sprite'
SOUND_PATH = f'{ASSET_ROOT}/sound'
MUSIC_PATH = f'{ASSET_ROOT}/music'

# Sprite scaling
GENERAL_SCALE = 0.04
MINION_SCALE = 0.03

# Colors (RGB tuples)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BACKGROUND = (20, 20, 40)
