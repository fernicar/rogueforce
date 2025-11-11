"""
Ping-pong animation system for sprites
"""
from __future__ import annotations
import pygame
from typing import Dict, List, Optional, Any
from config import DEBUG

class Animation:
    """
    Handles ping-pong animations
    Idle sprite is in the middle, animates to extremes and back
    """

    def __init__(self, sprites: Dict[str, Any], fps: int = 2) -> None:
        """
        Args:
            sprites: Dict with keys like 'base_idle', 'breathe_1', 'breathe_2', etc.
            fps: Frames per second for animation
        """
        self.sprites = sprites
        self.fps = fps
        self.frame_duration = 1000 / fps # milliseconds per frame
        self.last_update = pygame.time.get_ticks()

        # Animation states
        self.current_state = 'idle' # idle, walk, attack, flinch
        self.frame_index = 0
        self.forward = True # Direction of ping-pong

        # Define animation sequences (ping-pong)
        self.sequences: Dict[str, List[str]] = {
            'idle': ['breathe_1', 'base_idle', 'breathe_2'],
            'walk': ['walk_2', 'base_idle', 'walk_1'],
            'attack': ['attack_1', 'attack_2'],
            'flinch': ['flinch_1', 'flinch_2']
        }

    def update(self) -> None:
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

    def get_current_sprite(self) -> Optional[Any]:
        """Get current sprite surface"""
        sequence = self.sequences[self.current_state]
        sprite_name = sequence[self.frame_index]
        return self.sprites.get(sprite_name)

    def set_state(self, state: str) -> None:
        """Change animation state (idle, walk, attack, flinch)"""
        if state != self.current_state:
            self.current_state = state
            self.frame_index = 0
            self.forward = True
