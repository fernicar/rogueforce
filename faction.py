from __future__ import annotations
from typing import List, Sequence, TYPE_CHECKING
from factions import doto
from factions import mechanics
from factions import oracles
from factions import saviours
from factions import wizerds
import general

if TYPE_CHECKING:
    from battleground import Battleground
    from general import General

class Faction(object):
    """Base class for game factions containing generals.

    A faction represents a collection of generals that can be used in battles.
    Each faction has a unique set of generals with different abilities.

    Attributes:
        bg: The battleground this faction belongs to
        side: Team identifier for the faction
        generals: List of general instances available in this faction
        name: Display name of the faction
    """

    def __init__(self, battleground: 'Battleground', side: int, generals: Sequence['General'], name: str = "Faction") -> None:
        """Initialize a Faction.

        Args:
            battleground: The battleground this faction belongs to
            side: Team identifier (0 or 1)
            generals: List of general classes available in this faction
            name: Display name of the faction
        """
        self.bg = battleground
        self.side = side
        self.generals = generals
        self.name = name

class Doto(Faction):
    """Doto faction with earth-themed generals."""

    def __init__(self, battleground: 'Battleground', side: int) -> None:
        """Initialize Doto faction.

        Args:
            battleground: The battleground this faction belongs to
            side: Team identifier (0 or 1)
        """
        generals = [doto.Bloodrotter(battleground, side),
                    doto.Ox(battleground, side),
                    doto.Pock(battleground, side),
                    doto.Rubock(battleground, side)]
        super(Doto, self).__init__(battleground, side, generals, "Doto")

class Mechanics(Faction):
    """Mechanics faction with technology-themed generals."""

    def __init__(self, battleground: 'Battleground', side: int) -> None:
        """Initialize Mechanics faction.

        Args:
            battleground: The battleground this faction belongs to
            side: Team identifier (0 or 1)
        """
        generals = [mechanics.Flappy(battleground, side)]
        super(Mechanics, self).__init__(battleground, side, generals, "Mechanics")

class Oracles(Faction):
    """Oracles faction with mystical generals."""

    def __init__(self, battleground: 'Battleground', side: int) -> None:
        """Initialize Oracles faction.

        Args:
            battleground: The battleground this faction belongs to
            side: Team identifier (0 or 1)
        """
        generals = [oracles.Gemekaa(battleground, side),
                    doto.Ox(battleground, side),
                    doto.Pock(battleground, side)]
        super(Oracles, self).__init__(battleground, side, generals, "Oracles")

class Saviours(Faction):
    """Saviours faction with heroic generals."""

    def __init__(self, battleground: 'Battleground', side: int) -> None:
        """Initialize Saviours faction.

        Args:
            battleground: The battleground this faction belongs to
            side: Team identifier (0 or 1)
        """
        generals = [saviours.Ares(battleground, side),
                    doto.Bloodrotter(battleground, side),
                    doto.Rubock(battleground, side)]
        super(Saviours, self).__init__(battleground, side, generals, "Saviours")

class Wizerds(Faction):
    """Wizerds faction with magical generals."""

    def __init__(self, battleground: 'Battleground', side: int) -> None:
        """Initialize Wizerds faction.

        Args:
            battleground: The battleground this faction belongs to
            side: Team identifier (0 or 1)
        """
        generals = [wizerds.Starcall(battleground, side)]
        super(Wizerds, self).__init__(battleground, side, generals, "Wizerds")
