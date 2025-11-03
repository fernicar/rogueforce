from sprite_animator import SpriteAnimator, AnimationState
from asset_manager import AssetManager
from config import DEBUG, SPRITE_SCALE_GENERAL, CAMERA_VIEW_BATTLE

class SpriteEntityMixin:
    """Mixin to add sprite support to Entity classes"""

    def init_sprite_system(self, character_name, scale=SPRITE_SCALE_GENERAL, hue_shift=0):
        """Initialize sprite system for this entity"""
        self.character_name = character_name
        self.sprite_scale = scale
        self.sprite_set = AssetManager.load_character_sprites(
            character_name, scale, hue_shift
        )

        if self.sprite_set:
            self.animator = SpriteAnimator(self.sprite_set)
            self.has_sprites = True
            if DEBUG:
                print(f"DEBUG: Loaded sprites for {character_name}")
        else:
            self.animator = None
            self.has_sprites = False
            if DEBUG:
                print(f"DEBUG: No sprites for {character_name}, using ASCII fallback")

        self.facing_right = (self.side == 0)  # Side 0 faces right
        self.last_dx = 0

    def update_sprite_animation(self):
        """Update sprite animation (call in entity.update())"""
        if self.has_sprites and self.animator:
            self.animator.update()

    def trigger_walk_animation(self, dx):
        """Trigger walk animation when moving"""
        if self.has_sprites and self.animator:
            self.animator.transition_to(AnimationState.WALKING)
            if dx != 0:
                self.facing_right = (dx > 0)
                self.last_dx = dx

    def trigger_attack_animation(self):
        """Trigger attack animation"""
        if self.has_sprites and self.animator:
            self.animator.transition_to(AnimationState.ATTACKING)

    def trigger_flinch_animation(self):
        """Trigger flinch animation when hit"""
        if self.has_sprites and self.animator:
            self.animator.transition_to(AnimationState.FLINCH)

    def get_current_sprite(self):
        """Get current sprite with proper facing direction"""
        if not self.has_sprites or not self.animator:
            return None

        sprite = self.animator.get_current_sprite()

        # Mirror sprite if facing left
        if CAMERA_VIEW_BATTLE == "side":
            # For side view: side 0 faces right, side 1 faces left
            should_mirror = (self.side == 1)

            if should_mirror and sprite:
                import pygame
                return pygame.transform.flip(sprite, True, False)

        return sprite
