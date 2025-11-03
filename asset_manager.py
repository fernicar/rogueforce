import os
import sys
from PIL import Image, ImageOps
import pygame
from config import DEBUG, SPRITE_PATH, SOUND_PATH, MUSIC_PATH
from sprite_animator import SpriteAnimator

class AssetManager:
    """Centralized asset loading with graceful fallbacks"""

    sprite_cache = {}
    sound_cache = {}
    missing_assets = set()

    @staticmethod
    def init():
        try:
            pygame.mixer.init()
        except Exception as e:
            if DEBUG:
                print(f"DEBUG: Failed to initialize audio: {e}")

    @staticmethod
    def get_animator(sprite_name, scale=1.0, hue_shift=0):
        """Load sprites and create a SpriteAnimator"""
        if not sprite_name:
            return None

        sprite_set = AssetManager.load_character_sprites(sprite_name, scale, hue_shift)
        if sprite_set:
            return SpriteAnimator(sprite_set)
        return None

    @staticmethod
    def load_sprite(path, scale=1.0, hue_shift=0):
        """Load sprite with caching and fallback"""
        cache_key = f"{path}_{scale}_{hue_shift}"

        if cache_key in AssetManager.missing_assets:
            return None

        if cache_key in AssetManager.sprite_cache:
            return AssetManager.sprite_cache[cache_key]

        full_path = os.path.join(SPRITE_PATH, path)

        try:
            img = Image.open(full_path).convert("RGBA")

            if hue_shift != 0:
                img = AssetManager._apply_hue_shift(img, hue_shift)

            if scale != 1.0:
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.NEAREST)

            sprite = AssetManager._pil_to_pygame(img)
            AssetManager.sprite_cache[cache_key] = sprite
            return sprite

        except FileNotFoundError:
            if DEBUG:
                print(f"DEBUG: Sprite not found: {full_path}")
            AssetManager.missing_assets.add(cache_key)
            return None
        except Exception as e:
            if DEBUG:
                print(f"DEBUG: Error loading sprite {full_path}: {e}")
            AssetManager.missing_assets.add(cache_key)
            return None

    @staticmethod
    def load_character_sprites(character_name, scale=1.0, hue_shift=0):
        """Load complete sprite set for a character"""
        sprite_set = {}

        base = AssetManager.load_sprite(f"{character_name}/base_idle.png", scale, hue_shift)
        if base is None:
            if DEBUG:
                print(f"DEBUG: No base sprite for {character_name}, using fallback")
            return None

        sprite_set['base'] = base

        animations = ['breathe', 'walk', 'attack', 'flinch']
        for anim in animations:
            frames = []
            for i in [1, 2]:
                frame = AssetManager.load_sprite(f"{character_name}/{anim}_{i}.png", scale, hue_shift)
                frames.append(frame if frame else base)
            sprite_set[anim] = frames

        return sprite_set

    @staticmethod
    def load_sound(filename):
        """Load sound effect with fallback"""
        if filename in AssetManager.missing_assets:
            return None

        if filename in AssetManager.sound_cache:
            return AssetManager.sound_cache[filename]

        full_path = os.path.join(SOUND_PATH, filename)

        try:
            sound = pygame.mixer.Sound(full_path)
            AssetManager.sound_cache[filename] = sound
            return sound
        except FileNotFoundError:
            if DEBUG:
                print(f"DEBUG: Sound not found: {full_path}")
            AssetManager.missing_assets.add(filename)
            return None
        except Exception as e:
            if DEBUG:
                print(f"DEBUG: Error loading sound {full_path}: {e}")
            AssetManager.missing_assets.add(filename)
            return None

    @staticmethod
    def load_music(filename):
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

    @staticmethod
    def _apply_hue_shift(img, hue_shift):
        """Apply hue shift to image for minion color variation"""
        from PIL import ImageEnhance
        # Simplified hue shift - in production use HSV manipulation
        return img

    @staticmethod
    def _pil_to_pygame(pil_image):
        """Convert PIL image to pygame surface"""
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()

        return pygame.image.fromstring(data, size, mode)

AssetManager.init()
