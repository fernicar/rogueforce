from __future__ import annotations
import entity
import concepts
import sys
import os
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from entity import Entity, Fortress
    from effect import Effect
    from general import General
    from minion import Minion

class Battleground(object):
    """Represents the game battlefield grid containing tiles, entities, and game state.

    The Battleground manages the spatial layout of the game world, including tiles,
    entities (minions, generals, fortresses), and various game effects.

    Attributes:
        width: Width of the battlefield in tiles
        height: Height of the battlefield in tiles
        tiles: Dictionary mapping (x, y) coordinates to Tile objects
        effects: List of active effects on the battlefield
        minions: List of all minions currently on the battlefield
        generals: List of generals for each side
        reserves: List of reserve generals for each side
        fortresses: List of fortress entities on the battlefield
        hovered: List of currently hovered tiles
    """

    def __init__(self, width: int, height: int, tilefile: Optional[str] = None) -> None:
        self.height = height
        self.width = width
        self.effects: List['Effect'] = []
        self.minions: List['Minion'] = []
        self.generals: List['General'] = []
        self.reserves: List[List['General']] = [[], []]
        self.fortresses: List['Fortress'] = []
        self.tiles: Dict[Tuple[int, int], Tile] = {}
        if tilefile:
            self.load_tiles(tilefile)
        else:
            self.default_tiles()
        self.tiles[(-1, -1)] = Tile(-1, -1)
        self.hovered: List[Tile] = []
        self.connect_fortresses()

    def connect_fortresses(self) -> None:
        for f in self.fortresses:
            f.get_connections()

    def default_tiles(self) -> None:
        for x in range(self.width):
            for y in range(self.height):
                if x in [0, self.width-1] or y in [0, self.height-1]: # Walls
                    self.tiles[(x,y)] = Tile(x, y, "#", False)
                    self.tiles[(x,y)].color = concepts.UI_TEXT
                else: # Floor
                    self.tiles[(x,y)] = Tile(x, y)
                    self.tiles[(x,y)].char = '.'
                    self.tiles[(x,y)].color = concepts.UI_TILE_NEUTRAL

    def hover_tiles(self, l: List[Tile], color: Tuple[int, int, int] = concepts.UI_HOVER_DEFAULT) -> None:
        self.unhover_tiles()
        for t in l:
            t.hover(color)
        self.hovered = l

    def is_inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def load_tiles(self, tilefile: str) -> None:
        forts = []
        passables = ['.']
        f = open(os.path.join("data", tilefile), 'r')
        for y in range(self.height):
            x = 0
            for c in f.readline():
                self.tiles[(x,y)] = Tile(x, y, c, c in passables)
                if c == ':':
                    forts.append((x,y))
                x += 1
        f.close()
        for f in forts:
            colors: List[Tuple[int, int, int]] = [concepts.UI_BACKGROUND] * 4
            self.fortresses.append(entity.Fortress(self, entity.NEUTRAL_SIDE, f[0], f[1], [self.tiles[f].char]*4, colors))

    def unhover_tiles(self) -> None:
        for t in self.hovered:
            t.unhover()

@dataclass
class Tile:
    """Represents a single tile on the battlefield grid.

    Tiles can contain entities, effects, and have different passability and visual properties.

    Attributes:
        x: X coordinate of the tile
        y: Y coordinate of the tile
        char: Character representation of the tile
        passable: Whether entities can move through this tile
        color: Foreground color of the tile
        bg_original_color: Original background color
        bg_color: Current background color
        entity: Entity currently occupying this tile (if any)
        effects: List of effects active on this tile
    """
    x: int
    y: int
    char: str = '.'
    passable: bool = True
    color: Tuple[int, int, int] = field(default_factory=lambda: concepts.ENTITY_DEFAULT)
    bg_original_color: Tuple[int, int, int] = field(default_factory=lambda: concepts.UI_BACKGROUND)
    bg_color: Tuple[int, int, int] = field(default_factory=lambda: concepts.UI_BACKGROUND)
    entity: Optional['Entity'] = None
    effects: List['Effect'] = field(default_factory=list)

    def get_char(self, x: int, y: int) -> str:
        """Get the character representation of this tile.

        Args:
            x: X coordinate (unused, for compatibility)
            y: Y coordinate (unused, for compatibility)

        Returns:
            Character representation of the tile
        """
        return self.char

    def is_passable(self, passenger: 'Entity') -> bool:
        """Check if this tile can be passed through by a given entity.

        Args:
            passenger: Entity attempting to pass through

        Returns:
            True if the tile is passable for the entity
        """
        return self.passable and (self.entity == None or self.entity.is_ally(passenger))

    def hover(self, color: Tuple[int, int, int] = concepts.UI_HOVER_DEFAULT) -> None:
        """Set the tile to hovered state with a specific color.

        Args:
            color: RGB color tuple for hover effect
        """
        self.bg_color = color

    def unhover(self) -> None:
        """Remove hover state and restore original background color."""
        self.bg_color = self.bg_original_color
