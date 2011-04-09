from pygame.locals import *

KEYBINDINGS = {
    'alt': {
        'up': K_w,
        'down': K_s,
        'left': K_a,
        'right': K_d,
        'paint': K_f,
        'next_colour': K_g,
        'attack': K_r,
    },
    'cursors': {
        'up': K_UP,
        'down': K_DOWN,
        'left': K_LEFT,
        'right': K_RIGHT,
        'paint': K_INSERT,
        'next_colour': K_DELETE,
        'attack': K_END,
    },
}


def get_keybindings():
    return KEYBINDINGS
