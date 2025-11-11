from __future__ import annotations
from math import copysign
from typing import TYPE_CHECKING

if TYPE_CHECKING:
        from minion import Minion

def attack_general(minion: 'Minion') -> None:
    minion.move(int(copysign(1, minion.bg.generals[(minion.side+1)%2].x - minion.x)),
            int(copysign(1, minion.bg.generals[(minion.side+1)%2].y - minion.y)))

def backward(minion: 'Minion') -> None:
    minion.move(-1 if minion.side == 0 else 1, 0)

def defend_general(minion: 'Minion') -> None:
    minion.move(int(copysign(1, minion.bg.generals[minion.side].x - minion.x)),
            int(copysign(1, minion.bg.generals[minion.side].y - minion.y)))

def disperse(minion: 'Minion') -> None:
    r = 5
    d = {(1,1):0, (-1,1):0, (-1,-1):0, (1,-1):0}
    for i in range(-r, r+1):
        for j in range(-r, r+1):
            (x, y) = (minion.x+i, minion.y+j)
            if not minion.bg.is_inside(x, y): continue
            entity = minion.bg.tiles[(x, y)].entity
            if entity is not None and entity != minion:
                d[(int(copysign(1, i)), int(copysign(1, j)))] += 1
    minion.move(*min(d, key=lambda k: d[k]))

def forward(minion: 'Minion') -> None:
    minion.move(1 if minion.side == 0 else -1, 0)

def go_bottom(minion: 'Minion') -> None:
    minion.move(0, 1)

def go_center(minion: 'Minion') -> None:
    minion.move(0, -1 if minion.y >= minion.bg.height/2 else 1)

def go_sides(minion: 'Minion') -> None:
    minion.move(0, 1 if minion.y >= minion.bg.height/2 else -1)

def go_top(minion: 'Minion') -> None:
    minion.move(0, -1)

def null(minion: 'Minion') -> None:
    pass

def stop(minion: 'Minion') -> None:
    minion.next_action = 1
