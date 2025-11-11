"""
AI package for Rogue Force computer-controlled opponents.

This package contains the AI logic for making tactical decisions
in the battlefield, including skill evaluation and strategic movement.
"""

from .ai_controller_optimized import AIController
from .evaluators_optimized import (
    find_best_aoe_target,
    find_best_heal_target,
    find_strategic_move_target,
    evaluate_tactical_urgency,
    should_use_tactical_command,
    evaluate_skill_priority_with_cooldowns,
    get_combat_effectiveness_score,
    validate_skill_effectiveness
)

__all__ = [
    "AIController",
    "find_best_aoe_target",
    "find_best_heal_target",
    "find_strategic_move_target",
    "evaluate_tactical_urgency",
    "should_use_tactical_command",
    "evaluate_skill_priority_with_cooldowns",
    "get_combat_effectiveness_score",
    "validate_skill_effectiveness"
]
