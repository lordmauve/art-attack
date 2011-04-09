import os
import math

import re
import pygame
from pygame.locals import *


from .artwork import Painting
from .data import filepath
from .animation import Loadable, sprite
from .game import TwoPlayerController, HostController, ClientController
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


class Menu(Loadable):
    def draw(self, screen):
        screen.fill((255, 255, 255))
        x, y = self.get_tl(screen)

        banner = self.sprites['menu']
        banner.draw(screen, (x, y))

    def draw_brush(self, screen):
        x, y = self.get_tl(screen)
        self.brush.draw(screen, (x, y))

    def get_tl(self, screen):
        w, h = screen.get_size()

        banner = self.sprites['menu']
        sw, sh = banner.get_size()
    
        x = w // 2 - sw // 2
        y = h // 2 - sh // 2
        return x, y

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


class GameMenu(Menu):
    SPRITES = {
        'menu': sprite('game-menu'),
        'menu-brush': sprite('menu-brush', (5, 124)),
    }

    def __init__(self, controller=TwoPlayerController, controller_args={}):
        GameMenu.load()
        Brush.load()
        self.controller = controller
        self.controller_args = controller_args
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
        self.game.set_gamestate(MainMenu())

    def start_game(self):
        self.game.set_gamestate(self.controller(painting=self.get_painting(), timelimit=self.timelimit, **self.controller_args))

    def draw(self, screen):
        super(GameMenu, self).draw(screen)
        x, y = self.get_tl(screen)
        screen.blit(self.painting, (x + 300, y + 111))

        if self.timelimit == 0:
            text = 'Off'
        else:
            text = '%d:%02d' % (int(self.timelimit / 60), self.timelimit % 60)
        self.timelimit_label.draw(screen, text)
        self.draw_brush(screen)


class MainMenu(Menu):
    SPRITES = {
        'menu': sprite('main-menu'),
        'menu-brush': sprite('menu-brush', (5, 124)),
    }

    def __init__(self):
        MainMenu.load()
        Brush.load()
        self.setup_buttons()

    def setup_buttons(self):
        local_game = Button('local_game', (512, 158)) 
        host_game = Button('host_game', (567, 238)) 
        join_game = Button('join_game', (519, 315)) 
        exit = Button('exit', (371, 391))

        local_game.above(host_game)
        host_game.above(join_game)
        join_game.above(exit)
        local_game.below(exit)

        self.brush = Brush(local_game)

    def local_game(self):
        self.game.set_gamestate(GameMenu())

    def host_game(self):
        self.game.set_gamestate(GameMenu(controller=HostController))

    def join_game(self):
        self.game.set_gamestate(JoinMenu())

    def exit(self):
        self.game.end()

    def draw(self, screen):
        super(MainMenu, self).draw(screen)
        self.draw_brush(screen)


class JoinMenu(Menu):
    SPRITES = {
        'menu': sprite('join-menu'),
        'menu-brush': sprite('menu-brush', (5, 124)),
    }

    def __init__(self):
        JoinMenu.load()
        Brush.load()
        self.setup_buttons()
        self.host = ''

        sw, sh = self.sprites['menu'].get_size()
    
        x = 512 - sw // 2
        y = 300 - sh // 2
        self.host_label = Label((x + 236, y + 210), align=Label.ALIGN_LEFT, size=30)

    def setup_buttons(self):
        start_game = Button('start_game', (512, 331))
        back = Button('back', (359, 400))
#        hostname = Button('hostname', (572, 226))
    
#        hostname.above(start_game)
        start_game.above(back)
        start_game.below(back)
#        back.above(hostname)

        self.brush = Brush(start_game)

    def start_game(self):
        self.game.set_gamestate(ClientController(host=self.host))

    def back(self):
        self.game.set_gamestate(MainMenu())

    def draw(self, screen):
        super(JoinMenu, self).draw(screen)
        self.host_label.draw(screen, self.host)
        
        lw, lh = self.host_label.text_surface.get_size()
        ax, ay = self.host_label.anchor
        pygame.draw.rect(screen, Color('white'), Rect((ax + lw, ay), (1, lh)), 0)

        self.draw_brush(screen)

    def on_key(self, event):
        super(JoinMenu, self).on_key(event)

        if event.unicode and re.match(r'^[A-Za-z0-9.-]$', event.unicode):
            self.host += str(event.unicode)
        elif event.key == K_BACKSPACE:
            self.host = self.host[:-1]
