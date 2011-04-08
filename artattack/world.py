"""Represent the state of the world in 2D space and the artworks encapsulated within.

There are three spaces in the game:

 - Screen space. Coordinates are an integer tuple
 - Floor space. Coordinates are a real vector
 - Arwork space. Coordinates are an ArtworkPosition

There are various mappings between these spaces.

"""

import random

from .artwork import *

from .data import filepath
from .animation import Loadable

from vector import Vector

BACKGROUND = filepath('background.png', subdir='background')

LEFT_ARTWORK = 0
RIGHT_ARTWORK = 1

COLLISION_GROUP_PLAYER = 1
COLLISION_GROUP_POWERUP = 2

class Actor(Loadable):
    DEFAULT_SPRITE = 'undefined'

    COLLISION_GROUPS = 0
    COLLISION_MASK = 0

    RADIUS = 10

    def __init__(self, pos):
        self.pos = pos
        self.sprite = self.DEFAULT_SPRITE

    def __str__(self):
        return '<%s at %s>' % (self.__class__.__name__, self.pos)

    def kill(self):
        self.world.kill(self)

    def get_sprite(self):
        return self.sprites[self.sprite]

    def update(self, dt):
        sprite = self.get_sprite()
        if hasattr(self.sprite, 'update'):
            self.sprite.update(dt)

    def draw(self, screen):
        self.get_sprite().draw(screen, floor_to_screen(self.pos))

    def handle_collision(self, ano):
        """Handle a collision between this actor and another.
        
        Default behaviour is to do nothing.
        
        """
        


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
        from .powerups import PowerupFactory
        from .player import RedPlayer, BluePlayer
        self.painting = painting
        self.background = pygame.image.load(BACKGROUND).convert()
        self.actors = []

        outlines = self.painting.build_outline_surface(*ARTWORK_SIZE)

        self.red_artwork = Artwork(painting, self.background.subsurface(RECT_RED), RECT_RED.copy(), outlines=outlines)
        self.blue_artwork = Artwork(painting, self.background.subsurface(RECT_BLUE), RECT_BLUE, outlines=outlines)

        # For convenience
        self.artworks = (self.red_artwork, self.blue_artwork)

        red_start = ArtworkPosition.artwork_centre(self, LEFT_ARTWORK)
        blue_start = ArtworkPosition.artwork_centre(self, RIGHT_ARTWORK)
        self.red_player = RedPlayer(self, self.red_artwork, red_start)
        self.blue_player = BluePlayer(self, self.blue_artwork, blue_start)
        self.red_player.set_other_player(self.blue_player)
        self.blue_player.set_other_player(self.red_player)

        # Also for convenience
        self.players = (self.red_player, self.blue_player)

        for p in self.players:
            self.spawn(p.pc)

        self.powerup_factory = PowerupFactory(self)

    def spawn(self, actor):
        actor.world = self
        actor.alive = True
        self.actors.append(actor)

    def kill(self, actor):
        actor.alive = False
        self.actors.remove(actor)

    def get_floor_space(self):
        """Compute the top left and bottom right floor positions of the space"""
        tl = ArtworkPosition(self, LEFT_ARTWORK, 0, 0).floor_pos()
        br = ArtworkPosition(self, RIGHT_ARTWORK, self.blue_artwork.width - 1, self.blue_artwork.height - 1).floor_pos()
        return tl, br

    def give_colour(self):
        """Give each player a random colour."""
        for player in self.players:
            player.palette.add_colour(self.get_random_colour())

    def get_random_colour(self):
        palette = self.painting.get_palette()
        return random.choice(palette)

    def give_all_colours(self):
        palette = self.painting.get_palette()
        for player in self.players:
            player.palette.colours = palette[:]

    def drop_powerups(self):
        for side in range(2):
            self.powerup_factory.drop(side)

    def update(self, dt):
        for p in self.players:
            p.update(dt)

        for a in self.actors:
            a.update(dt)

        self.handle_collisions()

        self.powerup_factory.update(dt)

    def handle_collisions(self):
        """Brute force collision detection with O(n^2) time complexity.
        """
        acs = self.actors[:]
        for i, a in enumerate(acs):
            if not a.alive:
                continue

            for b in acs[i + 1:]:
                if not b.alive:
                    continue

                if a.COLLISION_MASK & b.COLLISION_GROUPS:
                    if (b.pos - a.pos).length2 < (a.RADIUS + b.RADIUS) * (a.RADIUS + b.RADIUS):
                        #print a, "collides", b
                        a.handle_collision(b)

    def actors_in_region(self, tl, br):
        x1, y1 = tl
        x2, y2 = br
        for a in self.actors:
            p = a.pos
            if x1 <= p.x < x2 and y1 <= p.y < y2:
                yield a

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        self.painting.draw(screen)
        self.red_artwork.draw(screen)
        self.blue_artwork.draw(screen)

        for p in self.players:
            p.draw(screen)
        self.actors.sort(key=lambda a: a.pos.y)
        for a in self.actors:
            a.draw(screen)

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
