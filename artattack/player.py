"""Classes representing each player in the game."""

import random
import time

import pygame
from pygame.color import Color
from vector import Vector

from .world import Actor, COLLISION_GROUP_PLAYER, COLLISION_GROUP_POWERUP
from .tools import Brush
from .text import Label
from .animation import Loadable, sprite, anim, mirror_anim

from .signals import Signal

class PlayerCharacter(Actor):
    """The player's avatar.

    The PlayerCharacter is not directly controlled, but moves
    automatically to keep in track with the player's brush cursor.
    
    (Eventually the game may swap from brush control to player control
    automatically if the player holds down a key. This would allow more
    responsive control of the character which will be important for PvP.)

    """

    SOUNDS = {
        'hit': 'hit.wav',
        'swish': 'swish.wav',
    }

    DEFAULT_SPRITE = 'standing-right'
    DEFAULT_DIR = 'right'

    COLLISION_GROUP = COLLISION_GROUP_PLAYER
    COLLISION_MASK = COLLISION_GROUP_PLAYER | COLLISION_GROUP_POWERUP
    RADIUS = 30

    brush_offsets = {
        'left': (-37, 12),
        'right': (47, 12),
        'centre': (0, 14),
    }

    MAX_SPEED = 500

    ATTACK_DURATION = 0.3 #seconds, how long the animation is shown
    ATTACK_INTERVAL = 0.2 #seconds, how long after the animation finishes the player can attack once more

    HIT_TIME = 1.5 #seconds, how long you are stunned when hit
    HIT_TIME_OWN_HALF = 1 #seconds, how long you are stunned when hit

    MAX_STUN_TIME = 5 # seconds, how long your stun can build up
    MAX_STUN_TIME_OWN_HALF = 2 # seconds, how long your stun can build up in your own half

    def __init__(self, pos, player):
        self.player = player
        self.sprite_colour = None
        super(PlayerCharacter, self).__init__(pos)
        self.brush_pos = None  # The position the character should try to get to
        self.painting = 0
        self.dir = 'right'
        self.attacking = 0
        self.stun = 0
        self.sprite = None
        self.play(self.DEFAULT_SPRITE)

    def play(self, animation):
        """Play an animation named in self.sprites"""
        colour = self.player.palette.get_selected()
        if animation == self.sprite and self.sprite_colour == colour:
            return
        self.sprite = animation
        self.sprite_colour = colour
        self.sprite_instance = self.sprites[self.sprite].create_instance(colour=colour)

    def track_tool(self, tool):
        """Specify a tool for the PC to track"""
        self.tool = tool

    def stop_tracking(self):
        self.tool = None

    def update(self, dt):
        from .world import screen_to_floor, FORESHORTENING
        if self.tool is None:
            return

        if self.attacking > 0:
            self.attacking -= dt
        if self.stun > 0:
            self.stun -= dt

        if not self.can_act():
            if self.stun > 0:
                v = self.target_pos - self.pos
                if v.length2 > 0.00001:
                    self.pos += v.scaled_to(min(v.length, 8))
                self.play('hit')
            elif self.attacking > self.ATTACK_INTERVAL:
                self.play('standing-attack')
            return
    
        bx, by = self.brush_offsets[self.dir]
        t = self.tool.pos.floor_pos() - Vector([bx, by * FORESHORTENING])

        v = (t - self.pos)
        
        # orient character
        if self.dir == 'centre':
            if v.x <= -20:
                self.dir = 'left'
            elif v.x >= 30:
                self.dir = 'right'
        elif self.dir == 'right':
            if v.x < -30:
                self.dir = 'centre'
        elif self.dir == 'left':
            if v.x > 20:
                self.dir = 'centre'

        if -37 <= v.x <= 47:
            v = self.alter_v_for_collision(Vector([0, max(-self.MAX_SPEED * dt, min(self.MAX_SPEED * dt, v.y))]))
            self.pos += v
        else:
            if v.length > self.MAX_SPEED * dt:
                v = v.scaled_to(self.MAX_SPEED * dt)
            v = self.alter_v_for_collision(v)
            self.pos += v

        if self.painting > 0:
            self.painting -= dt

        if self.stun > 0:
            sprite = 'hit'
        elif self.attacking > self.ATTACK_INTERVAL:
            sprite = 'standing-attack'
        elif self.is_painting():
            sprite = 'painting-%s' % self.dir
        else:
            sprite = 'standing-%s' % self.dir

        self.play(sprite)

    def get_hit_region(self):
        tl = self.pos + Vector([0, -40])
        br = self.pos + Vector([0, 40])
        if self.ATTACK_VECTOR.x < 0:
            tl += self.ATTACK_VECTOR
        else:
            br += self.ATTACK_VECTOR
        return tl, br

    def attack(self):
        if self.attacking > 0 or self.stun > 0:
            return
        self.sounds['swish'].play()
        self.attacking = self.ATTACK_INTERVAL + self.ATTACK_DURATION
        region = self.get_hit_region()
        for a in self.world.actors_in_region(*region):
            if a is self:
                continue
            if isinstance(a, PlayerCharacter):
                self.world.on_pc_hit.fire(a, self.ATTACK_VECTOR)

    def hit(self, attack_vector):
        self.sounds['hit'].play()
        if self.stun <= 0:
            self.target_pos = self.pos
            self.stunned_in_own_half = self.in_own_half()
        self.target_pos += attack_vector * 0.6
        if self.stunned_in_own_half:
            self.stun = min(self.stun + self.HIT_TIME_OWN_HALF, self.MAX_STUN_TIME_OWN_HALF)
        else:
            self.stun = min(self.stun + self.HIT_TIME, self.MAX_STUN_TIME)
        if self.tool:
            x, y = attack_vector
            self.tool.pos += (x // 20, 0)

    def can_act(self):
        """Are the conditions right for the player to paint or attack?"""
        return (
            self.attacking <= 0 and 
            self.stun <= 0
        )

    def paint(self):
        self.painting = 0.3

    def is_painting(self):
        return self.painting > 0

    def is_stunned(self):
        return self.stun > 0

    def alter_v_for_collision(self, v):
        if (self.pos + v).distance_to(self.other_player.pos) > 20:
            return v
        else:
            return v.rotated(v.angle_to(self.pos - self.other_player.pos) - 90)

    def handle_collision(self, ano):
        from .powerups import Powerup
        if isinstance(ano, Powerup):
            ano.handle_collision(self)
        elif isinstance(ano, Player):
            #TODO: resolve collision
            pass

    @classmethod
    def for_tool(cls, tool, player):
        """Create an instance of a PlayerCharacter based on the position of the corresponding tool.""" 
        from .world import screen_to_floor, FORESHORTENING
        bx, by = cls.brush_offsets[cls.DEFAULT_DIR]
        off = Vector([bx, by * FORESHORTENING])
        floor_pos = tool.pos.floor_pos() - off
        inst = cls(floor_pos, player)
        inst.track_tool(tool)
        return inst


class RedPlayerCharacter(PlayerCharacter):
    SPRITES = {
        'painting-left': anim('red-artist-painting-left'),
        'painting-centre': anim('red-artist-painting-centre'),
        'painting-right': anim('red-artist-painting-right'),
        'standing-left': anim('red-artist-standing-left'),
        'standing-centre': anim('red-artist-standing-centre'),
        'standing-right': anim('red-artist-standing-right'),
        'standing-attack': anim('red-artist-attack'),
        'hit': anim('red-artist-stun'),
        'run-right': anim('red-artist-run'),
        'run-left': mirror_anim('red-artist-run'),
    }

    ATTACK_VECTOR = Vector([165, 0])

    def in_own_half(self):
        return self.pos.x < 512


class BluePlayerCharacter(PlayerCharacter):
    SPRITES = {
        'painting-left': anim('blue-artist-painting-left'),
        'painting-centre': anim('blue-artist-painting-centre'),
        'painting-right': anim('blue-artist-painting-right'),
        'standing-left': anim('blue-artist-standing-left'),
        'standing-centre': anim('blue-artist-standing-centre'),
        'standing-right': anim('blue-artist-standing-right'),
        'standing-attack': anim('blue-artist-attack'),
        'hit': anim('blue-artist-stun'),
    }

    ATTACK_VECTOR = Vector([-165, 0])

    def in_own_half(self):
        return self.pos.x >= 512


class PlayerPalette(Loadable):
    """A player's collection of colours.
    
    One of these colours is selected for drawing at a time and this can be
    cycled through the colours. Features an MRU system so the least used colour
    is replaced on pickup, and players can use one key for toggling colours and
    cycling through them all.

    """
    MAX_COLOURS = 6
    SPRITES = {
        'selection_cursor': sprite('colour-selected'),
    }

    def __init__(self):
        self.colours = []
        self.selected = None
        self.change_time = 0

        self.on_change = Signal()

    def get_selected(self):
        if self.selected is None:
            return None
        return self.colours[self.selected]

    def next(self):
        self.selected = (self.selected + 1) % len(self.colours)
        self.change_time = 1
        self.on_change.fire(self)

    def update(self, dt):
        if self.change_time > 0:
            self.change_time -= dt
            if self.change_time <= 0:
                self.switch()

    def to_net(self):
        return (self.selected, [c.index for c in self.colours])

    def from_net(self, net, palette_map):
        selected, colours = net
        cs = []
        self.selected = selected
        for c in colours:
            cs.append(palette_map[c])
        self.colours = cs

    def switch(self):
        """Switch the order of the palette so that the currently selected colour is first.
        """
        if not self.selected:
            return

        c = self.get_selected()
        self.colours.remove(c)
        self.colours.insert(0, c)
        self.selected = 0

        self.on_change.fire(self)

    def add_colour(self, colour):
        """If the palette doesn't contain it, add the colour to the palette.
        
        Also select the new colour.

        """
        if colour in self.colours:
            return
        self.colours = [colour] + self.colours[:self.MAX_COLOURS - 1]
        self.selected = 0

        self.on_change.fire(self)

    def draw(self, screen):
        xoff, yoff = self.DISPLAY_POS
        for i, pos, c in zip(range(self.MAX_COLOURS), self.SWATCH_POSITIONS, self.colours): 
            if c is None:
                continue
            x, y = pos
            c.draw_swatch(screen, (x + xoff, y + yoff)) 
            if i == self.selected:
                self.sprites['selection_cursor'].draw(screen, (x + xoff, y + yoff))


class PlayerPaletteLeft(PlayerPalette):
    SWATCH_POSITIONS = [(52, 5), (82, 5), (111, 15), (121, 43), (97, 62), (67, 67)]
    DISPLAY_POS = (8, 14)


class PlayerPaletteRight(PlayerPalette):
    SWATCH_POSITIONS = [(141 - x, y) for x, y in PlayerPaletteLeft.SWATCH_POSITIONS]
    DISPLAY_POS = (850, 14)


class Player(object):
    """A player of the game.

    This class ties together the concepts of PlayerPalette, PlayerCharacter,
    tools and so on as one identity.

    """
    def __init__(self, world, artwork, start_pos):
        self.palette = self.PALETTE_CLASS()
        self.world = world
        self.artwork = artwork
        self.tool = None

        tool = Brush(self, start_pos)
        self.pc = self.CHARACTER.for_tool(tool, self)
        self.set_tool(tool)

        self.create_labels()

        self.on_tool_move = Signal()
        self.on_palette_change = Signal()
        self.on_paint = Signal()
        self.on_attack = Signal()

        self.palette.on_change.connect(self.handle_palette_change)

    def handle_palette_change(self, palette):
        self.on_palette_change.fire(self, palette)

    def create_labels(self):
        """Create the labels for the player's score"""
        raise NotImplementedError()

    def set_other_player(self, other_player):
        self.pc.other_player = other_player.pc

    def set_tool(self, tool):
        if self.tool:
            tool.pos = self.tool.pos
        self.tool = tool
        self.pc.track_tool(tool)

    def draw(self, screen):
        self.palette.draw(screen)
        if self.tool:
            self.tool.draw(screen, self.COLOUR)

        complete, total = self.artwork.completeness()
        percent = u'%0.1f%% complete' % (complete * 100.0 / total)
        pixels = '%d correct / %d total' % (complete, total)
        self.percent_label.draw(screen, percent)
        self.pixels_label.draw(screen, pixels)

    def paint(self):
        if self.tool and self.pc.can_act():
            colour = self.palette.get_selected().index
            self.tool.paint(colour, sound=not self.pc.is_painting())
            self.pc.paint()
            self.palette.switch()
            self.on_paint.fire(self, self.tool, colour)

    def up(self):
        if self.tool and not self.pc.is_stunned():
            self.tool.move_up()
            self.on_tool_move.fire(self, self.tool.pos)

    def down(self):
        if self.tool and not self.pc.is_stunned():
            self.tool.move_down()
            self.on_tool_move.fire(self, self.tool.pos)

    def left(self):
        if self.tool and not self.pc.is_stunned():
            self.tool.move_left()
            self.on_tool_move.fire(self, self.tool.pos)

    def right(self):
        if self.tool and not self.pc.is_stunned():
            self.tool.move_right()
            self.on_tool_move.fire(self, self.tool.pos)
        
    def set_tool_position(self, pos):
        if self.tool:
            self.tool.pos = pos

    def attack(self):
        if self.pc.can_act():
            self.pc.attack()
            region = self.pc.get_hit_region()
            self.on_attack.fire(self.pc, region)

    def next_colour(self):
        self.palette.next()

    def update(self, dt):
        self.palette.update(dt)
        self.pc.update(dt)

    @classmethod
    def load(cls):
        cls.CHARACTER.load()
        cls.PALETTE_CLASS.load()


class RedPlayer(Player):
    """Subclass of Player to specify properties specific to the red player."""

    COLOUR = Color('#880000')
    PALETTE_CLASS = PlayerPaletteLeft
    CHARACTER = RedPlayerCharacter
    ID = 0

    def create_labels(self):
        self.percent_label = Label((15, 135))
        self.pixels_label = Label((15, 159))
        

class BluePlayer(Player):
    """Subclass of Player to specify properties specific to the blue player."""

    COLOUR = Color('#3333AA')
    PALETTE_CLASS = PlayerPaletteRight
    CHARACTER = BluePlayerCharacter
    ID = 1

    def create_labels(self):
        self.percent_label = Label((1009, 135), align=Label.ALIGN_RIGHT)
        self.pixels_label = Label((1009, 159), align=Label.ALIGN_RIGHT)
