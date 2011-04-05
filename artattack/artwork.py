"""Classes to represent artworks - the originals and the copies."""

import pygame
from pygame.locals import *

from .data import filepath
from .paint import PaintColour


PAINTINGS_DIR = 'paintings'
OUTLINE_COLOUR = pygame.color.Color('#00000033')
BORDER_COLOUR = pygame.color.Color('#00000066')


class Painting(object):
    """An original painting as loaded from disk.

    This in effect represents a 'level' that players must copy. The detail
    present in the painting affects the difficult of the level.

    """

    def __init__(self, filename):
        self.filename = filename
        self.load()

    def load(self):
        fpath = filepath(self.filename, subdir=PAINTINGS_DIR)
        self.painting = pygame.image.load(fpath)
        self.surface = pygame.transform.scale(self.painting, (240, 160)).convert()
        self.palette = [PaintColour(i, c) for i, c in enumerate(self.painting.get_palette())]

    def get_palette(self):
        return self.palette 

    def build_outline_surface(self, sw, sh):
        """Generate partially transparent guidelines to show where players should paint.
        """
        outlines = pygame.Surface((sw, sh), pygame.SRCALPHA)
        outlines.fill((0, 0, 0, 0))
        w, h = self.painting.get_size()
        xstep = sw // w
        ystep = sh // h

        cy = 0
        for j in range(h):
            cx = 0
            for i in range(w):
                p = self.painting.get_at((i, j))
                if i > 0:
                    p2 = self.painting.get_at((i - 1, j))
                    if p != p2:
                        pygame.draw.line(outlines, OUTLINE_COLOUR, (cx, cy), (cx, cy + ystep))
                if j > 0:
                    p2 = self.painting.get_at((i, j - 1))
                    if p != p2:
                        pygame.draw.line(outlines, OUTLINE_COLOUR, (cx, cy), (cx + xstep, cy))
                cx += xstep  
            cy += ystep
        pygame.draw.rect(outlines, BORDER_COLOUR, Rect((0, 0), (xstep * w, ystep * h)), 1)
        return outlines

    def draw(self, screen):
        screen.blit(self.surface, (390, 55))


class Artwork(object):
    """A player's copy of an original painting."""
    def __init__(self, painting, surface, rect, outlines=None):
        """Create an artwork to copy painting occupying screen position rect."""

        self.painting = painting
        self.artwork = self.painting.painting.copy()
        self.surface = surface

        # Compute display dimensions of a pixel
        w, h = self.artwork.get_size()
        self.rect = rect
        self.xpix = rect.width // w
        self.ypix = rect.height // h
        self.outlines = outlines

        self.blank()

    @property
    def width(self):
        return self.artwork.get_width()

    @property
    def height(self):
        return self.artwork.get_height()

    def screen_rect_for_pixel(self, pixel):
        """Return the screen rectangle covered by pixel"""
        x, y = pixel
        return Rect(self.rect.left + self.xpix * x, self.rect.top + self.ypix * y, self.xpix, self.ypix)

    def pixel_for_screen_pos(self, pos):
        """Return the x, y coordinates of the pixel that corresponds to pos, or None if it is outside the Artwork bounds"""
        if not self.rect.collidepoint(pos):
            return None
        x, y = pos
        return (x - self.rect.left) // self.xpix, (y - self.rect.top) // self.ypix
        
    def blank(self):
        """Clear the artwork completely (paint it white)."""
        self.white = self.get_white()
        self.artwork.fill(self.white)
        
        self.surface.fill((255, 255, 255))
        if not self.outlines:
            self.outlines = self.painting.build_outline_surface(self.rect.width, self.rect.height)

    def get_white(self):
        """Find or set a white colour in the artwork palette, for blanking the canvas."""
        white = pygame.Color('#ffffff')
        pal = self.artwork.get_palette()
        try:
            return pal.index(white)
        except ValueError:
            pal = list(pal) + [white]
            self.artwork.set_palette(pal)
            return len(pal) - 1

    def paint_pixel(self, pixel, color):
        """Paint a pixel a given colour, where pixel = (x, y)"""
        self.artwork.set_at(pixel, color)
        x, y = pixel

        r = Rect(self.xpix * x, self.ypix * y, self.xpix, self.ypix)
        color = self.artwork.get_palette_at(color)

        self.surface.fill(color, r)

    def draw(self, screen):
        screen.blit(self.outlines, self.rect)

