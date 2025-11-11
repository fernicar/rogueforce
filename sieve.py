from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional, TYPE_CHECKING
import area

if TYPE_CHECKING:
    from general import General
    from battleground import Tile

@dataclass
class Sieve:
    """A filter for selecting tiles based on custom criteria.

    A Sieve combines a general and a filtering function to determine
    which tiles meet specific conditions for skill targeting or movement.

    Attributes:
        general: The general this sieve belongs to (can be None)
        function: The filtering function that takes (general, tile) and returns bool
    """
    general: Optional['General']
    function: Callable[[Optional['General'], 'Tile'], bool]

    def apply(self, tile: 'Tile') -> bool:
        """Apply the sieve function to a tile.

        Args:
                tile: The tile to test

        Returns:
                True if the tile passes the filter, False otherwise
        """
        return self.function(self.general, tile)

def is_adjacent(general: Optional['General'], tile: 'Tile') -> bool:
    if general is None:
        return False
    return abs(tile.x - general.x) <= 1 and abs(tile.y - general.y) <= 1

def is_ally(general: Optional['General'], tile: 'Tile') -> bool:
    if general is None:
        return False
    return tile.entity is not None and tile.entity.is_ally(general)

def is_ally_general(general: Optional['General'], tile: 'Tile') -> bool:
    if tile.entity is None or general is None:
        return False
    return tile.entity == general

def is_ally_minion(general: Optional['General'], tile: 'Tile') -> bool:
    if tile.entity is None or general is None:
        return False
    return tile.entity in general.bg.minions and tile.entity.is_ally(general)

def is_empty(general: Optional['General'], tile: 'Tile') -> bool:
    return tile.entity is None

def is_enemy(general: Optional['General'], tile: 'Tile') -> bool:
    if general is None:
        return False
    return tile.entity is not None and not tile.entity.is_ally(general)

def is_enemy_general(general: Optional['General'], tile: 'Tile') -> bool:
    if general is None:
        return False
    return tile.entity is not None and tile.entity == general.bg.generals[(general.side+1)%2]

def is_inrange(general: Optional['General'], tile: 'Tile', radius: int) -> bool:
    if general is None:
        return False
    a = area.Circle(general.bg, radius=radius)
    return tile in a.get_tiles(general.x, general.y)

def is_inrange_close(general: Optional['General'], tile: 'Tile') -> bool:
    return is_inrange(general, tile, 8)

def is_inrange_long(general: Optional['General'], tile: 'Tile') -> bool:
    return is_inrange(general, tile, 20)

def is_minion(general: Optional['General'], tile: 'Tile') -> bool:
    if general is None:
        return False
    return tile.entity is not None and tile.entity in general.bg.minions

def is_unit(general: Optional['General'], tile: 'Tile') -> bool:
    if general is None:
        return False
    return tile.entity is not None and (tile.entity in general.bg.minions or tile.entity in general.bg.generals)
