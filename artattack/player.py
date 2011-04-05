"""Classes representing each player in the game."""

import time

from pygame.color import Color

from .data import load_sprite


class PlayerPalette(object):
    """A player's collection of colours.
    
    One of these colours is selected for drawing at a time and this can be
    cycled through the colours. Features an MRU system so the least used colour
    is replaced on pickup, and players can use one key for toggling colours and
    cycling through them all.

    """
    MAX_COLOURS = 6

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
                screen.blit(self.selection_cursor, (x + xoff, y + yoff))

    @classmethod
    def load(cls):
        cls.selection_cursor = load_sprite('colour-selected.png')


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
    def __init__(self, world):
        self.palette = self.PALETTE_CLASS()
        self.world = world
        self.tool = None

#        self.pos = self.START_POS

    def set_tool(self, tool):
        if self.tool:
            tool.pos = self.tool.pos
        self.tool = tool

    def draw(self, screen):
        self.palette.draw(screen)
        if self.tool:
            self.tool.draw(screen, self.COLOUR)

    def paint(self):
        if self.tool:
            colour = self.palette.get_selected().index
            self.tool.paint(colour)

    def up(self):
        if self.tool:
            self.tool.move_up()

    def down(self):
        if self.tool:
            self.tool.move_down()

    def left(self):
        if self.tool:
            self.tool.move_left()

    def right(self):
        if self.tool:
            self.tool.move_right()

    def next_colour(self):
        self.palette.next()

    def update(self, dt):
        self.palette.update(dt)

    @classmethod
    def load(cls):
        pass


class RedPlayer(Player):
    """Subclass of Player to specify properties specific to the red player."""

    COLOUR = Color('#880000')
    PALETTE_CLASS = PlayerPaletteLeft
        

class BluePlayer(Player):
    """Subclass of Player to specify properties specific to the blue player."""

    COLOUR = Color('#3333AA')
    PALETTE_CLASS = PlayerPaletteRight


class PlayerCharacter(object):
    """The player's avatar.

    The PlayerCharacter is not directly controlled, but moves
    automatically to keep in track with the player's brush cursor.
    
    (Eventually the game may swap from brush control to player control
    automatically if the player holds down a key. This would allow more
    responsive control of the character which will be important for PvP.)

    """

    def __init__(self, pos):
        self.pos = pos # character position, in floor space
        self.brush_pos = None # position of the brush, in floor space

    def track_brush(self, pos):
        """Update the position of the brush."""
        self.brush_pos = pos

    def update(self):
        pass

