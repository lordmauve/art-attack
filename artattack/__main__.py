#!/usr/bin/python

import sys
import os.path
import random
import datetime

import pygame
from pygame.locals import *


from .game import GameState, StartGameState
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

    def start_game(self, gamestate):
        self.set_gamestate(StartGameState(gamestate))

    def set_gamestate(self, gamestate):
        gamestate.game = self
        self.gamestate = gamestate

    def end(self):
        self.keeprunning = False

    def run(self):
        clock = pygame.time.Clock()
        pygame.key.set_repeat(100, 30)

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
                        save_screenshot(self.screen)
                    self.gamestate.on_key(event)

            self.gamestate.update(dt)
            self.gamestate.draw(self.screen)

            pygame.display.flip()

    def save_screenshot(self):
        pygame.image.save(self.screen, screenshot_path(datetime.datetime.now().strftime('screenshot_%Y-%m-%d_%H:%M:%S.png')))


def main(painting=DEFAULT_PAINTING, timelimit=120):
    game = Game()
    game.start_game(GameState(painting, timelimit=timelimit))
    game.run()
    pygame.quit()
    pygame.quit()
