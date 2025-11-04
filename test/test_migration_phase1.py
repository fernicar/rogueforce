"""
Tests for Phase 1 migration
"""
import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import DEBUG
from rendering.renderer import Renderer
from assets.asset_loader import asset_loader

class TestPhase1Setup(unittest.TestCase):
    """Test Phase 1 setup and structure"""

    def test_directory_structure(self):
        """Verify all required directories exist"""
        required_dirs = [
            'doc',
            'test',
            'assets/sound',
            'assets/music',
            'assets/sprite/game'
        ]

        for dir_path in required_dirs:
            self.assertTrue(
                os.path.exists(dir_path),
                f"Required directory missing: {dir_path}"
            )

    def test_config_module(self):
        """Verify config module has required settings"""
        from config import (
            DEBUG, WINDOW_WIDTH, WINDOW_HEIGHT,
            GRID_WIDTH, GRID_HEIGHT, TILE_SIZE
        )

        self.assertIsInstance(DEBUG, bool)
        self.assertGreater(WINDOW_WIDTH, 0)
        self.assertGreater(WINDOW_HEIGHT, 0)

    def test_asset_loader_debug_mode(self):
        """Test asset loader handles missing files in DEBUG mode"""
        # Try to load non-existent sprite
        sprite = asset_loader.load_sprite('nonexistent/test.png')

        # Should return placeholder in DEBUG mode, not crash
        self.assertIsNotNone(sprite)

    def test_no_tcod_imports(self):
        """Verify no direct tcod imports in main modules"""
        import re

        files_to_check = [
            'config.py',
            'rendering/renderer.py',
            'assets/asset_loader.py'
        ]

        for filepath in files_to_check:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    self.assertNotIn('import libtcod', content,
                                   f"{filepath} should not import libtcod")
                    self.assertNotIn('from libtcod', content,
                                   f"{filepath} should not import libtcod")

if __name__ == '__main__':
    unittest.main()
