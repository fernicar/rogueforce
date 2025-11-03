import pygame
from entity_sprite_mixin import SpriteEntityMixin
import cmath as math

NEUTRAL_SIDE = 555

class Entity(SpriteEntityMixin):
  def __init__(self, battleground, side=NEUTRAL_SIDE, x=-1, y=-1, sprite_name=None, name="Entity"):
    self.bg = battleground
    self.x = x
    self.y = y
    self.side = side
    self.name = name
    self.init_sprite_system(sprite_name)

    if x != -1 and y != -1:
        self.bg.tiles[(x, y)].entity = self

    self.default_next_action = 5
    self.next_action = self.default_next_action
    self.pushed = False
    self.alive = True
    self.statuses = []
    self.path = []
    self.attack_effect = None
    self.attack_type = "physical"
    self.kills = 0
    self.owner = None

  def can_be_attacked(self):
    return False
    
  def can_be_pushed(self, dx, dy):
    next_tile = self.bg.tiles[(self.x+dx, self.y+dy)]
    return next_tile.is_passable(self) and (next_tile.entity is None or next_tile.entity.can_be_pushed(dx, dy))
    
  def can_move(self, dx, dy):
    next_tile = self.bg.tiles[(self.x+dx, self.y+dy)]
    if not next_tile.is_passable(self): return False
    if next_tile.entity is None: return True
    if not next_tile.entity.is_ally(self): return False
    return next_tile.entity.can_be_pushed(dx, dy)

  def change_battleground(self, bg, x, y):
    if self.x != -1 and self.y != -1:
        self.bg.tiles[(self.x, self.y)].entity = None
    self.bg = bg
    (self.x, self.y) = (x, y)
    self.bg.tiles[(self.x, self.y)].entity = self

  def clone(self, x, y): 
    if self.bg.is_inside(x, y) and self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
      return self.__class__(self.bg, self.side, x, y, self.sprite_name, self.name)
    return None

  def die(self):
    if self.x != -1 and self.y != -1:
        self.bg.tiles[(self.x, self.y)].entity = None
    self.alive = False
  
  def get_attacked(self, enemy, power=None, attack_effect=None, attack_type=None):
    self.trigger_flinch_animation()

  def get_passable_neighbours(self):
    neighbours = [(self.x+i, self.y+j) for i in range(-1,2) for j in range(-1,2)] 
    return filter(lambda t: self.bg.tiles[t].passable and t != (self.x, self.y), neighbours)

  def get_pushed(self, dx, dy):
    self.pushed = False
    self.move(dx, dy)
    self.pushed = True
   
  def is_ally(self, entity):
    return self.side == entity.side

  def move(self, dx, dy):
    self.trigger_walk_animation(dx)
    if self.pushed:
      self.pushed = False
      return False
    (dx,dy) = (int(dx), int(dy))
    next_tile = self.bg.tiles[(self.x+dx, self.y+dy)]
    if self.can_move(dx, dy):
      if next_tile.entity is not None:
        next_tile.entity.get_pushed(dx, dy)
      self.bg.tiles[(self.x, self.y)].entity = None
      next_tile.entity = self
      self.x += dx
      self.y += dy
      return True
    return False

  def move_path(self):
    if self.path:
      next_tile = self.path.pop(0)
      if self.move(next_tile.x - self.x, next_tile.y - self.y):
        return True
      else:
        self.path.insert(0, next_tile)
    return False

  def register_kill(self, killed):
    self.kills += 1
    if self.owner:
      self.owner.kills += 1

  def reset_action(self):
    self.next_action = self.default_next_action

  def teleport(self, x, y):
    if self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
      self.bg.tiles[(x, y)].entity = self
      if self.x != -1 and self.y != -1:
        self.bg.tiles[(self.x, self.y)].entity = None
      (self.x, self.y) = (x, y)
      return True
    return False

  def update(self):
    self.update_sprite_animation()
    for s in self.statuses:
      s.update()

class BigEntity(Entity):
  def __init__(self, battleground, side, x, y, sprite_name=None, name="BigEntity"):
    super(BigEntity, self).__init__(battleground, side, x, y, sprite_name, name)
    self.length = 2
    self.update_body()
  
  def can_be_pushed(self, dx, dy):
    return False

  def can_move(self, dx, dy):
    for (x,y) in [(self.x+dx+x,self.y+dy+y) for x in range (0, self.length) for y in range (0, self.length)]:
      next_tile = self.bg.tiles[(x, y)]
      if not next_tile.is_passable(self): return False
      if next_tile.entity is None: continue
      if not next_tile.entity.is_ally(self): return False
      if next_tile.entity is self: continue
      if not next_tile.entity.can_be_pushed(dx, dy): return False
    return True  

  def clear_body(self):
    for i in range(self.length):
      for j in range(self.length):
        if self.bg.is_inside(self.x + i, self.y + j):
            self.bg.tiles[(self.x+i, self.y+j)].entity = None
    
  def die(self):
    self.clear_body()
    self.alive = False
    
  def move(self, dx, dy):
    self.trigger_walk_animation(dx)
    if self.pushed:
      self.pushed = False
      return
    next_tile = self.bg.tiles[(self.x+dx, self.y+dy)]
    if self.can_move(dx, dy):
      if next_tile.entity is not None and next_tile.entity is not self:
        next_tile.entity.get_pushed(dx, dy)
      self.clear_body()
      self.x += dx
      self.y += dy
      self.update_body()

  def update_body(self):
    for i in range(self.length):
      for j in range(self.length):
        if self.bg.is_inside(self.x + i, self.y + j):
            self.bg.tiles[(self.x+i, self.y+j)].entity = self
      
class Fortress(BigEntity):
  def __init__(self, battleground, side=NEUTRAL_SIDE, x=-1, y=-1, sprite_name='fortress', requisition_production=1):
    super(Fortress, self).__init__(battleground, side, x, y, sprite_name, name="Fortress")
    self.capacity = 4
    self.connected_fortresses = []
    self.guests = []
    self.requisition_production = requisition_production

  def can_be_attacked(self):
    return True

  def can_host(self, entity):
    return self.side == entity.side or self.side == NEUTRAL_SIDE

  def can_move(self, dx, dy):
    return False

  def get_connections(self):
    # Gather all tiles inside and surrounding the fortress
    starting_tiles = [(self.x+i, self.y+j) for i in range(-1,3) for j in range(-1,3)] 
    # Remove those inside it
    checked = [(self.x+i, self.y+j) for i in range(0,2) for j in range(0,2)]
    starting_tiles = filter(lambda t: self.bg.tiles[t].passable and t not in checked, starting_tiles)
    # Try every reachable tile from the fortress and save the connections
    for starting in starting_tiles:
      tiles = [starting]
      while tiles:
        (x, y) = tiles.pop()
        checked.append((x, y))
        for t in [(x+i, y+j) for i in range(-1,2) for j in range(-1,2)]:
          entity = self.bg.tiles[t].entity
          if entity in self.bg.fortresses and entity is not self and entity not in self.connected_fortresses:
            self.connected_fortresses.append((entity, starting))
          if self.bg.tiles[t].passable and t not in checked:
            tiles.append(t)

  def host(self, entity):
    if not self.can_host(entity) or len(self.guests) >= self.capacity: return
    if not self.guests:
      self.side = entity.side
    self.bg.tiles[(entity.x, entity.y)].entity = None
    (entity.x, entity.y) = (self.x, self.y)
    self.bg.generals.remove(entity)
    self.guests.append(entity)

  def unhost(self, entity):
    self.guests.remove(entity)
    self.bg.generals.append(entity)
    if not self.guests:
      self.side = NEUTRAL_SIDE

class Mine(Entity):
  def __init__(self, battleground, x=-1, y=-1, power=50, sprite_name='mine'):
    super(Mine, self).__init__(battleground, NEUTRAL_SIDE, x, y, sprite_name, "Mine")
    self.power = power

  def can_be_attacked(self):
    return True

  def clone(self, x, y):
    if self.bg.is_inside(x, y) and self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
      return self.__class__(self.bg, x, y, self.power, self.sprite_name)
    return None

  def get_attacked(self, attacker):
    super().get_attacked(attacker)
    if attacker.can_be_attacked():
      attacker.get_attacked(self)
    self.die()
