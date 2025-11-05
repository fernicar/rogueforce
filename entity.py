from config import COLOR_WHITE
from rendering.animation import Animation
from assets.asset_loader import asset_loader
import cmath as math

NEUTRAL_SIDE = 555

class Entity(object):
  def __init__(self, battleground, side=NEUTRAL_SIDE, x=-1, y=-1, sprite_name=' ', character_name=None, color=COLOR_WHITE):
    self.bg = battleground
    self.x = x
    self.y = y
    self.side = side
    self.sprite_name = sprite_name
    self.char = sprite_name # The old 'char' is now the sprite_name
    self.character_name = character_name if character_name else self.char
    self.original_char = self.char # Keep original for reference
    self.original_sprite_name = sprite_name
    self.color = color
    self.original_color = color
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
    self.animation = None  # Defer sprite loading until pygame is initialized

  def load_sprites(self):
    """Load sprites after pygame display is initialized"""
    if self.character_name and not self.animation:
        try:
            sprites = asset_loader.get_character_sprites(self.character_name)
            self.animation = Animation(sprites)
        except Exception as e:
            print(f"[SPRITE WARNING] Failed to load sprites for {self.character_name}: {e}")
            self.animation = None

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
    self.bg.tiles[(self.x, self.y)].entity = None
    self.bg = bg
    (self.x, self.y) = (x, y)
    self.bg.tiles[(self.x, self.y)].entity = self

  def clone(self, x, y): 
    if self.bg.is_inside(x, y) and self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
      return self.__class__(self.bg, self.side, x, y, self.sprite_name, self.character_name, self.original_color)
    return None

  def die(self):
    self.bg.tiles[(self.x, self.y)].entity = None
    self.alive = False
  
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
      if self.animation: self.animation.set_state('walk')
      return True
    return False

  def move_path(self):
    if self.path:
      next_tile = self.path.pop(0)
      if self.move(next_tile.x - self.x, next_tile.y - self.y):
        return True
      else:
        self.path.insert(0, next_tile)
    elif self.animation and self.animation.current_state == 'walk':
        self.animation.set_state('idle')
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
      self.bg.tiles[(self.x, self.y)].entity = None
      (self.x, self.y) = (x, y)
      return True
    return False

  def update(self):
    for s in self.statuses:
      s.update()
    if self.animation:
        self.animation.update()

class BigEntity(Entity):
  def __init__(self, battleground, side, x, y, sprite_names=["a", "b", "c", "d"], colors=[COLOR_WHITE]*4):
    super(BigEntity, self).__init__(battleground, side, x, y, sprite_names[0], None, colors[0])
    self.sprite_names = sprite_names
    self.colors = colors
    self.length = int(math.sqrt(len(self.sprite_names)).real)
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
        self.bg.tiles[(self.x+i, self.y+j)].entity = None
    
  def die(self):
    self.clear_body()
    self.alive = False
    
  def move(self, dx, dy):
    if self.pushed:
      self.pushed = False
      return
    next_tile = self.bg.tiles[(self.x+dx, self.y+dy)]
    if self.can_move(dx, dy):
      if next_tile.entity is not None and next_tile.entity is not self:
        next_tile.entity.get_pushed(dx, dy)
      self.clear_body()
      next_tile.entity = self
      self.x += dx
      self.y += dy
      self.update_body()

  def update_body(self):
    for i in range(self.length):
      for j in range(self.length):
        self.bg.tiles[(self.x+i, self.y+j)].entity = self
      
class Fortress(BigEntity):
  def __init__(self, battleground, side=NEUTRAL_SIDE, x=-1, y=-1, sprite_names=[':']*4, colors=[COLOR_WHITE]*4, requisition_production=1):
    super(Fortress, self).__init__(battleground, side, x, y, sprite_names, colors)
    self.capacity = len(sprite_names)
    self.connected_fortresses = []
    self.guests = []
    self.name = "Fortress"
    self.requisition_production = requisition_production

  def can_be_attacked(self):
    return True

  def can_host(self, entity):
    return self.side == entity.side or self.side == NEUTRAL_SIDE

  def can_move(self, dx, dy):
    return False

  def get_connections(self):
    starting_tiles = [(self.x+i, self.y+j) for i in range(-1,3) for j in range(-1,3)] 
    checked = [(self.x+i, self.y+j) for i in range(0,2) for j in range(0,2)]
    starting_tiles = filter(lambda t: self.bg.tiles[t].passable and t not in checked, starting_tiles)
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
    self.sprite_names[len(self.guests)] = entity.sprite_name
    self.colors[len(self.guests)] = entity.color
    self.guests.append(entity)
    self.update_body()

  def refresh_chars(self):
    self.sprite_names = [':']*len(self.sprite_names)
    self.colors = [COLOR_WHITE]*len(self.colors)
    for i in range(len(self.guests)):
      self.sprite_names[i] = self.guests[i].sprite_name
      self.colors[i] = self.guests[i].color

  def unhost(self, entity):
    self.guests.remove(entity)
    self.bg.generals.append(entity)
    self.refresh_chars()
    if not self.guests:
      self.side = NEUTRAL_SIDE

class Mine(Entity):
  def __init__(self, battleground, x=-1, y=-1, power=50):
    super(Mine, self).__init__(battleground, NEUTRAL_SIDE, x, y, sprite_name='X', color=COLOR_WHITE)
    self.power = power

  def can_be_attacked(self):
    return True

  def clone(self, x, y):
    if self.bg.is_inside(x, y) and self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
      return self.__class__(self.bg, x, y, self.power)
    return None

  def get_attacked(self, attacker):
    if attacker.can_be_attacked():
      attacker.get_attacked(self)
    self.die()
