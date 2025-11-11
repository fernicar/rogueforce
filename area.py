from __future__ import annotations
from general import General
from sieve import Sieve
import math
from typing import List, Tuple, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from battleground import Battleground, Tile

class Area(object):
    """Base class for defining areas of effect on the battlefield.

    Areas define regions on the battlefield that can be affected by skills,
    filtered by sieve functions, and constrained by reach functions.

    Attributes:
        bg: The battleground this area operates on
        general: The general associated with this area (if any)
        sieve: Sieve function to filter tiles
        reach: Reach function to limit area extent
        selfcentered: Whether the area is centered on the general
    """

    def __init__(self, bg: Battleground, sieve_function: Optional[Callable] = None, general: Optional['General'] = None, reach_function: Optional[Callable] = None, selfcentered: bool = False) -> None:
        """Initialize an area.

        Args:
            bg: The battleground this area operates on
            sieve_function: Function to filter which tiles are included
            general: The general associated with this area
            reach_function: Function to limit the reach/extent of the area
            selfcentered: Whether the area should be centered on the general
        """
        self.bg = bg
        self.general = general
        self.sieve = Sieve(general, sieve_function) if sieve_function else None
        self.reach = Sieve(general, reach_function) if reach_function else None
        self.selfcentered = selfcentered

    def clone(self, general: 'General') -> 'Area':
        """Create a copy of this area with a different general.

        Args:
            general: The new general for the cloned area

        Returns:
            A new Area instance with the same properties but different general
        """
        sieve = self.sieve.function if self.sieve else None
        reach = self.reach.function if self.reach else None
        return self.__class__(self.bg, sieve, general, reach, self.selfcentered)

    def get_all_tiles(self, x: int, y: int) -> List['Tile']:
        """Get all tiles in this area without filtering.

        Args:
            x: X coordinate of the target point
            y: Y coordinate of the target point

        Returns:
            List of tiles in the area
        """
        return self.get_tiles()

    def get_tiles(self, x: int = -1, y: int = -1) -> List['Tile']:
        """Get tiles in this area, applying all filters.

        Args:
            x: X coordinate of the target point (default: -1)
            y: Y coordinate of the target point (default: -1)

        Returns:
            List of tiles that pass all filters
        """
        if self.selfcentered and self.general is not None:
            (x, y) = (self.general.x, self.general.y)
        if self.reach and self.bg.is_inside(x, y) and not self.reach.apply(self.bg.tiles[(x, y)]):
            return []
        if not self.sieve:
            return self.get_all_tiles(x, y)
        return list(filter(self.sieve.apply, self.get_all_tiles(x, y)))

class AllBattleground(Area):
    """Area that covers the entire battleground."""

    def get_all_tiles(self, x: int, y: int) -> List['Tile']:
        """Get all tiles on the battleground.

        Args:
            x: X coordinate (unused for this area type)
            y: Y coordinate (unused for this area type)

        Returns:
            All tiles on the battleground
        """
        return list(self.bg.tiles.values())

class Arc(Area):
    """Arc-shaped area defined by origin, angle, and radius."""

    def __init__(self, bg: Battleground, sieve_function: Optional[Callable] = None, general: Optional['General'] = None, reach_function: Optional[Callable] = None, selfcentered: bool = False,
                origin: Tuple[int, int] = (0, 0), angle: int = 360, ratio_y: int = 1, steps: int = 50) -> None:
        """Initialize an arc area.

        Args:
            bg: The battleground this area operates on
            sieve_function: Function to filter which tiles are included
            general: The general associated with this area
            reach_function: Function to limit the reach/extent of the area
            selfcentered: Whether the area should be centered on the general
            origin: Origin point of the arc
            angle: Angle of the arc in degrees
            ratio_y: Y-axis scaling ratio
            steps: Number of steps to approximate the arc
        """
        super(Arc, self).__init__(bg, sieve_function, general, reach_function, selfcentered)
        self.origin = origin
        self.ratio_y = ratio_y
        self.start_angle = math.radians(angle)
        self.steps = steps
        self.step_angle = self.start_angle / self.steps

    def get_all_tiles(self, x: int, y: int) -> List['Tile']:
        """Get all tiles in the arc area.

        Args:
            x: Target x coordinate
            y: Target y coordinate

        Returns:
            List of tiles within the arc
        """
        if not self.bg.is_inside(x, y):
            return []
        tiles = []
        center_x = (self.origin[0] + x) / 2.0
        center_y = self.origin[1]
        radius = abs(self.origin[0] - x) / 2.0
        direction = math.copysign(1, self.origin[0] - x)
        xx = int(round(center_x + math.cos(self.start_angle) * radius * direction))
        yy = int(round(center_y + math.sin(self.start_angle) * radius * self.ratio_y))
        if self.bg.is_inside(xx, yy):
            tiles.append(self.bg.tiles[(xx, yy)])
        for i in range(1, self.steps+1):
            angle = self.start_angle + i * self.step_angle
            xx = int(round(center_x + math.cos(angle) * radius * direction))
            yy = int(round(center_y + math.sin(angle) * radius * self.ratio_y))
            if not self.bg.is_inside(xx, yy):
                return []
            if self.bg.tiles[(xx, yy)] not in tiles:
                tiles.append(self.bg.tiles[(xx, yy)])
        return tiles

class Circle(Area):
    """Circular area defined by radius."""

    def __init__(self, bg: Battleground, sieve_function: Optional[Callable] = None, general: Optional['General'] = None, reach_function: Optional[Callable] = None, selfcentered: bool = False, radius: int = 5) -> None:
        """Initialize a circular area.

        Args:
            bg: The battleground this area operates on
            sieve_function: Function to filter which tiles are included
            general: The general associated with this area
            reach_function: Function to limit the reach/extent of the area
            selfcentered: Whether the area should be centered on the general
            radius: Radius of the circle in tiles
        """
        super(Circle, self).__init__(bg, sieve_function, general, reach_function, selfcentered)
        self.radius = radius

    def get_all_tiles(self, x: int, y: int) -> List['Tile']:
        """Get all tiles within the circular area.

        Args:
            x: Center x coordinate
            y: Center y coordinate

        Returns:
            List of tiles within the circle
        """
        square = [(a,b) for a in range(x-self.radius, x+self.radius+1) for b in range(y-self.radius, y+self.radius+1)]
        return [self.bg.tiles[(a,b)] for (a,b) in square if self.bg.is_inside(a,b) and (a-x)**2+(b-y)**2 <= self.radius**2]

class CustomArea(Area):
    """Custom area defined by a specific list of tiles."""

    def __init__(self, bg: Battleground, sieve_function: Optional[Callable] = None, general: Optional['General'] = None, tiles: List['Tile'] = []) -> None:
        """Initialize a custom area.

        Args:
            bg: The battleground this area operates on
            sieve_function: Function to filter which tiles are included
            general: The general associated with this area
            tiles: List of tiles that make up this area
        """
        super(CustomArea, self).__init__(bg, sieve_function, general)
        self.tiles = tiles

    def get_all_tiles(self, x: int, y: int) -> List['Tile']:
        """Get the predefined list of tiles.

        Args:
            x: X coordinate (unused for custom areas)
            y: Y coordinate (unused for custom areas)

        Returns:
            The predefined list of tiles
        """
        return self.tiles

class Line(Area):
    """Line-shaped area defined by origin and endpoint."""

    def __init__(self, bg: Battleground, sieve_function: Optional[Callable] = None, general: Optional['General'] = None, reach_function: Optional[Callable] = None, selfcentered: bool = False, origin: Tuple[int, int] = (0, 0)) -> None:
        """Initialize a line area.

        Args:
            bg: The battleground this area operates on
            sieve_function: Function to filter which tiles are included
            general: The general associated with this area
            reach_function: Function to limit the reach/extent of the area
            selfcentered: Whether the area should be centered on the general
            origin: Starting point of the line
        """
        super(Line, self).__init__(bg, sieve_function, general, reach_function, selfcentered)
        self.origin = origin

    def get_all_tiles(self, x2: int, y2: int) -> List['Tile']:
        """Get all tiles along the line using Bresenham's algorithm.

        Args:
            x2: End x coordinate
            y2: End y coordinate

        Returns:
            List of tiles along the line
        """
        # Stolen from: http://roguebasin.roguelikedevelopment.org/index.php?title=Bresenham's_Line_Algorithm#Python
        points = []
        (x1, y1) = self.origin
        issteep = abs(y2-y1) > abs(x2-x1)
        if issteep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
        rev = False
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            rev = True
        deltax = x2 - x1
        deltay = abs(y2-y1)
        error = int(deltax / 2)
        y = y1
        ystep = None
        if y1 < y2:
            ystep = 1
        else:
            ystep = -1
        for x in range(x1, x2 + 1):
            if issteep and self.bg.is_inside(y,x):
                points.append(self.bg.tiles[(y, x)])
            elif self.bg.is_inside(x,y):
                points.append(self.bg.tiles[(x, y)])
            error -= deltay
            if error < 0:
                y += ystep
                error += deltax
        # Reverse the list if the coordinates were reversed
        if rev:
            points.reverse()
        return points

class SingleTarget(Area):
    """Area consisting of a single target tile."""

    def get_all_tiles(self, x: int, y: int) -> List['Tile']:
        """Get the single target tile.

        Args:
            x: Target x coordinate
            y: Target y coordinate

        Returns:
            List containing the single target tile, or empty list if out of bounds
        """
        if not self.bg.is_inside(x, y): return []
        return [self.bg.tiles[(x, y)]]
