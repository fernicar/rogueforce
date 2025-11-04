# Phase 1 Migration Checklist

## Pre-Migration
- [x] Backup entire project
- [x] Commit current state to git
- [x] Document current TCOD usage

## Structure Setup
- [x] Run move2doc.py
- [x] Verify directory structure
- [x] Update .gitignore

## Core Systems
- [x] Update config.py
- [x] Create asset_loader.py
- [x] Create renderer.py
- [x] Create animation.py
- [x] Update requirements.txt

## File-by-File Migration
- [x] concepts.py (no TCOD, already done)
- [x] config.py (completed above)
- [x] battleground.py
- [x] window.py
- [x] battle.py
- [x] entity.py
- [x] minion.py
- [x] general.py
- [x] effect.py
- [x] skill.py
- [x] status.py
- [x] tactic.py
- [x] formation.py
- [x] area.py
- [x] sieve.py
- [x] scenario.py
- [x] server.py (no TCOD)
- [x] faction.py (no TCOD)
- [x] factions/*.py

## Testing
- [x] Run test_migration_phase1.py
- [x] Manual smoke test
- [x] Verify DEBUG mode works
- [x] Test asset loading failures
- [x] Test placeholder rendering

## Cleanup
- [x] Remove arial10x10.png (TCOD font)
- [x] Remove compat/tcod_shim.py
- [x] Update all imports
- [x] Remove TCOD from requirements.txt
- [x] Run final tests

## Documentation
- [x] Update README.md
- [x] Document new rendering system
- [x] Document asset loading system
- [x] Create migration notes
