"""Classes representing each player in the game."""

import time

import pygame
from pygame.color import Color
from vector import Vector

from .world import Actor, COLLISION_GROUP_PLAYER, COLLISION_GROUP_POWERUP
from .tools import Brush
from .text import Label
from .animation import Loadable, sprite, anim, mirror_anim


class PlayerCharacter(Actor):
    """The player's avatar.

    The PlayerCharacter is not directly controlled, but moves
    automatically to keep in track with the player's brush cursor.
    
    (Eventually the game may swap from brush control to player control
    automatically if the player holds down a key. This would allow more
    responsive control of the character which will be important for PvP.)

    """

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

    ATTACK_DURATION = 0.4 #seconds, how long an attack lasts
    ATTACK_INTERVAL = 0.3 #seconds, how long between attacks

    HIT_TIME = 0.5 #seconds, how long you are stunned when hit

    def __init__(self, pos, player):
        super(PlayerCharacter, self).__init__(pos)
        self.player = player
        self.brush_pos = None  # The position the character should try to get to
        self.sprite = self.DEFAULT_SPRITE
        self.painting = 0
        self.dir = 'right'
        self.attacking = 0
        self.hit = 0

    def track_brush(self, pos):
        """Update the position of the brush (in floor space)."""
        self.brush_pos = pos

    def update(self, dt):
        from .world import screen_to_floor, FORESHORTENING
        if self.brush_pos is None:
            return

        if self.attacking > 0:
            self.attacking -= dt
        if self.hit > 0:
            self.hit -= dt
    
        bx, by = self.brush_offsets[self.dir]
        t = self.brush_pos - Vector([bx, by * FORESHORTENING])

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
            if abs(v.y) > 1:
                self.painting = 0
        else:
            if v.length > self.MAX_SPEED * dt:
                v = v.scaled_to(self.MAX_SPEED * dt)
            v = self.alter_v_for_collision(v)
            self.pos += v
            self.painting = 0

        if self.painting > 0:
            self.painting -= dt

        if self.hit > 0:
            self.sprite = 'hit'
        elif self.attacking > self.ATTACK_INTERVAL:
            self.sprite = 'standing-attack'
        elif self.painting > 0:
            self.sprite = 'painting-%s' % self.dir
        else:
            self.sprite = 'standing-%s' % self.dir

    def get_hit_region(self):
        tl = self.pos + Vector([0, -40])
        br = self.pos + Vector([0, 40])
        if self.ATTACK_VECTOR.x < 0:
            tl += self.ATTACK_VECTOR
        else:
            br += self.ATTACK_VECTOR
        return tl, br

    def attack(self):
        if self.attacking > 0 or self.hit > 0:
            return
        self.attacking = self.ATTACK_INTERVAL + self.ATTACK_DURATION
        region = self.get_hit_region()
        for a in self.world.actors_in_region(*region):
            if a is self:
                continue
            if isinstance(a, PlayerCharacter):
                a.on_hit(self.ATTACK_VECTOR)

    def on_hit(self, attack_vector):
        self.hit = self.HIT_TIME
        self.pos += attack_vector
        if self.player.tool:
            x, y = attack_vector
            self.player.tool.pos += (x // 30, 0)
            self.track_brush(self.player.tool.pos.floor_pos())

    def paint(self):
        self.painting = 0.1

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
    def for_brush_pos(cls, brush_pos, player):
        """Create an instance of a PlayerCharacter based on the position of the corresponding tool.""" 
        from .world import screen_to_floor, FORESHORTENING
        bx, by = cls.brush_offsets[cls.DEFAULT_DIR]
        off = Vector([bx, by * FORESHORTENING])
        floor_pos = brush_pos.floor_pos() - off
        inst = cls(floor_pos, player)
        inst.track_brush(brush_pos.floor_pos())
        return inst


class RedPlayerCharacter(PlayerCharacter):
    SPRITES = {
        'painting-left': sprite('red-artist-painting-left', (-50, -160)),
        'painting-centre': sprite('red-artist-painting-centre', (-31, -150)),
        'painting-right': sprite('red-artist-painting-right', (-60, -126)),
        'standing-left': sprite('red-artist-standing-left', (-50, -165)),
        'standing-centre': sprite('red-artist-standing-centre', (-59, -157)),
        'standing-right': sprite('red-artist-standing-right', (-68, -116)),
        'standing-attack': sprite('red-artist-standing-attack', (-27, -100)),
        'hit': sprite('red-artist-hit', (-67, -123)),
        'run-right': anim('red-artist-run'),
        'run-left': mirror_anim('red-artist-run'),
    }

    ATTACK_VECTOR = Vector([150, 0])


class BluePlayerCharacter(PlayerCharacter):
    SPRITES = {
        'painting-left': sprite('blue-artist-painting-left', (-50, -160)),
        'painting-centre': sprite('blue-artist-painting-centre', (-31, -150)),
        'painting-right': sprite('blue-artist-painting-right', (-60, -126)),
        'standing-left': sprite('blue-artist-standing-left', (-50, -165)),
        'standing-centre': sprite('blue-artist-standing-centre', (-59, -157)),
        'standing-right': sprite('blue-artist-standing-right', (-68, -116)),
        'standing-attack': sprite('blue-artist-standing-attack', (-154, -100)),
        'hit': sprite('blue-artist-hit', (-57, -152)),
    }

    ATTACK_VECTOR = Vector([-150, 0])


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

    def get_selected(self):
        return self.colours[self.selected]

    def next(self):
        self.selected = (self.selected + 1) % len(self.colours)
        self.change_time = 1

    def update(self, dt):
        if self.change_time > 0:
            self.change_time -= dt
            if self.change_time <= 0:
                self.switch()

    def switch(self):
        """Switch the order of the palette so that the currently selected colour is first.
        """
        if not self.selected:
            return

        c = self.get_selected()
        self.colours.remove(c)
        self.colours.insert(0, c)
        self.selected = 0

    def add_colour(self, colour):
        """If the palette doesn't contain it, add the colour to the palette.
        
        Also select the new colour.

        """
        if colour in self.colours:
            return
        self.colours = [colour] + self.colours[:self.MAX_COLOURS - 1]
        self.selected = 0

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

        self.pc = self.CHARACTER.for_brush_pos(start_pos, self)

        self.tool = None
        self.set_tool(Brush(self, start_pos))

        self.create_labels()

    def create_labels(self):
        """Create the labels for the player's score"""
        raise NotImplementedError()

    def set_other_player(self, other_player):
        self.pc.other_player = other_player.pc

    def set_tool(self, tool):
        if self.tool:
            tool.pos = self.tool.pos
        self.tool = tool

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
        if self.tool:
            colour = self.palette.get_selected().index
            self.tool.paint(colour)
            self.pc.paint()
            self.palette.switch()

    def up(self):
        if self.tool:
            self.tool.move_up()
            self.pc.track_brush(self.tool.pos.floor_pos())

    def down(self):
        if self.tool:
            self.tool.move_down()
            self.pc.track_brush(self.tool.pos.floor_pos())

    def left(self):
        if self.tool:
            self.tool.move_left()
            self.pc.track_brush(self.tool.pos.floor_pos())

    def right(self):
        if self.tool:
            self.tool.move_right()
            self.pc.track_brush(self.tool.pos.floor_pos())

    def attack(self):
        self.pc.attack()

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

    def create_labels(self):
        self.percent_label = Label((15, 135))
        self.pixels_label = Label((15, 159))
        

class BluePlayer(Player):
    """Subclass of Player to specify properties specific to the blue player."""

    COLOUR = Color('#3333AA')
    PALETTE_CLASS = PlayerPaletteRight
    CHARACTER = BluePlayerCharacter

    def create_labels(self):
        self.percent_label = Label((1009, 135), align=Label.ALIGN_RIGHT)
        self.pixels_label = Label((1009, 159), align=Label.ALIGN_RIGHT)
