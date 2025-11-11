from entity import Entity
import area
import effect
import skill
import tactic
import concepts
from pygame import Color
import random
from typing import TYPE_CHECKING, Optional, Any, List

if TYPE_CHECKING:
    from battleground import Battleground, Tile

class Status(object):
    def __init__(self, entity: Optional[Entity] = None, owner: Optional[Entity] = None, duration: int = 9999, name: str = "Status") -> None:
        self.entity: Optional[Entity] = entity
        self.owner: Optional[Entity] = owner
        self.duration: int = duration
        self.name: str = name
        self.attack_effect: Optional[Any] = None
        self.attack_type: str = "magical"
        self.kills: int = 0
        self.duplicated: bool = False
        if entity: # Not a prototype
            if hasattr(entity, 'statuses'):
                for s in entity.statuses:
                    if s.name == self.name:
                        # We refresh the duration if it's bigger
                        s.duration = max(s.duration, self.duration)
                        self.duplicated = True
                        return
                entity.statuses.append(self)

    def clone(self, entity: Entity) -> 'Status':
        return self.__class__(entity, self.owner, self.duration, self.name)

    def end(self) -> None:
        self.duration = -1
        if self.entity:
            self.entity.statuses.remove(self)

    def register_kill(self, killed: Entity) -> None:
        self.kills += 1
        if self.owner:
            self.owner.kills += 1

    def tick(self) -> None:
        pass

    def update(self) -> None:
        if self.duration > 0:
            self.duration -= 1
            self.tick()
            if self.duration <= 0:
                self.end()

class Aura(Status):
    def __init__(self, entity: Optional[Entity] = None, owner: Optional[Entity] = None, duration: int = 9999, name: str = "Aura", area: Optional['area.Area'] = None, status: Optional['Status'] = None) -> None:
        super(Aura, self).__init__(entity, owner, duration, name)
        self.area: Optional['area.Area'] = area
        self.status: Optional['Status'] = status
        self.tbt: int = 10
        self.timer: int = 0
        if status:
            status.duration = self.tbt+2
        self.skill: 'skill.Skill' = skill.Skill(owner, skill.apply_status, 0, [status], area=area)

    def clone(self, entity: Entity) -> 'Aura':
        return self.__class__(entity, self.owner, self.duration, self.name, self.area, self.status)

    def tick(self) -> None:
        if not self.entity:
            return
        self.timer -= 1
        if self.timer < 0:
            self.timer = self.tbt
            self.skill.use(self.entity.x, self.entity.y)

class Bleeding(Status):
    def __init__(self, entity: Optional[Entity] = None, owner: Optional[Entity] = None, power: int = 0, duration: int = 9999, name: str = "Bleeding") -> None:
        super(Bleeding, self).__init__(entity, owner, duration, name)
        self.power: int = power
        self.last_x: int = 0
        self.last_y: int = 0
        if entity:
            (self.last_x, self.last_y) = (entity.x, entity.y)

    def clone(self, entity: Entity) -> 'Bleeding':
        return self.__class__(entity, self.owner, self.power, self.duration, self.name)

    def tick(self) -> None:
        if not self.entity:
            return
        if (self.last_x, self.last_y) != (self.entity.x, self.entity.y):
            diff = max(abs(self.last_x - self.entity.x), abs(self.last_y - self.entity.y))
            if self.owner:
                self.entity.get_attacked(self.owner, diff*self.power, None, "magical")
            effect.TempEffect(self.entity.bg, self.entity.side, self.last_x, self.last_y, '*', concepts.UI_TEXT)
            (self.last_x, self.last_y) = (self.entity.x, self.entity.y)

class Blind(Status):
    def __init__(self, entity: Optional[Entity] = None, owner: Optional[Entity] = None, duration: int = 9999, name: str = "Blindness") -> None:
        super(Blind, self).__init__(entity, owner, duration, name)
        self.saved_power: int = 0
        if entity is not None and hasattr(entity, 'power') and entity.power is not None:
            (self.saved_power, entity.power) = (entity.power, self.saved_power)

    def end(self) -> None:
        if self.entity and hasattr(self.entity, 'power') and self.entity.power is not None:
            self.entity.power = self.saved_power
        super(Blind, self).end()

class Empower(Status):
    def __init__(self, entity: Optional[Entity] = None, owner: Optional[Entity] = None, duration: int = 9999, name: str = "Empower", power_ratio: float = 0) -> None:
        super(Empower, self).__init__(entity, owner, duration, name)
        self.power_ratio: float = power_ratio
        self.bonus_power: int = 0
        if entity and hasattr(entity, 'power') and entity.power is not None:
            self.bonus_power = int(entity.power * power_ratio)
            entity.power += self.bonus_power

    def clone(self, entity: Entity) -> 'Empower':
        return self.__class__(entity, self.owner, self.duration, self.name, self.power_ratio)

    def end(self) -> None:
        super(Empower, self).end()
        if self.entity and hasattr(self.entity, 'power') and self.entity.power is not None:
            self.entity.power -= self.bonus_power

class FreezeCooldowns(Status):
    def __init__(self, entity: Optional[Entity] = None, owner: Optional[Entity] = None, duration: int = 9999, name: str = "Freeze cooldowns") -> None:
        super(FreezeCooldowns, self).__init__(entity, owner, duration, name)
        if self.entity and getattr(self.entity, 'bg', None) and self.entity not in self.entity.bg.generals:
            self.end()

    def tick(self) -> None:
        if self.entity and hasattr(self.entity, 'skills'):
            for s in self.entity.skills:
                s.change_cd(-1)

class Haste(Status):
    def __init__(self, entity: Optional[Entity] = None, duration: int = 9999, name: str = "Haste", speedup: int = 0) -> None:
        super(Haste, self).__init__(entity, None, duration, name)
        self.speedup: int = speedup

    def clone(self, entity: Entity) -> 'Haste':
        return self.__class__(entity, self.duration, self.name, self.speedup)

    def tick(self) -> None:
        if self.entity and hasattr(self.entity, 'next_action'):
            self.entity.next_action -= self.speedup

class Jumping(Status):
    def __init__(self, entity: Optional[Entity] = None, owner: Optional[Entity] = None, duration: int = 9999, name: str = "Jumping",
                             power: int = 0, power_delta: int = 0, area: Optional['area.Area'] = None, status: Optional['Status'] = None) -> None:
        super(Jumping, self).__init__(entity, owner, duration, name)
        self.area: Optional['area.Area'] = area
        self.status: Optional['Status'] = status
        self.power: int = power
        self.power_delta: int = power_delta
        self.rand: random.Random = random.Random()
        self.rand.seed(duration)
        self.already_hit: List[Entity] = []
        if entity:
            self.attack_effect = effect.TempEffect(entity.bg, character_name='-', color=owner.color if owner else concepts.UI_TEXT)

    def clone(self, entity: Entity) -> 'Jumping':
        return self.__class__(entity, self.owner, self.duration, self.name,
                                                    self.power, self.power_delta, self.area, self.status)

    def tick(self) -> None:
        if not self.entity or not self.area or not self.status:
            return
        if self.owner:
            self.entity.get_attacked(self.owner, self.power, self.attack_effect, self.attack_type)
        self.already_hit.append(self.entity)
        self.status.clone(self.entity)
        entities = [tile.entity for tile in self.area.get_tiles(self.entity.x, self.entity.y)
                                                            if tile.entity not in self.already_hit]
        if entities:
            e = self.rand.choice(entities)
            clone = self.clone(e)
            clone.power += self.power_delta
            clone.duration += 1
            clone.rand = self.rand
            clone.already_hit = self.already_hit

class Lifted(Status):
    def __init__(self, entity=None, owner=None, duration=9999, name="Lifted", land_area=None, land_status=None):
        super(Lifted, self).__init__(entity, owner, duration, name)
        self.land_area = land_area
        self.land_status = land_status
        self.skill = skill.Skill(owner, skill.apply_status, 0, [land_status], area=land_area)
        if entity:
            effect.TempEffect(entity.bg, x=entity.x, y=entity.y, character_name='^', color=owner.color if owner else concepts.UI_TEXT, duration=duration)

    def clone(self, entity):
        return self.__class__(entity, self.owner, self.duration, self.name, self.land_area, self.land_status)

    def tick(self):
        if self.entity:
            self.entity.reset_action()
    
    def end(self):
        if self.land_status and self.entity:
            self.skill.use(self.entity.x, self.entity.y)

class Linked(Status):
    def __init__(self, entity=None, owner=None, duration=9999, name="Linked", x=-1, y=-1,
                             power=10, radius=4, status=None):
        super(Linked, self).__init__(entity, owner, duration, name)
        self.x = x
        self.y = y
        self.power = power
        self.radius = radius
        self.status = status
        if entity:
            self.tiles = area.Circle(entity.bg, radius=radius).get_tiles(x, y)
            Stunned(entity, owner, 1, name + " stun")

    def clone(self, entity):
        return self.__class__(entity, self.owner, self.duration, self.name, self.x, self.y,
                                                    self.power, self.radius, self.status)

    def end(self):
        super(Linked, self).end()
        self.duration = -1
        if self.entity and self.entity.bg and self.tiles:
            self.entity.bg.tiles[(self.entity.x, self.entity.y)].bg_color = concepts.UI_BACKGROUND
            for t in self.tiles:
                t.bg_color = concepts.UI_BACKGROUND
        
    def update(self):
        super(Linked, self).update()
        if not self.entity or not self.entity.bg or not self.owner or not self.status:
            return
        t = self.entity.bg.tiles[(self.entity.x, self.entity.y)]
        if self.duration > 0:
            if t not in self.tiles:
                self.status.clone(self.entity)
                self.entity.get_attacked(self)
                self.end()
            else:
                t.bg_color = Color(concepts.UI_BACKGROUND).lerp(self.owner.original_color, 0.4)

class Poison(Status):
    def __init__(self, entity=None, owner=None, power=0, tbt=0, ticks=9999, name="Poison"):
        super(Poison, self).__init__(entity, owner, ticks*(tbt+1), name)
        self.tbt = tbt
        self.ticks = ticks
        self.power = power
        self.timer = 0

    def clone(self, entity):
        return self.__class__(entity, self.owner, self.power, self.tbt, self.ticks, self.name)

    def tick(self):
        if not self.entity:
            return
        self.timer -= 1
        if self.timer < 0:
            self.entity.get_attacked(self)
            self.timer = self.tbt

class PoisonHunger(Poison):
    def __init__(self, entity=None, owner=None, power=0, tbt=0, ticks=9999, name="PoisonHunger"):
        super(PoisonHunger, self).__init__(entity, owner, power, tbt, ticks, name)
        if entity:
            self.entity_kills = entity.kills

    def tick(self):
        if not self.entity or not self.owner:
            return
        if not self.entity.alive or self.entity.kills > self.entity_kills:
            self.duration = -1
        else:
            self.entity.next_action += 1
            self.owner.next_action -= 1
            super(PoisonHunger, self).tick()

class Phasing(Status):
    def __init__(self, entity=None, duration=9999, name="Phasing"):
        super(Phasing, self).__init__(entity, None, duration, name)
        if entity:
            self.p_shield = Shield(entity, duration+1, "Phasing physical shield", 10000, "physical")
            self.m_shield = Shield(entity, duration+1, "Phasing magical shield", 10000, "magical")
            entity.bg.tiles[(entity.x, entity.y)].entity = None
            entity.next_action = duration+1
            self.placeholder = Entity(entity.bg, entity.side, entity.x, entity.y, 'u', entity.color)

    def clone(self, entity):
        return self.__class__(entity, self.duration, self.name)

    def end(self):
        super(Phasing, self).end()
        self.p_shield.end()
        self.m_shield.end()
        if self.placeholder:
            self.placeholder.die()
        if self.entity and self.entity.bg and hasattr(self.entity, 'x') and hasattr(self.entity, 'y'):
            self.entity.bg.tiles[(self.entity.x, self.entity.y)].entity = self.entity

class Recalling(Status):
    def __init__(self, entity=None, duration=9999, name="Recalling"):
        super(Recalling, self).__init__(entity, None, duration, name)
        self.color = self.entity.color if self.entity else None

    def update(self):
        super(Recalling, self).update()
        if self.duration > 0 and self.entity and self.entity.bg and self.color:
            self.entity.next_action = 100
            tile = self.entity.bg.tiles[(self.entity.x, self.entity.y)]
            self.entity.color = Color(tile.bg_color).lerp(self.color, 1-(self.duration/10.0))

    def end(self):
        super(Recalling, self).end()
        if self.entity:
            self.entity.update_color()
            self.entity.reset_action()

class Shield(Status):
    def __init__(self, entity=None, duration=9999, name="Shield", armor=0, armor_type="physical", color=None):
        super(Shield, self).__init__(entity, None, duration, name)
        self.armor = armor
        self.armor_type = armor_type
        self.color = color
        if entity and not self.duplicated:
            entity.armor[armor_type] += armor
            if color:
                entity.color = color

    def clone(self, entity):
        return self.__class__(entity, self.duration, self.name, self.armor, self.armor_type, self.color)

    def end(self):
        super(Shield, self).end()
        if self.entity:
            self.entity.update_color()
            self.entity.armor[self.armor_type] -= self.armor

class Stunned(Status):
    def __init__(self, entity=None, owner=None, duration=9999, name="Stunned"):
        super(Stunned, self).__init__(entity, owner, duration, name)
        if entity:
            self.effect = effect.Blinking(entity.bg, x=entity.x, y=entity.y, character_name='~', color=entity.color)

    def end(self):
        super(Stunned, self).end()
        self.effect.dissapear()

    def tick(self):
        if self.entity:
            self.entity.reset_action()

class Taunted(Status):
    def __init__(self, entity=None, owner=None, duration=9999, name="Taunted"):
        super(Taunted, self).__init__(entity, owner, duration, name)

    def tick(self):
        if not self.entity or not self.owner or not self.entity.bg:
            return
        if self.entity in self.entity.bg.generals:
            self.entity.place_flag(self.owner.x, self.owner.y)
        elif self.entity in self.entity.bg.minions:
            self.entity.tactic = tactic.attack_general

class Vanished(Status):
    def __init__(self, entity=None, duration=9999, name="Vanished"):
        super(Vanished, self).__init__(entity, None, duration, name)
        if entity:
            (self.x, self.y) = (entity.x, entity.y)
            entity.bg.tiles[(entity.x, entity.y)].entity = None
            (entity.x, entity.y) = (-1, -1)
            entity.next_action = 100

    def update(self):
        super(Vanished, self).update()
        if self.entity:
            self.entity.next_action = 100

    def end(self):
        super(Vanished, self).end()
        if self.entity and hasattr(self, 'x') and hasattr(self, 'y'):
            if self.entity.teleport(self.x, self.y):
                self.entity.reset_action()
            else:
                self.entity.die()

class Vanishing(Status):
    def __init__(self, entity=None, duration=9999, vanished_duration=9999, name="Vanishing"):
        super(Vanishing, self).__init__(entity, None, duration, name)
        self.vanished_duration = vanished_duration

    def clone(self, entity):
        return self.__class__(entity, self.duration, self.vanished_duration, self.name)

    def update(self):
        super(Vanishing, self).update()
        if self.duration > 0 and self.entity and self.entity.bg:
            self.entity.next_action = 100
            tile = self.entity.bg.tiles[(self.entity.x, self.entity.y)]
            if self.entity.color and tile.bg_color:
                self.entity.color = Color(self.entity.color).lerp(tile.bg_color, 1-(self.duration/10.0))

    def end(self):
        super(Vanishing, self).end()
        if self.entity:
            self.entity.update_color()
            self.entity.reset_action()
            Vanished(self.entity, self.vanished_duration)
