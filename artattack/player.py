"""Classes representing each player in the game."""

from pygame.color import Color


class PlayerPalette(object):
    """A player's collection of colours.
    
    One of these colours is selected for drawing at a time.

    """
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
        xoff, yoff = self.DISPLAY_POS
        for pos, c in zip(self.SWATCH_POSITIONS, self.colours): 
            if c is None:
                continue
            x, y = pos
            c.draw_swatch(screen, (x + xoff, y + yoff)) 


class PlayerPaletteLeft(PlayerPalette):
    SWATCH_POSITIONS = [(52, 5), (82, 5), (111, 15), (121, 43), (97, 62), (67, 67)]
    DISPLAY_POS = (8, 14)

class PlayerPaletteRight(PlayerPalette):
    SWATCH_POSITIONS = [(143 - x, y) for x, y in PlayerPaletteLeft.SWATCH_POSITIONS]
    DISPLAY_POS = (852, 14)



class Player(object):
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

    @classmethod
    def load(cls):
        pass


class RedPlayer(Player):
    COLOUR = Color('#880000')
    PALETTE_CLASS = PlayerPaletteLeft


class BluePlayer(Player):
    COLOUR = Color('#3333AA')
    PALETTE_CLASS = PlayerPaletteRight
