# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 20:48:19 2022

@author: SurrealPartisan
"""

from collections import namedtuple
import numpy as np

import utils

Attack = namedtuple('Attack', ['name', 'verb2nd', 'verb3rd', 'post2nd', 'post3rd', 'hitprobability', 'time', 'mindamage', 'maxdamage', 'bane', 'special'])

Material = namedtuple('Material', ['damage', 'armor', 'hp', 'density', 'color'])
materials = {'leather': Material(None, 5, 100, 4, (186, 100, 13)),
             'wood': Material(10, None, 100, 5, (164,116,73)),
             'bone': Material(15, 10, 100, 20, (255, 255, 204)),
             'chitin': Material(15, 10, 150, 20, (0, 102, 0)),
             'silver': Material(20, 10, 150, 105, (192, 192, 192)),
             'bronze': Material(20, 10, 200, 75, (150,116,68)),
             'iron': Material(25, 15, 300, 79, (200, 200, 200)),
             'steel': Material(30, 20, 400, 79, (210, 210, 210)),
             'elven steel': Material(30, 20, 400, 60, (210, 210, 210)),
             'dwarven steel': Material(32, 22, 440, 80, (210, 210, 210)),
             'titanium': Material(35, 25, 500, 45, (135, 134, 129)),
             'orichalcum': Material(40, 30, 500, 75, (255, 102, 102)),
             'nanotube': Material(40, 30, 500, 10, (51, 0, 0)),
             'neutronium': Material(45, 35, 600, 1000, (0, 255, 255)),
             'angelbone': Material(45, 35, 600, 20, (204, 255, 255)),
             'duranium': Material(50, 40, 700, 30, (200, 200, 200)),
             'tritanium': Material(55, 45, 800, 50, (135, 134, 129)),
             'octiron': Material(60, 50, 900, 85, (0, 0, 0)),
             'diamond': Material(65, 55, 1000, 35, (200, 200, 255)),
             'alicorn': Material(70, 60, 1100, 30, (150, 150, 255)),
             'impervium': Material(75, 65, 1200, 80, (150, 150, 150)),
             'dragonbone': Material(80, 70, 1300, 20, (255, 255, 204)),
             'devilbone': Material(85, 75, 1400, 20, (255, 204, 204)),
             'mithril': Material(90, 80, 1500, 10, (192, 192, 192)),
             'infernal steel': Material(95, 85, 1600, 79, (255, 0, 0)),
             'kryptonite': Material(100, 90, 1700, 32, (0, 255, 0)),
             'corbomite': Material(105, 95, 1800, 50, (0, 150, 0)),
             'tachyonite': Material(110, 100, 1900, -10, (0, 0, 255)),
             'vibranium': Material(115, 105, 2000, 100, (200, 200, 255)),
             'forbidium': Material(120, 110, 2100, 200, (200, 200, 200)),
             'starmetal': Material(125, 115, 2200, 150, (255, 255, 255)),
             'phlebotinum': Material(130, 120, 2300, 40, (255, 255, 0)),
             'beskar': Material(135, 125, 2400, 80, (210, 210, 210)),
             'unobtainium': Material(140, 130, 2500, 10, (255, 0, 255)),
             'adamantine': Material(145, 135, 2600, 100, (0, 0, 0))}
armormaterials = [material for material in materials if not materials[material].armor == None]
weaponmaterials = [material for material in materials if not materials[material].damage == None]
likeliestmaterialbylevel = ['bone',
                            'bronze',
                            'elven steel',
                            'orichalcum',
                            'angelbone',
                            'duranium',
                            'tritanium',
                            'octiron',
                            'diamond',
                            'alicorn',
                            'impervium',
                            'dragonbone',
                            'devilbone',
                            'mithril',
                            'infernal steel',
                            'kryptonite',
                            'corbomite',
                            'tachyonite',
                            'vibranium',
                            'forbidium',
                            'starmetal',
                            'phlebotinum',
                            'beskar',
                            'unobtainium',
                            'adamantine']

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
        self.weight = 0
        self.carryingcapacity = 0
        self.consumable = False
        self.edible = False
        self.cure = False
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

class Food(Item):
    def __init__(self, owner, x, y, name, char, color, maxhp, material, weight):
        super().__init__(owner, x, y, name, char, color)
        self.maxhp = maxhp
        self.material = material
        self.weight = weight
        self.basename = name
        self.consumable = True
        self.edible = True

    def consume(self, user, efficiency):
        if int(self.hp()*efficiency) > user.hunger:
            self.damagetaken += int(user.hunger/efficiency)
            user.hunger = 0
            user.log().append('You ate some of the ' + self.name + '.')
            user.log().append('You are satiated.')
            if self.damagetaken < 0.4*self.maxhp:
                self.name = 'partially eaten ' + self.basename
            elif self.damagetaken < 0.6*self.maxhp:
                self.name = 'half-eaten ' + self.basename
            else:
                self.name = 'mostly eaten ' + self.basename
        else:
            user.hunger -= int(self.hp()*efficiency)
            self.damagetaken = self.maxhp
            self.owner.remove(self)
            user.log().append('You ate the ' + self.name + '.')
            if user.hunger == 0:
                user.log().append('You are satiated.')

def randomfood(owner, x, y):
    i = np.random.randint(2)
    if i == 0:
        return Food(owner, x, y, 'hamburger', '*', (250, 220, 196), 20, 'cooked meat', 250)
    elif i == 1:
        return Food(owner, x, y, 'veggie burger', '*', (250, 220, 196), 20, 'vegetables', 250)

CureType = namedtuple('CureType', ['curedmaterial', 'name', 'hpgiven_base', 'dosage'])

class Cure(Item):
    def __init__(self, owner, x, y, curetype, level):
        if curetype.curedmaterial == 'living flesh':
            color = (255, 0, 0)
            name = 'dose of medication labeled "' + curetype.name + ', ' + repr(curetype.dosage*level) + ' mg"'
        elif curetype.curedmaterial == 'undead flesh':
            color = (0, 255, 0)
            name = 'vial of ectoplasmic infusion labeled "' + curetype.name + ', ' + repr(curetype.dosage*level) + ' mmol/l"'
        super().__init__(owner, x, y, name, '!', color)
        self.consumable = True
        self.cure = True
        self.curetype = curetype
        self.curedmaterial = curetype.curedmaterial
        self._hpgiven = curetype.hpgiven_base * level
        self.weight = 100
    
    def hpgiven(self):
        return self._hpgiven
    
    def consume(self, user):
        partlist = [part for part in user.bodyparts if part.material == self.curedmaterial and not part.destroyed()]
        if len(partlist) > 0:
            part = max(partlist, key=lambda part : part.damagetaken)
            user.heal(part, self.hpgiven())
        else:
            user.log().append('You were unaffected.')
        self.owner.remove(self)

class Dagger(Item):
    def __init__(self, owner, x, y, material, enchantment, bane):
        if enchantment == 0:
            enchaname = ''
        elif enchantment > 0:
            enchaname = '+' + repr(enchantment) + ' '
        banename = ''
        for b in bane:
            banename += b + '-bane '
        name = enchaname + banename + material + ' dagger'
        color = materials[material].color
        super().__init__(owner, x, y, name, '/', color)
        self.wieldable = True
        self.weapon = True
        self.bane = bane
        self.mindamage = 1 + enchantment
        self.maxdamage = materials[material].damage + enchantment
        density = materials[material].density
        self.weight = 6*density

    def attackslist(self):
        return[Attack(self.name, 'stabbed', 'stabbed', '', '', 0.8, 1, self.mindamage, self.maxdamage, self.bane, [('bleed', 0.2)])]

def randomdagger(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Dagger(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.01)), enchantment, bane)

class Spear(Item):
    def __init__(self, owner, x, y, material, enchantment, bane):
        if enchantment == 0:
            enchaname = ''
        elif enchantment > 0:
            enchaname = '+' + repr(enchantment) + ' '
        banename = ''
        for b in bane:
            banename += b + '-bane '
        name = enchaname + banename + material + ' spear'
        color = materials[material].color
        super().__init__(owner, x, y, name, '/', color)
        self.wieldable = True
        self.weapon = True
        self.bane = bane
        self.mindamage = 1 + enchantment
        self.maxdamage = materials[material].damage + enchantment
        density = materials[material].density
        self.weight = 6*density + 2000

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'thrust', 'thrust', ' with a ' + self.name, ' with a ' + self.name, 0.8, 1, self.mindamage, self.maxdamage, self.bane, [('charge',)])]
        else:
            return[Attack(self.name, 'thrust', 'thrust', ' with a ' + self.name, ' with a ' + self.name, 0.6, 1, self.mindamage, int(self.maxdamage*0.75), self.bane, [('charge',)])]

def randomspear(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Spear(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.01)), enchantment, bane)

class Mace(Item):
    def __init__(self, owner, x, y, material, enchantment, bane):
        if enchantment == 0:
            enchaname = ''
        elif enchantment > 0:
            enchaname = '+' + repr(enchantment) + ' '
        banename = ''
        for b in bane:
            banename += b + '-bane '
        name = enchaname + banename + material + ' mace'
        color = materials[material].color
        super().__init__(owner, x, y, name, '/', color)
        self.wieldable = True
        self.weapon = True
        self.bane = bane
        self.mindamage = 1 + enchantment
        self.maxdamage = int(materials[material].damage*1.2) + enchantment
        density = materials[material].density
        self.weight = 50*density

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, 0.8, 1, self.mindamage, self.maxdamage, self.bane, [('knockback', 0.2)])]
        else:
            return[Attack(self.name, 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, 0.6, 1, self.mindamage, int(self.maxdamage*0.75), self.bane, [('knockback', 0.1)])]

def randommace(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Mace(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.01)), enchantment, bane)

def randomweapon(owner, x, y, level):
    return np.random.choice([randomdagger, randomspear, randommace])(owner, x, y, level)

class LightPick(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'light pick', '\\', (186, 100, 13))
        self.wieldable = True
        self.weapon = True
        self.weight = 1500

    def attackslist(self):
        return[Attack('light pick', 'hit', 'hit', ' with a light pick', ' with a light pick', 0.6, 1.5, 1, 20, [], [])]

    def minespeed(self):
        return 0.25

class HeavyPick(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'heavy pick', '\\', (186, 100, 13))
        self.wieldable = True
        self.weapon = True
        self.weight = 3000

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack('heavy pick', 'hit', 'hit', ' with a heavy pick', ' with a heavy pick', 0.6, 1.5, 1, 30, [], [])]
        else:
            return[Attack('heavy pick', 'hit', 'hit', ' with a heavy pick', ' with a heavy pick', 0.4, 2, 1, 20, [], [])]

    def minespeed(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return 0.33
        else:
            return 0.2

def randomtool(owner, x, y):
    return np.random.choice([HeavyPick, LightPick])(owner, x, y)

class PieceOfArmor(Item):
    def __init__(self, owner, x, y, wearcategory, material, enchantment):
        if enchantment == 0:
            enchaname = ''
        elif enchantment > 0:
            enchaname = '+' + repr(enchantment) + ' '
        name = enchaname + material + ' ' + wearcategory
        color = materials[material].color
        super().__init__(owner, x, y, name, '[', color)
        self.wearcategory = wearcategory
        self.wearable = True
        self.isarmor = True
        self.mindamage = 0 + enchantment
        self.maxdamage = materials[material].armor + enchantment
        density = materials[material].density

        if wearcategory == 'chest armor':
            self.weight = 200*density
        if wearcategory == 'barding':
            self.weight = 200*density
        if wearcategory == 'gauntlet':
            self.weight = 10*density
        if wearcategory == 'leg armor':
            self.weight = 50*density
        if wearcategory == 'wheel cover':
            self.weight = 50*density
        if wearcategory == 'helmet':
            self.weight = 20*density
        if wearcategory == 'tentacle armor':
            self.weight = 20*density

def randomarmor(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    return PieceOfArmor(owner, x, y, np.random.choice(['chest armor', 'barding', 'gauntlet', 'leg armor', 'wheel cover', 'helmet', 'tentacle armor']), np.random.choice(armormaterials, p=utils.normalish(len(armormaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.01)), enchantment)

class Backpack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'backpack', '¤', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'backpack'
        self.carryingcapacity = 20000
        self.weight = 500