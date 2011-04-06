"""Represent the state of the world in 2D space and the artworks encapsulated within.

There are three spaces in the game:

 - Screen space. Coordinates are an integer tuple
 - Floor space. Coordinates are a real vector
 - Arwork space. Coordinates are an ArtworkPosition

There are various mappings between these spaces.

"""

import random

from .player import RedPlayer, BluePlayer
from .artwork import *

from .data import filepath

from vector import Vector

BACKGROUND = filepath('background.png', subdir='background')


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

    def floor_pos(self):
        """Compute the floor-space position of the centre of the pixel."""
        r = self.screen_rect()
        return screen_to_floor(r.centerx, r.centery)

    @staticmethod
    def artwork_centre(world, artwork):
        w = world.painting.painting.get_width()
        h = world.painting.painting.get_height()

        return ArtworkPosition(world, artwork, w // 2, h // 2)


ARTWORK_SIZE = (360, 240)
RECT_RED = Rect((79, 310), ARTWORK_SIZE)
RECT_BLUE = Rect((602, 310), ARTWORK_SIZE)

# The ratio of pixels in the x direction to pixels in the y direction in floor
# space. The value derived from the perspective of some of the graphics that
# have been drawn to exist in floor space is about 0.38, but we haven't
# foreshortened the artworks that much so that they appear more face-on to
# players. This value is thus a compromise.
FORESHORTENING = 0.7

# Y-position of bottom of the back wall in screen space
BACK_WALL = 262

# Floor space <-> screen space conversions
# These are bijective (except that screen space coordinates are rounded to integers)

def screen_to_floor(x, y):
    return Vector((x, (y - BACK_WALL) / FORESHORTENING))

def floor_to_screen(v):
    return v.x, int(v.y * FORESHORTENING + BACK_WALL + 0.5)


class World(object):
    """The data model underlying what is drawn on the screen.
    
    The world contains some fixed instances of objects - eg. two players, two
    artworks, as well as a collection of arbitrary objects that exist in "floor
    space".
    
    Floor space matches pixels in the x direction and is
    FORESHORTENING * pixels in the y direction, measured from the back wall.

    """
    def __init__(self, painting):
        self.painting = painting
        self.background = pygame.image.load(BACKGROUND).convert()

        outlines = self.painting.build_outline_surface(*ARTWORK_SIZE)

        self.red_artwork = Artwork(painting, self.background.subsurface(RECT_RED), RECT_RED.copy(), outlines=outlines)
        self.blue_artwork = Artwork(painting, self.background.subsurface(RECT_BLUE), RECT_BLUE, outlines=outlines)

        # For convenience
        self.artworks = (self.red_artwork, self.blue_artwork)

        red_start = ArtworkPosition.artwork_centre(self, 0)
        blue_start = ArtworkPosition.artwork_centre(self, 1)
        self.red_player = RedPlayer(self, red_start)
        self.blue_player = BluePlayer(self, blue_start)

        # Also for convenience
        self.players = (self.red_player, self.blue_player)

    def give_colour(self):
        """Give each player a random colour."""
        palette = self.painting.get_palette()
        for player in self.players:
            player.palette.add_colour(random.choice(palette))

    def give_all_colours(self):
        palette = self.painting.get_palette()
        for player in self.players:
            player.palette.colours = palette[:]

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        self.painting.draw(screen)
        self.red_artwork.draw(screen)
        self.blue_artwork.draw(screen)

        for player in sorted(self.players, key=lambda p: p.pc.pos.y):
            player.draw(screen)

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
