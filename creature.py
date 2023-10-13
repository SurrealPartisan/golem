# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 21:16:44 2022

@author: SurrealPartisan
"""

import numpy as np
import bodypart
import item
from utils import fov, listwithowner, numlevels

def checkitems(creat, cave, x,y):
    for it in cave.items:
        if it.x == x and it.y == y:
            creat.log().append('There is a ' + it.name + ' here.')

class Creature():
    def __init__(self, world, world_i):
        self.world = world
        self.world_i = world_i
        self.max_world_i = world_i
        self.faction = ''
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

    def log(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not part.destroyed()]
        if len(brains) > 0:
            return brains[0].log
        else:
            if not self.dead:
                return ['You have no brain, so nothing is logged.']
            else:
                return ['You have no brain, so nothing is logged.', 'You are dead!', 'Press escape to end.']

    def seen(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not part.destroyed()]
        if len(brains) > 0:
            return brains[0].seen
        else:
            seenlist = []
            for i in range(numlevels):
                seenlist.append(np.zeros((self.world.width, self.world.height)))
            return seenlist

    def godsknown(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not part.destroyed()]
        if len(brains) > 0:
            return brains[0].godsknown
        else:
            return []

    def curesknown(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not part.destroyed()]
        if len(brains) > 0:
            return brains[0].curesknown
        else:
            return []

    def creaturesseen(self):
        brains = [part for part in self.bodyparts if 'brain' in part.categories and not part.destroyed()]
        if len(brains) > 0:
            return brains[0].creaturesseen
        else:
            return []

    def carryingcapacity(self):
        wornlist = [it[0] for part in self.bodyparts for it in part.worn.values() if len(it) > 0]
        return sum([part.carryingcapacity for part in self.bodyparts]) + sum([it.carryingcapacity for it in wornlist])

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
        self.hunger += livingmass*time*2e-06

    def starve(self):
        part = np.random.choice([part for part in self.bodyparts if part.material == 'living flesh' and not part.destroyed()])
        part.damagetaken += 1
        if part.damagetaken > part.maxhp:
            part.damagetaken = part.maxhp
        if part.parentalconnection != None:
            partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
        elif part == self.torso:
            partname = 'torso'
        if not part.destroyed():
            self.log().append('Your ' + partname + ' took 1 damage from starvation.')
        else:
            self.log().append('Your ' + partname + ' was destroyed by starvation.')
        if self.dying():
            self.log().append("You are dead!")
            self.die()
            self.causeofdeath = ('starvation',)

    def burdened(self):
        return self.weightcarried() > self.carryingcapacity()/2

    def overloaded(self):
        return self.weightcarried() > self.carryingcapacity()
    
    def slowed(self):
        return self.world.spiderwebs[self.x, self.y]
    
    def speed(self):
        if self.overloaded():
            return 0
        elif self.burdened():
            return max([part.speed() for part in self.bodyparts]) / 2
        else:
            return max([part.speed() for part in self.bodyparts])

    def steptime(self):
        return 1/self.speed()

    def move(self, dx, dy):
        self.x_old = self.x
        self.y_old = self.y
        self.x += dx
        self.y += dy
        if self.world.spiderwebs[self.x, self.y]:
            self.log().append('There is spiderweb here.')
        if (self.x, self.y) == self.world.stairsupcoords:
            self.log().append('There are stairs up here.')
        if (self.x, self.y) == self.world.stairsdowncoords:
            self.log().append('There are stairs down here.')
        for x, y, gd in self.world.altars:
            if (self.x, self.y) == (x, y):
                self.log().append('There is an altar of ' + gd.name + ' here.')
                if not gd in self.godsknown():
                    self.godsknown().append(gd)
                    self.log().append('You learn the ways of ' + gd.name + ', the ' + gd.faction + '-god of ' + gd.sin + '.')
                    self.log().append(gd.pronoun.capitalize() + ' ' + gd.copula + ' a ' + gd.power + ' and ' + gd.attitude + ' god.')
        checkitems(self, self.world, self.x, self.y)

    def pray(self, gd):
        self.log().append('You prayed to ' + gd.name + '.')
        gd.answer_to_prayer(self)

    def minespeed(self):
        return max([part.minespeed() for part in self.bodyparts])

    def minetime(self):
        return 1/self.minespeed()

    def sight(self):
        return 1 + sum([part.sight() for part in self.bodyparts])
    
    def heal(self, part, hpgiven):
        healed = min(hpgiven, part.damagetaken)
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
            if not part.destroyed():
                self.log().append('Your ' + partname + ' was harmed by ' + repr(-healed) + ' points.')
            else:
                self.log().append('Your ' + partname + ' was destroyed.')
            if self.dying():
                self.log().append("You are dead!")
                self.die()
        else:
            self.log().append('You were unaffected.')

    def dying(self):
        return self.dead or sum([part.damagetaken for part in self.bodyparts]) >= sum([part.maxhp for part in self.bodyparts])/2 or np.any([part.vital() and part.destroyed() for part in self.bodyparts])

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

    def attackslist(self):
        return [attack for part in self.bodyparts for attack in part.attackslist()]
    
    def fight(self, target, targetbodypart, attack):
        if abs(self.x - target.x) <= 1 and abs(self.y - target.y) <= 1:
            if np.random.rand() < max(min(attack.hitprobability*targetbodypart.defensecoefficient(), 0.95), 0.05):
                hit = True
            else:
                adjacentparts = [connection.child for connection in targetbodypart.childconnections.values() if not connection.child == None and not connection.child.destroyed()]
                if targetbodypart.parentalconnection != None and not targetbodypart.parentalconnection.parent.destroyed():
                    adjacentparts.append(targetbodypart.parentalconnection.parent)
                if len(adjacentparts) > 0:
                    targetbodypart = np.random.choice(adjacentparts)
                    if np.random.rand() < max(min(attack.hitprobability*targetbodypart.defensecoefficient(), 0.95), 0.05):
                        hit = True
                    else:
                        hit = False
                else:
                    hit = False
            if hit:
                target.lasthitter = self
                totaldamage = np.random.randint(attack.mindamage, attack.maxdamage+1)
                knocked_back = False
                knocked_to_wall = False
                for special in attack.special:
                    if special[0] == 'charge' and self.previousaction == 'move' and np.sqrt((self.x-target.x)**2 + (self.y-target.y)**2) < np.sqrt((self.x_old-target.x)**2 + (self.y_old-target.y)**2):
                        totaldamage = int(1.5*totaldamage)
                        attack = item.Attack(attack[0], 'charged', 'charged', attack[3], attack[4], attack[5], attack[6], attack[7], attack[8], attack[9], attack[10])
                    if special[0] == 'knockback' and np.random.rand() < special[1]:
                        dx = target.x - self.x
                        dy = target.y - self.y
                        if self.world.walls[target.x+dx, target.y+dy]:
                            knocked_to_wall = True
                            totaldamage *= 2
                        elif not np.any([creat.x == target.x+dx and creat.y == target.y+dy for creat in self.world.creatures]):
                            knocked_back = True
                            target.move(dx, dy)
                if targetbodypart.armor() != None:
                    armor = targetbodypart.armor()
                    armordamage = min(armor.hp(), min(totaldamage, np.random.randint(armor.mindamage, armor.maxdamage+1)))
                    armor.damagetaken += armordamage
                else:
                    armor = None
                    armordamage = 0
                if target.faction in attack.bane:
                    banemultiplier = 2
                else:
                    banemultiplier = 1
                bleed = False
                for special in attack.special:
                    if special[0] == 'bleed' and np.random.rand() < special[1]:
                        bleed = True
                        targetbodypart.bleedclocks.append((banemultiplier*(totaldamage - armordamage), 0, self))
                damage = min(banemultiplier*(totaldamage - armordamage), targetbodypart.hp())
                targetbodypart.damagetaken += damage
                if targetbodypart.parentalconnection != None:
                    partname = list(targetbodypart.parentalconnection.parent.childconnections.keys())[list(targetbodypart.parentalconnection.parent.childconnections.values()).index(targetbodypart.parentalconnection)]
                elif targetbodypart == target.torso:
                    partname = 'torso'
                if not target.dying():
                    if not targetbodypart.destroyed():
                        if not bleed and not knocked_back and not knocked_to_wall:
                            self.log().append('You ' + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', dealing ' + repr(damage) + ' damage!')
                            target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', dealing ' + repr(damage) + ' damage!')
                        elif bleed:
                            self.log().append('You ' + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', dealing ' + repr(damage) + ' damage and making it bleed!')
                            target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', dealing ' + repr(damage) + ' damage and making you bleed!')
                        elif knocked_back:
                            self.log().append('You ' + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', dealing ' + repr(damage) + ' damage and knocking it back!')
                            target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', dealing ' + repr(damage) + ' damage and knocking you back!')
                        elif knocked_to_wall:
                            self.log().append('You ' + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', dealing ' + repr(damage) + ' damage and knocking it against the wall!')
                            target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', dealing ' + repr(damage) + ' damage and knocking you against the wall!')
                        if armordamage > 0:
                            if not armor.destroyed():
                                target.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                            else:
                                target.log().append('Your ' + armor.name + ' was destroyed!')
                                armor.owner.remove(armor)
                    else:
                        if not knocked_back and not knocked_to_wall:
                            self.log().append('You ' + attack.verb2nd +' and destroyed the ' + partname + ' of the ' + target.name + attack.post2nd + '!')
                            target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' and destroyed your ' + partname + attack.post3rd + '!')
                        elif knocked_back:
                            self.log().append('You ' + attack.verb2nd +' and destroyed the ' + partname + ' of the ' + target.name + attack.post2nd + ', knocking it back!')
                            target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' and destroyed your ' + partname + attack.post3rd + ', knocking you back!')
                        elif knocked_to_wall:
                            self.log().append('You ' + attack.verb2nd +' and destroyed the ' + partname + ' of the ' + target.name + attack.post2nd + ', knocking it against the wall!')
                            target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' and destroyed your ' + partname + attack.post3rd + ', knocking you against the wall!')
                        if armordamage > 0:
                            if not armor.destroyed():
                                target.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                            else:
                                target.log().append('Your ' + armor.name + ' was also destroyed!')
                                armor.owner.remove(armor)
                        if targetbodypart.capableofwielding:
                            for it in targetbodypart.wielded:
                                it.owner.remove(it)
                                target.world.items.append(it)
                                it.owner = target.world.items
                                it.x = target.x
                                it.y = target.y
                                target.log().append('You dropped your ' + it.name)
                        for it in [l[0] for l in targetbodypart.worn.values() if len(l) > 0]:
                            it.owner.remove(it)
                            target.world.items.append(it)
                            it.owner = target.world.items
                            it.x = target.x
                            it.y = target.y
                            target.log().append('You dropped your ' + it.name)
                else:
                    if not knocked_back and not knocked_to_wall:
                        self.log().append('You ' + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', killing it!')
                        target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', killing you!')
                    elif knocked_back:
                        self.log().append('You ' + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', knocking it back and killing it!')
                        target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', knocking you back and killing you!')
                    elif knocked_to_wall:
                        self.log().append('You ' + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', knocking it against the wall and killing it!')
                        target.log().append('The ' + self.name + ' ' + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', knocking you against the wall and killing you!')
                    target.log().append('You are dead!')
                    target.die()
                    target.causeofdeath = ('attack', self)
            else:
                self.log().append('The ' + target.name + ' evaded your ' + attack.name +'!')
                target.log().append("You evaded the " + self.name + "'s " + attack.name +"!")
        else:
            self.log().append('The ' + target.name + ' evaded your ' + attack.name + '!')
            target.log().append("You evaded the " + self.name + "'s " + attack.name + "!")

    def bleed(self, time):
        totalcausers = []
        for part in self.bodyparts:
            if part.parentalconnection != None:
                partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
            elif part == self.torso:
                partname = 'torso'
            bled, causers = part.bleed(time)
            totalcausers += causers
            if bled > 0:
                if part.destroyed():
                    self.log().append('Your ' + partname + ' bled out.')
                else:
                    self.log().append('Your ' + partname + ' took ' + repr(bled) + ' damage from bleeding.')
        if self.dying():
            self.log().append('You are dead!')
            for creat in self.world.creatures:
                fovmap = fov(creat.world.walls, creat.x, creat.y, creat.sight())
                if fovmap[self.x, self.y] and creat != self:
                    creat.log().append('The ' + self.name + ' bled to death!')
            self.die()
            self.causeofdeath = ('bloodloss', np.unique(totalcausers))

    def ai(self):
        # Return something to put in self.nextaction. It should be a list,
        # starting with action string, followed by parameters, last of which is
        # the time needed.
        return ['wait', 1]

    def resolveaction(self):
        if self.nextaction[0] == 'move':
            creaturesintheway = [creature for creature in self.world.creatures if creature.x == self.x+self.nextaction[1] and creature.y == self.y+self.nextaction[2]]
            if len(creaturesintheway) == 0:
                self.move(self.nextaction[1], self.nextaction[2])
                self.previousaction = 'move'
            else:
                self.log().append("There's a " + creaturesintheway[0].name + " in your way.")
                self.previousaction = 'wait'
        elif self.nextaction[0] == 'fight':
            if not self.nextaction[1].dead:  # prevent a crash
                self.fight(self.nextaction[1], self.nextaction[2], self.nextaction[3])
                self.previousaction = 'fight'

    def update(self, time):
        if time < self.nextaction[-1]*(1 + self.slowed()*(self.nextaction[0] != 'wait')):
            self.nextaction[-1] -= time/(1 + self.slowed()*(self.nextaction[0] != 'wait'))
            self.bleed(time)
        else:
            timeleft = time - self.nextaction[-1]*(1 + self.slowed()*(self.nextaction[0] != 'wait'))
            self.bleed(self.nextaction[-1]*(1 + self.slowed()*(self.nextaction[0] != 'wait')))
            if not self.dead:
                self.resolveaction()
    
                fovmap = fov(self.world.walls, self.x, self.y, self.sight())
                for i in range(self.world.width):
                    for j in range(self.world.height):
                        if fovmap[i,j]:
                            self.seen()[self.world_i][i,j] = 1
                for creat in self.world.creatures:
                    if fovmap[creat.x, creat.y] and not creat in self.creaturesseen() and creat != self:
                        self.creaturesseen().append(creat)
                        self.log().append('You see a ' + creat.name +'.')
    
                self.nextaction = self.ai()
                self.update(timeleft)

class Zombie(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'undead'
        self.char = 'z'
        self.color = (191, 255, 128)
        self.name = np.random.choice(['zombie', 'headless zombie', 'one-armed zombie', 'crawler zombie'], p=[0.7, 0.1, 0.1, 0.1])
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
        self.bodyparts[0].connect('stomach', bodypart.ZombieStomach(self.bodyparts, 0, 0))
        if self.name != 'headless zombie':
            self.bodyparts[0].connect('head', bodypart.ZombieHead(self.bodyparts, 0, 0))
            self.bodyparts[-1].connect('brain', bodypart.ZombieBrain(self.bodyparts, 0, 0))
            self.bodyparts[-2].connect('left eye', bodypart.ZombieEye(self.bodyparts, 0, 0))
            self.bodyparts[-3].connect('right eye', bodypart.ZombieEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class MolePerson(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'mole'
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
        self.bodyparts[0].connect('stomach', bodypart.MolePersonStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.MolePersonHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.MolePersonBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.MolePersonEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.MolePersonEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class CaveOctopus(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'octopus'
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
        self.bodyparts[0].connect('heart', bodypart.OctopusHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('stomach', bodypart.OctopusStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('brain', bodypart.OctopusBrain(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left eye', bodypart.OctopusEye(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right eye', bodypart.OctopusEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Hobgoblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'goblinoid'
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
        self.bodyparts[0].connect('stomach', bodypart.HobgoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.HobgoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.HobgoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.HobgoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.HobgoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Wolf(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'canine'
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
        self.bodyparts[0].connect('stomach', bodypart.WolfStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('tail', bodypart.WolfTail(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.WolfHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.WolfBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.WolfEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.WolfEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                maxdmglist = [atk[8] for atk in self.attackslist()]
                i = maxdmglist.index(max(maxdmglist)) # N.B. DIFFERENT THAN MOST CREATURES!
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Drillbot(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'robot'
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
        self.bodyparts[0].connect('biomass processor', bodypart.DrillBotBiomassProcessor(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('central processor', bodypart.DrillbotProcessor(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left camera', bodypart.DrillbotCamera(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right camera', bodypart.DrillbotCamera(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Ghoul(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'undead'
        self.char = 'g'
        self.color = (191, 255, 255)
        self.name = np.random.choice(['ghoul', 'headless ghoul', 'one-armed ghoul', 'crawler ghoul'], p=[0.7, 0.1, 0.1, 0.1])
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
        self.bodyparts[0].connect('stomach', bodypart.GhoulStomach(self.bodyparts, 0, 0))
        if self.name != 'headless ghoul':
            self.bodyparts[0].connect('head', bodypart.GhoulHead(self.bodyparts, 0, 0))
            self.bodyparts[-1].connect('brain', bodypart.GhoulBrain(self.bodyparts, 0, 0))
            self.bodyparts[-2].connect('left eye', bodypart.GhoulEye(self.bodyparts, 0, 0))
            self.bodyparts[-3].connect('right eye', bodypart.GhoulEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class SmallFireElemental(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'elemental'
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
        self.bodyparts[0].connect('head', bodypart.SmallFireElementalHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.SmallFireElementalBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('eye', bodypart.SmallFireElementalEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class DireWolf(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'canine'
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
        self.bodyparts[0].connect('stomach', bodypart.DireWolfStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('tail', bodypart.DireWolfTail(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.DireWolfHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.DireWolfBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.DireWolfEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.DireWolfEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                maxdmglist = [atk[8] for atk in self.attackslist()]
                i = maxdmglist.index(max(maxdmglist)) # N.B. DIFFERENT THAN MOST CREATURES!
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])

class Jobgoblin(Creature):
    def __init__(self, world, world_i, x, y):
        super().__init__(world, world_i)
        self.faction = 'goblinoid'
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
        self.bodyparts[0].connect('stomach', bodypart.JobgoblinStomach(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.JobgoblinHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.JobgoblinBrain(self.bodyparts, 0, 0))
        self.bodyparts[-2].connect('left eye', bodypart.JobgoblinEye(self.bodyparts, 0, 0))
        self.bodyparts[-3].connect('right eye', bodypart.JobgoblinEye(self.bodyparts, 0, 0))
        self.targetcoords = None
        
    def ai(self):
        if len([creature for creature in self.world.creatures if creature.faction == 'player']) > 0:  # This is for preventing a crash when player dies.
            player = [creature for creature in self.world.creatures if creature.faction == 'player'][0]
            fovmap = fov(self.world.walls, self.x, self.y, self.sight())
            target = None
            if abs(self.x - player.x) <= 1 and abs(self.y - player.y) <= 1:
                target = player
            elif fovmap[player.x, player.y]:
                self.targetcoords = (player.x, player.y)
            if target != None and len(self.attackslist()) > 0:
                i = np.random.choice(range(len(self.attackslist())))
                atk = self.attackslist()[i]
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), atk, atk[6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                # dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                # dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]]
                if len(dxdylist) > 0:
                    dx, dy = min(dxdylist, key=lambda dxdy : np.sqrt((self.x + dxdy[0] - self.targetcoords[0])**2 + (self.y + dxdy[1] - self.targetcoords[1])**2))
                    time = np.sqrt(dx**2 + dy**2) * self.steptime()
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
            else:
                self.targetcoords = None
                dx = 0
                dy = 0
                while (dx,dy) == (0,0) or self.world.walls[self.x+dx, self.y+dy] != 0:
                    dx = np.random.choice([-1,0,1])
                    dy = np.random.choice([-1,0,1])
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0:
                    return(['move', dx, dy, time])
                else:
                    return(['wait', 1])
        else:
            return(['wait', 1])



enemytypesbylevel = [ # List of tuples for each level. Each tuple is an enemy type and a propability weight for its presence.
    [(Zombie, 10), (MolePerson, 10)],
    [(Zombie, 5), (MolePerson, 5), (CaveOctopus, 10)],
    [(CaveOctopus, 10), (Hobgoblin, 10)],
    [(Hobgoblin, 10), (Wolf, 10)],
    [(Wolf, 10), (Drillbot, 10)],
    [(Drillbot, 10), (Ghoul, 10)],
    [(Ghoul, 10), (SmallFireElemental, 10)],
    [(SmallFireElemental, 10), (DireWolf, 10)],
    [(DireWolf, 10), (Jobgoblin, 10)]
    ]