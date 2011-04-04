"""Classes representing tools for painting onto an Artwork."""

import pygame
from pygame.color import Color


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

