# TODO LIST - Fix Sprite Loading Errors

## ✅ COMPLETED - All Sprite Issues Fixed!

### Problem Solved:
The game now runs successfully without sprite loading errors. The command `python battle.py 0` executes completely, showing:
- Game starts normally
- Turns are processed (Turn 10, 20, 30 completed)
- Game loop ends successfully

### Changes Made to Fix Sprite Case Sensitivity:
1. **Bloodrotter**: Set `character_name = "bloodrotter"`
2. **Ox**: Set `character_name = "ox"`
3. **Pock**: Set `character_name = "pock"`
4. **Rubock**: Set `character_name = "rubock"`
5. **Starcall**: Set `character_name = "starcall"`
6. **Ares**: Set `character_name = "ares"`
7. **Flappy**: Set `character_name = "flappy"`
8. **Gemekaa**: Set `character_name = "gemekaa"`

### Final Faction Structure:
- **Doto**: Bloodrotter, Ox, Pock, Rubock (4 characters)
- **Mechanics**: Flappy (1 character)
- **Oracles**: Gemekaa, Ox, Pock (3 characters)
- **Saviours**: Ares, Bloodrotter, Rubock (3 characters)
- **Wizerds**: Starcall (1 character)

### Root Cause:
Character classes were inheriting capitalized class names as their character_name, but sprite directories were lowercase (pock/, rubock/, bloodrotter/, ox/, etc.). This caused case sensitivity issues when the asset loader tried to load sprites.

### Solution:
Explicitly set character_name to lowercase versions in each character class constructor to match the actual sprite directory names.

### Verification:
✅ All characters now have lowercase character_name  
✅ Sprite directories exist for all character names  
✅ Game runs successfully without sprite errors  
✅ Python syntax validation passed
