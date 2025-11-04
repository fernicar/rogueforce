# Phase 1 Migration Checklist

## Pre-Migration
- [x] Backup entire project
- [x] Commit current state to git
- [x] Document current TCOD usage

## Structure Setup
- [x] Run move2doc.py
- [x] Verify directory structure
- [ ] Update .gitignore

## Core Systems
- [x] Update config.py
- [x] Create asset_loader.py
- [x] Create renderer.py
- [x] Create animation.py
- [x] Update requirements.txt

## File-by-File Migration
- [x] concepts.py (no TCOD, already done)
- [x] config.py (completed above)
- [ ] battleground.py
- [ ] window.py
- [ ] battle.py
- [ ] entity.py
- [ ] minion.py
- [ ] general.py
- [ ] effect.py
- [ ] skill.py
- [ ] status.py
- [ ] tactic.py
- [ ] formation.py
- [ ] area.py
- [ ] sieve.py
- [ ] scenario.py
- [ ] server.py (no TCOD)
- [ ] faction.py (no TCOD)
- [ ] factions/*.py

## Testing
- [x] Run test_migration_phase1.py
- [ ] Manual smoke test
- [ ] Verify DEBUG mode works
- [ ] Test asset loading failures
- [ ] Test placeholder rendering

## Cleanup
- [x] Remove arial10x10.png (TCOD font)
- [ ] Remove compat/tcod_shim.py
- [ ] Update all imports
- [x] Remove TCOD from requirements.txt
- [ ] Run final tests

## Documentation
- [ ] Update README.md
- [ ] Document new rendering system
- [ ] Document asset loading system
- [ ] Create migration notes
