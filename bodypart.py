#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 21:26:04 2023

@author: surrealpartisan
"""

import numpy as np
import item
from item import Attack
from utils import listwithowner, mapwidth, mapheight, numlevels

class BodyPartConnection():
    def __init__(self, parent, categories, vital, prefix, defensecoefficient=1, armorapplies=False):
        self.parent = parent
        self.categories = categories
        self.vital = vital
        self.child = None
        self.prefix = prefix
        self.defensecoefficient = defensecoefficient
        self.armorapplies = armorapplies
    
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
        self.capableofwielding = False
        self.worn = {}  # Each key is a category of item, e.g. helmet or backpack. Each value is a listwithowner, with the bodypart as the owner. The lists themselves should contain at most one item per list.
        self.material = "living flesh"
        self._defensecoefficient = 0.8
        self._wearwieldname = name
        self.bleedclocks = []

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

    def armor(self):
        armorlist = [wearlist[0] for wearlist in self.worn.values() if len(wearlist) > 0 and wearlist[0].isarmor and not wearlist[0].destroyed()]
        if len(armorlist) > 0:
            return armorlist[0]
        elif self.parentalconnection != None and self.parentalconnection.armorapplies:
            return self.parentalconnection.parent.armor()
        else:
            return None

    def bleed(self, time):
        newbleedclocklist = []
        dmgtotal = 0
        for bleedclock in self.bleedclocks:
            dmgleft = bleedclock[0]
            timepassed = bleedclock[1] + time
            dmg = min(int(timepassed), dmgleft, self.maxhp - self.damagetaken)
            self.damagetaken += dmg
            dmgtotal += dmg
            if dmgleft - dmg > 0:
                newbleedclocklist.append((dmgleft - dmg, timepassed % 1))
        self.bleedclocks = newbleedclocklist
        return dmgtotal


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
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 50
        self.worn = {'chest armor': listwithowner([], self), 'backpack': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 45000
        self.carryingcapacity = 20000

class HumanArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human arm', 'i', (250, 220, 196))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 20
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self)}
        self.weight = 5000

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 10, [], [])]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class HumanLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human leg', 'l', (250, 220, 196))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 20
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 17000
        self.carryingcapacity = 20000

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15, [], [])]
        else:
            return []

class HumanHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human head', 'ö', (250, 220, 196))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 20
        self.worn = {'helmet': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000

    def attackslist(self):
        if not self.destroyed():
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 2, 1, 10, [], [('bleed', 0.1)])]
        else:
            return []

class HumanEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 8

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
        self.maxhp = 10
        self.weight = 1300
        self.log = []
        self.seen = []
        for i in range(numlevels):
            self.seen.append(np.zeros((mapwidth, mapheight)))
        self.creaturesseen = []

class HumanHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 300



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
            'heart': BodyPartConnection(self, ['heart'], False, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 50
        self.material = "undead flesh"
        self.worn = {'chest armor': listwithowner([], self), 'backpack': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 40000
        self.carryingcapacity = 30000

class ZombieArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie arm', 'i', (191, 255, 128))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 20
        self.material = "undead flesh"
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self)}
        self.weight = 4000

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 10, [], [])]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class ZombieLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie leg', 'l', (191, 255, 128))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 20
        self.material = "undead flesh"
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 30000

    def attackslist(self):
        if not self.destroyed():
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15, [], [])]
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
            'brain': BodyPartConnection(self, ['brain'], False, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 20
        self.material = "undead flesh"
        self.worn = {'helmet': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000

    def attackslist(self):
        if not self.destroyed():
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 2, 1, 10, [], [('bleed', 0.1)])]
        else:
            return []

class ZombieEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie eye', '*', (155, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10
        self.material = "undead flesh"
        self.weight = 7

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
        self.maxhp = 10
        self.material = "undead flesh"
        self.weight = 1000
        self.log = []
        self.seen = []
        for i in range(numlevels):
            self.seen.append(np.zeros((mapwidth, mapheight)))
        self.creaturesseen = []

class ZombieHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie heart', '*', (150, 178, 82))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 10
        self.material = "undead flesh"
        self.weight = 250



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
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 50
        self.worn = {'chest armor': listwithowner([], self), 'backpack': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 45000
        self.carryingcapacity = 20000

class MolePersonArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person arm', 'i', (186, 100, 13))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 20
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self)}
        self.weight = 6000

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 10, [], [])]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class MolePersonLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person leg', 'l', (186, 100, 13))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 20
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 15000

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15, [], [])]
        else:
            return []

class MolePersonHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person head', 'ö', (186, 100, 13))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 20
        self.worn = {'helmet': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000

    def attackslist(self):
        if not self.destroyed():
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 1, 1, 20, [], [('bleed', 0.1)])]
        else:
            return []

class MolePersonEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 5

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
        self.maxhp = 10
        self.weight = 1300
        self.log = []
        self.seen = []
        for i in range(numlevels):
            self.seen.append(np.zeros((mapwidth, mapheight)))
        self.creaturesseen = []

class MolePersonHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 300



class OctopusHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus head', 'ö', (255, 0, 255))
        self.categories = ['torso']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.8, armorapplies=True),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.8, armorapplies=True),
            'front left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front left '),
            'center-front left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-front left '),
            'center-back left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-back left '),
            'back left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back left '),
            'front right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front right '),
            'center-front right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-front right '),
            'center-back right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-back right '),
            'back right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back right ')
            }
        self.maxhp = 80
        self.worn = {'helmet': listwithowner([], self), 'backpack': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 40000
        self.carryingcapacity = 20000

    def attackslist(self):
        if not self.destroyed():
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 1, 1, 20, [], [('bleed', 0.1)])]
        else:
            return []

class OctopusTentacle(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus tentacle', '~', (255, 0, 255))
        self.categories = ['arm', 'leg', 'tentacle']
        self.childconnections = {}
        self.maxhp = 10
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'tentacle'
        self.worn = {'tentacle armor': listwithowner([], self)}
        self.weight = 10000
        self.carryingcapacity = 10000

    def speed(self):
        if not self.destroyed():
            if 'leg' in self.parentalconnection.categories:
                return 0.1*len([part for part in self.owner if 'leg' in part.categories and not part.destroyed()])
            elif 'arm' in self.parentalconnection.categories:
                return 0.1*len([part for part in self.owner if 'arm' in part.categories and not part.destroyed()])
            else:
                return 0.1*len([part for part in self.owner if 'tentacle' in part.categories and not part.destroyed()])
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
                timetaken = 2 / len([part for part in self.owner if 'tentacle' in part.categories and not part.destroyed()])
                return [Attack(self.parentalconnection.prefix + 'tentacle', 'constricted', 'constricted', '', '', 0.8, timetaken, 1, 10, [], [])]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class OctopusEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 10

    def sight(self):
        if not self.destroyed():
            return 3
        else:
            return 0

class OctopusBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 2000
        self.log = []
        self.seen = []
        for i in range(numlevels):
            self.seen.append(np.zeros((mapwidth, mapheight)))
        self.creaturesseen = []

class OctopusHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 500



class GoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin torso', 'T', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 100
        self.worn = {'chest armor': listwithowner([], self), 'backpack': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 35000
        self.carryingcapacity = 20000

class GoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin arm', 'i', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 30
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self)}
        self.weight = 5000

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 30, [], [('knockback', 0.2)]), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', '', '', 0.8, 1, 1, 30, [], [('bleed', 0.2)])]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class GoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin leg', 'l', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 30
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 13000
        self.carryingcapacity = 15000

    def speed(self):
        if not self.destroyed():
            if len([part for part in self.owner if 'leg' in part.categories and not part.destroyed()]) > 1:
                return 1.5
            else:
                return 0.75
        else:
            return 0

    def attackslist(self):
        if not self.destroyed():
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 40, [], [])]
        else:
            return []

class GoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin head', 'ö', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 30
        self.worn = {'helmet': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000

    def attackslist(self):
        if not self.destroyed():
            return [Attack('bite', 'bit', 'bit', '', '', 0.6, 1, 1, 40, [], [('bleed', 0.1)])]
        else:
            return []

class GoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 5

    def sight(self):
        if not self.destroyed():
            return 3
        else:
            return 0

class GoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 1000
        self.log = []
        self.seen = []
        for i in range(numlevels):
            self.seen.append(np.zeros((mapwidth, mapheight)))
        self.creaturesseen = []

class GoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 250