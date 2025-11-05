"""
Global configuration for Rogue Force
"""

# Development flags
DEBUG = True  # Set to False for production

# Display settings
WINDOW_WIDTH = 1280+256-64
WINDOW_HEIGHT = 1024-128-64
FPS = 60

# Grid settings (logical game units)
BG_WIDTH = 60
BG_HEIGHT = 43
TILE_SIZE = 16  # Pixels per tile

# Asset paths
ASSET_ROOT = 'assets'
SPRITE_PATH = f'{ASSET_ROOT}/sprite'
SOUND_PATH = f'{ASSET_ROOT}/sound'
MUSIC_PATH = f'{ASSET_ROOT}/music'

# Sprite scaling
GENERAL_SCALE = 0.08
MINION_SCALE = 0.04

# UI Layout (in pixels)
# These values are derived from the old tcod layout constants
PANEL_WIDTH = 16  # Character width for side panels
PANEL_PIXEL_WIDTH = PANEL_WIDTH * TILE_SIZE  # 16 * 16 = 256
BATTLEGROUND_PIXEL_WIDTH = BG_WIDTH * TILE_SIZE # 60 * 16 = 960
BATTLEGROUND_PIXEL_HEIGHT = BG_HEIGHT * TILE_SIZE # 43 * 16 = 688

MSG_PIXEL_HEIGHT = 90 # Approximate height for message log

# Define the top-left corner (x, y) for each main UI element
BATTLEGROUND_OFFSET = (PANEL_PIXEL_WIDTH, MSG_PIXEL_HEIGHT)
LEFT_PANEL_OFFSET = (0, 0)
RIGHT_PANEL_OFFSET = (PANEL_PIXEL_WIDTH + BATTLEGROUND_PIXEL_WIDTH, 0)
MSG_LOG_OFFSET = (PANEL_PIXEL_WIDTH, 5)
INFO_BAR_OFFSET = (PANEL_PIXEL_WIDTH, MSG_PIXEL_HEIGHT + BATTLEGROUND_PIXEL_HEIGHT + 5)

# Panel content offset
PANEL_OFFSET_Y = 0
