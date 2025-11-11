from __future__ import annotations
from area import *
from formation import *
from minion import *
from sieve import *
from skill import *
from status import *
import effect
import tactic

from concepts import ENTITY_DEFAULT
from typing import List, Optional, Tuple, Any, TYPE_CHECKING
import math

if TYPE_CHECKING:
    from battleground import Battleground, Tile
    from ai.ai_controller_optimized import AIController
    from skill import Skill

# Import AI Controller for computer-controlled opponents
from ai.ai_controller_optimized import AIController

class General(Minion):
    """Represents a general unit that commands minions and has special abilities.

    Generals are powerful units that can command tactics, use skills, and have
    various special abilities. They can also be swapped out during battle.

    Attributes:
        name: The name of this general
        max_hp: Maximum health points
        hp: Current health points
        cost: Requisition cost to deploy
        death_quote: Quote displayed when the general dies
        flag: Current flag position for movement targeting
        formation: Formation object for minion deployment
        minion: Template minion for spawning
        skills: List of available skills
        starting_minions: Number of minions this general starts with
        tactics: List of available tactical commands
        tactic_quotes: Display names for tactics
        selected_tactic: Currently selected tactic
        previous_tactic: Previously selected tactic
        swap_cd: Cooldown for swapping generals
        swap_max_cd: Maximum swap cooldown
        swap_sickness: Action delay after swapping
        last_skill_used: Index of last used skill
        armor: Armor values by damage type
        power: Attack power
        ai_controller: AI controller for computer-controlled generals
    """

    def __init__(self, battleground: Battleground, side: int, x: int = -1, y: int = -1, name: str = "General", color: Tuple[int, int, int] = ENTITY_DEFAULT) -> None:
        super(General, self).__init__(battleground, side, x, y, name[0], name, color) # Use name[0] as sprite_name/char
        self.max_hp = 300
        self.cost = 250
        self.death_quote = "..."
        self.flag = None
        self.formation = Rows(self)
        self.minion = Minion(self.bg, self.side, character_name=name, sprite_name='b' if side else 'd') # sprite_name is the fallback char
        self.skills: List['Skill'] = []
        self.starting_minions = 101
        self.tactics = [tactic.stop, tactic.forward, tactic.backward, tactic.go_sides, tactic.go_center, tactic.attack_general, tactic.defend_general]
        self.tactic_quotes = ["Stop/Fire", "Forward", "Backward", "Go sides", "Go center", "Attack", "Defend"]
        self.selected_tactic = self.tactics[0]
        self.previous_tactic = self.tactics[0]
        self.swap_cd = 0
        self.swap_max_cd = 200
        self.swap_sickness = 10
        self.last_skill_used = -1
        self.copied_skill = -1
        self.armor["physical"] = 2
        self.power = 10

        # AI Controller for computer-controlled generals
        self.ai_controller: Optional['AIController'] = None

        # Scenario-specific attributes (added dynamically in scenario.py)
        self.target: Optional[Tuple[int, int]] = None
        self.home: Optional[Tuple[int, int]] = None
        self.deployed: bool = False
        self.requisition: int = 0

    def ai_action(self, turn: int) -> Optional[Any]:
        """AI action for computer-controlled generals.

        Delegates decision-making to the AI controller when available.
        For human players, this returns None and lets the game handle input normally.

        Args:
            turn: Current turn number

        Returns:
            AI decision result or None for human players
        """
        if self.ai_controller:
            return self.ai_controller.decide_action(turn)
        return None

    def can_be_pushed(self, dx: int, dy: int) -> bool:
        """Check if this general can be pushed (generals cannot be pushed).

        Args:
            dx: X direction of push
            dy: Y direction of push

        Returns:
            Always False - generals cannot be pushed
        """
        return False

    def change_battleground(self, bg: Battleground, x: int, y: int) -> None:
        """Change the battleground this general is on.

        Args:
            bg: New battleground
            x: New x position
            y: New y position
        """
        super(General, self).change_battleground(bg, x, y)
        if self.minion is not None:
            self.minion.change_battleground(bg, -1, -1)
        # Update AI controller's battlefield reference if it exists
        if self.ai_controller:
            self.ai_controller.bg = bg

    def command_tactic(self, i: int) -> None:
        """Command all allied minions to use a specific tactic.

        Args:
            i: Index of the tactic in the tactics list
        """
        self.selected_tactic = self.tactics[i]
        for m in self.bg.minions:
            if m.side == self.side:
                m.tactic = self.tactics[i]

    def initialize_skills(self) -> None:
        """Initialize the general's skill set with default skills."""
        self.skills = []
        self.skills.append(Skill(self, heal, 50, [100], "Don't die!", "1", SingleTarget(self.bg, is_ally_minion, self)))
        self.skills.append(Skill(self, heal, 50, [20], "Heal you all men!", "2", AllBattleground(self.bg, is_minion, self)))
        self.skills.append(Skill(self, place_entity, 50, [Mine(self.bg)], "Can't touch this", "3", SingleTarget(self.bg, is_empty)))
        self.skills.append(Skill(self, sonic_waves, 50, [10, 3], "Sonic Waves", "4"))
        self.skills.append(Skill(self, water_pusher, 50, [], "Hidro Pump", "5", SingleTarget(self.bg)))

    def place_flag(self, x: int, y: int) -> None:
        """Place or move the general's flag to target coordinates.

        Args:
            x: Target x coordinate
            y: Target y coordinate
        """
        if self.flag:
            if (self.flag.x, self.flag.y) == (x,y):
                return
            self.flag.dissapear()
        if self.bg.is_inside(x, y):
            self.flag = effect.Blinking(self.bg, self.side, x, y, 'q', self.original_color) # Restore original 'q' character
        else:
            self.flag = None

    def recommand_tactic(self) -> None:
        """Re-command the currently selected tactic to all minions."""
        self.command_tactic(self.tactics.index(self.selected_tactic))

    def recount_minions_alive(self) -> None:
        """Update the count of living minions for this general."""
        self.minions_alive = len([x for x in self.bg.minions if x.alive and x.side == self.side])

    def start_battle(self) -> None:
        """Initialize the general for battle start."""
        self.initialize_skills()
        self.command_tactic(0)
        self.swap_cd = 200

    def start_scenario(self) -> None:
        """Initialize the general for scenario start."""
        self.deployed = False
        self.hp = self.max_hp
        self.minions_alive = self.starting_minions
        self.requisition = 0

    def swap(self, i: int) -> bool:
        """Attempt to swap this general with a reserve general.

        Args:
            i: Index of the reserve general to swap with

        Returns:
            True if swap was successful, False otherwise
        """
        r = self.bg.reserves[self.side]
        if self.swap_cd >= self.swap_max_cd and len(r) > i:
            self.bg.generals[self.side] = r[i]
            r[i].swap_cd = 0
            r[i].next_action = r[i].swap_sickness
            self.bg.tiles[(self.x, self.y)].entity = r[i]
            (r[i].x, r[i].y) = (self.x, self.y)
            if self.flag:
                r[i].place_flag(self.flag.x, self.flag.y)
                self.flag.dissapear()
                self.flag = None
            self.bg.reserves[self.side][i] = self
            return True
        return False

    def update(self) -> None:
        """Update the general's state each game tick."""
        if not self.alive:
            return

        # First, call the inherited update from Entity to handle statuses and animations
        super(General, self).update()

        # Then, update skills and swap cooldown
        for s in self.skills:
            s.update()
        self.swap_cd = min(self.swap_cd+1, self.swap_max_cd)

        # Now, process actions if the timer is up
        if self.next_action <= 0:
            self.reset_action()
            # General-specific logic: move towards flag or attack
            if self.flag and self.bg.is_inside(self.flag.x, self.flag.y):
                dx = self.flag.x - self.x
                dy = self.flag.y - self.y
                # Use copysign to move 1 step in the right direction
                move_dx = int(math.copysign(1, dx)) if dx != 0 else 0
                move_dy = int(math.copysign(1, dy)) if dy != 0 else 0
                if not self.move(move_dx, move_dy) or (self.x, self.y) == (self.flag.x, self.flag.y):
                    self.place_flag(-1, -1) # Arrived or blocked, remove flag
            else:
                # If no flag, try to attack like a minion
                if not self.try_attack():
                    self.next_action = -1 # If nothing to do, wait
        else:
            self.next_action -= 1

    def update_color(self) -> None:
        """Update the general's color to original color (no health-based coloring)."""
        self.color = self.original_color

    def use_skill(self, i: int, x: int, y: int) -> bool:
        """Attempt to use a skill at the specified coordinates.

        Args:
            i: Index of the skill to use
            x: Target x coordinate
            y: Target y coordinate

        Returns:
            True if skill was used successfully, False otherwise
        """
        skill = self.skills[i]
        if skill.is_ready():
            if skill.use(x, y):
                for s in self.skills:
                    s.change_cd(-5)
                skill.reset_cd()
                self.last_skill_used = i
                return True
        return False

class Conway(General):
    def __init__(self, battleground, side, x=-1, y=-1, name="Conway", color=ENTITY_DEFAULT):
        super(Conway, self).__init__(battleground, side, x, y, name, color)
        self.death_quote = "This is more like a game of... death"
        self.tactics = [tactic.stop, tactic.null]
        self.tactic_quotes = ["Stop", "Live life"]
        self.selected_tactic = self.tactics[0]

    def initialize_skills(self):
        self.skills = []
        self.skills.append(Skill(self, minion_glider, 50, [False], "Glide from the top!", "", SingleTarget(self.bg, is_empty)))
        self.skills.append(Skill(self, minion_glider, 50, [True], "Glide from the bottom!", "", SingleTarget(self.bg, is_empty)))
        self.skills.append(Skill(self, minion_lwss, 50, [], "Lightweight strike force!", "", SingleTarget(self.bg, is_empty)))
        self.skills.append(Skill(self, apply_status, 50, [Poison(None, 5, 19, 4)],
                "Poison on your veins!", "", SingleTarget(self.bg, is_enemy, self)))

    def live_life(self, tile: 'Tile') -> None:
        neighbours = 0
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                (x, y) = (tile.x+i, tile.y+j)
                if (i, j) == (0, 0) or not self.bg.is_inside(x, y): continue
                entity = self.bg.tiles[(x, y)].entity
                if entity is not None and entity.is_ally(self): neighbours += 1
        if tile.entity is None and neighbours == 3 and tile.passable: self.next_gen_births.append(tile)
        elif tile.entity is not None and tile.entity.is_ally(self) and tile.entity != self:
            if neighbours > 3: self.next_gen_deaths.append(tile)
            elif neighbours < 2: self.next_gen_deaths.append(tile)

    def update(self):
        if not self.alive: return
        if self.selected_tactic == tactic.null:
            if self.next_action <= 0:
                self.reset_action()
                self.next_gen_births = []
                self.next_gen_deaths = []
                for t in self.bg.tiles.values():
                    self.live_life(t)
                for tile in self.next_gen_births:
                    if self.minion is not None:
                        minion_placed = self.minion.clone(tile.x, tile.y)
                        if minion_placed is not None:
                            self.bg.minions.append(minion_placed)
                for tile in self.next_gen_deaths:
                    if tile.entity is not None:
                        tile.entity.die()
                self.recount_minions_alive()
            else:
                self.next_action -= 1
        super(Conway, self).update()

class Emperor(General):
    def __init__(self, battleground, side, x=-1, y=-1, name="Emperor", color=ENTITY_DEFAULT):
        super(Emperor, self).__init__(battleground, side, x, y, name, color)
        self.max_hp = 60
        self.death_quote = "Nightspirit... embrace my soul..."
        self.human_form = True
        self.minion = RangedMinion(self.bg, self.side, name="wizard", character_name="wizard")
        self.minion.attack_effects = [')', '(']
        self.starting_minions = 0
        self.transform_index = 3

    def die(self):
        if self.human_form:
            self.use_skill(self.transform_index, 0, 0)
        else:
            self.transform()
            super(Emperor, self).die()

    def initialize_skills(self):
        self.skills = []
        self.skills.append(Skill(self, restock_minions, 25, [21], "Once destroyed, their souls are being summoned", ""))
        self.skills.append(Skill(self, apply_status, 50, [FreezeCooldowns(None, 15)], "I curse you of all men", "",
                AllBattleground(self.bg, is_enemy_general, self)))
        self.skills.append(Skill(self, water_pusher, 50, [], "Towards the Pantheon", "", SingleTarget(self.bg)))
        self.skills.append(Skill(self, null, 200, [], "This shouldn't be showed", ""))

    def start_battle(self):
        super(Emperor, self).start_battle()
        self.minions_alive = 0

    def transform(self):
        if not self.human_form:
            self.character_name = 'Emperor'
            self.name = "Emperor"
            return
        self.human_form = False
        self.hp = self.max_hp
        self.character_name = 'Nightspirit'
        self.name = "Nightspirit"
        self.original_color = ENTITY_DEFAULT
        self.color = self.original_color
        self.skills = []
        self.skills.append(Skill(self, sonic_waves, 50, [10, 3], "Thus spake the Nightspirit", ""))
        self.skills.append(Skill(self, darkness, 50, [20], "Nightside eclipse", "", AllBattleground(self.bg)))
        self.skills.append(Skill(self, consume, 50, [1, 1], "My wizards are many, but their essence is mine", "",
                AllBattleground(self.bg, is_ally_minion, self)))
        self.skills.append(Skill(self, sonic_waves, 250, [50, 50],
                "O'Nightspirit... I am one with thee, I am the eternal power, I am the Emperor!", ""))
        return True

    def use_skill(self, i, x, y):
        skill_used = super(Emperor, self).use_skill(i, x, y)
        if skill_used and self.human_form and i == self.transform_index: self.transform()
        return skill_used
