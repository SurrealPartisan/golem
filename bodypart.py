#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 21:26:04 2023

@author: surrealpartisan
"""

import numpy as np
import item
from item import Attack
from utils import listwithowner

class BodyPartConnection():
    def __init__(self, parent, categories, vital, prefix, defensecoefficient=1):
        self.parent = parent
        self.categories = categories
        self.vital = vital
        self.child = None
        self.prefix = prefix
        self.defensecoefficient = defensecoefficient
    
    def connect(self, child):
        if np.any([category in child.categories for category in self.categories]):
            self.child = child
            child.parentalconnection = self
            return True
        else:
            return False

class BodyPart(item.Item):
    def __init__(self, owner, x, y, name, char, color):
        super().__init__(owner, x, y, name, char, color)
        self.bodypart = True
        self.categories = []
        self.parentalconnection = None
        self.childconnections = {}
        self.maxhp = np.inf
        self.damagetaken = 0
        self.capableofwielding = False
        self.material = "living flesh"
        self._defensecoefficient = 0.8
        self._wearwieldname = name

    def connect(self, connection_name, child):
        return self.childconnections[connection_name].connect(child)

    def vital(self):
        if 'torso' in self.categories:
            return True
        else:
            return self.parentalconnection.vital

    def speed(self):
        return 0

    def minespeed(self):
        return 0

    def sight(self):
        return 0

    def hp(self):
        return self.maxhp - self.damagetaken

    def destroyed(self):
        return self.damagetaken >= self.maxhp

    def attackslist(self):
        return []

    def defensecoefficient(self):
        if self.parentalconnection == None:
            return self._defensecoefficient
        else:
            return self.parentalconnection.defensecoefficient*self._defensecoefficient

    def wearwieldname(self):
        if self.parentalconnection == None:
            return self._wearwieldname
        else:
            return self.parentalconnection.prefix + self._wearwieldname



class HumanTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human torso', 'T', (250, 220, 196))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5)
            }
        self.maxhp = 100

class HumanArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human arm', 'i', (250, 220, 196))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 40
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'

    def speed(self):
        if not self.destroyed():
            if len([part for part in self.owner if 'arm' in part.categories and not part.destroyed()]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not self.destroyed():
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not self.destroyed():
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 10)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class HumanLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human leg', 'l', (250, 220, 196))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 40
        self._wearwieldname = 'foot'

    def speed(self):
        if not self.destroyed():
            if len([part for part in self.owner if 'leg' in part.categories and not part.destroyed()]) > 1:
                return 1
            else:
                return 0.5
        else:
            return 0

    def attackslist(self):
        if not self.destroyed():
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15)]
        else:
            return []

class HumanHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human head', 'ö', (250, 220, 196))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5)
            }
        self.maxhp = 40

    def attackslist(self):
        if not self.destroyed():
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 2, 1, 10)]
        else:
            return []

class HumanEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10

    def sight(self):
        if not self.destroyed():
            return 3
        else:
            return 0

class HumanBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 20
        
class HumanHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 20



class ZombieTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie torso', 'T', (191, 255, 128))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], False, ''),
            'heart': BodyPartConnection(self, ['heart'], False, '', defensecoefficient=0.5)
            }
        self.maxhp = 100
        self.material = "undead flesh"

class ZombieArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie arm', 'i', (191, 255, 128))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 40
        self.material = "undead flesh"
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'

    def speed(self):
        if not self.destroyed():
            if len([part for part in self.owner if 'arm' in part.categories and not part.destroyed()]) > 1:
                return 0.1
            else:
                return 0.05
        else:
            return 0

    def minespeed(self):
        if not self.destroyed():
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not self.destroyed():
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 10)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class ZombieLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie leg', 'l', (191, 255, 128))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 40
        self.material = "undead flesh"
        self._wearwieldname = 'foot'

    def attackslist(self):
        if not self.destroyed():
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15)]
        else:
            return []

    def speed(self):
        if not self.destroyed():
            if len([part for part in self.owner if 'leg' in part.categories and not part.destroyed()]) > 1:
                return 0.5
            else:
                return 0.25
        else:
            return 0

class ZombieHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie head', 'ö', (191, 255, 128))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], False, '', defensecoefficient=0.5)
            }
        self.maxhp = 40
        self.material = "undead flesh"

    def attackslist(self):
        if not self.destroyed():
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 2, 1, 10)]
        else:
            return []

class ZombieEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie eye', '*', (155, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10
        self.material = "undead flesh"

    def sight(self):
        if not self.destroyed():
            return 3
        else:
            return 0

class ZombieBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie brain', '*', (150, 178, 82))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 20
        self.material = "undead flesh"
        
class ZombieHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie heart', '*', (150, 178, 82))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 20
        self.material = "undead flesh"



class MolePersonTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person torso', 'T', (186, 100, 13))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5)
            }
        self.maxhp = 100

class MolePersonArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person arm', 'i', (186, 100, 13))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 40
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'

    def speed(self):
        if not self.destroyed():
            if len([part for part in self.owner if 'arm' in part.categories and not part.destroyed()]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not self.destroyed():
            if len(self.wielded) == 0:
                return 0.33
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not self.destroyed():
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 10)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class MolePersonLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person leg', 'l', (186, 100, 13))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 40
        self._wearwieldname = 'foot'

    def speed(self):
        if not self.destroyed():
            if len([part for part in self.owner if 'leg' in part.categories and not part.destroyed()]) > 1:
                return 1
            else:
                return 0.5
        else:
            return 0

    def attackslist(self):
        if not self.destroyed():
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15)]
        else:
            return []

class MolePersonHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person head', 'ö', (186, 100, 13))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5)
            }
        self.maxhp = 40

    def attackslist(self):
        if not self.destroyed():
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 1, 1, 20)]
        else:
            return []

class MolePersonEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10

    def sight(self):
        if not self.destroyed():
            return 1
        else:
            return 0

class MolePersonBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 20
        
class MolePersonHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 20