"""
Central registry for all factions and generals in the game.
"""
from factions import doto, wizerds, oracles, saviours, mechanics

# A dictionary defining all factions and their available general classes.
# This structure makes it easy to add new factions or generals later.
FACTIONS = {
    "doto": {
        "name": "DOTO FACTION",
        "generals": [doto.Pock, doto.Rubock, doto.Bloodrotter, doto.Ox],
    },
    "wizerds": {
        "name": "WIZERDS FACTION",
        "generals": [wizerds.Starcall],
    },
    "oracles": {
        "name": "ORACLES FACTION",
        "generals": [oracles.Gemekaa],
    },
    "saviours": {
        "name": "SAVIOURS FACTION",
        "generals": [saviours.Ares],
    },
    "mechanics": {
        "name": "MECHANICS FACTION",
        "generals": [mechanics.Flappy],
    }
}

# A flat list of all general classes for easy random sampling.
ALL_GENERALS = [gen_class for faction in FACTIONS.values() for gen_class in faction["generals"]]
