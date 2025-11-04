# Rendering System

The rendering system in Rogue Force is built on top of Pygame. It's designed to be simple and flexible, allowing for easy drawing of sprites, text, and other graphical elements.

## `rendering/renderer.py`

The `Renderer` class in `renderer.py` is the core of the rendering system. It's responsible for:

*   Initializing Pygame and creating the main display window.
*   Clearing the screen at the start of each frame.
*   Drawing sprites, text, and primitive shapes (rectangles, lines) to the screen.
*   Managing the game's frame rate.
*   Handling the camera position for scrolling.

## `rendering/animation.py`

The `Animation` class in `animation.py` handles sprite animations. It's designed to work with a specific set of sprite names (e.g., `base_idle`, `walk_1`, `walk_2`) to create looping "ping-pong" animations for different character states (idle, walk, attack, flinch).
