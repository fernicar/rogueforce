from __future__ import annotations
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from general import General

class Formation(object):
    """Base class for general formations that determine minion placement patterns.

    Formations control how minions are arranged around a general on the battlefield.
    Different formations provide different tactical advantages.

    Attributes:
        general: The general this formation belongs to
    """

    def __init__(self, general: 'General') -> None:
        """Initialize a Formation.

        Args:
            general: The general this formation belongs to
        """
        self.general = general

    def place_minions(self) -> None:
        """Place minions according to the formation pattern.

        This method should be overridden by subclasses to implement
        specific formation placement logic.
        """
        pass

    def mirror(self, x: int, y: int) -> Tuple[int, int]:
        """Mirror coordinates for the opposing side.

        Args:
            x: X coordinate to mirror
            y: Y coordinate to mirror

        Returns:
            Tuple of mirrored (x, y) coordinates
        """
        return (self.general.bg.width - x - 1, self.general.bg.height - y - 1) if self.general.side else (x, y)

class FlyingWedge(Formation):
    """Flying wedge formation that creates a V-shaped pattern.

    This formation places minions in a wedge pattern pointing forward,
    providing good breakthrough capabilities.
    """

    def __init__(self, general: 'General', increment: int = 1) -> None:
        """Initialize FlyingWedge formation.

        Args:
            general: The general this formation belongs to
            increment: Formation density increment
        """
        super(FlyingWedge, self).__init__(general)
        self.increment = increment

    def place_minions(self) -> None:
        """Place minions in a flying wedge pattern."""
        n = self.general.minions_alive
        for i in range(14, 3, -1):
            offset_y = 0
            for x in range(i, 3, -1):
                for j in range(0, self.increment + 1):
                    if n <= 0: return
                    if self.general.minion is not None:
                        minion_placed = self.general.minion.clone(*self.mirror(x, self.general.y + offset_y))
                        if minion_placed is not None:
                            self.general.bg.minions.append(minion_placed)
                            n -= 1
                    offset_y = abs(offset_y)+1 if j%2 else -offset_y

class InvertedWedge(Formation):
    """Inverted wedge formation that creates an inverted V-shaped pattern.

    This formation places minions in an inverted wedge pattern,
    providing good defensive capabilities.
    """

    def __init__(self, general: 'General', increment: int = 1) -> None:
        """Initialize InvertedWedge formation.

        Args:
            general: The general this formation belongs to
            increment: Formation density increment
        """
        super(InvertedWedge, self).__init__(general)
        self.increment = increment

    def place_minions(self) -> None:
        """Place minions in an inverted wedge pattern."""
        n = self.general.minions_alive
        for i in range(4, 15):
            offset_y = 0
            for x in range(i, 15):
                for j in range(0, self.increment + 1):
                    if n <= 0: return
                    if self.general.minion is not None:
                        minion_placed = self.general.minion.clone(*self.mirror(x, self.general.y + offset_y))
                        if minion_placed is not None:
                            self.general.bg.minions.append(minion_placed)
                            n -= 1
                    offset_y = abs(offset_y)+1 if j%2 else -offset_y

class Rows(Formation):
    """Row formation that places minions in organized rows.

    This formation places minions in horizontal rows,
    providing good flanking and coordinated movement.
    """

    def __init__(self, general: 'General', rows: int = 21) -> None:
        """Initialize Rows formation.

        Args:
            general: The general this formation belongs to
            rows: Number of rows to create
        """
        super(Rows, self).__init__(general)
        self.rows = rows

    def place_minions(self) -> None:
        """Place minions in organized rows."""
        n = self.general.minions_alive
        for x in range(5, 15):
            offset_y = 0
            r = self.rows
            while r > 0:
                if n <= 0: return
                if self.general.minion is not None:
                    minion_placed = self.general.minion.clone(*self.mirror(x, self.general.y + offset_y))
                    if minion_placed is not None:
                        self.general.bg.minions.append(minion_placed)
                        n -= 1
                offset_y = abs(offset_y)+1 if r%2 or not self.rows%2 else -offset_y
                r -= 1
