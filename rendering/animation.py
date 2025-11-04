"""
Ping-pong animation system for sprites
"""
import pygame
from config import DEBUG

class Animation:
    """
    Handles ping-pong animations
    Idle sprite is in the middle, animates to extremes and back
    """

    def __init__(self, sprites, fps=10):
        """
        Args:
            sprites: Dict with keys like 'base_idle', 'breathe_1', 'breathe_2', etc.
            fps: Frames per second for animation
        """
        self.sprites = sprites
        self.fps = fps
        self.frame_duration = 1000 / fps  # milliseconds per frame
        self.last_update = pygame.time.get_ticks()

        # Animation states
        self.current_state = 'idle'  # idle, walk, attack, flinch
        self.frame_index = 0
        self.forward = True  # Direction of ping-pong

        # Define animation sequences (ping-pong)
        self.sequences = {
            'idle': ['base_idle', 'breathe_1', 'breathe_2', 'breathe_1', 'base_idle'],
            'walk': ['base_idle', 'walk_1', 'walk_2', 'walk_1', 'base_idle'],
            'attack': ['base_idle', 'attack_1', 'attack_2', 'attack_1', 'base_idle'],
            'flinch': ['base_idle', 'flinch_1', 'flinch_2', 'flinch_1', 'base_idle']
        }

    def update(self):
        """Update animation frame based on time"""
        now = pygame.time.get_ticks()

        if now - self.last_update > self.frame_duration:
            self.last_update = now

            sequence = self.sequences[self.current_state]

            if self.forward:
                self.frame_index += 1
                if self.frame_index >= len(sequence):
                    self.frame_index = len(sequence) - 2
                    self.forward = False
            else:
                self.frame_index -= 1
                if self.frame_index < 0:
                    self.frame_index = 1
                    self.forward = True

    def get_current_sprite(self):
        """Get current sprite surface"""
        sequence = self.sequences[self.current_state]
        sprite_name = sequence[self.frame_index]
        return self.sprites.get(sprite_name)

    def set_state(self, state):
        """Change animation state (idle, walk, attack, flinch)"""
        if state != self.current_state:
            self.current_state = state
            self.frame_index = 0
            self.forward = True
