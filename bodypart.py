#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 21:26:04 2023

@author: surrealpartisan
"""

import numpy as np
import item
from item import Attack
from utils import listwithowner, loglist, mapwidth, mapheight, numlevels, difficulty

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
        if np.any([category in child.categories for category in self.categories]) and self.child == None:
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
        self.consumable = True
        self.edible = True
        self._defensecoefficient = 0.8
        self._attackpoisonresistance = 0
        self._wearwieldname = name
        self.bleedclocks = []
        self._resistances = {'sharp': 0, 'blunt': 0, 'rough': 0, 'fire': 0}
        self.detectiondistance = 0
        self.detectionprobability = 0
        self.carefulness = 0
        self.usable = True
        self.maxrunstamina = 0
        self.runstaminarecoveryspeed = 0
        self.bravery = 0
        self.scariness = 0
        self.endotoxicity = 0

    def connect(self, connection_name, child):
        return self.childconnections[connection_name].connect(child)

    def vital(self):
        if 'torso' in self.categories:
            return True
        else:
            return self.parentalconnection.vital

    def incapacitated(self):
        if hasattr(self.owner, 'owner') and self.owner.owner.faction != 'player':
            return self.damagetaken >= difficulty*self.maxhp
        else:
            return False

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

    def attackpoisonresistance(self):
        return self._attackpoisonresistance

    def resistance(self, damagetype):
        return self._resistances[damagetype]

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
        causers = []
        for bleedclock in self.bleedclocks:
            dmgleft = bleedclock[0]
            timepassed = bleedclock[1] + time
            causer = bleedclock[2]
            if not causer in causers:
                causers.append(causer)
            dmg = min(int(timepassed), dmgleft, self.maxhp - self.damagetaken)
            self.damagetaken += dmg
            dmgtotal += dmg
            if dmgleft - dmg > 0:
                newbleedclocklist.append((dmgleft - dmg, timepassed % 1, causer))
        self.bleedclocks = newbleedclocklist
        return dmgtotal, causers

    def consume(self, user, efficiency):
        if int(self.hp()*efficiency) > user.hunger:
            self.damagetaken += int(user.hunger/efficiency)
            user.hunger = 0
            user.log().append('You ate some of the ' + self.name + '.')
            user.log().append('You are satiated.')
        else:
            user.hunger -= int(self.hp()*efficiency)
            self.damagetaken = self.maxhp
            self.owner.remove(self)
            user.log().append('You ate the ' + self.name + '.')
            if user.hunger == 0:
                user.log().append('You are satiated.')

    def on_destruction(self, dead):
        if not dead:
            if self.capableofwielding:
                for it in self.wielded:
                    it.owner.remove(it)
                    self.owner.owner.world.items.append(it)
                    it.owner = self.owner.owner.world.items
                    it.x = self.owner.owner.x
                    it.y = self.owner.owner.y
                    self.owner.owner.log().append('You dropped your ' + it.name)
            for it in [l[0] for l in self.worn.values() if len(l) > 0]:
                it.owner.remove(it)
                self.owner.owner.world.items.append(it)
                it.owner = self.owner.owner.world.items
                it.x = self.owner.owner.x
                it.y = self.owner.owner.y
                self.owner.owner.log().append('You dropped your ' + it.name)



class HumanTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human torso', '*', (250, 220, 196))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 50
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 45000
        self.carryingcapacity = 20000
        self._info = 'A torso consisting of living flesh.'

class HumanArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human arm', '~', (250, 220, 196))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 20
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 5000
        self.carefulness = 0.5
        self._info = 'An arm consisting of living flesh.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 10, 'blunt', [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class HumanLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human leg', '~', (250, 220, 196))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 20
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 17000
        self.carryingcapacity = 20000
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self._info = 'A leg consisting of living flesh.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1
            else:
                return 0.5
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15, 'blunt', [], [], self)]
        else:
            return []

class HumanHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human head', '*', (250, 220, 196))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 20
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self._info = 'A head consisting of living flesh.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 2, 1, 10, 'sharp', [], [('bleed', 0.1)], self)]
        else:
            return []

class HumanEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 8
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
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
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh.'

class HumanHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 300
        self.bravery = 0.5
        self._info = 'A heart consisting of living flesh. Average bravery.'

class HumanLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 600
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh.'

class HumanKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'

class HumanStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
            }
        self._info = 'A stomach consisting of living flesh.'



class ZombieTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie torso', '*', (191, 255, 128))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], False, ''),
            'heart': BodyPartConnection(self, ['heart'], False, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 50
        self.material = "undead flesh"
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 40000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A torso consisting of undead flesh. Needs neither head nor heart. Has good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class ZombieArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie arm', '~', (191, 255, 128))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 20
        self.material = "undead flesh"
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.carefulness = 0.3
        self._info = 'An arm consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.1
            else:
                return 0.05
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 10, 'blunt', [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class ZombieLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie leg', '~', (191, 255, 128))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 20
        self.material = "undead flesh"
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.carefulness = 0.3
        self.maxrunstamina = 20
        self._info = 'A leg consisting of undead flesh. Quite slow and somewhat clumsy, but has good carrying capacity and high running stamina. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15, 'blunt', [], [], self)]
        else:
            return []

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.5
            else:
                return 0.25
        else:
            return 0

class ZombieHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie head', '*', (191, 255, 128))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], False, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 20
        self.material = "undead flesh"
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.scariness = 5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A head consisting of undead flesh. Can scare enemies for up to 5 s. Needs no brain. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 2, 1, 10, 'sharp', [], [('bleed', 0.1)], self)]
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
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
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
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A brain consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class ZombieHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie heart', '*', (150, 178, 82))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 10
        self.material = "undead flesh"
        self.weight = 250
        self.bravery = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A heart consisting of undead flesh. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class ZombieLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie lung', '*', (150, 178, 82))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 10
        self.material = 'undead flesh'
        self.weight = 500
        self.runstaminarecoveryspeed = 0.25
        self.breathepoisonresistance = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A lung consisting of undead flesh. Protects living bodyparts from poison gas quite well. Recovers running stamina slowly. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class ZombieKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie kidney', '*', (150, 178, 82))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 10
        self.material = 'undead flesh'
        self.weight = 100
        self._attackpoisonresistance = 1
        self.endotoxicity = -0.5
        self._resistances['sharp'] = -0.2
        self._info = 'A kidney consisting of undead flesh. Filters toxins at a slow speed. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks.'

class ZombieStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie stomach', '*', (150, 178, 82))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 10
        self.material = "undead flesh"
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'vegetables': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'living flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'undead flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.')
            }
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A stomach consisting of undead flesh. Inefficient at processing food. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'



class MolePersonTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person torso', '*', (186, 100, 13))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 50
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 45000
        self.carryingcapacity = 20000
        self._info = 'A torso consisting of living flesh.'

class MolePersonArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person arm', '~', (186, 100, 13))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 20
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 6000
        self.carefulness = 0.5
        self._info = 'An arm consisting of living flesh. Can be used for mining.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0.33
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', '', '', 0.8, 1, 1, 10, 'rough', [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class MolePersonLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person leg', '~', (186, 100, 13))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 20
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 15000
        self.carefulness = 0.5
        self.maxrunstamina = 5
        self._info = 'A leg consisting of living flesh. Somewhat weak at carrying. Low running stamina.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1
            else:
                return 0.5
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15, 'blunt', [], [], self)]
        else:
            return []

class MolePersonHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person head', '*', (186, 100, 13))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 20
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self._info = 'A head consisting of living flesh.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 1, 1, 20, 'sharp', [], [('bleed', 0.1)], self)]
        else:
            return []

class MolePersonEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of living flesh. Very short-sighted.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
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
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh.'

class MolePersonHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 300
        self.bravery = 0.25
        self._info = 'A heart consisting of living flesh. Easily scared.'

class MolePersonLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 600
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 1
        self._info = 'A lung consisting of living flesh. Recovers running stamina quickly.'

class MolePersonKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'

class MolePersonStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
            }
        self._info = 'A stomach consisting of living flesh.'



class GoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 50
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 25000
        self.carryingcapacity = 20000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self._info = 'A torso consisting of living flesh. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

class GoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 20
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self._info = 'An arm consisting of living flesh. Good at avoiding traps when crawling. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 10, 'blunt', [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', '', '', 0.8, 1, 1, 10, 'sharp', [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class GoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 20
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 10000
        self.carryingcapacity = 15000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self._info = 'A torso consisting of living flesh. Good at avoiding traps. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1
            else:
                return 0.5
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 15, 'blunt', [], [], self)]
        else:
            return []

class GoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 20
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 5000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.6, 1, 1, 15, 'sharp', [], [('bleed', 0.1)], self)]
        else:
            return []

class GoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of living flesh. Good at detecting traps.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

class GoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh.'

class GoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 250
        self.bravery = 0.5
        self._info = 'A heart consisting of living flesh. Average bravery.'

class GoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 600
        self.breathepoisonresistance = 0.2
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh. Some protection against poison gas.'

class GoblinKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'

class GoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 900
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
            }
        self._info = 'A stomach consisting of living flesh.'



class OctopusHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus head', '*', (255, 0, 255))
        self.categories = ['torso']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.8, armorapplies=True),
            'central heart': BodyPartConnection(self, ['heart'], True, 'central ', defensecoefficient=0.8, armorapplies=True),
            'left heart': BodyPartConnection(self, ['heart'], True, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right heart': BodyPartConnection(self, ['heart'], True, 'right ', defensecoefficient=0.8, armorapplies=True),
            'left gills': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right gills': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'left metanephridium': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right metanephridium': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True),
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
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 40000
        self.carryingcapacity = 20000
        self._info = 'A torso (despite being called head!) consisting of living flesh.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 1, 1, 20, 'sharp', [], [('bleed', 0.1)], self)]
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
        self.worn = {'tentacle armor': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 10000
        self.carryingcapacity = 10000
        self.carefulness = 0.4
        self.maxrunstamina = 2.5
        self._info = 'A tentacle consisting of living flesh. Works both as an arm and as a leg. Slow at moving, but faster if there are more of them. Also faster at attacking if there are more of them. Individually very low running stamina, collectively average. Slightly clumsy.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if 'leg' in self.parentalconnection.categories:
                return 0.1*len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())])
            elif 'arm' in self.parentalconnection.categories:
                return 0.1*len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())])
            else:
                return 0.1*len([part for part in self.owner if 'tentacle' in part.categories and not (part.destroyed() or part.incapacitated())])
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                timetaken = 2 / len([part for part in self.owner if 'tentacle' in part.categories and not (part.destroyed() or part.incapacitated())])
                return [Attack(self.parentalconnection.prefix + 'tentacle', 'constricted', 'constricted', '', '', 0.8, timetaken, 1, 10, 'blunt', [], [], self)]
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
        self.detectiondistance = 2.9
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh. Can detect traps from farther away than most.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
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
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh.'

class OctopusHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 500
        self.bravery = 0.25
        self._info = 'A heart consisting of living flesh. Individually easily scared (luckily the octopus has three of them).'

class OctopusGills(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus gills', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 500
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung-like organ consisting of living flesh.'

class OctopusMetanephridium(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus metanephridium', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 100
        self.endotoxicity = -1
        self._info = 'A kidney-like organ consisting of living flesh. Filters toxins at average speed.'

class OctopusStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (-1,),
            'living flesh': (1, 1, None),
            'undead flesh': (-1,)
            }
        self._info = 'A hypercarnivorous stomach consisting of living flesh.'



class DogTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog torso', '*', (170, 130, 70))
        self.categories = ['torso']
        self.childconnections = {
            'front left leg': BodyPartConnection(self, ['leg'], False, 'front left '),
            'front right leg': BodyPartConnection(self, ['leg'], False, 'front right '),
            'back left leg': BodyPartConnection(self, ['leg'], False, 'back left '),
            'back right leg': BodyPartConnection(self, ['leg'], False, 'back right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True),
            'tail': BodyPartConnection(self, ['tail'], False, '')
            }
        self.maxhp = 75
        self.worn = {'barding': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 20000
        self.carryingcapacity = 20000
        self._info = 'A torso consisting of living flesh.'

class DogLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog leg', '~', (170, 130, 70))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 25
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 3000
        self.carryingcapacity = 6000
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self._info = 'A leg consisting of living flesh. On its own very weak at carrying. Quite fast if there are at least four legs.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 3:
                return 1.5
            elif len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1
            else:
                return 0.5
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', '', '', 0.7, 1, 1, 5, 'sharp', [], [], self)]
        else:
            return []

class DogHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog head', '*', (170, 130, 70))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 25
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 3000
        self._info = 'A head consisting of living flesh.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.80, 1, 1, 25, 'sharp', [], [('bleed', 0.2)], self)]
        else:
            return []

class DogEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog eye', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 15
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

class DogBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 15
        self.weight = 100
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh.'

class DogHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 15
        self.weight = 400
        self.bravery = 0.5
        self._info = 'A heart consisting of living flesh. Average bravery.'

class DogLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 15
        self.weight = 450
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh.'

class DogKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 15
        self.weight = 100
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'

class DogStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 15
        self.weight = 800
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 0.25, 'Your carnivorous stomach is very poor at processing vegetables.'),
            'living flesh': (1, 1, None),
            'undead flesh': (-1,)
            }
        self._info = 'A stomach consisting of living flesh. Very poor at processing vegetables.'

class DogTail(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog tail', '~', (170, 130, 70))
        self.categories = ['tail']
        self.childconnections = {}
        self.maxhp = 7
        self.weight = 400
        self._info = 'A tail consisting of living flesh.'



class HobgoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 100
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 35000
        self.carryingcapacity = 20000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self._info = 'A torso consisting of living flesh. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

class HobgoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 30
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 5000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self._info = 'An arm consisting of living flesh. Good at avoiding traps when crawling. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 30, 'blunt', [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', '', '', 0.8, 1, 1, 30, 'sharp', [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class HobgoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 30
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 13000
        self.carryingcapacity = 15000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self._info = 'A torso consisting of living flesh. Good at avoiding traps. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1.5
            else:
                return 0.75
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 40, 'blunt', [], [], self)]
        else:
            return []

class HobgoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 30
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.6, 1, 1, 40, 'sharp', [], [('bleed', 0.1)], self)]
        else:
            return []

class HobgoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of living flesh. Good at detecting traps.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

class HobgoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh.'

class HobgoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 250
        self.bravery = 0.5
        self._info = 'A heart consisting of living flesh. Average bravery.'

class HobgoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 600
        self.breathepoisonresistance = 0.2
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh. Some protection against poison gas.'

class HobgoblinKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'

class HobgoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
            }
        self._info = 'A stomach consisting of living flesh.'



class MoleMonkTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk torso', '*', (186, 100, 13))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 100
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 50000
        self.carryingcapacity = 30000
        self._info = 'A torso consisting of living flesh. Good carrying capacity.'

class MoleMonkArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk arm', '~', (186, 100, 13))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 30
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 7000
        self.carefulness = 0.5
        self._info = 'An arm consisting of living flesh. Can be used for mining.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0.5
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', '', '', 0.8, 1, 1, 30, 'rough', [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class MoleMonkLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk leg', '~', (186, 100, 13))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 30
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 17000
        self.carryingcapacity = 20000
        self.carefulness = 0.5
        self.maxrunstamina = 5
        self._info = 'A leg consisting of living flesh. Low running stamina.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1.5
            else:
                return 0.75
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 40, 'blunt', [], [], self)]
        else:
            return []

class MoleMonkHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk head', '*', (186, 100, 13))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 30
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self._info = 'A head consisting of living flesh.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 1, 1, 45, 'sharp', [], [('bleed', 0.1)], self)]
        else:
            return []

class MoleMonkEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of living flesh. Very short-sighted.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 1
        else:
            return 0

class MoleMonkBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 1300
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = ['fasting']
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh. Enables the fasting stance.'

class MoleMonkHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 300
        self.bravery = 0.25
        self._info = 'A heart consisting of living flesh. Easily scared.'

class MoleMonkLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 600
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 1
        self._info = 'A lung consisting of living flesh. Recovers running stamina quickly.'

class MoleMonkKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'

class MoleMonkStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
            }
        self._info = 'A stomach consisting of living flesh.'



class WolfTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf torso', '*', (100, 100, 150))
        self.categories = ['torso']
        self.childconnections = {
            'front left leg': BodyPartConnection(self, ['leg'], False, 'front left '),
            'front right leg': BodyPartConnection(self, ['leg'], False, 'front right '),
            'back left leg': BodyPartConnection(self, ['leg'], False, 'back left '),
            'back right leg': BodyPartConnection(self, ['leg'], False, 'back right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True),
            'tail': BodyPartConnection(self, ['tail'], False, '')
            }
        self.maxhp = 150
        self.worn = {'barding': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 25000
        self.carryingcapacity = 25000
        self._info = 'A torso consisting of living flesh. Rather strong at carrying.'

class WolfLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf leg', '~', (100, 100, 150))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 30
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 4000
        self.carryingcapacity = 7500
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self._info = 'A leg consisting of living flesh. On its own rather weak at carrying. Very fast if there are at least four legs, and quite fast even when there are two.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 3:
                return 2
            elif len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1.5
            else:
                return 0.5
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', '', '', 0.7, 1, 1, 10, 'sharp', [], [], self)]
        else:
            return []

class WolfHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf head', '*', (100, 100, 150))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 30
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 4000
        self._info = 'A head consisting of living flesh.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.85, 1, 1, 40, 'sharp', [], [('bleed', 0.2)], self)]
        else:
            return []

class WolfEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf eye', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh. Sees farther than most.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 4
        else:
            return 0

class WolfBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 120
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh.'

class WolfHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 500
        self.bravery = 0.75
        self._info = 'A heart consisting of living flesh. Very brave.'

class WolfLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 600
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh.'

class WolfKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'

class WolfStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 0.25, 'Your carnivorous stomach is very poor at processing vegetables.'),
            'living flesh': (1, 1, None),
            'undead flesh': (-1,)
            }
        self._info = 'A stomach consisting of living flesh. Very poor at processing vegetables.'

class WolfTail(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf tail', '~', (100, 100, 150))
        self.categories = ['tail']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 500
        self._info = 'A tail consisting of living flesh.'



class DrillbotChassis(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'drillbot chassis', '*', (150, 150, 150))
        self.categories = ['torso']
        self.childconnections = {
            'front left wheel': BodyPartConnection(self, ['leg'], False, 'front left '),
            'front right wheel': BodyPartConnection(self, ['leg'], False, 'front right '),
            'back left wheel': BodyPartConnection(self, ['leg'], False, 'back left '),
            'back right wheel': BodyPartConnection(self, ['leg'], False, 'back right '),
            'arm': BodyPartConnection(self, ['arm'], False, ''),
            'coolant pumping system': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'coolant aerator system': BodyPartConnection(self, ['lung'], False, '', defensecoefficient=0.5, armorapplies=True),
            'coolant filtering system': BodyPartConnection(self, ['kidney'], False, '', defensecoefficient=0.5, armorapplies=True),
            'biomass processor': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.5, armorapplies=True),
            'left camera': BodyPartConnection(self, ['eye'], False, 'left '),
            'right camera': BodyPartConnection(self, ['eye'], False, 'right '),
            'central processor': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 150
        self.worn = {'barding': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'chassis'
        self.weight = 30000
        self.carryingcapacity = 50000
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self._info = 'A torso consisting of electronics. Has very good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp attacks.'

class DrillbotWheel(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'drillbot wheel', '*', (150, 150, 150))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 30
        self.worn = {'wheel cover': listwithowner([], self)}
        self._wearwieldname = 'wheel'
        self.weight = 4000
        self.carryingcapacity = 10000
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = -0.5
        self._resistances['rough'] = -0.5
        self.carefulness = 0.5
        self.maxrunstamina = 20
        self._info = 'A leg-like organ consisting of electronics. Doesn\'t gain hunger and can\'t be poisoned. Very weak against sharp and rough attacks. Very fast if there are at least four legs or wheels, and quite fast even when there are two. High "running" stamina.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 3:
                return 2
            elif len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1.5
            else:
                return 0.5
        else:
            return 0

class DrillArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'drill arm', '~', (150, 150, 150))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 40
        self.weight = 7000
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self._info = 'A dual-purpose pneumatic drill arm consisting of electronics. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp attacks. Can be used for mining.'

    def minespeed(self):
        return 0.5

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'drill', 'drilled', 'drilled', '', '', 0.8, 1, 1, 50, 'rough', [], [('bleed', 0.2)], self)]
        else:
            return []

class DrillbotCamera(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'drillbot camera', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 20
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of electronics. Good at detecting traps. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp attacks.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 4
        else:
            return 0

class DrillbotPump(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'coolant pump, model DB-100', '*', (0, 0, 255))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 30
        self.weight = 1500
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self.bravery = 0.5
        self._info = 'A heart consisting of electronics. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp attacks.'

class DrillbotAerator(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'coolant aerator, model DB-100', '*', (0, 0, 255))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 30
        self.weight = 600
        self.material = 'electronics'
        self._attackpoisonresistance = 1
        self.breathepoisonresistance = 0.5
        self.runstaminarecoveryspeed = 1
        self._resistances['sharp'] = 0.2
        self._info = 'A lung consisting of electronics. Doesn\'t gain hunger and can\'t be poisoned. Protects living bodyparts from poison gas quite well. Recovers running stamina quickly. Resistant against sharp attacks.'

class DrillbotFilter(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'coolant filter, model DB-100', '*', (0, 0, 255))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 30
        self.weight = 600
        self.material = 'electronics'
        self._attackpoisonresistance = 1
        self.endotoxicity = -1
        self._resistances['sharp'] = 0.2
        self._info = 'A kidney consisting of electronics. Doesn\'t gain hunger and can\'t be poisoned. Filters toxins at an average speed. Resistant against sharp attacks.'

class DrillbotProcessor(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'tactical processor, model DB-100', '*', (255, 255, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 30
        self.weight = 2000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self._info = 'A brain consisting of electronics. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp attacks.'

class DrillBotBiomassProcessor(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'drillbot biomass processor', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 30
        self.weight = 2000
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (1, 1, None),
            'undead flesh': (1, 1, None)
            }
        self._info = 'A stomach consisting of electronics. Processes everything even somewhat edible perfectly. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp attacks.'



class GhoulTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul torso', '*', (191, 255, 255))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], False, ''),
            'heart': BodyPartConnection(self, ['heart'], False, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 175
        self.material = "undead flesh"
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 40000
        self.carryingcapacity = 60000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A torso consisting of undead flesh. Needs neither head nor heart. Has extremely good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class GhoulArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul arm', '~', (191, 255, 255))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 50
        self.material = "undead flesh"
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.carefulness = 0.3
        self._info = 'An arm consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 50, 'blunt', [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class GhoulLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul leg', '~', (191, 255, 255))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 50
        self.material = "undead flesh"
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.carefulness = 0.3
        self.maxrunstamina = 20
        self._info = 'A leg consisting of undead flesh. Somewhat clumsy, but has good carrying capacity and high running stamina. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 75, 'blunt', [], [], self)]
        else:
            return []

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1
            else:
                return 0.5
        else:
            return 0

class GhoulHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul head', '*', (191, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], False, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 50
        self.material = "undead flesh"
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.scariness = 10
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A head consisting of undead flesh. Can scare enemies for up to 10 s. Needs no brain. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 2, 1, 50, 'sharp', [], [('bleed', 0.1)], self)]
        else:
            return []

class GhoulEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul eye', '*', (155, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 25
        self.material = "undead flesh"
        self.weight = 7
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

class GhoulBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul brain', '*', (150, 178, 82))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 25
        self.material = "undead flesh"
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A brain consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class GhoulHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul heart', '*', (150, 178, 82))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 25
        self.material = "undead flesh"
        self.weight = 250
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.bravery = 0.5
        self._info = 'A heart consisting of undead flesh. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class GhoulLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul lung', '*', (150, 178, 82))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 25
        self.material = 'undead flesh'
        self.weight = 600
        self.breathepoisonresistance = 0.5
        self.runstaminarecoveryspeed = 0.25
        self._resistances['sharp'] = -0.2
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._info = 'A lung consisting of undead flesh. Protects living bodyparts from poison gas quite well. Recovers running stamina slowly. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class GhoulKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie kidney', '*', (150, 178, 82))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 25
        self.material = 'undead flesh'
        self.weight = 120
        self._attackpoisonresistance = 1
        self.endotoxicity = -0.5
        self._resistances['sharp'] = -0.2
        self._info = 'A kidney consisting of undead flesh. Filters toxins at a slow speed. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks.'

class GhoulStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul stomach', '*', (150, 178, 82))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 25
        self.material = "undead flesh"
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'vegetables': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'living flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'undead flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.')
            }
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A stomach consisting of undead flesh. Inefficient at processing food. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'



class SmallFireElementalTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental torso', '*', (255, 204, 0))
        self.categories = ['torso']
        self.childconnections = {
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.8, armorapplies=True),
            'left bellows': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right bellows': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True),
            'front left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front left '),
            'back left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back left '),
            'front right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front right '),
            'back right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back right ')
            }
        self.maxhp = 200
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 400
        self.carryingcapacity = 60000
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._info = 'A torso consisting of elemental fire. Has extremely good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire attacks.'

class SmallFireElementalHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental head', '*', (255, 204, 0))
        self.categories = ['head']
        self.childconnections = {
            'eye': BodyPartConnection(self, ['eye'], False, ''),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 55
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 100
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._info = 'A head consisting of elemental fire.Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire attacks.'

class SmallFireElementalEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ember eye', '*', (255, 204, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 0
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of elemental fire. Sees much farther than most, and is rather good at detecting traps. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire attacks.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 5
        else:
            return 0

class SmallFireElementalBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental brain', '*', (255, 204, 0))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 30
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 10
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._info = 'A brain consisting of elemental fire. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire attacks.'

class SmallFireElementalHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fiery heart', '*', (255, 204, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 30
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 10
        self.bravery = 0.5
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._info = 'A heart consisting of elemental fire. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire attacks.'

class SmallFireElementalBellows(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental bellows', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 30
        self.material = 'elemental'
        self.weight = 600
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._resistances['fire'] = 1
        self._info = 'A lung consisting of elemental fire. Doesn\'t gain hunger and can\'t be poisoned, but doesn\'t protect living body parts from poison gas. Completely resistant against fire attacks.'

class SmallFireElementalTentacle(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental tentacle', '~', (255, 204, 0))
        self.categories = ['arm', 'leg', 'tentacle']
        self.childconnections = {}
        self.maxhp = 40
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'tentacle'
        self.worn = {'tentacle armor': listwithowner([], self), 'ring': listwithowner([], self)}
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 100
        self.carryingcapacity = 20000
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self._info = 'A tentacle consisting of elemental fire. Works both as an arm and as a leg. Faster at moving and attacking if there are more of them. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire attacks.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if 'leg' in self.parentalconnection.categories:
                return 0.5*len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())])
            elif 'arm' in self.parentalconnection.categories:
                return 0.5*len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())])
            else:
                return 0.5*len([part for part in self.owner if 'tentacle' in part.categories and not (part.destroyed() or part.incapacitated())])
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                timetaken = 2 / len([part for part in self.owner if 'tentacle' in part.categories and not (part.destroyed() or part.incapacitated())])
                return [Attack(self.parentalconnection.prefix + 'tentacle burn', 'burned', 'burned', '', '', 0.8, timetaken, 1, 30, 'fire', [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []



class DireWolfTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf torso', '*', (100, 100, 150))
        self.categories = ['torso']
        self.childconnections = {
            'front left leg': BodyPartConnection(self, ['leg'], False, 'front left '),
            'front right leg': BodyPartConnection(self, ['leg'], False, 'front right '),
            'back left leg': BodyPartConnection(self, ['leg'], False, 'back left '),
            'back right leg': BodyPartConnection(self, ['leg'], False, 'back right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True),
            'tail': BodyPartConnection(self, ['tail'], False, '')
            }
        self.maxhp = 225
        self.worn = {'barding': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 35000
        self.carryingcapacity = 40000
        self._info = 'A torso consisting of living flesh. Very strong at carrying.'

class DireWolfLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf leg', '~', (100, 100, 150))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 60
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 6000
        self.carryingcapacity = 10000
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self._info = 'A leg consisting of living flesh. On its own somewhat weak at carrying. Very fast if there are at least four legs, and quite fast even when there are two.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 3:
                return 2
            elif len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1.5
            else:
                return 0.5
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', '', '', 0.7, 1, 1, 20, 'sharp', [], [], self)]
        else:
            return []

class DireWolfHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf head', '*', (100, 100, 150))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 60
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._info = 'A head consisting of living flesh.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.85, 1, 1, 60, 'sharp', [], [('bleed', 0.2)], self)]
        else:
            return []

class DireWolfEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf eye', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh. Sees farther than most.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 4
        else:
            return 0

class DireWolfBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 20
        self.weight = 120
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh.'

class DireWolfHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 35
        self.weight = 700
        self.bravery = 0.75
        self._info = 'A heart consisting of living flesh. Very brave.'

class DireWolfLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 35
        self.weight = 800
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh.'

class DireWolfKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 35
        self.weight = 160
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'

class DireWolfStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 30
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 0.25, 'Your carnivorous stomach is very poor at processing vegetables.'),
            'living flesh': (1, 1, None),
            'undead flesh': (-1,)
            }
        self._info = 'A stomach consisting of living flesh. Very poor at processing vegetables.'

class DireWolfTail(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf tail', '~', (100, 100, 150))
        self.categories = ['tail']
        self.childconnections = {}
        self.maxhp = 10
        self.weight = 600
        self._info = 'A tail consisting of living flesh.'



class JobgoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], True, ''),
            'heart': BodyPartConnection(self, ['heart'], True, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 250
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 35000
        self.carryingcapacity = 20000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self._info = 'A torso consisting of living flesh. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

class JobgoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 60
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 5000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self._info = 'An arm consisting of living flesh. Good at avoiding traps when crawling. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 65, 'blunt', [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', '', '', 0.8, 1, 1, 65, 'sharp', [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class JobgoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 60
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 13000
        self.carryingcapacity = 15000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self._info = 'A torso consisting of living flesh. Good at avoiding traps. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 2
            else:
                return 1
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 90, 'blunt', [], [], self)]
        else:
            return []

class JobgoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 60
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp attacks) but weak bones (weak against blunt attacks).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.6, 1, 1, 90, 'sharp', [], [('bleed', 0.1)], self)]
        else:
            return []

class JobgoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 40
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of living flesh. Good at detecting traps.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

class JobgoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 40
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._info = 'A brain consisting of living flesh.'

class JobgoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 40
        self.weight = 250
        self.bravery = 0.5
        self._info = 'A heart consisting of living flesh. Average bravery.'

class JobgoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 40
        self.weight = 500
        self.breathepoisonresistance = 0.2
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh. Some protection against poison gas.'

class JobgoblinKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 40
        self.weight = 100
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'

class JobgoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 40
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
            }
        self._info = 'A stomach consisting of living flesh.'



class GhastTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast torso', '*', (191, 255, 255))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left '),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right '),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left '),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right '),
            'head': BodyPartConnection(self, ['head'], False, ''),
            'heart': BodyPartConnection(self, ['heart'], False, '', defensecoefficient=0.5, armorapplies=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', defensecoefficient=0.5, armorapplies=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', defensecoefficient=0.5, armorapplies=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', defensecoefficient=0.8, armorapplies=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', defensecoefficient=0.8, armorapplies=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', defensecoefficient=0.8, armorapplies=True)
            }
        self.maxhp = 275
        self.material = "undead flesh"
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 40000
        self.carryingcapacity = 60000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A torso consisting of undead flesh. Needs neither head nor heart. Has extremely good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class GhastArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast arm', '~', (191, 255, 255))
        self.categories = ['arm']
        self.childconnections = {}
        self.maxhp = 65
        self.material = "undead flesh"
        self.capableofwielding = True
        self.wielded = listwithowner([], self)  # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner([], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.carefulness = 0.3
        self._info = 'An arm consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'arm' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 0.2
            else:
                return 0.1
        else:
            return 0

    def minespeed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return 0
            else:
                return self.wielded[0].minespeed()
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            if len(self.wielded) == 0:
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', '', '', 0.8, 1, 1, 70, 'blunt', [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

class GhastLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast leg', '~', (191, 255, 255))
        self.categories = ['leg']
        self.childconnections = {}
        self.maxhp = 65
        self.material = "undead flesh"
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.carefulness = 0.3
        self.maxrunstamina = 20
        self._info = 'A leg consisting of undead flesh. Somewhat clumsy, but has good carrying capacity and high running stamina. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', '', '', 0.6, 1, 1, 105, 'blunt', [], [], self)]
        else:
            return []

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            if len([part for part in self.owner if 'leg' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
                return 1
            else:
                return 0.5
        else:
            return 0

class GhastHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast head', '*', (191, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], False, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 65
        self.material = "undead flesh"
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.scariness = 15
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A head consisting of undead flesh. Can scare enemies for up to 15 s. Needs no brain. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.4, 2, 1, 70, 'sharp', [], [('bleed', 0.1)], self)]
        else:
            return []

class GhastEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast eye', '*', (155, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self.maxhp = 45
        self.material = "undead flesh"
        self.weight = 7
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

class GhastBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast brain', '*', (150, 178, 82))
        self.categories = ['brain']
        self.childconnections = {}
        self.maxhp = 45
        self.material = "undead flesh"
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.stances = []
        self.frightenedby = []
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A brain consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class GhastHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast heart', '*', (150, 178, 82))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 45
        self.material = "undead flesh"
        self.weight = 250
        self.bravery = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A heart consisting of undead flesh. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class GhastLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast lung', '*', (150, 178, 82))
        self.categories = ['lung']
        self.childconnections = {}
        self.maxhp = 45
        self.material = 'undead flesh'
        self.weight = 600
        self.breathepoisonresistance = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.runstaminarecoveryspeed = 0.25
        self._info = 'A lung consisting of undead flesh. Protects living bodyparts from poison gas quite well. Recovers running stamina slowly. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'

class GhastKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast kidney', '*', (150, 178, 82))
        self.categories = ['kidney']
        self.childconnections = {}
        self.maxhp = 45
        self.material = 'undead flesh'
        self.weight = 120
        self._attackpoisonresistance = 1
        self.endotoxicity = -0.5
        self._resistances['sharp'] = -0.2
        self._info = 'A kidney consisting of undead flesh. Filters toxins at a slow speed. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks.'

class GhastStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast stomach', '*', (150, 178, 82))
        self.categories = ['stomach']
        self.childconnections = {}
        self.maxhp = 45
        self.material = "undead flesh"
        self.weight = 1000
        self.foodprocessing = { # Tuples, first item: is 1 if can eta normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'vegetables': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'living flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'undead flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.')
            }
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A stomach consisting of undead flesh. Inefficient at processing food. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp attacks. In the presence of living body parts, accumulates endotoxins.'



class VelociraptorSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized velociraptor skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 50
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 1000
        self.material = "fossil"
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.5
        self._resistances['blunt'] = 0.5
        self._resistances['fire'] = 0.5
        self._resistances['rough'] = -1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Very resistant against sharp, blunt and fire attacks, but very weak against rough attacks.'
        

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 0.9, 1, 1, 50, 'sharp', [], [('bleed', 0.2)], self)]
        else:
            return []

class DeinonychusSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized deinonychus skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 75
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 5500
        self.material = "fossil"
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.5
        self._resistances['blunt'] = 0.5
        self._resistances['fire'] = 0.5
        self._resistances['rough'] = -1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Very resistant against sharp, blunt and fire attacks, but very weak against rough attacks.'
        

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 1.0, 1, 1, 75, 'sharp', [], [('bleed', 0.2)], self)]
        else:
            return []

class CeratosaurusSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized ceratosaurus skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 100
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 13500
        self.material = "fossil"
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.5
        self._resistances['blunt'] = 0.5
        self._resistances['fire'] = 0.5
        self._resistances['rough'] = -1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Very resistant against sharp, blunt and fire attacks, but very weak against rough attacks.'
        

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 1.1, 1, 1, 100, 'sharp', [], [('bleed', 0.2)], self)]
        else:
            return []

class AllosaurusSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized allosaurus skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 125
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 48500
        self.material = "fossil"
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.5
        self._resistances['blunt'] = 0.5
        self._resistances['fire'] = 0.5
        self._resistances['rough'] = -1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Very resistant against sharp, blunt and fire attacks, but very weak against rough attacks.'
        

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 1.2, 1, 1, 125, 'sharp', [], [('bleed', 0.2)], self)]
        else:
            return []

class TyrannosaurusSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized tyrannosaurus skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left '),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right '),
            'brain': BodyPartConnection(self, ['brain'], True, '', defensecoefficient=0.5, armorapplies=True)
            }
        self.maxhp = 150
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 270000
        self.material = "fossil"
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.5
        self._resistances['blunt'] = 0.5
        self._resistances['fire'] = 0.5
        self._resistances['rough'] = -1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Very resistant against sharp, blunt and fire attacks, but very weak against rough attacks.'
        

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', '', '', 1.3, 1, 1, 150, 'sharp', [], [('bleed', 0.2)], self)]
        else:
            return []
