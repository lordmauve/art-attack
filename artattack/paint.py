import pygame
from pygame.locals import *

from .data import *

del color

def make_coloured_surface(colour, mask, base=None, mask_dest=(0, 0), overlay=None, overlay_dest=(0, 0)):
    """Construct a colourised sprite by sandwiching a colourised layer between
    a base and an overlay.

    Multiply mask by colour, then composite the stack:
    
    overlay, if given, over (the colourised layer, over base, if given)

    The rectangle mask_dest if given specifies the location to blend mask onto
    base. The rectangle overlay_dest if given specifies the location to blend
    overlay onto base/mask.

    """
    col = mask.copy()
    col.fill(colour, None, BLEND_RGB_MULT)

    if base:
        out = base.copy()
        out.blit(col, mask_dest)
    else:
        out = col

    if overlay:
        out.blit(overlay, overlay_dest)

    return out


class PaintColour(object):
    def __init__(self, index, colour):
        self.index = index
        self.colour = colour
        self.swatch = make_coloured_surface(colour, self.colour_mask, overlay=self.colour_overlay)

    @classmethod
    def load(cls):
        cls.colour_mask = pygame.image.load(filepath('colour-mask.png', subdir='sprites')).convert_alpha()
        cls.colour_overlay = pygame.image.load(filepath('colour-overlay.png', subdir='sprites')).convert_alpha()

    def draw_swatch(self, screen, pos):
        screen.blit(self.swatch, pos)

