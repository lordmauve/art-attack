import random

from .animation import sprite
from .world import Actor, floor_to_screen, LEFT_ARTWORK, RIGHT_ARTWORK, COLLISION_GROUP_PLAYER, COLLISION_GROUP_POWERUP

from vector import Vector

GRAVITY = 1000


class Powerup(Actor):
    WEIGHT = 1 # The relative likelihood that this powerup will be dropped
    COLOUR = False # Needs random colour

    COLLISION_GROUPS = 0
    COLLISION_MASK = 0

    LIFETIME = 15
    BLINK_TIME = 3
    BLINK_RATE = 0.1

    def __init__(self, pos):
        super(Powerup, self).__init__(pos)
        self.pos = pos
        self.alt = 600
        self.valt = 0
        self.age = 0

    def update(self, dt):
        if self.alt > 0:
            self.valt -= GRAVITY * dt
            self.alt = max(0, self.alt + self.valt * dt)
        else:
            self.valt = 0
            self.alt = 0
            self.COLLISION_GROUPS = COLLISION_GROUP_POWERUP
            self.COLLISION_MASK = COLLISION_GROUP_PLAYER

            self.age += dt
            
            if self.age > self.LIFETIME:
                self.kill()

    def handle_collision(self, pc):
        self.pickup(pc.player)
        self.kill()

    def pickup(self, player):
        raise NotImplementedError("Subclasses must implement this method.")

    def draw(self, screen):
        if self.age > self.LIFETIME - self.BLINK_TIME:
            if int((self.age - (self.LIFETIME - self.BLINK_TIME)) / self.BLINK_RATE) % 2 == 0:
                return
        x, y = floor_to_screen(self.pos)
        self.sprite_instance.draw(screen, (x, y - self.alt))


class PowerupFactory(object):
    DROP_MEAN = 20  # mean time between drops in seconds
    DROP_SD = 5 # standard deviation in drop times

    MIN_DELAY = 5
    INITIAL_DELAY = 6 # give players something after 6s just to help them get started

    POWERUPS = []

    @staticmethod
    def register(powerup_class):
        PowerupFactory.POWERUPS.append(powerup_class)
    
    def __init__(self, world):
        self.world = world
        self.t = 0
        # FIXME: for balance, initial drop should be paint and should be a different colour to the one they already have
        self.nextdrop = [self.INITIAL_DELAY, self.INITIAL_DELAY]

    def schedule_drop(self, side):
        delay = max(self.MIN_DELAY, random.normalvariate(self.DROP_MEAN, self.DROP_SD))
        self.nextdrop[side] = self.t + delay

    def drop(self, side):
        tl, br = self.world.get_floor_space()
        tl += Vector([30, 15]) 
        br -= Vector([45, 15]) 
        w2 = (br.x - tl.x) / 2
        x = tl.x + random.random() * (w2) + side * w2
        y = tl.y + random.random() * (br.y - tl.y)
        powerup_class = random.choice(self.POWERUPS)

        pos = Vector([x, y])

        if powerup_class.COLOUR:
            colour = self.world.get_random_colour()
            self.world.spawn_powerup(powerup_class(pos, colour))
        else:
            self.world.spawn_powerup(powerup_class(pos))
        self.schedule_drop(side)

    def update(self, dt):
        self.t += dt
        for side, drop_time in enumerate(self.nextdrop):
            if self.t > drop_time: 
                self.drop(side)

    @classmethod
    def load_all(cls):
        for powerup in cls.POWERUPS:
            powerup.load()
        

class PaintCan(Powerup):
    COLOUR = True

    SOUNDS = {
        'powerup': 'powerup.wav',
    }

    def __init__(self, pos, colour):
        super(PaintCan, self).__init__(pos)
        self.colour = colour
        self.sprite_instance = self.colour.paint_can

    def play(self, animation):
        # Doesn't use sprite system yet
        pass
    
    def pickup(self, player):
        self.sounds['powerup'].play()
        player.palette.add_colour(self.colour)

    def to_net(self):
        return (self.pos, self.colour.index)

    @classmethod
    def from_net(cls, net, palette_map):
        pos, index = net
        return cls(pos, palette_map[index])



PowerupFactory.register(PaintCan)
