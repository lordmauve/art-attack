"""Classes representing tools for painting onto an Artwork."""

import random

import pygame
from pygame.color import Color

from .animation import Loadable

class Brush(Loadable):
    SOUNDS = {
        'brush1': 'brush1.wav',
        'brush2': 'brush2.wav',
        'brush3': 'brush3.wav',
    }

    """A 3x3 brush to paint onto an Artwork"""
    def __init__(self, world, pos):
        self.world = world
        self.pos = pos

    def topleft(self):
        """Return the top left pixel of the brush, limited to the area of the artwork."""
        x, y = self.pos.pos()
        a = self.pos.get_artwork()
        x = max(0, min(x - 1, a.width - 1))
        y = max(0, min(y - 1, a.height - 1))
        return x, y

    def bottomright(self):
        """Return the bottom right pixel of the brush, limited to the area of the artwork."""
        x, y = self.pos.pos()
        a = self.pos.get_artwork()
        x = max(0, min(x + 1, a.width - 1))
        y = max(0, min(y + 1, a.height - 1))
        return x, y

    def draw(self, screen, colour):
        a = self.pos.get_artwork()
        r = a.screen_rect_for_pixel(self.topleft())
        r2 = a.screen_rect_for_pixel(self.bottomright())
        r.union_ip(r2)
        pygame.draw.rect(screen, colour, r, 1)

    def update(self):
        pos = pygame.mouse.get_pos()
        px = self.artwork.pixel_for_screen_pos(pos)
        if px:
            self.pos = px

    def move_left(self):
        self.pos += (-1, 0)

    def move_right(self):
        self.pos += (1, 0)

    def move_up(self):
        self.pos += (0, -1)

    def move_down(self):
        self.pos += (0, 1)

    def paint(self, colour):
        left, top = self.topleft()
        right, bottom = self.bottomright()
        artwork = self.pos.get_artwork()
        for j in range(top, bottom + 1):
            for i in range(left, right + 1):
                artwork.paint_pixel((i, j), colour)

        sound = random.choice(self.sounds.values())
        sound.play()


