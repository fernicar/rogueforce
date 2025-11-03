# Rogue Force Visual Enhancement TINS

## Description

A comprehensive visual and audio enhancement system for Rogue Force that replaces ASCII characters with sprite-based animations while maintaining full backward compatibility. The system implements a sophisticated animation framework supporting breathing, walking, attacking, and flinch animations with automatic fallback to ASCII rendering when sprites are unavailable. All sprites are designed for side-scroller perspective with automatic mirroring for directional movement.

## Core Functionality

### Animation System Architecture

The enhancement system operates as a non-invasive layer over the existing ASCII rendering engine. Each entity (generals, minions, effects) can have associated sprite sheets organized in a standardized directory structure. When sprites are available, the system seamlessly transitions from ASCII to animated sprite rendering. When sprites are missing, the system gracefully falls back to the original ASCII display.

### Sprite Organization Structure

```
sprites/
├── generals/
│   ├── pock/
│   │   ├── base.png          # Base idle frame (32x32px)
│   │   ├── breathe_1.png     # Breathing animation frame 1
│   │   ├── breathe_2.png     # Breathing animation frame 2
│   │   ├── walk_1.png        # Walking animation frame 1
│   │   ├── walk_2.png        # Walking animation frame 2
│   │   ├── attack_1.png      # Attack animation frame 1
│   │   ├── attack_2.png      # Attack animation frame 2
│   │   ├── flinch_1.png      # Flinch animation frame 1
│   │   └── flinch_2.png      # Flinch animation frame 2
│   ├── rubock/
│   ├── bloodrotter/
│   └── ox/
├── minions/
│   ├── wizard/
│   ├── archer/
│   └── default/
├── effects/
│   ├── explosion/
│   ├── wave/
│   ├── thunder/
│   └── orb/
└── ui/
    ├── icons/
    └── panels/
```

### Animation State Machine

Each animated entity maintains an animation state that determines which sprite sequence to display:

**IDLE State**: Plays the breathing animation loop
- Sequence: base → breathe_1 → breathe_2 → breathe_1 → (repeat)
- Frame duration: 8 game ticks per frame
- Triggers: Entity is not performing any action

**WALKING State**: Plays the walking animation loop
- Sequence: base → walk_1 → walk_2 → walk_1 → (repeat)
- Frame duration: 4 game ticks per frame
- Triggers: Entity moves to a new position
- Duration: Continues for 12 ticks after movement stops

**ATTACKING State**: Plays the attack animation once, then returns to idle
- Sequence: base → attack_1 → attack_2 → (return to idle)
- Frame duration: 3 game ticks per frame
- Triggers: Entity performs an attack action
- Duration: One complete cycle (9 ticks total)

**FLINCH State**: Plays the flinch animation once, then returns to previous state
- Sequence: base → flinch_1 → flinch_2 → (return to previous)
- Frame duration: 2 game ticks per frame
- Triggers: Entity receives damage
- Duration: One complete cycle (6 ticks total)
- Priority: Interrupts all other animations

### Sprite Loading and Caching

The system implements intelligent sprite loading with memory-efficient caching:

```python
class SpriteManager:
    def __init__(self):
        self.sprite_cache = {}
        self.missing_sprites = set()
        self.base_sprite_size = (32, 32)
    
    def load_sprite_set(self, entity_type, entity_name):
        """
        Loads all sprite frames for an entity.
        Returns dictionary of animation states or None if base sprite missing.
        
        Sprite set includes:
        - base: The foundational idle frame
        - breathe: List of 2 breathing frames
        - walk: List of 2 walking frames
        - attack: List of 2 attack frames
        - flinch: List of 2 flinch frames
        """
        cache_key = f"{entity_type}/{entity_name}"
        
        if cache_key in self.missing_sprites:
            return None
            
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]
        
        base_path = f"sprites/{entity_type}/{entity_name}"
        base_sprite = self.load_image(f"{base_path}/base.png")
        
        if base_sprite is None:
            self.missing_sprites.add(cache_key)
            return None
        
        sprite_set = {
            'base': base_sprite,
            'breathe': self.load_animation_frames(base_path, 'breathe', 2, base_sprite),
            'walk': self.load_animation_frames(base_path, 'walk', 2, base_sprite),
            'attack': self.load_animation_frames(base_path, 'attack', 2, base_sprite),
            'flinch': self.load_animation_frames(base_path, 'flinch', 2, base_sprite)
        }
        
        self.sprite_cache[cache_key] = sprite_set
        return sprite_set
    
    def load_animation_frames(self, base_path, animation_name, frame_count, fallback):
        """
        Loads animation frames with fallback to base sprite.
        If any frame is missing, uses the base sprite for that frame.
        """
        frames = []
        for i in range(1, frame_count + 1):
            frame_path = f"{base_path}/{animation_name}_{i}.png"
            frame = self.load_image(frame_path)
            frames.append(frame if frame else fallback)
        return frames
```

### Directional Sprite Mirroring

All sprites are authored facing right (for side 1) or left (for side 0). The system automatically mirrors sprites based on entity facing direction:

```python
class AnimatedEntity:
    def get_current_sprite(self):
        """Returns the current sprite frame with appropriate mirroring."""
        sprite = self.get_animation_frame()
        
        if sprite is None:
            return None
        
        # Determine if sprite should be mirrored
        needs_mirror = False
        
        # For generals and minions
        if hasattr(self, 'side'):
            # Side 0 faces right, side 1 faces left in original game
            # Sprites are drawn facing right by default
            needs_mirror = (self.side == 1)
        
        # For movement-based mirroring (if entity has direction)
        if hasattr(self, 'last_direction'):
            needs_mirror = (self.last_direction < 0)
        
        if needs_mirror:
            return self.mirror_sprite(sprite)
        return sprite
    
    def mirror_sprite(self, sprite):
        """Horizontally flips a sprite."""
        # Implementation depends on graphics library
        # For pygame: pygame.transform.flip(sprite, True, False)
        # For libtcod: requires custom implementation
        pass
```

### Integration with Existing Rendering

The visual enhancement integrates into the existing `draw()` methods throughout the codebase:

```python
class Entity:
    def __init__(self, battleground, side, x, y, char, color):
        # Existing initialization
        self.char = char
        self.color = color
        
        # New sprite animation system
        self.sprite_animator = SpriteAnimator(self)
        self.animation_state = AnimationState.IDLE
        self.animation_frame = 0
        self.animation_timer = 0
    
    def draw_sprite(self, console, sprite_manager):
        """
        Attempts to draw sprite. Returns True if sprite was drawn,
        False if ASCII fallback should be used.
        """
        sprite = self.sprite_animator.get_current_frame()
        
        if sprite is None:
            return False
        
        # Convert grid coordinates to pixel coordinates
        pixel_x = self.x * TILE_WIDTH
        pixel_y = self.y * TILE_HEIGHT
        
        # Draw sprite centered on tile
        offset_x = (TILE_WIDTH - sprite.width) // 2
        offset_y = (TILE_HEIGHT - sprite.height) // 2
        
        console.draw_sprite(sprite, pixel_x + offset_x, pixel_y + offset_y)
        return True
    
    def update(self):
        # Existing update logic
        # ...
        
        # Update animation
        self.sprite_animator.update()
```

### Modified Battleground Drawing

The `Battleground.draw()` method is enhanced to support both rendering modes:

```python
class Battleground:
    def __init__(self, width, height, tilefile=None):
        # Existing initialization
        # ...
        
        # New sprite management
        self.sprite_manager = SpriteManager()
        self.use_sprites = True  # Can be toggled via settings
    
    def draw(self, con):
        """Enhanced draw method with sprite support."""
        # Draw tiles (background)
        for pos in self.tiles:
            tile = self.tiles[pos]
            if self.use_sprites:
                if not tile.draw_sprite(con, self.sprite_manager):
                    tile.draw_ascii(con)  # Fallback
            else:
                tile.draw_ascii(con)
        
        # Draw entities with sprite support
        entities = []
        entities.extend(self.effects)
        entities.extend(self.minions)
        entities.extend(self.generals)
        
        # Sort by y-coordinate for proper layering
        entities.sort(key=lambda e: e.y)
        
        for entity in entities:
            if not entity.alive:
                continue
                
            if self.use_sprites:
                if not entity.draw_sprite(con, self.sprite_manager):
                    entity.draw_ascii(con)  # Fallback
            else:
                entity.draw_ascii(con)
```

### Animation Timing and Frame Management

```python
class SpriteAnimator:
    def __init__(self, entity):
        self.entity = entity
        self.current_state = AnimationState.IDLE
        self.frame_index = 0
        self.frame_timer = 0
        self.state_timer = 0
        self.previous_state = AnimationState.IDLE
        
        # Frame durations for each animation type (in game ticks)
        self.frame_durations = {
            AnimationState.IDLE: 8,
            AnimationState.WALKING: 4,
            AnimationState.ATTACKING: 3,
            AnimationState.FLINCH: 2
        }
        
        # Animation sequences
        self.sequences = {
            AnimationState.IDLE: ['base', 'breathe', 0, 'breathe', 1, 'breathe', 0],
            AnimationState.WALKING: ['base', 'walk', 0, 'walk', 1, 'walk', 0],
            AnimationState.ATTACKING: ['base', 'attack', 0, 'attack', 1],
            AnimationState.FLINCH: ['base', 'flinch', 0, 'flinch', 1]
        }
        
        # Which animations loop vs play once
        self.looping_states = {
            AnimationState.IDLE: True,
            AnimationState.WALKING: True,
            AnimationState.ATTACKING: False,
            AnimationState.FLINCH: False
        }
    
    def update(self):
        """Updates animation frame based on timing."""
        self.frame_timer += 1
        self.state_timer += 1
        
        current_duration = self.frame_durations[self.current_state]
        
        if self.frame_timer >= current_duration:
            self.frame_timer = 0
            self.advance_frame()
    
    def advance_frame(self):
        """Advances to next animation frame."""
        sequence = self.sequences[self.current_state]
        self.frame_index += 1
        
        if self.frame_index >= len(sequence):
            if self.looping_states[self.current_state]:
                self.frame_index = 0
            else:
                # Non-looping animation finished, return to previous state
                self.transition_to(self.previous_state)
    
    def transition_to(self, new_state):
        """Transitions to a new animation state."""
        if new_state == self.current_state:
            return
        
        # FLINCH always interrupts current animation
        if new_state == AnimationState.FLINCH:
            self.previous_state = self.current_state
        elif not self.looping_states[self.current_state]:
            # Don't interrupt non-looping animations unless flinching
            return
        
        self.current_state = new_state
        self.frame_index = 0
        self.frame_timer = 0
        self.state_timer = 0
    
    def get_current_frame(self):
        """Returns the current sprite frame to display."""
        sprite_set = self.entity.sprite_set
        if sprite_set is None:
            return None
        
        sequence = self.sequences[self.current_state]
        if self.frame_index >= len(sequence):
            return sprite_set['base']
        
        frame_descriptor = sequence[self.frame_index]
        
        # Frame descriptor format: 'base' or ('animation_name', frame_number)
        if frame_descriptor == 'base':
            return sprite_set['base']
        
        # Get animation type and frame number
        animation_type = sequence[self.frame_index]
        frame_num = sequence[self.frame_index + 1] if self.frame_index + 1 < len(sequence) else 0
        
        # Handle tuple-style descriptors
        if isinstance(frame_descriptor, tuple):
            animation_type, frame_num = frame_descriptor
        
        return sprite_set[animation_type][frame_num]
```

### Entity-Specific Animation Triggers

Enhanced entity classes trigger appropriate animations:

```python
class Minion(Entity):
    def move(self, dx, dy):
        """Enhanced move with animation trigger."""
        moved = super(Minion, self).move(dx, dy)
        
        if moved and hasattr(self, 'sprite_animator'):
            self.sprite_animator.transition_to(AnimationState.WALKING)
            self.last_direction = dx
        
        return moved
    
    def try_attack(self):
        """Enhanced attack with animation trigger."""
        enemy = self.enemy_reachable()
        
        if enemy and hasattr(self, 'sprite_animator'):
            self.sprite_animator.transition_to(AnimationState.ATTACKING)
        
        if enemy:
            enemy.get_attacked(self)
        
        return enemy != None
    
    def get_attacked(self, enemy, power=None, attack_effect=None, attack_type=None):
        """Enhanced damage reception with flinch animation."""
        # Trigger flinch animation before applying damage
        if hasattr(self, 'sprite_animator'):
            self.sprite_animator.transition_to(AnimationState.FLINCH)
        
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
            enemy.register_kill(self)
```

### Effect Sprite Animations

Effects use a simplified animation system optimized for visual effects:

```python
class Effect(Entity):
    def __init__(self, battleground, side, x, y, char, color):
        super(Effect, self).__init__(battleground, side, x, y, char, color)
        
        # Effects use frame-based animation sequences
        self.effect_animator = EffectAnimator(self)
    
    def draw_sprite(self, console, sprite_manager):
        """Effects render full animation sequences."""
        sprite = self.effect_animator.get_current_frame()
        
        if sprite is None:
            return False
        
        pixel_x = self.x * TILE_WIDTH
        pixel_y = self.y * TILE_HEIGHT
        
        # Effects render centered with potential scaling
        console.draw_sprite(sprite, pixel_x, pixel_y, 
                          alpha=self.effect_animator.get_alpha())
        return True

class EffectAnimator:
    def __init__(self, effect):
        self.effect = effect
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_duration = 2  # Faster than entity animations
    
    def get_current_frame(self):
        """Returns current effect sprite frame."""
        effect_name = self.effect.__class__.__name__.lower()
        sprite_set = sprite_manager.load_effect_sprites(effect_name)
        
        if sprite_set is None or len(sprite_set) == 0:
            return None
        
        return sprite_set[self.frame_index % len(sprite_set)]
    
    def get_alpha(self):
        """Returns alpha transparency for fade effects."""
        if hasattr(self.effect, 'duration'):
            # Fade out in last 25% of duration
            fade_threshold = self.effect.duration * 0.25
            if self.effect.duration < fade_threshold:
                return self.effect.duration / fade_threshold
        return 1.0
```

## Audio System

### Sound Effect Management

```python
class AudioManager:
    def __init__(self):
        self.sound_cache = {}
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.enabled = True
        
        # Initialize audio system (pygame.mixer or similar)
        self.init_audio()
    
    def load_sound(self, sound_name):
        """Loads and caches sound effects."""
        if sound_name in self.sound_cache:
            return self.sound_cache[sound_name]
        
        sound_path = f"audio/sfx/{sound_name}.ogg"
        try:
            sound = self.load_audio_file(sound_path)
            self.sound_cache[sound_name] = sound
            return sound
        except FileNotFoundError:
            return None
    
    def play_sound(self, sound_name, volume_modifier=1.0):
        """Plays a sound effect with volume control."""
        if not self.enabled:
            return
        
        sound = self.load_sound(sound_name)
        if sound:
            sound.set_volume(self.sfx_volume * volume_modifier)
            sound.play()
```

### Audio Event Integration

```python
class Minion(Entity):
    def move(self, dx, dy):
        moved = super(Minion, self).move(dx, dy)
        
        if moved:
            if hasattr(self, 'sprite_animator'):
                self.sprite_animator.transition_to(AnimationState.WALKING)
            # Play footstep sound
            audio_manager.play_sound('footstep', 0.3)
        
        return moved
    
    def try_attack(self):
        enemy = self.enemy_reachable()
        
        if enemy:
            if hasattr(self, 'sprite_animator'):
                self.sprite_animator.transition_to(AnimationState.ATTACKING)
            
            # Play attack sound based on type
            if isinstance(self, RangedMinion):
                audio_manager.play_sound('arrow_shot')
            else:
                audio_manager.play_sound('sword_swing')
            
            enemy.get_attacked(self)
        
        return enemy != None
    
    def get_attacked(self, enemy, power=None, attack_effect=None, attack_type=None):
        # Play hit sound before damage
        if power and power > 0:
            audio_manager.play_sound('hit_impact')
        
        # Existing damage logic
        # ...
        
        if self.hp <= 0:
            audio_manager.play_sound('unit_death')
```

### Sound Effect Catalog

```
audio/
├── sfx/
│   ├── footstep.ogg           # Walking sound
│   ├── sword_swing.ogg        # Melee attack
│   ├── arrow_shot.ogg         # Ranged attack
│   ├── hit_impact.ogg         # Taking damage
│   ├── unit_death.ogg         # Unit dies
│   ├── skill_cast.ogg         # Skill activation
│   ├── explosion.ogg          # Explosion effect
│   ├── thunder.ogg            # Lightning effect
│   ├── teleport.ogg           # Teleportation
│   ├── heal.ogg               # Healing effect
│   ├── buff.ogg               # Buff applied
│   ├── debuff.ogg             # Debuff applied
│   └── victory.ogg            # Battle won
└── music/
    ├── battle_theme.ogg       # Main battle music
    ├── menu_theme.ogg         # Menu music
    └── victory_theme.ogg      # Victory music
```

### Skill-Specific Audio

```python
class Skill:
    def use(self, x, y):
        """Enhanced skill use with audio feedback."""
        result = self.original_use(x, y)
        
        if result and audio_manager:
            # Play skill-specific sound
            skill_sound = self.get_skill_sound()
            if skill_sound:
                audio_manager.play_sound(skill_sound)
        
        return result
    
    def get_skill_sound(self):
        """Returns appropriate sound effect for this skill."""
        skill_name = self.quote.lower()
        
        # Map skill types to sounds
        if 'thunder' in skill_name or 'lightning' in skill_name:
            return 'thunder'
        elif 'heal' in skill_name:
            return 'heal'
        elif 'teleport' in skill_name or 'jaunt' in skill_name:
            return 'teleport'
        elif 'explosion' in skill_name or 'blast' in skill_name:
            return 'explosion'
        else:
            return 'skill_cast'
```

## Performance Optimization

### Sprite Batching

```python
class SpriteBatcher:
    def __init__(self):
        self.batch = []
        self.max_batch_size = 1000
    
    def add_sprite(self, sprite, x, y, mirror=False, alpha=1.0):
        """Adds sprite to batch for efficient rendering."""
        self.batch.append({
            'sprite': sprite,
            'x': x,
            'y': y,
            'mirror': mirror,
            'alpha': alpha
        })
        
        if len(self.batch) >= self.max_batch_size:
            self.flush()
    
    def flush(self):
        """Renders all batched sprites at once."""
        if not self.batch:
            return
        
        # Sort by texture for optimal GPU usage
        self.batch.sort(key=lambda s: id(s['sprite']))
        
        # Render all sprites in one draw call
        for sprite_data in self.batch:
            self.render_sprite(**sprite_data)
        
        self.batch.clear()
```

### Viewport Culling

```python
class Battleground:
    def draw(self, con, camera_x=0, camera_y=0, viewport_width=60, viewport_height=43):
        """Enhanced draw with viewport culling."""
        # Only draw entities within viewport
        min_x = camera_x
        max_x = camera_x + viewport_width
        min_y = camera_y
        max_y = camera_y + viewport_height
        
        visible_entities = []
        for entity in self.all_entities():
            if min_x <= entity.x < max_x and min_y <= entity.y < max_y:
                visible_entities.append(entity)
        
        # Draw only visible entities
        for entity in visible_entities:
            if self.use_sprites:
                if not entity.draw_sprite(con, self.sprite_manager):
                    entity.draw_ascii(con)
            else:
                entity.draw_ascii(con)
```

## Configuration and Settings

### Visual Settings

```python
class VisualSettings:
    def __init__(self):
        self.use_sprites = True
        self.sprite_quality = 'high'  # 'low', 'medium', 'high'
        self.animation_speed = 1.0
        self.use_sprite_effects = True
        self.screen_shake_enabled = True
        
    def save(self):
        """Saves settings to configuration file."""
        config = {
            'use_sprites': self.use_sprites,
            'sprite_quality': self.sprite_quality,
            'animation_speed': self.animation_speed,
            'use_sprite_effects': self.use_sprite_effects,
            'screen_shake': self.screen_shake_enabled
        }
        
        with open('config/visual_settings.json', 'w') as f:
            json.dump(config, f, indent=2)
    
    def load(self):
        """Loads settings from configuration file."""
        try:
            with open('config/visual_settings.json', 'r') as f:
                config = json.load(f)
                self.use_sprites = config.get('use_sprites', True)
                self.sprite_quality = config.get('sprite_quality', 'high')
                self.animation_speed = config.get('animation_speed', 1.0)
                self.use_sprite_effects = config.get('use_sprite_effects', True)
                self.screen_shake_enabled = config.get('screen_shake', True)
        except FileNotFoundError:
            # Use defaults
            pass

class AudioSettings:
    def __init__(self):
        self.master_volume = 0.8
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.enabled = True
    
    def save(self):
        """Saves audio settings to configuration file."""
        config = {
            'master_volume': self.master_volume,
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume,
            'enabled': self.enabled
        }
        
        with open('config/audio_settings.json', 'w') as f:
            json.dump(config, f, indent=2)
    
    def load(self):
        """Loads audio settings from configuration file."""
        try:
            with open('config/audio_settings.json', 'r') as f:
                config = json.load(f)
                self.master_volume = config.get('master_volume', 0.8)
                self.music_volume = config.get('music_volume', 0.7)
                self.sfx_volume = config.get('sfx_volume', 0.8)
                self.enabled = config.get('enabled', True)
        except FileNotFoundError:
            pass
```

## Implementation Notes

### Sprite Creation Guidelines

1. **Resolution**: All sprites should be 32x32 pixels at base size
2. **Format**: PNG with alpha transparency
3. **Style**: Consistent pixel art style matching game aesthetic
4. **Color Palette**: Limited palette for retro look (16-32 colors recommended)
5. **Animation Frames**: Keep frame count low (2-3 per animation) for smooth retro feel
6. **Facing Direction**: All sprites face right by default
7. **Centering**: Character sprites should be centered in frame with consistent ground level

### Audio Guidelines

1. **Format**: OGG Vorbis for cross-platform compatibility
2. **Sample Rate**: 44.1kHz for sound effects, 44.1kHz-48kHz for music
3. **Bit Depth**: 16-bit for effects, 16-24 bit for music
4. **Duration**: Sound effects should be 0.1-2 seconds, music can be longer with loops
5. **Normalization**: All audio should be normalized to prevent clipping
6. **Style**: 8-bit/16-bit style effects to match retro aesthetic

### Backward Compatibility

The system maintains full backward compatibility:
- ASCII rendering remains as fallback for all entities
- Game logic is completely unchanged
- All existing gameplay mechanics function identically
- Sprites can be added incrementally without breaking existing functionality
- Settings allow complete disabling of sprite system

### Performance Targets

- Maintain 60 FPS with full sprite animations
- Memory usage should not exceed 256MB for all sprites
- Load times should remain under 2 seconds
- Audio latency should be under 50ms

## Testing Scenarios

1. **Full Sprite Coverage**: All entities have complete sprite sets
2. **Partial Coverage**: Mix of sprite and ASCII entities
3. **No Sprites**: Complete ASCII fallback mode
4. **Performance**: 100+ animated entities on screen simultaneously
5. **Audio Sync**: Verify sound effects match visual actions
6. **Memory**: Load/unload test for sprite caching efficiency
7. **Configuration**: Test all setting combinations
8. **Compatibility**: Verify ASCII mode matches original appearance exactly