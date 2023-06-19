# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 20:48:19 2022

@author: SurrealPartisan
"""

from collections import namedtuple
import numpy as np

import utils

Attack = namedtuple('Attack', ['name', 'verb2nd', 'verb3rd', 'post2nd', 'post3rd', 'hitprobability', 'time', 'mindamage', 'maxdamage'])

class Item():
    def __init__(self, owner, x, y, name, char, color):
        self.owner = owner # A list, such as inventory or list of map items
        self.owner.append(self)
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.color = color
        self.consumable = False
        self.wieldable = False
        self.weapon = False
        self.bodypart = False

    def attackslist(self):
        return []

class Consumable(Item):
    def __init__(self, owner, x, y, name, char, color):
        super().__init__(owner, x, y, name, char, color)
        self.consumable = True
        self._hpgiven = 0
    
    def hpgiven(self):
        return self._hpgiven
    
    def consume(self, user):
        part = max([part for part in user.bodyparts if not part.destroyed()], key=lambda part : part.damagetaken)
        healed = user.heal(part, self.hpgiven())
        self.owner.remove(self)
        return part, healed

def create_medication(owner, x, y):
    drugs = Consumable(owner, x, y, 'dose of ' + utils.drugname(), '!', (0, 255, 255))
    drugs._hpgiven = np.random.randint(-2, 11)

class HumanIronDagger(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human-made iron dagger', '/', (200, 200, 200))
        self.wieldable = True
        self.weapon = True
    
    def attackslist(self):
        return[Attack('human-made iron dagger', 'stabbed', 'stabbed', '', '', 0.8, 1, 1, 20)]