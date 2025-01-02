# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 21:16:44 2022

@author: SurrealPartisan
"""

import numpy as np

import bodypart
import item
import magic
from utils import fov, listwithowner, numlevels, mapwidth, mapheight, difficulty, anglebetween, directionnames

def checkitems(creat, cave, x,y):
    for it in cave.items:
        if it.x == x and it.y == y:
            creat.log().append('There is a ' + it.name + ' here.')

class Creature():
    def __init__(self, world, world_i):
        self.world = world
        self.world_i = world_i
        self.max_world_i = world_i
        self.factions = []
        self.char = '@'
        self.color = 'white'
        self.name = 'golem'
        self.individualname = ''
        self.x = 0
        self.y = 0
        self.x_old = 0
        self.y_old = 0
        self.xp = 0
        self.inventory = listwithowner([], self)
        self.nextaction = ['wait', 1]
        self.previousaction = 'wait'
        self.bodyparts = listwithowner([], self)
        self.lasthitter = None
        self.torso = None
        self.dead = False
        self.causeofdeath = None
        self.hunger = 0
        self.starvationclock = 0
        self.suffocationclock = 0
        self.weakenedclock = 0
        self.vomitclock = 0
        self.disorientedclock = 0
        self.slowedclock = 0
        self.poisonclock = 0
        self.accumulatedpoison = 0
        self.burnclock = 0
        self.scaredclock = 0
        self.panickedclock = 0
        self.runstaminaused = 0
        self.manaused = 0
        self.stance = 'neutral'
        self.preferredstance = 'neutral'

    def log(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not (part.destroyed() or part.incapacitated())]
        if len(brains) > 0:
            return brains[0].log
        else:
            if not self.dead:
                return ['You have no brain, so nothing is logged.']
            else:
                return ['You have no brain, so nothing is logged.', 'You are dead!', 'Press escape to end.']

    def seen(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not (part.destroyed() or part.incapacitated())]
        if len(brains) > 0:
            return brains[0].seen
        else:
            seenlist = []
            for i in range(numlevels):
                seenlist.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
            return seenlist

    def godsknown(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not (part.destroyed() or part.incapacitated())]
        if len(brains) > 0:
            return brains[0].godsknown
        else:
            return []

    def curesknown(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not (part.destroyed() or part.incapacitated())]
        if len(brains) > 0:
            return brains[0].curesknown
        else:
            return []

    def creaturesseen(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not (part.destroyed() or part.incapacitated())]
        if len(brains) > 0:
            return brains[0].creaturesseen
        else:
            return []

    def frightenedby(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not (part.destroyed() or part.incapacitated())]
        if len(brains) > 0:
            return brains[0].frightenedby
        else:
            return []

    def itemsseen(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not (part.destroyed() or part.incapacitated())]
        if len(brains) > 0:
            return brains[0].itemsseen
        else:
            return []

    def spellsknown(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not (part.destroyed() or part.incapacitated())]
        if len(brains) > 0:
            return brains[0].spellsknown
        else:
            return []

    def manacapacity(self):
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        return sum([part.manacapacity for part in self.bodyparts if hasattr(part, 'manacapacity')]) + sum([it.manacapacity for it in wornlist if hasattr(it, 'manacapacity')])

    def mana(self):
        return self.manacapacity() - self.manaused

    def intelligence(self):
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        return sum([part.intelligence for part in self.bodyparts if hasattr(part, 'intelligence')]) + sum([it.intelligence for it in wornlist if hasattr(it, 'intelligence')])

    def maxrunstamina(self):
        return sum([part.maxrunstamina for part in self.bodyparts])

    def runstaminarecoveryspeed(self):
        return sum([part.runstaminarecoveryspeed for part in self.bodyparts])

    def stancesknown(self):
        known = ['neutral', 'aggressive', 'defensive']
        if self.stance == 'running' or self.runstaminaused < 0.5*self.maxrunstamina():
            known.append('running')
        if self.panicked():
            if 'running' in known:
                known = ['running']
            else:
                known = ['defensive']
        elif self.scared():
            if 'running' in known:
                known = ['defensive', 'running']
            else:
                known = ['defensive']
        for part in self.bodyparts:
            for stance in part.stances():
                if (not self.panicked() and not self.scared()) or stance == 'flying':
                    known.append(stance)
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        for it in wornlist:
            if hasattr(it, 'stances'):
                for stance in it.stances:
                    if (not self.panicked() and not self.scared()) or stance == 'flying':
                        known.append(stance)
        return known

    def imbalanced(self):
        return np.any([part.imbalanced() for part in self.bodyparts])

    def weakened(self):
        return self.weakenedclock > 0

    def scared(self):
        return self.scaredclock > 0

    def panicked(self):
        return self.panickedclock > 0

    def carryingcapacity(self):
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        divider = 2 if self.weakened() else 1
        return int((sum([part.carryingcapacity for part in self.bodyparts if not (part.destroyed() or part.incapacitated())]) + sum([it.carryingcapacity for it in wornlist])) / divider)

    def weightcarried(self):
        wieldlist = [part.wielded[0] for part in self.bodyparts if part.capableofwielding and len(part.wielded) > 0]
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        return sum([it.weight for it in self.inventory]) + sum([it.weight for it in wornlist]) + sum([it.weight for it in wieldlist])

    def hungry(self):
        return self.hunger > 20 and len([part for part in self.bodyparts if part.material == 'living flesh']) > 0

    def starving(self):
        return self.hunger > 40 and len([part for part in self.bodyparts if part.material == 'living flesh']) > 0

    def gainhunger(self, time):
        livingmass = sum([part.weight for part in self.bodyparts if part.material == 'living flesh'])
        itemmultipliers = [it[0].hungermultiplier for part in self.bodyparts for it in part.worn.values() if len(it) > 0 and hasattr(it[0], 'hungermultiplier')]
        multiplier = 1
        for m in itemmultipliers:
            multiplier *= m
        if 'player' in self.factions:
            self.hunger += livingmass*time*multiplier*1e-06
        if self.vomitclock > 0:
            self.hunger += livingmass*min(time, self.vomitclock)*multiplier*1e-05

    def starve(self):
        if not self.dying():
            part = np.random.choice([part for part in self.bodyparts if part.material == 'living flesh' and not part.destroyed()])
            alreadyincapacitated = part.incapacitated()
            part.damagetaken += 1
            if part.damagetaken > part.maxhp:
                part.damagetaken = part.maxhp
            if part.parentalconnection != None:
                partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
            elif part == self.torso:
                partname = 'torso'
            if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                self.log().append('Your ' + partname + ' was incapacitated by starvation.')
            elif not part.destroyed():
                self.log().append('Your ' + partname + ' took 1 damage from starvation.')
            else:
                self.log().append('Your ' + partname + ' was destroyed by starvation.')
                part.on_destruction(self.dying())
            if self.dying() and not self.dead:
                self.log().append("You are dead!")
                self.die()
                self.causeofdeath = ('starvation',)

    def suffocating(self):
        lungs = [part for part in self.bodyparts if 'lung' in part.categories and not (part.destroyed() or part.incapacitated())]
        livingparts = [part for part in self.bodyparts if part.material == 'living flesh' and not part.destroyed()]
        return len(lungs) == 0 and len(livingparts) > 0

    def suffocate(self, time):
        if not self.dying():
            lungs = [part for part in self.bodyparts if 'lung' in part.categories and not (part.destroyed() or part.incapacitated())]
            if len(lungs) == 0:
                self.suffocationclock += time
                for i in range(int(self.suffocationclock // 1)):
                    livingparts = [part for part in self.bodyparts if part.material == 'living flesh' and not part.destroyed()]
                    for part in livingparts:
                        alreadyincapacitated = part.incapacitated()
                        part.damagetaken += 1
                        if part.damagetaken > part.maxhp:
                            part.damagetaken = part.maxhp
                        if part.parentalconnection != None:
                            partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
                        elif part == self.torso:
                            partname = 'torso'
                        if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                            self.log().append('Your ' + partname + ' was incapacitated by suffocation.')
                        elif not part.destroyed():
                            self.log().append('Your ' + partname + ' took 1 damage from suffocation.')
                        else:
                            self.log().append('Your ' + partname + ' was destroyed by suffocation.')
                            part.on_destruction(self.dying())
                self.suffocationclock = self.suffocationclock % 1
                if self.dying() and not self.dead:
                    self.log().append("You are dead!")
                    self.die()
                    self.causeofdeath = ('suffocation',)

    def burn(self, cause, time):
        if cause == 'campfire':
            if not self.dying():
                self.burnclock += time
                for i in range(int(self.burnclock // 1)):
                    part = self.approxfastestpart()
                    adjacentparts = [connection.child for connection in part.childconnections.values() if not connection.child == None and not connection.child.destroyed() and not connection.child.internal()]
                    if part.parentalconnection != None and not part.parentalconnection.parent.destroyed():
                        adjacentparts.append(part.parentalconnection.parent)
                    if np.random.rand() > 0.75 and len(adjacentparts) > 0:
                        part = np.random.choice(adjacentparts)
                    totaldamage = np.random.randint(1, 11)
                    resistancemultiplier = 1 - part.resistance('fire')
                    damage = min(int(resistancemultiplier*totaldamage), part.hp())
                    alreadyincapacitated = part.incapacitated()
                    part.damagetaken += damage
                    alreadyimbalanced = self.imbalanced()
                    if 'leg' in part.categories:
                        numlegs = len([p for p in self.bodyparts if 'leg' in p.categories and not p.destroyed() and not p.incapacitated()])
                        if np.random.rand() < 0.5 - 0.05*numlegs:
                            part.imbalanceclock += 20*damage/part.maxhp
                    if damage > 0:
                        if part.parentalconnection != None:
                            partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
                        elif part == self.torso:
                            partname = 'torso'
                        if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                            if self.imbalanced() and not alreadyimbalanced:
                                self.log().append('The campfire burned and incapacitated your ' + partname + ', imbalancing you.')
                            else:
                                self.log().append('The campfire burned and incapacitated your ' + partname + '.')
                        elif not part.destroyed():
                            if self.imbalanced() and not alreadyimbalanced:
                                self.log().append('The campfire burned your ' + partname + ', dealing ' + repr(damage) + ' damage and imbalancing you.')
                            else:
                                self.log().append('The campfire burned your ' + partname + ', dealing ' + repr(damage) + ' damage.')
                        else:
                            if self.imbalanced() and not alreadyimbalanced:
                                self.log().append('The campfire burned and destroyed your ' + partname + ', imbalancing you.')
                            else:
                                self.log().append('The campfire burned and destroyed your ' + partname + '.')
                            part.on_destruction(self.dying())
                self.burnclock = self.burnclock % 1
                if self.dying() and not self.dead:
                    self.log().append("You are dead!")
                    self.die()
                    self.causeofdeath = ('burning', 'in a campfire')
        elif cause == 'lava':
            if not self.dying():
                self.burnclock += time
                for i in range(int(self.burnclock // 1)):
                    for part in [part for part in self.bodyparts if not part.internal()]:
                        totaldamage = np.random.randint(1, 21)
                        resistancemultiplier = 1 - part.resistance('fire')
                        damage = min(int(resistancemultiplier*totaldamage), part.hp())
                        alreadyincapacitated = part.incapacitated()
                        part.damagetaken += damage
                        alreadyimbalanced = self.imbalanced()
                        if 'leg' in part.categories:
                            numlegs = len([p for p in self.bodyparts if 'leg' in p.categories and not p.destroyed() and not p.incapacitated()])
                            if np.random.rand() < 0.5 - 0.05*numlegs:
                                part.imbalanceclock += 20*damage/part.maxhp
                        if damage > 0:
                            if part.parentalconnection != None:
                                partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
                            elif part == self.torso:
                                partname = 'torso'
                            if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                                if self.imbalanced() and not alreadyimbalanced:
                                    self.log().append('The lava burned and incapacitated your ' + partname + ', imbalancing you.')
                                else:
                                    self.log().append('The lava burned and incapacitated your ' + partname + '.')
                            elif not part.destroyed():
                                if self.imbalanced() and not alreadyimbalanced:
                                    self.log().append('The lava burned your ' + partname + ', dealing ' + repr(damage) + ' damage and imbalancing you.')
                                else:
                                    self.log().append('The lava burned your ' + partname + ', dealing ' + repr(damage) + ' damage.')
                            else:
                                if self.imbalanced() and not alreadyimbalanced:
                                    self.log().append('The lava burned and destroyed your ' + partname + ', imbalancing you.')
                                else:
                                    self.log().append('The lava burned and destroyed your ' + partname + '.')
                                part.on_destruction(self.dying())
                self.burnclock = self.burnclock % 1
                if self.dying() and not self.dead:
                    self.log().append("You are dead!")
                    self.die()
                    self.causeofdeath = ('burning', 'in a lava pit')

    def bleed(self, time):
        totalcausers = []
        for part in self.bodyparts:
            if part.parentalconnection != None:
                partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
            elif part == self.torso:
                partname = 'torso'
            alreadyincapacitated = part.incapacitated()
            bled, causers = part.bleed(time)
            for causer in causers:
                if not causer in totalcausers:
                    totalcausers.append(causer)
            if bled > 0:
                if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                    self.log().append('The bleeding incapacitated your ' + partname + '.')
                elif part.destroyed():
                    self.log().append('Your ' + partname + ' bled out.')
                    part.on_destruction(self.dying())
                else:
                    self.log().append('Your ' + partname + ' took ' + repr(bled) + ' damage from bleeding.')
        if self.dying() and not self.dead:
            self.log().append('You are dead!')
            for creat in self.world.creatures:
                fovmap = fov(creat.world.walls, creat.x, creat.y, creat.sight())
                if fovmap[self.x, self.y] and creat != self:
                    creat.log().append('The ' + self.name + ' bled to death!')
            self.die()
            self.causeofdeath = ('bloodloss', totalcausers)

    def endotoxicity(self):
        return 0.1 + sum([part.endotoxicity for part in self.bodyparts if not (part.destroyed() or part.incapacitated())])

    def breathepoisonresistance(self):
        lungresistances = [part.breathepoisonresistance for part in self.bodyparts if 'lung' in part.categories and not (part.destroyed() or part.incapacitated())]
        wornresistances = [it[0].breathepoisonresistance for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        return min(1, np.mean(lungresistances) + sum(wornresistances))

    def applypoison(self, time):
        oldaccumulation = self.accumulatedpoison
        self.accumulatedpoison = min(50, max(0, self.accumulatedpoison + self.endotoxicity()*time))
        if self.accumulatedpoison > 5 and oldaccumulation > 5:
            self.poisonclock = self.poisonclock + time
        elif self.accumulatedpoison > 5:
            self.poisonclock = self.poisonclock + (self.accumulatedpoison - 5)/self.endotoxicity()
        elif oldaccumulation > 5:
            self.poisonclock = self.poisonclock + (oldaccumulation - 5)/self.endotoxicity()
        else:
            self.poisonclock = 0
        ticks = int(self.poisonclock)
        self.poisonclock -= ticks
        if len([part for part in self.bodyparts if part.material == 'living flesh']) > 0:
            for i in range(ticks):
                if np.random.rand() < 0.5:
                    affliction = np.random.randint(4)
                    if affliction == 0:
                        if self.weakenedclock == 0:
                            self.log().append('The poison made you weak!')
                        self.weakenedclock += np.random.rand()*10
                    if affliction == 1:
                        if self.vomitclock == 0:
                            self.log().append('The poison made you start vomiting!')
                        self.vomitclock += np.random.rand()*10
                    if affliction == 2:
                        if self.disorientedclock == 0:
                            self.log().append('The poison made you disoriented!')
                        self.disorientedclock += np.random.rand()*10
                    if affliction == 3:
                        if self.slowedclock == 0:
                            self.log().append('The poison made you slowed!')
                        self.slowedclock += np.random.rand()*10
        if oldaccumulation > 5 and self.accumulatedpoison <= 5:
            self.log().append('You are no longer poisoned, but some aftereffects may linger.')
        if oldaccumulation <= 5 and self.accumulatedpoison > 5:
            self.log().append('The endotoxins of your body poisoned you!')

    def burdened(self):
        return self.weightcarried() > self.carryingcapacity()/2

    def overloaded(self):
        return self.weightcarried() > self.carryingcapacity()
    
    def slowed(self):
        return int(self.world.spiderwebs[self.x, self.y]) + (self.slowedclock > 0)
    
    def speed(self):
        if self.stance != 'flying':
            basespeed = max([part.speed() for part in self.bodyparts])
        else:
            basespeed = max([part.flyingspeed() for part in self.bodyparts] + [it[0].flyingspeed for part in self.bodyparts for it in part.worn.values() if len(it) > 0 and hasattr(it[0], 'flyingspeed')])
        if self.stance == 'running':
            basespeed *= 2
        if self.overloaded():
            return 0
        elif self.burdened():
            return basespeed / 2
        else:
            return basespeed

    def approxfastestpart(self):
        return max(self.bodyparts, key=lambda x: x.speed() + np.random.rand()*0.1)

    def steptime(self):
        if self.speed() > 0:
            return 1/self.speed()
        else:
            return np.inf

    def move(self, dx, dy):
        self.x_old = self.x
        self.y_old = self.y
        self.x += dx
        self.y += dy
        for smellx in [self.x_old-1, self.x_old, self.x_old+1]:
            for smelly in [self.y_old-1, self.y_old, self.y_old+1]:
                smelldistance = np.sqrt((smellx - self.x_old)**2 + (smelly - self.y_old)**2)
                if self in self.world.smells[smellx][smelly]:
                    self.world.smells[smellx][smelly][self] = max(self.world.smells[smellx][smelly][self], self.smell()/(1+smelldistance))
                else:
                    self.world.smells[smellx][smelly][self] = self.smell()/(1+smelldistance)
        if self.stance != 'flying':
            for it in self.world.items:
                if (it.x, it.y) == (self.x, self.y) and it.trap:
                    part = self.approxfastestpart()
                    if it in self.itemsseen() or not it.hidden:
                        if np.random.rand() < part.carefulness:
                            self.log().append('You managed to move carefully and avoided the ' + it.name + '.')
                        else:
                            it.entrap(self, part)
                    else:
                        it.entrap(self, part)
                        self.itemsseen().append(it)
        if self.world.largerocks[self.x, self.y]:
            self.log().append('There is a large rock here.')
        if self.world.lavapits[self.x, self.y]:
            self.log().append('There is a lava pit here.')
            if self.stance != 'flying':
                self.burnclock = 1
        if self.world.campfires[self.x, self.y]:
            self.log().append('There is a campfire here.')
            if self.stance != 'flying':
                self.burnclock = 1
        if self.world.spiderwebs[self.x, self.y]:
            self.log().append('There is spiderweb here.')
        if self.world.poisongas[self.x, self.y]:
            self.log().append('There is a cloud of poison gas here.')
        if (self.x, self.y) == self.world.stairsupcoords:
            self.log().append('There are stairs up here.')
        if (self.x, self.y) == self.world.stairsdowncoords:
            self.log().append('There are stairs down here.')
        for x, y, gd in self.world.altars:
            if (self.x, self.y) == (x, y):
                self.log().append('There is an altar of ' + gd.name + ' here.')
                if not gd in self.godsknown():
                    self.godsknown().append(gd)
                    self.log().append('You learn the ways of ' + gd.name + ', the ' + gd.factions[0] + '-god of ' + gd.sin + '.')
                    self.log().append(gd.pronoun.capitalize() + ' ' + gd.copula + ' a ' + gd.power + ' and ' + gd.attitude + ' god.')
        if self.senseofsmell() > 0:
            for creat in self.world.smells[self.x][self.y]:
                if creat != self and self.world.smells[self.x][self.y][creat] > 1/self.senseofsmell():
                    strongestsmell = self.world.smells[self.x][self.y][creat]
                    strongestdcoords = (0, 0)
                    for dx2 in [-1, 0, 1]:
                        for dy2 in [-1, 0, 1]:
                            if creat in self.world.smells[self.x + dx2][self.y + dy2] and self.world.smells[self.x + dx2][self.y + dy2][creat] > strongestsmell:
                                strongestsmell = self.world.smells[self.x + dx2][self.y + dy2][creat]
                                strongestdcoords = (dx2, dy2)
                    if hasattr(creat, 'smellname'):
                        smellname = creat.smellname
                    else:
                        smellname = creat.name
                    if strongestdcoords != (0,0):
                        self.log().append('You smell a ' + smellname + '. The smell gets stronger towards ' + directionnames[strongestdcoords] + '.')
                    else:
                        self.log().append('You smell a ' + smellname + '. The smell is at its strongest right here.')
        checkitems(self, self.world, self.x, self.y)

    def godlylove(self):
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        wieldlist = [part.wielded[0] for part in self.bodyparts if part.capableofwielding and len(part.wielded) > 0]
        return 1 + sum([part.godlylove for part in self.bodyparts if hasattr(part, 'godlylove') and not (part.destroyed() or part.incapacitated())]) + sum([it.godlylove for it in wornlist if hasattr(it, 'godlylove')]) + sum([it.godlylove for it in wieldlist if hasattr(it, 'godlylove')])

    def pray(self, gd):
        self.log().append('You prayed to ' + gd.name + '.')
        gd.answer_to_prayer(self)

    def minespeed(self):
        return max([part.minespeed() for part in self.bodyparts])

    def minetime(self):
        return 1/self.minespeed()

    def smell(self):
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        return max(0, sum([part.smell for part in self.bodyparts] + [it.smell for it in wornlist if hasattr(it, 'smell')]))

    def senseofsmell(self):
        return sum([part.senseofsmell for part in self.bodyparts if hasattr(part, 'senseofsmell')])

    def sight(self):
        if (self.world.largerocks[self.x, self.y] or self.stance == 'flying') and sum([part.sight() for part in self.bodyparts]) > 0:
            highground = 1
        else:
            highground = 0
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        wieldlist = [part.wielded[0] for part in self.bodyparts if part.capableofwielding and len(part.wielded) > 0]
        return 1 + sum([part.sight() for part in self.bodyparts]) + sum([it.sight() for it in wornlist if hasattr(it, 'sight')]) + sum([it.sight() for it in wieldlist if hasattr(it, 'sight')]) + highground

    def heal(self, part, hpgiven):
        healed = min(hpgiven, part.damagetaken)
        alreadyincapacitated = part.incapacitated()
        part.damagetaken -= healed
        if part.damagetaken > part.maxhp:
            part.damagetaken = part.maxhp
        if part.parentalconnection != None:
            partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
        elif part == self.torso:
            partname = 'torso'
        if healed > 0:
            self.log().append('Your ' + partname + ' was healed by ' + repr(healed) + ' points.')
        elif healed < 0:
            if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                self.log().append('Your ' + partname + ' was incapacitated.')
            elif not part.destroyed():
                self.log().append('Your ' + partname + ' was harmed by ' + repr(-healed) + ' points.')
            else:
                self.log().append('Your ' + partname + ' was destroyed.')
                part.on_destruction(self.dying())
            if self.dying() and not self.dead:
                self.log().append("You are dead!")
                self.die()
        else:
            self.log().append('You were unaffected.')

    def dying(self):
        maxtotalhp = sum([part.maxhp for part in self.bodyparts])/2
        if not 'player' in self.factions:
            maxtotalhp *= difficulty
        return self.dead or sum([part.damagetaken for part in self.bodyparts]) >= maxtotalhp or np.any([part.vital() and (part.destroyed() or part.incapacitated()) for part in self.bodyparts])

    def die(self):
        if self.lasthitter != None:
            self.lasthitter.xp += sum([part.maxhp for part in self.bodyparts]) // 2
        self.world.creatures.remove(self)
        for it in self.inventory:
            it.owner = self.world.items
            self.world.items.append(it)
            self.inventory.remove(it)
            it.x = self.x
            it.y = self.y
        for it in [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]:
            it.owner.remove(it)
            it.owner = self.world.items
            self.world.items.append(it)
            it.x = self.x
            it.y = self.y
        for part in self.bodyparts:
            if not part.destroyed():
                part.owner = self.world.items
                self.world.items.append(part)
                part.x = self.x
                part.y = self.y
                if np.random.rand() > 0.25 + 0.5*part.hp()/part.maxhp:
                    part.usable = False
                    part.name += ' [UNUSABLE]'
            part.parentalconnection = None
            for con in part.childconnections:
                part.childconnections[con].child = None
            if part.capableofwielding:
                for it in part.wielded:
                    it.owner = self.world.items
                    self.world.items.append(it)
                    part.wielded.remove(it)
                    it.x = self.x
                    it.y = self.y
        self.dead = True

    def scariness(self):
        return sum([part.scariness for part in self.bodyparts if not part.destroyed() and not part.incapacitated()])

    def frighten(self):
        if self.scariness() > 0:
            targets = []
            for creat in self.world.creatures:
                if creat != self and not self in creat.frightenedby() and ('player' in creat.factions or 'player' in self.factions) and creat.sight() > 1:
                    fovmap = fov(creat.world.walls, creat.x, creat.y, creat.sight())
                    if fovmap[self.x, self.y]:
                        targets.append(creat)
            logtext = 'You made a scary face.'
            if len(targets) == 0:
                logtext += ' No one new saw it.'
            for target in targets:
                target.frightenedby().append(self)
                braveries = [part.bravery for part in target.bodyparts if part.bravery > 0] + [it[0].bravery for part in target.bodyparts for it in part.worn.values() if len(it) > 0 and hasattr(it[0], 'bravery')]
                scared = True
                for bravery in braveries:
                    if np.random.rand() < bravery:
                        scared = False
                if scared:
                    panic = True
                    for bravery in braveries:
                        if np.random.rand() < bravery:
                            panic = False
                    if panic:
                        target.panickedclock += 1 + np.random.rand()*(self.scariness() - 1)
                        logtext += ' The ' + target.name + ' got panicked.'
                        target.log().append('The ' + self.name + ' made a scary face. You got panicked.')
                    else:
                        target.scaredclock += 1 + np.random.rand()*(self.scariness() - 1)
                        logtext += ' The ' + target.name + ' got scared.'
                        target.log().append('The ' + self.name + ' made a scary face. You got scared.')
                else:
                    logtext += ' The ' + target.name + ' remained calm.'
                    target.log().append('The ' + self.name + ' made a scary face. You remained calm.')
            self.log().append(logtext)
        else:
            self.log().append('You attempted to make a scary face, but failed.')

    def attackslist(self):
        return sorted([attack for part in self.bodyparts for attack in part.attackslist()], key=lambda x: x.maxdamage * x.hitprobability / x.time, reverse=True)

    def thrownattackslist(self):
        wieldlist = [part.wielded[0] for part in self.bodyparts if part.capableofwielding and len(part.wielded) > 0]
        freelimbs = len([part for part in self.bodyparts if part.capableofwielding and part.capableofthrowing and len(part.wielded) == 0])
        l = sorted([attack for it in wieldlist for attack in it.thrownattackslist()], key=lambda x: x.maxdamage * x.hitprobability, reverse=True)
        if freelimbs > 0:
            l += sorted([attack for it in self.inventory for attack in it.thrownattackslist()], key=lambda x: x.maxdamage * x.hitprobability, reverse=True)
        return l

    def throwatsquare(self, targetx, targety, missile, throwinglimb, verbose=True):
        if throwinglimb in self.bodyparts and not throwinglimb.incapacitated() and not throwinglimb.destroyed():
            distance = np.sqrt((targetx - self.x)**2 + (targety - self.y)**2)
            if distance <= missile.throwrange:
                accuracy = throwinglimb.throwaccuracy**distance
                if np.random.rand() < accuracy:
                    x, y = targetx, targety
                    if verbose:
                        self.log().append('You threw the ' + missile.name + ' where you wanted.')
                    hit = True
                else:
                    x, y = targetx, targety
                    while (x, y) == (targetx, targety) or self.world.walls[x, y]:
                        x, y = np.random.randint(targetx-1, targetx+2), np.random.randint(targety-1, targety+2)
                    if verbose:
                        self.log().append('You threw the ' + missile.name + ' approximately where you wanted.')
                    hit = False
            else:
                angle = anglebetween((self.x, self.y), (targetx, targety))
                x, y = targetx, targety
                r = distance
                newdistance = np.sqrt((x - self.x)**2 + (y - self.y)**2)
                while newdistance > missile.throwrange or self.world.walls[x, y]:
                    r -= 0.1
                    x = round(self.x + r*np.cos(angle))
                    y = round(self.y + r*np.sin(angle))
                    newdistance = np.sqrt((x - self.x)**2 + (y - self.y)**2)
                if verbose:
                    self.log().append('You threw the ' + missile.name + ' but could not get it as far as you wanted.')
                hit = False
            missile.owner.remove(missile)
            missile.owner = self.world.items
            self.world.items.append(missile)
            missile.x = x
            missile.y = y
        else:
            if verbose:
                self.log().append('You were unable to finish your throw.')
            hit = False
        return hit

    def throwatenemy(self, target, targetbodypart, attack, throwinglimb):
        missile = attack.weapon
        if throwinglimb in self.bodyparts and not throwinglimb.incapacitated() and not throwinglimb.destroyed():
            hitsquare = self.throwatsquare(target.x, target.y, missile, throwinglimb, verbose=False)
            if hitsquare:
                self.fight(target, targetbodypart, attack, thrown=True)
            else:
                self.log().append('You threw the ' + missile.name + ' but missed the ' + target.name + '.')
                target.log().append('The ' + self.name + ' threw a ' + missile.name + 'at you but missed.')
        else:
            self.log().append('You were unable to finish your throw.')

    def fight(self, target, targetbodypart, attack, thrown=False, magical=False):
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        if attack.weapon in self.bodyparts or attack.weapon == None:
            attackingpart = attack.weapon
        elif attack.weapon.owner != self.world.items:
            attackingpart = attack.weapon.owner.owner
        else:
            attackingpart = None
        if thrown or magical or (attackingpart != None and not (attackingpart.destroyed() or attackingpart.incapacitated())):
            if targetbodypart in target.bodyparts and not targetbodypart.destroyed():
                if thrown or magical or (abs(self.x - target.x) <= 1 and abs(self.y - target.y) <= 1):
                    if (not self.scared() or np.random.rand() < 0.5) and not self.panicked():
                        if self.stance == 'aggressive':
                            attackerstancecoefficient = 1.25
                        elif self.stance == 'defensive':
                            attackerstancecoefficient = 0.9
                        elif self.stance == 'berserk':
                            attackerstancecoefficient = 1.5
                        else:
                            attackerstancecoefficient = 1
                        if target.stance == 'aggressive':
                            defenderstancecoefficient = 1.111
                        elif target.stance == 'defensive':
                            defenderstancecoefficient = 0.80
                        elif target.stance == 'berserk':
                            defenderstancecoefficient = 1.222
                        else:
                            defenderstancecoefficient = 1
                        if (self.stance == 'flying' or self.world.largerocks[self.x, self.y]) and target.stance != 'flying' and not target.world.largerocks[target.x, target.y]:
                            highgroundcoefficient = 1.05
                        elif self.stance != 'flying' and not self.world.largerocks[self.x, self.y] and (target.stance == 'flying' or target.world.largerocks[target.x, target.y]):
                            highgroundcoefficient = 0.95
                        else:
                            highgroundcoefficient = 1
                        if not thrown and not magical and not (np.any([hasattr(it, 'martialartist') and it.martialartist for it in wornlist]) and attack.weapon in self.bodyparts):
                            upperpoorlimit = attackingpart.baseheight() + attackingpart.upperpoorlimit + attack.weaponlength
                            upperfinelimit = attackingpart.baseheight() + attackingpart.upperfinelimit + attack.weaponlength
                            lowerfinelimit = attackingpart.baseheight() + attackingpart.lowerfinelimit - attack.weaponlength
                            lowerpoorlimit = attackingpart.baseheight() + attackingpart.lowerpoorlimit - attack.weaponlength
                            if upperfinelimit >= targetbodypart.topheight() >= lowerfinelimit or upperfinelimit >= targetbodypart.bottomheight() >= lowerfinelimit or targetbodypart.topheight() >= upperfinelimit >= targetbodypart.bottomheight():
                                heightcoefficient = 1
                            elif targetbodypart.bottomheight() >= upperpoorlimit or targetbodypart.topheight() <= lowerpoorlimit:
                                heightcoefficient = 0.5
                            elif upperpoorlimit > targetbodypart.bottomheight() > upperfinelimit:
                                heightcoefficient = 0.5 + 0.5*(upperpoorlimit - targetbodypart.bottomheight())/(upperpoorlimit - upperfinelimit)
                            elif lowerpoorlimit < targetbodypart.topheight() < lowerfinelimit:
                                heightcoefficient = 0.5 + 0.5*(targetbodypart.topheight() - lowerpoorlimit)/(lowerfinelimit - lowerpoorlimit)
                        else:
                            heightcoefficient = 1
                        if hasattr(targetbodypart, 'protectiveness'):
                            protectioncoefficient = 1 + targetbodypart.protectiveness
                        else:
                            protectioncoefficient = 1
                            for part in [part for part in target.bodyparts if hasattr(part, 'protectiveness') and part != targetbodypart and not part.destroyed() and not part.incapacitated()]:
                                upperlimit = part.baseheight() + part.upperpoorlimit
                                lowerlimit = part.baseheight() + part.lowerpoorlimit
                                if upperlimit >= targetbodypart.topheight() >= lowerlimit or upperlimit >= targetbodypart.bottomheight() >= lowerlimit or targetbodypart.topheight() >= upperlimit >= targetbodypart.bottomheight():
                                    protectioncoefficient *= (1 - part.protectiveness)
                        speedcoefficient = 1/np.sqrt(target.speed()/(1 + target.slowed())+0.1)
                        if target.imbalanced():
                            imbalancedcoefficient = 1.25
                        else:
                            imbalancedcoefficient = 1
                        secondarytargetbodypart = None
                        if np.random.rand() < max(min(attack.hitprobability*targetbodypart.defensecoefficient()*attackerstancecoefficient*defenderstancecoefficient*highgroundcoefficient*heightcoefficient*protectioncoefficient*speedcoefficient*imbalancedcoefficient, 0.95), 0.05):
                            hit = True
                            if targetbodypart.internal():
                                secondarytargetbodypart = targetbodypart.parentalconnection.parent
                            elif len([connection for connection in targetbodypart.childconnections if targetbodypart.childconnections[connection].child != None and targetbodypart.childconnections[connection].internal and not targetbodypart.childconnections[connection].child.destroyed()]) > 0 and np.random.rand() < 0.5:
                                internaltarget = np.random.choice([targetbodypart.childconnections[connection].child for connection in targetbodypart.childconnections if targetbodypart.childconnections[connection].child != None and targetbodypart.childconnections[connection].internal and not targetbodypart.childconnections[connection].child.destroyed()])
                                if not thrown and not magical and not (np.any([hasattr(it, 'martialartist') and it.martialartist for it in wornlist]) and attack.weapon in self.bodyparts):
                                    upperpoorlimit = attackingpart.baseheight() + attackingpart.upperpoorlimit + attack.weaponlength
                                    upperfinelimit = attackingpart.baseheight() + attackingpart.upperfinelimit + attack.weaponlength
                                    lowerfinelimit = attackingpart.baseheight() + attackingpart.lowerfinelimit - attack.weaponlength
                                    lowerpoorlimit = attackingpart.baseheight() + attackingpart.lowerpoorlimit - attack.weaponlength
                                    if upperfinelimit >= internaltarget.topheight() >= lowerfinelimit or upperfinelimit >= internaltarget.bottomheight() >= lowerfinelimit or internaltarget.topheight() >= upperfinelimit >= internaltarget.bottomheight():
                                        heightcoefficient = 1
                                    elif internaltarget.bottomheight() >= upperpoorlimit or internaltarget.topheight() <= lowerpoorlimit:
                                        heightcoefficient = 0.5
                                    elif upperpoorlimit > internaltarget.bottomheight() > upperfinelimit:
                                        heightcoefficient = 0.5 + 0.5*(upperpoorlimit - internaltarget.bottomheight())/(upperpoorlimit - upperfinelimit)
                                    elif lowerpoorlimit < internaltarget.topheight() < lowerfinelimit:
                                        heightcoefficient = 0.5 + 0.5*(internaltarget.topheight() - lowerpoorlimit)/(lowerfinelimit - lowerpoorlimit)
                                else:
                                    heightcoefficient = 1
                                if hasattr(internaltarget, 'protectiveness'):
                                    protectioncoefficient = 1 + internaltarget.protectiveness
                                else:
                                    protectioncoefficient = 1
                                    for part in [part for part in target.bodyparts if hasattr(part, 'protectiveness') and part != internaltarget and not part.destroyed() and not part.incapacitated()]:
                                        upperlimit = part.baseheight() + part.upperpoorlimit
                                        lowerlimit = part.baseheight() + part.lowerpoorlimit
                                        if upperlimit >= internaltarget.topheight() >= lowerlimit or upperlimit >= internaltarget.bottomheight() >= lowerlimit or internaltarget.topheight() >= upperlimit >= internaltarget.bottomheight():
                                            protectioncoefficient *= (1 - part.protectiveness)
                                if np.random.rand() < max(min(attack.hitprobability*internaltarget.defensecoefficient()*attackerstancecoefficient*defenderstancecoefficient*highgroundcoefficient*heightcoefficient*protectioncoefficient*speedcoefficient*imbalancedcoefficient, 0.95), 0.05):
                                    secondarytargetbodypart = targetbodypart
                                    targetbodypart = internaltarget
                        else:
                            adjacentparts = [connection.child for connection in targetbodypart.childconnections.values() if not connection.child == None and not connection.child.destroyed() and not connection.child.internal()]
                            if targetbodypart.parentalconnection != None and not targetbodypart.parentalconnection.parent.destroyed():
                                adjacentparts.append(targetbodypart.parentalconnection.parent)
                            for part in [part for part in target.bodyparts if hasattr(part, 'protectiveness') and part != targetbodypart and not part.destroyed() and not part.incapacitated()]:
                                if not part in adjacentparts:
                                    adjacentparts.append(part)
                            if len(adjacentparts) > 0:
                                targetbodypart = np.random.choice(adjacentparts)
                                if not thrown and not magical and not (np.any([hasattr(it, 'martialartist') and it.martialartist for it in wornlist]) and attack.weapon in self.bodyparts):
                                    upperpoorlimit = attackingpart.baseheight() + attackingpart.upperpoorlimit + attack.weaponlength
                                    upperfinelimit = attackingpart.baseheight() + attackingpart.upperfinelimit + attack.weaponlength
                                    lowerfinelimit = attackingpart.baseheight() + attackingpart.lowerfinelimit - attack.weaponlength
                                    lowerpoorlimit = attackingpart.baseheight() + attackingpart.lowerpoorlimit - attack.weaponlength
                                    if upperfinelimit >= targetbodypart.topheight() >= lowerfinelimit or upperfinelimit >= targetbodypart.bottomheight() >= lowerfinelimit or targetbodypart.topheight() >= upperfinelimit >= targetbodypart.bottomheight():
                                        heightcoefficient = 1
                                    elif targetbodypart.bottomheight() >= upperpoorlimit or targetbodypart.topheight() <= lowerpoorlimit:
                                        heightcoefficient = 0.5
                                    elif upperpoorlimit > targetbodypart.bottomheight() > upperfinelimit:
                                        heightcoefficient = 0.5 + 0.5*(upperpoorlimit - targetbodypart.bottomheight())/(upperpoorlimit - upperfinelimit)
                                    elif lowerpoorlimit < targetbodypart.topheight() < lowerfinelimit:
                                        heightcoefficient = 0.5 + 0.5*(targetbodypart.topheight() - lowerpoorlimit)/(lowerfinelimit - lowerpoorlimit)
                                else:
                                    heightcoefficient = 1
                                if hasattr(targetbodypart, 'protectiveness'):
                                    protectioncoefficient = 1 + targetbodypart.protectiveness
                                else:
                                    protectioncoefficient = 1
                                    for part in [part for part in target.bodyparts if hasattr(part, 'protectiveness') and part != targetbodypart and not part.destroyed() and not part.incapacitated()]:
                                        upperlimit = part.baseheight() + part.upperpoorlimit
                                        lowerlimit = part.baseheight() + part.lowerpoorlimit
                                        if upperlimit >= targetbodypart.topheight() >= lowerlimit or upperlimit >= targetbodypart.bottomheight() >= lowerlimit or targetbodypart.topheight() >= upperlimit >= targetbodypart.bottomheight():
                                            protectioncoefficient *= (1 - part.protectiveness)
                                if np.random.rand() < max(min(attack.hitprobability*targetbodypart.defensecoefficient()*attackerstancecoefficient*defenderstancecoefficient*highgroundcoefficient*heightcoefficient*protectioncoefficient*speedcoefficient*imbalancedcoefficient, 0.95), 0.05):
                                    hit = True
                                else:
                                    hit = False
                            else:
                                hit = False
                        if hit:
                            target.lasthitter = self
                            totaldamage = np.random.randint(attack.mindamage, attack.maxdamage+1)
                            knocked_back = False
                            knocked_to_obstacle = ''
                            for special in attack.special:
                                if special[0] == 'charge' and self.previousaction[0] == 'move' and np.sqrt((self.x-target.x)**2 + (self.y-target.y)**2) < np.sqrt((self.x_old-target.x)**2 + (self.y_old-target.y)**2):
                                    if self.stance == 'running':
                                        totaldamage = 2*totaldamage
                                    else:
                                        totaldamage = int(1.5*totaldamage)
                                    if not thrown:
                                        attack = item.Attack(attack[0], 'charged', 'charged', attack[3], attack[4], attack[5], attack[6], attack[7], attack[8], attack[9], attack[10], attack[11], attack[12], attack[13])
                                if special[0] == 'knockback' and np.random.rand() < special[1]:
                                    dx = target.x - self.x
                                    dy = target.y - self.y
                                    if self.world.walls[target.x+dx, target.y+dy]:
                                        knocked_to_obstacle = 'wall'
                                        totaldamage *= 2
                                    elif self.world.largerocks[target.x+dx, target.y+dy]:
                                        knocked_to_obstacle = 'large rock'
                                        totaldamage *= 2
                                    elif not np.any([creat.x == target.x+dx and creat.y == target.y+dy for creat in self.world.creatures]):
                                        knocked_back = True
                                        target.move(dx, dy)
                            if target.imbalanced():
                                totaldamage = int(1.5*totaldamage)
                                alreadyimbalanced = True
                            else:
                                alreadyimbalanced = False
                            if self.stance == 'running' and not 'charge' in [special[0] for special in attack.special] and self.previousaction[0] == 'move' and np.sqrt((self.x-target.x)**2 + (self.y-target.y)**2) < np.sqrt((self.x_old-target.x)**2 + (self.y_old-target.y)**2) and not magical:
                                totaldamage = int(1.5*totaldamage)
                                if not thrown:
                                    attack = item.Attack(attack[0], 'charged', 'charged', attack[3], attack[4], attack[5], attack[6], attack[7], attack[8], attack[9], attack[10], attack[11], attack[12], attack[13])
                            if self.stance == 'fasting' and attack.weapon in self.bodyparts and self.starving():
                                totaldamage *= 3
                            elif self.stance == 'fasting' and attack.weapon in self.bodyparts and self.hungry():
                                totaldamage *= 2
                            if not self in target.creaturesseen():
                                totaldamage *= 2
                                sneak = True
                            else:
                                sneak = False
                            if self.weakened() and not magical:
                                totaldamage //= 2
                            if targetbodypart.armor() != None:
                                armor = targetbodypart.armor()
                                armordamage = min(armor.hp(), min(totaldamage, np.random.randint(armor.mindamage, armor.maxdamage+1)))
                                armor.damagetaken += armordamage
                            else:
                                armor = None
                                armordamage = 0
                            if np.any([faction in attack.bane for faction in target.factions]):
                                banemultiplier = 2
                            else:
                                banemultiplier = 1
                            armorpassingdamage = banemultiplier*(totaldamage - armordamage)
                            if secondarytargetbodypart != None and armorpassingdamage > 1:
                                _secondarydamage = np.random.randint(1, armorpassingdamage)
                                secondaryresistancemultiplier = 1 - secondarytargetbodypart.resistance(attack.damagetype)
                                secondarydamage = min(int(secondaryresistancemultiplier*_secondarydamage), secondarytargetbodypart.hp())
                            elif secondarytargetbodypart != None and armorpassingdamage < 2:
                                targetbodypart = secondarytargetbodypart
                                secondarytargetbodypart = None
                                _secondarydamage = 0
                                secondarydamage = 0
                            else:
                                _secondarydamage = 0
                                secondarydamage = 0
                            resistancemultiplier = 1 - targetbodypart.resistance(attack.damagetype)
                            damage = min(int(resistancemultiplier*(armorpassingdamage - _secondarydamage)), targetbodypart.hp())
                            bleed = False
                            for special in attack.special:
                                if special[0] == 'bleed' and np.random.rand() < special[1]:
                                    bleed = True
                                    targetbodypart.bleedclocks.append((damage, 0, self))
                            alreadyincapacitated = targetbodypart.incapacitated()
                            if secondarytargetbodypart != None:
                                secondaryalreadyincapacitated = secondarytargetbodypart.incapacitated()
                            if 'player' in target.factions:
                                targetparthalfhp = targetbodypart.maxhp / 2
                                if secondarytargetbodypart != None:
                                    secondarytargetparthalfhp = secondarytargetbodypart.maxhp / 2
                                totalthreequartershp = sum([part.maxhp for part in target.bodyparts])/2*3/4
                            else:
                                targetparthalfhp = targetbodypart.maxhp * difficulty / 2
                                if secondarytargetbodypart != None:
                                    secondarytargetparthalfhp = secondarytargetbodypart.maxhp * difficulty / 2
                                totalthreequartershp = sum([part.maxhp for part in target.bodyparts])/2*3/4*difficulty
                            vitalalreadyunderhalf = (targetbodypart.vital() and targetbodypart.damagetaken > targetparthalfhp) or (secondarytargetbodypart != None and secondarytargetbodypart.vital() and secondarytargetbodypart.damagetaken > secondarytargetparthalfhp)
                            totalalreadyunderquarter = sum([part.damagetaken for part in target.bodyparts]) > totalthreequartershp
                            targetbodypart.damagetaken += damage
                            if secondarytargetbodypart != None:
                                secondarytargetbodypart.damagetaken += secondarydamage
                            reasontopanic = (not vitalalreadyunderhalf and ((targetbodypart.vital() and targetbodypart.damagetaken > targetparthalfhp) or (secondarytargetbodypart != None and secondarytargetbodypart.vital() and secondarytargetbodypart.damagetaken > secondarytargetparthalfhp))) or (not totalalreadyunderquarter and sum([part.damagetaken for part in target.bodyparts]) > totalthreequartershp)
                            panic = False
                            scared = False
                            if reasontopanic:
                                braveries = [part.bravery for part in target.bodyparts if part.bravery > 0] + [it[0].bravery for part in target.bodyparts for it in part.worn.values() if len(it) > 0 and hasattr(it[0], 'bravery')]
                                scared = True
                                for bravery in braveries:
                                    if np.random.rand() < bravery:
                                        scared = False
                                if scared:
                                    panic = True
                                    for bravery in braveries:
                                        if np.random.rand() < bravery:
                                            panic = False
                                    if panic:
                                        target.panickedclock += 2*(damage+secondarydamage)
                                    else:
                                        target.scaredclock += 2*(damage+secondarydamage)
                            if 'leg' in targetbodypart.categories:
                                numlegs = len([part for part in target.bodyparts if 'leg' in part.categories and not part.destroyed() and not part.incapacitated()])
                                if np.random.rand() < 0.5 - 0.05*numlegs:
                                    targetbodypart.imbalanceclock += 20*damage/targetbodypart.maxhp
                            if secondarytargetbodypart != None and 'leg' in secondarytargetbodypart.categories:
                                numlegs = len([part for part in target.bodyparts if 'leg' in part.categories and not part.destroyed() and not part.incapacitated()])
                                if np.random.rand() < 0.5 - 0.05*numlegs:
                                    secondarytargetbodypart.imbalanceclock += 20*secondarydamage/secondarytargetbodypart.maxhp
                            if targetbodypart.parentalconnection != None:
                                partname = list(targetbodypart.parentalconnection.parent.childconnections.keys())[list(targetbodypart.parentalconnection.parent.childconnections.values()).index(targetbodypart.parentalconnection)]
                            elif targetbodypart == target.torso:
                                partname = 'torso'
                            if secondarytargetbodypart != None and secondarytargetbodypart.parentalconnection != None:
                                secondarypartname = list(secondarytargetbodypart.parentalconnection.parent.childconnections.keys())[list(secondarytargetbodypart.parentalconnection.parent.childconnections.values()).index(secondarytargetbodypart.parentalconnection)]
                            elif secondarytargetbodypart == target.torso:
                                secondarypartname = 'torso'
                            else:
                                secondarypartname = ''
                            if not target.dying():
                                if targetbodypart.incapacitated() and not alreadyincapacitated and not targetbodypart.destroyed() and secondarytargetbodypart != None and secondarytargetbodypart.incapacitated() and not secondaryalreadyincapacitated and not secondarytargetbodypart.destroyed():
                                    if not knocked_back and not knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' and incapacitated the ' + partname + ' and the ' + secondarypartname + ' of the ' + target.name + attack.post2nd + '!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and incapacitated your ' + partname + ' and your ' + secondarypartname + attack.post3rd + '!')
                                    elif knocked_back:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' and incapacitated the ' + partname + ' and the ' + secondarypartname + ' of the ' + target.name + attack.post2nd + ', knocking it back!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and incapacitated your ' + partname + ' and your ' + secondarypartname + attack.post3rd + ', knocking you back!')
                                    elif knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' and incapacitated the ' + partname + ' and the ' + secondarypartname + ' of the ' + target.name + attack.post2nd + ', knocking it against the ' + knocked_to_obstacle + '!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and incapacitated your ' + partname + ' and your ' + secondarypartname + attack.post3rd + ', knocking you against the ' + knocked_to_obstacle + '!')
                                    if armordamage > 0:
                                        if not armor.destroyed():
                                            target.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                                        else:
                                            target.log().append('Your ' + armor.name + ' was destroyed!')
                                            armor.owner.remove(armor)
                                elif targetbodypart.incapacitated() and not alreadyincapacitated and not targetbodypart.destroyed():
                                    if secondarytargetbodypart != None and not secondarytargetbodypart.destroyed():
                                        secondarymessage1 = ', dealing ' + repr(secondarydamage) + ' damage to its ' + secondarypartname
                                        secondarymessage2 = ', dealing ' + repr(secondarydamage) + ' damage to your ' + secondarypartname
                                        commaorand = ' and'
                                    elif secondarytargetbodypart != None and secondarytargetbodypart.destroyed():
                                        secondarymessage1 = 'destroying its ' + secondarypartname
                                        secondarymessage2 = 'destroying your ' + secondarypartname
                                        commaorand = ' and'
                                    else:
                                        secondarymessage1 = ''
                                        secondarymessage2 = ''
                                        commaorand = ','
                                    if not knocked_back and not knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd + ' and incapacitated the ' + partname + ' of the ' + target.name + attack.post2nd + secondarymessage1 + '!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and incapacitated your ' + partname + attack.post3rd + secondarymessage2 + '!')
                                    elif knocked_back:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd + ' and incapacitated the ' + partname + ' of the ' + target.name + attack.post2nd + secondarymessage1 + commaorand + ' knocking it back!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and incapacitated your ' + partname + attack.post3rd + secondarymessage2 + commaorand + ' knocking you back!')
                                    elif knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd + ' and incapacitated the ' + partname + ' of the ' + target.name + attack.post2nd + secondarymessage1 + commaorand + ' knocking it against the ' + knocked_to_obstacle + '!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and incapacitated your ' + partname + attack.post3rd + secondarymessage2 + commaorand + ' knocking you against the ' + knocked_to_obstacle + '!')
                                    if armordamage > 0:
                                        if not armor.destroyed():
                                            target.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                                        else:
                                            target.log().append('Your ' + armor.name + ' was destroyed!')
                                            armor.owner.remove(armor)
                                    if secondarytargetbodypart != None and secondarytargetbodypart.destroyed():
                                        secondarytargetbodypart.on_destruction(False)
                                elif not targetbodypart.destroyed():
                                    if secondarytargetbodypart != None and not (secondarytargetbodypart.incapacitated() and not secondaryalreadyincapacitated) and not secondarytargetbodypart.destroyed():
                                        secondarymessage1 = '(' + repr(secondarydamage) + ' to the ' + secondarypartname + ')'
                                        secondarymessage2 = '(' + repr(secondarydamage) + ' to the ' + secondarypartname + ')'
                                        andorspace = ' '
                                        commaorspace = ' '
                                    elif secondarytargetbodypart != None and not secondarytargetbodypart.destroyed():
                                        secondarymessage1 = ' incapacitating its ' + secondarypartname
                                        secondarymessage2 = ' incapacitating your ' + secondarypartname
                                        andorspace = ' and '
                                        commaorspace = ', '
                                    elif secondarytargetbodypart != None:  # destroyed
                                        secondarymessage1 = ' destroying its ' + secondarypartname
                                        secondarymessage2 = ' destroying your ' + secondarypartname
                                        andorspace = ' and '
                                        commaorspace = ', '
                                    else:
                                        secondarymessage1 = ''
                                        secondarymessage2 = ''
                                        andorspace = ''
                                        commaorspace = ''
                                    if not thrown:
                                        if not bleed and not knocked_back and not knocked_to_obstacle:
                                            self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', dealing ' + repr(damage) + ' damage' + andorspace + secondarymessage1 + '!')
                                            target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', dealing ' + repr(damage) + ' damage' + andorspace + secondarymessage2 + '!')
                                        elif bleed:
                                            self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', dealing ' + repr(damage) + ' damage' + commaorspace + secondarymessage1 + ' and making it bleed!')
                                            target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', dealing ' + repr(damage) + ' damage' + commaorspace + secondarymessage2 + ' and making you bleed!')
                                        elif knocked_back:
                                            self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', dealing ' + repr(damage) + ' damage' + commaorspace + secondarymessage1 + ' and knocking it back!')
                                            target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', dealing ' + repr(damage) + ' damage' + commaorspace + secondarymessage2 + ' and knocking you back!')
                                        elif knocked_to_obstacle:
                                            self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', dealing ' + repr(damage) + ' damage' + commaorspace + secondarymessage1 + ' and knocking it against the ' + knocked_to_obstacle + '!')
                                            target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', dealing ' + repr(damage) + ' damage' + commaorspace + secondarymessage2 + ' and knocking you against the ' + knocked_to_obstacle + '!')
                                    else:
                                        if not bleed and not knocked_back and not knocked_to_obstacle:
                                            self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' at the ' + target.name + '\'s ' + partname + attack.post2nd + ', hitting for ' + repr(damage) + ' damage' + andorspace + secondarymessage1 + '!')
                                            target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' at your ' + partname + attack.post3rd + ', hitting for ' + repr(damage) + ' damage' + andorspace + secondarymessage2 + '!')
                                        elif bleed:
                                            self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' at the ' + target.name + '\'s ' + partname + attack.post2nd + ', hitting for ' + repr(damage) + ' damage' + andorspace + secondarymessage1 + ' and making it bleed!')
                                            target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' at your ' + partname + attack.post3rd + ', hitting for ' + repr(damage) + ' damage' + andorspace + secondarymessage2 + ' and making you bleed!')
                                        elif knocked_back:
                                            self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' at the ' + target.name + '\'s ' + partname + attack.post2nd + ', hitting for ' + repr(damage) + ' damage' + andorspace + secondarymessage1 + ' and knocking it back!')
                                            target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' at your ' + partname + attack.post3rd + ', hitting for ' + repr(damage) + ' damage' + andorspace + secondarymessage2 + ' and knocking you back!')
                                        elif knocked_to_obstacle:
                                            self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' at the ' + target.name + '\'s ' + partname + attack.post2nd + ', hitting for ' + repr(damage) + ' damage' + andorspace + secondarymessage1 + ' and knocking it against the ' + knocked_to_obstacle + '!')
                                            target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' at your ' + partname + attack.post3rd + ', hitting for ' + repr(damage) + ' damage' + andorspace + secondarymessage2 + ' and knocking you against the ' + knocked_to_obstacle + '!')
                                    if armordamage > 0:
                                        if not armor.destroyed():
                                            target.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                                        else:
                                            target.log().append('Your ' + armor.name + ' was destroyed!')
                                            armor.owner.remove(armor)
                                elif secondarytargetbodypart != None and secondarytargetbodypart.destroyed():
                                    if not knocked_back and not knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' and destroyed the ' + partname + ' and the ' + secondarypartname + ' of the ' + target.name + attack.post2nd + '!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and destroyed your ' + partname + ' and your ' + secondarypartname + attack.post3rd + '!')
                                    elif knocked_back:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' and destroyed the ' + partname + ' and the ' + secondarypartname + ' of the ' + target.name + attack.post2nd + ', knocking it back!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and destroyed your ' + partname + ' and your ' + secondarypartname + attack.post3rd + ', knocking you back!')
                                    elif knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' and destroyed the ' + partname + ' and the ' + secondarypartname + ' of the ' + target.name + attack.post2nd + ', knocking it against the ' + knocked_to_obstacle + '!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and destroyed your ' + partname + ' and your ' + secondarypartname + attack.post3rd + ', knocking you against the ' + knocked_to_obstacle + '!')
                                    if armordamage > 0:
                                        if not armor.destroyed():
                                            target.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                                        else:
                                            target.log().append('Your ' + armor.name + ' was also destroyed!')
                                            armor.owner.remove(armor)
                                    targetbodypart.on_destruction(False)
                                    secondarytargetbodypart.on_destruction(False)
                                else:
                                    if secondarytargetbodypart != None and not (secondarytargetbodypart.incapacitated() and not secondaryalreadyincapacitated):
                                        secondarymessage1 = ', dealing ' + repr(secondarydamage) + ' damage to its ' + secondarypartname
                                        secondarymessage2 = ', dealing ' + repr(secondarydamage) + ' damage to your ' + secondarypartname
                                        commaorand = ' and'
                                    elif secondarytargetbodypart != None:
                                        secondarymessage1 = 'incapacitating its ' + secondarypartname
                                        secondarymessage2 = 'incapacitating your ' + secondarypartname
                                        commaorand = ' and'
                                    else:
                                        secondarymessage1 = ''
                                        secondarymessage2 = ''
                                        commaorand = ','
                                    if not knocked_back and not knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' and destroyed the ' + partname + ' of the ' + target.name + attack.post2nd + secondarymessage1 + '!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and destroyed your ' + partname + attack.post3rd + secondarymessage2 + '!')
                                    elif knocked_back:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' and destroyed the ' + partname + ' of the ' + target.name + attack.post2nd + secondarymessage1 + commaorand + ' knocking it back!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and destroyed your ' + partname + attack.post3rd + secondarymessage2 + commaorand + ' knocking you back!')
                                    elif knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' and destroyed the ' + partname + ' of the ' + target.name + attack.post2nd + secondarymessage1 + commaorand + ' knocking it against the ' + knocked_to_obstacle + '!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' and destroyed your ' + partname + attack.post3rd + secondarymessage2 + commaorand + ' knocking you against the ' + knocked_to_obstacle + '!')
                                    if armordamage > 0:
                                        if not armor.destroyed():
                                            target.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                                        else:
                                            target.log().append('Your ' + armor.name + ' was also destroyed!')
                                            armor.owner.remove(armor)
                                    targetbodypart.on_destruction(False)
                                if not alreadyimbalanced and target.imbalanced():
                                    self.log().append('The ' + target.name + ' was imbalanced by the attack.')
                                    target.log().append('You were imbalanced by the attack.')
                                if panic:
                                    self.log().append('The ' + target.name + ' got panicked.')
                                    target.log().append('You got panicked.')
                                elif scared:
                                    self.log().append('The ' + target.name + ' got scared.')
                                    target.log().append('You got scared.')
                            else:
                                if not thrown:
                                    if not knocked_back and not knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', killing it!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', killing you!')
                                    elif knocked_back:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', knocking it back and killing it!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', knocking you back and killing you!')
                                    elif knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', knocking it against the ' + knocked_to_obstacle + ' and killing it!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', knocking you against the ' + knocked_to_obstacle + ' and killing you!')
                                else:
                                    if not knocked_back and not knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' at the ' + target.name + '\'s ' + partname + attack.post2nd + ', killing it!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' at your ' + partname + attack.post3rd + ', killing you!')
                                    elif knocked_back:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' at the ' + target.name + '\'s ' + partname + attack.post2nd + ', knocking it back and killing it!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' at your ' + partname + attack.post3rd + ', knocking you back and killing you!')
                                    elif knocked_to_obstacle:
                                        self.log().append('You ' + 'sneakily '*sneak + attack.verb2nd +' at the ' + target.name + '\'s ' + partname + attack.post2nd + ', knocking it against the ' + knocked_to_obstacle + ' and killing it!')
                                        target.log().append('The ' + self.name + ' ' + 'sneakily '*sneak + attack.verb3rd + ' at your ' + partname + attack.post3rd + ', knocking you against the ' + knocked_to_obstacle + ' and killing you!')
                                target.log().append('You are dead!')
                                if targetbodypart.destroyed():
                                    targetbodypart.on_destruction(True)
                                target.die()
                                target.causeofdeath = ('attack', self)
                        else:
                            self.log().append('The ' + target.name + ' evaded your ' + 'thrown '*thrown + attack.name +'!')
                            target.log().append("You evaded the " + self.name + "'s " + 'thrown '*thrown + attack.name +"!")
                    else:
                        self.log().append('Your attack missed due to fear!')
                        target.log().append("The " + self.name + "'s attack missed due to fear!")
                else:
                    self.log().append('The ' + target.name + ' evaded your ' + attack.name + ' by being too far away!')
                    target.log().append("You evaded the " + self.name + "'s " + attack.name + " by being too far away!")
            elif targetbodypart.destroyed():
                self.log().append('The target body part is already destroyed!')
            else:
                self.log().append('The ' + target.name + ' no longer has that part!')
        elif attackingpart != None:
            if attackingpart.parentalconnection != None:
                attackingpartname = list(attackingpart.parentalconnection.parent.childconnections.keys())[list(attackingpart.parentalconnection.parent.childconnections.values()).index(attackingpart.parentalconnection)]
            elif attackingpart == self.torso:
                attackingpartname = 'torso'
            if attackingpart.destroyed():
                self.log().append('Your ' + attackingpartname + ' was destroyed before you could finish the attack!')
                target.log().append('The ' + self.name + '\'s ' + attackingpartname + ' was destroyed before it could finish its attack!')
            else:
                self.log().append('Your ' + attackingpartname + ' was incapacitated before you could finish the attack!')
                target.log().append('The ' + self.name + '\'s ' + attackingpartname + ' was incapacitated before it could finish its attack!')
        else:
            self.log().append('You dropped your weapon before you could finish the attack!')
            target.log().append('The ' + self.name + ' dropped its weapon before it could finish its attack!')

    def ai(self):
        # Return something to put in self.nextaction. It should be a list,
        # starting with action string, followed by parameters, last of which is
        # the time needed.
        return ['wait', 1]

    def resolveaction(self):
        if self.nextaction[0] == 'move':
            if self.stance == 'running':
                self.runstaminaused += self.nextaction[-1]*(1 + self.slowed())
            creaturesintheway = [creature for creature in self.world.creatures if creature.x == self.x+self.nextaction[1] and creature.y == self.y+self.nextaction[2]]
            if len(creaturesintheway) == 0:
                self.move(self.nextaction[1], self.nextaction[2])
                self.previousaction = ('move',)
            else:
                self.log().append("There's a " + creaturesintheway[0].name + " in your way.")
                self.previousaction = ('wait',)
        elif self.nextaction[0] == 'bump':
            if self.stance == 'running':
                self.runstaminaused += self.nextaction[-1]*(1 + self.slowed())
                part = np.random.choice([part for part in self.bodyparts if not part.internal() and not part.destroyed()])
                resistancemultiplier = 1 - part.resistance('blunt')
                totaldamage = np.random.randint(1, max(1, part.maxhp//5)+1)
                if part.armor() != None:
                    armor = part.armor()
                    armordamage = min(armor.hp(), min(totaldamage, np.random.randint(armor.mindamage, armor.maxdamage+1)))
                    armor.damagetaken += armordamage
                else:
                    armor = None
                    armordamage = 0
                damage = min(int(resistancemultiplier*(totaldamage - armordamage)), part.hp())
                alreadyincapacitated = part.incapacitated()
                part.damagetaken += damage
                alreadyimbalanced = self.imbalanced()
                if 'leg' in part.categories:
                    numlegs = len([p for p in self.bodyparts if 'leg' in p.categories and not p.destroyed() and not p.incapacitated()])
                    if np.random.rand() < 0.5 - 0.05*numlegs:
                        part.imbalanceclock += 20*damage/part.maxhp
                if self.imbalanced() and not alreadyimbalanced:
                    imbalancedtext = ', imbalancing you'
                else:
                    imbalancedtext = ''
                if part.parentalconnection != None:
                    partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
                elif part == self.torso:
                    partname = 'torso'
                if not self.dying():
                    if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                        self.log().append('You ran into wall. It incapacitated your ' + partname + imbalancedtext + '.')
                        if armordamage > 0:
                            if not armor.destroyed():
                                self.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                            else:
                                self.log().append('Your ' + armor.name + ' was destroyed!')
                                armor.owner.remove(armor)
                    elif not part.destroyed():
                        self.log().append('You ran into wall. It dealt ' + repr(damage) + ' damage to your ' + partname + imbalancedtext + '.')
                        if armordamage > 0:
                            if not armor.destroyed():
                                self.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                            else:
                                self.log().append('Your ' + armor.name + ' was destroyed!')
                                armor.owner.remove(armor)
                    else:
                        self.log().append('You ran into wall. It destroyed your ' + partname + imbalancedtext + '.')
                        if armordamage > 0:
                            if not armor.destroyed():
                                self.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                            else:
                                self.log().append('Your ' + armor.name + ' was also destroyed!')
                                armor.owner.remove(armor)
                        part.on_destruction(False)
                else:
                    self.log().append('You ran into wall ' + partname + ' first. It killed you.')
                    self.log().append('You are dead!')
                    if part.destroyed():
                        part.on_destruction(True)
                    self.die()
                    self.causeofdeath = ('ranintowall', partname)
            else:
                self.log().append("You bumped into a wall.")
            self.previousaction = ('wait',)
        elif self.nextaction[0] == 'frighten':
            self.frighten()
            self.previousaction = ('frighten',)
        elif self.nextaction[0] == 'fight':
            if not self.nextaction[1].dead:  # prevent a crash
                self.fight(self.nextaction[1], self.nextaction[2], self.nextaction[3])
                self.previousaction = ('fight', self.nextaction[3].weapon, self.nextaction[2])
        elif self.nextaction[0] == 'cast':
            self.nextaction[1].cast(*self.nextaction[2])
            self.previousaction = ('cast',)

    def update(self, time):
        if self.preferredstance in self.stancesknown():
            self.stance = self.preferredstance
        if not self.stance in self.stancesknown() or (self.stance == 'running' and self.runstaminaused >= self.maxrunstamina()):
            oldstance = self.stance
            if 'neutral' in self.stancesknown():
                self.stance = 'neutral'
            elif 'defensive' in self.stancesknown():
                self.stance = 'defensive'
            elif 'running' in self.stancesknown():
                self.stance = 'running'
            else: # Shouldn't happen, but just in case
                self.stance = 'neutral'
            if oldstance == 'flying':
                for it in self.world.items:
                    if (it.x, it.y) == (self.x, self.y) and it.trap:
                        part = self.approxfastestpart()
                        if it in self.itemsseen() or not it.hidden:
                            if np.random.rand() < part.carefulness:
                                self.log().append('You managed to land carefully and avoided the ' + it.name + '.')
                            else:
                                it.entrap(self, part)
                        else:
                            it.entrap(self, part)
                            self.itemsseen().append(it)
        timetoact = self.nextaction[-1]*(1 + self.slowed()*(self.nextaction[0] != 'wait'))
        if time < timetoact:
            self.nextaction[-1] -= time/(1 + self.slowed()*(self.nextaction[0] != 'wait'))
            self.bleed(time)
            if self.world.campfires[self.x, self.y] and self.stance != 'flying':
                self.burn('campfire', time)
            if self.world.lavapits[self.x, self.y] and self.stance != 'flying':
                self.burn('lava', time)
            imbalanced = self.imbalanced()
            for part in self.bodyparts:
                part.imbalanceclock = max(0, part.imbalanceclock - time)
            if imbalanced and not self.imbalanced():
                self.log().append('You regained your balance.')
            self.applypoison(time)
            self.weakenedclock = max(0, self.weakenedclock - time)
            self.disorientedclock = max(0, self.disorientedclock - time)
            self.slowedclock = max(0, self.slowedclock - time)
            self.gainhunger(time)
            vomiting = self.vomitclock > 0
            self.vomitclock = max(0, self.vomitclock - time)
            if vomiting and self.vomitclock == 0:
                self.log().append('You stopped vomiting.')
            if self.starving():
                self.starvationclock += time
                for i in range(int(self.starvationclock // 1)):
                    self.starve()
                self.starvationclock = self.starvationclock % 1
            self.suffocate(time)
            if self.stance != 'running' and not self.hungry():
                self.runstaminaused = max(0, self.runstaminaused - time*self.runstaminarecoveryspeed())
            elif self.stance != 'running' and not self.starving():
                self.runstaminaused = max(0, self.runstaminaused - time*0.5*self.runstaminarecoveryspeed())
            if self.panicked():
                self.panickedclock = max(0, self.panickedclock - time)
            elif self.scared():
                self.scaredclock = max(0, self.scaredclock - time)
            self.manaused = max(0, self.manaused - time)
        else:
            timeleft = time - timetoact
            self.bleed(timetoact)
            if self.world.campfires[self.x, self.y] and self.stance != 'flying':
                self.burn('campfire', timetoact)
            if self.world.lavapits[self.x, self.y] and self.stance != 'flying':
                self.burn('lava', timetoact)
            imbalanced = self.imbalanced()
            for part in self.bodyparts:
                part.imbalanceclock = max(0, part.imbalanceclock - time)
            if imbalanced and not self.imbalanced():
                self.log().append('You regained your balance.')
            self.applypoison(timetoact)
            self.weakenedclock = max(0, self.weakenedclock - timetoact)
            self.disorientedclock = max(0, self.disorientedclock - timetoact)
            self.slowedclock = max(0, self.slowedclock - timetoact)
            self.gainhunger(timetoact)
            vomiting = self.vomitclock > 0
            self.vomitclock = max(0, self.vomitclock - timetoact)
            if vomiting and self.vomitclock == 0:
                self.log().append('You stopped vomiting.')
            if self.starving():
                self.starvationclock += timetoact
                for i in range(int(self.starvationclock // 1)):
                    self.starve()
                self.starvationclock = self.starvationclock % 1
            self.suffocate(timetoact)
            if self.stance != 'running' and not self.hungry():
                self.runstaminaused = max(0, self.runstaminaused - timetoact*self.runstaminarecoveryspeed())
            elif self.stance != 'running' and not self.starving():
                self.runstaminaused = max(0, self.runstaminaused - timetoact*0.5*self.runstaminarecoveryspeed())
            if self.panicked():
                self.panickedclock = max(0, self.panickedclock - timetoact)
            elif self.scared():
                self.scaredclock = max(0, self.scaredclock - timetoact)
            self.manaused = max(0, self.manaused - timetoact)
            if self.world.poisongas[self.x, self.y]:
                livingparts = [part for part in self.bodyparts if part.material == 'living flesh' and not part.destroyed()]
                lungs = [part for part in self.bodyparts if 'lung' in part.categories and not (part.destroyed() or part.incapacitated())]
                if np.random.rand() > self.breathepoisonresistance() and len(livingparts) > 0 and len(lungs) > 0:
                    oldaccumulation = self.accumulatedpoison
                    self.accumulatedpoison = min(50, self.accumulatedpoison + np.random.rand()*40)
                    if self.accumulatedpoison > 5 and oldaccumulation <= 5:
                        self.log().append('You were poisoned by the gas.')
            if not self.dead:
                self.resolveaction()

                fovmap = fov(self.world.walls, self.x, self.y, self.sight())
                for i in range(self.world.width):
                    for j in range(self.world.height):
                        if fovmap[i,j]:
                            if self.world.walls[i,j]:
                                self.seen()[self.world_i][i][j] = (' ', (0, 0, 0), (128, 128, 128), (0, 0, 0))
                            elif self.world.spiderwebs[i,j]:
                                self.seen()[self.world_i][i][j] = ('#', (128, 128, 128), (0, 0, 0), (0, 0, 0))
                            elif self.world.largerocks[i,j]:
                                self.seen()[self.world_i][i][j] = ('%', (128, 128, 128), (0, 0, 0), (0, 0, 0))
                            elif self.world.campfires[i,j]:
                                self.seen()[self.world_i][i][j] = ('%', (128, 102, 0), (0, 0, 0), (0, 0, 0))
                            else:
                                self.seen()[self.world_i][i][j] = (' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))
                            i, j = self.world.stairsdowncoords
                            if fovmap[i,j]:
                                self.seen()[self.world_i][i][j] = ('>', (128, 128, 128), (0, 0, 0), (0, 0, 0))
                            i, j = self.world.stairsupcoords
                            if fovmap[i,j]:
                                self.seen()[self.world_i][i][j] = ('<', (128, 128, 128), (0, 0, 0), (0, 0, 0))
                            for i, j, _ in self.world.altars:
                                if fovmap[i,j]:
                                    self.seen()[self.world_i][i][j] = ('%', (0, 128, 128), (0, 0, 0), (0, 0, 0))
                            for it in self.world.items:
                                if fovmap[it.x, it.y]:
                                    if not it in self.itemsseen() and not it.hidden:
                                        self.itemsseen().append(it)
                                    if not it in self.itemsseen() and it.hidden:
                                        for part in self.bodyparts:
                                            if np.sqrt((it.x-self.x)**2 + (it.y-self.y)**2) < part.detectiondistance and np.random.rand() < part.detectionprobability:
                                                self.log().append('You noticed ' + it.name + '!')
                                                self.itemsseen().append(it)
                                    if it in self.itemsseen():
                                        self.seen()[self.world_i][it.x][it.y] = ('?', (128, 128, 128), (0, 0, 0), (0, 0, 0))
                for creat in self.world.creatures:
                    if fovmap[creat.x, creat.y] and not creat in self.creaturesseen() and creat != self:
                        self.creaturesseen().append(creat)
                        if self in creat.creaturesseen():
                            self.log().append('You see a ' + creat.name +'. It has noticed you.')
                            fovmap2 = fov(creat.world.walls, creat.x, creat.y, creat.sight())
                            if fovmap2[self.x, self.y]:
                                creat.log().append('The ' + self.name + ' noticed you!')
                        else:
                            self.log().append('You see a ' + creat.name +'. It hasn\'t noticed you.')

                if not self.dead:
                    self.nextaction = self.ai()
                else:
                    self.nextaction = ['wait', 1]
                if self.nextaction[0] == 'fight' and self.previousaction[0] == 'fight' and self.nextaction[3].weapon == self.previousaction[1] and self.nextaction[2] == self.previousaction[2]:
                    self.nextaction[-1] = self.nextaction[-1]*1.5
                self.update(timeleft)

class Zombie(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['undead']
        self.char = 'z'
        self.color = (191, 255, 128)
        self.name = np.random.choice(['zombie', 'headless zombie', 'one-armed zombie', 'crawler zombie'], p=[0.7, 0.1, 0.1, 0.1])
        self.smellname = 'zombie'
        self.x = x
        self.y = y
        self.torso = bodypart.ZombieTorso(self.bodyparts, 0, 0)
        if self.name != 'one-armed zombie':
            self.bodyparts[0].connect('left arm', bodypart.ZombieArm(self.bodyparts, 0, 0))
            self.bodyparts[0].connect('right arm', bodypart.ZombieArm(self.bodyparts, 0, 0))
        else:
            if np.random.choice(2):
                self.bodyparts[0].connect('left arm', bodypart.ZombieArm(self.bodyparts, 0, 0))
            else:
                self.bodyparts[0].connect('right arm', bodypart.ZombieArm(self.bodyparts, 0, 0))
        if self.name != 'crawler zombie':
            self.bodyparts[0].connect('left leg', bodypart.ZombieLeg(self.bodyparts, 0, 0))
            self.bodyparts[0].connect('right leg', bodypart.ZombieLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.ZombieHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.ZombieLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.ZombieLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.ZombieKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.ZombieKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.ZombieStomach(self.bodyparts, 0, 0))
        if self.name != 'headless zombie':
            self.bodyparts[0].connect('head', bodypart.ZombieHead(self.bodyparts, 0, 0))
            self.bodyparts[-1].connect('brain', bodypart.ZombieBrain(self.bodyparts, 0, 0))
            self.bodyparts[-2].connect('left eye', bodypart.ZombieEye(self.bodyparts, 0, 0))
            self.bodyparts[-3].connect('right eye', bodypart.ZombieEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            fovmap2 = fov(self.world.walls, player.x, player.y, player.sight())
            if self.scariness() > 0 and fovmap[player.x, player.y] and fovmap2[self.x, self.y] and self in player.creaturesseen() and not self in player.frightenedby():
                return(['frighten', 0.75])
            else:
                target = None
                if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                    target = player
                elif fovmap[player.x, player.y]:
                    self.targetcoords = (player.x, player.y)
                if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                    i = np.random.choice(range(len(self.attackslist())))
                    atk = self.attackslist()[i]
                    return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
                elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                    # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                    # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                    dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                    if len(dxdylist) > 0:
                        if not self.panicked():
                            dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                        else:
                            dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                        time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                        return(['move', dx, dy, time])
                    else:
                        return(['wait', 1])
                elif not disoriented:
                    self.targetcoords = None
                    dx = 0
                    dy = 0
                    repeats = 0
                    while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                        dx = np.random.choice([-1,0,1])
                        dy = np.random.choice([-1,0,1])
                        repeats += 1
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                        return(['move', dx, dy, time])
                    else:
                        return(['wait', 1])
                else:
                    self.targetcoords = None
                    dx = 0
                    dy = 0
                    while (dx,dy) == (0,0):
                        dx = np.random.choice([-1,0,1])
                        dy = np.random.choice([-1,0,1])
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                        if not self.world.walls[self.x+dx, self.y+dy]:
                            return(['move', dx, dy, time])
                        else:
                            return(['bump', time/2])
                    else:
                        return(['wait', 1])
        else:
            return(['wait', 1])

class MolePerson(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['mole']
        self.char = 'm'
        self.color = (186, 100, 13)
        self.name = 'mole person'
        self.x = x
        self.y = y
        self.torso = bodypart.MolePersonTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.MolePersonArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.MolePersonArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.MolePersonLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.MolePersonLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.MolePersonHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.MolePersonLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.MolePersonLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.MolePersonKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.MolePersonKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.MolePersonStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.MolePersonHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.MolePersonBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.MolePersonEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.MolePersonEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            elif player in self.world.smells[self.x][self.y] and self.world.smells[self.x][self.y][player] > 1/self.senseofsmell():
                strongestsmell = self.world.smells[self.x][self.y][player]
                strongestdcoords = (0, 0)
                for dx2 in [-1, 0, 1]:
                    for dy2 in [-1, 0, 1]:
                        if player in self.world.smells[self.x + dx2][self.y + dy2] and self.world.smells[self.x + dx2][self.y + dy2][player] > strongestsmell:
                            strongestsmell = self.world.smells[self.x + dx2][self.y + dy2][player]
                            strongestdcoords = (dx2, dy2)
                if strongestdcoords != (0, 0):
                    self.targetcoords = (self.x + strongestdcoords[0], self.y + strongestdcoords[1])
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Goblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['goblinoid']
        self.char = 'g'
        self.color = (0, 255, 0)
        self.name = 'goblin'
        self.x = x
        self.y = y
        self.torso = bodypart.GoblinTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.GoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.GoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.GoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.GoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.GoblinHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.GoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.GoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.GoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.GoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.GoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.GoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.GoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.GoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.GoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class GlassElemental(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['elemental']
        self.char = 'g'
        self.color = (0, 255, 255)
        self.name = 'glass elemental'
        self.x = x
        self.y = y
        self.torso = bodypart.GlassElementalTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.GlassElementalArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.GlassElementalArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.GlassElementalHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.GlassElementalLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.GlassElementalLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('tail', bodypart.GlassElementalTail(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.GlassElementalHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.GlassElementalBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('upper left eye', bodypart.GlassElementalEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('upper right eye', bodypart.GlassElementalEye(self.bodyparts, 0, 0))
        self.bodyparts[-4].connect('center left eye', bodypart.GlassElementalEye(self.bodyparts, 0, 0))
        self.bodyparts[-5].connect('center right eye', bodypart.GlassElementalEye(self.bodyparts, 0, 0))
        self.bodyparts[-6].connect('lower left eye', bodypart.GlassElementalEye(self.bodyparts, 0, 0))
        self.bodyparts[-7].connect('lower right eye', bodypart.GlassElementalEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class CaveOctopus(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['octopus']
        self.char = 'o'
        self.color = (255, 0, 255)
        self.name = 'cave octopus'
        self.x = x
        self.y = y
        self.torso = bodypart.OctopusHead(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('front left limb', bodypart.OctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('center-front left limb', bodypart.OctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('center-back left limb', bodypart.OctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back left limb', bodypart.OctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front right limb', bodypart.OctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('center-front right limb', bodypart.OctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('center-back right limb', bodypart.OctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back right limb', bodypart.OctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('central heart', bodypart.OctopusHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left heart', bodypart.OctopusHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right heart', bodypart.OctopusHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left gills', bodypart.OctopusGills(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right gills', bodypart.OctopusGills(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left metanephridium', bodypart.OctopusMetanephridium(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right metanephridium', bodypart.OctopusMetanephridium(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.OctopusStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('brain', bodypart.OctopusBrain(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left eye', bodypart.OctopusEye(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right eye', bodypart.OctopusEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Dog(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['canine']
        self.char = 'd'
        self.color = (170, 130, 70)
        self.name = 'dog'
        self.x = x
        self.y = y
        self.torso = bodypart.DogTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('front left leg', bodypart.DogLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front right leg', bodypart.DogLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back left leg', bodypart.DogLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back right leg', bodypart.DogLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.DogHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.DogLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.DogLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.DogKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.DogKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.DogStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('tail', bodypart.DogTail(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.DogHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.DogBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.DogEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.DogEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            elif player in self.world.smells[self.x][self.y] and self.world.smells[self.x][self.y][player] > 1/self.senseofsmell():
                strongestsmell = self.world.smells[self.x][self.y][player]
                strongestdcoords = (0, 0)
                for dx2 in [-1, 0, 1]:
                    for dy2 in [-1, 0, 1]:
                        if player in self.world.smells[self.x + dx2][self.y + dy2] and self.world.smells[self.x + dx2][self.y + dy2][player] > strongestsmell:
                            strongestsmell = self.world.smells[self.x + dx2][self.y + dy2][player]
                            strongestdcoords = (dx2, dy2)
                if strongestdcoords != (0, 0):
                    self.targetcoords = (self.x + strongestdcoords[0], self.y + strongestdcoords[1])
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                maxdmglist = [atk[8] for atk in self.attackslist()]
                i = maxdmglist.index(max(maxdmglist)) # N.B. DIFFERENT THAN MOST CREATURES!
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Imp(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['demon']
        self.char = 'i'
        self.color = (128, 0, 0)
        self.name = 'imp'
        self.x = x
        self.y = y
        self.torso = bodypart.ImpTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.ImpArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.ImpArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left wing', bodypart.ImpWing(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right wing', bodypart.ImpWing(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.ImpLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.ImpLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.ImpHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.ImpLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.ImpLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.ImpKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.ImpKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.ImpStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.ImpHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.ImpBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.ImpEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.ImpEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        self.stance = 'flying'
        self.preferredstance = 'flying'
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                if self.stance == 'flying':
                    dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                else:
                    dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or (self.world.lavapits[self.x+dx, self.y+dy] != 0 and self.stance != 'flying') or (self.world.campfires[self.x+dx, self.y+dy] != 0 and self.stance != 'flying') or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or (len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0 and self.stance != 'flying'):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Hobgoblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['goblinoid']
        self.char = 'h'
        self.color = (0, 255, 0)
        self.name = 'hobgoblin'
        self.x = x
        self.y = y
        self.torso = bodypart.HobgoblinTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.HobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.HobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.HobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.HobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.HobgoblinHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.HobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.HobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.HobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.HobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.HobgoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.HobgoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.HobgoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.HobgoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.HobgoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class MoleMonk(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['mole']
        self.char = 'M'
        self.color = (186, 100, 13)
        self.name = 'mole monk'
        self.x = x
        self.y = y
        self.torso = bodypart.MoleMonkTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.MoleMonkArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.MoleMonkArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.MoleMonkLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.MoleMonkLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.MoleMonkHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.MoleMonkLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.MoleMonkLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.MoleMonkKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.MoleMonkKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.MoleMonkStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.MoleMonkHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.MoleMonkBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.MoleMonkEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.MoleMonkEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        self.stance = 'fasting'
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            elif player in self.world.smells[self.x][self.y] and self.world.smells[self.x][self.y][player] > 1/self.senseofsmell():
                strongestsmell = self.world.smells[self.x][self.y][player]
                strongestdcoords = (0, 0)
                for dx2 in [-1, 0, 1]:
                    for dy2 in [-1, 0, 1]:
                        if player in self.world.smells[self.x + dx2][self.y + dy2] and self.world.smells[self.x + dx2][self.y + dy2][player] > strongestsmell:
                            strongestsmell = self.world.smells[self.x + dx2][self.y + dy2][player]
                            strongestdcoords = (dx2, dy2)
                if strongestdcoords != (0, 0):
                    self.targetcoords = (self.x + strongestdcoords[0], self.y + strongestdcoords[1])
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class ZombieZorcerer(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['undead']
        self.char = 'Z'
        self.color = (191, 255, 128)
        self.name = np.random.choice(['zombie zorcerer', 'one-armed zombie zorcerer', 'crawler zombie zorcerer'], p=[0.8, 0.1, 0.1])
        self.smellname = 'zombie zorcerer'
        self.x = x
        self.y = y
        self.torso = bodypart.ZombieZorcererTorso(self.bodyparts, 0, 0)
        if self.name != 'one-armed zombie zorcerer':
            self.bodyparts[0].connect('left arm', bodypart.ZombieZorcererArm(self.bodyparts, 0, 0))
            self.bodyparts[0].connect('right arm', bodypart.ZombieZorcererArm(self.bodyparts, 0, 0))
        else:
            if np.random.choice(2):
                self.bodyparts[0].connect('left arm', bodypart.ZombieZorcererArm(self.bodyparts, 0, 0))
            else:
                self.bodyparts[0].connect('right arm', bodypart.ZombieZorcererArm(self.bodyparts, 0, 0))
        if self.name != 'crawler zombie zorcerer':
            self.bodyparts[0].connect('left leg', bodypart.ZombieZorcererLeg(self.bodyparts, 0, 0))
            self.bodyparts[0].connect('right leg', bodypart.ZombieZorcererLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.ZombieZorcererHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.ZombieZorcererLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.ZombieZorcererLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.ZombieZorcererKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.ZombieZorcererKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.ZombieZorcererStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.ZombieZorcererHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.ZombieZorcererBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.ZombieZorcererEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.ZombieZorcererEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            fovmap2 = fov(self.world.walls, player.x, player.y, player.sight())
            if self.scariness() > 0 and fovmap[player.x, player.y] and fovmap2[self.x, self.y] and self in player.creaturesseen() and not self in player.frightenedby():
                return(['frighten', 0.75])
            elif np.any([part.incapacitated() and not part.destroyed() for part in self.bodyparts]) and len([spell for spell in self.spellsknown() if isinstance(spell, magic.HealThyself)]) > 0 and self.mana() >= [spell for spell in self.spellsknown() if isinstance(spell, magic.HealThyself)][0].manarequirement and not self.panicked():
                spell = [spell for spell in self.spellsknown() if isinstance(spell, magic.HealThyself)][0]
                return(['cast', spell, [self, max(spell.choices(self), key=lambda part : part.damagetaken)], spell.castingtime])
            elif fovmap[player.x, player.y] and (abs(self.x - player.x) > 1 or abs(self.y - player.y) > 1) and len([spell for spell in self.spellsknown() if isinstance(spell, (magic.TargetedSpell, magic.BodypartTargetedSpell)) and self.mana() >= spell.manarequirement]) > 0 and not self.panicked():
                spell = np.random.choice([spell for spell in self.spellsknown() if isinstance(spell, (magic.TargetedSpell, magic.BodypartTargetedSpell)) and self.mana() >= spell.manarequirement])
                if isinstance(spell, magic.TargetedSpell):
                    return(['cast', spell, [self, player], spell.castingtime])
                else:
                    return(['cast', spell, [self, player, np.random.choice(spell.partchoices(player))], spell.castingtime])
            else:
                target = None
                if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                    target = player
                elif fovmap[player.x, player.y]:
                    self.targetcoords = (player.x, player.y)
                if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                    i = np.random.choice(range(len(self.attackslist())))
                    atk = self.attackslist()[i]
                    return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
                elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                    # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                    # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                    dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                    if len(dxdylist) > 0:
                        if not self.panicked():
                            dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                        else:
                            dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                        time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                        return(['move', dx, dy, time])
                    else:
                        return(['wait', 1])
                elif not disoriented:
                    self.targetcoords = None
                    dx = 0
                    dy = 0
                    repeats = 0
                    while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                        dx = np.random.choice([-1,0,1])
                        dy = np.random.choice([-1,0,1])
                        repeats += 1
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                        return(['move', dx, dy, time])
                    else:
                        return(['wait', 1])
                else:
                    self.targetcoords = None
                    dx = 0
                    dy = 0
                    while (dx,dy) == (0,0):
                        dx = np.random.choice([-1,0,1])
                        dy = np.random.choice([-1,0,1])
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                        if not self.world.walls[self.x+dx, self.y+dy]:
                            return(['move', dx, dy, time])
                        else:
                            return(['bump', time/2])
                    else:
                        return(['wait', 1])
        else:
            return(['wait', 1])

class Wolf(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['canine']
        self.char = 'w'
        self.color = (100, 100, 150)
        self.name = 'wolf'
        self.x = x
        self.y = y
        self.torso = bodypart.WolfTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('front left leg', bodypart.WolfLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front right leg', bodypart.WolfLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back left leg', bodypart.WolfLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back right leg', bodypart.WolfLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.WolfHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.WolfLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.WolfLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.WolfKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.WolfKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.WolfStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('tail', bodypart.WolfTail(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.WolfHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.WolfBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.WolfEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.WolfEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            elif player in self.world.smells[self.x][self.y] and self.world.smells[self.x][self.y][player] > 1/self.senseofsmell():
                strongestsmell = self.world.smells[self.x][self.y][player]
                strongestdcoords = (0, 0)
                for dx2 in [-1, 0, 1]:
                    for dy2 in [-1, 0, 1]:
                        if player in self.world.smells[self.x + dx2][self.y + dy2] and self.world.smells[self.x + dx2][self.y + dy2][player] > strongestsmell:
                            strongestsmell = self.world.smells[self.x + dx2][self.y + dy2][player]
                            strongestdcoords = (dx2, dy2)
                if strongestdcoords != (0, 0):
                    self.targetcoords = (self.x + strongestdcoords[0], self.y + strongestdcoords[1])
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                maxdmglist = [atk[8] for atk in self.attackslist()]
                i = maxdmglist.index(max(maxdmglist)) # N.B. DIFFERENT THAN MOST CREATURES!
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Drillbot(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['robot']
        self.char = 'd'
        self.color = (150, 150, 150)
        self.name = 'drillbot'
        self.x = x
        self.y = y
        self.torso = bodypart.DrillbotChassis(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('front left wheel', bodypart.DrillbotWheel(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back left wheel', bodypart.DrillbotWheel(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front right wheel', bodypart.DrillbotWheel(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back right wheel', bodypart.DrillbotWheel(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('arm', bodypart.DrillArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('coolant pumping system', bodypart.DrillbotPump(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('coolant aerator system', bodypart.DrillbotAerator(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('coolant filtering system', bodypart.DrillbotFilter(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('biomass processor', bodypart.DrillBotBiomassProcessor(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('central processor', bodypart.DrillbotProcessor(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left camera', bodypart.DrillbotCamera(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right camera', bodypart.DrillbotCamera(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Lobgoblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['goblinoid']
        self.char = 'l'
        self.color = (0, 255, 0)
        self.name = 'lobgoblin'
        self.x = x
        self.y = y
        self.torso = bodypart.LobgoblinTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.LobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.LobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.LobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.LobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.LobgoblinHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.LobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.LobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.LobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.LobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.LobgoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.LobgoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.LobgoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.LobgoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.LobgoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class RevenantCaveOctopus(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['octopus', 'undead']
        self.char = 'r'
        self.color = (255, 0, 255)
        self.name = 'revenant cave octopus'
        self.x = x
        self.y = y
        self.torso = bodypart.RevenantOctopusHead(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('front left limb', bodypart.RevenantOctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('center-front left limb', bodypart.RevenantOctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('center-back left limb', bodypart.RevenantOctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back left limb', bodypart.RevenantOctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front right limb', bodypart.RevenantOctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('center-front right limb', bodypart.RevenantOctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('center-back right limb', bodypart.RevenantOctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back right limb', bodypart.RevenantOctopusTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('central heart', bodypart.RevenantOctopusHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left heart', bodypart.RevenantOctopusHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right heart', bodypart.RevenantOctopusHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left gills', bodypart.RevenantOctopusGills(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right gills', bodypart.RevenantOctopusGills(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left metanephridium', bodypart.RevenantOctopusMetanephridium(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right metanephridium', bodypart.RevenantOctopusMetanephridium(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.RevenantOctopusStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('brain', bodypart.RevenantOctopusBrain(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left eye', bodypart.RevenantOctopusEye(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right eye', bodypart.RevenantOctopusEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Ghoul(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['undead']
        self.char = 'g'
        self.color = (191, 255, 255)
        self.name = np.random.choice(['ghoul', 'headless ghoul', 'one-armed ghoul', 'crawler ghoul'], p=[0.7, 0.1, 0.1, 0.1])
        self.smellname = 'ghoul'
        self.x = x
        self.y = y
        self.torso = bodypart.GhoulTorso(self.bodyparts, 0, 0)
        if self.name != 'one-armed ghoul':
            self.bodyparts[0].connect('left arm', bodypart.GhoulArm(self.bodyparts, 0, 0))
            self.bodyparts[0].connect('right arm', bodypart.GhoulArm(self.bodyparts, 0, 0))
        else:
            if np.random.choice(2):
                self.bodyparts[0].connect('left arm', bodypart.GhoulArm(self.bodyparts, 0, 0))
            else:
                self.bodyparts[0].connect('right arm', bodypart.GhoulArm(self.bodyparts, 0, 0))
        if self.name != 'crawler ghoul':
            self.bodyparts[0].connect('left leg', bodypart.GhoulLeg(self.bodyparts, 0, 0))
            self.bodyparts[0].connect('right leg', bodypart.GhoulLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.GhoulHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.GhoulLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.GhoulLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.GhoulKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.GhoulKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.GhoulStomach(self.bodyparts, 0, 0))
        if self.name != 'headless ghoul':
            self.bodyparts[0].connect('head', bodypart.GhoulHead(self.bodyparts, 0, 0))
            self.bodyparts[-1].connect('brain', bodypart.GhoulBrain(self.bodyparts, 0, 0))
            self.bodyparts[-2].connect('left eye', bodypart.GhoulEye(self.bodyparts, 0, 0))
            self.bodyparts[-3].connect('right eye', bodypart.GhoulEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            fovmap2 = fov(self.world.walls, player.x, player.y, player.sight())
            if self.scariness() > 0 and fovmap[player.x, player.y] and fovmap2[self.x, self.y] and self in player.creaturesseen() and not self in player.frightenedby():
                return(['frighten', 0.75])
            else:
                target = None
                if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                    target = player
                elif fovmap[player.x, player.y]:
                    self.targetcoords = (player.x, player.y)
                if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                    i = np.random.choice(range(len(self.attackslist())))
                    atk = self.attackslist()[i]
                    return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
                elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                    # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                    # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                    dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                    if len(dxdylist) > 0:
                        if not self.panicked():
                            dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                        else:
                            dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                        time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                        return(['move', dx, dy, time])
                    else:
                        return(['wait', 1])
                elif not disoriented:
                    self.targetcoords = None
                    dx = 0
                    dy = 0
                    repeats = 0
                    while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                        dx = np.random.choice([-1,0,1])
                        dy = np.random.choice([-1,0,1])
                        repeats += 1
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                        return(['move', dx, dy, time])
                    else:
                        return(['wait', 1])
                else:
                    self.targetcoords = None
                    dx = 0
                    dy = 0
                    while (dx,dy) == (0,0):
                        dx = np.random.choice([-1,0,1])
                        dy = np.random.choice([-1,0,1])
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                        if not self.world.walls[self.x+dx, self.y+dy]:
                            return(['move', dx, dy, time])
                        else:
                            return(['bump', time/2])
                    else:
                        return(['wait', 1])
        else:
            return(['wait', 1])

class SmallFireElemental(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['elemental']
        self.char = 'f'
        self.color = (255, 204, 0)
        self.name = 'small fire elemental'
        self.x = x
        self.y = y
        self.torso = bodypart.SmallFireElementalTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('front left limb', bodypart.SmallFireElementalTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back left limb', bodypart.SmallFireElementalTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front right limb', bodypart.SmallFireElementalTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back right limb', bodypart.SmallFireElementalTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.SmallFireElementalHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left bellows', bodypart.SmallFireElementalBellows(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right bellows', bodypart.SmallFireElementalBellows(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.SmallFireElementalHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.SmallFireElementalBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('eye', bodypart.SmallFireElementalEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Mobgoblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['goblinoid']
        self.char = 'm'
        self.color = (0, 255, 0)
        self.name = 'mobgoblin'
        self.x = x
        self.y = y
        self.torso = bodypart.MobgoblinTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.MobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.MobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.MobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.MobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.MobgoblinHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.MobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.MobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.MobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.MobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.MobgoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.MobgoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.MobgoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.MobgoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.MobgoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class DireWolf(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['canine']
        self.char = 'd'
        self.color = (100, 100, 150)
        self.name = 'dire wolf'
        self.x = x
        self.y = y
        self.torso = bodypart.DireWolfTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('front left leg', bodypart.DireWolfLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front right leg', bodypart.DireWolfLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back left leg', bodypart.DireWolfLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back right leg', bodypart.DireWolfLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.DireWolfHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.DireWolfLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.DireWolfLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.DireWolfKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.DireWolfKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.DireWolfStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('tail', bodypart.DireWolfTail(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.DireWolfHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.DireWolfBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.DireWolfEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.DireWolfEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            elif player in self.world.smells[self.x][self.y] and self.world.smells[self.x][self.y][player] > 1/self.senseofsmell():
                strongestsmell = self.world.smells[self.x][self.y][player]
                strongestdcoords = (0, 0)
                for dx2 in [-1, 0, 1]:
                    for dy2 in [-1, 0, 1]:
                        if player in self.world.smells[self.x + dx2][self.y + dy2] and self.world.smells[self.x + dx2][self.y + dy2][player] > strongestsmell:
                            strongestsmell = self.world.smells[self.x + dx2][self.y + dy2][player]
                            strongestdcoords = (dx2, dy2)
                if strongestdcoords != (0, 0):
                    self.targetcoords = (self.x + strongestdcoords[0], self.y + strongestdcoords[1])
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                maxdmglist = [atk[8] for atk in self.attackslist()]
                i = maxdmglist.index(max(maxdmglist)) # N.B. DIFFERENT THAN MOST CREATURES!
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Jobgoblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['goblinoid']
        self.char = 'j'
        self.color = (0, 255, 0)
        self.name = 'jobgoblin'
        self.x = x
        self.y = y
        self.torso = bodypart.JobgoblinTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.JobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.JobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.JobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.JobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.JobgoblinHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.JobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.JobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.JobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.JobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.JobgoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.JobgoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.JobgoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.JobgoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.JobgoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Ghast(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['undead']
        self.char = 'g'
        self.color = (191, 255, 255)
        self.name = np.random.choice(['ghast', 'headless ghast', 'one-armed ghast', 'crawler ghast'], p=[0.7, 0.1, 0.1, 0.1])
        self.smellname = 'ghast'
        self.x = x
        self.y = y
        self.torso = bodypart.GhastTorso(self.bodyparts, 0, 0)
        if self.name != 'one-armed ghast':
            self.bodyparts[0].connect('left arm', bodypart.GhastArm(self.bodyparts, 0, 0))
            self.bodyparts[0].connect('right arm', bodypart.GhastArm(self.bodyparts, 0, 0))
        else:
            if np.random.choice(2):
                self.bodyparts[0].connect('left arm', bodypart.GhastArm(self.bodyparts, 0, 0))
            else:
                self.bodyparts[0].connect('right arm', bodypart.GhastArm(self.bodyparts, 0, 0))
        if self.name != 'crawler ghast':
            self.bodyparts[0].connect('left leg', bodypart.GhastLeg(self.bodyparts, 0, 0))
            self.bodyparts[0].connect('right leg', bodypart.GhastLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.GhastHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.GhastLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.GhastLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.GhastKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.GhastKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.GhastStomach(self.bodyparts, 0, 0))
        if self.name != 'headless ghast':
            self.bodyparts[0].connect('head', bodypart.GhastHead(self.bodyparts, 0, 0))
            self.bodyparts[-1].connect('brain', bodypart.GhastBrain(self.bodyparts, 0, 0))
            self.bodyparts[-2].connect('left eye', bodypart.GhastEye(self.bodyparts, 0, 0))
            self.bodyparts[-3].connect('right eye', bodypart.GhastEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            fovmap2 = fov(self.world.walls, player.x, player.y, player.sight())
            if self.scariness() > 0 and fovmap[player.x, player.y] and fovmap2[self.x, self.y] and self in player.creaturesseen() and not self in player.frightenedby():
                return(['frighten', 0.75])
            else:
                target = None
                if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                    target = player
                elif fovmap[player.x, player.y]:
                    self.targetcoords = (player.x, player.y)
                if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                    i = np.random.choice(range(len(self.attackslist())))
                    atk = self.attackslist()[i]
                    return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
                elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                    # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                    # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                    dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                    if len(dxdylist) > 0:
                        if not self.panicked():
                            dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                        else:
                            dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                        time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                        return(['move', dx, dy, time])
                    else:
                        return(['wait', 1])
                elif not disoriented:
                    self.targetcoords = None
                    dx = 0
                    dy = 0
                    repeats = 0
                    while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                        dx = np.random.choice([-1,0,1])
                        dy = np.random.choice([-1,0,1])
                        repeats += 1
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                        return(['move', dx, dy, time])
                    else:
                        return(['wait', 1])
                else:
                    self.targetcoords = None
                    dx = 0
                    dy = 0
                    while (dx,dy) == (0,0):
                        dx = np.random.choice([-1,0,1])
                        dy = np.random.choice([-1,0,1])
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                        if not self.world.walls[self.x+dx, self.y+dy]:
                            return(['move', dx, dy, time])
                        else:
                            return(['bump', time/2])
                    else:
                        return(['wait', 1])
        else:
            return(['wait', 1])

class Nobgoblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['goblinoid']
        self.char = 'n'
        self.color = (0, 255, 0)
        self.name = 'nobgoblin'
        self.x = x
        self.y = y
        self.torso = bodypart.NobgoblinTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.NobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.NobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.NobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.NobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.NobgoblinHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.NobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.NobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.NobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.NobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.NobgoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.NobgoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.NobgoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.NobgoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.NobgoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Warg(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['canine']
        self.char = 'W'
        self.color = (150, 150, 1200)
        self.name = 'warg'
        self.x = x
        self.y = y
        self.torso = bodypart.WargTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('front left leg', bodypart.WargLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front right leg', bodypart.WargLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back left leg', bodypart.WargLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back right leg', bodypart.WargLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.WargHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.WargLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.WargLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.WargKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.WargKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.WargStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('tail', bodypart.WargTail(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.WargHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.WargBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.WargEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.WargEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            elif player in self.world.smells[self.x][self.y] and self.world.smells[self.x][self.y][player] > 1/self.senseofsmell():
                strongestsmell = self.world.smells[self.x][self.y][player]
                strongestdcoords = (0, 0)
                for dx2 in [-1, 0, 1]:
                    for dy2 in [-1, 0, 1]:
                        if player in self.world.smells[self.x + dx2][self.y + dy2] and self.world.smells[self.x + dx2][self.y + dy2][player] > strongestsmell:
                            strongestsmell = self.world.smells[self.x + dx2][self.y + dy2][player]
                            strongestdcoords = (dx2, dy2)
                if strongestdcoords != (0, 0):
                    self.targetcoords = (self.x + strongestdcoords[0], self.y + strongestdcoords[1])
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                maxdmglist = [atk[8] for atk in self.attackslist()]
                i = maxdmglist.index(max(maxdmglist)) # N.B. DIFFERENT THAN MOST CREATURES!
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Fobgoblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['goblinoid']
        self.char = 'f'
        self.color = (0, 255, 0)
        self.name = 'fobgoblin'
        self.x = x
        self.y = y
        self.torso = bodypart.FobgoblinTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.FobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.FobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.FobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.FobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.FobgoblinHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.FobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.FobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.FobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.FobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.FobgoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.FobgoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.FobgoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.FobgoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.FobgoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class LargeFireElemental(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['elemental']
        self.char = 'F'
        self.color = (255, 204, 0)
        self.name = 'large fire elemental'
        self.x = x
        self.y = y
        self.torso = bodypart.LargeFireElementalTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.LargeFireElementalArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.LargeFireElementalArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front left limb', bodypart.LargeFireElementalTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back left limb', bodypart.LargeFireElementalTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('front right limb', bodypart.LargeFireElementalTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('back right limb', bodypart.LargeFireElementalTentacle(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.LargeFireElementalHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left bellows', bodypart.LargeFireElementalBellows(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right bellows', bodypart.LargeFireElementalBellows(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.LargeFireElementalHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.LargeFireElementalBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.LargeFireElementalEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.LargeFireElementalEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Dobgoblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.factions = ['goblinoid']
        self.char = 'f'
        self.color = (0, 255, 0)
        self.name = 'dobgoblin'
        self.x = x
        self.y = y
        self.torso = bodypart.DobgoblinTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.DobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.DobgoblinArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.DobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.DobgoblinLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.DobgoblinHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left lung', bodypart.DobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right lung', bodypart.DobgoblinLung(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left kidney', bodypart.DobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right kidney', bodypart.DobgoblinKidney(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.DobgoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.DobgoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.DobgoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.DobgoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.DobgoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        disoriented = False
        if (self.disorientedclock > 0 and np.random.rand() < 0.5) or (self.imbalanced() and np.random.rand() < 0.2):
            disoriented = True
            self.log().append('You stumble around.')
        if len([creature for creature in self.world.creatures if 'player' in creature.factions]) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if 'player' in creature.factions][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0 and not disoriented and not self.panicked():
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.internal() and not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords and not disoriented:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy] and not self.world.lavapits[self.x+dx, self.y+dy] and not self.world.campfires[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    if not self.panicked():
                        dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    else:
                        dx, dy = max(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            elif not disoriented:
                self.targetcoords = None
                dx = 0
                dy = 0
                repeats = 0
                while repeats < 10 and (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0 or self.world.lavapits[self.x+dx, self.y+dy] != 0 or self.world.campfires[self.x+dx, self.y+dy] != 0 or (self.world.poisongas[self.x+dx, self.y+dy] != 0 and self.world.poisongas[self.x, self.y] == 0) or len([it for it in self.world.items if (it.x, it.y) == (self.x+dx, self.y+dy) and it.trap and (it in self.itemsseen() or not it.hidden)]) > 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                    repeats += 1
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if repeats < 10 and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0):
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime() * (1 + (self.world.largerocks[player.x+dx, player.y+dy] and self.stance != 'flying'))
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    if not self.world.walls[self.x+dx, self.y+dy]:
                        return(['move', dx, dy, time])
                    else:
                        return(['bump', time/2])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])



enemytypesbylevel = [ # List of tuples for each level. Each tuple is an enemy type and a probability weight for its presence.
    [(Zombie, 10), (MolePerson, 10), (Goblin, 10), (GlassElemental, 10)], # 1
    [(Zombie, 15), (MolePerson, 15), (Goblin, 15), (GlassElemental, 15), (CaveOctopus, 20), (Dog, 20), (Imp, 20)], # 2
    [(CaveOctopus, 10), (Dog, 10), (Imp, 10), (Hobgoblin, 10), (MoleMonk, 10), (ZombieZorcerer, 10)], # 3
    [(Hobgoblin, 5), (MoleMonk, 5), (ZombieZorcerer, 5), (Wolf, 15)], # 4
    [(Wolf, 15), (Drillbot, 5), (Lobgoblin, 5), (RevenantCaveOctopus, 5)], # 5
    [(Drillbot, 5), (Lobgoblin, 5), (RevenantCaveOctopus, 5), (Ghoul, 15)], # 6
    [(Ghoul, 10), (SmallFireElemental, 5), (Mobgoblin, 5)], # 7
    [(SmallFireElemental, 5), (Mobgoblin, 5), (DireWolf, 10)], # 8
    [(DireWolf, 10), (Jobgoblin, 10)], # 9
    [(Jobgoblin, 10), (Ghast, 10)], # 10
    [(Ghast, 10), (Nobgoblin, 10)], # 11
    [(Nobgoblin, 10), (Warg, 10)], # 12
    [(Warg, 10), (Fobgoblin, 10)], # 13
    [(Fobgoblin, 10), (LargeFireElemental, 10)], # 14
    [(LargeFireElemental, 10), (Dobgoblin, 10)] # 15
    ]