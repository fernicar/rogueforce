import sys
import os
import unittest
from PIL import Image

# Add the project root to the Python path
sys.path.insert(0, os.getcwd())

from asset_manager import asset_manager
from config import DEBUG

class TestSpriteLoading(unittest.TestCase):
    def test_sprite_loading(self):
        """Test sprite loading for all characters"""
        characters = ['pock', 'rubock', 'bloodrotter', 'ox',
                      'starcall', 'gemekaa', 'ares', 'flappy']

        for char in characters:
            with self.subTest(char=char):
                sprites = asset_manager.load_character_sprites(char)
                self.assertIsNotNone(sprites, f"Failed to load sprites for {char}")
                self.assertIn('base', sprites)
                self.assertIsNotNone(sprites['base'], f"Missing base sprite for {char}")

    def test_hue_shift(self):
        """Test the hue shift function"""
        # Create a dummy red image
        red_img = Image.new('RGBA', (1, 1), (255, 0, 0, 255))

        # Apply a 120-degree hue shift (red to green)
        green_img = asset_manager._apply_hue_shift(red_img, 120)

        # Check that the new color is green
        self.assertEqual(green_img.getpixel((0, 0)), (0, 255, 0, 255))

if __name__ == "__main__":
    unittest.main()
