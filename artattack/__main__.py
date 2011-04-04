#!/usr/bin/python

import sys
import os.path
import random
import datetime

import pygame
from pygame.locals import *

from .data import filepath

from .paint import PaintColour


PAINTINGS_DIR = 'paintings'
BACKGROUND = filepath('background.png', subdir='background')

del color

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

    def get_palette(self):
        return [PaintColour(i, c) for i, c in enumerate(self.painting.get_palette())]

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

        self.tool = Brush(self)

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
        if self.tool:
            self.tool.draw(screen)


class PlayerPalette(object):
    """A player's collection of colours.
    
    One of these colours is selected for drawing at a time.

    """
    LEFT_SWATCH_POSITIONS = [(52, 5), (82, 5), (111, 15), (121, 43), (97, 62), (67, 67)]
    MAX_COLOURS = 6

    def __init__(self):
        self.colours = [None] * self.MAX_COLOURS
        self.selected = None

    def get_selected(self):
        return self.colours[self.selected]

    def add_colour(self, colour):
        for i, c in enumerate(self.colours):
            if c is None:
                self.colours[i] = colour
                if self.selected is None:
                    self.selected = i
                return
        else:
            self.colours[self.selected] = colour

    def draw(self, screen):
        for pos, c in zip(self.LEFT_SWATCH_POSITIONS, self.colours): 
            if c is None:
                continue
            x, y = pos
            x += 8
            y += 55
            c.draw_swatch(screen, (x, y)) 


class Brush(object):
    """A 3x3 brush to paint onto an Artwork"""
    def __init__(self, artwork, pos=None):
        self.artwork = artwork
        if pos is None:
            pos = (self.artwork.width // 2, self.artwork.height // 2)
        self.pos = pos
        self.color = Color('red')

    def topleft(self):
        """Return the top left pixel of the brush, limited to the area of the artwork."""
        return (max(0, self.pos[0] - 1), max(0, self.pos[1] - 1))

    def bottomright(self):
        """Return the bottom right pixel of the brush, limited to the area of the artwork."""
        w, h = self.artwork.artwork.get_size()
        return (min(w, self.pos[0] + 1), min(h, self.pos[1] + 1))

    def draw(self, screen):
        r = self.artwork.screen_rect_for_pixel(self.topleft())
        r.union_ip(self.artwork.screen_rect_for_pixel(self.bottomright()))
        pygame.draw.rect(screen, self.color, r, 1)

    def update(self):
        pos = pygame.mouse.get_pos()
        px = self.artwork.pixel_for_screen_pos(pos)
        if px:
            self.pos = px

    def paint(self, colour):
        left, top = self.topleft()
        right, bottom = self.bottomright()
        for j in range(top, bottom + 1):
            for i in range(left, right + 1):
                self.artwork.paint_pixel((i, j), colour)


def load():
    global screen, background, painting, red_artwork, red_palette
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))

    background = pygame.image.load(BACKGROUND).convert()
    PaintColour.load()

    painting = Painting('desert-island2.png')
    red_artwork = Artwork(painting, Rect(69, 343, 375, 248))
    red_palette = PlayerPalette()
    red_palette.add_colour(painting.get_palette()[0])


def draw():
    screen.blit(background, (0, 0))
    painting.draw(screen)
    red_artwork.draw(screen)
    red_palette.draw(screen)


def save_screenshot():
    pygame.image.save(screen, datetime.datetime.now().strftime('screenshots/screenshot_%Y-%m-%d_%H:%M:%S.png'))


def main():
    clock = pygame.time.Clock()

    keeprunning = True
    while keeprunning:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == MOUSEBUTTONDOWN:
                if red_artwork.tool:
                    colour = red_palette.get_selected().index
                    red_artwork.tool.paint(colour)
            elif event.type == KEYDOWN:
                if event.key == K_F12:
                    save_screenshot()

        if red_artwork.tool:
            red_artwork.tool.update()

        draw()
        pygame.display.flip()


load()
main()

