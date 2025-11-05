# Implementation Progress

## Part 1: GUI Color Restoration and Standardization

### Step 1.1: Consolidate Color Definitions
- [x] Remove color definitions from `config.py`
- [x] Update `concepts.py` with correct background color

### Step 1.2: Update Files to Use `concepts.py` for Colors
- [x] Modify `battleground.py` to use centralized color constants
- [x] Modify `status.py` to fix imports and handle Pygame color interpolation
- [x] Modify `minion.py` to handle dynamic health-based coloring

## Part 2: Random General Selection and Sprite Integration

### Step 2.1: Create a Central Faction and General Registry
- [x] Create `faction_data.py` to define all available factions and generals

### Step 2.2: Update General Classes for Sprite Loading
- [x] Modify `factions/doto.py` to add character_name attributes
- [x] Modify `factions/wizerds.py` to add character_name attributes
- [x] Modify `factions/oracles.py` to add character_name attributes
- [x] Modify `factions/saviours.py` to add character_name attributes
- [x] Modify `factions/mechanics.py` to add character_name attributes

### Step 2.3: Implement Random Selection in `battle.py`
- [ ] Replace hardcoded setup in `battle.py` with dynamic, random selection logic

## Verification
- [ ] Test the implementation by running `python battle.py`
- [ ] Verify random general selection works
- [ ] Check color consistency throughout the application
