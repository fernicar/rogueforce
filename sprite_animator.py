from enum import Enum
from config import DEBUG

class AnimationState(Enum):
    IDLE = "idle"
    WALKING = "walking"
    ATTACKING = "attacking"
    FLINCH = "flinch"

class SpriteAnimator:
    """Handles ping-pong sprite animation with idle center"""

    # Frame durations (in game ticks)
    DURATIONS = {
        AnimationState.IDLE: 8,
        AnimationState.WALKING: 4,
        AnimationState.ATTACKING: 3,
        AnimationState.FLINCH: 2
    }

    # Which animations loop
    LOOPING = {
        AnimationState.IDLE: True,
        AnimationState.WALKING: True,
        AnimationState.ATTACKING: False,
        AnimationState.FLINCH: False
    }

    def __init__(self, sprite_set):
        """
        sprite_set: dict with keys 'base', 'breathe', 'walk', 'attack', 'flinch'
        Each animation key contains a list of 2 frames
        """
        self.sprite_set = sprite_set
        self.current_state = AnimationState.IDLE
        self.previous_state = AnimationState.IDLE

        self.frame_timer = 0
        self.ping_pong_forward = True

        # Ping-pong sequences: base -> frame1 -> frame2 -> frame1 -> base (repeat)
        self.sequences = {
            AnimationState.IDLE: ['base', 'breathe_0', 'breathe_1', 'breathe_0'],
            AnimationState.WALKING: ['base', 'walk_0', 'walk_1', 'walk_0'],
            AnimationState.ATTACKING: ['base', 'attack_0', 'attack_1', 'attack_0'],
            AnimationState.FLINCH: ['base', 'flinch_0', 'flinch_1', 'flinch_0']
        }

        self.sequence_index = 0

    def update(self):
        """Update animation frame"""
        self.frame_timer += 1
        duration = self.DURATIONS[self.current_state]

        if self.frame_timer >= duration:
            self.frame_timer = 0
            self._advance_frame()

    def _advance_frame(self):
        """Advance to next frame in ping-pong sequence"""
        sequence = self.sequences[self.current_state]
        self.sequence_index += 1

        # Check if sequence completed
        if self.sequence_index >= len(sequence):
            if self.LOOPING[self.current_state]:
                self.sequence_index = 0
            else:
                # Non-looping animation finished, return to previous state
                self.transition_to(self.previous_state)

    def transition_to(self, new_state):
        """Transition to a new animation state"""
        if new_state == self.current_state:
            return

        # FLINCH always interrupts
        if new_state == AnimationState.FLINCH:
            self.previous_state = self.current_state
        elif not self.LOOPING[self.current_state]:
            # Don't interrupt non-looping animations unless flinching
            return

        self.current_state = new_state
        self.sequence_index = 0
        self.frame_timer = 0

    def get_current_sprite(self):
        """Get the current sprite to render"""
        if not self.sprite_set:
            return None

        sequence = self.sequences[self.current_state]
        frame_key = sequence[self.sequence_index]

        # Parse frame key
        if frame_key == 'base':
            return self.sprite_set['base']
        else:
            # Format: 'animation_index' e.g., 'breathe_0'
            parts = frame_key.split('_')
            anim_name = parts[0]
            frame_idx = int(parts[1])
            return self.sprite_set[anim_name][frame_idx]
