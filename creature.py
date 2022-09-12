# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 21:16:44 2022

@author: SurrealPartisan
"""

class Creature():
    def __init__(self, world):
        self.world = world
        self.char = '@'
        self.x = 0
        self.y = 0
        self.inventory = []
        self.hp = 100
    
    def move(self, x, y):
        if self.world[self.x+x, self.y+y] == 0:
            self.y += y
            self.x += x
            return True
        else:
            return False
    
    def heal(self, hpgiven):
        self.hp += hpgiven
