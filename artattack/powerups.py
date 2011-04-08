import random

from .animation import sprite
from .world import Actor, floor_to_screen, LEFT_ARTWORK, RIGHT_ARTWORK, COLLISION_GROUP_PLAYER

from vector import Vector

GRAVITY = 1000


class Powerup(Actor):
    WEIGHT = 1 # The relative likelihood that this powerup will be dropped
    COLOUR = False # Needs random colour

    COLLISION_GROUP = 0

    def __init__(self, pos):
        super(Powerup, self).__init__(pos)
        self.pos = pos
        self.alt = 600
        self.valt = 0

    def update(self, dt):
        if self.alt > 0:
            self.valt -= GRAVITY * dt
            self.alt = max(0, self.alt + self.valt * dt)
        else:
            self.valt = 0
            self.alt = 0
            self.COLLISION_GROUP = COLLISION_GROUP_PLAYER

    def handle_collision(self, pc):
        self.pickup(pc.player)
        self.kill()

    def pickup(self, player):
        raise NotImplementedError("Subclasses must implement this method.")

    def draw(self, screen):
        x, y = floor_to_screen(self.pos)
        self.get_sprite().draw(screen, (x, y - self.alt))


class PowerupFactory(object):
    DROP_MEAN = 20  # mean time between drops in seconds
    DROP_SD = 5 # standard deviation in drop times

    MIN_DELAY = 5
    INITIAL_DELAY = 10 # give players something after 10s just to help them get started

    POWERUPS = []

    @staticmethod
    def register(powerup_class):
        PowerupFactory.POWERUPS.append(powerup_class)
    
    def __init__(self, world):
        self.world = world
        self.t = 0
        self.nextdrop = [self.INITIAL_DELAY, self.INITIAL_DELAY]

    def schedule_drop(self, side):
        delay = max(self.MIN_DELAY, random.normalvariate(self.DROP_MEAN, self.DROP_SD))
        self.nextdrop[side] = self.t + delay

    def drop(self, side):
        # FIXME: drop onto the correct side
        tl, br = self.world.get_floor_space()
        x = tl.x + random.random() * (br.x - tl.x)
        y = tl.y + random.random() * (br.y - tl.y)
        powerup_class = random.choice(self.POWERUPS)

        pos = Vector([x, y])

        if powerup_class.COLOUR:
            colour = self.world.get_random_colour()
            self.world.spawn(powerup_class(pos, colour))
        else:
            self.world.spawn(powerup_class(pos))
        self.schedule_drop(side)

    def update(self, dt):
        self.t += dt
        for side, drop_time in enumerate(self.nextdrop):
            if self.t > drop_time: 
                self.drop(side)
        

class PaintCan(Powerup):
    COLOUR = True

    def __init__(self, pos, colour):
        super(PaintCan, self).__init__(pos)
        self.colour = colour

    def get_sprite(self):
        return self.colour.paint_can

    def pickup(self, player):
        player.palette.add_colour(self.colour)


PowerupFactory.register(PaintCan)
