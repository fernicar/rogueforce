"""
Asset loading with DEBUG-safe fallbacks
"""
import pygame
import os
from pathlib import Path
from config import DEBUG, SPRITE_PATH, SOUND_PATH, MUSIC_PATH, GENERAL_SCALE, MINION_SCALE

class AssetLoader:
    """Handles loading of all game assets with DEBUG mode support"""

    def __init__(self):
        self.sprites = {}
        self.sounds = {}
        self.music = {}
        self.missing_assets = []
        # Sprite cache: (path, scale, hue_shift) -> pygame.Surface
        self.sprite_cache = {}

    def load_sprite(self, path, scale=1.0, hue_shift=0):
        """
        Load sprite with optional scaling and hue shift

        Args:
            path: Relative path from SPRITE_PATH
            scale: Scale multiplier (1.0 = original size)
            hue_shift: HSV hue shift in degrees (-180 to 180)

        Returns:
            pygame.Surface or None if missing (in DEBUG mode)
        """
        # Create cache key
        cache_key = (path, scale, hue_shift)
        
        # Return cached sprite if available
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]
        
        full_path = os.path.join(SPRITE_PATH, path)

        if not os.path.exists(full_path):
            if DEBUG:
                print(f"[ASSET WARNING] Sprite not found: {full_path}")
                self.missing_assets.append(full_path)
                # Return placeholder surface
                size = int(32 * scale)
                surface = pygame.Surface((size, size))
                surface.fill((255, 0, 255)) # Magenta placeholder
                # Cache the placeholder too
                self.sprite_cache[cache_key] = surface
                return surface
            else:
                raise FileNotFoundError(f"Required sprite missing: {full_path}")

        try:
            surface = pygame.image.load(full_path).convert_alpha()

            # Apply scaling
            if scale != 1.0:
                new_size = (
                    int(surface.get_width() * scale),
                    int(surface.get_height() * scale)
                )
                surface = pygame.transform.scale(surface, new_size)

            # Apply hue shift if needed
            if hue_shift != 0:
                surface = self._hue_shift(surface, hue_shift)

            # Store in cache
            self.sprite_cache[cache_key] = surface
            return surface

        except Exception as e:
            if DEBUG:
                print(f"[ASSET ERROR] Failed to load sprite {full_path}: {e}")
                self.missing_assets.append(full_path)
                size = int(32 * scale)
                surface = pygame.Surface((size, size))
                surface.fill((255, 0, 255))
                # Cache the error placeholder too
                self.sprite_cache[cache_key] = surface
                return surface
            else:
                raise

    def _hue_shift(self, surface, degrees):
        """Apply hue shift to surface (for minion color variations)"""
        import colorsys

        # Convert surface to pixel array
        arr = pygame.surfarray.pixels3d(surface)

        # Shift hue for each pixel
        for x in range(arr.shape[0]):
            for y in range(arr.shape[1]):
                r, g, b = arr[x, y]
                h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                h = (h + degrees/360) % 1.0
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                arr[x, y] = (int(r*255), int(g*255), int(b*255))

        del arr # Release pixel array
        return surface

    def load_sound(self, path):
        """Load sound effect with DEBUG fallback"""
        full_path = os.path.join(SOUND_PATH, path)

        if not os.path.exists(full_path):
            if DEBUG:
                print(f"[ASSET WARNING] Sound not found: {full_path}")
                self.missing_assets.append(full_path)
                return None
            else:
                raise FileNotFoundError(f"Required sound missing: {full_path}")

        try:
            return pygame.mixer.Sound(full_path)
        except Exception as e:
            if DEBUG:
                print(f"[ASSET ERROR] Failed to load sound {full_path}: {e}")
                self.missing_assets.append(full_path)
                return None
            else:
                raise

    def load_music(self, path):
        """Load music file with DEBUG fallback"""
        full_path = os.path.join(MUSIC_PATH, path)

        if not os.path.exists(full_path):
            if DEBUG:
                print(f"[ASSET WARNING] Music not found: {full_path}")
                self.missing_assets.append(full_path)
                return False
            else:
                raise FileNotFoundError(f"Required music missing: {full_path}")

        try:
            pygame.mixer.music.load(full_path)
            return True
        except Exception as e:
            if DEBUG:
                print(f"[ASSET ERROR] Failed to load music {full_path}: {e}")
                self.missing_assets.append(full_path)
                return False
            else:
                raise

    def get_character_sprites(self, character_name, is_general=False):
        """
        Load all sprites for a character

        Args:
            character_name: Name of the character sprite folder
            is_general: True for generals (uses GENERAL_SCALE), False for minions (uses MINION_SCALE)

        Returns dict: {
            'base_idle': Surface,
            'breathe_1': Surface,
            'breathe_2': Surface,
            'walk_1': Surface,
            'walk_2': Surface,
            'attack_1': Surface,
            'attack_2': Surface,
            'flinch_1': Surface,
            'flinch_2': Surface
        }
        """
        sprites = {}
        sprite_names = [
            'base_idle', 'breathe_1', 'breathe_2',
            'walk_1', 'walk_2', 'attack_1', 'attack_2',
            'flinch_1', 'flinch_2'
        ]

        # Check if character_name is valid (string and alphanumeric)
        if not character_name or not isinstance(character_name, str) or not character_name.isalnum():
            if DEBUG:
                print(f"[SPRITE WARNING] Invalid character_name: {character_name} (type: {type(character_name)})")
            return {sprite_name: None for sprite_name in sprite_names}

        # Use appropriate scaling based on character type
        scale = GENERAL_SCALE if is_general else MINION_SCALE

        for sprite_name in sprite_names:
            path = f"{character_name}/{sprite_name}.png"
            sprites[sprite_name] = self.load_sprite(path, scale=scale)

        return sprites

    def clear_cache(self):
        """Clear sprite cache (useful for memory management)"""
        self.sprite_cache.clear()

    def report_cache_stats(self):
        """Report cache statistics"""
        print(f"[ASSET LOADER] Sprite cache size: {len(self.sprite_cache)} sprites cached")

    def report_missing_assets(self):
        """Print report of all missing assets"""
        if self.missing_assets:
            print("\n=== MISSING ASSETS REPORT ===")
            print(f"Total missing: {len(self.missing_assets)}")
            for asset in sorted(set(self.missing_assets)):
                print(f"  - {asset}")
            print("============================\n")

# Global asset loader instance
asset_loader = AssetLoader()
