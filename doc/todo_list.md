# Phase 1: Remove TCOD and Implement Pygame - Detailed Migration Plan

## Overview
This phase focuses on completely removing libtcod/libtcodpy dependencies and replacing them with Pygame, while establishing the proper project structure and development safeguards.

---

## Part A: Project Structure Setup (Complete First)

### A.1: Create Directory Structure
```bash
# Create required directories
mkdir -p doc
mkdir -p test
mkdir -p assets/sound
mkdir -p assets/music
mkdir -p assets/sprite/game
```

### A.2: Create move2doc.py Utility
Create `move2doc.py` in project root:

```python
import os
import shutil
from pathlib import Path

def move_files():
    """Move documentation and test files to proper directories"""
    root = Path('.')
    
    # Move markdown files (except README.md) to doc/
    for md_file in root.glob('*.md'):
        if md_file.name != 'README.md':
            dest = Path('doc') / md_file.name
            if dest.exists():
                # Rename if duplicate
                base = dest.stem
                ext = dest.suffix
                counter = 1
                while dest.exists():
                    dest = Path('doc') / f"{base}_{counter}{ext}"
                    counter += 1
            shutil.move(str(md_file), str(dest))
            print(f"Moved {md_file.name} to {dest}")
    
    # Move test files to test/
    for test_file in root.glob('*test*.py'):
        dest = Path('test') / test_file.name
        if dest.exists():
            base = dest.stem
            ext = dest.suffix
            counter = 1
            while dest.exists():
                dest = Path('test') / f"{base}_{counter}{ext}"
                counter += 1
        shutil.move(str(test_file), str(dest))
        print(f"Moved {test_file.name} to {dest}")

if __name__ == '__main__':
    move_files()
```

Run this immediately:
```bash
python move2doc.py
```

### A.3: Update config.py
Replace `config.py` content:

```python
"""
Global configuration for Rogue Force
"""

# Development flags
DEBUG = True  # Set to False for production

# Display settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Grid settings (logical game units)
GRID_WIDTH = 60
GRID_HEIGHT = 43
TILE_SIZE = 16  # Pixels per tile

# Asset paths
ASSET_ROOT = 'assets'
SPRITE_PATH = f'{ASSET_ROOT}/sprite'
SOUND_PATH = f'{ASSET_ROOT}/sound'
MUSIC_PATH = f'{ASSET_ROOT}/music'

# Sprite scaling
GENERAL_SCALE = 1.0
MINION_SCALE = 0.8

# Colors (RGB tuples)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BACKGROUND = (20, 20, 40)
```

---

## Part B: Asset Management System

### B.1: Create assets/asset_loader.py

```python
"""
Asset loading with DEBUG-safe fallbacks
"""
import pygame
import os
from pathlib import Path
from config import DEBUG, SPRITE_PATH, SOUND_PATH, MUSIC_PATH

class AssetLoader:
    """Handles loading of all game assets with DEBUG mode support"""
    
    def __init__(self):
        self.sprites = {}
        self.sounds = {}
        self.music = {}
        self.missing_assets = []
    
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
        full_path = os.path.join(SPRITE_PATH, path)
        
        if not os.path.exists(full_path):
            if DEBUG:
                print(f"[ASSET WARNING] Sprite not found: {full_path}")
                self.missing_assets.append(full_path)
                # Return placeholder surface
                size = int(32 * scale)
                surface = pygame.Surface((size, size))
                surface.fill((255, 0, 255))  # Magenta placeholder
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
            
            return surface
            
        except Exception as e:
            if DEBUG:
                print(f"[ASSET ERROR] Failed to load sprite {full_path}: {e}")
                self.missing_assets.append(full_path)
                size = int(32 * scale)
                surface = pygame.Surface((size, size))
                surface.fill((255, 0, 255))
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
        
        del arr  # Release pixel array
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
    
    def get_character_sprites(self, character_name):
        """
        Load all sprites for a character
        
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
        
        for sprite_name in sprite_names:
            path = f"{character_name}/{sprite_name}.png"
            sprites[sprite_name] = self.load_sprite(path)
        
        return sprites
    
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
```

---

## Part C: Pygame Rendering System

### C.1: Create rendering/renderer.py

```python
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
        pygame.mixer.init()
        
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
```

---

## Part D: Update requirements.txt

Replace `requirements.txt`:

```
pygame==2.5.2
```

---

## Part E: Remove TCOD Dependencies

### E.1: Find all TCOD imports
```bash
# List all files with tcod imports
grep -r "import.*tcod" --include="*.py" .
grep -r "from.*tcod" --include="*.py" .
```

### E.2: Create compatibility shims (temporary)

Create `compat/tcod_shim.py`:

```python
"""
Temporary compatibility shim during migration
DO NOT USE FOR NEW CODE - will be removed after Phase 1
"""
from config import DEBUG
import sys

if DEBUG:
    print("[MIGRATION WARNING] tcod_shim.py imported - this should not happen after Phase 1")

# Stub classes to prevent import errors during gradual migration
class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

class Key:
    def __init__(self):
        self.vk = 0
        self.c = 0

class Mouse:
    def __init__(self):
        self.cx = 0
        self.cy = 0
        self.lbutton_pressed = False
        self.rbutton_pressed = False

# Map old TCOD constants to Pygame equivalents
FONT_TYPE_GREYSCALE = 1
FONT_LAYOUT_TCOD = 2
EVENT_ANY = 0
KEY_ESCAPE = 27
BKGND_SET = 1

def console_init_root(*args, **kwargs):
    if DEBUG:
        print(f"[STUB] console_init_root called with {args}, {kwargs}")

def console_new(*args, **kwargs):
    if DEBUG:
        print(f"[STUB] console_new called")
    return None

def console_set_custom_font(*args, **kwargs):
    if DEBUG:
        print(f"[STUB] console_set_custom_font called")

def console_flush():
    pass

def console_is_window_closed():
    return False

def sys_check_for_event(*args, **kwargs):
    pass

# Add more stubs as needed during migration
```

### E.3: Update imports gradually

For each file, replace:
```python
# OLD
import libtcodpy as libtcod
from libtcod import *

# NEW
from rendering.renderer import Renderer
from assets.asset_loader import asset_loader
import pygame
```

---

## Part F: Create Animation System

Create `rendering/animation.py`:

```python
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
```

---

## Part G: Testing Framework

Create `test/test_migration_phase1.py`:

```python
"""
Tests for Phase 1 migration
"""
import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import DEBUG
from rendering.renderer import Renderer
from assets.asset_loader import asset_loader

class TestPhase1Setup(unittest.TestCase):
    """Test Phase 1 setup and structure"""
    
    def test_directory_structure(self):
        """Verify all required directories exist"""
        required_dirs = [
            'doc',
            'test',
            'assets/sound',
            'assets/music',
            'assets/sprite/game'
        ]
        
        for dir_path in required_dirs:
            self.assertTrue(
                os.path.exists(dir_path),
                f"Required directory missing: {dir_path}"
            )
    
    def test_config_module(self):
        """Verify config module has required settings"""
        from config import (
            DEBUG, WINDOW_WIDTH, WINDOW_HEIGHT,
            GRID_WIDTH, GRID_HEIGHT, TILE_SIZE
        )
        
        self.assertIsInstance(DEBUG, bool)
        self.assertGreater(WINDOW_WIDTH, 0)
        self.assertGreater(WINDOW_HEIGHT, 0)
    
    def test_asset_loader_debug_mode(self):
        """Test asset loader handles missing files in DEBUG mode"""
        # Try to load non-existent sprite
        sprite = asset_loader.load_sprite('nonexistent/test.png')
        
        # Should return placeholder in DEBUG mode, not crash
        self.assertIsNotNone(sprite)
    
    def test_no_tcod_imports(self):
        """Verify no direct tcod imports in main modules"""
        import re
        
        files_to_check = [
            'config.py',
            'rendering/renderer.py',
            'assets/asset_loader.py'
        ]
        
        for filepath in files_to_check:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    self.assertNotIn('import libtcod', content,
                                   f"{filepath} should not import libtcod")
                    self.assertNotIn('from libtcod', content,
                                   f"{filepath} should not import libtcod")

if __name__ == '__main__':
    unittest.main()
```

---

## Part H: Migration Checklist

Create `doc/PHASE1_CHECKLIST.md`:

```markdown
# Phase 1 Migration Checklist

## Pre-Migration
- [ ] Backup entire project
- [ ] Commit current state to git
- [ ] Document current TCOD usage

## Structure Setup
- [ ] Run move2doc.py
- [ ] Verify directory structure
- [ ] Update .gitignore

## Core Systems
- [ ] Update config.py
- [ ] Create asset_loader.py
- [ ] Create renderer.py
- [ ] Create animation.py
- [ ] Update requirements.txt

## File-by-File Migration
- [ ] concepts.py (no TCOD, already done)
- [ ] config.py (completed above)
- [ ] battleground.py
- [ ] window.py
- [ ] battle.py
- [ ] entity.py
- [ ] minion.py
- [ ] general.py
- [ ] effect.py
- [ ] skill.py
- [ ] status.py
- [ ] tactic.py
- [ ] formation.py
- [ ] area.py
- [ ] sieve.py
- [ ] scenario.py
- [ ] server.py (no TCOD)
- [ ] faction.py (no TCOD)
- [ ] factions/*.py

## Testing
- [ ] Run test_migration_phase1.py
- [ ] Manual smoke test
- [ ] Verify DEBUG mode works
- [ ] Test asset loading failures
- [ ] Test placeholder rendering

## Cleanup
- [ ] Remove arial10x10.png (TCOD font)
- [ ] Remove compat/tcod_shim.py
- [ ] Update all imports
- [ ] Remove TCOD from requirements.txt
- [ ] Run final tests

## Documentation
- [ ] Update README.md
- [ ] Document new rendering system
- [ ] Document asset loading system
- [ ] Create migration notes
```

---

## Success Criteria for Phase 1

1. ✅ **No TCOD imports** - All `import libtcodpy` and `import libtcod` removed
2. ✅ **Project structure** - doc/, test/, assets/ properly organized
3. ✅ **DEBUG mode works** - Missing assets don't crash game
4. ✅ **Pygame rendering** - Basic window opens and displays
5. ✅ **Asset loading** - Character sprites load with proper scaling
6. ✅ **Tests pass** - test_migration_phase1.py runs successfully
7. ✅ **No regressions** - Existing gameplay logic intact (even if not rendering yet)

---

## Next Steps (Phase 2 Preview)

- Implement side-view battle camera
- Connect entity rendering to new system
- Implement animation controllers
- Add particle effects
- Create UI system with Pygame

---

**This completes Phase 1 specification. Each part should be implemented in order (A→H) to ensure dependencies are met.**