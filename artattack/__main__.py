#!/usr/bin/python

import sys
import os.path
import random
import datetime

import pygame
from pygame.locals import *

from .data import filepath


BACKGROUND = filepath('background.png', subdir='background')

del color

from .paint import PaintColour
from .artwork import *
from .player import *
from .tools import *


def load():
    global screen, background, painting, red_artwork, red_palette, red_tool
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))

    background = pygame.image.load(BACKGROUND).convert()
    PaintColour.load()

    painting = Painting('desert-island2.png')
    red_artwork = Artwork(painting, Rect(69, 343, 375, 248))
    red_palette = PlayerPalette()
    red_palette.add_colour(painting.get_palette()[0])
    red_tool = Brush(red_artwork)


def draw():
    screen.blit(background, (0, 0))
    painting.draw(screen)
    red_artwork.draw(screen)
    red_palette.draw(screen)
    red_tool.draw(screen)


def save_screenshot():
    pygame.image.save(screen, datetime.datetime.now().strftime('screenshots/screenshot_%Y-%m-%d_%H:%M:%S.png'))


def main():
    clock = pygame.time.Clock()

    keeprunning = True
    while keeprunning:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == MOUSEBUTTONDOWN:
                if red_tool:
                    colour = red_palette.get_selected().index
                    red_tool.paint(colour)
            elif event.type == KEYDOWN:
                if event.key == K_F12:
                    save_screenshot()

        if red_tool:
            red_tool.update()

        draw()
        pygame.display.flip()


load()
main()

