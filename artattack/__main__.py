#!/usr/bin/python

import sys
import os.path
import random
import datetime

import pygame
from pygame.locals import *

from .data import filepath, screenshot_path


BACKGROUND = filepath('background.png', subdir='background')

del color

from .paint import PaintColour
from .artwork import *
from .player import *
from .tools import *
from .world import World


def load():
    global screen, background, world
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))

    background = pygame.image.load(BACKGROUND).convert()
    PaintColour.load()

    world = World.for_painting('desert-island2.png')
    world.give_colour()


def draw():
    screen.blit(background, (0, 0))
    world.draw(screen)


def save_screenshot():
    pygame.image.save(screen, screenshot_path(datetime.datetime.now().strftime('screenshot_%Y-%m-%d_%H:%M:%S.png')))


KEYBINDINGS = {
    'red': {
        K_w: 'up',
        K_s: 'down',
        K_a: 'left',
        K_d: 'right',
        K_f: 'paint',
    },
    'blue': {
        K_UP: 'up',
        K_DOWN: 'down',
        K_LEFT: 'left',
        K_RIGHT: 'right',
        K_INSERT: 'paint',
    },
}

def run():
    clock = pygame.time.Clock()
    pygame.key.set_repeat(100, 30)

    keeprunning = True
    while keeprunning:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return
                if event.key == K_F12:
                    save_screenshot()

                keybindings = [
                    (KEYBINDINGS['red'], world.red_player),
                    (KEYBINDINGS['blue'], world.blue_player),
                ]

                for (keyset, player) in keybindings:
                    if event.key in keyset:
                        getattr(player, keyset[event.key])()

        draw()
        pygame.display.flip()


def main():
    load()
    run()
    pygame.quit()
