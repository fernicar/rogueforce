from entity import Entity
from entity import BigEntity
import pygame

import effect
import tactic

from collections import defaultdict

class Minion(Entity):
  def __init__(self, battleground, side, x=-1, y=-1, name="minion", sprite_name="minion"):
    super(Minion, self).__init__(battleground, side, x, y, sprite_name, name)
    self.max_hp = 30
    self.hp = 30
    self.armor = defaultdict(lambda: 0)
    self.power = 5
    self.tactic = tactic.null
    self.attack_effect = effect.TempEffect(self.bg, sprite_name='attack_effect')

  def can_be_attacked(self):
    return True

  def clone(self, x, y):
    if self.bg.is_inside(x, y) and self.bg.tiles[(x, y)].entity is None and self.bg.tiles[(x, y)].is_passable(self):
      return self.__class__(self.bg, self.side, x, y, self.name, self.character_name)
    return None

  def die(self):
    super(Minion, self).die()
    if self in self.bg.minions:
      self.bg.generals[self.side].minions_alive -= 1

  def enemy_reachable(self, diagonals=False):
    order = [(1, 0), (-1, 0), (0, -1), (0, 1)]
    if diagonals:
      order.extend([(1, -1), (1, 1), (-1, -1), (-1, 1)])
    for (i, j) in order:
      enemy = self.bg.tiles[(self.x + (-i if self.side else i), self.y + j)].entity
      if enemy and not self.is_ally(enemy) and enemy.can_be_attacked():
        return enemy
    return None
 
  def follow_tactic(self):
    self.tactic(self)

  def get_attacked(self, enemy, power=None, attack_effect=None, attack_type=None):
    super().get_attacked(enemy, power, attack_effect, attack_type)
    if not power:
      power = enemy.power
    if not attack_effect:
      attack_effect = enemy.attack_effect
    if not attack_type:
      attack_type = enemy.attack_type
    self.hp -= max(0, power - self.armor[attack_type])
    if attack_effect:
      attack_effect.clone(self.x, self.y)
    if self.hp <= 0:
      self.hp = 0
      self.die()
      enemy.register_kill(self)

  def get_healed(self, amount):
    self.hp += amount
    if self.hp > self.max_hp: self.hp = self.max_hp

  def try_attack(self):
    enemy = self.enemy_reachable()
    if enemy:
      self.trigger_attack_animation()
      enemy.get_attacked(self)
    return enemy != None
    
  def update(self):
    if not self.alive: return
    super().update()
    if self.next_action <= 0:
      self.reset_action()
      if not self.try_attack():
        self.follow_tactic()
    else: self.next_action -= 1

class BigMinion(BigEntity, Minion):
  def __init__(self, battleground, side, x=-1, y=-1, name="Giant", sprite_name="giant"):
    BigEntity.__init__(self, battleground, side, x, y, sprite_name, name)
    Minion.__init__(self, battleground, side, x, y, name, sprite_name)
    self.max_hp *= self.length
    self.hp = self.max_hp
    
  def clone(self, x, y):
    for (pos_x, pos_y) in [(x+i, y+j) for i in range (0, self.length) for j in range (0, self.length)]:
      if not self.bg.is_inside(pos_x, pos_y) or self.bg.tiles[(pos_x, pos_y)].entity is not None or not self.bg.tiles[(x, y)].is_passable(self):
        return None
    entity = self.__class__(self.bg, self.side, x, y, self.name, self.character_name)
    entity.update_body()
    return entity

  def enemy_reachable(self):
    for (dx, dy) in [(1 if self.side == 0 else -1, 0), (1 if self.side == 0 else -1, 0), (0, 1), (0, -1)]:
      for (x,y) in [(self.x+dx+x,self.y+dy+y) for x in range (0, self.length) for y in range (0, self.length)]:
        enemy = self.bg.tiles[(x, y)].entity
        if enemy is not None and not self.is_ally(enemy) and enemy.can_be_attacked():
          return enemy
    return None

class RangedMinion(Minion):
  def __init__(self, battleground, side, x=-1, y=-1, name="archer", sprite_name="archer"):
    super(RangedMinion, self).__init__(battleground, side, x, y, name, sprite_name)
    self.max_hp = 10
    self.hp = 10
    self.power = 1
    self.ranged_power = 4
    self.default_next_action = 10
    self.reset_action()

  def clone(self, x, y):
    if super(RangedMinion, self).clone(x, y) == None: return None
    return self.__class__(self.bg, self.side, x, y, self.name, self.character_name)

  def follow_tactic(self):
    if self.tactic is None: return
    next_x = self.x+1 if self.side == 0 else self.x-1
    if self.tactic == tactic.stop and self.bg.tiles[(next_x, self.y)].entity == None:
      self.trigger_attack_animation()
      self.bg.effects.append(effect.Arrow(self.bg, self.side, next_x, self.y, self.ranged_power))
    else: super(RangedMinion, self).follow_tactic()
