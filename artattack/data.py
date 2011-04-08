'''Simple data loader module.

Loads data files from the "data" directory shipped with a game.
'''

import sys
import os
import re


data_py = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.normpath(os.path.join(data_py, '..', 'data'))


def filepath(filename, subdir=None):
    '''Determine the path to a file in the data directory.
    '''
    if subdir:
        return os.path.join(data_dir, subdir, filename)
    else:
        return os.path.join(data_dir, filename)


def screenshot_path(filename):
    '''Determine the path to a file in the data directory.
    '''
    return os.path.join(data_dir, '..', 'screenshots', filename)


def load(filename, mode='rb'):
    '''Open a file in the data directory.

    "mode" is passed as the second arg to open().
    '''
    return open(os.path.join(data_dir, filename), mode)


anim_comment_re = re.compile(r'#.*$')
anim_line_re = re.compile(r'^(?P<key>base|frames|colour|offsets):\s*(?P<value>.*)$')

def load_anim_def(filename):
    '''Open an animation definition file and parse the contents.
    '''
    f = open(os.path.join(data_dir, 'anims', filename), 'r')

    layers = []
    base = None
    frames = None
    offsets = []
    colour = False
    for line, l in enumerate(f):
        line += 1
        l = anim_comment_re.sub('', l).rstrip()
        if not l:
            continue

        mo = anim_line_re.match(l)
        if not mo:
            print >>sys.stderr, "Warning: failed to parse animation (%s, line %d)" % (filename, line)
            continue

        key = mo.group('key')
        value = mo.group('value')

        if key == 'base':
            if base:
                if not frames:
                    print >>sys.stderr, "Warning: animation layer %s missing frames (%s, line %d)" % (base, filename, line)
                elif not offsets:
                    print >>sys.stderr, "Warning: animation layer %s missing offsets (%s, line %d)" % (base, filename, line)
                else: 
                    layers.append((base, frames, offsets, colour))

            base = value
            frames = None
            offsets = []
            colour = False
        elif key == 'frames':
            frames = int(value)
        elif key == 'colour':
            colour = value.lower() == 'true'
        elif key == 'offsets':
            coords = value.split(' ')
            offsets = []
            for c in coords:
                if c == '-':
                    offsets.append(None)
                else:
                    x, y = c.split(',')
                    offsets.append((int(x), int(y)))
    if base:
        if not frames:
            print >>sys.stderr, "Warning: animation layer %s missing frames (%s, line %d)" % (base, filename, line)
        elif not offsets:
            print >>sys.stderr, "Warning: animation layer %s missing offsets (%s, line %d)" % (base, filename, line)
        else: 
            layers.append((base, frames, offsets, colour))

    return layers





def load_sprite(fname):
    import pygame.image
    return pygame.image.load(filepath(fname, subdir='sprites')).convert_alpha()
