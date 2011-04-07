from pygame import transform
from .data import load_sprite, load_anim_def


def sprite(name):
    def load():
        return load_sprite(name + '.png')

    return load


def anim(name):
    def load():
        return Animation.from_file(name + '.txt')

    return load


def mirror_anim(name):
    # Not the most efficient way of doing it.
    def load():
        return Animation.from_file(name + '.txt').mirror()

    return load


class Loadable(object):
    """Base class of things that are made up of loadable sprites."""

    @classmethod
    def load(cls):
        if hasattr(cls, 'sprites'):
            return

        sprites = {}
        # TODO: load base classes' sprites and pre-populate the sprites dict

        for k, load in cls.SPRITES.iteritems():
            sprites[k] = load()

        cls.sprites = sprites


class AnimationInstance(object):
    """An instance of an animation."""
    def __init__(self, anim):
        self.anim = anim
        self.playing = False
        self.frame = 0
        self.frametime = 0
        self.finished = False

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

    def create_instance(self, started=True):
        inst = self.INSTANCE_CLASS(self)
        if started:
            inst.play()

    @classmethod
    def from_file(cls, filename):
        layers = load_anim_def(filename)
        l = layers[0]
        return cls.load_as_layer(*l)

    @classmethod
    def load_as_layer(cls, base, frames, offsets):
        if frames == 1:
            surface = load_sprite(base)
            return cls([(surface, offsets[0])])
        else:
            fs = []
            for f in range(frames):
                fname = '%s-%s.png' % (base, f + 1)
                surface = load_sprite(fname)
                offset = offsets[f % len(offsets)]
                fs.append((surface, offset))
            return cls(fs)
        

class LayeredAnimationInstance(AnimationInstance):
    def __init__(self, anim):
        self.anim = anim
        self.layers = [layer.create_instance() for layer in anim.layers]

    def on_layer_finish(self, layer):
        self.finished = True
        self._fire_on_finish_handlers()

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

    @classmethod
    def from_file(cls, filename):
        layers = load_anim_def(filename)
        ls = []
        for l in layers:
            ls.append(Animation.load_as_layer(*l))
        return cls(ls)
