from area import *
from effect import *
from general import General
from minion import Minion, BigMinion
from skill import *
import sieve

class Flappy(General):
  def __init__(self, battleground, side, x=-1, y=-1, name="Flappy", sprite_name="flappy"):
    super(Flappy, self).__init__(battleground, side, x, y, name, sprite_name)
    self.death_quote = "I'll be back, like a boo... me..."
    self.minion = Minion(self.bg, self.side, name="goblin", sprite_name="goblin")

  def draw_slingshot(self):
    if self.slingshot.animator:
        self.slingshot.animator.set_animation('draw')

  def initialize_skills(self):
    self.skills = []
    self.skills.append(Skill(self, add_path, 5, [self.gobmerang], "Fire the Gobmerang!", "Launches Gobmerang to fly high in the air",
                             Arc(self.bg, origin=(self.gobmerang.x, self.y), ratio_y=1)))
    self.skills.append(Skill(self, place_entity, 5, [Boulder(self.bg, delay=5)], "Drop the boulder!", "Tells Gobmerang to drop a boulder",
                             SingleTarget(self.bg)))
    self.skills.append(Skill(self, place_entity, 5, [Lava(self.bg)], "Burn them from above!", "Tells Gobmerang to drop a cauldron of oil",
                             SingleTarget(self.bg)))
    self.skills.append(Skill(self, add_path, 5, [], "Fire the Gobmerang!", "Launches Gobmerang to fly high in the air",
                             Arc(self.bg, origin=(self.x, self.y+1), ratio_y=1, steps=120)))
    self.skills.append(Skill(self, place_entity, 5, [Explosion(self.bg, power=20)], "Last chance, boom the machine!", "Explodes the slingshot",
                             CustomArea(self.bg, tiles=Circle(self.bg, radius=4).get_all_tiles(self.slingshot.x+1, self.slingshot.y+1))))

  def start_battle(self):
    self.boomerang = Bouncing(self.bg, sprite_name="boomerang")
    self.gobmerang = Pathing(self.bg, self.side, self.x + (-3 if self.side else 3), self.y, sprite_name='gobmerang')
    self.slingshot = BigMinion(self.bg, self.side, self.x + (-4 if self.side else 2), self.y-1, name="Slingmerang", sprite_name="slingshot")
    self.draw_slingshot()
    self.slingshot_drawn = False
    self.gobmerang_shot = False
    super(Flappy, self).start_battle()

  def update(self):
    if not self.alive:
      return
    if not self.slingshot.alive and self.gobmerang.alive and not self.gobmerang.path:
      self.gobmerang.dissapear()
    elif self.skills[0].cd == self.skills[0].max_cd-1 and not self.slingshot_drawn:
      self.draw_slingshot()
      self.slingshot_drawn = True
    super(Flappy, self).update()

  def use_skill(self, i, x, y):
    if i == 0:
      if self.gobmerang.path:
        return False
      if self.slingshot.alive and super(Flappy, self).use_skill(i, x, y):
        # Gobmerang needs to return to the slingshot afterwards
        self.gobmerang.path.append(self.bg.tiles[(self.gobmerang.x, self.gobmerang.y)])
        self.draw_slingshot()
        self.slingshot_drawn = False
        self.gobmerang_shot = False
        return True
    elif i == 1 or i == 2:
      if not self.gobmerang_shot and len(self.gobmerang.path) > 3:
        index = 2 if i == 1 else 0
        if super(Flappy, self).use_skill(i, self.gobmerang.path[index].x, self.gobmerang.path[index].y):
          self.bg.effects[-1].path = self.gobmerang.path[index:15]
          self.gobmerang_shot = True
          return True
    elif i == 3:
      clone = self.boomerang.clone(x,y)
      if not clone:
        return False
      clone.path = []
      self.skills[i].parameters = [clone]
      if super(Flappy, self).use_skill(i, x, y):
        return True
      else:
        clone.dissapear()
        return False
    elif i == 4:
      if self.slingshot.alive:
        return super(Flappy, self).use_skill(i, x, y)
    return False
