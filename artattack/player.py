"""Classes representing each player in the game."""

import time

from pygame.color import Color

from .tools import Brush
from .animation import Loadable


class PlayerCharacter(Loadable):
    """The player's avatar.

    The PlayerCharacter is not directly controlled, but moves
    automatically to keep in track with the player's brush cursor.
    
    (Eventually the game may swap from brush control to player control
    automatically if the player holds down a key. This would allow more
    responsive control of the character which will be important for PvP.)

    """

    DEFAULT_SPRITE = 'painting-right'

    sprite_offsets = {
        'painting-left': (50, 160),
        'painting-right': (60, 126),
        'painting-centre': (31, 150),
    }

    brush_offsets = {
        'painting-left': (13, 172),
        'painting-right': (107, 138),
        'painting-centre': (318, 168),
    }

    MAX_SPEED = 500

    def __init__(self, pos):
        self.pos = pos # character position, in floor space
        self.brush_pos = None  # The position the character should try to get to
        self.sprite = self.DEFAULT_SPRITE

    def track_brush(self, pos):
        """Update the position of the brush (in floor space)."""
        self.brush_pos = pos

    def update(self, dt):
        from .world import screen_to_floor
        if self.brush_pos is None:
            return
        t = self.brush_pos - screen_to_floor(*self.brush_offsets[self.sprite]) + screen_to_floor(*self.sprite_offsets[self.sprite])
        v = (t - self.pos)
        if v.length > self.MAX_SPEED * dt:
            v = v.scaled_to(self.MAX_SPEED * dt)
        self.pos += v

    def draw(self, screen):
        from .world import floor_to_screen
        x, y = floor_to_screen(self.pos)
        xoff, yoff = self.sprite_offsets[self.sprite]
        screen.blit(self.sprites[self.sprite], (x - xoff, y - yoff))

    @classmethod
    def for_brush_pos(cls, brush_pos):
        from .world import screen_to_floor
        floor_pos = brush_pos.floor_pos() - screen_to_floor(*cls.brush_offsets[cls.DEFAULT_SPRITE]) + screen_to_floor(*cls.sprite_offsets[cls.DEFAULT_SPRITE])
        return cls(floor_pos)


class RedPlayerCharacter(PlayerCharacter):
    SPRITES = {
        'painting-left': 'red-artist-painting-left.png',
        'painting-centre': 'red-artist-painting-centre.png',
        'painting-right': 'red-artist-painting-right.png',
    }


class BluePlayerCharacter(PlayerCharacter):
    SPRITES = {
        'painting-left': 'blue-artist-painting-left.png',
        'painting-centre': 'blue-artist-painting-centre.png',
        'painting-right': 'blue-artist-painting-right.png',
    }


class PlayerPalette(Loadable):
    """A player's collection of colours.
    
    One of these colours is selected for drawing at a time and this can be
    cycled through the colours. Features an MRU system so the least used colour
    is replaced on pickup, and players can use one key for toggling colours and
    cycling through them all.

    """
    MAX_COLOURS = 6
    SPRITES = {
        'selection_cursor': 'colour-selected.png'
    }

    def __init__(self):
        self.colours = []
        self.selected = None
        self.change_time = 0

    def get_selected(self):
        return self.colours[self.selected]

    def next(self):
        self.selected = (self.selected + 1) % len(self.colours)
        self.change_time = 1

    def update(self, dt):
        if self.change_time > 0:
            self.change_time -= dt
            if self.change_time <= 0:
                c = self.get_selected()
                self.colours.remove(c)
                self.colours.insert(0, c)
                self.selected = 0

    def add_colour(self, colour):
        """If the palette doesn't contain it, add the colour to the palette.
        
        Also select the new colour.

        """
        if colour in self.colours:
            return
        self.colours = [colour] + self.colours[:self.MAX_COLOURS - 1]
        self.selected = 0

    def draw(self, screen):
        xoff, yoff = self.DISPLAY_POS
        for i, pos, c in zip(range(self.MAX_COLOURS), self.SWATCH_POSITIONS, self.colours): 
            if c is None:
                continue
            x, y = pos
            c.draw_swatch(screen, (x + xoff, y + yoff)) 
            if i == self.selected:
                screen.blit(self.sprites['selection_cursor'], (x + xoff, y + yoff))


class PlayerPaletteLeft(PlayerPalette):
    SWATCH_POSITIONS = [(52, 5), (82, 5), (111, 15), (121, 43), (97, 62), (67, 67)]
    DISPLAY_POS = (8, 14)


class PlayerPaletteRight(PlayerPalette):
    SWATCH_POSITIONS = [(141 - x, y) for x, y in PlayerPaletteLeft.SWATCH_POSITIONS]
    DISPLAY_POS = (850, 14)



class Player(object):
    """A player of the game.

    This class ties together the concepts of PlayerPalette, PlayerCharacter,
    tools and so on as one identity.

    """
    def __init__(self, world, start_pos):
        self.palette = self.PALETTE_CLASS()
        self.world = world

        self.pc = self.CHARACTER.for_brush_pos(start_pos)

        self.tool = None
        self.set_tool(Brush(self, start_pos))

    def set_tool(self, tool):
        if self.tool:
            tool.pos = self.tool.pos
        self.tool = tool

    def draw(self, screen):
        self.palette.draw(screen)
        if self.tool:
            self.tool.draw(screen, self.COLOUR)

        self.pc.draw(screen)

    def paint(self):
        if self.tool:
            colour = self.palette.get_selected().index
            self.tool.paint(colour)

    def up(self):
        if self.tool:
            self.tool.move_up()
            self.pc.track_brush(self.tool.pos.floor_pos())

    def down(self):
        if self.tool:
            self.tool.move_down()
            self.pc.track_brush(self.tool.pos.floor_pos())

    def left(self):
        if self.tool:
            self.tool.move_left()
            self.pc.track_brush(self.tool.pos.floor_pos())

    def right(self):
        if self.tool:
            self.tool.move_right()
            self.pc.track_brush(self.tool.pos.floor_pos())

    def next_colour(self):
        self.palette.next()

    def update(self, dt):
        self.palette.update(dt)
        self.pc.update(dt)

    @classmethod
    def load(cls):
        cls.CHARACTER.load()
        cls.PALETTE_CLASS.load()


class RedPlayer(Player):
    """Subclass of Player to specify properties specific to the red player."""

    COLOUR = Color('#880000')
    PALETTE_CLASS = PlayerPaletteLeft
    CHARACTER = RedPlayerCharacter
        

class BluePlayer(Player):
    """Subclass of Player to specify properties specific to the blue player."""

    COLOUR = Color('#3333AA')
    PALETTE_CLASS = PlayerPaletteRight
    CHARACTER = BluePlayerCharacter
