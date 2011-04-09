import pygame
from pygame.locals import *

MOVE_RATE = 0.035
REPEAT_RATES = {
    'attack': 0.12,
    'paint': 0.105,
    'left': MOVE_RATE,
    'right': MOVE_RATE,
    'up': MOVE_RATE,
    'down': MOVE_RATE,
    'next_colour': None,
}

REPEAT_DELAY = 0.1

class KeyController(object):
    def __init__(self, player, keybindings):
        self.player = player
        self.keybindings = keybindings
    
        self.keymap = {}
        self.t = 0
        self.action_times = {}

        for k in self.keybindings:
            key = self.keybindings.get(k)
            self.keymap[key] = k

    def do(self, action, keydown):
        """Call the action on the player if the repeat time allows it.
        
        """
        rate = REPEAT_RATES[action]
        if rate is None:
            if not keydown:
                return
            getattr(self.player, action)()
            return
        else:
            t = self.action_times.get(action, 0)
            if self.t > t or keydown:
                next_t = self.t + rate
                if keydown:
                    next_t += REPEAT_DELAY
                self.action_times[action] = next_t
                getattr(self.player, action)()

    def on_key_down(self, event):
        if event.key in self.keymap:
            self.do(self.keymap[event.key], keydown=True)

    def update(self, dt):
        self.t += dt
        keys_pressed = pygame.key.get_pressed()
        for action, key in self.keybindings.items():
            if keys_pressed[key]:
                self.do(action, keydown=False)
            
