#!/usr/bin/python

"""Animation tool for working with Inkscape.

Uses Inkscape to export an object, then cuts it into frames and displays the
animation with Pygame, rebuilding the animation when the SVG is saved.

"""

import os
import pygame
from pygame.locals import *

import subprocess 


class Animation(object):
    def __init__(self, svgfile, object_id, num_frames, frame_time=0.03):
        self.svgfile = svgfile
        self.object_id = object_id
        self.num_frames = num_frames
        self.frame = 0

    def build(self):
        tmp = os.tempnam()
        proc = subprocess.Popen(['inkscape', '-e', tmp, '-i', self.object_id, self.svgfile])
        proc.wait()
        surf = pygame.image.load(tmp)
        self.frame_height = surf.get_height()
        self.frame_width = surf.get_width() // self.num_frames
        self.surface = surf

    def show(self):
        self.build()
        screen = pygame.display.set_mode((self.frame_width, self.frame_height))
        self.surface = self.surface.convert_alpha()
        return screen

    def draw(self, screen):
        area = Rect(self.frame * self.frame_width, 0, self.frame_width, self.frame_height)
        screen.blit(self.surface, (0, 0), area)
        self.frame = (self.frame + 1) % self.num_frames



class AnimationApp(object):
    def __init__(self, animation, framerate=10):
        pygame.init()
        self.animation = animation
        self.background = Color('black')
        self.framerate = framerate
        self.screen = self.animation.show()

    def run(self):
        self.keeprunning = True
        clock = pygame.time.Clock()
        while self.keeprunning:
            dt = clock.tick(self.framerate)
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.keeprunning = False

            self.screen.fill(self.background)
            self.animation.draw(self.screen)
            pygame.display.flip()


if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-i', '--object-id', help='ID of the object that defines the boundaries of the animation')
    parser.add_option('-f', '--frames', help='Number of frames in the animation', type='int')
    parser.add_option('-r', '--framerate', help='Frames per second to show the animation', type='int', default=10)

    options, args = parser.parse_args()

    if not args:
        parser.error("You must specify an SVG file to open.")
    else:
        svgfile = args[0]

    if not options.object_id:
        parser.error("You must specify an object ID within the SVG file (-i).")

    if not options.frames:
        parser.error("You must specify the number of frames in the animation (-f).")
        
    animation = Animation(svgfile, options.object_id, options.frames)
    app = AnimationApp(animation, options.framerate)
    app.run()
