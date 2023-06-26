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
        self.owner = owner  # A list, such as inventory or list of map items
        self.owner.append(self)
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.color = color
        self.maxhp = np.inf
        self.damagetaken = 0
        self.consumable = False
        self.wieldable = False
        self.weapon = False
        self.bodypart = False
        self.wearable = False
        self.isarmor = False

    def hp(self):
        return self.maxhp - self.damagetaken

    def destroyed(self):
        return self.damagetaken >= self.maxhp

    def attackslist(self):
        return []

    def minespeed(self):
        return 0

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

class LightPick(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'light pick', '\\', (186, 100, 13))
        self.wieldable = True
        self.weapon = True

    def attackslist(self):
        return[Attack('light pick', 'hit', 'hit', ' with a light pick', ' with a light pick', 0.6, 1.5, 1, 20)]

    def minespeed(self):
        return 0.25

class HeavyPick(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'heavy pick', '\\', (186, 100, 13))
        self.wieldable = True
        self.weapon = True

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack('heavy pick', 'hit', 'hit', ' with a heavy pick', ' with a heavy pick', 0.6, 1.5, 1, 30)]
        else:
            return[Attack('heavy pick', 'hit', 'hit', ' with a heavy pick', ' with a heavy pick', 0.4, 2, 1, 20)]

    def minespeed(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return 0.33
        else:
            return 0.2

class PieceOfArmor(Item):
    def __init__(self, owner, x, y, wearcategory, material):
        name = material + ' ' + wearcategory
        if material == 'leather': color = (186, 100, 13)
        if material == 'bronze': color = (150,116,68)
        if material == 'iron': color = (200, 200, 200)
        if material == 'steel': color = (210, 210, 210)
        super().__init__(owner, x, y, name, '[', color)
        self.wearcategory = wearcategory
        self.wearable = True
        self.isarmor = True
        if material == 'leather':
            self.maxhp = 100
            self.mindamage = 0
            self.maxdamage = 5
        if material == 'bronze':
            self.maxhp = 200
            self.mindamage = 0
            self.maxdamage = 10
        if material == 'iron':
            self.maxhp = 300
            self.mindamage = 0
            self.maxdamage = 15
        if material == 'steel':
            self.maxhp = 400
            self.mindamage = 0
            self.maxdamage = 20

def randomarmor(owner, x, y):
    return PieceOfArmor(owner, x, y, np.random.choice(['chest armor', 'gauntlet', 'leg armor', 'helmet']), np.random.choice(['leather', 'bronze', 'iron', 'steel']))