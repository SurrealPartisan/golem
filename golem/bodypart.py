#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 21:26:04 2023

@author: surrealpartisan
"""

import numpy as np

from golem import item
from golem.item import Attack
from golem import magic
from golem.utils import constantfunction, listwithowner, loglist, mapwidth, mapheight, numlevels, difficulty


class BodyPartConnection():
    def __init__(self, parent, categories, vital, prefix, heightfunc, defensecoefficient=1, armorapplies=False, internal=False):
        self.parent = parent
        self.categories = categories
        self.vital = vital
        self.child = None
        self.prefix = prefix
        self.heightfunc = heightfunc
        self.defensecoefficient = defensecoefficient
        self.armorapplies = armorapplies
        self.internal = internal

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
        self._topheight = 0
        self._bottomheight = 0
        self.capableofwielding = False
        self.capableofthrowing = False
        self.worn = {}  # Each key is a category of item, e.g. helmet or back item. Each value is a listwithowner, with the bodypart as the owner. The lists themselves should contain at most one item per list.
        self.material = "living flesh"
        self.consumable = True
        self.edible = True
        self._defensecoefficient = 0.8
        self._attackpoisonresistance = 0
        self._wearwieldname = name
        self.bleedclocks = []
        self.imbalanceclock = 0
        self._resistances = {'sharp': 0, 'blunt': 0,
                             'rough': 0, 'fire': 0, 'electric': 0}
        self.nonconductive = False
        self.detectiondistance = 0
        self.detectionprobability = 0
        self.carefulness = 0
        self.usable = True
        self.maxrunstamina = 0
        self.runstaminarecoveryspeed = 0
        self.bravery = 0
        self.scariness = 0
        self.endotoxicity = 0
        self.smell = 0
        self._stances = []

    def connect(self, connection_name, child):
        return self.childconnections[connection_name].connect(child)

    def baseheight(self):
        if 'torso' in self.categories:
            leglengths = [part.standingheight() for part in self.owner if 'leg' in part.categories and not part.destroyed(
            ) and not part.incapacitated()]  # These should all be same
            if len(leglengths) > 0:
                if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
                    return leglengths[0] + 50
                else:
                    return leglengths[0]
            else:
                if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
                    return 50 - self._bottomheight
                else:
                    return 0 - self._bottomheight
        else:
            return self.parentalconnection.parent.baseheight() + self.parentalconnection.heightfunc()

    def topheight(self):
        return self.baseheight() + self._topheight

    def bottomheight(self):
        return self.baseheight() + self._bottomheight

    def vital(self):
        if 'torso' in self.categories:
            return True
        else:
            return self.parentalconnection.vital

    def incapacitated(self):
        if hasattr(self.owner, 'owner') and not 'player' in self.owner.owner.factions:
            return self.damagetaken >= difficulty*self.maxhp
        else:
            return False

    def internal(self):
        if 'torso' in self.categories:
            return False
        else:
            return self.parentalconnection.internal and not self.parentalconnection.parent.destroyed()

    def speed(self):
        return 0

    def flyingspeed(self):
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
        armorlist = [wearlist[0] for wearlist in self.worn.values() if len(
            wearlist) > 0 and wearlist[0].isarmor and not wearlist[0].destroyed()]
        if len(armorlist) > 0:
            return armorlist[0]
        elif self.parentalconnection != None and self.parentalconnection.armorapplies:
            return self.parentalconnection.parent.armor()
        else:
            return None

    def stances(self):
        return self._stances

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
                newbleedclocklist.append(
                    (dmgleft - dmg, timepassed % 1, causer))
        self.bleedclocks = newbleedclocklist
        return dmgtotal, causers

    def imbalanced(self):
        if 'torso' in self.categories:
            maxlegs = len([connection for connection in self.childconnections.values(
            ) if 'leg' in connection.categories])
            functioninglegs = len([connection for connection in self.childconnections.values() if 'leg' in connection.categories and connection.child !=
                                  None and 'leg' in connection.child.categories and not connection.child.destroyed() and not connection.child.incapacitated()])
            if functioninglegs < 4:
                return 0 < functioninglegs <= maxlegs/2
            else:
                return False
        elif 'leg' in self.categories:
            return self.imbalanceclock > 0
        else:
            return False

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
                    it.on_unwearunwield(self.owner.owner)
            for it in [l[0] for l in self.worn.values() if len(l) > 0]:
                it.owner.remove(it)
                self.owner.owner.world.items.append(it)
                it.owner = self.owner.owner.world.items
                it.x = self.owner.owner.x
                it.y = self.owner.owner.y
                self.owner.owner.log().append('You dropped your ' + it.name)
                it.on_unwearunwield(self.owner.owner)


def heightfuncuprightorprone(torso, uprightheight, proneheight):
    def fun():
        legs = [part for part in torso.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return proneheight
        else:
            return uprightheight
    return fun


class HumanTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human torso', '*', (250, 220, 196))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 55, 20)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 55, 20)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 60, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 40, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 30, 15), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 60
        self._pronetopheight = 30
        self.maxhp = 50
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 45000
        self.carryingcapacity = 20000
        self.smell = 1
        self._info = 'A torso consisting of living flesh.'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class HumanArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human arm', '~', (250, 220, 196))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 30
        self.upperfinelimit = 15
        self.lowerfinelimit = -15
        self.lowerpoorlimit = -30
        self.maxhp = 20
        self.capableofthrowing = True
        self.throwaccuracy = 0.99
        self.throwspeed = 1
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 5000
        self.carefulness = 0.5
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Accurate at throwing. Protects other bodyparts quite well.'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 0.8, 1, 1, 5, 'blunt', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class HumanLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human leg', '~', (250, 220, 196))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -90
        self.upperpoorlimit = 40
        self.upperfinelimit = -15
        self.lowerfinelimit = -90
        self.lowerpoorlimit = -90
        self.maxheight = 90
        self.maxhp = 20
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 17000
        self.carryingcapacity = 20000
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.6, 1, 1, 7, 'blunt', 0, [], [], self)]
        else:
            return []


class HumanHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human head', '*', (250, 220, 196))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 20
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.4, 2, 1, 5, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class HumanEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 5
        self.weight = 8
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class HumanBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 10
        self.weight = 1300
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 1
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 1, average mana capacity.'


class HumanHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 10
        self.weight = 300
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class HumanLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
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
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 10
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'


class HumanStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'human stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 10
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
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
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 55, 20)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 55, 20)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], False, '', heightfuncuprightorprone(self, 60, 20)),
            'heart': BodyPartConnection(self, ['heart'], False, '', heightfuncuprightorprone(self, 40, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 30, 15), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 60
        self._pronetopheight = 30
        self.maxhp = 50
        self.material = "undead flesh"
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 40000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.smell = 2
        self._info = 'A torso consisting of undead flesh. Needs neither head nor heart. Has good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class ZombieArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie arm', '~', (191, 255, 128))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 30
        self.upperfinelimit = 15
        self.lowerfinelimit = -15
        self.lowerpoorlimit = -30
        self.maxhp = 20
        self.material = "undead flesh"
        self.capableofthrowing = True
        self.throwaccuracy = 0.97
        self.throwspeed = 0.75
        self.protectiveness = 0.1
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.carefulness = 0.3
        self.smell = 2
        self._info = 'An arm consisting of undead flesh. Slow at throwing. Protects other bodyparts but not that well. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 0.8, 1, 1, 5, 'blunt', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class ZombieLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie leg', '~', (191, 255, 128))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -90
        self.upperpoorlimit = 40
        self.upperfinelimit = -15
        self.lowerfinelimit = -90
        self.lowerpoorlimit = -90
        self.maxheight = 90
        self.maxhp = 20
        self.material = "undead flesh"
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.carefulness = 0.3
        self.maxrunstamina = 20
        self.smell = 2
        self._info = 'A leg consisting of undead flesh. Quite slow and somewhat clumsy, but has good carrying capacity and high running stamina. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.6, 1, 1, 7, 'blunt', 0, [], [], self)]
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
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], False, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 20
        self.material = "undead flesh"
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.scariness = 5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.smell = 2
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of undead flesh. Can scare enemies for up to 5 s. Needs no brain. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.4, 2, 1, 5, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class ZombieEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie eye', '*', (155, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 5
        self.material = "undead flesh"
        self.weight = 7
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class ZombieBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie brain', '*', (150, 178, 82))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 10
        self.material = "undead flesh"
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 0
        self.manacapacity = 25
        self.spellsknown = []
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A brain consisting of undead flesh. Intelligence 0, high mana capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class ZombieHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie heart', '*', (150, 178, 82))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 10
        self.material = "undead flesh"
        self.weight = 250
        self.bravery = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A heart consisting of undead flesh. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage. In the presence of living body parts, accumulates endotoxins.'


class ZombieLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie lung', '*', (150, 178, 82))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 10
        self.material = 'undead flesh'
        self.weight = 500
        self.runstaminarecoveryspeed = 0.25
        self.breathepoisonresistance = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A lung consisting of undead flesh. Protects living bodyparts from poison gas quite well. Recovers running stamina slowly. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class ZombieKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie kidney', '*', (150, 178, 82))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 10
        self.material = 'undead flesh'
        self.weight = 100
        self._attackpoisonresistance = 1
        self.endotoxicity = -0.5
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A kidney consisting of undead flesh. Filters toxins at a slow speed. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage.'


class ZombieStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie stomach', '*', (150, 178, 82))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 10
        self.material = "undead flesh"
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'vegetables': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'living flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'undead flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.')
        }
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A stomach consisting of undead flesh. Inefficient at processing food. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class MolePersonTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person torso', '*', (186, 100, 13))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 55, 20)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 55, 20)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 60, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 40, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 30, 15), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 60
        self._pronetopheight = 30
        self.maxhp = 50
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 45000
        self.carryingcapacity = 20000
        self.smell = 1
        self._info = 'A torso consisting of living flesh.'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class MolePersonArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person arm', '~', (186, 100, 13))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 30
        self.upperfinelimit = 15
        self.lowerfinelimit = -15
        self.lowerpoorlimit = -30
        self.maxhp = 20
        self.capableofthrowing = True
        self.throwaccuracy = 0.97
        self.throwspeed = 1
        self.protectiveness = 0.2
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 6000
        self.carefulness = 0.5
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Can be used for mining. Protects other bodyparts very well.'

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
                return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.8, 1, 1, 5, 'rough', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class MolePersonLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person leg', '~', (186, 100, 13))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -90
        self.upperpoorlimit = 40
        self.upperfinelimit = -15
        self.lowerfinelimit = -90
        self.lowerpoorlimit = -90
        self.maxheight = 90
        self.maxhp = 20
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 15000
        self.carefulness = 0.5
        self.maxrunstamina = 5
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Somewhat weak at carrying. Low running stamina.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.6, 1, 1, 7, 'blunt', 0, [], [], self)]
        else:
            return []


class MolePersonHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person head', '*', (186, 100, 13))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 20
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.smell = 1
        self.senseofsmell = 10
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Good sense of smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.4, 1, 1, 7, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class MolePersonEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 5
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of living flesh. Very short-sighted.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 1
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class MolePersonBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 10
        self.weight = 1300
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 2
        self.manacapacity = 15
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 2, low mana capacity.'


class MolePersonHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 10
        self.weight = 300
        self.bravery = 0.25
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Easily scared. Weak against electric damage.'


class MolePersonLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
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
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 10
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'


class MolePersonStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole person stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 10
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
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
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 35, 17)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 35, 17)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 40, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 30, 12), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 25, 12), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 25, 12), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 15, 12), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 15, 12), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 20, 12), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 40
        self._pronetopheight = 25
        self.maxhp = 50
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 25000
        self.carryingcapacity = 20000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class GoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 30
        self.upperfinelimit = 15
        self.lowerfinelimit = -15
        self.lowerpoorlimit = -30
        self.maxhp = 20
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 1.5
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Quick but rather inaccurate at throwing. Protects other bodyparts quite well. Good at avoiding traps when crawling. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 0.8, 1, 1, 5, 'blunt', 0, [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.8, 1, 1, 5, 'sharp', 0, [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class GoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -70
        self.upperpoorlimit = 30
        self.upperfinelimit = -15
        self.lowerfinelimit = -70
        self.lowerpoorlimit = -70
        self.maxheight = 70
        self.maxhp = 20
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 10000
        self.carryingcapacity = 15000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Good at avoiding traps. Somewhat weak at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.6, 1, 1, 7, 'blunt', 0, [], [], self)]
        else:
            return []


class GoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 20
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.6, 1, 1, 7, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class GoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 5
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of living flesh. Good at detecting traps.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class GoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 10
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 1
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 1, average mana capacity.'


class GoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 10
        self.weight = 250
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class GoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
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
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 10
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'


class GoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'goblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 10
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
        }
        self._info = 'A stomach consisting of living flesh.'


class GlassElementalTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'glass elemental torso', '*', (0, 255, 255))
        self.categories = ['torso']
        self.childconnections = {
            'head': BodyPartConnection(self, ['head'], True, '', constantfunction(150)),
            'heart': BodyPartConnection(self, ['heart'], True, '', constantfunction(100), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', constantfunction(100), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', constantfunction(100), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', constantfunction(70), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', constantfunction(70), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', constantfunction(90), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', constantfunction(145)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', constantfunction(145)),
            'tail': BodyPartConnection(self, ['tail'], False, '', constantfunction(2))
        }
        self._topheight = 150
        self.maxhp = 25
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 10000
        self.carryingcapacity = 40000
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self.maxrunstamina = 20
        self._attackpoisonresistance = 1
        self._resistances['blunt'] = -1
        self._resistances['rough'] = -1
        self._resistances['electric'] = 1
        self.nonconductive = True
        self._info = 'A snake-like torso consisting of elemental glass. Has very good carrying capacity. Doesn\'t have leg slots, but has a movement speed itself. Doesn\'t gain hunger and can\'t be poisoned. Very weak against blunt and rough damage, but completely resistant against electric damage and nonconductive. No smell. Breaks into glass shards when destroyed.'

    def speed(self):
        if not (self.destroyed() or self.incapacitated()):
            return 1
        else:
            return 0

    def baseheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

    def on_destruction(self, dead):
        if not np.any([it.x == self.owner.owner.x and it.y == self.owner.owner.y and it.name == 'glass shards' for it in self.owner.owner.world.items]):
            item.GlassShards(self.owner.owner.world.items,
                             self.owner.owner.x, self.owner.owner.y)
        super().on_destruction(dead)


class GlassElementalHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'glass elemental head', '*', (0, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'upper left eye': BodyPartConnection(self, ['eye'], False, 'upper left ', constantfunction(20)),
            'upper right eye': BodyPartConnection(self, ['eye'], False, 'upper right ', constantfunction(20)),
            'center left eye': BodyPartConnection(self, ['eye'], False, 'center left ', constantfunction(18)),
            'center right eye': BodyPartConnection(self, ['eye'], False, 'center right ', constantfunction(18)),
            'lower left eye': BodyPartConnection(self, ['eye'], False, 'lower left ', constantfunction(16)),
            'lower right eye': BodyPartConnection(self, ['eye'], False, 'lower right ', constantfunction(16)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 10
        self._bottomheight = 0
        self.maxhp = 10
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 1000
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['blunt'] = -1
        self._resistances['rough'] = -1
        self._resistances['electric'] = 1
        self.nonconductive = True
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of elemental glass. Doesn\'t gain hunger and can\'t be poisoned. Very weak against blunt and rough damage, but completely resistant against electric damage and nonconductive. No smell. Breaks into glass shards when destroyed.'

    def on_destruction(self, dead):
        if not np.any([it.x == self.owner.owner.x and it.y == self.owner.owner.y and it.name == 'glass shards' for it in self.owner.owner.world.items]):
            item.GlassShards(self.owner.owner.world.items,
                             self.owner.owner.x, self.owner.owner.y)
        super().on_destruction(dead)


class GlassElementalEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'glass eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 5
        self.weight = 10
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['blunt'] = -1
        self._resistances['rough'] = -1
        self._resistances['electric'] = 1
        self.nonconductive = True
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of elemental glass. Very short-sighted on its own. Doesn\'t gain hunger and can\'t be poisoned. Very weak against blunt and rough damage, but completely resistant against electric damage and nonconductive.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 1
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        if not np.any([it.x == self.owner.owner.x and it.y == self.owner.owner.y and it.name == 'glass shards' for it in self.owner.owner.world.items]):
            item.GlassShards(self.owner.owner.world.items,
                             self.owner.owner.x, self.owner.owner.y)
        super().on_destruction(dead)


class GlassElementalBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'glass elemental brain', '*', (0, 255, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 5
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 100
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 1
        self.manacapacity = 20
        self.spellsknown = []
        self._attackpoisonresistance = 1
        self._resistances['blunt'] = -1
        self._resistances['rough'] = -1
        self._resistances['electric'] = 1
        self.nonconductive = True
        self._info = 'A brain consisting of elemental glass. Intelligence 1, average mana capacity. Doesn\'t gain hunger and can\'t be poisoned. Very weak against blunt and rough damage, but completely resistant against electric damage and nonconductive. Breaks into glass shards when destroyed.'

    def on_destruction(self, dead):
        if not np.any([it.x == self.owner.owner.x and it.y == self.owner.owner.y and it.name == 'glass shards' for it in self.owner.owner.world.items]):
            item.GlassShards(self.owner.owner.world.items,
                             self.owner.owner.x, self.owner.owner.y)
        super().on_destruction(dead)


class GlassElementalHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'glass heart', '*', (0, 255, 255))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 5
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 100
        self.bravery = 0.5
        self._attackpoisonresistance = 1
        self._resistances['blunt'] = -1
        self._resistances['rough'] = -1
        self._resistances['electric'] = 1
        self.nonconductive = True
        self._info = 'A heart consisting of elemental fire. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Very weak against blunt and rough damage, but completely resistant against electric damage and nonconductive. Breaks into glass shards when destroyed.'

    def on_destruction(self, dead):
        if not np.any([it.x == self.owner.owner.x and it.y == self.owner.owner.y and it.name == 'glass shards' for it in self.owner.owner.world.items]):
            item.GlassShards(self.owner.owner.world.items,
                             self.owner.owner.x, self.owner.owner.y)
        super().on_destruction(dead)


class GlassElementalLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'glass elemental lung', '*', (0, 255, 255))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 5
        self.material = 'elemental'
        self.weight = 600
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._resistances['blunt'] = -1
        self._resistances['rough'] = -1
        self._resistances['electric'] = 1
        self.nonconductive = True
        self._info = 'A lung consisting of elemental glass. Doesn\'t gain hunger and can\'t be poisoned, but doesn\'t protect living body parts from poison gas. Very weak against blunt and rough damage, but completely resistant against electric damage and nonconductive. Breaks into glass shards when destroyed.'

    def on_destruction(self, dead):
        if not np.any([it.x == self.owner.owner.x and it.y == self.owner.owner.y and it.name == 'glass shards' for it in self.owner.owner.world.items]):
            item.GlassShards(self.owner.owner.world.items,
                             self.owner.owner.x, self.owner.owner.y)
        super().on_destruction(dead)


class GlassElementalArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'glass elemental arm', '~', (0, 255, 255))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 30
        self.upperfinelimit = 15
        self.lowerfinelimit = -15
        self.lowerpoorlimit = -30
        self.maxhp = 10
        self.capableofthrowing = True
        self.throwaccuracy = 0.97
        self.throwspeed = 1
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 1000
        self._attackpoisonresistance = 1
        self._resistances['blunt'] = -1
        self._resistances['rough'] = -1
        self._resistances['electric'] = 1
        self.nonconductive = True
        self.carefulness = 0.5
        self._info = 'An arm consisting of elemental glass. Protects other bodyparts quite well. Doesn\'t gain hunger and can\'t be poisoned. Very weak against blunt and rough damage, but completely resistant against electric damage and nonconductive. No smell. Breaks into glass shards when destroyed.'

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
                return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.8, 1, 1, 12, 'sharp', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []

    def on_destruction(self, dead):
        if not np.any([it.x == self.owner.owner.x and it.y == self.owner.owner.y and it.name == 'glass shards' for it in self.owner.owner.world.items]):
            item.GlassShards(self.owner.owner.world.items,
                             self.owner.owner.x, self.owner.owner.y)
        super().on_destruction(dead)


class GlassElementalTail(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'glass elemental tail', '~', (0, 255, 255))
        self.categories = ['tail']
        self.childconnections = {}
        self._bottomheight = -2
        self.maxhp = 5
        self.weight = 100
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['blunt'] = -1
        self._resistances['rough'] = -1
        self._resistances['electric'] = 1
        self.nonconductive = True
        self._info = 'A tail consisting of elemental glass. Doesn\'t gain hunger and can\'t be poisoned. Very weak against blunt and rough damage, but completely resistant against electric damage and nonconductive. No smell. Breaks into glass shards when destroyed.'

    def on_destruction(self, dead):
        if not np.any([it.x == self.owner.owner.x and it.y == self.owner.owner.y and it.name == 'glass shards' for it in self.owner.owner.world.items]):
            item.GlassShards(self.owner.owner.world.items,
                             self.owner.owner.x, self.owner.owner.y)
        super().on_destruction(dead)


class OctopusHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus head', '*', (255, 0, 255))
        self.categories = ['torso']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(35)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(35)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(40), defensecoefficient=0.8, armorapplies=True, internal=True),
            'central heart': BodyPartConnection(self, ['heart'], True, 'central ', constantfunction(25), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left heart': BodyPartConnection(self, ['heart'], True, 'left ', constantfunction(20), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right heart': BodyPartConnection(self, ['heart'], True, 'right ', constantfunction(20), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left gills': BodyPartConnection(self, ['lung'], False, 'left ', constantfunction(15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right gills': BodyPartConnection(self, ['lung'], False, 'right ', constantfunction(15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left metanephridium': BodyPartConnection(self, ['kidney'], False, 'left ', constantfunction(25), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right metanephridium': BodyPartConnection(self, ['kidney'], False, 'right ', constantfunction(25), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', constantfunction(35), defensecoefficient=0.8, armorapplies=True, internal=True),
            'front left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front left ', constantfunction(0)),
            'center-front left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-front left ', constantfunction(0)),
            'center-back left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-back left ', constantfunction(0)),
            'back left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back left ', constantfunction(0)),
            'front right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front right ', constantfunction(0)),
            'center-front right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-front right ', constantfunction(0)),
            'center-back right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-back right ', constantfunction(0)),
            'back right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back right ', constantfunction(0))
        }
        self._topheight = 50
        self.upperpoorlimit = 50
        self.upperfinelimit = 30
        self.lowerfinelimit = 0
        self.lowerpoorlimit = 0
        self.maxhp = 80
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner(
            [], self), 'back': listwithowner([], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 40000
        self.carryingcapacity = 20000
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A torso (despite being called head!) consisting of living flesh.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.42, 1, 1, 15, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class OctopusTentacle(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus tentacle', '~', (255, 0, 255))
        self.categories = ['arm', 'leg', 'tentacle']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -10
        self.upperpoorlimit = 100
        self.upperfinelimit = 65
        self.lowerfinelimit = -65
        self.lowerpoorlimit = -100
        self.maxheight = 120
        self.minheight = 10
        self.maxhp = 10
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 0.75
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'tentacle'
        self.worn = {'tentacle armor': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 10000
        self.carryingcapacity = 10000
        self.carefulness = 0.4
        self.maxrunstamina = 2.5
        self.smell = 1
        self._info = 'A tentacle consisting of living flesh. Works both as an arm and as a leg. Slow at moving, but faster if there are more of them. Also faster at attacking if there are more of them. Slow and rather inaccurate at throwing. Individually very low running stamina, collectively average. Slightly clumsy.'

    def standingheight(self):
        legsnotentacles = [part for part in self.owner if 'leg' in part.categories and not 'tentacle' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        tentacles = [part for part in self.owner if 'tentacle' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legsnotentacles) > 0:
            legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
            ) and not part.incapacitated()]
            return min([leg.maxheight for leg in legs])
        else:
            return max([tentacle.minheight for tentacle in tentacles])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
                return [Attack(self.parentalconnection.prefix + 'tentacle', 'constricted', 'constricted', 'constrict', '', '', 0.82, timetaken, 1, 3, 'blunt', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class OctopusEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 7
        self.weight = 10
        self.detectiondistance = 2.9
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh. Can detect traps from farther away than most.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class OctopusBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 6
        self._bottomheight = -6
        self.maxhp = 20
        self.weight = 2000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 2
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 2, average mana capacity.'


class OctopusHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 20
        self.weight = 500
        self.bravery = 0.25
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Individually easily scared (luckily the octopus has three of them). Weak against electric damage.'


class OctopusGills(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus gills', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
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
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 20
        self.weight = 100
        self.endotoxicity = -1
        self._info = 'A kidney-like organ consisting of living flesh. Filters toxins at average speed.'


class OctopusStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cave octopus stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 10
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
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
            'front left leg': BodyPartConnection(self, ['leg'], False, 'front left ', constantfunction(0)),
            'front right leg': BodyPartConnection(self, ['leg'], False, 'front right ', constantfunction(0)),
            'back left leg': BodyPartConnection(self, ['leg'], False, 'back left ', constantfunction(0)),
            'back right leg': BodyPartConnection(self, ['leg'], False, 'back right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', constantfunction(10)),
            'heart': BodyPartConnection(self, ['heart'], True, '', constantfunction(-5), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', constantfunction(2), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', constantfunction(2), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', constantfunction(9), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', constantfunction(9), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', constantfunction(0), defensecoefficient=0.8, armorapplies=True, internal=True),
            'tail': BodyPartConnection(self, ['tail'], False, '', constantfunction(13))
        }
        self._topheight = 18
        self._bottomheight = -18
        self.maxhp = 75
        self.worn = {'barding': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 20000
        self.carryingcapacity = 20000
        self.smell = 1
        self._info = 'A torso consisting of living flesh.'


class DogLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog leg', '~', (170, 130, 70))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -54
        self.upperpoorlimit = 27
        self.upperfinelimit = -22
        self.lowerfinelimit = -54
        self.lowerpoorlimit = -54
        self.maxheight = 54
        self.maxhp = 25
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 3000
        self.carryingcapacity = 6000
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. On its own very weak at carrying. Quite fast if there are at least four legs.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.72, 1, 1, 2, 'sharp', 0, [], [], self)]
        else:
            return []


class DogHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog head', '*', (170, 130, 70))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(13)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(13)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(22), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 27
        self._bottomheight = 0
        self.upperpoorlimit = 50
        self.upperfinelimit = 27
        self.lowerfinelimit = -58
        self.lowerpoorlimit = -63
        self.maxhp = 25
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 3000
        self.smell = 1
        self.senseofsmell = 10
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Good sense of smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.82, 1, 1, 10, 'sharp', 0, [], [('bleed', 0.2)], self)]
        else:
            return []


class DogEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog eye', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 7
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class DogBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 3
        self._bottomheight = -3
        self.maxhp = 15
        self.weight = 100
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 2
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 2, average mana capacity.'


class DogHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 6
        self._bottomheight = -6
        self.maxhp = 15
        self.weight = 400
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self.godlylove = 1
        self._info = 'A heart consisting of living flesh. Average bravery. Reduces the waiting period between successful prayers, as all gods love a good dog. Weak against electric damage.'


class DogLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
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
        self._topheight = 2
        self._bottomheight = -2
        self.maxhp = 15
        self.weight = 90
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'


class DogStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dog stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 8
        self._bottomheight = -8
        self.maxhp = 15
        self.weight = 800
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
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
        self._bottomheight = -59
        self.maxhp = 7
        self.weight = 400
        self.smell = 1
        self._info = 'A tail consisting of living flesh.'


class ImpTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp torso', '*', (128, 0, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 35, 17)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 35, 17)),
            'left wing': BodyPartConnection(self, ['wing'], False, 'left ', heightfuncuprightorprone(self, 35, 25)),
            'right wing': BodyPartConnection(self, ['wing'], False, 'right ', heightfuncuprightorprone(self, 35, 25)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 40, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 30, 12), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 25, 12), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 25, 12), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 15, 12), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 15, 12), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 20, 12), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 40
        self._pronetopheight = 25
        self.maxhp = 75
        self.worn = {'chest armor': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 25000
        self.carryingcapacity = 20000
        self._resistances['fire'] = 0.2
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Resistant against fire damage.'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class ImpArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp arm', '~', (128, 0, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 30
        self.upperfinelimit = 15
        self.lowerfinelimit = -15
        self.lowerpoorlimit = -30
        self.maxhp = 25
        self.capableofthrowing = True
        self.throwaccuracy = 0.97
        self.throwspeed = 1
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._resistances['fire'] = 0.2
        self.carefulness = 0.5
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Protects other bodyparts quite well. Resistant against fire damage.'

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
                return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.82, 1, 1, 10, 'sharp', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class ImpWing(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp wing', '~', (128, 0, 0))
        self.categories = ['wing']
        self.childconnections = {}
        self._topheight = 30
        self._bottomheight = -20
        self.maxhp = 20
        self.weight = 5000
        self._resistances['fire'] = 0.2
        self.smell = 1
        self._info = 'A wing consisting of living flesh. Enables flying at a quite fast speed if there are at least two wings. Resistant against fire damage.'

    def stances(self):
        if not (self.destroyed() or self.incapacitated()) and len([part for part in self.owner if 'wing' in part.categories and not (part.destroyed() or part.incapacitated())]) > 1:
            return ['flying']
        else:
            return []

    def flyingspeed(self):
        if not (self.destroyed() or self.incapacitated()):
            return 1.5
        else:
            return 0


class ImpLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp leg', '~', (128, 0, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -70
        self.upperpoorlimit = 30
        self.upperfinelimit = -15
        self.lowerfinelimit = -70
        self.lowerpoorlimit = -70
        self.maxheight = 70
        self.maxhp = 25
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 10000
        self.carryingcapacity = 20000
        self._resistances['fire'] = 0.2
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Resistant against fire damage.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.62, 1, 1, 15, 'blunt', 0, [], [], self)]
        else:
            return []


class ImpHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp head', '*', (128, 0, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 25
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self.scariness = 7
        self._resistances['fire'] = 0.2
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Can scare enemies for up to 7 s. Resistant against fire damage.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.62, 1, 1, 15, 'sharp', 0, [], [('bleed', 0.1)], self), Attack('horns', 'gored', 'gored', 'gore', '', '', 0.82, 1, 1, 10, 'sharp', 0, [], [('charge', )], self)]
        else:
            return []


class ImpEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp eye', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 7
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class ImpBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 15
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 2
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 2, average mana capacity.'


class ImpHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 15
        self.weight = 250
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class ImpLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 15
        self.weight = 600
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh.'


class ImpKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 15
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'


class ImpStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'imp stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 15
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
        }
        self._info = 'A stomach consisting of living flesh.'


class HobgoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 40, 19)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 40, 19)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 45, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 35, 14), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 30, 14), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 30, 14), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 20, 14), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 20, 14), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 25, 14), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 45
        self._pronetopheight = 27
        self.maxhp = 100
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 35000
        self.carryingcapacity = 20000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class HobgoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -25
        self.upperpoorlimit = 35
        self.upperfinelimit = 20
        self.lowerfinelimit = -20
        self.lowerpoorlimit = -35
        self.maxhp = 30
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 1.5
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 5000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Quick but rather inaccurate at throwing. Protects other bodyparts quite well. Good at avoiding traps when crawling. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 0.84, 1, 1, 15, 'blunt', 0, [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.84, 1, 1, 15, 'sharp', 0, [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class HobgoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -75
        self.upperpoorlimit = 35
        self.upperfinelimit = -15
        self.lowerfinelimit = -75
        self.lowerpoorlimit = -75
        self.maxheight = 75
        self.maxhp = 30
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 13000
        self.carryingcapacity = 15000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Good at avoiding traps. Somewhat weak at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.64, 1, 1, 22, 'blunt', 0, [], [], self)]
        else:
            return []


class HobgoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 30
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.64, 1, 1, 22, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class HobgoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
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

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class HobgoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 20
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 3
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 3, average mana capacity.'


class HobgoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 20
        self.weight = 250
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class HobgoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
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
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 20
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'


class HobgoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hobgoblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 20
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
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
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 55, 20)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 55, 20)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 60, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 40, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 30, 15), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 60
        self._pronetopheight = 30
        self.maxhp = 100
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 50000
        self.carryingcapacity = 30000
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Good carrying capacity.'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class MoleMonkArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk arm', '~', (186, 100, 13))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 50
        self.upperfinelimit = 25
        self.lowerfinelimit = -25
        self.lowerpoorlimit = -50
        self.maxhp = 30
        self.capableofthrowing = True
        self.throwaccuracy = 0.99
        self.throwspeed = 1
        self.protectiveness = 0.2
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 7000
        self.carefulness = 0.5
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Accurate at throwing. Can be used for mining. Protects other bodyparts very well.'

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
                return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.84, 1, 1, 15, 'rough', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class MoleMonkLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk leg', '~', (186, 100, 13))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -90
        self.upperpoorlimit = 70
        self.upperfinelimit = 0
        self.lowerfinelimit = -90
        self.lowerpoorlimit = -90
        self.maxheight = 90
        self.maxhp = 30
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 17000
        self.carryingcapacity = 20000
        self.carefulness = 0.5
        self.maxrunstamina = 5
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Low running stamina.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.64, 1, 1, 22, 'blunt', 0, [], [], self)]
        else:
            return []


class MoleMonkHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk head', '*', (186, 100, 13))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 30
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.smell = 1
        self.senseofsmell = 10
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Good sense of smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.44, 1, 1, 22, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class MoleMonkEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
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

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class MoleMonkBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 20
        self.weight = 1300
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self._stances = ['fasting']
        self.frightenedby = []
        self.intelligence = 4
        self.manacapacity = 15
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 4, low mana capacity. Enables the fasting stance.'


class MoleMonkHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 20
        self.weight = 300
        self.bravery = 0.25
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Easily scared. Weak against electric damage.'


class MoleMonkLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
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
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 20
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'


class MoleMonkStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mole monk stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 20
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
        }
        self._info = 'A stomach consisting of living flesh.'


class ZombieZorcererTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer torso', '*', (191, 255, 128))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 55, 20)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 55, 20)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], False, '', heightfuncuprightorprone(self, 60, 20)),
            'heart': BodyPartConnection(self, ['heart'], False, '', heightfuncuprightorprone(self, 40, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 30, 15), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 60
        self._pronetopheight = 30
        self.maxhp = 100
        self.material = "undead flesh"
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 40000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.smell = 2
        self._info = 'A torso consisting of undead flesh. Needs neither head nor heart. Has good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class ZombieZorcererArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer arm', '~', (191, 255, 128))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 30
        self.upperfinelimit = 15
        self.lowerfinelimit = -15
        self.lowerpoorlimit = -30
        self.maxhp = 30
        self.material = "undead flesh"
        self.capableofthrowing = True
        self.throwaccuracy = 0.97
        self.throwspeed = 0.75
        self.protectiveness = 0.1
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.carefulness = 0.3
        self.smell = 2
        self._info = 'An arm consisting of undead flesh. Slow at throwing. Protects other bodyparts but not that well. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 0.8, 1, 1, 5, 'blunt', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class ZombieZorcererLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer leg', '~', (191, 255, 128))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -90
        self.upperpoorlimit = 40
        self.upperfinelimit = -15
        self.lowerfinelimit = -90
        self.lowerpoorlimit = -90
        self.maxheight = 90
        self.maxhp = 30
        self.material = "undead flesh"
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.carefulness = 0.3
        self.maxrunstamina = 20
        self.smell = 2
        self._info = 'A leg consisting of undead flesh. Quite slow and somewhat clumsy, but has good carrying capacity and high running stamina. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.6, 1, 1, 7, 'blunt', 0, [], [], self)]
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


class ZombieZorcererHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer head', '*', (191, 255, 128))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], False, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 30
        self.material = "undead flesh"
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.scariness = 7
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.smell = 2
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of undead flesh. Can scare enemies for up to 7 s. Needs no brain. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.4, 2, 1, 5, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class ZombieZorcererEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer eye', '*', (155, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 10
        self.material = "undead flesh"
        self.weight = 7
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class ZombieZorcererBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer brain', '*', (150, 178, 82))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 20
        self.material = "undead flesh"
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 2
        self.manacapacity = 25
        self.spellsknown = [np.random.choice([magic.SharpMissile, magic.BluntMissile, magic.RoughMissile, magic.FireMissile])(np.random.randint(
            1, 3)), np.random.choice([magic.CurseOfSlowness, magic.CurseOfWeakness])(np.random.randint(1, 3)), magic.HealThyself(np.random.randint(1, 3))]
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A brain consisting of undead flesh. Intelligence 2, high mana capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class ZombieZorcererHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer heart', '*', (150, 178, 82))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 20
        self.material = "undead flesh"
        self.weight = 250
        self.bravery = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A heart consisting of undead flesh. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage. In the presence of living body parts, accumulates endotoxins.'


class ZombieZorcererLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer lung', '*', (150, 178, 82))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 20
        self.material = 'undead flesh'
        self.weight = 500
        self.runstaminarecoveryspeed = 0.25
        self.breathepoisonresistance = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A lung consisting of undead flesh. Protects living bodyparts from poison gas quite well. Recovers running stamina slowly. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class ZombieZorcererKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer kidney', '*', (150, 178, 82))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 20
        self.material = 'undead flesh'
        self.weight = 100
        self._attackpoisonresistance = 1
        self.endotoxicity = -0.5
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A kidney consisting of undead flesh. Filters toxins at a slow speed. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage.'


class ZombieZorcererStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'zombie zorcerer stomach', '*', (150, 178, 82))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 20
        self.material = "undead flesh"
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'vegetables': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'living flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'undead flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.')
        }
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A stomach consisting of undead flesh. Inefficient at processing food. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class WolfTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf torso', '*', (100, 100, 150))
        self.categories = ['torso']
        self.childconnections = {
            'front left leg': BodyPartConnection(self, ['leg'], False, 'front left ', constantfunction(0)),
            'front right leg': BodyPartConnection(self, ['leg'], False, 'front right ', constantfunction(0)),
            'back left leg': BodyPartConnection(self, ['leg'], False, 'back left ', constantfunction(0)),
            'back right leg': BodyPartConnection(self, ['leg'], False, 'back right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', constantfunction(12)),
            'heart': BodyPartConnection(self, ['heart'], True, '', constantfunction(-5), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', constantfunction(2), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', constantfunction(2), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', constantfunction(10), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', constantfunction(10), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', constantfunction(0), defensecoefficient=0.8, armorapplies=True, internal=True),
            'tail': BodyPartConnection(self, ['tail'], False, '', constantfunction(15))
        }
        self._topheight = 20
        self._bottomheight = -20
        self.maxhp = 150
        self.worn = {'barding': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 25000
        self.carryingcapacity = 25000
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Rather strong at carrying.'


class WolfLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf leg', '~', (100, 100, 150))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -60
        self.upperpoorlimit = 30
        self.upperfinelimit = -25
        self.lowerfinelimit = -60
        self.lowerpoorlimit = -60
        self.maxheight = 60
        self.maxhp = 30
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 4000
        self.carryingcapacity = 7500
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. On its own rather weak at carrying. Very fast if there are at least four legs, and quite fast even when there are two.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.76, 1, 1, 5, 'sharp', 0, [], [], self)]
        else:
            return []


class WolfHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf head', '*', (100, 100, 150))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(15)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(15)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(24), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 55
        self.upperfinelimit = 30
        self.lowerfinelimit = -65
        self.lowerpoorlimit = -70
        self.maxhp = 30
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 4000
        self.smell = 1
        self.senseofsmell = 10
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Good sense of smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.86, 1, 1, 20, 'sharp', 0, [], [('bleed', 0.2)], self)]
        else:
            return []


class WolfEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf eye', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 12
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh. Sees farther than most.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 4
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class WolfBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 3
        self._bottomheight = -3
        self.maxhp = 20
        self.weight = 120
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 4
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 4, average mana capacity.'


class WolfHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 6
        self._bottomheight = -6
        self.maxhp = 20
        self.weight = 500
        self.bravery = 0.75
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Very brave. Weak against electric damage.'


class WolfLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 8
        self._bottomheight = -8
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
        self._topheight = 2
        self._bottomheight = -2
        self.maxhp = 20
        self.weight = 95
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'


class WolfStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wolf stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 9
        self._bottomheight = -9
        self.maxhp = 20
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
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
        self._bottomheight = -65
        self.maxhp = 20
        self.weight = 500
        self.smell = 1
        self._info = 'A tail consisting of living flesh.'


class DrillbotChassis(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'drillbot chassis', '*', (150, 150, 150))
        self.categories = ['torso']
        self.childconnections = {
            'front left wheel': BodyPartConnection(self, ['leg'], False, 'front left ', constantfunction(0)),
            'front right wheel': BodyPartConnection(self, ['leg'], False, 'front right ', constantfunction(0)),
            'back left wheel': BodyPartConnection(self, ['leg'], False, 'back left ', constantfunction(0)),
            'back right wheel': BodyPartConnection(self, ['leg'], False, 'back right ', constantfunction(0)),
            'arm': BodyPartConnection(self, ['arm'], False, '', constantfunction(50)),
            'coolant pumping system': BodyPartConnection(self, ['heart'], True, '', constantfunction(25), defensecoefficient=0.5, armorapplies=True, internal=True),
            'coolant aerator system': BodyPartConnection(self, ['lung'], False, '', constantfunction(25), defensecoefficient=0.5, armorapplies=True, internal=True),
            'coolant filtering system': BodyPartConnection(self, ['kidney'], False, '', constantfunction(25), defensecoefficient=0.5, armorapplies=True, internal=True),
            'biomass processor': BodyPartConnection(self, ['stomach'], False, '', constantfunction(25), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left camera': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(45)),
            'right camera': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(45)),
            'central processor': BodyPartConnection(self, ['brain'], True, '', constantfunction(30), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 50
        self.maxhp = 150
        self.worn = {'barding': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'chassis'
        self.weight = 30000
        self.carryingcapacity = 50000
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self._resistances['electric'] = -0.2
        self.hearing = 1
        self.sound = 1
        self._info = 'A torso consisting of electronics. Has very good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp damage, but weak against electric damage. No smell.'


class DrillbotWheel(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'drillbot wheel', '*', (150, 150, 150))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 40
        self._bottomheight = -40
        self.maxheight = 40
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
        self._resistances['electric'] = 1
        self.nonconductive = True
        self.carefulness = 0.5
        self.maxrunstamina = 20
        self._info = 'A leg-like organ consisting of electronics. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against electric damage and nonconductive, but very weak against sharp and rough damage. Very fast if there are at least four legs or wheels, and quite fast even when there are two. High "running" stamina. No smell.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 50
        self.upperfinelimit = 50
        self.lowerfinelimit = -50
        self.lowerpoorlimit = -50
        self.maxhp = 40
        self.weight = 7000
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self._resistances['electric'] = -0.2
        self._info = 'A dual-purpose pneumatic drill arm consisting of electronics. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp damage, but weak against electric damage. Can directly attack internal organs. Can be used for mining. No smell.'

    def minespeed(self):
        return 0.5

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'drill', 'drilled', 'drilled', 'drill', '', '', 0.88, 1, 1, 25, 'rough', 0, [], [('bleed', 0.2), ('internals-seeking',)], self)]
        else:
            return []


class DrillbotCamera(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'drillbot camera', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 15
        self.weight = 20
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self._resistances['electric'] = -0.2
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of electronics. Good at detecting traps. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp damage, but weak against electric damage.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 4
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class DrillbotPump(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'coolant pump, model DB-100', '*', (0, 0, 255))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 30
        self.weight = 1500
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of electronics. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp damage, but weak against electric damage.'


class DrillbotAerator(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'coolant aerator, model DB-100', '*', (0, 0, 255))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 30
        self.weight = 600
        self.material = 'electronics'
        self._attackpoisonresistance = 1
        self.breathepoisonresistance = 0.5
        self.runstaminarecoveryspeed = 1
        self._resistances['sharp'] = 0.2
        self._resistances['electric'] = -0.2
        self._info = 'A lung consisting of electronics. Doesn\'t gain hunger and can\'t be poisoned. Protects living bodyparts from poison gas quite well. Recovers running stamina quickly. Resistant against sharp damage, but weak against electric damage.'


class DrillbotFilter(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'coolant filter, model DB-100', '*', (0, 0, 255))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 30
        self.weight = 600
        self.material = 'electronics'
        self._attackpoisonresistance = 1
        self.endotoxicity = -1
        self._resistances['sharp'] = 0.2
        self._resistances['electric'] = -0.2
        self._info = 'A kidney consisting of electronics. Doesn\'t gain hunger and can\'t be poisoned. Filters toxins at an average speed. Resistant against sharp damage, but weak against electric damage.'


class DrillbotProcessor(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'tactical processor, model DB-100', '*', (255, 255, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 30
        self.weight = 2000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 6
        self.manacapacity = 15
        self.spellsknown = []
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self._resistances['electric'] = -0.2
        self._info = 'A brain consisting of electronics. Intelligence 6, low mana capacity. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp damage, but weak against electric damage.'


class DrillBotBiomassProcessor(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'drillbot biomass processor', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 30
        self.weight = 2000
        self.material = 'electronics'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['sharp'] = 0.2
        self._resistances['electric'] = -0.2
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (1, 1, None),
            'undead flesh': (1, 1, None)
        }
        self._info = 'A stomach consisting of electronics. Processes everything even somewhat edible perfectly. Doesn\'t gain hunger and can\'t be poisoned. Resistant against sharp damage, but weak against electric damage.'


class LobgoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 45, 20)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 45, 20)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 50, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 40, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 35, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 35, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 30, 15), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 50
        self._pronetopheight = 30
        self.maxhp = 150
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 45000
        self.carryingcapacity = 25000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Rather strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class LobgoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -30
        self.upperpoorlimit = 40
        self.upperfinelimit = 25
        self.lowerfinelimit = -25
        self.lowerpoorlimit = -40
        self.maxhp = 40
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 1.5
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Quick but rather inaccurate at throwing. Protects other bodyparts quite well. Good at avoiding traps when crawling. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 0.9, 1, 1, 25, 'blunt', 0, [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.9, 1, 1, 25, 'sharp', 0, [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class LobgoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -80
        self.upperpoorlimit = 40
        self.upperfinelimit = -15
        self.lowerfinelimit = -80
        self.lowerpoorlimit = -80
        self.maxheight = 80
        self.maxhp = 40
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 16000
        self.carryingcapacity = 20000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Good at avoiding traps. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.7, 1, 1, 37, 'blunt', 0, [], [], self)]
        else:
            return []


class LobgoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 40
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.7, 1, 1, 37, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class LobgoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 15
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of living flesh. Good at detecting traps.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class LobgoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 30
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 5
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 5, average mana capacity.'


class LobgoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 30
        self.weight = 250
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class LobgoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 30
        self.weight = 600
        self.breathepoisonresistance = 0.2
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh. Some protection against poison gas.'


class LobgoblinKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 30
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'


class LobgoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'lobgoblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 30
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
        }
        self._info = 'A stomach consisting of living flesh.'


class RevenantOctopusHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'revenant cave octopus head', '*', (255, 0, 255))
        self.categories = ['torso']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(35)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(35)),
            'brain': BodyPartConnection(self, ['brain'], False, '', constantfunction(40), defensecoefficient=0.8, armorapplies=True, internal=True),
            'central heart': BodyPartConnection(self, ['heart'], False, 'central ', constantfunction(25), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left heart': BodyPartConnection(self, ['heart'], False, 'left ', constantfunction(20), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right heart': BodyPartConnection(self, ['heart'], False, 'right ', constantfunction(20), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left gills': BodyPartConnection(self, ['lung'], False, 'left ', constantfunction(15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right gills': BodyPartConnection(self, ['lung'], False, 'right ', constantfunction(15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left metanephridium': BodyPartConnection(self, ['kidney'], False, 'left ', constantfunction(25), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right metanephridium': BodyPartConnection(self, ['kidney'], False, 'right ', constantfunction(25), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', constantfunction(35), defensecoefficient=0.8, armorapplies=True, internal=True),
            'front left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front left ', constantfunction(0)),
            'center-front left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-front left ', constantfunction(0)),
            'center-back left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-back left ', constantfunction(0)),
            'back left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back left ', constantfunction(0)),
            'front right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front right ', constantfunction(0)),
            'center-front right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-front right ', constantfunction(0)),
            'center-back right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'center-back right ', constantfunction(0)),
            'back right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back right ', constantfunction(0))
        }
        self._topheight = 50
        self.upperpoorlimit = 50
        self.upperfinelimit = 30
        self.lowerfinelimit = 0
        self.lowerpoorlimit = 0
        self.maxhp = 160
        self.material = "undead flesh"
        self.worn = {'helmet': listwithowner([], self), 'face': listwithowner(
            [], self), 'back': listwithowner([], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 40000
        self.carryingcapacity = 20000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.smell = 2
        self.hearing = 1
        self.sound = 1
        self._info = 'A torso (despite being called head!) consisting of undead flesh. Needs neither brain nor hearts. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.5, 1, 1, 37, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class RevenantOctopusTentacle(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'revenant cave octopus tentacle', '~', (255, 0, 255))
        self.categories = ['arm', 'leg', 'tentacle']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -10
        self.upperpoorlimit = 100
        self.upperfinelimit = 65
        self.lowerfinelimit = -65
        self.lowerpoorlimit = -100
        self.maxheight = 120
        self.minheight = 10
        self.maxhp = 30
        self.material = "undead flesh"
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 0.75
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'tentacle'
        self.worn = {'tentacle armor': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 10000
        self.carryingcapacity = 10000
        self.carefulness = 0.4
        self.maxrunstamina = 2.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.carefulness = 0.3
        self.smell = 2
        self._info = 'A tentacle consisting of undead flesh. Works both as an arm and as a leg. Slow at moving, but faster if there are more of them. Also faster at attacking if there are more of them. Slow and rather inaccurate at throwing. Individually very low running stamina, collectively average. Slightly clumsy. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def standingheight(self):
        legsnotentacles = [part for part in self.owner if 'leg' in part.categories and not 'tentacle' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        tentacles = [part for part in self.owner if 'tentacle' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legsnotentacles) > 0:
            legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
            ) and not part.incapacitated()]
            return min([leg.maxheight for leg in legs])
        else:
            return max([tentacle.minheight for tentacle in tentacles])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
                return [Attack(self.parentalconnection.prefix + 'tentacle', 'constricted', 'constricted', 'constrict', '', '', 0.9, timetaken, 1, 13, 'blunt', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class RevenantOctopusEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'revenant cave octopus eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 15
        self.material = "undead flesh"
        self.weight = 10
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.detectiondistance = 2.9
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of undead flesh. Can detect traps from farther away than most. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class RevenantOctopusBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'revenant cave octopus brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 6
        self._bottomheight = -6
        self.maxhp = 30
        self.material = "undead flesh"
        self.weight = 2000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 4
        self.manacapacity = 25
        self.spellsknown = []
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A brain consisting of undead flesh. Intelligence 4, high mana capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class RevenantOctopusHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'revenant cave octopus heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 30
        self.material = "undead flesh"
        self.weight = 500
        self.bravery = 0.25
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A heart consisting of undead flesh. Individually easily scared (luckily the octopus has three of them). Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage. In the presence of living body parts, accumulates endotoxins.'


class RevenantOctopusGills(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'revenant cave octopus gills', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 30
        self.material = 'undead flesh'
        self.weight = 500
        self.breathepoisonresistance = 0.5
        self.runstaminarecoveryspeed = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A lung-like organ consisting of undead flesh. Protects living bodyparts from poison gas quite well. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class RevenantOctopusMetanephridium(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'revenant cave octopus metanephridium', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 30
        self.material = 'undead flesh'
        self.weight = 100
        self._attackpoisonresistance = 1
        self.endotoxicity = -0.5
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A kidney-like organ consisting of undead flesh. Filters toxins at a slow speed. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage.'


class RevenantOctopusStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'revenant cave octopus stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 10
        self.material = 'undead flesh'
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'vegetables': (-1,),
            'living flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'undead flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.')
        }
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A hypercarnivorous stomach consisting of undead flesh. Inefficient at processing food. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class GhoulTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul torso', '*', (191, 255, 255))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 55, 20)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 55, 20)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], False, '', heightfuncuprightorprone(self, 60, 20)),
            'heart': BodyPartConnection(self, ['heart'], False, '', heightfuncuprightorprone(self, 40, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 30, 15), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 60
        self._pronetopheight = 30
        self.maxhp = 175
        self.material = "undead flesh"
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 40000
        self.carryingcapacity = 60000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.smell = 2
        self._info = 'A torso consisting of undead flesh. Needs neither head nor heart. Has extremely good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class GhoulArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul arm', '~', (191, 255, 255))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 30
        self.upperfinelimit = 15
        self.lowerfinelimit = -15
        self.lowerpoorlimit = -30
        self.maxhp = 50
        self.material = "undead flesh"
        self.capableofthrowing = True
        self.throwaccuracy = 0.97
        self.throwspeed = 0.75
        self.protectiveness = 0.1
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.carefulness = 0.3
        self.smell = 2
        self._info = 'An arm consisting of undead flesh. Slow at throwing. Protects other bodyparts but not that well. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 0.92, 1, 1, 30, 'blunt', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class GhoulLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul leg', '~', (191, 255, 255))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -90
        self.upperpoorlimit = 40
        self.upperfinelimit = -15
        self.lowerfinelimit = -90
        self.lowerpoorlimit = -90
        self.maxheight = 90
        self.maxhp = 50
        self.material = "undead flesh"
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.carefulness = 0.3
        self.maxrunstamina = 20
        self.smell = 2
        self._info = 'A leg consisting of undead flesh. Somewhat clumsy, but has good carrying capacity and high running stamina. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.72, 1, 1, 45, 'blunt', 0, [], [], self)]
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
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], False, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 50
        self.material = "undead flesh"
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.scariness = 10
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.smell = 2
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of undead flesh. Can scare enemies for up to 10 s. Needs no brain. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.52, 2, 1, 30, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class GhoulEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul eye', '*', (155, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 17
        self.material = "undead flesh"
        self.weight = 7
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class GhoulBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul brain', '*', (150, 178, 82))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 25
        self.material = "undead flesh"
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 5
        self.manacapacity = 25
        self.spellsknown = []
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A brain consisting of undead flesh. Intelligence 5, high mana capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class GhoulHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul heart', '*', (150, 178, 82))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 25
        self.material = "undead flesh"
        self.weight = 250
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self.bravery = 0.5
        self._info = 'A heart consisting of undead flesh. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage. In the presence of living body parts, accumulates endotoxins.'


class GhoulLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul lung', '*', (150, 178, 82))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 25
        self.material = 'undead flesh'
        self.weight = 600
        self.breathepoisonresistance = 0.5
        self.runstaminarecoveryspeed = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._info = 'A lung consisting of undead flesh. Protects living bodyparts from poison gas quite well. Recovers running stamina slowly. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class GhoulKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul kidney', '*', (150, 178, 82))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 25
        self.material = 'undead flesh'
        self.weight = 120
        self._attackpoisonresistance = 1
        self.endotoxicity = -0.5
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A kidney consisting of undead flesh. Filters toxins at a slow speed. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage.'


class GhoulStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghoul stomach', '*', (150, 178, 82))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 25
        self.material = "undead flesh"
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'vegetables': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'living flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'undead flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.')
        }
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A stomach consisting of undead flesh. Inefficient at processing food. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class SmallFireElementalTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental torso', '*', (255, 204, 0))
        self.categories = ['torso']
        self.childconnections = {
            'head': BodyPartConnection(self, ['head'], True, '', constantfunction(100)),
            'heart': BodyPartConnection(self, ['heart'], True, '', constantfunction(50), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left bellows': BodyPartConnection(self, ['lung'], False, 'left ', constantfunction(70), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right bellows': BodyPartConnection(self, ['lung'], False, 'right ', constantfunction(70), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', constantfunction(30), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', constantfunction(30), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', constantfunction(60), defensecoefficient=0.8, armorapplies=True, internal=True),
            'front left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front left ', constantfunction(0)),
            'back left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back left ', constantfunction(0)),
            'front right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front right ', constantfunction(0)),
            'back right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back right ', constantfunction(0))
        }
        self._topheight = 100
        self.maxhp = 200
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 400
        self.carryingcapacity = 60000
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self._info = 'A torso consisting of elemental fire. Has extremely good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage. No smell.'


class SmallFireElementalHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental head', '*', (255, 204, 0))
        self.categories = ['head']
        self.childconnections = {
            'eye': BodyPartConnection(self, ['eye'], False, '', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.maxhp = 55
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 100
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of elemental fire. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage. No smell.'


class SmallFireElementalEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ember eye', '*', (255, 204, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 3
        self._bottomheight = -3
        self.maxhp = 20
        self.weight = 0
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of elemental fire. Sees much farther than most, and is rather good at detecting traps. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 5
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class SmallFireElementalBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental brain', '*', (255, 204, 0))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 30
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 10
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 7
        self.manacapacity = 20
        self.spellsknown = [magic.FireMissile(np.random.randint(1, 8))]
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self._info = 'A brain consisting of elemental fire. Intelligence 7, average mana capacity. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage.'


class SmallFireElementalHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fiery heart', '*', (255, 204, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 30
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 10
        self.bravery = 0.5
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.2
        self._info = 'A heart consisting of elemental fire. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and resistant against electric damage.'


class SmallFireElementalBellows(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental bellows', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 30
        self.material = 'elemental'
        self.weight = 600
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self._info = 'A lung consisting of elemental fire. Doesn\'t gain hunger and can\'t be poisoned, but doesn\'t protect living body parts from poison gas. Completely resistant against fire damage, and very resistant against electric damage.'


class SmallFireElementalTentacle(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'small fire elemental tentacle', '~', (255, 204, 0))
        self.categories = ['arm', 'leg', 'tentacle']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -10
        self.upperpoorlimit = 150
        self.upperfinelimit = 100
        self.lowerfinelimit = -100
        self.lowerpoorlimit = -150
        self.maxheight = 200
        self.minheight = 20
        self.maxhp = 40
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 0.75
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'tentacle'
        self.worn = {'tentacle armor': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 100
        self.carryingcapacity = 20000
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self._info = 'A tentacle consisting of elemental fire. Works both as an arm and as a leg. Faster at moving and attacking if there are more of them. Slow and rather inaccurate at throwing. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage. No smell.'

    def standingheight(self):
        legsnotentacles = [part for part in self.owner if 'leg' in part.categories and not 'tentacle' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        tentacles = [part for part in self.owner if 'tentacle' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legsnotentacles) > 0:
            legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
            ) and not part.incapacitated()]
            return min([leg.maxheight for leg in legs])
        else:
            return max([tentacle.minheight for tentacle in tentacles])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
                return [Attack(self.parentalconnection.prefix + 'tentacle burn', 'burned', 'burned', 'burn', '', '', 0.94, timetaken, 1, 17, 'fire', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class MobgoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 50, 21)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 50, 21)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 55, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 45, 16), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 40, 16), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 40, 16), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 30, 16), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 30, 16), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 35, 16), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 55
        self._pronetopheight = 32
        self.maxhp = 200
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 50000
        self.carryingcapacity = 25000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Rather strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class MobgoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -35
        self.upperpoorlimit = 45
        self.upperfinelimit = 30
        self.lowerfinelimit = -30
        self.lowerpoorlimit = -45
        self.maxhp = 50
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 1.5
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 7000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Quick but rather inaccurate at throwing. Protects other bodyparts quite well. Good at avoiding traps when crawling. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 0.94, 1, 1, 35, 'blunt', 0, [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.94, 1, 1, 35, 'sharp', 0, [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class MobgoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -85
        self.upperpoorlimit = 45
        self.upperfinelimit = -15
        self.lowerfinelimit = -85
        self.lowerpoorlimit = -85
        self.maxheight = 85
        self.maxhp = 50
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 17000
        self.carryingcapacity = 20000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Good at avoiding traps. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.74, 1, 1, 52, 'blunt', 0, [], [], self)]
        else:
            return []


class MobgoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 50
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.74, 1, 1, 52, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class MobgoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
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

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class MobgoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 40
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 7
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 7, average mana capacity.'


class MobgoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 40
        self.weight = 250
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class MobgoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 40
        self.weight = 600
        self.breathepoisonresistance = 0.2
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh. Some protection against poison gas.'


class MobgoblinKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 40
        self.weight = 120
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at average speed.'


class MobgoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mobgoblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 40
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
        }
        self._info = 'A stomach consisting of living flesh.'


class DireWolfTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf torso', '*', (100, 100, 150))
        self.categories = ['torso']
        self.childconnections = {
            'front left leg': BodyPartConnection(self, ['leg'], False, 'front left ', constantfunction(0)),
            'front right leg': BodyPartConnection(self, ['leg'], False, 'front right ', constantfunction(0)),
            'back left leg': BodyPartConnection(self, ['leg'], False, 'back left ', constantfunction(0)),
            'back right leg': BodyPartConnection(self, ['leg'], False, 'back right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', constantfunction(13)),
            'heart': BodyPartConnection(self, ['heart'], True, '', constantfunction(-5), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', constantfunction(2), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', constantfunction(2), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', constantfunction(11), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', constantfunction(11), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', constantfunction(0), defensecoefficient=0.8, armorapplies=True, internal=True),
            'tail': BodyPartConnection(self, ['tail'], False, '', constantfunction(17))
        }
        self._topheight = 22
        self._bottomheight = -22
        self.maxhp = 225
        self.worn = {'barding': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 35000
        self.carryingcapacity = 40000
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Very strong at carrying.'


class DireWolfLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf leg', '~', (100, 100, 150))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -66
        self.upperpoorlimit = 33
        self.upperfinelimit = -28
        self.lowerfinelimit = -66
        self.lowerpoorlimit = -66
        self.maxheight = 66
        self.maxhp = 60
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 6000
        self.carryingcapacity = 10000
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. On its own somewhat weak at carrying. Very fast if there are at least four legs, and quite fast even when there are two.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.86, 1, 1, 10, 'sharp', 0, [], [], self)]
        else:
            return []


class DireWolfHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf head', '*', (100, 100, 150))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(17)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(17)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(27), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 33
        self._bottomheight = 0
        self.upperpoorlimit = 60
        self.upperfinelimit = 33
        self.lowerfinelimit = -72
        self.lowerpoorlimit = -77
        self.maxhp = 60
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self.smell = 1
        self.senseofsmell = 10
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Good sense of smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.96, 1, 1, 40, 'sharp', 0, [], [('bleed', 0.2)], self)]
        else:
            return []


class DireWolfEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf eye', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 22
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh. Sees farther than most.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 4
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class DireWolfBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 3
        self._bottomheight = -3
        self.maxhp = 45
        self.weight = 120
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 8
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 8, average mana capacity.'


class DireWolfHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 45
        self.weight = 700
        self.bravery = 0.75
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Very brave. Weak against electric damage.'


class DireWolfLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 9
        self._bottomheight = -9
        self.maxhp = 45
        self.weight = 800
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh.'


class DireWolfKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 2
        self._bottomheight = -2
        self.maxhp = 45
        self.weight = 160
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'


class DireWolfStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dire wolf stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 9
        self._bottomheight = -9
        self.maxhp = 45
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
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
        self._bottomheight = -72
        self.maxhp = 45
        self.weight = 600
        self.smell = 1
        self._info = 'A tail consisting of living flesh.'


class JobgoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 55, 22)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 55, 22)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 60, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 50, 17), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 45, 17), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 45, 17), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 35, 17), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 35, 17), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 40, 17), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 60
        self._pronetopheight = 34
        self.maxhp = 250
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 55000
        self.carryingcapacity = 30000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class JobgoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -40
        self.upperpoorlimit = 50
        self.upperfinelimit = 35
        self.lowerfinelimit = -35
        self.lowerpoorlimit = -50
        self.maxhp = 60
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 1.5
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 8000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Quick but rather inaccurate at throwing. Protects other bodyparts quite well. Good at avoiding traps when crawling. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 0.98, 1, 1, 45, 'blunt', 0, [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.98, 1, 1, 45, 'sharp', 0, [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class JobgoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -90
        self.upperpoorlimit = 50
        self.upperfinelimit = -15
        self.lowerfinelimit = -90
        self.lowerpoorlimit = -90
        self.maxheight = 90
        self.maxhp = 60
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 18000
        self.carryingcapacity = 25000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Good at avoiding traps. Rather strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.78, 1, 1, 67, 'blunt', 0, [], [], self)]
        else:
            return []


class JobgoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 60
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.78, 1, 1, 67, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class JobgoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 25
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of living flesh. Good at detecting traps.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class JobgoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 50
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 9
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 9, average mana capacity.'


class JobgoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 50
        self.weight = 300
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class JobgoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 50
        self.weight = 600
        self.breathepoisonresistance = 0.2
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh. Some protection against poison gas.'


class JobgoblinKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 50
        self.weight = 100
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'


class JobgoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 50
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
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
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 55, 20)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 55, 20)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], False, '', heightfuncuprightorprone(self, 60, 20)),
            'heart': BodyPartConnection(self, ['heart'], False, '', heightfuncuprightorprone(self, 40, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 45, 15), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 25, 15), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 30, 15), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 60
        self._pronetopheight = 30
        self.maxhp = 275
        self.material = "undead flesh"
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 40000
        self.carryingcapacity = 60000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.smell = 2
        self._info = 'A torso consisting of undead flesh. Needs neither head nor heart. Has extremely good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class GhastArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast arm', '~', (191, 255, 255))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -20
        self.upperpoorlimit = 30
        self.upperfinelimit = 15
        self.lowerfinelimit = -15
        self.lowerpoorlimit = -30
        self.maxhp = 65
        self.material = "undead flesh"
        self.capableofthrowing = True
        self.throwaccuracy = 0.97
        self.throwspeed = 0.75
        self.protectiveness = 0.1
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 4000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.carefulness = 0.3
        self.smell = 2
        self._info = 'An arm consisting of undead flesh. Slow at throwing. Protects other bodyparts but not that well. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 1.0, 1, 1, 50, 'blunt', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class GhastLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast leg', '~', (191, 255, 255))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -90
        self.upperpoorlimit = 40
        self.upperfinelimit = -15
        self.lowerfinelimit = -90
        self.lowerpoorlimit = -90
        self.maxheight = 90
        self.maxhp = 65
        self.material = "undead flesh"
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 15000
        self.carryingcapacity = 30000
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.carefulness = 0.3
        self.maxrunstamina = 20
        self.smell = 2
        self._info = 'A leg consisting of undead flesh. Somewhat clumsy, but has good carrying capacity and high running stamina. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.8, 1, 1, 75, 'blunt', 0, [], [], self)]
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
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], False, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 65
        self.material = "undead flesh"
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 7000
        self.scariness = 15
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.smell = 2
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of undead flesh. Can scare enemies for up to 15 s. Needs no brain. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins. Strong smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.6, 2, 1, 50, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class GhastEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast eye', '*', (155, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 27
        self.material = "undead flesh"
        self.weight = 7
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.detectiondistance = 1.5
        self.detectionprobability = 0.1
        self._info = 'An eye consisting of undead flesh. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class GhastBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast brain', '*', (150, 178, 82))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 55
        self.material = "undead flesh"
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 9
        self.manacapacity = 25
        self.spellsknown = []
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A brain consisting of undead flesh. Intelligence 9, high mana capacity. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class GhastHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast heart', '*', (150, 178, 82))
        self.categories = ['heart']
        self.childconnections = {}
        self.maxhp = 55
        self.material = "undead flesh"
        self._topheight = 5
        self._bottomheight = -5
        self.weight = 250
        self.bravery = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._info = 'A heart consisting of undead flesh. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage. In the presence of living body parts, accumulates endotoxins.'


class GhastLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast lung', '*', (150, 178, 82))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 55
        self.material = 'undead flesh'
        self.weight = 600
        self.breathepoisonresistance = 0.5
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self.runstaminarecoveryspeed = 0.25
        self._info = 'A lung consisting of undead flesh. Protects living bodyparts from poison gas quite well. Recovers running stamina slowly. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class GhastKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast kidney', '*', (150, 178, 82))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 55
        self.material = 'undead flesh'
        self.weight = 120
        self._attackpoisonresistance = 1
        self.endotoxicity = -0.5
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A kidney consisting of undead flesh. Filters toxins at a slow speed. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage.'


class GhastStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ghast stomach', '*', (150, 178, 82))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 55
        self.material = "undead flesh"
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'vegetables': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'living flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.'),
            'undead flesh': (1, 0.5, 'Your undead stomach isn\'t very efficient at processing food.')
        }
        self._attackpoisonresistance = 1
        self.endotoxicity = 0.25
        self._resistances['sharp'] = -0.2
        self._resistances['electric'] = 0.2
        self._info = 'A stomach consisting of undead flesh. Inefficient at processing food. Doesn\'t gain hunger and can\'t be poisoned. Weak against sharp damage, but resistant against electric damage. In the presence of living body parts, accumulates endotoxins.'


class NobgoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nobgoblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 60, 23)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 60, 23)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 65, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 55, 18), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 50, 18), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 50, 18), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 40, 18), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 40, 18), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 45, 18), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 65
        self._pronetopheight = 36
        self.maxhp = 300
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 60000
        self.carryingcapacity = 30000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class NobgoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nobgoblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -45
        self.upperpoorlimit = 55
        self.upperfinelimit = 40
        self.lowerfinelimit = -40
        self.lowerpoorlimit = -55
        self.maxhp = 70
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 1.5
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 9000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Quick but rather inaccurate at throwing. Protects other bodyparts quite well. Good at avoiding traps when crawling. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 1.02, 1, 1, 55, 'blunt', 0, [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 1.02, 1, 1, 55, 'sharp', 0, [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class NobgoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nobgoblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -95
        self.upperpoorlimit = 55
        self.upperfinelimit = -15
        self.lowerfinelimit = -95
        self.lowerpoorlimit = -95
        self.maxheight = 95
        self.maxhp = 70
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 19000
        self.carryingcapacity = 25000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Good at avoiding traps. Rather strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.82, 1, 1, 82, 'blunt', 0, [], [], self)]
        else:
            return []


class NobgoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nobgoblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 70
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.82, 1, 1, 82, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class NobgoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nobgoblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 30
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of living flesh. Good at detecting traps.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class NobgoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nobgoblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 60
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 11
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 11, average mana capacity.'


class NobgoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'jobgoblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 60
        self.weight = 300
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class NobgoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nobgoblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 60
        self.weight = 600
        self.breathepoisonresistance = 0.2
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh. Some protection against poison gas.'


class NobgoblinKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nobgoblin kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 60
        self.weight = 100
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'


class NobgoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nobgoblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 60
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
        }
        self._info = 'A stomach consisting of living flesh.'


class WargTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg torso', '*', (150, 150, 200))
        self.categories = ['torso']
        self.childconnections = {
            'front left leg': BodyPartConnection(self, ['leg'], False, 'front left ', constantfunction(0)),
            'front right leg': BodyPartConnection(self, ['leg'], False, 'front right ', constantfunction(0)),
            'back left leg': BodyPartConnection(self, ['leg'], False, 'back left ', constantfunction(0)),
            'back right leg': BodyPartConnection(self, ['leg'], False, 'back right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', constantfunction(15)),
            'heart': BodyPartConnection(self, ['heart'], True, '', constantfunction(-6), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', constantfunction(2), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', constantfunction(2), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', constantfunction(13), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', constantfunction(13), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', constantfunction(0), defensecoefficient=0.8, armorapplies=True, internal=True),
            'tail': BodyPartConnection(self, ['tail'], False, '', constantfunction(20))
        }
        self._topheight = 25
        self._bottomheight = -25
        self.maxhp = 325
        self.worn = {'barding': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 50000
        self.carryingcapacity = 60000
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Extremely strong at carrying.'


class WargLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg leg', '~', (150, 150, 200))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -76
        self.upperpoorlimit = 38
        self.upperfinelimit = -32
        self.lowerfinelimit = -76
        self.lowerpoorlimit = -76
        self.maxheight = 76
        self.maxhp = 90
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 9000
        self.carryingcapacity = 15000
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. On its own somewhat weak at carrying. Very fast if there are at least four legs, and quite fast even when there are two.'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 0.86, 1, 1, 12, 'sharp', 0, [], [], self)]
        else:
            return []


class WargHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg head', '*', (150, 150, 200))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(31), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 38
        self._bottomheight = 0
        self.upperpoorlimit = 69
        self.upperfinelimit = 38
        self.lowerfinelimit = -83
        self.lowerpoorlimit = -89
        self.maxhp = 90
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 9000
        self.smell = 1
        self.senseofsmell = 10
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Good sense of smell.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.96, 1, 1, 60, 'sharp', 0, [], [('bleed', 0.2)], self)]
        else:
            return []


class WargEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg eye', '*', (255, 255, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 32
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of living flesh. Sees farther than most.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 4
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class WargBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 3
        self._bottomheight = -3
        self.maxhp = 65
        self.weight = 120
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 12
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 12, average mana capacity.'


class WargHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 65
        self.weight = 700
        self.bravery = 0.75
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Very brave. Weak against electric damage.'


class WargLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 65
        self.weight = 1000
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh.'


class WargKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 2
        self._bottomheight = -2
        self.maxhp = 65
        self.weight = 160
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'


class WargStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 9
        self._bottomheight = -9
        self.maxhp = 65
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 0.25, 'Your carnivorous stomach is very poor at processing vegetables.'),
            'living flesh': (1, 1, None),
            'undead flesh': (-1,)
        }
        self._info = 'A stomach consisting of living flesh. Very poor at processing vegetables.'


class WargTail(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'warg tail', '~', (150, 150, 200))
        self.categories = ['tail']
        self.childconnections = {}
        self._bottomheight = -83
        self.maxhp = 65
        self.weight = 900
        self.smell = 1
        self._info = 'A tail consisting of living flesh.'


class FobgoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 65, 24)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 65, 24)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 70, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 60, 19), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 55, 19), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 55, 19), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 45, 19), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 45, 19), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 50, 19), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 70
        self._pronetopheight = 38
        self.maxhp = 350
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 65000
        self.carryingcapacity = 35000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class FobgoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -50
        self.upperpoorlimit = 60
        self.upperfinelimit = 45
        self.lowerfinelimit = -45
        self.lowerpoorlimit = -60
        self.maxhp = 80
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 1.5
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 10000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Quick but rather inaccurate at throwing. Protects other bodyparts quite well. Good at avoiding traps when crawling. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 1.06, 1, 1, 65, 'blunt', 0, [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 1.06, 1, 1, 65, 'sharp', 0, [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class FobgoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -100
        self.upperpoorlimit = 60
        self.upperfinelimit = -15
        self.lowerfinelimit = -100
        self.lowerpoorlimit = -100
        self.maxheight = 100
        self.maxhp = 80
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 30000
        self.carryingcapacity = 20000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Good at avoiding traps. Strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.86, 1, 1, 97, 'blunt', 0, [], [], self)]
        else:
            return []


class FobgoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 80
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.86, 1, 1, 97, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class FobgoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
        self.maxhp = 35
        self.weight = 5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.3
        self._info = 'An eye consisting of living flesh. Good at detecting traps.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class FobgoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 70
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 13
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 13, average mana capacity.'


class FobgoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 70
        self.weight = 300
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class FobgoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 70
        self.weight = 600
        self.breathepoisonresistance = 0.2
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh. Some protection against poison gas.'


class FobgoblinKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 70
        self.weight = 100
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'


class FobgoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fobgoblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 70
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
        }
        self._info = 'A stomach consisting of living flesh.'


class LargeFireElementalTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'large fire elemental torso', '*', (255, 204, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', constantfunction(145)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', constantfunction(145)),
            'head': BodyPartConnection(self, ['head'], True, '', constantfunction(150)),
            'heart': BodyPartConnection(self, ['heart'], True, '', constantfunction(100), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left bellows': BodyPartConnection(self, ['lung'], False, 'left ', constantfunction(100), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right bellows': BodyPartConnection(self, ['lung'], False, 'right ', constantfunction(100), defensecoefficient=0.8, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', constantfunction(70), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', constantfunction(70), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', constantfunction(90), defensecoefficient=0.8, armorapplies=True, internal=True),
            'front left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front left ', constantfunction(0)),
            'back left limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back left ', constantfunction(0)),
            'front right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'front right ', constantfunction(0)),
            'back right limb': BodyPartConnection(self, ['tentacle', 'arm', 'leg'], False, 'back right ', constantfunction(0))
        }
        self._topheight = 150
        self.maxhp = 375
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 800
        self.carryingcapacity = 60000
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self._info = 'A torso consisting of elemental fire. Has extremely good carrying capacity. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage. No smell.'


class LargeFireElementalArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'large fire elemental arm', '~', (255, 204, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -55
        self.upperpoorlimit = 65
        self.upperfinelimit = 50
        self.lowerfinelimit = -50
        self.lowerpoorlimit = -65
        self.maxhp = 85
        self.capableofthrowing = True
        self.throwaccuracy = 0.97
        self.throwspeed = 1
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 100
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self.carefulness = 0.5
        self._info = 'An arm consisting of elemental fire. Protects other bodyparts quite well. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage. No smell.'

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
                return [Attack(self.parentalconnection.prefix + 'fist burn', 'burned', 'burned', 'burn', '', '', 1.08, 1, 1, 70, 'fire', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class LargeFireElementalHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'large fire elemental head', '*', (255, 204, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.maxhp = 90
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 200
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of elemental fire. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage. No smell.'


class LargeFireElementalEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'flaming eye', '*', (255, 204, 0))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 3
        self._bottomheight = -3
        self.maxhp = 37
        self.weight = 0
        self.material = 'elemental'
        self.consumable = False
        self.edible = False
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self.detectiondistance = 1.5
        self.detectionprobability = 0.2
        self._info = 'An eye consisting of elemental fire. Rather good at detecting traps. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage.'

    def sight(self):
        if not (self.destroyed() or self.incapacitated()):
            return 3
        else:
            return 0

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class LargeFireElementalBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'large fire elemental brain', '*', (255, 204, 0))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 75
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 10
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 14
        self.manacapacity = 20
        self.spellsknown = [magic.FireMissile(np.random.randint(8, 15))]
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self._info = 'A brain consisting of elemental fire. Intelligence 14, average mana capacity. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage.'


class LargeFireElementalHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'burning heart', '*', (255, 204, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 75
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 10
        self.bravery = 0.5
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.2
        self._info = 'A heart consisting of elemental fire. Average bravery. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and resistant against electric damage.'


class LargeFireElementalBellows(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'large fire elemental bellows', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 12
        self._bottomheight = -12
        self.maxhp = 75
        self.material = 'elemental'
        self.weight = 600
        self.breathepoisonresistance = 0
        self.runstaminarecoveryspeed = 0.5
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self._info = 'A lung consisting of elemental fire. Doesn\'t gain hunger and can\'t be poisoned, but doesn\'t protect living body parts from poison gas. Completely resistant against fire damage, and very resistant against electric damage.'


class LargeFireElementalTentacle(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'large fire elemental tentacle', '~', (255, 204, 0))
        self.categories = ['arm', 'leg', 'tentacle']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -30
        self.upperpoorlimit = 150
        self.upperfinelimit = 100
        self.lowerfinelimit = -100
        self.lowerpoorlimit = -150
        self.maxheight = 200
        self.minheight = 30
        self.maxhp = 90
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 0.75
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'tentacle'
        self.worn = {'tentacle armor': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.material = "elemental"
        self.consumable = False
        self.edible = False
        self.weight = 200
        self.carryingcapacity = 20000
        self._attackpoisonresistance = 1
        self._resistances['fire'] = 1
        self._resistances['electric'] = 0.5
        self.carefulness = 0.5
        self.maxrunstamina = 10
        self._info = 'A tentacle consisting of elemental fire. Works both as an arm and as a leg. Faster at moving and attacking if there are more of them. Slow and rather inaccurate at throwing. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against fire damage, and very resistant against electric damage. No smell.'

    def standingheight(self):
        legsnotentacles = [part for part in self.owner if 'leg' in part.categories and not 'tentacle' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        tentacles = [part for part in self.owner if 'tentacle' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legsnotentacles) > 0:
            legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
            ) and not part.incapacitated()]
            return min([leg.maxheight for leg in legs])
        else:
            return max([tentacle.minheight for tentacle in tentacles])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
                return [Attack(self.parentalconnection.prefix + 'tentacle burn', 'burned', 'burned', 'burn', '', '', 1.08, timetaken, 1, 35, 'fire', 0, [], [], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class DobgoblinTorso(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin torso', '*', (0, 255, 0))
        self.categories = ['torso']
        self.childconnections = {
            'left arm': BodyPartConnection(self, ['arm'], False, 'left ', heightfuncuprightorprone(self, 70, 25)),
            'right arm': BodyPartConnection(self, ['arm'], False, 'right ', heightfuncuprightorprone(self, 70, 25)),
            'left leg': BodyPartConnection(self, ['leg'], False, 'left ', constantfunction(0)),
            'right leg': BodyPartConnection(self, ['leg'], False, 'right ', constantfunction(0)),
            'head': BodyPartConnection(self, ['head'], True, '', heightfuncuprightorprone(self, 75, 20)),
            'heart': BodyPartConnection(self, ['heart'], True, '', heightfuncuprightorprone(self, 65, 20), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left lung': BodyPartConnection(self, ['lung'], False, 'left ', heightfuncuprightorprone(self, 60, 20), defensecoefficient=0.5, armorapplies=True, internal=True),
            'right lung': BodyPartConnection(self, ['lung'], False, 'right ', heightfuncuprightorprone(self, 60, 20), defensecoefficient=0.5, armorapplies=True, internal=True),
            'left kidney': BodyPartConnection(self, ['kidney'], False, 'left ', heightfuncuprightorprone(self, 50, 20), defensecoefficient=0.8, armorapplies=True, internal=True),
            'right kidney': BodyPartConnection(self, ['kidney'], False, 'right ', heightfuncuprightorprone(self, 50, 20), defensecoefficient=0.8, armorapplies=True, internal=True),
            'stomach': BodyPartConnection(self, ['stomach'], False, '', heightfuncuprightorprone(self, 55, 20), defensecoefficient=0.8, armorapplies=True, internal=True)
        }
        self._topheight = 75
        self._pronetopheight = 40
        self.maxhp = 400
        self.worn = {'chest armor': listwithowner([], self), 'back': listwithowner(
            [], self), 'belt': listwithowner([], self)}
        self._wearwieldname = 'torso'
        self.weight = 70000
        self.carryingcapacity = 35000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self._info = 'A torso consisting of living flesh. Strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def topheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        if len(legs) == 0:
            return self.baseheight() + self._pronetopheight
        else:
            return self.baseheight() + self._topheight


class DobgoblinArm(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin arm', '~', (0, 255, 0))
        self.categories = ['arm']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -55
        self.upperpoorlimit = 65
        self.upperfinelimit = 50
        self.lowerfinelimit = -50
        self.lowerpoorlimit = -65
        self.maxhp = 90
        self.capableofthrowing = True
        self.throwaccuracy = 0.95
        self.throwspeed = 1.5
        self.protectiveness = 0.15
        self.capableofwielding = True
        # It's a list so that it can be an item's owner. However, it shouldn't hold more than one item at a time.
        self.wielded = listwithowner([], self)
        self._wearwieldname = 'hand'
        self.worn = {'gauntlet': listwithowner(
            [], self), 'ring': listwithowner([], self)}
        self.weight = 11000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.smell = 1
        self._info = 'An arm consisting of living flesh. Quick but rather inaccurate at throwing. Protects other bodyparts quite well. Good at avoiding traps when crawling. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

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
                return [Attack(self.parentalconnection.prefix + 'fist', 'punched', 'punched', 'punch', '', '', 1.10, 1, 1, 75, 'blunt', 0, [], [('knockback', 0.2)], self), Attack(self.parentalconnection.prefix + 'claws', 'clawed', 'clawed', 'claw', '', '', 1.10, 1, 1, 75, 'sharp', 0, [], [('bleed', 0.2)], self)]
            else:
                return self.wielded[0].attackslist()
        else:
            return []


class DobgoblinLeg(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin leg', '~', (0, 255, 0))
        self.categories = ['leg']
        self.childconnections = {}
        self._topheight = 0
        self._bottomheight = -105
        self.upperpoorlimit = 65
        self.upperfinelimit = -15
        self.lowerfinelimit = -105
        self.lowerpoorlimit = -105
        self.maxheight = 105
        self.maxhp = 90
        self.worn = {'leg armor': listwithowner([], self)}
        self._wearwieldname = 'leg'
        self.weight = 21000
        self.carryingcapacity = 30000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.carefulness = 0.75
        self.maxrunstamina = 10
        self.smell = 1
        self._info = 'A leg consisting of living flesh. Good at avoiding traps. Strong at carrying. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def standingheight(self):
        legs = [part for part in self.owner if 'leg' in part.categories and not part.destroyed(
        ) and not part.incapacitated()]
        return min([leg.maxheight for leg in legs])

    def bottomheight(self):
        if self.owner.owner.stance == 'flying' or self.owner.owner.world.largerocks[self.owner.owner.x, self.owner.owner.y]:
            return 50
        else:
            return 0

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
            return [Attack(self.parentalconnection.prefix + 'foot kick', 'kicked', 'kicked', 'kick', '', '', 0.90, 1, 1, 112, 'blunt', 0, [], [], self)]
        else:
            return []


class DobgoblinHead(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin head', '*', (0, 255, 0))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(20)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(20)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(20), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 30
        self._bottomheight = 0
        self.upperpoorlimit = 25
        self.upperfinelimit = 20
        self.lowerfinelimit = -5
        self.lowerpoorlimit = -15
        self.maxhp = 90
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
        self._wearwieldname = 'head'
        self.weight = 6000
        self._resistances['sharp'] = 0.2
        self._resistances['blunt'] = -0.2
        self.smell = 1
        self.hearing = 1
        self.sound = 1
        self._info = 'A head consisting of living flesh. Tough skin (resistant against sharp damage) but weak bones (weak against blunt damage).'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.90, 1, 1, 112, 'sharp', 0, [], [('bleed', 0.1)], self)]
        else:
            return []


class DobgoblinEye(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin eye', '*', (0, 255, 255))
        self.categories = ['eye']
        self.childconnections = {}
        self._topheight = 1
        self._bottomheight = -1
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

    def on_destruction(self, dead):
        self.owner.owner.fovuptodate = False
        super().on_destruction(dead)


class DobgoblinBrain(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin brain', '*', (255, 0, 255))
        self.categories = ['brain']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 80
        self.weight = 1000
        self.log = loglist()
        self.seen = []
        for i in range(numlevels):
            self.seen.append(
                [[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for j in range(mapwidth)])
        self.creaturesseen = []
        self.itemsseen = []
        self.godsknown = []
        self.curesknown = []
        self.frightenedby = []
        self.intelligence = 15
        self.manacapacity = 20
        self.spellsknown = []
        self._info = 'A brain consisting of living flesh. Intelligence 15, average mana capacity.'


class DobgoblinHeart(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin heart', '*', (255, 0, 0))
        self.categories = ['heart']
        self.childconnections = {}
        self._topheight = 5
        self._bottomheight = -5
        self.maxhp = 80
        self.weight = 300
        self.bravery = 0.5
        self._resistances['electric'] = -0.2
        self._info = 'A heart consisting of living flesh. Average bravery. Weak against electric damage.'


class DobgoblinLung(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin lung', '*', (255, 0, 0))
        self.categories = ['lung']
        self.childconnections = {}
        self._topheight = 10
        self._bottomheight = -10
        self.maxhp = 80
        self.weight = 600
        self.breathepoisonresistance = 0.2
        self.runstaminarecoveryspeed = 0.5
        self._info = 'A lung consisting of living flesh. Some protection against poison gas.'


class DobgoblinKidney(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin kidney', '*', (255, 0, 0))
        self.categories = ['kidney']
        self.childconnections = {}
        self._topheight = 4
        self._bottomheight = -4
        self.maxhp = 80
        self.weight = 100
        self.endotoxicity = -1
        self._info = 'A kidney consisting of living flesh. Filters toxins at an average speed.'


class DobgoblinStomach(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'dobgoblin stomach', '*', (255, 0, 0))
        self.categories = ['stomach']
        self.childconnections = {}
        self._topheight = 7
        self._bottomheight = -7
        self.maxhp = 80
        self.weight = 1000
        self.foodprocessing = {  # Tuples, first item: is 1 if can eat normally, 0 if refuses to eat unless starving and may get sick and -1 if refuses to eat whatsoever. Second item (only necessary if first is not -1) is efficiency. Third is message to be displayed, if any.
            'cooked meat': (1, 1, None),
            'vegetables': (1, 1, None),
            'living flesh': (0, 0.75, 'That was disgusting, but at least it easened your hunger.'),
            'undead flesh': (-1,)
        }
        self._info = 'A stomach consisting of living flesh.'


class VelociraptorSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized velociraptor skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(6)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(6)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(5), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 8
        self._bottomheight = 0
        self.upperpoorlimit = 55
        self.upperfinelimit = 30
        self.lowerfinelimit = -65
        self.lowerpoorlimit = -70
        self.maxhp = 50
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
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
        self._resistances['electric'] = 1
        self.nonconductive = True
        self.sound = 1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against electric damage and nonconductive, very resistant against sharp, blunt and fire damage, but very weak against rough damage. No smell. No sense of hearing.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 0.9, 1, 1, 25, 'sharp', 0, [], [('bleed', 0.2)], self)]
        else:
            return []


class DeinonychusSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized deinonychus skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(15)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(15)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(15), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 20
        self._bottomheight = 0
        self.upperpoorlimit = 65
        self.upperfinelimit = 40
        self.lowerfinelimit = -70
        self.lowerpoorlimit = -80
        self.maxhp = 75
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
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
        self._resistances['electric'] = 1
        self.nonconductive = True
        self.sound = 1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against electric damage and nonconductive, very resistant against sharp, blunt and fire damage, but very weak against rough damage. No smell. No sense of hearing.'
        
    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 1.0, 1, 1, 50, 'sharp', 0, [], [('bleed', 0.2)], self)]
        else:
            return []


class CeratosaurusSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized ceratosaurus skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(30)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(30)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(30), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 40
        self._bottomheight = 0
        self.upperpoorlimit = 70
        self.upperfinelimit = 45
        self.lowerfinelimit = -75
        self.lowerpoorlimit = -85
        self.maxhp = 100
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
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
        self._resistances['electric'] = 1
        self.nonconductive = True
        self.sound = 1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against electric damage and nonconductive, very resistant against sharp, blunt and fire damage, but very weak against rough damage. No smell. No sense of hearing.'
        
    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 1.1, 1, 1, 75, 'sharp', 0, [], [('bleed', 0.2)], self)]
        else:
            return []


class AllosaurusSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized allosaurus skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(40)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(40)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(40), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 50
        self._bottomheight = 0
        self.upperpoorlimit = 80
        self.upperfinelimit = 60
        self.lowerfinelimit = -80
        self.lowerpoorlimit = -100
        self.maxhp = 125
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
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
        self._resistances['electric'] = 1
        self.nonconductive = True
        self.sound = 1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against electric damage and nonconductive, very resistant against sharp, blunt and fire damage, but very weak against rough damage. No smell. No sense of hearing.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 1.2, 1, 1, 100, 'sharp', 0, [], [('bleed', 0.2)], self)]
        else:
            return []


class TyrannosaurusSkull(BodyPart):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fossilized tyrannosaurus skull', '*', (255, 255, 255))
        self.categories = ['head']
        self.childconnections = {
            'left eye': BodyPartConnection(self, ['eye'], False, 'left ', constantfunction(80)),
            'right eye': BodyPartConnection(self, ['eye'], False, 'right ', constantfunction(80)),
            'brain': BodyPartConnection(self, ['brain'], True, '', constantfunction(80), defensecoefficient=0.5, armorapplies=True, internal=True)
        }
        self._topheight = 100
        self._bottomheight = 0
        self.upperpoorlimit = 120
        self.upperfinelimit = 100
        self.lowerfinelimit = -100
        self.lowerpoorlimit = -120
        self.maxhp = 150
        self.worn = {'helmet': listwithowner(
            [], self), 'face': listwithowner([], self)}
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
        self._resistances['electric'] = 1
        self.nonconductive = True
        self.sound = 1
        self._info = 'A head consisting of stone. Doesn\'t gain hunger and can\'t be poisoned. Completely resistant against electric damage and nonconductive, very resistant against sharp, blunt and fire damage, but very weak against rough damage. No smell. No sense of hearing.'

    def attackslist(self):
        if not (self.destroyed() or self.incapacitated()):
            return [Attack('bite', 'bit', 'bit', 'bite', '', '', 1.3, 1, 1, 125, 'sharp', 0, [], [('bleed', 0.2)], self)]
        else:
            return []
