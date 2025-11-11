"""
Optimized battlefield evaluators for AI decision-making.

This module contains efficient functions that analyze the battlefield state and return
strategic information to help the AI make tactical decisions without performance degradation.
"""

from __future__ import annotations
from typing import Optional, Tuple, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from general import General


def find_best_aoe_target(general: 'General', skill, bonus_general_hit: float = 2.0) -> Tuple[Optional[Tuple[int, int]], float]:
    """
    Optimized AoE target finding with reduced sampling.
    
    Args:
        general: The AI general using the skill
        skill: The AoE skill to evaluate
        bonus_general_hit: Extra score for hitting enemy general

    Returns:
        tuple: (best_target_position, best_score) or (None, 0) if no good target found
    """
    best_target = None
    best_score = 0
    bg = general.bg
    enemy_side = (general.side + 1) % 2
    enemy_general = bg.generals[enemy_side]

    # Optimize: Focus sampling around enemy positions and minion clusters
    potential_positions = []
    
    # Add enemy general position
    potential_positions.append((enemy_general.x, enemy_general.y))
    
    # Add positions around enemy general (2x2 grid)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            x, y = enemy_general.x + dx, enemy_general.y + dy
            if bg.is_inside(x, y):
                potential_positions.append((x, y))
    
    # Add random sampling but much fewer iterations
    for _ in range(25): # Reduced from 100 to 25
        if enemy_side == 1:
            x = random.randint(bg.width // 2, bg.width - 1)
        else:
            x = random.randint(0, bg.width // 2 - 1)
        y = random.randint(1, bg.height - 2)
        potential_positions.append((x, y))
    
    # Evaluate potential positions
    for x, y in potential_positions:
        if not bg.is_inside(x, y):
            continue
            
        tiles_in_aoe = skill.get_area_tiles(x, y)
        if not tiles_in_aoe:
            continue
            
        score = 0
        for tile in tiles_in_aoe:
            if tile.entity:
                if not tile.entity.is_ally(general):
                    score += 1
                    # Prioritize hitting the enemy general
                    if tile.entity == enemy_general:
                        score += bonus_general_hit
                else:
                    # Avoid hitting allies
                    score -= 1.5
        
        if score > best_score:
            best_score = score
            best_target = (x, y)
            
    return best_target, best_score


def find_best_heal_target(general: 'General', skill) -> Tuple[Optional[Tuple[int, int]], int]:
    """
    Optimized healing target finding.
    
    Args:
        general: The AI general using the skill
        skill: The healing skill to evaluate

    Returns:
        tuple: (best_target_position, damage_to_heal) or (None, 0) if no healing needed
    """
    best_target = None
    most_damage_taken = 0
    
    # Check general first - always prioritize general healing
    if general.hp is not None and general.max_hp is not None and general.hp < general.max_hp:
        damage_taken = general.max_hp - general.hp
        most_damage_taken = damage_taken
        best_target = (general.x, general.y)

    # Check allied minions - limit to most damaged ones for performance
    damaged_minions = [(m, m.max_hp - m.hp) for m in general.bg.minions
        if m.is_ally(general) and m.hp is not None and m.max_hp is not None and m.hp < m.max_hp]
    
    # Sort by damage taken and take top 5 for performance
    damaged_minions.sort(key=lambda x: x[1], reverse=True)
    for minion, damage_taken in damaged_minions[:5]:
        if damage_taken > most_damage_taken:
            most_damage_taken = damage_taken
            best_target = (minion.x, minion.y)

    return best_target, most_damage_taken


def find_strategic_move_target(general: 'General') -> Tuple[int, int]:
    """
    Enhanced strategic movement with maximum diversity to prevent repetition.

    Args:
        general: The AI general that needs to move

    Returns:
        tuple: (target_x, target_y) for strategic movement
    """
    bg = general.bg
    enemy_general = bg.generals[(general.side + 1) % 2]

    # Generate multiple strategic options and pick the best available one
    candidate_positions = []

    # Always include some randomization to prevent getting stuck
    base_variations = [
        (enemy_general.x + random.randint(-3, 3), enemy_general.y + random.randint(-2, 2)),
        (enemy_general.x + random.randint(-4, 4), enemy_general.y + random.randint(-3, 3)),
        (enemy_general.x + random.randint(-2, 2), enemy_general.y + random.randint(-4, 4)),
    ]

    # Add flanking positions
    flank_positions = [
        (enemy_general.x - 6, enemy_general.y),
        (enemy_general.x + 6, enemy_general.y),
        (enemy_general.x, enemy_general.y - 4),
        (enemy_general.x - 4, enemy_general.y - 3),
        (enemy_general.x + 4, enemy_general.y - 3),
    ]

    candidate_positions.extend(base_variations)
    candidate_positions.extend(flank_positions)

    # Filter valid, unoccupied positions
    valid_positions = []
    for x, y in candidate_positions:
        # Ensure bounds
        x = max(1, min(bg.width - 2, x))
        y = max(1, min(bg.height - 2, y))

        # Check if position is free
        if bg.is_inside(x, y):
            tile = bg.tiles[(x, y)]
            if not tile.entity or tile.entity == general:
                distance = abs(x - general.x) + abs(y - general.y)
                if distance >= 2: # Ensure meaningful movement
                    valid_positions.append((x, y, distance))

    if valid_positions:
        # Sort by distance (prefer closer positions) and pick randomly from top 3
        valid_positions.sort(key=lambda pos: pos[2]) # Sort by distance
        top_candidates = valid_positions[:3] # Take closest 3
        chosen = random.choice(top_candidates)
        return (chosen[0], chosen[1])

    # Emergency fallback: any valid unoccupied position
    for attempt in range(50): # Try up to 50 times
        x = random.randint(1, bg.width - 2)
        y = random.randint(1, bg.height - 2)

        if bg.is_inside(x, y):
            tile = bg.tiles[(x, y)]
            if not tile.entity or tile.entity == general:
                distance = abs(x - general.x) + abs(y - general.y)
                if distance >= 1: # Any movement at all
                    return (x, y)

    # Absolute last resort
    return (general.x + 1, general.y)


def evaluate_tactical_urgency(general: 'General') -> int:
    """
    Lightweight tactical urgency evaluation.
    
    Args:
        general: The AI general
        
    Returns:
        int: Urgency score (0-100, higher = more urgent)
    """
    urgency = 0
    
    # Health-based urgency (simplified)
    if general.hp is not None and general.max_hp is not None and general.max_hp > 0:
        health_ratio = general.hp / general.max_hp
        if health_ratio < 0.3:
            urgency += 40
        elif health_ratio < 0.6:
            urgency += 20
    
    # Simple minion count check (performance optimized)
    our_minions = sum(1 for m in general.bg.minions if m.is_ally(general) and m.alive)
    enemy_minions = sum(1 for m in general.bg.minions if not m.is_ally(general) and m.alive)
    
    if enemy_minions > our_minions * 1.5:
        urgency += 30
    elif enemy_minions > our_minions:
        urgency += 15
    
    # Distance to enemy general (simplified calculation)
    enemy_general = general.bg.generals[(general.side + 1) % 2]
    distance_to_enemy = abs(enemy_general.x - general.x) + abs(enemy_general.y - general.y)
    
    if distance_to_enemy < 8:
        urgency += 25
    
    # Enemy general health
    if enemy_general.hp is not None and enemy_general.max_hp is not None and enemy_general.max_hp > 0:
        enemy_health_ratio = enemy_general.hp / enemy_general.max_hp
        if enemy_health_ratio < 0.5:
            urgency += 15
    
    return min(urgency, 100)


def should_use_tactical_command(general: 'General') -> Tuple[bool, int, str]:
    """
    Optimized tactical command decision-making.
    
    Args:
        general: The AI general
        
    Returns:
        tuple: (should_command, tactic_index, reason)
    """
    # Lightweight minion count
    our_minions = sum(1 for m in general.bg.minions if m.is_ally(general) and m.alive)
    enemy_minions = sum(1 for m in general.bg.minions if not m.is_ally(general) and m.alive)
    
    if our_minions < 3: # Too few minions to command effectively
        return False, -1, "Insufficient minions"
    
    urgency = evaluate_tactical_urgency(general)
    enemy_general = general.bg.generals[(general.side + 1) % 2]
    distance_to_enemy = abs(enemy_general.x - general.x) + abs(enemy_general.y - general.y)
    
    # Simplified tactical decisions
    if urgency > 50:
        return True, 5, f"High urgency ({urgency}) - attack mode"
    elif our_minions > enemy_minions * 1.2 and distance_to_enemy < 15:
        return True, 1, "Advantageous position - advance"
    elif general.hp is not None and general.max_hp is not None and general.hp < general.max_hp * 0.6:
        return True, 6, "General needs protection - defend mode"
    
    return False, -1, "Current tactics appropriate"


def evaluate_skill_priority_with_cooldowns(general: 'General', skill_index: int, skill) -> Tuple[float, bool, str]:
    """
    Balanced skill priority evaluation with lower thresholds.
    
    Args:
        general: The AI general
        skill_index: Index of the skill
        skill: The skill to evaluate
        
    Returns:
        tuple: (priority_score, should_use, reason)
    """
    if not skill.is_ready():
        return 0, False, "Skill on cooldown"
    
    urgency = evaluate_tactical_urgency(general)
    skill_desc = skill.description.lower()
    
    # Lower base priority to allow more skill usage
    base_priority = 40
    
    # Damage skills - moderate priority
    if any(keyword in skill_desc for keyword in ["damage", "deals", "area", "explosion", "burst", "nova"]):
        priority = base_priority + (urgency * 0.2)
        
        # Quick target check without expensive validation
        target, score = find_best_aoe_target(general, skill)
        if target and score > 1.0: # Lowered threshold
            return priority + score, True, f"Effective AoE (score: {score})"
        else:
            return 0, False, "No good AoE targets"
    
    # Healing skills - higher priority when needed
    elif any(keyword in skill_desc for keyword in ["heal", "restore", "regenerate", "mend"]):
        if general.hp is not None and general.max_hp is not None and general.max_hp > 0:
            health_ratio = general.hp / general.max_hp
            if health_ratio < 0.8: # More liberal healing threshold
                priority = base_priority + ((1 - health_ratio) * 30)
                return priority, True, f"Healing needed ({int(health_ratio * 100)}% health)"
            else:
                return 0, False, "At good health"
        else:
            return 0, False, "Health data unavailable"
    
    # Buff/debuff skills - moderate priority
    elif any(keyword in skill_desc for keyword in ["grants", "shield", "buff", "enhance", "armor", "resist"]):
        priority = base_priority + (urgency * 0.15)
        if urgency > 20: # Lowered threshold
            return priority, True, f"Buff for situation (urgency: {urgency})"
        else:
            return priority * 0.7, False, "Low urgency"
    
    # Movement skills - tactical use only
    elif any(keyword in skill_desc for keyword in ["teleport", "blink", "move", "dash", "rush"]):
        target = find_strategic_move_target(general)
        if target:
            distance = abs(target[0] - general.x) + abs(target[1] - general.y)
            if distance > 5: # Only for significant movement
                priority = base_priority + (distance * 3)
                return priority, True, f"Strategic reposition ({distance} tiles)"
            else:
                return 0, False, "Movement too short"
    
    # Default: allow unknown skills to be used occasionally
    return base_priority * 0.4, True, "Experimental skill use"


def get_combat_effectiveness_score(general: 'General') -> float:
    """
    Lightweight combat effectiveness calculation.
    
    Args:
        general: The AI general
        
    Returns:
        float: Effectiveness score (0.0 to 1.0)
    """
    # Simple calculations for performance
    general_health_ratio = 1.0
    if general.hp is not None and general.max_hp is not None and general.max_hp > 0:
        general_health_ratio = general.hp / general.max_hp
    
    our_minions = sum(1 for m in general.bg.minions if m.is_ally(general) and m.alive)
    enemy_minions = sum(1 for m in general.bg.minions if not m.is_ally(general) and m.alive)
    
    minion_effectiveness = min(1.0, our_minions / max(enemy_minions, 1))
    
    enemy_general = general.bg.generals[(general.side + 1) % 2]
    distance_to_enemy = abs(enemy_general.x - general.x) + abs(enemy_general.y - general.y)
    position_effectiveness = max(0.3, 1.0 - (distance_to_enemy / 40))
    
    # Simplified weighted average
    return (general_health_ratio * 0.5 + minion_effectiveness * 0.3 + position_effectiveness * 0.2)


def validate_skill_effectiveness(general: 'General', skill, target_x: int, target_y: int) -> Tuple[bool, int, str]:
    """
    Lightweight skill validation with liberal acceptance.
    
    Args:
        general: The AI general using the skill
        skill: The skill to validate
        target_x: Target X coordinate
        target_y: Target Y coordinate
        
    Returns:
        tuple: (is_effective, effectiveness_score, reason)
    """
    if not skill.is_ready():
        return False, 0, "Skill not ready"
    
    if not general.bg.is_inside(target_x, target_y):
        return False, 0, "Target out of bounds"
    
    area_tiles = skill.get_area_tiles(target_x, target_y)
    if not area_tiles:
        return False, 0, "Invalid skill area"
    
    skill_desc = skill.description.lower()
    
    # Liberal validation for most skill types
    if any(keyword in skill_desc for keyword in ["damage", "deals", "area", "explosion", "burst", "nova"]):
        enemy_count = sum(1 for tile in area_tiles if tile.entity and not tile.entity.is_ally(general))
        if enemy_count > 0:
            return True, enemy_count, f"Hits {enemy_count} enemies"
        else:
            return False, 0, "No enemies hit"
    
    elif any(keyword in skill_desc for keyword in ["heal", "restore", "regenerate", "mend"]):
        return True, 30, "Healing skill"
    
    else:
        # Default: accept unknown skills
        return True, 20, "Skill accepted"
