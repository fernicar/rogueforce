from effect import *
from entity import *

import area
import effect
import sieve
import status
from typing import List, Optional, Any, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from general import General
    from battleground import Tile

class Skill(object):
    def __init__(self, general: Optional['General'], function, max_cd, parameters=[], quote="", description="", area=None, multifunction=False):
        self.general: Optional['General'] = general
        self.function = function
        self.original_max_cd: int = max_cd
        self.max_cd: int = max_cd
        self.cd: int = 0
        self.parameters: List[Any] = parameters
        self.area: Optional[Any] = area
        self.quote: str = quote
        self.name: str = quote
        self.description: str = description
        self.multifunction: bool = multifunction

    def apply_function(self, tiles):
        did_anything = False
        for t in tiles:
            if self.multifunction:
                for i in range(0, len(self.function)):
                    did_anything += self.function[i](self.general, t, *self.parameters[i])
            else:
                did_anything += self.function(self.general, t, *self.parameters)
        return did_anything

    def change_cd(self, delta):
        self.cd += delta
        self.cd = 0 if self.cd < 0 else self.max_cd if self.cd > self.max_cd else self.cd

    def change_max_cd(self, delta):
        self.max_cd += delta

    def clone(self, general):
        return self.__class__(general, self.function, self.max_cd, self.parameters, self.quote, self.description,
                    self.area.clone(general) if self.area else None, self.multifunction)

    def get_area_tiles(self, x, y):
        if self.area is None: return None
        return self.area.get_tiles(x, y)

    def is_ready(self):
        return self.cd >= self.max_cd

    def reset_cd(self):
        self.cd = 0

    def update(self):
        if self.cd < self.max_cd: self.cd += 1

    def use(self, x, y):
        if self.area is None:
            return self.function(self.general, *self.parameters)
        return self.apply_function(self.area.get_tiles(x, y))

class DummySkill(Skill):
    def __init__(self, quote, description):
        super(DummySkill, self).__init__(None, null, 1, [], quote, description)
        self.cd = 1

    def change_cd(self, delta):
        pass
    
    def reset_cd(self):
        pass

    def update(self):
        pass

    def use(self, x, y):
        return False


def add_path(general: 'General', tile: 'Tile', entity) -> bool:
    entity.path.append(tile)
    return True

def apply_status(general: 'General', tile: 'Tile', status, selfcast: bool = False) -> bool:
    clone = status.clone(general if selfcast else tile.entity)
    clone.owner = general
    return True

def apply_statuses(general: 'General', tile: 'Tile', statuses: List) -> bool:
    for s in statuses:
        apply_status(general, tile, s)
    return statuses != []

def consume(general: 'General', tile: 'Tile', hp_gain: int = 1, delta_cd: int = 1) -> bool:
    if tile.entity is not None:
        tile.entity.die()
    general.get_healed(hp_gain)
    for s in general.skills:
        s.change_cd(delta_cd)
    return True

def copy_spell(general: 'General', tile: 'Tile') -> bool:
    if tile.entity is None:
        return False
    # Cast to General since we expect General-specific attributes
    target_general = cast('General', tile.entity)
    if target_general.last_skill_used == -1:
        char = '?'
    else:
        char = '!'
        old_skill = general.skills[general.copied_skill].name
        general.skills[general.copied_skill] = target_general.skills[target_general.last_skill_used].clone(general)
        if general.skills[general.copied_skill].name != old_skill:
            general.skills[general.copied_skill].cd = general.skills[general.copied_skill].max_cd
    effect.TempEffect(general.bg, x=tile.x, y=tile.y, character_name=char, color=general.color)
    effect.TempEffect(general.bg, x=general.x, y=general.y, character_name=char, color=general.color, duration=2)
    return True

def create_minions(general: 'General', l: List[Tuple[int, int]]) -> bool:
    did_anything = False
    for (x, y) in l:
        if general.minion is not None:
            minion_placed = general.minion.clone(x, y)
            if minion_placed is not None:
                general.bg.minions.append(minion_placed)
                general.minions_alive += 1
                did_anything = True
    return did_anything

def darkness(general: 'General', tile: 'Tile', duration: int) -> bool:
    if tile.passable:
        d = TempEffect(general.bg, x=tile.x, y=tile.y, character_name=' ', duration=duration)
    return tile.passable

def decapitate(general: 'General', tile: 'Tile', threshold: float = 1.0) -> bool:
    if tile.entity is None:
        return False
    if tile.entity.hp is None or tile.entity.max_hp is None or tile.entity.max_hp == 0:
        return False
    effect.EffectLoop(general.bg, x=tile.x, y=tile.y, character_names=['-', '\\', 'v'], color=general.color, duration=3)
    if tile.entity.hp/float(tile.entity.max_hp) > threshold:
        tile.entity.get_attacked(general, int(tile.entity.max_hp*threshold/2))
    else: # Decapitated
        tile.entity.get_attacked(general, 9999) # Removed attack_type parameter that doesn't exist
        a = area.Circle(general.bg, sieve.is_ally, general, None, True, 8)
        for t in a.get_tiles():
            apply_status(general, t, status.Haste(None, 30, "Decapitation haste", 3))
    return True

def explosion(general: 'General', tile: 'Tile', power: int, area, statuses: List = []) -> bool:
    for s in statuses:
        (s.x, s.y) = (tile.x, tile.y)
    did_anything = False
    for t in area.get_tiles(tile.x, tile.y):
        nuke_statuses(general, t, power, statuses=statuses)
        did_anything = True
    return did_anything

def heal(general: 'General', tile: 'Tile', amount: int) -> bool:
    if tile.entity is None or tile.entity.hp == tile.entity.max_hp:
        return False
    cast(Minion, tile.entity).get_healed(amount)
    return True

def minion_glider(general: 'General', tile: 'Tile', go_bottom: bool = True) -> bool:
    (x, y) = (tile.x, tile.y)
    if not general.bg.is_inside(x-1, y-1) or not general.bg.is_inside(x+1, y+1): return False
    j = 1 if go_bottom else -1
    i = 1 if general.side == 0 else -1
    return create_minions(general, [(x-i, y-j), (x, y-j), (x, y), (x+i, y), (x-i, y+j)])

def minion_lwss(general: 'General', tile: 'Tile') -> bool:
    (x, y) = (tile.x, tile.y)
    if not general.bg.is_inside(x-2, y-2) or not general.bg.is_inside(x+2, y+2): return False
    j = 1 if general.side == 0 else -1
    return create_minions(general,\
        [(x-1*j, y-1), (x, y-1), (x+1*j, y-1), (x+2*j, y-1), (x-2*j, y), (x+2*j, y), (x+2*j, y+1), (x-2*j, y+2), (x+1*j, y+2)])

def nuke(general: 'General', tile: 'Tile', nuke_power: int, nuke_effect=None, nuke_type: str = "magical") -> bool:
    if tile.entity is not None:
        tile.entity.get_attacked(general, nuke_power, nuke_effect, nuke_type)
    return True

def nuke_statuses(general: 'General', tile: 'Tile', nuke_power: int, nuke_effect=None, nuke_type: str = "magical", statuses: List = []) -> bool:
    nuke(general, tile, nuke_power, nuke_effect, nuke_type)
    apply_statuses(general, tile, statuses)
    return True

def null(general: 'General') -> bool:
    return False

def place_entity(general: 'General', tile: 'Tile', entity) -> bool:
    clone = entity.clone(tile.x, tile.y)
    clone.owner = general
    return clone is not None

def recall_entity(general: 'General', tile: 'Tile', duration: int) -> bool:
    for m in general.bg.minions:
        if m.is_ally(general):
            for s in m.statuses:
                if s.name == "Vanished" and m.teleport(tile.x, tile.y):
                    s.end()
                    m.teleport(tile.x, tile.y)
                    status.Recalling(m, duration)
                    return True
    return False

def restock_minions(general: 'General', number: int) -> bool:
    #TODO: this can be a lot cleaner
    tmp = general.minions_alive
    general.minions_alive = number
    general.formation.place_minions()
    general.minions_alive = tmp
    general.command_tactic([i for i,x in enumerate(general.tactics) if x == general.selected_tactic][0])
    general.recount_minions_alive()
    return True

def sonic_waves(general: 'General', power: int, waves: int) -> bool:
    from effect import Wave
    for i in range(0, waves):
        x = int(general.x+1-(i+1)/2) if general.side == 0 else int(general.x-1+(i+1)/2)
        y = int(general.y+(((i+1)/2)*(-1 if i%2 == 0 else 1)))
        if general.bg.is_inside(x,y):
            general.bg.effects.append(Wave(general.bg, general.side, x, y, power))
    return waves > 0

def teleport(general: 'General', tile: 'Tile', entity) -> bool:
    return entity.teleport(tile.x, tile.y)

def water_pusher(general: 'General', tile: 'Tile') -> bool:
    did_anything = False
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            if not general.bg.is_inside(tile.x + i, tile.y + j): continue
            entity = general.bg.tiles[(tile.x + i, tile.y + j)].entity
            if entity is not None and (i, j) != (0, 0) and entity.can_be_pushed(i, j):
                entity.get_pushed(i, j)
                did_anything = True
    return did_anything
