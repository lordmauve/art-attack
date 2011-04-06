from .data import load_sprite


class Loadable(object):
    """Base class of things that are made up of loadable sprites."""

    @classmethod
    def load(cls):
        sprites = {}
        # TODO: load base classes' sprites and pre-populate the sprites dict

        for k, name in cls.SPRITES.iteritems():
            sprites[k] = load_sprite(name)

        cls.sprites = sprites

