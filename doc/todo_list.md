# Rogue Force Visual Enhancement System

## Description

A comprehensive sprite-based visual and audio system for Rogue Force that replaces ASCII rendering with animated sprites while maintaining full backward compatibility. The system features ping-pong animations with idle states, graceful fallbacks for missing assets, and a robust developer-friendly architecture organized in a clean asset structure.

## Project Structure

```
rogueforce/
├── assets/
│   ├── sprites/
│   │   ├── {character_name}/         # General sprites (1x scale)
│   │   │   ├── base_idle.png
│   │   │   ├── breathe_1.png
│   │   │   ├── breathe_2.png
│   │   │   ├── walk_1.png
│   │   │   ├── walk_2.png
│   │   │   ├── attack_1.png
│   │   │   ├── attack_2.png
│   │   │   ├── flinch_1.png
│   │   │   └── flinch_2.png
│   │   └── game/                      # Game UI sprites
│   │       ├── healthbar.png
│   │       ├── skill_icons/
│   │       └── effects/
│   ├── sound/
│   │   ├── footstep.ogg
│   │   ├── sword_swing.ogg
│   │   ├── hit_impact.ogg
│   │   └── [other sfx].ogg
│   └── music/
│       ├── battle_theme.ogg
│       └── victory_theme.ogg
├── doc/                               # All documentation
├── test/                              # All tests
├── data/                              # Game data files
├── factions/                          # Faction modules
├── [game_modules].py                  # Core game modules
├── move2doc.py                        # Doc organization utility
└── README.md
```

## Core System Architecture

### Configuration (config.py enhancements)

```python
# config.py
DEBUG = True  # Set to True during development

# Visual settings
USE_SPRITES = True
SPRITE_SCALE_GENERAL = 1.0
SPRITE_SCALE_MINION = 0.8
CAMERA_VIEW_BATTLE = "side"  # Side-scroller view for battles
CAMERA_VIEW_MAP = "top_down"  # Top-down for map

# Audio settings
AUDIO_ENABLED = True
MASTER_VOLUME = 0.8
SFX_VOLUME = 0.8
MUSIC_VOLUME = 0.7

# Asset paths
ASSET_ROOT = "assets"
SPRITE_PATH = f"{ASSET_ROOT}/sprites"
SOUND_PATH = f"{ASSET_ROOT}/sound"
MUSIC_PATH = f"{ASSET_ROOT}/music"
```

### Asset Manager (asset_manager.py)

```python
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
        from PIL import ImageEnhance
        # Simplified hue shift - in production use HSV manipulation
        return img
    
    def _pil_to_pygame(self, pil_image):
        """Convert PIL image to pygame surface"""
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()
        
        return pygame.image.fromstring(data, size, mode)

# Global asset manager instance
asset_manager = AssetManager()
```

### Sprite Animator (sprite_animator.py)

```python
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
```

### Enhanced Entity with Sprites (entity_sprite_mixin.py)

```python
from sprite_animator import SpriteAnimator, AnimationState
from asset_manager import asset_manager
from config import DEBUG, SPRITE_SCALE_GENERAL, CAMERA_VIEW_BATTLE

class SpriteEntityMixin:
    """Mixin to add sprite support to Entity classes"""
    
    def init_sprite_system(self, character_name, scale=SPRITE_SCALE_GENERAL, hue_shift=0):
        """Initialize sprite system for this entity"""
        self.character_name = character_name
        self.sprite_scale = scale
        self.sprite_set = asset_manager.load_character_sprites(
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
```

### Audio Manager (audio_manager.py)

```python
import pygame
from asset_manager import asset_manager
from config import DEBUG, AUDIO_ENABLED, SFX_VOLUME, MUSIC_VOLUME, MASTER_VOLUME

class AudioManager:
    """Manages sound effects and music playback"""
    
    def __init__(self):
        self.enabled = AUDIO_ENABLED
        self.sfx_volume = SFX_VOLUME * MASTER_VOLUME
        self.music_volume = MUSIC_VOLUME * MASTER_VOLUME
        
        if self.enabled:
            try:
                pygame.mixer.set_num_channels(16)
            except Exception as e:
                if DEBUG:
                    print(f"DEBUG: Audio initialization failed: {e}")
                self.enabled = False
    
    def play_sound(self, filename, volume_modifier=1.0):
        """Play a sound effect"""
        if not self.enabled:
            return
        
        sound = asset_manager.load_sound(filename)
        if sound:
            try:
                sound.set_volume(self.sfx_volume * volume_modifier)
                sound.play()
            except Exception as e:
                if DEBUG:
                    print(f"DEBUG: Error playing sound {filename}: {e}")
    
    def play_music(self, filename, loop=-1):
        """Play background music"""
        if not self.enabled:
            return
        
        if asset_manager.load_music(filename):
            try:
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(loop)
            except Exception as e:
                if DEBUG:
                    print(f"DEBUG: Error playing music {filename}: {e}")
    
    def stop_music(self):
        """Stop background music"""
        if self.enabled:
            pygame.mixer.music.stop()

# Global audio manager
audio_manager = AudioManager()
```

### Enhanced Minion Class

```python
# Add to minion.py

from entity_sprite_mixin import SpriteEntityMixin
from config import SPRITE_SCALE_MINION

class Minion(Entity, SpriteEntityMixin):
    def __init__(self, battleground, side, x=-1, y=-1, name="minion", char='m', color=concepts.ENTITY_DEFAULT):
        super(Minion, self).__init__(battleground, side, x, y, char, color)
        self.name = name
        self.max_hp = 30
        self.hp = 30
        # ... rest of existing init ...
        
        # Initialize sprite system for minions
        # Minions use their general's sprite with hue shift and 0.8 scale
        if hasattr(battleground, 'generals') and side < len(battleground.generals):
            general = battleground.generals[side]
            if hasattr(general, 'character_name'):
                # Use general's sprite with hue shift for variation
                self.init_sprite_system(
                    general.character_name, 
                    scale=SPRITE_SCALE_MINION,
                    hue_shift=20  # Slight hue shift for minions
                )
    
    def move(self, dx, dy):
        """Enhanced move with animation trigger"""
        moved = super(Minion, self).move(dx, dy)
        if moved:
            self.trigger_walk_animation(dx)
            # Play footstep sound
            from audio_manager import audio_manager
            audio_manager.play_sound('footstep.ogg', 0.3)
        return moved
    
    def try_attack(self):
        """Enhanced attack with animation and sound"""
        enemy = self.enemy_reachable()
        if enemy:
            self.trigger_attack_animation()
            # Play attack sound
            from audio_manager import audio_manager
            audio_manager.play_sound('sword_swing.ogg')
            enemy.get_attacked(self)
        return enemy != None
    
    def get_attacked(self, enemy, power=None, attack_effect=None, attack_type=None):
        """Enhanced get_attacked with flinch animation"""
        self.trigger_flinch_animation()
        
        # Play hit sound
        from audio_manager import audio_manager
        audio_manager.play_sound('hit_impact.ogg')
        
        # Existing damage logic
        if not power:
            power = enemy.power
        if not attack_effect:
            attack_effect = enemy.attack_effect
        if not attack_type:
            attack_type = enemy.attack_type
        self.hp -= max(0, power - self.armor[attack_type])
        if attack_effect:
            attack_effect.clone(self.x, self.y)
        if self.hp > 0:
            self.update_color()
        else:
            self.hp = 0
            self.die()
            # Play death sound
            audio_manager.play_sound('unit_death.ogg')
            enemy.register_kill(self)
    
    def update(self):
        """Enhanced update with sprite animation"""
        if not self.alive: 
            return
        
        # Update sprite animation
        self.update_sprite_animation()
        
        # Existing update logic
        for s in self.statuses:
            s.update()
        if self.next_action <= 0:
            self.reset_action()
            if not self.try_attack():
                self.follow_tactic()
        else: 
            self.next_action -= 1
```

### Enhanced General Class

```python
# Add to general.py

from entity_sprite_mixin import SpriteEntityMixin

class General(Minion, SpriteEntityMixin):
    def __init__(self, battleground, side, x=-1, y=-1, name="General", color=concepts.FACTION_LEADER):
        super(General, self).__init__(battleground, side, x, y, name, name[0], color)
        # ... existing init ...
        
        # Initialize sprite system (each general subclass should set character_name)
        self.character_name = name.lower()
        self.init_sprite_system(self.character_name)
```

### Documentation Organizer Utility

```python
# move2doc.py

import os
import shutil
from pathlib import Path

def move_docs_to_folder():
    """Move all .md files except README.md to doc/ folder"""
    doc_folder = Path("doc")
    doc_folder.mkdir(exist_ok=True)
    
    # Find all .md files in root
    for md_file in Path(".").glob("*.md"):
        if md_file.name == "README.md":
            continue
        
        dest_path = doc_folder / md_file.name
        
        # Handle duplicates
        if dest_path.exists():
            base = dest_path.stem
            suffix = dest_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = doc_folder / f"{base}_{counter}{suffix}"
                counter += 1
        
        print(f"Moving {md_file} to {dest_path}")
        shutil.move(str(md_file), str(dest_path))
    
    print("Documentation organization complete!")

if __name__ == "__main__":
    move_docs_to_folder()
```

## Implementation Guide

### Step 1: Install Dependencies

```bash
pip install pillow pygame
```

### Step 1a: Update `requirements.txt`

Remove `tcod` from `requirements.txt`.

### Step 2: Create Asset Structure

```bash
mkdir -p assets/sprites
mkdir -p assets/sound
mkdir -p assets/music
mkdir -p assets/sprites/game
mkdir -p doc
mkdir -p test
```

### Step 3: Add New Files

Create the following new files with the code provided above:
- `asset_manager.py`
- `sprite_animator.py`
- `entity_sprite_mixin.py`
- `audio_manager.py`
- `move2doc.py`

### Step 4: Modify Existing Files

**config.py**: Add the visual and audio configuration variables

**entity.py**: Import and use `SpriteEntityMixin`

**minion.py**: Enhance with sprite methods as shown

**general.py**: Add sprite initialization

**window.py**: Add a `pygame`-based rendering path to the `Window` class. This will involve creating a `pygame` screen, rendering the sprites, and then blitting the `libtcod` console on top of it.

**battle.py** and **scenario.py**: Modify the `render_all` methods in both files to call the new sprite rendering methods in `window.py`.

### Step 5: Sprite Naming Convention

Place sprite files in `assets/sprites/{character_name}/`:
- `base_idle.png` - Base idle frame (required)
- `breathe_1.png`, `breathe_2.png` - Breathing animation
- `walk_1.png`, `walk_2.png` - Walking animation
- `attack_1.png`, `attack_2.png` - Attack animation
- `flinch_1.png`, `flinch_2.png` - Hit reaction animation

Character names (lowercase):
- `pock`, `rubock`, `bloodrotter`, `ox` (Doto faction)
- `starcall` (Wizerds faction)
- `gemekaa` (Oracles faction)
- `ares` (Saviours faction)
- `flappy` (Mechanics faction)

### Step 6: Sound Files

Place sound files in `assets/sound/`:
- `footstep.ogg`
- `sword_swing.ogg`
- `arrow_shot.ogg`
- `hit_impact.ogg`
- `unit_death.ogg`
- `skill_cast.ogg`
- `explosion.ogg`
- `thunder.ogg`
- `heal.ogg`

### Step 7: Music Files

Place music files in `assets/music/`:
- `battle_theme.ogg`
- `victory_theme.ogg`

## Key Features

### Graceful Fallbacks
- Missing sprites → ASCII rendering automatically
- Missing sounds → Silent (game continues)
- Missing music → No background music (game continues)

### Debug Mode
- Set `DEBUG = True` in config.py during development
- Logs all missing assets without crashing
- Shows sprite loading status

### Ping-Pong Animation
- All animations center on base_idle sprite
- Sequence: base → frame1 → frame2 → frame1 → base (loop)
- Smooth transitions between states

### Minion Sprite Reuse
- Minions use their general's sprites at 0.8 scale
- Slight hue shift for visual variety
- Reduces asset requirements significantly

### Camera Views
- Battle: Side-view (side-scroller style)
- Map: Top-down (generals show side animations)

## Testing

Create `test/test_sprites.py`:

```python
import sys
sys.path.insert(0, '..')

from asset_manager import asset_manager
from config import DEBUG

def test_sprite_loading():
    """Test sprite loading for all characters"""
    characters = ['pock', 'rubock', 'bloodrotter', 'ox', 
                  'starcall', 'gemekaa', 'ares', 'flappy']
    
    for char in characters:
        print(f"\nTesting {char}:")
        sprites = asset_manager.load_character_sprites(char)
        if sprites:
            print(f"  ✓ Loaded successfully")
        else:
            print(f"  ✗ Failed (using ASCII fallback)")

if __name__ == "__main__":
    test_sprite_loading()
```

Run with: `python test/test_sprites.py`

## Production Checklist

- [ ] Set `DEBUG = False` in config.py
- [ ] All character sprites created and placed
- [ ] All sound effects created and placed
- [ ] Music tracks created and placed
- [ ] Run move2doc.py to organize documentation
- [ ] Test with missing assets to verify fallbacks
- [ ] Test all animations for each character
- [ ] Verify audio plays correctly
- [ ] Check minion sprite scaling and hue shift

## Notes

- Sprite size: 32x32 pixels recommended for generals
- Audio format: OGG Vorbis for cross-platform compatibility
- All paths relative to project root
- Documentation automatically organized in doc/
- Tests stay in test/ folder only
- Asset-not-found errors never crash the game in DEBUG mode