"""
Entity Concepts - Replaces color with meaningful entity-related concepts
This module provides semantic concepts instead of raw colors, allowing for
more maintainable and intuitive code.
"""

# UI Concept Definitions
class UIConcepts:
    """UI-related visual concepts"""
    TEXT_DEFAULT = (255, 255, 255)        # White for default text
    BACKGROUND_BASE = (20, 20, 40)        # Dark blue, as per new config
    HOVER_VALID = (0, 255, 0)             # Green for valid hover states
    HOVER_INVALID = (255, 0, 0)           # Red for invalid hover states
    HOVER_DEFAULT = (0, 0, 255)           # Blue for default hover states
    TILE_NEUTRAL = (50, 50, 150)          # Blue-grey for neutral tiles

# Faction Identity Concepts  
class FactionConcepts:
    """Faction and unit identity concepts"""
    LEADER_DEFAULT = (255, 127, 0)        # Orange for generic leaders
    CONWAY_LEADER = (0, 255, 0)           # Green for Conway
    EMPEROR_LEADER = (127, 101, 63)       # Sepia for Emperor
    WIZERDS_LEADER = (0, 255, 255)        # Cyan for Wizerds faction
    SAVIOURS_LEADER = (255, 0, 0)         # Red for Saviours faction
    MECHANICS_LEADER = (0, 128, 0)        # Dark Green for Mechanics faction
    DOTO_LEADER_DARK = (127, 0, 0)        # Darker Red for Doto faction (Bloodrotter)
    DOTO_LEADER_MEDIUM = (128, 0, 0)      # Dark Red for Doto faction (Ox)  
    DOTO_LEADER_LIGHT = (135, 206, 235)   # Sky Blue for Doto faction (Pock)
    DOTO_LEADER_PURE = (0, 255, 0)        # Green for Doto faction (Rubock)
    ENTITY_BASE = (255, 255, 255)         # White for base entity default
    ORACLE_LEADER = (220, 20, 60)         # Light Crimson for Oracle faction (Gemekaa)
    TRANSFORMATION_DARK = (192, 192, 192) # Light Grey for transformations (Nightspirit)

# Status and Progress Concepts
class StatusConcepts:
    """Status indicators and progress bar concepts"""
    HEALTH_CRITICAL = (255, 0, 0)         # Red for low health
    HEALTH_WARNING = (255, 255, 0)        # Yellow for medium health
    HEALTH_BACKGROUND = (0, 0, 0)         # Black for health bar background
    PROGRESS_DARK = (0, 0, 128)           # Dark Blue for progress bars
    PROGRESS_LIGHT = (135, 206, 235)      # Sky Blue for progress bars
    SELECTION_HIGHLIGHT = (255, 255, 255) # White for selected/highlighted items

# Effect and Animation Concepts  
class EffectConcepts:
    """Visual effects and animation concepts"""
    ATTACK_LIGHT = (255, 64, 64)          # Lighter Red for light attack effects
    ATTACK_MEDIUM = (255, 128, 128)       # Light Red for medium attack effects  
    DAMAGE_IMPACT = (255, 0, 0)           # Red for damage indicators
    WAVE_MOVEMENT = (128, 128, 255)       # Light Blue for wave effects
    HIGHLIGHT = (255, 255, 255)           # White for highlighted effects

# Convenience mappings for backward compatibility during migration
CONCEPT_MAPPINGS = {
    # UI Concepts
    'UI_TEXT': UIConcepts.TEXT_DEFAULT,
    'UI_BACKGROUND': UIConcepts.BACKGROUND_BASE,
    'UI_HOVER_VALID': UIConcepts.HOVER_VALID,
    'UI_HOVER_INVALID': UIConcepts.HOVER_INVALID,
    'UI_HOVER_DEFAULT': UIConcepts.HOVER_DEFAULT,
    'UI_TILE_NEUTRAL': UIConcepts.TILE_NEUTRAL,
    
    # Faction Concepts
    'FACTION_LEADER': FactionConcepts.LEADER_DEFAULT,
    'FACTION_CONWAY': FactionConcepts.CONWAY_LEADER,
    'FACTION_EMPEROR': FactionConcepts.EMPEROR_LEADER,
    'FACTION_WIZERDS': FactionConcepts.WIZERDS_LEADER,
    'FACTION_SAVIOURS': FactionConcepts.SAVIOURS_LEADER,
    'FACTION_MECHANICS': FactionConcepts.MECHANICS_LEADER,
    'FACTION_DOTO_DARK': FactionConcepts.DOTO_LEADER_DARK,
    'FACTION_DOTO_MEDIUM': FactionConcepts.DOTO_LEADER_MEDIUM,
    'FACTION_DOTO_LIGHT': FactionConcepts.DOTO_LEADER_LIGHT,
    'FACTION_DOTO_PURE': FactionConcepts.DOTO_LEADER_PURE,
    'FACTION_ORACLE': FactionConcepts.ORACLE_LEADER,
    'FACTION_TRANSFORMATION': FactionConcepts.TRANSFORMATION_DARK,
    'ENTITY_DEFAULT': FactionConcepts.ENTITY_BASE,
    
    # Status Concepts
    'STATUS_HEALTH_LOW': StatusConcepts.HEALTH_CRITICAL,
    'STATUS_HEALTH_MEDIUM': StatusConcepts.HEALTH_WARNING,
    'STATUS_HEALTH_HIGH': StatusConcepts.HEALTH_BACKGROUND,
    'STATUS_PROGRESS_DARK': StatusConcepts.PROGRESS_DARK,
    'STATUS_PROGRESS_LIGHT': StatusConcepts.PROGRESS_LIGHT,
    'STATUS_SELECTED': StatusConcepts.SELECTION_HIGHLIGHT,
    
    # Effect Concepts
    'EFFECT_HIGHLIGHT': EffectConcepts.HIGHLIGHT,
    'EFFECT_ATTACK_LIGHT': EffectConcepts.ATTACK_LIGHT,
    'EFFECT_ATTACK_MEDIUM': EffectConcepts.ATTACK_MEDIUM,
    'EFFECT_DAMAGE': EffectConcepts.DAMAGE_IMPACT,
    'EFFECT_WAVE': EffectConcepts.WAVE_MOVEMENT,
}

# Individual concept constants for direct import
UI_TEXT = UIConcepts.TEXT_DEFAULT
UI_BACKGROUND = UIConcepts.BACKGROUND_BASE
UI_HOVER_VALID = UIConcepts.HOVER_VALID
UI_HOVER_INVALID = UIConcepts.HOVER_INVALID
UI_HOVER_DEFAULT = UIConcepts.HOVER_DEFAULT
UI_TILE_NEUTRAL = UIConcepts.TILE_NEUTRAL

FACTION_LEADER = FactionConcepts.LEADER_DEFAULT
FACTION_CONWAY = FactionConcepts.CONWAY_LEADER
FACTION_EMPEROR = FactionConcepts.EMPEROR_LEADER
FACTION_WIZERDS = FactionConcepts.WIZERDS_LEADER
FACTION_SAVIOURS = FactionConcepts.SAVIOURS_LEADER
FACTION_MECHANICS = FactionConcepts.MECHANICS_LEADER
FACTION_DOTO_DARK = FactionConcepts.DOTO_LEADER_DARK
FACTION_DOTO_MEDIUM = FactionConcepts.DOTO_LEADER_MEDIUM
FACTION_DOTO_LIGHT = FactionConcepts.DOTO_LEADER_LIGHT
FACTION_DOTO_PURE = FactionConcepts.DOTO_LEADER_PURE
FACTION_ORACLE = FactionConcepts.ORACLE_LEADER
FACTION_TRANSFORMATION = FactionConcepts.TRANSFORMATION_DARK
ENTITY_DEFAULT = FactionConcepts.ENTITY_BASE

STATUS_HEALTH_LOW = StatusConcepts.HEALTH_CRITICAL
STATUS_HEALTH_MEDIUM = StatusConcepts.HEALTH_WARNING
STATUS_HEALTH_HIGH = StatusConcepts.HEALTH_BACKGROUND
STATUS_PROGRESS_DARK = StatusConcepts.PROGRESS_DARK
STATUS_PROGRESS_LIGHT = StatusConcepts.PROGRESS_LIGHT
STATUS_SELECTED = StatusConcepts.SELECTION_HIGHLIGHT

EFFECT_HIGHLIGHT = EffectConcepts.HIGHLIGHT
EFFECT_ATTACK_LIGHT = EffectConcepts.ATTACK_LIGHT
EFFECT_ATTACK_MEDIUM = EffectConcepts.ATTACK_MEDIUM
EFFECT_DAMAGE = EffectConcepts.DAMAGE_IMPACT
EFFECT_WAVE = EffectConcepts.WAVE_MOVEMENT
