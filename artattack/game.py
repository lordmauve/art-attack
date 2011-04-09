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
from .world import World, ArtworkPosition
from .keybindings import get_keybindings
from .powerups import PowerupFactory
from .signals import Signal

WINNER_RED = 0
WINNER_BLUE = 1
NO_WINNER = -1


class GameplayGameState(Loadable):
    SOUNDS = {
        'chord': 'chord.wav',
    }

    def __init__(self, world, timelimit=120):
        self.load()
        PaintColour.load()
        RedPlayer.load()
        BluePlayer.load()
        Brush.load()
        PowerupFactory.load_all()
        self.on_time_over = Signal()

        self.world = world 
        self.set_timelimit(timelimit)

    def set_timelimit(self, timelimit):
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

    def time_left(self, dt, target):
        # FIXME: this is a really perverse way of scheduling
        return self.t > target > self.t - dt

    def update_time(self, dt):
        if self.timelimit:
            if self.time_left(dt, 10):
                self.time_label.set_colour('#ff3333')
            if self.t < 11:
                if int(self.t) - int(self.t - dt):
                    self.sounds['chord'].play()
            self.t -= dt

        if self.t <= 0:
            self.t = 0
            self.on_time_over.fire()

    def update(self, dt):
        self.update_time(dt)
        self.world.update(dt)

    def draw(self, screen):
        self.world.draw(screen)
        if self.timelimit:
            text = '%d:%04.1f' % (int(self.t / 60), self.t % 60)
            self.time_label.draw(screen, text)

    def on_key(self, event):
        """No direct key input here, as this gamestate is controlled by the gamestates that wrap it."""


class GameStateController(object):
    def __init__(self, painting, timelimit=120):
        self.g = GameplayGameState(None, timelimit)

        world = World.for_painting(painting)
        self.g.world = world

        self.g.world.give_colour()
        self.g.on_time_over.connect(self.end_game)
        self.gs = self.g

        self.start_game()

    def start_game(self):
        self.gs = StartGameState(self.g)
        self.gs.on_finish.connect(self.on_countdown_finish)

    def on_gameover_finish(self):
        self.game.end()

    def on_countdown_finish(self):
        self.gs = self.gs.gamestate 

    def end_game(self):
        winner = self.g.get_winner()
        self.gs = EndGameState(self.g, winner)
        self.gs.on_finish.connect(self.on_gameover_finish)

    def update(self, dt):
        self.gs.update(dt)

    def draw(self, screen):
        self.gs.draw(screen)


class TwoPlayerController(GameStateController):
    def on_key(self, event):
        if event.key == K_F8:
            self.end_game()

        self.gs.on_key(event)

        if hasattr(self.gs, 'world'):
            if event.key == K_F10:
                self.gs.world.give_all_colours()
            if event.key == K_F9:
                self.gs.world.drop_powerups()

            keybindings = get_keybindings()
            ks = [
                (keybindings['red'], self.gs.world.red_player),
                (keybindings['blue'], self.gs.world.blue_player),
            ]

            for (keyset, player) in ks:
                if event.key in keyset:
                    getattr(player, keyset[event.key])()


from .network import *

class NetworkController(GameStateController):
    status = ''
    started = False

    def draw(self, screen):
        if self.gs:
            self.gs.draw(screen)
        self.status_label.draw(screen, self.status)

    def set_status(self, msg):
        self.status = msg

    def update(self, dt):
        self.process_request()
        if self.started:
            self.gs.update(dt)

    def process_request(self):
        while True:
            try:
                op, payload = self.net.receive_message()
            except Empty:
                break

#            print op, payload
            try:
                handler = self.HANDLERS[op]
            except KeyError:
                print "%s: unhandled opcode %d, payload %r" % (self.__class__.__name__, op, payload)
                continue

            getattr(self, handler)(payload)

    # Common handlers

    def on_tool_move(self, player, pos):
        self.net.send_message(OP_TOOL_MOVE, (player.ID, pos.to_net()))

    def handle_tool_move(self, player_pos):
        world = self.g.world
        playerid, pos = player_pos
        pos = ArtworkPosition.from_net(pos, self.g.world)
        world.players[playerid].set_tool_position(pos)

    def on_palette_change(self, player, palette):
        self.net.send_message(OP_PALETTE_CHANGE, (player.ID, palette.to_net()))

    def handle_palette_change(self, player_palette):
        playerid, palette = player_palette
        world = self.g.world
        world.players[playerid].palette.from_net(palette, world.painting.get_palette_map())

    def handle_network_error(self, errorstr):
        self.set_status(errorstr)
        self.started = False

    def on_paint(self, player, tool, colour):
        msg = (
            player.ID,
            tool.__class__,
            tool.pos.to_net(),
            colour
        )
        self.net.send_message(OP_PAINT, msg)

    def handle_paint(self, player_tool):
        playerid, tool_class, pos, colour = player_tool
        world = self.g.world
        pos = ArtworkPosition.from_net(pos, world)
        tool = tool_class(world, pos)
        tool.paint(colour)
    
        world.players[playerid].pc.paint()

        #TODO: server should sync back the pixels under the tool
        # to eliminate race conditions with one player overpainting the other
        


class HostController(NetworkController):
    # A mapping of operation to handler
    HANDLERS = {
        OP_ERR: 'handle_network_error',
        OP_CONNECT: 'on_connect',
        OP_START: 'send_start',
        OP_PALETTE_CHANGE: 'handle_palette_change',
        OP_TOOL_MOVE: 'handle_tool_move',
        OP_PAINT: 'handle_paint',
        OP_ENDGAME: 'handle_end_game',
    }

    def __init__(self, painting, timelimit=120, port=DEFAULT_PORT):
        super(HostController, self).__init__(painting, timelimit)
        self.net = ServerSocket(port)
        self.net.start()
        self.status_label = Label((768, 565), align=Label.ALIGN_CENTRE, size=16)
        self.status = 'Waiting for connection...'
        self.connect_game_signals()

    def connect_game_signals(self):
        world = self.g.world
        world.on_powerup_spawn.connect(self.on_powerup_spawn)
        world.red_player.on_palette_change.connect(self.on_palette_change)
        world.red_player.on_tool_move.connect(self.on_tool_move)
        world.red_player.on_paint.connect(self.on_paint)

    def end_game(self):
        # Do nothing, wait for the client to send OP_ENDGAME, which means all game
        # packets have been received.
        pass

    def handle_end_game(self, payload):
        super(HostController, self).end_game()
        winner = self.g.get_winner()
        self.net.send_message(OP_ENDGAME, winner)

    def on_powerup_spawn(self, powerup):
        self.net.send_message(OP_POWERUP_SPAWN, (powerup.__class__, powerup.to_net()))

    def on_connect(self, remote_addr):
        self.set_status("Client connected.")
        self.send_gameconfig()

    def on_key(self, event):
        if hasattr(self.gs, 'world'):
            keybindings = get_keybindings()
            ks = [
                (keybindings['red'], self.gs.world.red_player),
            ]

            for (keyset, player) in ks:
                if event.key in keyset:
                    getattr(player, keyset[event.key])()

    def send_gameconfig(self):
        world = self.g.world
        self.net.send_message(OP_GAMECONFIG, {
            'timelimit': self.g.timelimit,
            'painting': world.painting,
            'red_palette': world.red_player.palette.to_net(),
            'blue_palette': world.blue_player.palette.to_net(),
        }) 

    def send_start(self, ready):
        self.started = True
        world = self.g.world
        self.net.send_message(OP_START, None)


class ClientController(NetworkController):
    HANDLERS = {
        OP_GAMECONFIG: 'configure_game',
        OP_ERR: 'handle_network_error',
        OP_START: 'handle_start',
        OP_PALETTE_CHANGE: 'handle_palette_change',
        OP_POWERUP_SPAWN: 'handle_powerup_spawn',
        OP_TOOL_MOVE: 'handle_tool_move',
        OP_PAINT: 'handle_paint',
        OP_ENDGAME: 'handle_end_game',
    }

    def __init__(self, host, port=DEFAULT_PORT):
        self.net = ClientSocket(host, port)
        self.status_label = Label((256, 565), align=Label.ALIGN_CENTRE, size=16)

        self.g = GameplayGameState(None, 0)
        self.gs = ConnectingGameState()
        self.net.start()

    def end_game(self):
        self.net.send_message(OP_ENDGAME, None)

    def handle_end_game(self, winner):
        self.gs = EndGameState(self.gs, winner)
        self.gs.on_finish.connect(self.on_gameover_finish)

    def handle_start(self, arg):
        self.started = True
        self.start_game()

    def configure_game(self, configdict):
        self.gs = self.g
        self.g.set_timelimit(configdict['timelimit'])
        world = World(configdict['painting'], powerups=False)
        self.gs.world = world

        self.handle_palette_change((0, configdict['red_palette']))
        self.handle_palette_change((1, configdict['blue_palette']))

        self.connect_game_signals()

        self.net.send_message(OP_START, None)

    def connect_game_signals(self):
        self.g.on_time_over.connect(self.end_game)
        world = self.g.world
        world.blue_player.on_palette_change.connect(self.on_palette_change)
        world.blue_player.on_tool_move.connect(self.on_tool_move)
        world.blue_player.on_paint.connect(self.on_paint)

    def handle_powerup_spawn(self, powerup):
        world = self.g.world
        cls, net = powerup
        inst = cls.from_net(net, world.painting.get_palette_map())
        world.spawn_powerup(inst)

    def on_key(self, event):
        if not hasattr(self.gs, 'world'):
            return

        keybindings = get_keybindings()
        ks = [
            (keybindings['blue'], self.gs.world.blue_player),
        ]

        for (keyset, player) in ks:
            if event.key in keyset:
                getattr(player, keyset[event.key])()
    
    def on_time_out(self):
        # Wait for the server to end the game
        pass


class BannerGameState(Loadable):
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.__class__.load()

    def get_banners(self):
        raise NotImplementedError("Subclasses should define this method to return a tuple (left_banner, right_banner).")

    def update(self, dt):
        pass

    def draw(self, screen):
        if self.gamestate:
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

    SOUNDS = {
        'ready': 'ready.wav',
        'steady': 'steady.wav',
        'paint': 'paint.wav',
    }

    T_READY = 0.5
    T_STEADY = 2.0
    T_PAINT = 3.5
    T_END = 4.5

    def  __init__(self, gamestate, skippable=True):
        super(StartGameState, self).__init__(gamestate)
        self.on_finish = Signal()
        self.skippable = skippable
        self.t = 0 
        self.sprite = 'ready'

    def update(self, dt):
        t1 = self.t
        self.t += dt

        if self.t > self.T_END:
            self.on_finish.fire()
            return
        elif t1 < self.T_PAINT <= self.t:
            self.sprite = 'paint'
            self.sounds['paint'].play()
        elif t1 < self.T_STEADY <= self.t:
            self.sprite = 'steady'
            self.sounds['steady'].play()
        elif t1 < self.T_READY <= self.t:
            self.sounds['ready'].play()
            sprite = 'ready'

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

    SOUNDS = {
        'whistle': 'whistle.wav',
    }

    def  __init__(self, gamestate, winner):
        self.gamestate = gamestate
        self.on_finish = Signal()
        self.__class__.load()
        self.t = 0 

        if winner == WINNER_RED:
            self.banners = 'winner', 'loser'
        elif winner == WINNER_BLUE:
            self.banners = 'loser', 'winner'
        elif winner == NO_WINNER:
            self.banners = 'draw', 'draw'

        self.sounds['whistle'].play()

    def get_banners(self):
        return [self.sprites[s] for s in self.banners]

    def update(self, dt):
        self.t += dt

        if self.t > 5:
            self.on_finish.fire()

    def on_key(self, event):
        if event.key == K_SPACE:
            self.t += 5


class ConnectingGameState(BannerGameState):
    SPRITES = {
        'connecting': sprite('connecting')
    }

    def __init__(self):
        self.__class__.load()

    def draw(self, screen):
        w, h = screen.get_size()

        banner = self.sprites['connecting']
        sw, sh = banner.get_size()
    
        x = w // 2 - sw // 2
        y = h // 2 - sh // 2

        banner.draw(screen, (x, y))
