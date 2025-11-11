"""
Optimized AI Controller for Rogue Force computer-controlled opponents.

This module contains efficient AI logic that makes tactical decisions
for computer-controlled generals based on battlefield analysis.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
import random

if TYPE_CHECKING:
    from general import General

from . import evaluators_optimized as evaluators


class AIController:
    """
    Optimized AI controller that makes tactical decisions for computer generals.
    
    Features:
    - Balanced skill usage thresholds
    - Action cooldown system to prevent spam
    - Performance-optimized battlefield evaluation
    - Tactical command integration
    """
    
    def __init__(self, general: 'General') -> None:
        """
        Initialize the AI controller for a specific general.

        Args:
            general: The General instance this AI controls
        """
        self.general = general
        self.bg: Any = general.bg # Battleground with potential dynamic attributes like DEBUG
        
        # Balanced AI personality configuration
        self.personality = {
            'min_skill_priority': 20,         # Lower threshold for more skill usage
            'tactical_threshold': 30,         # Lower threshold for more tactical commands
            'move_vs_skill_chance': 0.6,     # Higher chance to move instead of spamming skills
            'aggression_level': 0.5,         # Balanced aggression
            'caution_level': 0.5,            # Balanced caution
            'skill_cooldown_min': 2,         # Minimum turns between similar skills
            'flag_cooldown_min': 3,          # Minimum turns between flag placements
        }
        
        # Action tracking for spam prevention
        self.last_actions = []
        self.action_counts = {} # Track action frequencies
        self.max_action_history = 15
        self.last_skill_use = {} # Track when skills were last used
        self.last_flag_positions = [] # Track recent flag positions
        self.last_movement_target = None # Track last movement target to prevent repetition

        # DEBUG: Spam detection and termination
        self.consecutive_same_flag_count = 0
        self.last_flag_position = None

        # Tactic stability and persistence tracking
        self.current_tactic = None # Currently active tactic index
        self.tactic_start_turn = 0 # When current tactic was set
        self.tactic_effectiveness_history = [] # Track how well tactics perform
        self.min_tactic_duration = 15 # Minimum turns to maintain a tactic
        self.max_tactic_duration = 45 # Maximum turns before forced reassessment

    def decide_action(self, turn):
        """
        Advanced AI decision-making with strategic planning and adaptive behavior.

        Args:
            turn: Current turn number

        Returns:
            str: Action command or None
        """
        # Debug output
        if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
            print(f"[AI] Turn {turn}: Side {self.general.side} - Strategic Analysis...")

        # Get comprehensive battlefield assessment
        battle_state = self._analyze_battlefield_state(turn)
        strategy = self._determine_optimal_strategy(battle_state)

        # Execute strategy with priority order
        action = self._execute_strategy(strategy, battle_state)
        if action:
            self._record_action(action)
            return action

        # GUARANTEED FALLBACK: AI must always take some action
        fallback_action = self._get_guaranteed_action(battle_state)
        if fallback_action:
            self._record_action(fallback_action)
            if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                print(f"[AI] Fallback action: {fallback_action.strip()}")
            return fallback_action

        # ABSOLUTE LAST RESORT: Basic movement toward enemy
        emergency_action = self._emergency_action(battle_state)
        if emergency_action:
            self._record_action(emergency_action)
            if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                print(f"[AI] Emergency action: {emergency_action.strip()}")
            return emergency_action

        # If all else fails, do nothing (shouldn't happen)
        if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
            print(f"[AI] No action possible - battle state: {battle_state['phase']}")
        return None

    def _analyze_battlefield_state(self, turn):
        """Comprehensive battlefield analysis for strategic decision making."""
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]

        # Basic metrics
        our_minions = [m for m in self.bg.minions if m.is_ally(self.general) and m.alive]
        enemy_minions = [m for m in self.bg.minions if not m.is_ally(self.general) and m.alive]

        # Health ratios
        our_health_ratio = 1.0
        if self.general.hp is not None and self.general.max_hp is not None and self.general.max_hp > 0:
            our_health_ratio = self.general.hp / self.general.max_hp
        enemy_health_ratio = 1.0
        if enemy_general.hp is not None and enemy_general.max_hp is not None and enemy_general.max_hp > 0:
            enemy_health_ratio = enemy_general.hp / enemy_general.max_hp

        # Positioning analysis
        distance_to_enemy = abs(enemy_general.x - self.general.x) + abs(enemy_general.y - self.general.y)
        our_center_x = sum(m.x for m in our_minions) / len(our_minions) if our_minions else self.general.x
        enemy_center_x = sum(m.x for m in enemy_minions) / len(enemy_minions) if enemy_minions else enemy_general.x

        # Formation analysis
        our_spread = max((abs(m.x - our_center_x) + abs(m.y - self.general.y) for m in our_minions), default=0)
        enemy_spread = max((abs(m.x - enemy_center_x) + abs(m.y - enemy_general.y) for m in enemy_minions), default=0)

        # Tactical assessment
        urgency = evaluators.evaluate_tactical_urgency(self.general)
        effectiveness = evaluators.get_combat_effectiveness_score(self.general)

        # Determine battle phase
        if turn < 50:
            phase = "early_game"
        elif our_health_ratio < 0.3 or enemy_health_ratio < 0.3:
            phase = "end_game"
        elif distance_to_enemy < 15:
            phase = "combat"
        else:
            phase = "positioning"

        return {
            'phase': phase,
            'urgency': urgency,
            'effectiveness': effectiveness,
            'our_health': our_health_ratio,
            'enemy_health': enemy_health_ratio,
            'distance': distance_to_enemy,
            'our_minions': len(our_minions),
            'enemy_minions': len(enemy_minions),
            'our_spread': our_spread,
            'enemy_spread': enemy_spread,
            'our_center': our_center_x,
            'enemy_center': enemy_center_x,
            'turn': turn
        }

    def _determine_optimal_strategy(self, battle_state):
        """Determine the best strategy based on current battle state."""
        phase = battle_state['phase']
        urgency = battle_state['urgency']

        if phase == "early_game":
            return self._early_game_strategy(battle_state)
        elif phase == "positioning":
            return self._positioning_strategy(battle_state)
        elif phase == "combat":
            return self._combat_strategy(battle_state)
        elif phase == "end_game":
            return self._end_game_strategy(battle_state)
        else:
            return {'type': 'defensive', 'priority': ['tactical', 'skill', 'move']}

    def _early_game_strategy(self, battle_state):
        """Early game: Focus on positioning and minion deployment."""
        if battle_state['our_minions'] < 5:
            return {'type': 'aggressive_deployment', 'priority': ['tactical', 'move', 'skill']}
        else:
            return {'type': 'positioning', 'priority': ['move', 'tactical', 'skill']}

    def _positioning_strategy(self, battle_state):
        """Positioning phase: Control territory and prepare for engagement."""
        if battle_state['distance'] > 20:
            return {'type': 'advance', 'priority': ['move', 'tactical', 'skill']}
        elif battle_state['our_spread'] > battle_state['enemy_spread'] * 1.2:
            return {'type': 'consolidate', 'priority': ['tactical', 'move', 'skill']}
        else:
            return {'type': 'flank', 'priority': ['move', 'tactical', 'skill']}

    def _combat_strategy(self, battle_state):
        """Combat phase: Aggressive tactics and skill usage."""
        if battle_state['urgency'] > 60:
            return {'type': 'aggressive', 'priority': ['skill', 'tactical', 'move']}
        elif battle_state['our_health'] < battle_state['enemy_health']:
            return {'type': 'defensive', 'priority': ['tactical', 'skill', 'move']}
        else:
            return {'type': 'balanced_combat', 'priority': ['skill', 'tactical', 'move']}

    def _end_game_strategy(self, battle_state):
        """End game: Go for the kill or survive."""
        if battle_state['our_health'] > battle_state['enemy_health']:
            return {'type': 'finish_him', 'priority': ['skill', 'move', 'tactical']}
        else:
            return {'type': 'survive', 'priority': ['skill', 'tactical', 'move']}

    def _execute_strategy(self, strategy, battle_state):
        """Execute the chosen strategy by trying actions in priority order."""
        strategy_type = strategy['type']
        priorities = strategy['priority']

        for action_type in priorities:
            if action_type == 'tactical':
                action = self._try_tactical_action(strategy_type, battle_state)
                if action:
                    return action
            elif action_type == 'skill':
                action = self._try_skill_action(strategy_type, battle_state)
                if action:
                    return action
            elif action_type == 'move':
                action = self._try_movement_action(strategy_type, battle_state)
                if action:
                    return action

        return None

    def _try_tactical_action(self, strategy_type, battle_state):
        """Try to execute a tactical command based on strategy with persistence."""
        current_turn = len(self.last_actions)
        tactic_age = current_turn - self.tactic_start_turn

        # TACTIC PERSISTENCE: If we have an active tactic, maintain it for minimum duration
        if self.current_tactic is not None and tactic_age < self.min_tactic_duration:
            if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                print(f"[AI] Maintaining tactic {self.current_tactic} (age: {tactic_age}/{self.min_tactic_duration})")
            return None # Don't change tactics yet

        # FORCE CHANGE: If tactic is too old, must reassess
        force_change = (self.current_tactic is not None and tactic_age >= self.max_tactic_duration)

        # Smart tactical decisions based on strategy - check available tactics first
        num_tactics = len(self.general.tactics)

        if strategy_type in ['aggressive', 'finish_him']:
            # Attack mode when being aggressive
            if battle_state['distance'] < 12 and num_tactics > 5: # Check if tactic 5 exists
                desired_tactic = 5 # attack_general
                if force_change or self.current_tactic != desired_tactic:
                    action = "tactic5\n"
                    if not self._is_action_spam(action):
                        if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                            print("[AI] Aggressive: Attack mode")
                        return action

        elif strategy_type == 'defensive':
            # Defend when hurt
            if battle_state['our_health'] < 0.7 and num_tactics > 6: # Check if tactic 6 exists
                desired_tactic = 6 # defend_general
                if force_change or self.current_tactic != desired_tactic:
                    action = "tactic6\n"
                    if not self._is_action_spam(action):
                        if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                            print("[AI] Defensive: Protect general")
                        return action

        elif strategy_type == 'consolidate':
            # Tighten formation
            if num_tactics > 4: # Check if tactic 4 exists
                desired_tactic = 4 # go_center
                if force_change or self.current_tactic != desired_tactic:
                    action = "tactic4\n"
                    if not self._is_action_spam(action):
                        if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                            print("[AI] Consolidate: Center formation")
                        return action

        elif strategy_type == 'aggressive_deployment':
            # Spread out for area control
            if num_tactics > 3: # Check if tactic 3 exists
                desired_tactic = 3 # go_sides
                if force_change or self.current_tactic != desired_tactic:
                    action = "tactic3\n"
                    if not self._is_action_spam(action):
                        if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                            print("[AI] Deploy: Spread formation")
                        return action

        # Fallback to basic tactical logic with persistence check
        should_command, tactic_index, reason = evaluators.should_use_tactical_command(self.general)
        if should_command and battle_state['urgency'] >= self.personality['tactical_threshold']:
            if force_change or self.current_tactic != tactic_index:
                action = f"tactic{tactic_index}\n"
                if not self._is_action_spam(action):
                    if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                        print(f"[AI] Tactical: tactic{tactic_index} - {reason}")
                    return action

        return None

    def _try_skill_action(self, strategy_type, battle_state):
        """Try to use a skill based on strategy."""
        best_skill_action = None
        best_score = 0

        for i, skill in enumerate(self.general.skills):
            if not skill.is_ready():
                continue

            priority, should_use, reason = evaluators.evaluate_skill_priority_with_cooldowns(
                self.general, i, skill
            )

            if not should_use:
                continue

            # Strategy-specific skill priority adjustments
            skill_desc = skill.description.lower()
            strategy_multiplier = 1.0

            if strategy_type in ['aggressive', 'finish_him']:
                if any(k in skill_desc for k in ['damage', 'explosion', 'burst']):
                    strategy_multiplier = 1.5 # Boost damage skills
            elif strategy_type == 'defensive':
                if any(k in skill_desc for k in ['heal', 'shield', 'armor']):
                    strategy_multiplier = 1.8 # Boost defensive skills
            elif strategy_type == 'survive':
                if any(k in skill_desc for k in ['heal', 'teleport', 'blink']):
                    strategy_multiplier = 2.0 # Critical survival skills

            # TACTIC ↔ SKILL COORDINATION: Boost skills that work well with current tactic
            tactic_multiplier = self._get_tactic_skill_synergy(skill_desc, battle_state)
            adjusted_priority = priority * strategy_multiplier * tactic_multiplier

            if adjusted_priority >= self.personality['min_skill_priority']:
                target, score = self._get_skill_target(i, skill)
                if target:
                    action = f"skill{i} {target[0]} {target[1]}\n"

                    if not self._is_action_spam(action) and self._check_skill_cooldown(i):
                        final_score = adjusted_priority + score

                        if final_score > best_score:
                            best_score = final_score
                            best_skill_action = action
                            best_skill_info = {
                                'skill': skill,
                                'index': i,
                                'priority': adjusted_priority,
                                'effectiveness': score,
                                'reason': reason
                            }

        if best_skill_action and best_score > self.personality['min_skill_priority']:
            if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                print(f"[AI] {strategy_type.title()}: {best_skill_info['skill'].description[:25]}... "
                      f"(score: {best_score:.1f})")

            if random.random() > self.personality['move_vs_skill_chance']:
                self._mark_skill_used(best_skill_info['index'])
                return best_skill_action

        return None

    def _try_movement_action(self, strategy_type, battle_state):
        """Try to execute a movement action based on strategy with skill coordination."""
        # FIRST PRIORITY: Position for optimal skill usage
        skill_based_target = self._calculate_skill_optimized_position(battle_state)
        if skill_based_target:
            distance_to_target = abs(skill_based_target[0] - self.general.x) + abs(skill_based_target[1] - self.general.y)
            if distance_to_target > 1: # Allow closer positioning for skills
                move_action = f"flag {skill_based_target[0]} {skill_based_target[1]}\n"
                if not self._is_action_spam(move_action):
                    self.last_movement_target = skill_based_target
                    if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                        print(f"[AI] Skill-Optimized: Move to {skill_based_target} for skill positioning")
                    return move_action
                else:
                    if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                        print(f"[AI] Skill target {skill_based_target} rejected as spam (recent positions: {self.last_flag_positions[-5:]})")

        # SECOND PRIORITY: Strategic positioning based on battle state
        if strategy_type == 'flank':
            move_target = self._calculate_flanking_position(battle_state)
        elif strategy_type in ['advance', 'aggressive_deployment']:
            if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                print(f"[AI] Trying strategic advance movement for {strategy_type}")
            move_target = self._calculate_advance_position(battle_state)
            if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                print(f"[AI] Strategic advance returned: {move_target}")
        elif strategy_type == 'survive':
            move_target = self._calculate_retreat_position(battle_state)
        else:
            move_target = self._calculate_advance_position(battle_state)

        # Ensure we don't repeat the same movement target
        if move_target and self.last_movement_target == move_target:
            move_target = self._find_alternative_movement_target(battle_state, move_target)

        if move_target:
            distance_to_target = abs(move_target[0] - self.general.x) + abs(move_target[1] - self.general.y)

            if distance_to_target > 2:
                move_action = f"flag {move_target[0]} {move_target[1]}\n"

                if not self._is_action_spam(move_action):
                    self.last_movement_target = move_target

                    if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                        print(f"[AI] {strategy_type.title()}: Move to {move_target} (dist: {distance_to_target})")

                    return move_action
                else:
                    if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                        print(f"[AI] Strategic target {move_target} rejected as spam")

        return None

    def _find_alternative_movement_target(self, battle_state, original_target):
        """Find an alternative movement target when the original would be repetitive."""
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]

        # Generate alternative positions around the enemy
        alternatives = []
        base_x, base_y = enemy_general.x, enemy_general.y

        # Try different offsets
        for dx in [-5, -4, -3, -2, 2, 3, 4, 5]:
            for dy in [-3, -2, -1, 1, 2, 3]:
                alt_x = base_x + dx
                alt_y = base_y + dy

                # Ensure valid bounds
                alt_x = max(1, min(self.bg.width - 2, alt_x))
                alt_y = max(1, min(self.bg.height - 2, alt_y))

                # Make sure it's different from the original and not occupied
                if (alt_x, alt_y) != original_target:
                    if self.bg.is_inside(alt_x, alt_y):
                        tile = self.bg.tiles[(alt_x, alt_y)]
                        if not tile.entity or tile.entity == self.general:
                            distance = abs(alt_x - self.general.x) + abs(alt_y - self.general.y)
                            if distance >= 3: # Ensure meaningful movement
                                alternatives.append((alt_x, alt_y))

        # Return a random alternative if available
        if alternatives:
            return random.choice(alternatives)

        # If no alternatives, return the original (better than no movement)
        return original_target

    def _calculate_flanking_position(self, battle_state):
        """Calculate a flanking position around the enemy."""
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]

        # Try to position to the side of enemy general
        flank_directions = [
            (enemy_general.x - 8, enemy_general.y), # Left flank
            (enemy_general.x + 8, enemy_general.y), # Right flank
            (enemy_general.x, enemy_general.y - 5), # Forward flank
        ]

        # Find best flanking position
        best_pos = None
        best_score = -1

        for x, y in flank_directions:
            if self.bg.is_inside(x, y):
                # Score based on distance from enemy and our current position
                dist_from_enemy = abs(x - enemy_general.x) + abs(y - enemy_general.y)
                dist_from_us = abs(x - self.general.x) + abs(y - self.general.y)

                # Prefer positions that are close to enemy but not too close to us (to avoid spam)
                score = (20 - dist_from_enemy) + max(0, 10 - dist_from_us)

                if score > best_score:
                    best_score = score
                    best_pos = (x, y)

        return best_pos

    def _calculate_retreat_position(self, battle_state):
        """Calculate a safe retreat position."""
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]

        # Retreat toward our side of the map
        if self.general.side == 0:
            retreat_x = max(2, self.general.x - 5)
        else:
            retreat_x = min(self.bg.width - 3, self.general.x + 5)

        retreat_y = self.general.y + random.randint(-2, 2)

        # Ensure valid position
        retreat_x = max(1, min(self.bg.width - 2, retreat_x))
        retreat_y = max(1, min(self.bg.height - 2, retreat_y))

        return (retreat_x, retreat_y)

    def _calculate_advance_position(self, battle_state):
        """
        Calculate a smart advance position that gets closer to enemy while avoiding repetition.

        This is better than evaluators.find_strategic_move_target() because it considers
        recent movement history and provides varied positioning.
        """
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]
        distance_to_enemy = battle_state['distance']

        if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
            print(f"[AI] Calculating advance position: AI at ({self.general.x}, {self.general.y}), Enemy at ({enemy_general.x}, {enemy_general.y}), Distance: {distance_to_enemy}")

        # If we're already close to enemy, don't advance further
        if distance_to_enemy <= 8:
            return None

        # Generate candidate positions around enemy general
        candidates = []
        base_x, base_y = enemy_general.x, enemy_general.y

        # Sample positions at different distances from enemy
        for dist in [6, 8, 10, 12]:
            for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                # Convert angle to dx, dy
                rad = angle * 3.14159 / 180
                dx = int(dist * (1 if angle <= 90 or angle >= 270 else -1) * (0.7 if 45 <= angle <= 135 or 225 <= angle <= 315 else 1))
                dy = int(dist * (1 if angle >= 0 and angle <= 180 else -1) * (0.7 if 135 <= angle <= 225 or 315 <= angle <= 45 else 1))

                x = base_x + dx
                y = base_y + dy

                # Ensure valid bounds
                x = max(1, min(self.bg.width - 2, x))
                y = max(1, min(self.bg.height - 2, y))

                if self.bg.is_inside(x, y):
                    candidates.append((x, y))

        # Score each candidate
        best_pos = None
        best_score = -1
        candidates_with_scores = []

        for x, y in candidates[:15]: # Limit for performance
            # Distance from enemy (closer is MUCH better - CRITICAL FIX!)
            dist_from_enemy = abs(x - enemy_general.x) + abs(y - enemy_general.y)
            enemy_score = max(0, 50 - dist_from_enemy) # Much higher weight for proximity to enemy

            # Distance from current position (prefer reasonable movement, not too far)
            dist_from_current = abs(x - self.general.x) + abs(y - self.general.y)
            movement_score = max(0, 15 - abs(dist_from_current - 6)) # Prefer 3-9 tile moves

            # Avoid recently used positions - HEAVY penalty
            recency_penalty = 0
            for recent_x, recent_y in self.last_flag_positions[-8:]: # Check more history
                if abs(x - recent_x) <= 3 and abs(y - recent_y) <= 3: # Larger exclusion zone
                    recency_penalty = 25 # Much heavier penalty

            # Prefer positions that aren't occupied
            tile = self.bg.tiles[(x, y)]
            occupancy_penalty = 5 if (tile.entity and tile.entity != self.general) else 0

            # Minimal randomization to avoid getting stuck but not override good choices
            randomization = random.uniform(-1, 1)

            total_score = enemy_score + movement_score - recency_penalty - occupancy_penalty + randomization

            candidates_with_scores.append((total_score, (x, y)))

        # Sort by score and pick from top 3 to add variety
        candidates_with_scores.sort(key=lambda x: x[0], reverse=True)
        if candidates_with_scores:
            # DEBUG: Show top candidates
            if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                print(f"[AI] Advance candidates (top 5):")
                for i, (score, pos) in enumerate(candidates_with_scores[:5]):
                    dist_to_enemy = abs(pos[0] - enemy_general.x) + abs(pos[1] - enemy_general.y)
                    dist_from_current = abs(pos[0] - self.general.x) + abs(pos[1] - self.general.y)
                    print(f" {i+1}. {pos} (score: {score:.1f}, enemy_dist: {dist_to_enemy}, our_dist: {dist_from_current})")

            # Pick randomly from top 3 candidates to add variety
            top_candidates = candidates_with_scores[:3]
            best_score, best_pos = random.choice(top_candidates)

            if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                print(f"[AI] Selected advance target: {best_pos} (score: {best_score:.1f})")

        return best_pos if best_score > 5 else None

    def _calculate_skill_optimized_position(self, battle_state):
        """
        Calculate the optimal position for the general to maximize skill effectiveness.

        Considers ready skills and finds positions that would make them most effective.
        """
        best_position = None
        best_score = 0

        # Check each ready skill and find optimal casting position
        for i, skill in enumerate(self.general.skills):
            if not skill.is_ready():
                continue

            skill_desc = skill.description.lower()

            # AREA SKILLS: Position for maximum AoE coverage
            if any(keyword in skill_desc for keyword in ["damage", "area", "explosion", "burst", "nova"]):
                position, score = self._find_optimal_aoe_position(skill, battle_state)
                if score > best_score:
                    best_score = score
                    best_position = position

            # HEALING SKILLS: Position near most damaged allies
            elif any(keyword in skill_desc for keyword in ["heal", "restore", "regenerate", "mend"]):
                position, score = self._find_optimal_healing_position(skill, battle_state)
                if score > best_score:
                    best_score = score
                    best_position = position

            # DIRECT SKILLS: Position for optimal targeting
            elif any(keyword in skill_desc for keyword in ["teleport", "blink", "move", "dash", "slash", "cut", "strike"]):
                position, score = self._find_optimal_direct_position(skill, battle_state)
                if score > best_score:
                    best_score = score
                    best_position = position

        # For generals with no optimal skill positions, try basic strategic positioning
        if not best_position:
            enemy_general = self.bg.generals[(self.general.side + 1) % 2]
            # Try positions that get closer to enemy for direct combat
            for dx in [-3, -2, -1, 1, 2, 3]:
                for dy in [-3, -2, -1, 1, 2, 3]:
                    x, y = enemy_general.x + dx, enemy_general.y + dy
                    if self.bg.is_inside(x, y):
                        distance_to_enemy = abs(x - enemy_general.x) + abs(y - enemy_general.y)
                        distance_from_current = abs(x - self.general.x) + abs(y - self.general.y)
                        # Prefer positions closer to enemy but not too far from current
                        if distance_to_enemy <= 5 and distance_from_current >= 2 and distance_from_current <= 6:
                            score = (10 - distance_to_enemy) + (6 - distance_from_current)
                            if score > best_score:
                                best_score = score
                                best_position = (x, y)

        # Only return position if it's significantly better than current
        if best_position and best_score > 5: # Lower threshold for basic positioning
            distance_from_current = abs(best_position[0] - self.general.x) + abs(best_position[1] - self.general.y)
            if distance_from_current > 1: # Allow closer positioning for combat
                return best_position

        return None

    def _find_optimal_aoe_position(self, skill, battle_state):
        """Find the best position to cast an area-of-effect skill."""
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]
        best_pos = None
        best_score = 0

        # Sample positions around enemy concentrations
        sample_positions = []

        # Add positions around enemy general
        for dx in [-3, -2, -1, 0, 1, 2, 3]:
            for dy in [-3, -2, -1, 0, 1, 2, 3]:
                x, y = enemy_general.x + dx, enemy_general.y + dy
                if self.bg.is_inside(x, y):
                    sample_positions.append((x, y))

        # Evaluate each position
        for x, y in sample_positions[:20]: # Limit for performance
            if not self.bg.is_inside(x, y):
                continue

            # Calculate skill effectiveness from this position
            area_tiles = skill.get_area_tiles(x, y)
            if not area_tiles:
                continue

            score = 0
            for tile in area_tiles:
                if tile.entity and not tile.entity.is_ally(self.general):
                    score += 1 # Hit enemy
                    if tile.entity == enemy_general:
                        score += 3 # Bonus for hitting general

            # Prefer positions that are reachable
            distance = abs(x - self.general.x) + abs(y - self.general.y)
            reachability_penalty = max(0, distance - 8) # Penalize very distant positions

            final_score = score - reachability_penalty

            if final_score > best_score:
                best_score = final_score
                best_pos = (x, y)

        return best_pos, best_score

    def _find_optimal_healing_position(self, skill, battle_state):
        """Find the best position to cast a healing skill."""
        best_pos = None
        best_score = 0

        # Find most damaged allies
        damaged_entities = []
        for minion in self.bg.minions:
            if (minion.is_ally(self.general) and minion.alive and
                minion.hp is not None and minion.max_hp is not None and
                minion.hp < minion.max_hp):
                damage_percent = (minion.max_hp - minion.hp) / minion.max_hp
                damaged_entities.append((minion, damage_percent))

        # Also consider general
        general_damage = 0.0
        if (self.general.hp is not None and self.general.max_hp is not None and
            self.general.max_hp > 0):
            general_damage = (self.general.max_hp - self.general.hp) / self.general.max_hp
        if general_damage > 0:
            damaged_entities.append((self.general, general_damage))

        if not damaged_entities:
            return None, 0

        # Sort by damage (most damaged first)
        damaged_entities.sort(key=lambda x: x[1], reverse=True)

        # Try positions near most damaged entities
        for entity, damage in damaged_entities[:3]: # Top 3 most damaged
            # Sample positions around the entity
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    x, y = entity.x + dx, entity.y + dy
                    if self.bg.is_inside(x, y):
                        # Calculate healing coverage from this position
                        area_tiles = skill.get_area_tiles(x, y)
                        if area_tiles:
                            coverage_score = 0
                            for tile in area_tiles:
                                if tile.entity and tile.entity.is_ally(self.general):
                                    entity_damage = (tile.entity.max_hp - tile.entity.hp) / tile.entity.max_hp
                                    coverage_score += entity_damage * 10 # Weight by damage

                            distance = abs(x - self.general.x) + abs(y - self.general.y)
                            reachability_penalty = max(0, distance - 6)

                            final_score = coverage_score - reachability_penalty

                            if final_score > best_score:
                                best_score = final_score
                                best_pos = (x, y)

        return best_pos, best_score

    def _find_optimal_direct_position(self, skill, battle_state):
        """Find the best position to cast a direct skill (teleport, etc.)."""
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]

        # For direct skills, position for optimal targeting
        # Try positions that give good angles on enemy general
        best_pos = None
        best_score = 0

        for dx in [-4, -3, -2, 2, 3, 4]:
            for dy in [-4, -3, -2, 2, 3, 4]:
                x, y = enemy_general.x + dx, enemy_general.y + dy
                if self.bg.is_inside(x, y):
                    # Score based on distance and angle
                    distance_to_enemy = abs(x - enemy_general.x) + abs(y - enemy_general.y)
                    distance_from_us = abs(x - self.general.x) + abs(y - self.general.y)

                    # Prefer positions that are close to enemy but not too far from us
                    score = (15 - distance_to_enemy) + max(0, 8 - distance_from_us)

                    if score > best_score:
                        best_score = score
                        best_pos = (x, y)

        return best_pos, best_score

    def _get_guaranteed_action(self, battle_state):
        """Get a guaranteed action that the AI can always take, but with resource awareness."""
        # Priority 1: Resource-aware skill usage (only when strategically valuable)
        valuable_skill = self._find_valuable_skill(battle_state)
        if valuable_skill:
            return valuable_skill

        # Priority 2: Tactical commands (formation management)
        tactic_action = self._get_smart_tactical_action(battle_state)
        if tactic_action:
            return tactic_action

        # Priority 3: Strategic movement (only when beneficial)
        move_action = self._get_strategic_movement(battle_state)
        if move_action:
            return move_action

        # Priority 4: Basic movement as absolute last resort
        return self._emergency_action(battle_state)

    def _find_valuable_skill(self, battle_state):
        """Find a skill that's actually worth using based on current situation."""
        # Only use skills if they provide clear strategic value
        for i, skill in enumerate(self.general.skills):
            if not skill.is_ready() or not self._check_skill_cooldown(i):
                continue

            priority, should_use, reason = evaluators.evaluate_skill_priority_with_cooldowns(
                self.general, i, skill
            )

            # Only use skills that meet minimum strategic value
            if priority >= self.personality['min_skill_priority'] * 0.7: # Lower threshold but still meaningful
                target, score = self._get_skill_target(i, skill)
                if target and score > 0: # Must have a valid target with some effectiveness
                    action = f"skill{i} {target[0]} {target[1]}\n"
                    if not self._is_action_spam(action):
                        return action

        return None

    def _get_smart_tactical_action(self, battle_state):
        """Get a tactical command that's appropriate for the current situation."""
        # Choose tactics based on battle phase and needs, but be more selective
        phase = battle_state['phase']
        our_minions = battle_state['our_minions']
        enemy_minions = battle_state['enemy_minions']
        turn = battle_state['turn']
        num_tactics = len(self.general.tactics)

        # Only use tactics when they provide real strategic value
        if phase == "early_game" and turn < 30:
            # Early game: spread out for control, but only once
            if our_minions >= 3 and num_tactics > 3 and not any("tactic3" in action for action in self.last_actions[-10:]):
                action = "tactic3\n" # go_sides
                if not self._is_action_spam(action):
                    return action

        elif phase == "combat":
            # Combat: focus on enemy, but only when close and not recently used
            if battle_state['distance'] < 20 and num_tactics > 5 and not any("tactic5" in action for action in self.last_actions[-15:]):
                action = "tactic5\n" # attack_general
                if not self._is_action_spam(action):
                    return action

        elif phase == "positioning" and turn > 60:
            # Positioning: advance carefully, but not too frequently
            if battle_state['distance'] > 15 and num_tactics > 1 and not any("tactic1" in action for action in self.last_actions[-20:]):
                action = "tactic1\n" # forward
                if not self._is_action_spam(action):
                    return action

        # Don't use default tactics as fallback - let movement handle it
        return None

    def _get_strategic_movement(self, battle_state):
        """Get movement that's strategically beneficial."""
        # Use our smart advance position logic instead of the broken evaluators
        move_target = self._calculate_advance_position(battle_state)

        if move_target:
            distance = abs(move_target[0] - self.general.x) + abs(move_target[1] - self.general.y)
            action = f"flag {move_target[0]} {move_target[1]}\n"

            if distance >= 3 and not self._is_action_spam(action):
                return action

        # Try flanking as secondary option
        flank_target = self._calculate_flanking_position(battle_state)
        if flank_target:
            distance = abs(flank_target[0] - self.general.x) + abs(flank_target[1] - self.general.y)
            action = f"flag {flank_target[0]} {flank_target[1]}\n"

            if distance >= 2 and not self._is_action_spam(action):
                return action

        # Generate alternative positions that avoid repetition
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]
        alternatives = []

        # Try positions at different angles from enemy
        for dist in [8, 10, 12]:
            for angle in [30, 60, 120, 150, 210, 240, 300, 330]: # Avoid cardinal directions
                rad = angle * 3.14159 / 180
                dx = int(dist * (1 if angle <= 90 or angle >= 270 else -1))
                dy = int(dist * (1 if angle >= 0 and angle <= 180 else -1))

                alt_x = enemy_general.x + dx
                alt_y = enemy_general.y + dy

                # Ensure valid bounds
                alt_x = max(1, min(self.bg.width - 2, alt_x))
                alt_y = max(1, min(self.bg.height - 2, alt_y))

                distance = abs(alt_x - self.general.x) + abs(alt_y - self.general.y)
                if distance >= 4: # Require meaningful movement
                    alternatives.append((alt_x, alt_y))

        # Try alternatives that aren't spammy, prioritizing by distance from recent positions
        alternatives.sort(key=lambda pos: min(
            (abs(pos[0] - rx) + abs(pos[1] - ry) for rx, ry in self.last_flag_positions[-3:]),
            default=999
        ), reverse=True) # Sort by maximum distance from recent positions

        for alt_x, alt_y in alternatives[:8]: # Try top 8 alternatives
            action = f"flag {alt_x} {alt_y}\n"
            if not self._is_action_spam(action):
                return action

        return None

    def _emergency_action(self, battle_state):
        """Absolute last resort action - always returns something with randomization."""
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]

        # Generate multiple possible moves and pick one that's not spammy
        possible_moves = []

        # Basic directional moves
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in directions:
            target_x = self.general.x + dx
            target_y = self.general.y + dy

            # Ensure valid coordinates
            target_x = max(1, min(self.bg.width - 2, target_x))
            target_y = max(1, min(self.bg.height - 2, target_y))

            action = f"flag {target_x} {target_y}\n"
            if not self._is_action_spam(action):
                possible_moves.append((target_x, target_y))

        # If we have valid moves, pick one
        if possible_moves:
            # Prefer moves that get closer to enemy
            best_move = None
            best_distance = float('inf')

            for target_x, target_y in possible_moves:
                distance = abs(target_x - enemy_general.x) + abs(target_y - enemy_general.y)
                if distance < best_distance:
                    best_distance = distance
                    best_move = (target_x, target_y)

            if best_move:
                return f"flag {best_move[0]} {best_move[1]}\n"

        # If all else fails, pick any valid move (ignore spam)
        for dx, dy in directions:
            target_x = self.general.x + dx
            target_y = self.general.y + dy
            target_x = max(1, min(self.bg.width - 2, target_x))
            target_y = max(1, min(self.bg.height - 2, target_y))

            # Make sure it's actually a different position
            if target_x != self.general.x or target_y != self.general.y:
                return f"flag {target_x} {target_y}\n"

        # Absolute last resort - move right
        return f"flag {min(self.bg.width - 2, self.general.x + 1)} {self.general.y}\n"

    def _get_tactic_skill_synergy(self, skill_desc, battle_state):
        """
        Calculate synergy multiplier between current tactic and skill type.

        Returns a multiplier that boosts skills working well with current formation.
        """
        if self.current_tactic is None:
            return 1.0 # No tactic active, no synergy bonus

        # TACTIC ↔ SKILL SYNERGY MATRIX
        synergy_matrix = {
            0: { # stop tactic - stationary, ranged focus
                'damage': 1.0, 'explosion': 1.0, 'area': 1.0, 'burst': 1.0,
                'heal': 1.2, 'shield': 1.2, 'armor': 1.2, # Defensive while stationary
            },
            1: { # forward tactic - advancing toward enemy
                'damage': 1.3, 'explosion': 1.2, 'burst': 1.3, # Aggressive skills
                'teleport': 1.2, 'blink': 1.2, 'move': 1.2, # Movement synergy
            },
            2: { # backward tactic - retreating
                'heal': 1.4, 'shield': 1.4, 'armor': 1.4, # Defensive while retreating
                'teleport': 1.3, 'blink': 1.3, # Escape skills
            },
            3: { # go_sides tactic - spread formation
                'area': 1.5, 'explosion': 1.5, 'damage': 1.3, 'burst': 1.4, # AoE coverage
                'heal': 1.1, # Spread healing covers more units
            },
            4: { # go_center tactic - concentrated formation
                'damage': 1.4, 'burst': 1.4, 'explosion': 1.2, # Focused damage
                'heal': 1.3, 'shield': 1.3, # Concentrated support
            },
            5: { # attack_general tactic - direct assault
                'damage': 1.5, 'burst': 1.5, 'explosion': 1.4, # Direct damage
                'teleport': 1.2, 'blink': 1.2, # Close assault
            },
            6: { # defend_general tactic - protective formation
                'heal': 1.5, 'shield': 1.5, 'armor': 1.5, # Protection focus
                'damage': 1.2, 'burst': 1.2, # Counter-attack capability
            }
        }

        # Get synergy bonuses for current tactic
        tactic_synergies = synergy_matrix.get(self.current_tactic, {})

        # Check skill keywords for synergy
        for keyword, multiplier in tactic_synergies.items():
            if keyword in skill_desc:
                if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                    print(f"[AI] Tactic {self.current_tactic} ↔ {keyword} synergy: {multiplier}x")
                return multiplier

        return 1.0 # No synergy

    def _get_skill_target(self, skill_index, skill):
        """Get the best target for a specific skill."""
        skill_description = skill.description.lower()

        if any(keyword in skill_description for keyword in
               ["damage", "deals", "area", "explosion", "burst", "nova"]):
            target, score = evaluators.find_best_aoe_target(self.general, skill)
            return target, score

        elif any(keyword in skill_description for keyword in
                ["heal", "restore", "regenerate", "mend"]):
            target, score = evaluators.find_best_heal_target(self.general, skill)
            return target, score

        elif any(keyword in skill_description for keyword in
                ["teleport", "blink", "move", "dash", "rush"]):
            target = evaluators.find_strategic_move_target(self.general)
            if target:
                distance = abs(target[0] - self.general.x) + abs(target[1] - self.general.y)
                return target, distance

        # Default: self-targeting
        return (self.general.x, self.general.y), 0

    def _is_action_spam(self, action):
        """
        Check if an action would be considered spam.
        
        Args:
            action: The action to check
            
        Returns:
            bool: True if action would be spam
        """
        if not action:
            return True
        
        action_parts = action.strip().split()
        if len(action_parts) < 1:
            return True
        
        action_type = action_parts[0]
        
        # Check for excessive flag placement
        if action_type == "flag":
            if len(action_parts) >= 3:
                try:
                    x, y = int(action_parts[1]), int(action_parts[2])
                    # Check if we've placed a flag at this exact position recently
                    for pos_x, pos_y in self.last_flag_positions[-5:]: # Check last 5 positions
                        if x == pos_x and y == pos_y:
                            return True # Same position too recently

                    # Check if we've been too close to this position recently
                    for pos_x, pos_y in self.last_flag_positions[-8:]:
                        if abs(x - pos_x) <= 2 and abs(y - pos_y) <= 2:
                            return True # Too close to recent position

                    # Add current position to history
                    self.last_flag_positions.append((x, y))
                    if len(self.last_flag_positions) > 15:
                        self.last_flag_positions.pop(0)

                except (ValueError, IndexError):
                    pass

            # Check flag placement frequency - very restrictive
            flag_count = sum(1 for a in self.last_actions[-15:] if a.startswith("flag"))
            if flag_count >= 2: # Only allow 2 flag placements in last 15 turns
                return True
        
        # Check overall action frequency
        recent_actions = self.last_actions[-10:]
        action_frequency = recent_actions.count(action)
        
        if action_type == "flag" and action_frequency >= 6:
            return True
        elif action_type in ["skill"] and action_frequency >= 4:
            return True
        elif action_type in ["tactic"] and action_frequency >= 3:
            return True
        
        return False

    def _check_skill_cooldown(self, skill_index):
        """Check if enough turns have passed since last use of this skill."""
        current_turn = len(self.last_actions)
        last_use = self.last_skill_use.get(skill_index, -999)
        
        min_cooldown = self.personality['skill_cooldown_min']
        return (current_turn - last_use) >= min_cooldown

    def _mark_skill_used(self, skill_index):
        """Mark that a skill was just used."""
        self.last_skill_use[skill_index] = len(self.last_actions)

    def _record_action(self, action):
        """Record an action for spam tracking."""
        self.last_actions.append(action)

        # DEBUG: Check for consecutive flag spam and terminate game
        if action and action.startswith("flag"):
            try:
                action_parts = action.strip().split()
                if len(action_parts) >= 3:
                    current_x, current_y = int(action_parts[1]), int(action_parts[2])
                    current_pos = (current_x, current_y)

                    if self.last_flag_position == current_pos:
                        self.consecutive_same_flag_count += 1
                    if self.consecutive_same_flag_count >= 5:
                            # DEBUG: Show spam detection but don't terminate
                            print("\n" + "="*60)
                            print(f"AI SPAM DETECTED: {self.consecutive_same_flag_count} consecutive flags at {current_pos}")
                            print("="*60)
                            print(f"Turn: {len(self.last_actions)}, AI at ({self.general.x}, {self.general.y}), Enemy at ({self.bg.generals[(self.general.side + 1) % 2].x}, {self.bg.generals[(self.general.side + 1) % 2].y})")

                            # Show why this position keeps being chosen
                            battle_state = self._analyze_battlefield_state(len(self.last_actions))
                            strategy = self._determine_optimal_strategy(battle_state)
                            print(f"Strategy: {strategy}, Phase: {battle_state['phase']}")

                            # Force different position by clearing history
                            print("Clearing position history to force variety...")
                            self.last_flag_positions.clear()
                            self.consecutive_same_flag_count = 0
                            print("="*60)
                    else:
                        self.consecutive_same_flag_count = 1
                        self.last_flag_position = current_pos
            except (ValueError, IndexError, AttributeError):
                pass

        # Track tactic changes for persistence
        if action and action.startswith("tactic"):
            try:
                tactic_index = int(action.split()[0][6:]) # Extract tactic index from "tactic5"
                if tactic_index != self.current_tactic:
                    self.current_tactic = tactic_index
                    self.tactic_start_turn = len(self.last_actions)
                    if hasattr(self.bg, 'DEBUG') and self.bg.DEBUG:
                        print(f"[AI] New tactic {tactic_index} active (turn {self.tactic_start_turn})")
            except (ValueError, IndexError):
                pass

        # Clean up old actions
        if len(self.last_actions) > self.max_action_history:
            self.last_actions.pop(0)

        # Update action counts
        action_type = action.split()[0] if action else ""
        self.action_counts[action_type] = self.action_counts.get(action_type, 0) + 1

    def set_personality(self, personality_config):
        """Update the AI personality configuration."""
        self.personality.update(personality_config)

    def get_battlefield_summary(self):
        """Get a summary of the current battlefield state for debugging."""
        enemy_general = self.bg.generals[(self.general.side + 1) % 2]
        urgency = evaluators.evaluate_tactical_urgency(self.general)
        effectiveness = evaluators.get_combat_effectiveness_score(self.general)
        
        our_minions = sum(1 for m in self.bg.minions if m.is_ally(self.general) and m.alive)
        enemy_minions = sum(1 for m in self.bg.minions if not m.is_ally(self.general) and m.alive)
        
        return {
            'our_health': f"{self.general.hp}/{self.general.max_hp}",
            'enemy_health': f"{enemy_general.hp}/{enemy_general.max_hp}",
            'our_minions': our_minions,
            'enemy_minions': enemy_minions,
            'ready_skills': len([s for s in self.general.skills if s.is_ready()]),
            'distance_to_enemy': abs(enemy_general.x - self.general.x) + abs(enemy_general.y - self.general.y),
            'tactical_urgency': urgency,
            'combat_effectiveness': effectiveness,
            'recent_actions': len(self.last_actions),
            'flag_positions': len(self.last_flag_positions)
        }
