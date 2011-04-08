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

WINNER_RED = 0
WINNER_BLUE = 1
NO_WINNER = -1


class GameState(object):
    def __init__(self, painting, timelimit=120):
        PaintColour.load()
        RedPlayer.load()
        BluePlayer.load()

        self.world = World.for_painting(painting)
        self.world.give_colour()
        
        self.timelimit = timelimit
        self.t = timelimit
        if timelimit:
            self.time_label = Label((512, 560), align=Label.ALIGN_CENTRE, size=24)

    def get_winner(self):
        red = self.world.red_player.artwork.completeness()[0]
        blue = self.world.blue_player.artwork.completeness()[0]
        if red > blue:
            return WINNER_RED
        elif red < blue:
            return WINNER_BLUE
        else:
            return NO_WINNER            

    def end_game(self):
        winner = self.get_winner()
        self.game.set_gamestate(EndGameState(self, winner))

    def on_key(self, event):
        if event.key == K_F10:
            self.world.give_all_colours()
        if event.key == K_F9:
            self.world.drop_powerups()
        if event.key == K_F8:
            self.end_game()

        keybindings = get_keybindings()
        ks = [
            (keybindings['red'], self.world.red_player),
            (keybindings['blue'], self.world.blue_player),
        ]

        for (keyset, player) in ks:
            if event.key in keyset:
                getattr(player, keyset[event.key])()

    def update(self, dt):
        if self.timelimit:
            self.t -= dt
            if self.t <= 0:
                self.t = 0
                self.end_game()
        self.world.update(dt)

    def draw(self, screen):
        self.world.draw(screen)
        if self.timelimit:
            text = '%d:%04.1f' % (int(self.t / 60), self.t % 60)
            self.time_label.draw(screen, text)


class BannerGameState(Loadable):
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.__class__.load()

    def get_banners(self):
        raise NotImplementedError("Subclasses should define this method to return a tuple (left_banner, right_banner).")

    def draw(self, screen):
        self.gamestate.draw(screen)

        w, h = screen.get_size()

        for i, banner in enumerate(self.get_banners()):
            sw, sh = banner.get_size()
        
            x = i * w //  2 + w // 4 - sw // 2
            y = h // 2 - sh // 2

            banner.draw(screen, (x, y))


class StartGameState(BannerGameState):
    SPRITES = {
        'ready': sprite('game-ready'),
        'steady': sprite('game-steady'),
        'paint': sprite('game-paint'),
    }

    def  __init__(self, gamestate, skippable=True):
        super(StartGameState, self).__init__(gamestate)
        self.skippable = skippable
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
        if self.skippable:
            if event.key == K_SPACE:
                self.t += 1

    def get_banners(self):
        s = self.sprites[self.sprite]
        return s, s


class EndGameState(BannerGameState):
    SPRITES = {
        'winner': sprite('gameover-winner'),
        'loser': sprite('gameover-loser', (0, 15)),
        'draw': sprite('gameover-draw'),
    }

    def  __init__(self, gamestate, winner):
        self.gamestate = gamestate
        self.__class__.load()
        self.t = 0 

        if winner == WINNER_RED:
            self.banners = 'winner', 'loser'
        elif winner == WINNER_BLUE:
            self.banners = 'loser', 'winner'
        elif winner == NO_WINNER:
            self.banners = 'draw', 'draw'

    def get_banners(self):
        return [self.sprites[s] for s in self.banners]

    def update(self, dt):
        self.t += dt

        if self.t > 5:
            self.game.end()

    def on_key(self, event):
        if event.key == K_SPACE:
            self.t += 5
