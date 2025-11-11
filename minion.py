from __future__ import annotations
from typing import Optional, List, Any, Dict, Tuple, TYPE_CHECKING, cast
from collections import defaultdict

from entity import Entity, BigEntity
import concepts
import effect
import tactic

if TYPE_CHECKING:
    from battleground import Battleground

class Minion(Entity):
    """A basic combat unit in the game.
    
    Minions are the primary combat units that can attack enemies,
    move around the battlefield, and follow tactical instructions.
    
    Attributes:
        name: The name of this minion type
        max_hp: Maximum health points
        hp: Current health points
        armor: Dictionary of armor types and values
        power: Basic attack power
        tactic: Current tactical behavior function
        attack_effect: Visual effect for attacks
    """
    
    def __init__(
        self, 
        battleground: Battleground, 
        side: int, 
        x: int = -1, 
        y: int = -1, 
        name: str = "minion", 
        character_name: Optional[str] = None, 
        color: Tuple[int, int, int] = concepts.UI_TEXT, 
        sprite_name: Optional[str] = None
    ) -> None:
        """Initialize a Minion.
        
        Args:
            battleground: The battleground this minion belongs to
            side: Team/faction identifier
            x: X position on the grid (default: -1)
            y: Y position on the grid (default: -1)
            name: Name of this minion type
            character_name: Display name (defaults to name)
            color: RGB color tuple
            sprite_name: Sprite file name (defaults to 'm')
        """
        super(Minion, self).__init__(
            battleground, side, x, y, 
            'm' if not sprite_name else sprite_name, 
            character_name if character_name else name, 
            color
        )
        self.name = name
        self.max_hp = 30
        self.hp = 30
        self.armor: Dict[str, int] = defaultdict(lambda: 0)
        self.power = 5
        self.tactic = tactic.null
        self.attack_effect = effect.TempEffect(self.bg, character_name='/' if side else '\\')

    def can_be_attacked(self) -> bool:
        """Check if this minion can be attacked.
        
        Returns:
            True - minions can always be attacked
        """
        return True

    def clone(self, x: int, y: int) -> Optional[Minion]:
        """Create a clone of this minion at a new position.
        
        Args:
            x: Target x position
            y: Target y position
            
        Returns:
            New minion instance if position is valid, None otherwise
        """
        if self.bg.is_inside(x, y) and self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
            return self.__class__(self.bg, self.side, x, y, cast(str, self.name), self.character_name, self.original_color)
        return None

    def die(self) -> None:
        """Handle minion death and update battleground statistics."""
        super(Minion, self).die()
        if self in self.bg.minions:
            self.bg.generals[self.side].minions_alive -= 1

    def enemy_reachable(self, diagonals: bool = False) -> Optional[Entity]:
        """Find the first enemy in reachable positions.
        
        Args:
            diagonals: Whether to check diagonal positions
            
        Returns:
            First enemy entity found, or None if no enemies reachable
        """
        order = [(1, 0), (-1, 0), (0, -1), (0, 1)]
        if diagonals:
            order.extend([(1, -1), (1, 1), (-1, -1), (-1, 1)])
        for (i, j) in order:
            enemy = self.bg.tiles[(self.x + (-i if self.side else i), self.y + j)].entity
            if enemy and not self.is_ally(enemy) and enemy.can_be_attacked():
                return enemy
        return None
 
    def follow_tactic(self) -> None:
        """Execute the current tactical behavior."""
        self.tactic(self)

    def get_attacked(
        self,
        enemy: Entity,
        power: Optional[int] = None,
        attack_effect: Optional[Any] = None,
        attack_type: Optional[str] = None
    ) -> None:
        """Handle being attacked by an enemy.

        Args:
            enemy: The attacking entity
            power: Attack power (defaults to enemy.power)
            attack_effect: Visual effect (defaults to enemy.attack_effect)
            attack_type: Type of attack (defaults to enemy.attack_type)
        """
        if power is None:
            power = getattr(enemy, 'power', 0)
        if power is None:
            power = 0
        if attack_effect is None:
            attack_effect = getattr(enemy, 'attack_effect', None)
        if attack_type is None:
            attack_type = getattr(enemy, 'attack_type', 'physical')
        if attack_type is None:
            attack_type = 'physical'
        if self.hp is None:
            self.hp = 0
        self.hp -= max(0, power - self.armor[attack_type])
        if attack_effect:
            attack_effect.clone(self.x, self.y)
        if self.hp > 0:
            self.update_color()
        else:
            self.hp = 0
            self.die()
            enemy.register_kill(self)

    def get_healed(self, amount: int) -> None:
        """Heal this minion by a specified amount.

        Args:
            amount: Amount of health to restore
        """
        if self.hp is not None:
            self.hp += amount
            if self.max_hp is not None and self.hp > self.max_hp:
                self.hp = self.max_hp
            self.update_color()

    def try_attack(self) -> bool:
        """Attempt to attack an adjacent enemy.
        
        Returns:
            True if an attack was made, False otherwise
        """
        enemy = self.enemy_reachable()
        if enemy:
            enemy.get_attacked(self)
        return enemy is not None
            
    def update(self) -> None:
        """Update the minion's state and actions."""
        if not self.alive: 
            return
        # First, let the parent Entity class handle status effects and animation
        super(Minion, self).update() 
        
        # Now, restore the core action logic
        if self.next_action <= 0:
            self.reset_action()
            if not self.try_attack():
                self.follow_tactic()
        else: 
            self.next_action -= 1

    def update_color(self) -> None:
        """Update the minion's color based on current health.

        The color changes to red as health decreases, providing
        a visual indicator of the minion's condition.
        """
        if self.hp is not None and self.max_hp is not None and self.max_hp > 0:
            c = int(255 * (float(self.hp) / self.max_hp))
            self.color = (255, c, c) # Changed from libtcod.Color to pygame tuple
        else:
            self.color = (255, 0, 0) # Changed from libtcod.Color to pygame tuple


class BigMinion(BigEntity, Minion):
    """A larger minion that occupies multiple grid spaces.
    
    BigMinions are larger units that take up a 2x2 grid space
    and have increased health based on their size.
    
    Attributes:
        name: The name of this big minion type
        max_hp: Maximum health points (scaled by size)
        hp: Current health points
        power: Basic attack power
        length: Size of the minion (grid dimension)
    """
    
    def __init__(
        self, 
        battleground: Battleground, 
        side: int, 
        x: int = -1, 
        y: int = -1, 
        name: str = "Giant", 
        chars: List[str] = ['G'] * 4, 
        colors: List[Tuple[int, int, int]] = [concepts.UI_TEXT] * 4
    ) -> None:
        """Initialize a BigMinion.
        
        Args:
            battleground: The battleground this minion belongs to
            side: Team/faction identifier
            x: X position on the grid (default: -1)
            y: Y position on the grid (default: -1)
            name: Name of this big minion type
            chars: List of sprite characters for the 2x2 grid
            colors: List of colors for each grid position
        """
        BigEntity.__init__(self, battleground, side, x, y, sprite_names=chars, colors=colors)
        Minion.__init__(self, battleground, side, x, y, name, name, colors[0])
        if self.max_hp is not None:
            self.max_hp *= self.length
        self.hp = self.max_hp
        
    def clone(self, x: int, y: int) -> Optional[BigMinion]:
        """Create a clone of this big minion at a new position.
        
        Args:
            x: Target x position
            y: Target y position
            
        Returns:
            New big minion instance if position is valid, None otherwise
        """
        for (pos_x, pos_y) in [(x+i, y+j) for i in range(0, self.length) for j in range(0, self.length)]:
            if not self.bg.is_inside(pos_x, pos_y) or self.bg.tiles[(pos_x, pos_y)].entity is not None or not self.bg.tiles[(x, y)].is_passable(self):
                return None
        entity = self.__class__(self.bg, self.side, x, y, cast(str, self.name), self.sprite_names, self.colors)
        entity.update_body()
        return entity

    def enemy_reachable(self) -> Optional[Entity]:
        """Find the first enemy in reachable positions for a big minion.
        
        Returns:
            First enemy entity found, or None if no enemies reachable
        """
        for (dx, dy) in [(1 if self.side == 0 else -1, 0), (1 if self.side == 0 else -1, 0), (0, 1), (0, -1)]:
            for (x,y) in [(self.x+dx+x,self.y+dy+y) for x in range(0, self.length) for y in range(0, self.length)]:
                enemy = self.bg.tiles[(x, y)].entity
                if enemy is not None and not self.is_ally(enemy) and enemy.can_be_attacked():
                    return enemy
        return None


class RangedMinion(Minion):
    """A minion that can attack from a distance using projectiles.
    
    RangedMinions have lower health but can attack enemies
    from a distance without moving into adjacent positions.
    
    Attributes:
        name: The name of this ranged minion type
        max_hp: Maximum health points
        hp: Current health points
        power: Basic melee attack power
        ranged_power: Projectile attack power
        attack_effects: Visual effects for projectiles
        default_next_action: Action delay for ranged attacks
    """
    
    def __init__(
        self, 
        battleground: Battleground, 
        side: int, 
        x: int = -1, 
        y: int = -1, 
        name: str = "archer", 
        character_name: Optional[str] = None, 
        color: Tuple[int, int, int] = concepts.UI_TEXT, 
        attack_effects: List[str] = ['>', '<']
    ) -> None:
        """Initialize a RangedMinion.
        
        Args:
            battleground: The battleground this minion belongs to
            side: Team/faction identifier
            x: X position on the grid (default: -1)
            y: Y position on the grid (default: -1)
            name: Name of this ranged minion type
            character_name: Display name (defaults to name)
            color: RGB color tuple
            attack_effects: Visual effects for projectile attacks
        """
        super(RangedMinion, self).__init__(battleground, side, x, y, name, character_name, color)
        self.max_hp = 10
        self.hp = 10
        self.power = 1
        self.ranged_power = 4
        self.attack_effects = attack_effects
        self.default_next_action = 10
        self.reset_action()

    def clone(self, x: int, y: int) -> Optional[RangedMinion]:
        """Create a clone of this ranged minion at a new position.
        
        Args:
            x: Target x position
            y: Target y position
            
        Returns:
            New ranged minion instance if position is valid, None otherwise
        """
        if self.bg.is_inside(x, y) and self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
            return self.__class__(self.bg, self.side, x, y, cast(str, self.name), self.character_name, self.original_color, self.attack_effects)
        return None

    def follow_tactic(self) -> None:
        """Execute the current tactical behavior for a ranged minion.
        
        Special handling for 'stop' tactic to fire projectiles
        when enemies are not in melee range.
        """
        if self.tactic is None: 
            return
        next_x = self.x+1 if self.side == 0 else self.x-1
        if self.tactic == tactic.stop and self.bg.tiles[(next_x, self.y)].entity == None:
            self.bg.effects.append(effect.Arrow(self.bg, self.side, next_x, self.y, self.ranged_power, self.attack_effects))
        else: 
            super(RangedMinion, self).follow_tactic()
