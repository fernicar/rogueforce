# Asset Loading System

The asset loading system is responsible for loading all game assets, including sprites and sounds. It's designed to be robust, with a fallback system for missing assets when running in `DEBUG` mode.

## `assets/asset_loader.py`

The `AssetLoader` class in `asset_loader.py` is the central point for loading all game assets. It provides the following features:

*   **Sprite Loading:** The `load_sprite` method can load a sprite from a given path, apply scaling, and perform a hue shift.
*   **Sound and Music Loading:** The `load_sound` and `load_music` methods load audio files.
*   **Character Sprite Loading:** The `get_character_sprites` method loads a full set of sprites for a character, based on a naming convention (e.g., `character_name/base_idle.png`).
*   **DEBUG Mode:** When `DEBUG` is `True` in `config.py`, the asset loader will not crash if an asset is missing. Instead, it will print a warning to the console and return a placeholder (a magenta square for sprites, `None` for sounds). This allows for rapid development without needing all assets in place.
