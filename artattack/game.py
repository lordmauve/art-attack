import sys
import os.path
import random

import pygame
from pygame.locals import *

from .data import filepath, screenshot_path

del color


from .animation import Loadable, sprite
from .paint import PaintColour
from .artwork import *
from .player import *
from .tools import *
from .world import World
from .keybindings import get_keybindings


class GameState(object):
    def __init__(self, painting):
        PaintColour.load()
        RedPlayer.load()
        BluePlayer.load()

        self.world = World.for_painting(painting)
        self.world.give_colour()

    def on_key(self, event):
        if event.key == K_F10:
            self.world.give_all_colours()

        keybindings = get_keybindings()
        ks = [
            (keybindings['red'], self.world.red_player),
            (keybindings['blue'], self.world.blue_player),
        ]

        for (keyset, player) in ks:
            if event.key in keyset:
                getattr(player, keyset[event.key])()

    def update(self, dt):
        for player in self.world.players:
            player.update(dt)

    def draw(self, screen):
        self.world.draw(screen)


class StartGameState(Loadable):
    SPRITES = {
        'ready': sprite('game-ready'),
        'steady': sprite('game-steady'),
        'paint': sprite('game-paint'),
    }

    def  __init__(self, gamestate):
        self.gamestate = gamestate
        self.__class__.load()
        self.t = 0 
        self.sprite = 'ready'

    def update(self, dt):
        self.t += dt

        if self.t > 3:
            self.game.set_gamestate(self.gamestate)
        elif self.t > 2:
            self.sprite = 'paint'
        elif self.t > 1:
            self.sprite = 'steady'
        else:
            self.sprite = 'ready'

    def on_key(self, event):
        pass

    def draw(self, screen):
        self.gamestate.draw(screen)

        w, h = screen.get_size()
        s = self.sprites[self.sprite]
        sw, sh = s.get_size()
        
        x1 = w // 4 - sw // 2
        x2 = x1 + w // 2
        y = h // 2 - sh // 2
        s.draw(screen, (x1, y))
        s.draw(screen, (x2, y))

