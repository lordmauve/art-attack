#!/usr/bin/python

import sys
import os.path
import random
import datetime

import pygame
from pygame.locals import *

from .data import screenshot_path
from .game import TwoPlayerController, HostController, ClientController
from .text import Label


DEFAULT_PAINTING = 'desert-island2.png'


class Game(object):
    """Wraps the Pygame initialisation/event loop system.
    
    All behaviour is delegated to a Gamestate
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 600))
        self.gamestate = None

    def set_gamestate(self, gamestate):
        gamestate.game = self
        self.gamestate = gamestate

    def end(self):
        self.keeprunning = False

    def run(self):
        clock = pygame.time.Clock()

        self.keeprunning = True
        while self.keeprunning:
            dt = clock.tick(30) / 1000.0
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        return
                    elif event.key == K_F12:
                        self.save_screenshot()
                    self.gamestate.on_key(event)

            self.gamestate.update(dt)
            self.gamestate.draw(self.screen)

            pygame.display.flip()

    def save_screenshot(self):
        pygame.image.save(self.screen, screenshot_path(datetime.datetime.now().strftime('screenshot_%Y-%m-%d_%H:%M:%S.png')))


def menu():
    from .menu import GameMenu
    game = Game()
    game.set_gamestate(GameMenu())
    game.run()
    pygame.quit()


def main(painting=DEFAULT_PAINTING, timelimit=120):
    game = Game()
    game.set_gamestate(TwoPlayerController(painting, timelimit=timelimit))
    game.run()
    pygame.quit()


def host(painting=DEFAULT_PAINTING, timelimit=120, port=None):
    game = Game()
    if port is not None:
        gs = HostController(painting, timelimit=timelimit, port=port)
    else:
        gs = HostController(painting, timelimit=timelimit)
    game.set_gamestate(gs)
    game.run()
    pygame.quit()


def connect(host, port=None):
    game = Game()
    if port is not None:
        gs = ClientController(host, port)
    else:
        gs = ClientController(host)
    game.set_gamestate(gs)
    game.run()
    pygame.quit()
