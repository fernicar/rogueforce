import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from asset_manager import asset_manager
from config import DEBUG

def test_sprite_loading():
    """Test sprite loading for all characters"""
    characters = ['pock', 'rubock', 'bloodrotter', 'ox', 
                  'starcall', 'gemekaa', 'ares', 'flappy']
    
    for char in characters:
        print(f"\nTesting {char}:")
        sprites = asset_manager.load_character_sprites(char)
        if sprites:
            print(f"  ✓ Loaded successfully")
        else:
            print(f"  ✗ Failed (using ASCII fallback)")

if __name__ == "__main__":
    test_sprite_loading()