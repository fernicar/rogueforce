from __future__ import annotations
from concepts import ENTITY_DEFAULT
from rendering.animation import Animation
from assets.asset_loader import asset_loader
import cmath as math
from typing import List, Tuple, Optional, Any, Iterator, TYPE_CHECKING, cast
import pygame

if TYPE_CHECKING:
    from battleground import Battleground, Tile
    from status import Status
    from general import General
    from minion import Minion

NEUTRAL_SIDE = 555

class Entity(object):
    """Base class for all entities in the game.

    An Entity represents any object that can exist on the battleground grid.
    This includes units, buildings, projectiles, and other interactive objects.

    Attributes:
        bg: The battleground this entity is currently on
        x: Current x position on the grid
        y: Current y position on the grid
        side: Team/faction identifier for the entity
        sprite_name: Name of the sprite for this entity
        character_name: Display name for the character
        color: Current color of the entity
        alive: Whether the entity is still alive
        statuses: List of status effects affecting this entity
        animation: Animation object for sprite management
        name: Display name (added by subclasses)
        hp: Health points (added by subclasses)
        max_hp: Maximum health points (added by subclasses)
        power: Attack/damage power (added by subclasses)
        minion: Associated minion (added by General subclass)
    """
    
    def __init__(
        self, 
        battleground: 'Battleground', 
        side: int = NEUTRAL_SIDE, 
        x: int = -1, 
        y: int = -1, 
        sprite_name: str = ' ', 
        character_name: Optional[str] = None, 
        color: Tuple[int, int, int] = ENTITY_DEFAULT
    ) -> None:
        """Initialize an Entity.
        
        Args:
            battleground: The battleground grid this entity belongs to
            side: Team/faction identifier (default: NEUTRAL_SIDE)
            x: X position on the grid (default: -1)
            y: Y position on the grid (default: -1)
            sprite_name: Name of the sprite file (default: ' ')
            character_name: Display name for the character (default: sprite_name)
            color: RGB color tuple (default: ENTITY_DEFAULT)
        """
        self.bg = battleground
        self.x = x
        self.y = y
        self.side = side
        self.sprite_name = sprite_name
        self.char = sprite_name # The old 'char' is now the sprite_name
        self.character_name = character_name if character_name else self.char
        self.original_char = self.char # Keep original for reference
        self.original_sprite_name = sprite_name
        self.color = color
        self.original_color = color
        self.bg.tiles[(x, y)].entity = self
        self.default_next_action = 5
        self.next_action = self.default_next_action
        self.pushed = False
        self.alive = True
        self.statuses: List['Status'] = []
        self.path: List['Tile'] = []
        self.attack_effect = None
        self.attack_type = "physical"
        self.kills = 0
        self.owner: Optional['Entity'] = None
        self.animation: Optional['Animation'] = None # Defer sprite loading until pygame is initialized

        # Attributes added by subclasses (declared here for type checking)
        self.name: Optional[str] = None
        self.hp: Optional[int] = None
        self.max_hp: Optional[int] = None
        self.power: Optional[int] = None
        self.minion: Optional['Minion'] = None
        
        # Horizontal mirroring state
        self.mirrored = False
        self.last_direction = 1 # 1 for right, -1 for left, 0 for stationary
        
        # Check initial spawn position for mirroring (case A: spawning on the right)
        if self.bg and hasattr(self.bg, 'width'):
            # If spawning on the right half of the arena, mirror the character
            if self.x >= self.bg.width // 2:
                self.mirrored = True
                self.last_direction = -1

    def load_sprites(self) -> None:
        """Load sprites after pygame display is initialized"""
        if self.character_name and not self.animation:
            try:
                sprites = asset_loader.get_character_sprites(self.character_name)
                self.animation = Animation(sprites)
            except Exception as e:
                print(f"[SPRITE WARNING] Failed to load sprites for {self.character_name}: {e}")
                self.animation = None

    def can_be_attacked(self) -> bool:
        return False

    def get_attacked(self, attacker: 'Entity', damage: int = 0, effect: Optional[Any] = None, damage_type: str = "physical") -> None:
        """Handle being attacked by another entity.

        Args:
            attacker: The entity attacking this one
            damage: Amount of damage dealt
            effect: Special effect applied
            damage_type: Type of damage ("physical", "magical", etc.)
        """
        pass  # Override in subclasses that can be attacked
    
    def can_be_pushed(self, dx: int, dy: int) -> bool:
        next_tile = self.bg.tiles[(self.x+dx, self.y+dy)]
        return next_tile.is_passable(self) and (next_tile.entity is None or next_tile.entity.can_be_pushed(dx, dy))
    
    def can_move(self, dx: int, dy: int) -> bool:
        next_tile = self.bg.tiles[(self.x+dx, self.y+dy)]
        if not next_tile.is_passable(self): return False
        if next_tile.entity is None: return True
        if not next_tile.entity.is_ally(self): return False
        return next_tile.entity.can_be_pushed(dx, dy)

    def change_battleground(self, bg: Battleground, x: int, y: int) -> None:
        self.bg.tiles[(self.x, self.y)].entity = None
        self.bg = bg
        (self.x, self.y) = (x, y)
        self.bg.tiles[(self.x, self.y)].entity = self
        
        # Update mirroring based on new position (case A: spawning on right)
        if self.x >= self.bg.width // 2:
            self.mirrored = True
            self.last_direction = -1
        else:
            self.mirrored = False
            self.last_direction = 1

    def clone(self, x: int, y: int) -> Optional[Entity]: 
        if self.bg.is_inside(x, y) and self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
            cloned = self.__class__(self.bg, self.side, x, y, self.sprite_name, self.character_name, self.original_color)
            # Preserve mirroring state in clone
            cloned.mirrored = self.mirrored
            cloned.last_direction = self.last_direction
            return cloned
        return None

    def die(self) -> None:
        self.bg.tiles[(self.x, self.y)].entity = None
        self.alive = False
    
    def get_passable_neighbours(self) -> Iterator[Tuple[int, int]]:
        neighbours = [(self.x+i, self.y+j) for i in range(-1,2) for j in range(-1,2)] 
        return filter(lambda t: self.bg.tiles[t].passable and t != (self.x, self.y), neighbours)

    def get_pushed(self, dx: int, dy: int) -> None:
        self.pushed = False
        self.move(dx, dy)
        self.pushed = True
   
    def is_ally(self, entity: Entity) -> bool:
        return self.side == entity.side

    def move(self, dx: int, dy: int) -> bool:
        if self.pushed:
            self.pushed = False
            return False
        (dx,dy) = (int(dx), int(dy))
        next_tile = self.bg.tiles[(self.x+dx, self.y+dy)]
        if self.can_move(dx, dy):
            if next_tile.entity is not None:
                next_tile.entity.get_pushed(dx, dy)
            self.bg.tiles[(self.x, self.y)].entity = None
            next_tile.entity = self
            self.x += dx
            self.y += dy
            
            # Track movement direction and update mirroring (case B: walking left/right)
            if dx != 0:  # Only track horizontal movement
                self.last_direction = 1 if dx > 0 else -1
                # Mirror when walking left, un-mirror when walking right
                if self.last_direction == -1:
                    self.mirrored = True
                else:
                    self.mirrored = False
            
            if self.animation: self.animation.set_state('walk')
            return True
        return False

    def move_path(self) -> bool:
        if self.path:
            next_tile = self.path.pop(0)
            if self.move(next_tile.x - self.x, next_tile.y - self.y):
                return True
            else:
                self.path.insert(0, next_tile)
        elif self.animation and self.animation.current_state == 'walk':
            self.animation.set_state('idle')
        return False

    def register_kill(self, killed: Entity) -> None:
        self.kills += 1
        if self.owner:
            self.owner.kills += 1

    def reset_action(self) -> None:
        self.next_action = self.default_next_action

    def teleport(self, x: int, y: int) -> bool:
        if self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
            self.bg.tiles[(x, y)].entity = self
            self.bg.tiles[(self.x, self.y)].entity = None
            (self.x, self.y) = (x, y)
            
            # Update mirroring based on new position (case A: spawning on right)
            if self.x >= self.bg.width // 2:
                self.mirrored = True
                self.last_direction = -1
            else:
                self.mirrored = False
                self.last_direction = 1
            
            return True
        return False

    def update(self) -> None:
        for s in self.statuses:
            s.update()
        if self.animation:
            self.animation.update()

class BigEntity(Entity):
    def __init__(self, battleground: Battleground, side: int, x: int, y: int, sprite_names: List[str] = ["a", "b", "c", "d"], colors: Optional[List[Tuple[int, int, int]]] = None) -> None:
        if colors is None:
            colors = cast(List[Tuple[int, int, int]], [ENTITY_DEFAULT]*4)
        super(BigEntity, self).__init__(battleground, side, x, y, sprite_names[0], None, colors[0])
        self.sprite_names = sprite_names
        self.colors = colors
        self.length = int(math.sqrt(len(self.sprite_names)).real)
        self.update_body()
    
    def can_be_pushed(self, dx: int, dy: int) -> bool:
        return False

    def can_move(self, dx: int, dy: int) -> bool:
        for (x,y) in [(self.x+dx+x,self.y+dy+y) for x in range (0, self.length) for y in range (0, self.length)]:
            next_tile = self.bg.tiles[(x, y)]
            if not next_tile.is_passable(self): return False
            if next_tile.entity is None: continue
            if not next_tile.entity.is_ally(self): return False
            if next_tile.entity is self: continue
            if not next_tile.entity.can_be_pushed(dx, dy): return False
        return True

    def clear_body(self) -> None:
        for i in range(self.length):
            for j in range(self.length):
                self.bg.tiles[(self.x+i, self.y+j)].entity = None
        
    def die(self) -> None:
        self.clear_body()
        self.alive = False
        
    def move(self, dx: int, dy: int) -> None:
        if self.pushed:
            self.pushed = False
            return
        next_tile = self.bg.tiles[(self.x+dx, self.y+dy)]
        if self.can_move(dx, dy):
            if next_tile.entity is not None and next_tile.entity is not self:
                next_tile.entity.get_pushed(dx, dy)
            self.clear_body()
            next_tile.entity = self
            self.x += dx
            self.y += dy
            
            # Track movement direction and update mirroring for BigEntity too
            if dx != 0: # Only track horizontal movement
                self.last_direction = 1 if dx > 0 else -1
                # Mirror when walking left, un-mirror when walking right
                if self.last_direction == -1:
                    self.mirrored = True
                else:
                    self.mirrored = False
            
            self.update_body()

    def update_body(self) -> None:
        for i in range(self.length):
            for j in range(self.length):
                self.bg.tiles[(self.x+i, self.y+j)].entity = self
            
class Fortress(BigEntity):
    def __init__(self, battleground: Battleground, side: int = NEUTRAL_SIDE, x: int = -1, y: int = -1, sprite_names: Optional[List[str]] = None, colors: Optional[List[Tuple[int, int, int]]] = None, requisition_production: int = 1) -> None:
        if sprite_names is None:
            sprite_names = [':']*4
        if colors is None:
            colors = cast(List[Tuple[int, int, int]], [ENTITY_DEFAULT]*4)
        super(Fortress, self).__init__(battleground, side, x, y, sprite_names, colors)
        self.capacity = len(sprite_names)
        self.connected_fortresses: List[Tuple[Fortress, Tuple[int, int]]] = []
        self.guests: List[Entity] = []
        self.name = "Fortress"
        self.requisition_production = requisition_production

    def can_be_attacked(self) -> bool:
        return True

    def can_host(self, entity: Entity) -> bool:
        return self.side == entity.side or self.side == NEUTRAL_SIDE

    def can_move(self, dx: int, dy: int) -> bool:
        return False

    def get_connections(self) -> None:
        starting_tiles = [(self.x+i, self.y+j) for i in range(-1,3) for j in range(-1,3)] 
        checked = [(self.x+i, self.y+j) for i in range(0,2) for j in range(0,2)]
        starting_tiles = filter(lambda t: self.bg.tiles[t].passable and t not in checked, starting_tiles)
        for starting in starting_tiles:
            tiles = [starting]
            while tiles:
                (x, y) = tiles.pop()
                checked.append((x, y))
                for t in [(x+i, y+j) for i in range(-1,2) for j in range(-1,2)]:
                    entity = self.bg.tiles[t].entity
                    if entity in self.bg.fortresses and entity is not self and entity not in [f for f, _ in self.connected_fortresses]:
                        self.connected_fortresses.append((cast(Fortress, entity), starting))
                    if self.bg.tiles[t].passable and t not in checked:
                        tiles.append(t)

    def host(self, entity: Entity) -> None:
        if not self.can_host(entity) or len(self.guests) >= self.capacity: return
        if not self.guests:
            self.side = entity.side
        self.bg.tiles[(entity.x, entity.y)].entity = None
        (entity.x, entity.y) = (self.x, self.y)
        self.bg.generals.remove(cast(General, entity))
        self.sprite_names[len(self.guests)] = entity.sprite_name
        self.colors[len(self.guests)] = cast(Tuple[int, int, int], entity.color)
        self.guests.append(entity)
        self.update_body()

    def refresh_chars(self) -> None:
        self.sprite_names = [':' for _ in range(len(self.sprite_names))]
        self.colors = cast(List[Tuple[int, int, int]], [ENTITY_DEFAULT for _ in range(len(self.colors))])
        for i in range(len(self.guests)):
            self.sprite_names[i] = self.guests[i].sprite_name
            self.colors[i] = cast(Tuple[int, int, int], self.guests[i].color)

    def unhost(self, entity: Entity) -> None:
        self.guests.remove(entity)
        self.bg.generals.append(cast(General, entity))
        self.refresh_chars()
        if not self.guests:
            self.side = NEUTRAL_SIDE

class Mine(Entity):
    def __init__(self, battleground: Battleground, x: int = -1, y: int = -1, power: int = 50) -> None:
        super(Mine, self).__init__(battleground, NEUTRAL_SIDE, x, y, sprite_name='X', color=ENTITY_DEFAULT)
        self.power = power

    def can_be_attacked(self) -> bool:
        return True

    def clone(self, x: int, y: int) -> Optional[Mine]:
        if self.bg.is_inside(x, y) and self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
            return self.__class__(self.bg, x, y, cast(int, self.power))
        return None

    def get_attacked(self, attacker: Entity) -> None:
        if attacker.can_be_attacked():
            attacker.get_attacked(self)
        self.die()
