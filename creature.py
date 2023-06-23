# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 21:16:44 2022

@author: SurrealPartisan
"""

import numpy as np
import bodypart
from utils import fov, anglebetween, numlevels

class Creature():
    def __init__(self, world):
        self.world = world
        self.faction = ''
        self.char = '@'
        self.name = 'golem'
        self.x = 0
        self.y = 0
        self.inventory = []
        self.log = []
        self.seen = []
        for i in range(numlevels):
            self.seen.append(np.zeros((world.width, world.height)))
        self.nextaction = ['wait', 1]
        self.bodyparts = []
        self.torso = None

    def speed(self):
        return max([part.speed() for part in self.bodyparts])

    def steptime(self):
        return 1/self.speed()

    def move(self, dx, dy):
        self.y += dy
        self.x += dx

    def minespeed(self):
        return max([part.minespeed() for part in self.bodyparts])

    def minetime(self):
        return 1/self.minespeed()

    def sight(self):
        return 1 + sum([part.sight() for part in self.bodyparts])
    
    def heal(self, part, hpgiven):
        healed = max(hpgiven, part.damagetaken)
        part.damagetaken -= healed
        return healed

    def dying(self):
        return sum([part.damagetaken for part in self.bodyparts]) > sum([part.maxhp for part in self.bodyparts])/2 or np.any([part.vital() and part.destroyed() for part in self.bodyparts])

    def die(self):
        self.world.creatures.remove(self)
        for it in self.inventory:
            it.owner = self.world.items
            self.world.items.append(it)
            self.inventory.remove(it)
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

    def attackslist(self):
        return [attack for part in self.bodyparts for attack in part.attackslist()]
    
    def fight(self, target, targetbodypart, attack):
        if abs(self.x - target.x) <= 1 and abs(self.y - target.y) <= 1:
            if np.random.rand() < max(min(attack.hitprobability*targetbodypart.defensecoefficient(), 0.95), 0.05):
                damage = min(np.random.randint(attack.mindamage, attack.maxdamage+1), targetbodypart.hp())
                targetbodypart.damagetaken += damage
                if targetbodypart.parentalconnection != None:
                    partname = list(targetbodypart.parentalconnection.parent.childconnections.keys())[list(targetbodypart.parentalconnection.parent.childconnections.values()).index(targetbodypart.parentalconnection)]
                elif targetbodypart == target.torso:
                    partname = 'torso'
                if not target.dying():
                    if not targetbodypart.destroyed():
                        self.log.append('You ' + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', dealing ' + repr(damage) + ' damage!')
                        target.log.append('The ' + self.name + ' ' + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', dealing ' + repr(damage) + ' damage!')
                    else:
                        self.log.append('You ' + attack.verb2nd +' and destroyed the ' + partname + ' of the ' + target.name + attack.post2nd + '!')
                        target.log.append('The ' + self.name + ' ' + attack.verb3rd + ' and destroyed your ' + partname + attack.post3rd + '!')
                else:
                    self.log.append('You ' + attack.verb2nd +' the ' + target.name + ' in the ' + partname + attack.post2nd + ', killing it!')
                    target.log.append('The ' + self.name + ' ' + attack.verb3rd + ' you in the ' + partname + attack.post3rd + ', killing you!')
                    target.log.append('You are dead!')
                    target.die()
            else:
                self.log.append('The ' + target.name + ' evaded your attack!')
                target.log.append("You evaded the " + self.name + "'s attack!")
        else:
            self.log.append('The ' + target.name + ' evaded your attack!')
            target.log.append("You evaded the " + self.name + "'s attack!")

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
            else:
                self.log.append("There's a " + creaturesintheway[0].name + " in your way.")
        elif self.nextaction[0] == 'fight':
            self.fight(self.nextaction[1], self.nextaction[2], self.nextaction[3])
    
    def update(self, time):
        if time < self.nextaction[-1]:
            self.nextaction[-1] -= time
        else:
            timeleft = time - self.nextaction[-1]
            self.resolveaction()
            self.nextaction = self.ai()
            self.update(timeleft)

class Zombie(Creature):
    def __init__(self, world, x, y):
        super().__init__(world)
        self.faction = 'zombie'
        self.char = 'z'
        self.name = 'zombie'
        self.x = x
        self.y = y
        self.hp = 10
        self.torso = bodypart.ZombieTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.ZombieArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.ZombieArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.ZombieLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.ZombieLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.ZombieHeart(self.bodyparts, 0, 0))
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
                return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), self.attackslist()[0], self.attackslist()[0][6]])
            elif self.targetcoords != None and (self.x, self.y) != self.targetcoords:
                dx = round(np.cos(anglebetween((self.x, self.y), self.targetcoords)))
                dy = round(np.sin(anglebetween((self.x, self.y), self.targetcoords)))
                time = np.sqrt(dx**2 + dy**2) * self.steptime()
                if len([creature for creature in self.world.creatures if creature.x == self.x+dx and creature.y == self.y+dy]) == 0 and not self.world.walls[self.x+dx, self.y+dy]:
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