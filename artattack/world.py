"""Represent the state of the world in 2D space and the artworks encapsulated within."""

import random

from .player import RedPlayer, BluePlayer
from .artwork import *
from .tools import Brush


class ArtworkPosition(object):
    """A pixel position within a pair of artworks.
    
    The domain is the artworks plus a 1-pixel border outside each, which allows
    a 3x3 brush to paint the single edge pixels.

    This class also provides arithmetic for cursor control that allows a cursor
    to move from one artwork to the next.

    """
    def __init__(self, world, artwork, x, y):
        self.world = world
        self.artwork = artwork
        self.x = x
        self.y = y

    def __repr__(self):
        return '<artwork-%r, (%r, %r)>' % (self.artwork, self.x, self.y)

    def get_artwork(self):
        return self.world.artworks[self.artwork]

    def pos(self):
        """Return the pixel position within the relevant artwork."""
        return (self.x, self.y)

    def __add__(self, v):
        """"Return a new ArtworkPosition offset by v"""
        vx, vy = v

        w = self.world.painting.painting.get_width()
        h = self.world.painting.painting.get_height()
        nx = self.x + vx
        ny = max(-1, min(self.y + vy, h))
        a = self.artwork

        if nx < -1:
            if a > 0:
                a = max(a + (nx + 1) // (w + 2), 0)
                nx = ((nx + 1) % (w + 2) - 1)
            else:
                nx = -1
        elif nx > w:
            if a < (len(self.world.artworks) - 1):
                a = min(a + (nx + 1) // (w + 2), len(self.world.artworks) - 1)
                nx = ((nx + 1) % (w + 2) - 1)
            else:
                nx = w

        return ArtworkPosition(self.world, a, nx, ny)

    def screen_rect(self):
        a = self.world.artworks[self.artwork]
        return a.screen_rect_for_pixel(self.pos())

    @staticmethod
    def artwork_centre(world, artwork):
        w = world.painting.painting.get_width()
        h = world.painting.painting.get_height()

        return ArtworkPosition(world, artwork, w // 2, h // 2)



class World(object):
    def __init__(self, painting):
        self.painting = painting

        self.red_artwork = Artwork(painting, Rect(69, 305, 375, 248))
        self.red_player = RedPlayer(self)
        self.red_player.set_tool(Brush(self, ArtworkPosition.artwork_centre(self, 0)))

        self.blue_artwork = Artwork(painting, Rect(591, 305, 375, 248))
        self.blue_player = BluePlayer(self)
        self.blue_player.set_tool(Brush(self, ArtworkPosition.artwork_centre(self, 1)))
        
        # For convenience
        self.artworks = (self.red_artwork, self.blue_artwork)
        self.players = (self.red_player, self.blue_player)

    def give_colour(self):
        """Give each player a random colour."""
        palette = self.painting.get_palette()
        for player in self.players:
            player.palette.add_colour(random.choice(palette))

    def draw(self, screen):
        self.painting.draw(screen)
        self.red_artwork.draw(screen)
        self.blue_artwork.draw(screen)

        self.red_player.draw(screen)
        self.blue_player.draw(screen)

    @staticmethod
    def for_painting(filename):
        painting = Painting(filename)
        return World(painting)

    def artwork_pixel_for_screen_pos(self, pos):
        """Return the x, y coordinates of the pixel that corresponds to pos, or None if it is outside the Artwork bounds"""
        for artwork in self.artworks:
            if not artwork.rect.collidepoint(pos):
                continue
            return artwork.pixel_for_screen_pos(pos)
