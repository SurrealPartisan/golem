# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 21:16:44 2022

@author: SurrealPartisan
"""

import numpy as np
import item
from item import Attack
import bodypart

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
        self.seen = np.zeros((world.width, world.height))
        self.nextaction = ['wait', 1]
        self.bodyparts = []
        self.torso = None

    def speed(self):
        return max([part.speed() for part in self.bodyparts])

    def sight(self):
        return 1 + sum([part.sight() for part in self.bodyparts])

    def steptime(self):
        return 1/self.speed()
    
    def move(self, x, y):
        if self.world.walls[self.x+x, self.y+y] == 0:
            self.y += y
            self.x += x
            return True
        else:
            return False
    
    def heal(self, part, hpgiven):
        healed = max(hpgiven, part.damagetaken)
        part.damagetaken -= healed
        return healed

    def dying(self):
        return sum([part.damagetaken for part in self.bodyparts]) > sum([part.maxhp for part in self.bodyparts])/2 or np.any([part.vital() and part.destroyed() for part in self.bodyparts])

    def die(self):
        self.world.creatures.remove(self)
        for item in self.inventory:
            item.owner = self.world.items
            self.world.items.append(item)
            self.inventory.remove(item)
            item.x = self.x
            item.y = self.y
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
                for item in part.wielded:
                    item.owner = self.world.items
                    self.world.items.append(item)
                    part.wielded.remove(item)
                    item.x = self.x
                    item.y = self.y

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
            self.move(self.nextaction[1], self.nextaction[2])
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

class Blind_zombie(Creature):
    def __init__(self, world, x, y):
        super().__init__(world)
        self.faction = 'zombie'
        self.char = 'z'
        self.name = 'blind zombie'
        self.x = x
        self.y = y
        self.sight = 0
        self.hp = 10
        self.torso = bodypart.ZombieTorso(self.bodyparts, 0, 0)
        self.bodyparts[0].connect('left arm', bodypart.ZombieArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right arm', bodypart.ZombieArm(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('left leg', bodypart.ZombieLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('right leg', bodypart.ZombieLeg(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('heart', bodypart.ZombieHeart(self.bodyparts, 0, 0))
        self.bodyparts[0].connect('head', bodypart.ZombieHead(self.bodyparts, 0, 0))
        self.bodyparts[-1].connect('brain', bodypart.ZombieBrain(self.bodyparts, 0, 0))
        
    def ai(self):
        target = None
        for creature in self.world.creatures:
            if creature.faction != 'zombie' and abs(self.x - creature.x) <= 1 and abs(self.y - creature.y) <= 1:
                target = creature
        if target == None or len(self.attackslist()) == 0:
            x = 0
            y = 0
            while (x,y) == (0,0) or self.world.walls[self.x+x, self.y+y] != 0:
                x = np.random.choice([-1,0,1])
                y = np.random.choice([-1,0,1])
            time = np.sqrt(x**2 + y**2) * self.steptime()
            if len([creature for creature in self.world.creatures if creature.x == self.x+x and creature.y == self.y+y]) == 0:
                return(['move', x, y, time])
            else:
                return(['wait', 1])
        else:
            return(['fight', target, np.random.choice([part for part in target.bodyparts if not part.destroyed()]), self.attackslist()[0], self.attackslist()[0][6]])