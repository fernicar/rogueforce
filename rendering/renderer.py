"""
Pygame-based rendering system to replace TCOD
"""
import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    BG_WIDTH, BG_HEIGHT, TILE_SIZE,
    DEBUG
)
from concepts import UI_TEXT, UI_BACKGROUND

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

        if DEBUG:
            print(f"[RENDERER] Initialized {WINDOW_WIDTH}x{WINDOW_HEIGHT} window")
            print(f"[RENDERER] Grid: {BG_WIDTH}x{BG_HEIGHT} tiles")
            print(f"[RENDERER] Tile size: {TILE_SIZE}px")

    def clear(self, color=UI_BACKGROUND):
        """Clear screen with given color"""
        self.screen.fill(color)

    def draw_sprite(self, surface, pixel_x, pixel_y, centered=True, mirrored=False):
        """
        Draw sprite at absolute pixel coordinates.

        Args:
            surface: pygame.Surface to draw
            pixel_x: Absolute screen X coordinate
            pixel_y: Absolute screen Y coordinate
            centered: Whether to center sprite on the coordinate
            mirrored: Whether to flip the sprite horizontally
        """
        if surface is None:
            if DEBUG:
                # Draw placeholder if sprite is missing
                rect = pygame.Rect(
                    pixel_x,
                    pixel_y,
                    TILE_SIZE, TILE_SIZE
                )
                # Adjust for centering if needed
                if centered:
                    rect.center = (pixel_x, pixel_y)
                pygame.draw.rect(self.screen, (255, 0, 255), rect)
            return

        # Apply horizontal mirroring if needed
        if mirrored:
            surface = pygame.transform.flip(surface, True, False)

        # The calling code now provides the final pixel coordinates.
        # We just need to handle centering.
        if centered:
            draw_pos = (
                pixel_x - surface.get_width() // 2,
                pixel_y - surface.get_height() // 2
            )
        else:
            draw_pos = (pixel_x, pixel_y)

        self.screen.blit(surface, draw_pos)

    def draw_text(self, text, x, y, color=UI_TEXT, large=False):
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

    def quit(self):
        """Cleanup Pygame"""
        pygame.quit()
