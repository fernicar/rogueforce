from __future__ import annotations
import entity
import status

from concepts import EFFECT_HIGHLIGHT
from math import copysign
import itertools
from typing import List, Tuple, Optional, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from battleground import Battleground
    from area import Area

# Define replacement colors for the old EFFECT_* constants
EFFECT_ATTACK_LIGHT: Tuple[int, int, int] = (255, 255, 0) # Yellow
EFFECT_ATTACK_MEDIUM: Tuple[int, int, int] = (255, 165, 0) # Orange
EFFECT_DAMAGE: Tuple[int, int, int] = (255, 0, 0) # Red
EFFECT_WAVE: Tuple[int, int, int] = (0, 0, 255) # Blue

class Effect(entity.Entity):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = ' ', color: Tuple[int, int, int] = EFFECT_HIGHLIGHT) -> None:
        saved = battleground.tiles[(x, y)].entity
        super(Effect, self).__init__(battleground, side, x, y, character_name, character_name, color)
        self.bg.tiles[(x, y)].entity = saved
        self.bg.tiles[(x, y)].effects.append(self)
        if x != -1:
            self.bg.effects.append(self)

    def can_be_pushed(self, dx: int, dy: int) -> bool:
        return False

    def clone(self, x: int, y: int) -> Optional[Effect]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, x, y, self.character_name, self.original_color)
        return None

    def dissapear(self) -> None:
        self.bg.tiles[(self.x, self.y)].effects.remove(self)
        self.alive = False

    def do_attack(self, dissapear: bool = False) -> None:
        entity_obj = self.bg.tiles[(self.x, self.y)].entity
        if entity_obj and entity_obj.can_be_attacked():
            if not entity_obj.is_ally(self):
                entity_obj.get_attacked(self)
            if dissapear:
                self.dissapear()

    def move(self, dx: int, dy: int) -> bool:
        self.bg.tiles[(self.x, self.y)].effects.remove(self)
        self.x += dx
        self.y += dy
        self.bg.tiles[(self.x, self.y)].effects.append(self)
        return True

    def teleport(self, x: int, y: int) -> bool:
        self.bg.tiles[(self.x, self.y)].effects.remove(self)
        self.x = x
        self.y = y
        self.bg.tiles[(self.x, self.y)].effects.append(self)
        return True


class Arrow(Effect):
    def __init__(self, battleground: 'Battleground', side: int, x: int, y: int, power: int, attack_effects: List[str] = ['>', '<']) -> None:
        super(Arrow, self).__init__(battleground, side, x, y, attack_effects[side], EFFECT_ATTACK_MEDIUM)
        self.power = cast(int, power)
        self.do_attack()

    def update(self) -> None:
        if not self.alive: return
        if not self.bg.is_inside(self.x + (1 if self.side == 0 else -1), self.y):
            self.dissapear()
        self.do_attack(True)
        if not self.alive: return
        self.move(1 if self.side == 0 else -1, 0)
        self.do_attack(True)

class Blinking(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = ' ', color: Tuple[int, int, int] = EFFECT_HIGHLIGHT) -> None:
        super(Blinking, self).__init__(battleground, side, x, y, character_name, color)
        self.visible = True

    def dissapear(self) -> None:
        if self.visible:
            super(Blinking, self).dissapear()
        self.alive = False

    def update(self) -> None:
        if not self.alive:
            return
        if self.next_action <= 0:
            self.reset_action()
            if self.visible:
                self.bg.tiles[(self.x, self.y)].effects.remove(self)
            else:
                self.bg.tiles[(self.x, self.y)].effects.append(self)
            self.visible = not self.visible
        else:
            self.next_action -= 1

class Boulder(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = 'O', color: Tuple[int, int, int] = EFFECT_HIGHLIGHT, power: int = 10, delay: int = 0, delta_power: int = -2) -> None:
        super(Boulder, self).__init__(battleground, side, x, y, character_name, color)
        self.power = cast(int, power)
        self.delta_power = delta_power
        self.delay = delay

    def clone(self, x: int, y: int) -> Optional[Boulder]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, x, y, self.character_name, self.original_color, cast(int, self.power), self.delay, self.delta_power)
        return None

    def update(self) -> None:
        if not self.alive:
            return
        self.move_path()
        if self.delay > 0:
            self.delay -= 1
            if self.delay == 0:
                self.character_name = self.character_name.lower()
            return
        self.do_attack()
        self.power = cast(int, self.power) + self.delta_power
        if not self.path or self.power == 0:
            self.dissapear()

class Bouncing(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = 'o', color: Tuple[int, int, int] = EFFECT_HIGHLIGHT, power: int = 5, path: List = []) -> None:
        super(Bouncing, self).__init__(battleground, side, x, y, character_name, color)
        self.path = path
        self.power = cast(int, power)
        self.direction = 1
        self.position = 1

    def clone(self, x: int, y: int) -> Optional[Bouncing]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, x, y, self.character_name, self.original_color, cast(int, self.power), self.path)
        return None

    def update(self) -> None:
        if not self.alive:
            return
        t = self.path[self.position % len(self.path)]
        if self.position == 0 or self.position == len(self.path)-1:
            self.dissapear()
            return
        self.teleport(t.x, t.y)
        entity_obj = self.bg.tiles[(self.x, self.y)].entity
        if entity_obj:
            self.do_attack()
            self.direction *= -1
        self.position += self.direction

class EffectLoop(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_names: List[str] = [' '], color: Tuple[int, int, int] = EFFECT_HIGHLIGHT, duration: int = 1) -> None:
        super(EffectLoop, self).__init__(battleground, side, x, y, character_names[0], color)
        self.character_names = character_names
        self.duration = duration
        self.index = 0

    def clone(self, x: int, y: int) -> Optional[EffectLoop]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, x, y, self.character_names, self.original_color, self.duration)
        return None

    def update(self) -> None:
        if not self.alive: return
        self.duration -= 1
        self.character_name = self.character_names[self.index]
        self.index = (self.index+1) % len(self.character_names)
        if self.duration < 0:
            self.dissapear()

class Explosion(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = '*', color: Tuple[int, int, int] = EFFECT_ATTACK_LIGHT, power: int = 10) -> None:
        super(Explosion, self).__init__(battleground, side, x, y, character_name, color)
        self.power = cast(int, power)

    def clone(self, x: int, y: int) -> Optional[Explosion]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, x, y, self.character_name, self.original_color, cast(int, self.power))
        return None

    def update(self) -> None:
        if not self.alive: return
        if self.color == EFFECT_ATTACK_LIGHT:
            self.color = EFFECT_ATTACK_MEDIUM
        elif self.color == EFFECT_ATTACK_MEDIUM:
            self.color = EFFECT_DAMAGE
        else:
            self.do_attack()
            self.dissapear()

class Lava(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = 'L', color: Tuple[int, int, int] = EFFECT_DAMAGE, power: int = 5, duration: int = 10) -> None:
        super(Lava, self).__init__(battleground, side, x, y, character_name, color)
        self.power = cast(int, power)
        self.original_duration = duration
        self.duration = duration
        self.bg.tiles[(self.x, self.y)].hover(color)
        self.burning_status = status.Poison(None, power=1, tbt=2, ticks=1, name="Burnt")
        entity_obj = self.bg.tiles[(self.x, self.y)].entity
        if entity_obj:
            entity_obj.get_attacked(self)

    def clone(self, x: int, y: int) -> Optional[Lava]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, x, y, self.character_name, self.original_color, cast(int, self.power), self.original_duration)
        return None

    def update(self) -> None:
        if not self.alive:
            return
        if self.duration == 0:
            self.bg.tiles[(self.x, self.y)].unhover()
            self.dissapear()
        if self.path:
            tile = self.path.pop(0)
            self.clone(tile.x, tile.y)
        entity_obj = self.bg.tiles[(self.x, self.y)].entity
        if entity_obj:
            self.burning_status.clone(entity_obj)
        self.duration -= 1

class Pathing(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = ' ', color: Tuple[int, int, int] = EFFECT_HIGHLIGHT) -> None:
        super(Pathing, self).__init__(battleground, side, x, y, character_name, color)

    def update(self) -> None:
        if self.alive and not self.move_path():
            self.dissapear()

class Orb(Pathing):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = 'o', color: Tuple[int, int, int] = EFFECT_HIGHLIGHT,
                             power: int = 15, attack_type: str = "magical") -> None:
        super(Orb, self).__init__(battleground, side, x, y, character_name, color)
        self.power = cast(int, power)
        self.attack_type = attack_type
        self.attacked_entities: List[entity.Entity] = []

    def clone(self, x: int, y: int) -> Optional[Orb]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, x, y, self.character_name, self.original_color, cast(int, self.power), self.attack_type)

    def update(self) -> None:
        super(Orb, self).update()
        if self.alive:
            for (pos_x, pos_y) in itertools.product([-1,0,1], [-1,0,1]):
                if self.bg.is_inside(self.x+pos_x, self.y+pos_y):
                    entity_obj = self.bg.tiles[(self.x+pos_x), (self.y+pos_y)].entity
                    if entity_obj and not entity_obj.is_ally(self) and entity_obj not in self.attacked_entities:
                        entity_obj.get_attacked(self)
                        self.attacked_entities.append(entity_obj)

class Slash(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = '|', color: Tuple[int, int, int] = EFFECT_HIGHLIGHT, power: int = 10, steps: int = 8, goto: int = 1, area=None) -> None:
        super(Slash, self).__init__(battleground, side, x, y, character_name, color)
        self.general = self.bg.generals[side]
        self.max_steps = steps
        self.step = 0
        self.power = cast(int, power)
        self.center_x = x
        self.center_y = y
        self.direction = 0
        self.chars = ['|', '\\', '-', '/']
        self.goto = goto
        self.directions = [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]

    def clone(self, x: int, y: int) -> Optional[Slash]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, self.general.x, self.general.y, self.character_name, self.original_color, cast(int, self.power), self.max_steps, self.goto)
        return None

    def update(self) -> None:
        if not self.alive:
            return
        if abs(self.step) >= self.max_steps:
            self.dissapear()
            return
        self.character_name = self.chars[(self.step+self.direction)%4]
        self.teleport(self.general.x, self.general.y)
        self.move(*self.directions[(self.step+self.direction)%8])
        self.step += int(copysign(1, self.goto))
        self.do_attack()

class TempEffect(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = ' ', color: Tuple[int, int, int] = EFFECT_HIGHLIGHT, duration: int = 1) -> None:
        super(TempEffect, self).__init__(battleground, side, x, y, character_name, color)
        self.duration = duration

    def clone(self, x: int, y: int) -> Optional[TempEffect]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, x, y, self.character_name, self.original_color, self.duration)
        return None

    def update(self) -> None:
        if not self.alive: return
        self.duration -= 1
        if self.duration < 0:
            self.dissapear()

class Thunder(Effect):
    def __init__(self, battleground: 'Battleground', side: int = entity.NEUTRAL_SIDE, x: int = -1, y: int = -1, character_name: str = '|', color: Tuple[int, int, int] = EFFECT_ATTACK_LIGHT, power: int = 30, area: Optional['Area'] = None) -> None:
        self.target_y = y
        self.power = cast(int, power)
        self.area = area
        if x != -1:
            y = y-5 if y-5 >= 0 else 0
        super(Thunder, self).__init__(battleground, side, x, y, character_name, color)

    def clone(self, x: int, y: int) -> Optional[Thunder]:
        if self.bg.is_inside(x, y):
            return self.__class__(self.bg, self.side, x, y, self.character_name, self.original_color, cast(int, self.power), self.area)
        return None

    def update(self) -> None:
        if not self.alive: return
        if self.color == EFFECT_ATTACK_LIGHT:
            self.color = EFFECT_ATTACK_MEDIUM
        elif self.color == EFFECT_ATTACK_MEDIUM:
            self.color = EFFECT_DAMAGE
        elif self.y != self.target_y:
            self.move(0, 1)
            self.color = EFFECT_ATTACK_LIGHT
        else:
            self.dissapear()
            e = Explosion(self.bg, self.side, self.x, self.y, '*', EFFECT_ATTACK_LIGHT, cast(int, self.power))
            if self.area:
                for t in self.area.get_tiles(self.x, self.y):
                    if (t.x, t.y) != (e.x, e.y):
                        e.clone(t.x, t.y)

class Wave(Effect):
    def __init__(self, battleground: 'Battleground', side: int, x: int, y: int, power: int) -> None:
        super(Wave, self).__init__(battleground, side, x, y, '~', EFFECT_WAVE)
        self.power = power
        self.entities_attacked: List[entity.Entity] = []
        self.do_attack()

    def do_attack(self) -> None:
        entity_obj = self.bg.tiles[(self.x, self.y)].entity
        if entity_obj is not None and entity_obj not in self.entities_attacked and entity_obj.can_be_attacked():
            entity_obj.get_attacked(self)
            self.entities_attacked.append(entity_obj)

    def update(self) -> None:
        if not self.alive: return
        if not self.bg.is_inside(self.x + (1 if self.side == 0 else -1), self.y):
            self.dissapear()
            return
        self.do_attack()
        self.move(1 if self.side == 0 else -1, 0)
        self.do_attack()
