# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 20:48:19 2022

@author: SurrealPartisan
"""

from collections import namedtuple
import numpy as np

import utils

Attack = namedtuple('Attack', ['name', 'verb2nd', 'verb3rd', 'post2nd', 'post3rd', 'hitprobability', 'time', 'mindamage', 'maxdamage', 'damagetype', 'bane', 'special', 'weapon'])

Material = namedtuple('Material', ['damage', 'hitbonus', 'minespeed', 'armor', 'hp', 'density', 'color'])
materials = {'leather': Material(None, None, None, 5, 100, 4, (186, 100, 13)),
             'wood': Material(10, 0, 0.25, None, 100, 5, (164,116,73)),
             'bone': Material(15, 0, 0.25, 10, 100, 20, (255, 255, 204)),
             'chitin': Material(15, 0, 0.25, 10, 150, 20, (0, 102, 0)),
             'silver': Material(20, 0.02, 0.26, 10, 150, 105, (192, 192, 192)),
             'bronze': Material(20, 0.02, 0.26, 10, 200, 75, (150,116,68)),
             'iron': Material(25, 0.03, 0.27, 15, 300, 79, (200, 200, 200)),
             'steel': Material(30, 0.04, 0.27, 20, 400, 79, (210, 210, 210)),
             'elven steel': Material(30, 0.05, 0.27, 20, 400, 60, (210, 210, 210)),
             'dwarven steel': Material(32, 0.04, 0.30, 22, 440, 80, (210, 210, 210)),
             'titanium': Material(35, 0.06, 0.28, 25, 500, 45, (135, 134, 129)),
             'orichalcum': Material(40, 0.08, 0.29, 30, 500, 75, (255, 102, 102)),
             'nanotube': Material(40, 0.08, 0.29, 30, 500, 10, (51, 0, 0)),
             'neutronium': Material(45, 0.1, 0.29, 35, 600, 1000, (0, 255, 255)),
             'angelbone': Material(45, 0.1, 0.3, 35, 600, 20, (204, 255, 255)),
             'duranium': Material(50, 0.12, 0.31, 40, 700, 30, (200, 200, 200)),
             'tungsten carbide': Material(50, 0.12, 0.33, 40, 650, 156, (180, 180, 180)),
             'tritanium': Material(55, 0.14, 0.32, 45, 800, 50, (135, 134, 129)),
             'yggdrasilwood':Material(55, 0.14, 0.32, 45, 800, 5, (164,116,73)),
             'octiron': Material(60, 0.16, 0.33, 50, 900, 85, (0, 0, 0)),
             'zzzilver': Material(60, 0.16, 0.33, 50, 900, 85, (192, 192, 192)),
             'diamond': Material(65, 0.18, 0.34, 55, 1000, 35, (200, 200, 255)),
             'frankensteinium': Material(65, 0.18, 0.34, 55, 1000, 66, (0, 200, 0)),
             'alicorn': Material(70, 0.2, 0.35, 60, 1100, 30, (150, 150, 255)),
             'titantooth': Material(70, 0.2, 0.35, 62, 1200, 30, (150, 150, 255)),
             'impervium': Material(75, 0.22, 0.36, 65, 1200, 80, (150, 150, 150)),
             'lonsdaleite': Material(75, 0.22, 0.36, 65, 1200, 35, (200, 200, 255)),
             'dragonbone': Material(80, 0.24, 0.37, 70, 1300, 20, (255, 255, 204)),
             'wraithbone': Material(80, 0.24, 0.37, 70, 1300, 10, (255, 204, 255)),
             'devilbone': Material(85, 0.26, 0.38, 75, 1400, 20, (255, 204, 204)),
             'dark matter': Material(85, 0.26, 0.38, 75, 1400, 50, (0, 0, 0)),
             'mithril': Material(90, 0.28, 0.39, 80, 1500, 10, (192, 192, 192)),
             'vampiric gold': Material(90, 0.28, 0.39, 80, 1500, 10, (255, 0, 0)),
             'infernal steel': Material(95, 0.3, 0.4, 85, 1600, 79, (255, 0, 0)),
             'soulmetal': Material(95, 0.3, 0.4, 85, 1600, 30, (255, 255, 255)),
             'kryptonite': Material(100, 0.32, 0.41, 90, 1700, 32, (0, 255, 0)),
             'administratium': Material(100, 0.32, 0.41, 90, 1700, 32, (255, 255, 0)),
             'corbomite': Material(105, 0.34, 0.42, 95, 1800, 50, (0, 150, 0)),
             'unbihexium-354': Material(105, 0.34, 0.42, 95, 1800, 100, (0, 150, 150)),
             'tachyonite': Material(110, 0.36, 0.43, 100, 1900, -10, (0, 0, 255)),
             'mithril carbide': Material(110, 0.36, 0.43, 100, 1900, 15, (200, 200, 200)),
             'vibranium': Material(115, 0.38, 0.44, 105, 2000, 100, (200, 200, 255)),
             'energy': Material(115, 0.38, 0.44, 105, 2000, 0, (0, 255, 255)),
             'forbidium': Material(120, 0.4, 0.45, 110, 2100, 200, (200, 200, 200)),
             'artefact': Material(120, 0.4, 0.45, 110, 2200, 100, (204, 204, 0)),
             'starmetal': Material(125, 0.42, 0.46, 115, 2200, 150, (255, 255, 255)),
             'galvorn': Material(125, 0.42, 0.46, 115, 2200, 15, (0, 0, 0)),
             'phlebotinum': Material(130, 0.44, 0.47, 120, 2300, 40, (255, 255, 0)),
             'hihi\'irokane': Material(130, 0.44, 0.47, 120, 2300, 75, (255, 153, 0)),
             'beskar': Material(135, 0.46, 0.48, 125, 2400, 80, (210, 210, 210)),
             'dark energy': Material(135, 0.47, 0.48, 125, 2300, 0, (204, 0, 153)),
             'unobtainium': Material(140, 0.48, 0.49, 130, 2500, 10, (255, 0, 255)),
             'indestructium': Material(140, 0.48, 0.49, 132, 2600, 60, (51, 102, 255)),
             'adamantine': Material(145, 0.5, 0.5, 135, 2600, 100, (0, 0, 0)),
             'eternium': Material(145, 0.5, 0.5, 135, 2600, 50, (255, 255, 255))}
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
        self.breathepoisonresistance = 0
        self.consumable = False
        self.edible = False
        self.cure = False
        self.wieldable = False
        self.weapon = False
        self.bodypart = False
        self.wearable = False
        self.isarmor = False
        self._info = 'No information available.'

    def hp(self):
        return self.maxhp - self.damagetaken

    def destroyed(self):
        return self.damagetaken >= self.maxhp

    def attackslist(self):
        return []

    def minespeed(self):
        return 0

    def info(self):
        return self._info

class Food(Item):
    def __init__(self, owner, x, y, name, char, color, maxhp, material, weight):
        super().__init__(owner, x, y, name, char, color)
        self.maxhp = maxhp
        self.material = material
        self.baseweight = weight
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
            self.weight = int(self.hp() / self.maxhp * self.baseweight)
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
    i = np.random.randint(8)
    if i == 0:
        return Food(owner, x, y, 'hamburger', '+', (250, 220, 196), 20, 'cooked meat', 250)
    elif i == 1:
        return Food(owner, x, y, 'veggie burger', '+', (250, 220, 196), 20, 'vegetables', 250)
    elif i == 2:
        return Food(owner, x, y, 'banana', '+', (227, 207, 87), 7, 'vegetables', 120)
    elif i == 3:
        return Food(owner, x, y, 'sausage', '+', (97,23,23), 8, 'cooked meat', 100)
    elif i == 4:
        return Food(owner, x, y, 'blood sausage', '+', (0, 0, 0), 12, 'cooked meat', 100)
    elif i == 5:
        return Food(owner, x, y, 'mushroom', '+', (191, 179, 162), 5, 'vegetables', 60)
    elif i == 6:
        return Food(owner, x, y, 'tomato', '+', (151, 46, 37), 3, 'vegetables', 100)
    elif i == 7:
        return Food(owner, x, y, 'fried fish', '+', (223, 130, 9), 10, 'cooked meat', 87)

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
        self.hitpropability = 0.8 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = materials[material].damage + enchantment
        density = materials[material].density
        self.weight = 6*density

    def attackslist(self):
        return[Attack(self.name, 'stabbed', 'stabbed', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'sharp', self.bane, [('bleed', 0.2)], self)]

def randomdagger(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Dagger(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment, bane)

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
        self.hitpropability = 0.8 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = materials[material].damage + enchantment
        density = materials[material].density
        self.weight = 6*density + 2000

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'thrust', 'thrust', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'sharp', self.bane, [('charge',)], self)]
        else:
            return[Attack(self.name, 'thrust', 'thrust', ' with a ' + self.name, ' with a ' + self.name, 0.75*self.hitpropability, 1, self.mindamage, int(self.maxdamage*0.75), 'sharp', self.bane, [('charge',)], self)]

def randomspear(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Spear(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment, bane)

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
        self.hitpropability = 0.8 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = int(materials[material].damage*1.2) + enchantment
        density = materials[material].density
        self.weight = 50*density

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'blunt', self.bane, [('knockback', 0.2)], self)]
        else:
            return[Attack(self.name, 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, 0.75*self.hitpropability, 1, self.mindamage, int(self.maxdamage*0.75), 'blunt', self.bane, [('knockback', 0.1)], self)]

def randommace(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Mace(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment, bane)

class Sword(Item):
    def __init__(self, owner, x, y, material, enchantment, bane):
        if enchantment == 0:
            enchaname = ''
        elif enchantment > 0:
            enchaname = '+' + repr(enchantment) + ' '
        banename = ''
        for b in bane:
            banename += b + '-bane '
        name = enchaname + banename + material + ' sword'
        color = materials[material].color
        super().__init__(owner, x, y, name, '/', color)
        self.wieldable = True
        self.weapon = True
        self.bane = bane
        self.hitpropability = 0.8 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = int(materials[material].damage*1.25) + enchantment
        density = materials[material].density
        self.weight = 50*density

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'slashed', 'slashed', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'sharp', self.bane, [], self)]
        else:
            return[Attack(self.name, 'slashed', 'slashed', ' with a ' + self.name, ' with a ' + self.name, 0.75*self.hitpropability, 1, self.mindamage, int(self.maxdamage*0.75), 'sharp', self.bane, [], self)]

def randomsword(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Sword(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment, bane)

class PickAxe(Item):
    def __init__(self, owner, x, y, material, enchantment, bane):
        if enchantment == 0:
            enchaname = ''
        elif enchantment > 0:
            enchaname = '+' + repr(enchantment) + ' '
        banename = ''
        for b in bane:
            banename += b + '-bane '
        name = enchaname + banename + material + ' pickaxe'
        color = materials[material].color
        super().__init__(owner, x, y, name, '/', color)
        self.wieldable = True
        self.weapon = True
        self.bane = bane
        self.hitpropability = 0.6 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = int(materials[material].damage*1.5) + enchantment
        self._minespeed = materials[material].minespeed
        density = materials[material].density
        self.weight = 12*density + 1500

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1.5, self.mindamage, self.maxdamage, 'hewing', self.bane, [], self)]
        else:
            return[Attack(self.name, 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, 0.67*self.hitpropability, 2, self.mindamage, int(0.67*self.maxdamage), 'hewing', self.bane, [], self)]

    def minespeed(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0]) > 0:  # looking for free hands or other appendages capable of wielding.
            return self._minespeed
        else:
            return 0.75*self._minespeed

def randompickaxe(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return PickAxe(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment, bane)

def randomweapon(owner, x, y, level):
    return np.random.choice([randomdagger, randomspear, randommace, randomsword, randompickaxe])(owner, x, y, level)

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
    return PieceOfArmor(owner, x, y, np.random.choice(['chest armor', 'barding', 'gauntlet', 'leg armor', 'wheel cover', 'helmet', 'tentacle armor']), np.random.choice(armormaterials, p=utils.normalish(len(armormaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment)

class SchoolkidBackpack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'schoolkid backpack', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'backpack'
        self.carryingcapacity = 10000
        self.weight = 500

class TouristBackpack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'tourist backpack', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'backpack'
        self.carryingcapacity = 20000
        self.weight = 1000

class HikerBackpack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hiker backpack', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'backpack'
        self.carryingcapacity = 40000
        self.weight = 2000

class MilitaryBackpack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'military backpack', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'backpack'
        self.carryingcapacity = 80000
        self.weight = 4000

class BackpackOfHolding(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'backpack of holding', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'backpack'
        self.carryingcapacity = 160000
        self.weight = 1000

class GreaterBackpackOfHolding(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'greater backpack of holding', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'backpack'
        self.carryingcapacity = 320000
        self.weight = 1000

def randomBackpack(owner, x, y):
    return np.random.choice([SchoolkidBackpack, TouristBackpack, HikerBackpack, MilitaryBackpack, BackpackOfHolding, GreaterBackpackOfHolding])(owner, x, y)

class RingOfCarrying(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ring of carrying', '=', (255, 255, 0))
        self.wearable = True
        self.wearcategory = 'ring'
        self.carryingcapacity = 20000
        self.weight = 5

class RingOfVision(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ring of vision', '=', (255, 255, 0))
        self.wearable = True
        self.wearcategory = 'ring'
        self.weight = 5

    def sight(self):
        return 1

class RingOfSustenance(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ring of sustenance', '=', (255, 255, 0))
        self.wearable = True
        self.wearcategory = 'ring'
        self.weight = 5
        self.hungermultiplier = 0.5

def randomRing(owner, x, y):
    return np.random.choice([RingOfCarrying, RingOfVision, RingOfSustenance])(owner, x, y)

class Eyeglasses(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'eyeglasses', '(', (0, 255, 255))
        self.wearable = True
        self.wearcategory = 'face'
        self.weight = 9

    def sight(self):
        if len([part for part in self.owner.owner.owner if 'eye' in part.categories and not part.destroyed()]) > 0:
            return 1
        else:
            return 0

class GasMask(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'gas mask', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'face'
        self.weight = 900
        self.breathepoisonresistance = 1

class BerserkerMask(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'berserker mask', '(', (255, 0, 0))
        self.wearable = True
        self.wearcategory = 'face'
        self.weight = 200
        self.stances = ['berserker']

def randomFaceItem(owner, x, y):
    return np.random.choice([Eyeglasses, GasMask, BerserkerMask])(owner, x, y)

def randomUtilityItem(owner, x, y):
    return np.random.choice([randomBackpack, randomRing, randomFaceItem])(owner, x, y)