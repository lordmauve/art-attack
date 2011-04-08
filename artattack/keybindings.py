from pygame.locals import *

KEYBINDINGS = {
    'red': {
        K_w: 'up',
        K_s: 'down',
        K_a: 'left',
        K_d: 'right',
        K_f: 'paint',
        K_g: 'next_colour',
        K_r: 'attack',
    },
    'blue': {
        K_UP: 'up',
        K_DOWN: 'down',
        K_LEFT: 'left',
        K_RIGHT: 'right',
        K_INSERT: 'paint',
        K_DELETE: 'next_colour',
        K_END: 'attack',
    },
}


def get_keybindings():
    return KEYBINDINGS
