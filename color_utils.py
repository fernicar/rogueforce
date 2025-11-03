"""
Color utilities for pygame-based rendering system
Replaces libtcod color functionality with pygame equivalents
"""

import pygame

class Color:
    """Pygame-based color class compatible with libtcod.Color interface"""
    
    def __init__(self, r, g, b, a=255):
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))
        self.a = max(0, min(255, a))
    
    def __iter__(self):
        """Allow unpacking as tuple"""
        return iter((self.r, self.g, self.b))
    
    def __getitem__(self, index):
        """Allow indexing like tuple"""
        if index == 0:
            return self.r
        elif index == 1:
            return self.g
        elif index == 2:
            return self.b
        elif index == 3:
            return self.a
        else:
            raise IndexError("Color index out of range")
    
    def __str__(self):
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"
    
    def __repr__(self):
        return self.__str__()
    
    def as_tuple(self):
        """Return as (r, g, b) tuple for pygame"""
        return (self.r, self.g, self.b)
    
    def as_tuple_rgba(self):
        """Return as (r, g, b, a) tuple for pygame"""
        return (self.r, self.g, self.b, self.a)

def color_lerp(color1, color2, factor):
    """
    Linear interpolation between two colors
    Replaces libtcod.color_lerp
    """
    factor = max(0.0, min(1.0, factor))
    
    r = int(color1.r + (color2.r - color1.r) * factor)
    g = int(color1.g + (color2.g - color1.g) * factor)
    b = int(color1.b + (color2.b - color1.b) * factor)
    
    return Color(r, g, b)

# Create compatibility aliases
Color = Color  # For direct replacement