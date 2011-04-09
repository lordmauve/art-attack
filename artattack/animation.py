from pygame import transform
from pygame.locals import *

from .data import load_sprite, load_anim_def, load_sound


def sprite(name, off=(0, 0)):
    def load():
        return Sprite(load_sprite(name + '.png'), off)

    return load


def anim(name):
    def load():
        return LayeredAnimation.from_file(name + '.txt')

    return load


def mirror_anim(name):
    # Not the most efficient way of doing it.
    def load():
        return LayeredAnimation.from_file(name + '.txt').mirror()

    return load


class Loadable(object):
    """Base class of things that are made up of loadable sprites."""

    SPRITES = {}
    SOUNDS = {}

    @classmethod
    def load(cls):
        if 'sprites' not in cls.__dict__:
            sprites = {}
            # TODO: load base classes' sprites and pre-populate the sprites dict

            for k, load in cls.SPRITES.iteritems():
                sprites[k] = load()

            cls.sprites = sprites

        if not hasattr(cls, 'sounds'):
            sounds = {}
            for k, filename in cls.SOUNDS.iteritems():
                sounds[k] = load_sound(filename)

            cls.sounds = sounds


class Sprite(object):
    """A surface plus an offset."""

    def __init__(self, surface, off=(0, 0)):
        self.surface = surface
        self.off = off

    def get_size(self):
        return self.surface.get_size()

    def create_instance(self, colour=None):
        return self

    def draw(self, screen, pos):
        x, y = pos
        xoff, yoff = self.off
        screen.blit(self.surface, (x + xoff, y + yoff))



class AnimationInstance(object):
    """An instance of an animation."""
    def __init__(self, anim, colour=None):
        self.anim = anim
        self.playing = False
        self.frame = 0
        self.frametime = 0
        self.finished = False
        self.colour = colour

        self.on_finish_handlers = []

    def add_on_finish_handler(self, callback):
        self.on_finish_handlers.append(callback)

    def _fire_on_finish_handlers(self):
        for h in self.on_finish_handlers:
            h(self)

    def play(self):
        self.playing = True

    def stop(self):
        self.playing = False

    def set_frame(self, frame):
        self.frame = frame % len(self.anim.frames)
        
    def get_frame(self):
        if self.colour:
            return self.anim.colourised_frames[self.colour][self.frame]
        return self.anim.frames[self.frame]

    def update(self, dt):
        if not self.playing:
            return
        self.frametime += dt
        self.frame += int(self.frametime / self.anim.frametime)
        self.frametime = self.frametime % self.anim.frametime

        if self.anim.looping:
            self.frame = self.frame % len(self.anim.frames)
        else:
            if self.frame >= len(self.anim.frames):
                self.frame = -1
                self.finished = True
                self._fire_on_finish_handlers()

    def draw(self, screen, pos):
        surface, off = self.get_frame()
        if off is None:
            return

        x, y = pos
        xoff, yoff = off
        screen.blit(surface, (x + xoff, y + yoff))



class Animation(object):
    """A 2D animation.
    
    Each frame is expected to be a tuple (Surface, (offset_x, offset_y)).

    Animations can be configured to loop. 
    """
    INSTANCE_CLASS = AnimationInstance

    def __init__(self, frames, framerate=12, looping=True):
        self.frames = frames
        self.colourised_frames = {}
        self.frametime = 1.0 / float(framerate)
        self.looping = looping

    def mirror(self):
        """Generate a copy of the animation mirrored left-right."""
        flipped_frames = []
        for surface, offset in self.frames:
            flipped = transform.flip(surface, True, False)
            offx, offy = offset
            offx = flipped.get_width() - offx
            flipped_frames.append((flipped, (offx, offy)))
        return Animation(flipped_frames, 1.0 / self.frametime, self.looping)

    def colourise(self, colour):
        fs = []
        for surface, offset in self.frames:
            col = surface.copy()
            col.fill(colour.colour, None, BLEND_RGB_MULT)
            fs.append((col, offset))
        self.colourised_frames[colour] = fs

    def create_instance(self, colour=None, started=True):
        if colour is not None:
            self.colourise(colour)
        inst = self.INSTANCE_CLASS(self, colour=colour)
        if started:
            inst.play()
        return inst

    @classmethod
    def from_file(cls, filename):
        layers = load_anim_def(filename)
        l = layers[0]
        return cls.load_as_layer(*l)

    @classmethod
    def load_as_layer(cls, base, frames, offsets, is_colour_mask):
        if frames == 1:
            surface = load_sprite(base + '.png')
            inst = cls([(surface, offsets[0])])
        else:
            fs = []
            for f in range(frames):
                fname = '%s-%s.png' % (base, f + 1)
                surface = load_sprite(fname)
                offset = offsets[f % len(offsets)]
                fs.append((surface, offset))
            inst = cls(fs)
        inst.is_colour_mask = is_colour_mask
        return inst
        

class LayeredAnimationInstance(AnimationInstance):
    def __init__(self, anim, colour=None):
        self.anim = anim
        self.layers = []
        for layer in anim.layers:
            if layer.is_colour_mask:
                self.layers.append(layer.create_instance(colour=colour))
            else:
                self.layers.append(layer.create_instance())

    def on_layer_finish(self, layer):
        self.finished = True
        self._fire_on_finish_handlers()

    def draw(self, screen, pos):
        for l in self.layers:
            l.draw(screen, pos)

    def update(self, dt):
        if self.playing:
            for l in self.layers:
                l.update(dt)


class LayeredAnimation(Animation):
    """An animation that combines several different animations as layers.
    
    This allows the combined animation to be handled as it if were a single
    object, as well as allowing the layer stack to be defined in the animations
    definition file.
    """

    INSTANCE_CLASS = LayeredAnimationInstance
    def __init__(self, layers):
        self.layers = layers

    def mirror(self):
        ls = [l.mirror() for l in self.layers]
        return LayeredAnimation(ls)

    def colourise(self, colour):
        pass

    @classmethod
    def from_file(cls, filename):
        layers = load_anim_def(filename)
        ls = []
        for l in layers:
            ls.append(Animation.load_as_layer(*l))
        return cls(ls)
