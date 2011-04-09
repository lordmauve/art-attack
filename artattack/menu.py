import os
import math

import pygame
from pygame.locals import *


from .artwork import Painting
from .data import filepath
from .animation import Loadable, sprite
from .game import TwoPlayerController
from .text import Label


class Button(object):
    """A notional position of a button on screen.
    
    This button doesn't draw itself or anything.

    """

    def __init__(self, name, pos):    
        self.name = name
        self.pos = pos

        self.left = None
        self.right = None
        self.up = None
        self.down = None

    def leftof(self, b):
        self.right = b
        b.left = self

    def rightof(self, b):
        self.left = b
        b.right = self

    def above(self, b):
        self.down = b
        b.up = self

    def below(self, b):
        self.up = b
        b.down = self


class ButtonSet(object):
    def __init__(self):
        self.buttons = []

    def add(self, name, pos):
        b = Button(name, pos)
        self.buttons.append(b)
        return b


class Brush(Loadable):
    SPRITES = {
        'brush': sprite('menu-brush', (-3, -125))
    }
    MOVE_TIME = 0.3

    def __init__(self, button):
        self.pos = button.pos
        self.button = button
        self.initial_pos = button.pos
        self.target_pos = button.pos
        self.t = self.MOVE_TIME

    def set_button(self, button):
        self.button = button
        self.initial_pos = self.pos
        self.target_pos = self.button.pos
        self.t = 0

    def up(self):
        if self.button.up:
            self.set_button(self.button.up)

    def down(self):
        if self.button.down:
            self.set_button(self.button.down)

    def left(self):
        if self.button.left:
            self.set_button(self.button.left)

    def right(self):
        if self.button.right:
            self.set_button(self.button.right)

    def update(self, dt):
        self.t += dt
        if self.t > self.MOVE_TIME:
            self.pos = self.target_pos
        else:
            frac = math.cos(math.pi * 0.5 * self.t / self.MOVE_TIME)
            frac = frac * frac
            tx, ty = self.target_pos
            ix, iy = self.initial_pos
            x = int(frac * ix + (1 - frac) * tx + 0.5)
            y = int(frac * iy + (1 - frac) * ty + 0.5)
            self.pos = x, y

    def draw(self, screen, off):
        x, y = self.pos
        xoff, yoff = off
        self.sprites['brush'].draw(screen, (x + xoff, y + yoff))


class GameMenu(Loadable):
    SPRITES = {
        'menu': sprite('game-menu'),
        'menu-brush': sprite('menu-brush', (5, 124)),
    }

    def __init__(self, controller=TwoPlayerController):
        self.load()
        Brush.load()
        self.controller = controller
        self.setup_buttons()
        self.timelimit = 180
        self.timelimit_label = Label((730, 310), align=Label.ALIGN_RIGHT, size=30)

        self.load_paintings()

    def load_paintings(self):
        self.paintings = os.listdir(filepath('paintings'))
        self.selected_painting = 0
        self.load_painting()

    def get_painting(self):
        return self.paintings[self.selected_painting]

    def load_painting(self):
        orig = pygame.image.load(filepath(self.get_painting(), subdir='paintings'))
        self.painting = pygame.transform.scale(orig, (180, 120)).convert()

    def setup_buttons(self):
        buttons = ButtonSet()
        start_game = Button('start_game', (512, 331))
        painting_left = Button('painting_left', (258, 168))
        painting_right = Button('painting_right', (527, 168))
        timelimit_up = Button('timelimit_up', (565, 234))
        timelimit_down = Button('timelimit_down', (565, 265))
        back = Button('back', (359, 400))

        painting_left.leftof(painting_right)
        painting_right.above(timelimit_up)
        timelimit_up.above(timelimit_down)
        timelimit_down.above(start_game)
        start_game.above(back)
        start_game.rightof(back)

        self.brush = Brush(start_game)

    def update(self, dt):
        self.brush.update(dt)

    def on_key(self, event):
        if event.key == K_UP:
            self.brush.up()
        elif event.key == K_DOWN:
            self.brush.down()
        elif event.key == K_LEFT:
            self.brush.left()
        elif event.key == K_RIGHT:
            self.brush.right()
        elif event.key == K_RETURN:
            self.do()

    def do(self):
        action = self.brush.button.name
        getattr(self, action)()

    def painting_left(self):
        self.selected_painting = (self.selected_painting - 1) % len(self.paintings)
        self.load_painting()

    def painting_right(self):
        self.selected_painting = (self.selected_painting + 1) % len(self.paintings)
        self.load_painting()

    def timelimit_up(self):
        self.timelimit += 30

    def timelimit_down(self):
        self.timelimit = max(0, self.timelimit - 30)

    def back(self):
        self.game.end()

    def start_game(self):
        self.game.set_gamestate(self.controller(painting=self.get_painting(), timelimit=self.timelimit))

    def draw(self, screen):
        screen.fill((255, 255, 255))
        w, h = screen.get_size()

        banner = self.sprites['menu']
        sw, sh = banner.get_size()
    
        x = w // 2 - sw // 2
        y = h // 2 - sh // 2

        banner.draw(screen, (x, y))

        screen.blit(self.painting, (x + 300, y + 111))

        if self.timelimit == 0:
            text = 'Off'
        else:
            text = '%d:%02d' % (int(self.timelimit / 60), self.timelimit % 60)
        self.timelimit_label.draw(screen, text)
        self.brush.draw(screen, (x, y))
