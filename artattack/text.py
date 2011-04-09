import pygame
from pygame.locals import Color


class Label(object):
    """A label with a fixed position and style, but changing text.

    The label caches its surfaces to avoid re-rendering text that hasn't
    changed.

    """
    ALIGN_LEFT = 0
    ALIGN_RIGHT = 1
    ALIGN_CENTRE = 2

    fonts = {}

    def __init__(self, anchor, align=ALIGN_LEFT, colour='white', shadow=True, size=18):
        self.anchor = anchor
        self.align = align
        self.colour = Color(colour)
        self.shadow = shadow
        self.text = None
        self.font = self.load_font(size)

    def set_colour(self, colour):
        self.colour = Color(colour)
        self.text = None

    def get_position(self):
        if self.align == Label.ALIGN_LEFT:
            return self.anchor
        elif self.align == Label.ALIGN_RIGHT:
            x, y = self.anchor
            return (x - self.text_surface.get_width(), y)
        elif self.align == Label.ALIGN_CENTRE:
            x, y = self.anchor
            return (x - self.text_surface.get_width() // 2, y)

    def rebuild_surfaces(self):
        self.text_surface = self.font.render(self.text, True, self.colour)
        self.shadow_surface = self.font.render(self.text, True, Color('#00000080'))

    def draw(self, screen, text):
        if text != self.text:
            self.text = text
            self.rebuild_surfaces()
        x, y = self.get_position()
        screen.blit(self.shadow_surface, (x + 1, y + 1))
        screen.blit(self.text_surface, (x, y))

    @classmethod
    def load_font(cls, size):
        try:
            return cls.fonts[size]
        except KeyError:
            cls.fonts[size] = pygame.font.SysFont("FreeSans, Arial, Sans, Helvetica", size)
            return cls.fonts[size]
