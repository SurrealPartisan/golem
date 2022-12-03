# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 21:16:44 2022

@author: SurrealPartisan
"""
import numpy as np

class Creature():
    def __init__(self, world):
        self.world = world
        self.char = '@'
        self.x = 0
        self.y = 0
        self.inventory = []
        self.hp = 100
        self.log = []
        self.sight = 7
        self.seen = np.zeros((len(world), len(world[0])))
        self.speed = 1
        self.nextaction = ['wait', 1]
        
    def steptime(self):
        return 1/self.speed
    
    def move(self, x, y):
        if self.world[self.x+x, self.y+y] == 0:
            self.y += y
            self.x += x
            return True
        else:
            return False
    
    def heal(self, hpgiven):
        self.hp += hpgiven
        
    def ai(self):
        # Return something to put in self.nextaction. It should be a list,
        # starting with action string, followed by parameters, last of which is
        # the time needed.
        return ['wait', 1]
    
    def resolveaction(self):
        if self.nextaction[0] == 'move':
            self.move(self.nextaction[1], self.nextaction[2])
    
    def update(self, time):
        if time < self.nextaction[-1]:
            self.nextaction[-1] -= time
        else:
            timeleft = time - self.nextaction[-1]
            self.resolveaction()
            self.nextaction = self.ai()
            self.update(timeleft)


class Blind_zombie(Creature):
    def __init__(self, world, x, y):
        super().__init__(world)
        self.char = 'z'
        self.x = x
        self.y = y
        self.sight = 0
        self.speed = 0.5
        
    def ai(self):
        x = 0
        y = 0
        while (x,y) == (0,0) or self.world[self.x+x, self.y+y] != 0:
            x = np.random.choice([-1,0,1])
            y = np.random.choice([-1,0,1])
        time = np.sqrt(x**2 + y**2) * self.steptime()
        return(['move', x, y, time])