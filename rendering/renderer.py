"""
Pygame-based rendering system to replace TCOD
"""
import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    GRID_WIDTH, GRID_HEIGHT, TILE_SIZE,
    COLOR_BLACK, COLOR_WHITE, COLOR_BACKGROUND, DEBUG
)

class Renderer:
    """Main rendering class using Pygame"""

    def __init__(self, title="Rogue Force"):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error as e:
            print(f"[AUDIO ERROR] Could not initialize mixer: {e}")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(title)

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)  # Default font, size 20
        self.large_font = pygame.font.Font(None, 32)

        # Camera offset for side view battles
        self.camera_x = 0
        self.camera_y = 0

        if DEBUG:
            print(f"[RENDERER] Initialized {WINDOW_WIDTH}x{WINDOW_HEIGHT} window")
            print(f"[RENDERER] Grid: {GRID_WIDTH}x{GRID_HEIGHT} tiles")
            print(f"[RENDERER] Tile size: {TILE_SIZE}px")

    def clear(self, color=COLOR_BACKGROUND):
        """Clear screen with given color"""
        self.screen.fill(color)

    def draw_sprite(self, surface, x, y, centered=True):
        """
        Draw sprite at grid coordinates

        Args:
            surface: pygame.Surface to draw
            x: Grid X coordinate
            y: Grid Y coordinate
            centered: Whether to center sprite on tile
        """
        if surface is None:
            if DEBUG:
                # Draw placeholder
                rect = pygame.Rect(
                    x * TILE_SIZE - self.camera_x,
                    y * TILE_SIZE - self.camera_y,
                    TILE_SIZE, TILE_SIZE
                )
                pygame.draw.rect(self.screen, (255, 0, 255), rect)
            return

        pixel_x = x * TILE_SIZE - self.camera_x
        pixel_y = y * TILE_SIZE - self.camera_y

        if centered:
            pixel_x -= surface.get_width() // 2
            pixel_y -= surface.get_height() // 2

        self.screen.blit(surface, (pixel_x, pixel_y))

    def draw_text(self, text, x, y, color=COLOR_WHITE, large=False):
        """Draw text at pixel coordinates"""
        font = self.large_font if large else self.font
        text_surface = font.render(str(text), True, color)
        self.screen.blit(text_surface, (x, y))

    def draw_rect(self, x, y, width, height, color, filled=True):
        """Draw rectangle at pixel coordinates"""
        rect = pygame.Rect(x, y, width, height)
        if filled:
            pygame.draw.rect(self.screen, color, rect)
        else:
            pygame.draw.rect(self.screen, color, rect, 1)

    def draw_tile_grid(self):
        """Draw debug grid (only in DEBUG mode)"""
        if not DEBUG:
            return

        for x in range(0, WINDOW_WIDTH, TILE_SIZE):
            pygame.draw.line(self.screen, (50, 50, 50), (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, TILE_SIZE):
            pygame.draw.line(self.screen, (50, 50, 50), (0, y), (WINDOW_WIDTH, y))

    def update(self):
        """Update display and maintain FPS"""
        pygame.display.flip()
        self.clock.tick(FPS)

    def set_camera(self, x, y):
        """Set camera position (for scrolling/following)"""
        self.camera_x = x
        self.camera_y = y

    def quit(self):
        """Cleanup Pygame"""
        pygame.quit()
