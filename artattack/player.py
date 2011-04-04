"""Classes representing each player in the game."""

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


