import os
import sys
from PIL import Image, ImageOps
import pygame
from config import DEBUG, SPRITE_PATH, SOUND_PATH, MUSIC_PATH

class AssetManager:
    """Centralized asset loading with graceful fallbacks"""

    def __init__(self):
        self.sprite_cache = {}
        self.sound_cache = {}
        self.music_cache = {}
        self.missing_assets = set()

        # Initialize pygame mixer for audio
        try:
            pygame.mixer.init()
        except Exception as e:
            if DEBUG:
                print(f"DEBUG: Failed to initialize audio: {e}")

    def load_sprite(self, path, scale=1.0, hue_shift=0):
        """Load sprite with caching and fallback"""
        cache_key = f"{path}_{scale}_{hue_shift}"

        if cache_key in self.missing_assets:
            return None

        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]

        full_path = os.path.join(SPRITE_PATH, path)

        try:
            img = Image.open(full_path).convert("RGBA")

            # Apply hue shift if requested (for minions)
            if hue_shift != 0:
                img = self._apply_hue_shift(img, hue_shift)

            # Apply scaling
            if scale != 1.0:
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.NEAREST)

            # Convert to pygame surface
            sprite = self._pil_to_pygame(img)
            self.sprite_cache[cache_key] = sprite
            return sprite

        except FileNotFoundError:
            if DEBUG:
                print(f"DEBUG: Sprite not found: {full_path}")
            self.missing_assets.add(cache_key)
            return None
        except Exception as e:
            if DEBUG:
                print(f"DEBUG: Error loading sprite {full_path}: {e}")
            self.missing_assets.add(cache_key)
            return None

    def load_character_sprites(self, character_name, scale=1.0, hue_shift=0):
        """Load complete sprite set for a character"""
        sprite_set = {}

        # Try to load base_idle first (required)
        base = self.load_sprite(f"{character_name}/base_idle.png", scale, hue_shift)
        if base is None:
            if DEBUG:
                print(f"DEBUG: No base sprite for {character_name}, using fallback")
            return None

        sprite_set['base'] = base

        # Load animation frames with fallback to base
        animations = ['breathe', 'walk', 'attack', 'flinch']
        for anim in animations:
            frames = []
            for i in [1, 2]:
                frame = self.load_sprite(f"{character_name}/{anim}_{i}.png", scale, hue_shift)
                frames.append(frame if frame else base)
            sprite_set[anim] = frames

        return sprite_set

    def load_sound(self, filename):
        """Load sound effect with fallback"""
        if filename in self.missing_assets:
            return None

        if filename in self.sound_cache:
            return self.sound_cache[filename]

        full_path = os.path.join(SOUND_PATH, filename)

        try:
            sound = pygame.mixer.Sound(full_path)
            self.sound_cache[filename] = sound
            return sound
        except FileNotFoundError:
            if DEBUG:
                print(f"DEBUG: Sound not found: {full_path}")
            self.missing_assets.add(filename)
            return None
        except Exception as e:
            if DEBUG:
                print(f"DEBUG: Error loading sound {full_path}: {e}")
            self.missing_assets.add(filename)
            return None

    def load_music(self, filename):
        """Load music file"""
        full_path = os.path.join(MUSIC_PATH, filename)

        try:
            pygame.mixer.music.load(full_path)
            return True
        except FileNotFoundError:
            if DEBUG:
                print(f"DEBUG: Music not found: {full_path}")
            return False
        except Exception as e:
            if DEBUG:
                print(f"DEBUG: Error loading music {full_path}: {e}")
            return False

    def _apply_hue_shift(self, img, hue_shift):
        """Apply hue shift to image for minion color variation"""
        import colorsys
        img = img.convert('RGBA')
        ld = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = ld[x, y]
                h, s, v = colorsys.rgb_to_hsv(r/255., g/255., b/255.)
                h = (h + hue_shift/360.0) % 1.0
                r, g, b = [int(c*255) for c in colorsys.hsv_to_rgb(h, s, v)]
                ld[x, y] = (r, g, b, a)
        return img

    def _pil_to_pygame(self, pil_image):
        """Convert PIL image to pygame surface"""
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()

        return pygame.image.fromstring(data, size, mode)

# Global asset manager instance
asset_manager = AssetManager()
