"""Classes to represent artworks - the originals and the copies."""

import pygame
from pygame.locals import *

from .data import filepath
from .paint import PaintColour


PAINTINGS_DIR = 'paintings'


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

    def draw(self, screen):
        screen.blit(self.surface, (390, 70))


class Artwork(object):
    """A player's copy of an original painting."""
    def __init__(self, painting, rect):
        """Create an artwork to copy painting occupying screen position rect."""

        self.painting = painting
        self.artwork = self.painting.painting.copy()

        # Compute display dimensions of a pixel
        w, h = self.artwork.get_size()
        self.rect = rect
        self.xpix = rect.width // w
        self.ypix = rect.height // h

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
        
        self.surface = pygame.Surface((self.rect.width, self.rect.height))
        self.surface.fill((255, 255, 255))

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
        screen.blit(self.surface, self.rect)

