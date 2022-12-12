# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 21:16:44 2022

@author: SurrealPartisan
"""
from collections import namedtuple
import numpy as np

Attack = namedtuple('Attack', ['name', 'hitprobability', 'time', 'mindamage', 'maxdamage'])

class Creature():
    def __init__(self, world):
        self.world = world
        self.faction = ''
        self.char = '@'
        self.name = 'golem'
        self.x = 0
        self.y = 0
        self.inventory = []
        self.hp = 100
        self.defensecoefficient = 0.8
        self.log = []
        self.sight = 7
        self.seen = np.zeros((world.width, world.height))
        self.speed = 1
        self.nextaction = ['wait', 1]
        
    def steptime(self):
        return 1/self.speed
    
    def move(self, x, y):
        if self.world.walls[self.x+x, self.y+y] == 0:
            self.y += y
            self.x += x
            return True
        else:
            return False
    
    def heal(self, hpgiven):
        self.hp += hpgiven
    
    def die(self):
        self.world.creatures.remove(self)
    
    def attackslist(self):
        return [Attack('fist', 0.8, 1, 1, 10)]
    
    def fight(self, target, attack):
        if abs(self.x - target.x) <= 1 and abs(self.y - target.y) <= 1:
            if np.random.rand() < max(min(attack.hitprobability*target.defensecoefficient, 0.95), 0.05):
                damage = np.random.randint(attack.mindamage, attack.maxdamage+1)
                target.hp -= damage
                if target.hp > 0:
                    self.log.append('You hit the ' + target.name + ' with your ' + attack.name + ', dealing ' + repr(damage) + ' damage!')
                    target.log.append('The ' + self.name + ' hit you, dealing ' + repr(damage) + ' damage!')
                else:
                    self.log.append('You hit the ' + target.name + ' with your ' + attack.name + ', killing it!')
                    target.log.append('The ' + self.name + ' hit you, killing you!')
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
            self.fight(self.nextaction[1], self.nextaction[2])
    
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
        self.speed = 0.5
        self.hp = 10
        
    def ai(self):
        target = None
        for creature in self.world.creatures:
            if creature.faction != 'zombie' and abs(self.x - creature.x) <= 1 and abs(self.y - creature.y) <= 1:
                target = creature
        if target == None:
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
            return(['fight', target, self.attackslist()[0], self.attackslist()[0][2]])