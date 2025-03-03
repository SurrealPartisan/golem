# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 20:48:19 2022

@author: SurrealPartisan
"""

from collections import namedtuple
import numpy as np
from golem import utils

Attack = namedtuple('Attack', ['name', 'verb2nd', 'verb3rd', 'verbinfinitive', 'post2nd', 'post3rd', 'hitprobability', 'time', 'mindamage', 'maxdamage', 'damagetype', 'weaponlength', 'bane', 'special', 'weapon'])

Material = namedtuple('Material', ['damage', 'hitbonus', 'minespeed', 'armor', 'hp', 'density', 'color'])
materials = {'leather': Material(None, None, None, 3, 25, 4, (186, 100, 13)),
             'wood': Material(5, 0, 0.25, None, 25, 5, (164,116,73)),
             'bone': Material(8, 0, 0.25, 5, 25, 20, (255, 255, 204)),
             'chitin': Material(8, 0, 0.25, 5, 35, 20, (0, 102, 0)),
             'silver': Material(10, 0.02, 0.26, 5, 35, 105, (192, 192, 192)),
             'bronze': Material(10, 0.02, 0.26, 5, 50, 75, (150,116,68)),
             'iron': Material(13, 0.03, 0.27, 8, 75, 79, (200, 200, 200)),
             'steel': Material(15, 0.04, 0.27, 10, 100, 79, (210, 210, 210)),
             'elven steel': Material(15, 0.05, 0.27, 10, 100, 60, (210, 210, 210)),
             'dwarven steel': Material(16, 0.04, 0.30, 11, 110, 80, (210, 210, 210)),
             'titanium': Material(18, 0.06, 0.28, 13, 125, 45, (135, 134, 129)),
             'orichalcum': Material(20, 0.08, 0.29, 15, 125, 75, (255, 102, 102)),
             'nanotube': Material(20, 0.08, 0.29, 15, 125, 10, (51, 0, 0)),
             'neutronium': Material(23, 0.1, 0.29, 18, 150, 1000, (0, 255, 255)),
             'angelbone': Material(23, 0.1, 0.3, 18, 150, 20, (204, 255, 255)),
             'duranium': Material(25, 0.12, 0.31, 20, 175, 30, (200, 200, 200)),
             'tungsten carbide': Material(25, 0.12, 0.33, 20, 175, 156, (180, 180, 180)),
             'tritanium': Material(28, 0.14, 0.32, 23, 200, 50, (135, 134, 129)),
             'yggdrasilwood':Material(28, 0.14, 0.32, 23, 200, 5, (164,116,73)),
             'octiron': Material(30, 0.16, 0.33, 25, 225, 85, (0, 0, 0)),
             'zzzilver': Material(30, 0.16, 0.33, 25, 225, 85, (192, 192, 192)),
             'diamond': Material(33, 0.18, 0.34, 28, 250, 35, (200, 200, 255)),
             'frankensteinium': Material(33, 0.18, 0.34, 28, 250, 66, (0, 200, 0)),
             'alicorn': Material(35, 0.2, 0.35, 30, 275, 30, (150, 150, 255)),
             'titantooth': Material(35, 0.2, 0.35, 31, 300, 30, (150, 150, 255)),
             'impervium': Material(38, 0.22, 0.36, 33, 300, 80, (150, 150, 150)),
             'lonsdaleite': Material(38, 0.22, 0.36, 33, 300, 35, (200, 200, 255)),
             'dragonbone': Material(40, 0.24, 0.37, 35, 325, 20, (255, 255, 204)),
             'wraithbone': Material(40, 0.24, 0.37, 35, 325, 10, (255, 204, 255)),
             'devilbone': Material(43, 0.26, 0.38, 38, 350, 20, (255, 204, 204)),
             'dark matter': Material(43, 0.26, 0.38, 38, 350, 50, (0, 0, 0)),
             'mithril': Material(45, 0.28, 0.39, 40, 375, 10, (192, 192, 192)),
             'vampiric gold': Material(45, 0.28, 0.39, 40, 375, 10, (255, 0, 0)),
             'infernal steel': Material(48, 0.3, 0.4, 43, 400, 79, (255, 0, 0)),
             'soulmetal': Material(48, 0.3, 0.4, 43, 400, 30, (255, 255, 255)),
             'kryptonite': Material(50, 0.32, 0.41, 45, 425, 32, (0, 255, 0)),
             'administratium': Material(50, 0.32, 0.41, 45, 425, 32, (255, 255, 0)),
             'corbomite': Material(53, 0.34, 0.42, 48, 450, 50, (0, 150, 0)),
             'unbihexium-354': Material(53, 0.34, 0.42, 48, 450, 100, (0, 150, 150)),
             'tachyonite': Material(55, 0.36, 0.43, 50, 475, -10, (0, 0, 255)),
             'mithril carbide': Material(55, 0.36, 0.43, 50, 475, 15, (200, 200, 200)),
             'vibranium': Material(58, 0.38, 0.44, 53, 500, 100, (200, 200, 255)),
             'energy': Material(58, 0.38, 0.44, 53, 500, 0, (0, 255, 255)),
             'forbidium': Material(60, 0.4, 0.45, 55, 525, 200, (200, 200, 200)),
             'artefact': Material(60, 0.4, 0.45, 55, 550, 100, (204, 204, 0)),
             'starmetal': Material(63, 0.42, 0.46, 58, 550, 150, (255, 255, 255)),
             'galvorn': Material(63, 0.42, 0.46, 58, 575, 15, (0, 0, 0)),
             'phlebotinum': Material(65, 0.44, 0.47, 60, 575, 40, (255, 255, 0)),
             'hihi\'irokane': Material(65, 0.44, 0.47, 60, 600, 75, (255, 153, 0)),
             'beskar': Material(68, 0.46, 0.48, 63, 600, 80, (210, 210, 210)),
             'dark energy': Material(68, 0.47, 0.48, 63, 625, 0, (204, 0, 153)),
             'unobtainium': Material(70, 0.48, 0.49, 65, 625, 10, (255, 0, 255)),
             'indestructium': Material(70, 0.48, 0.49, 66, 650, 60, (51, 102, 255)),
             'adamantine': Material(73, 0.5, 0.5, 68, 650, 100, (0, 0, 0)),
             'eternium': Material(73, 0.5, 0.5, 68, 675, 50, (255, 255, 255))}
armormaterials = [material for material in materials if not materials[material].armor == None]
weaponmaterials = [material for material in materials if not materials[material].damage == None]
likeliestmaterialbylevel = ['bone',           # 1
                            'bronze',         # 2
                            'elven steel',    # 3
                            'orichalcum',     # 4
                            'angelbone',      # 5
                            'duranium',       # 6
                            'tritanium',      # 7
                            'octiron',        # 8
                            'diamond',        # 9
                            'alicorn',        # 10
                            'impervium',      # 11
                            'dragonbone',     # 12
                            'devilbone',      # 13
                            'mithril',        # 14
                            'infernal steel', # 15
                            'kryptonite',     # 16
                            'corbomite',      # 17
                            'tachyonite',     # 18
                            'vibranium',      # 19
                            'forbidium',      # 20
                            'starmetal',      # 21
                            'phlebotinum',    # 22
                            'beskar',         # 23
                            'unobtainium',    # 24
                            'adamantine']     # 25

class Item():
    def __init__(self, owner, x, y, name, char, color):
        self.owner = owner  # A list, such as inventory or list of map items
        if self.owner != None:
            self.owner.append(self)
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.color = color
        self.maxhp = np.inf
        self.damagetaken = 0
        self.material = None
        self.weight = 0
        self.carryingcapacity = 0
        self.breathepoisonresistance = 0
        self.consumable = False
        self.edible = False
        self.cure = False
        self.wieldable = False
        self.weapon = False
        self.throwable = False
        self.throwrange = 0
        self.bodypart = False
        self.wearable = False
        self.isarmor = False
        self.readable = False # If True, must have the read(creature) method
        self.writable = False # If True, must have the write(creature, content) method
        self.hidden = False
        self.trap = False  # If True, must have the entrap(creature, bodypart) method
        self._info = 'No information available.'

    def hp(self):
        return self.maxhp - self.damagetaken

    def destroyed(self):
        return self.damagetaken >= self.maxhp

    def pickableinstance(self):
        return self

    def attackslist(self):
        return []

    def thrownattackslist(self):
        return []

    def minespeed(self):
        return 0

    def info(self):
        return self._info

    def on_wearwield(self, creat):
        pass

    def on_unwearunwield(self, creat):
        pass

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
        self._info = 'Food consisting of ' + material + '.'

    def consume(self, user, efficiency):
        if user.stance == 'fasting':
            user.stance = 'neutral'
            user.log().append('You stopped fasting.')
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
            name = 'dose of medication labeled "' + curetype.name + ', ' + repr(int(curetype.dosage*level)) + ' mg"'
            info = 'A cure for living flesh.'
        elif curetype.curedmaterial == 'undead flesh':
            color = (0, 255, 0)
            name = 'vial of ectoplasmic infusion labeled "' + curetype.name + ', ' + repr(int(curetype.dosage*level)) + ' mmol/l"'
            info = 'A cure for undead flesh.'
        super().__init__(owner, x, y, name, '!', color)
        self.consumable = True
        self.material = 'chemical'
        self.cure = True
        self.curetype = curetype
        self.curedmaterial = curetype.curedmaterial
        self._hpgiven = curetype.hpgiven_base * level
        self.weight = 100
        self._info = info
    
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

class ManaPotion(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'mana potion', '!', (0, 0, 255))
        self.consumable = True
        self.material = 'chemical'
        self.weight = 100
        self._info = 'A potion to restore your mana to full.'

    def consume(self, user):
        user.manaused = 0
        user.log().append('Your mana was restored.')
        self.owner.remove(self)

class Spellbooklet(Item):
    def __init__(self, owner, x, y, spell):
        if spell == None:
            name = 'empty spellbooklet'
        else:
            name = 'spellbooklet of ' + spell.name
        super().__init__(owner, x, y, name, '?', (252, 245, 229))
        self.spell = spell
        if spell == None:
            self.writable = True
        else:
            self.readable = True
        self.material = 'parchment'
        self.weight = 100
        self._info = 'A vessel for magical knowledge.'

    def read(self, creature):
        if self.spell == None:
            creature.log().append('The booklet is empty. You learned nothing.')
        elif creature.intelligence() < self.spell.intelligencerequirement:
            creature.log().append('You are not intelligent enough to comprehend the spell in this booklet. You learned nothing.')
        elif self.spell.name in [spell.name for spell in creature.spellsknown()]:
            creature.log().append('You already know the spell in this booklet. You learned nothing.')
        else:
            creature.spellsknown().append(self.spell)
            creature.log().append('You learned to cast ' + self.spell.name + '!')
            creature.log().append('After you read it, the booklet disappeared into a puff of smoke!')
            self.owner.remove(self)

    def write(self, creature, content):
        if not self.writable:
            creature.log().append('The booklet already contains a spell.')
        else:
            creature.log().append('You wrote down the ' + content.name + ' spell to a booklet.')
            self.spell = content
            self.name = 'spellbooklet of ' + content.name
            self.writable = False
            self.readable = True

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
        self.material = material
        self.wieldable = True
        self.weapon = True
        self.throwable = True
        self.throwrange = 5 + enchantment
        self.bane = bane
        self.hitpropability = 0.8 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = materials[material].damage + enchantment
        density = materials[material].density
        self.weight = 6*density
        self._info = 'A one-handed weapon made of ' + material + '. Can make enemies bleed (double damage over time). Can be thrown up to five (plus enchantment) paces.'

    def attackslist(self):
        return[Attack(self.name, 'stabbed', 'stabbed', 'stab', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'sharp', 20, self.bane, [('bleed', 0.2)], self)]

    def thrownattackslist(self):
        return[Attack(self.name, 'threw a ' + self.name, 'threw a ' + self.name, 'throw a ' + self.name, '', '', self.hitpropability, 1, self.mindamage, self.maxdamage, 'sharp', 20, self.bane, [('bleed', 0.2)], self)]

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
        self.material = material
        self.wieldable = True
        self.weapon = True
        self.throwable = True
        self.throwrange = 10 + enchantment
        self.bane = bane
        self.hitpropability = 0.8 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = materials[material].damage + enchantment
        density = materials[material].density
        self.weight = 6*density + 1000
        self._info = 'A weapon made of ' + material + '. Better used with two hands (leave another hand free when wielding). A charge weapon deals half again as much damage when you have moved towards the enemy just before the attack. Can be thrown up to ten (plus enchantment) paces.'

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0 and not (part.destroyed() or part.incapacitated())]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'thrust', 'thrust', 'thrust', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'sharp', 100, self.bane, [('charge',)], self)]
        else:
            return[Attack(self.name, 'thrust', 'thrust', 'thrust', ' with a ' + self.name, ' with a ' + self.name, 0.75*self.hitpropability, 1, self.mindamage, int(self.maxdamage*0.75), 'sharp', 100, self.bane, [('charge',)], self)]

    def thrownattackslist(self):
        return[Attack(self.name, 'threw a ' + self.name, 'threw a ' + self.name, 'throw a ' + self.name, '', '', self.hitpropability, 1, self.mindamage, self.maxdamage, 'sharp', 100, self.bane, [('charge',)], self)]

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
        self.material = material
        self.wieldable = True
        self.weapon = True
        self.bane = bane
        self.hitpropability = 0.8 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = int(materials[material].damage*1.2) + enchantment
        density = materials[material].density
        self.weight = 50*density
        self._info = 'A weapon made of ' + material + '. Can knock enemies back.'

    def attackslist(self):
        return[Attack(self.name, 'hit', 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'blunt', 50, self.bane, [('knockback', 0.2)], self)]

def randommace(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Mace(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment, bane)

class Staff(Item):
    def __init__(self, owner, x, y, material, enchantment, bane):
        if enchantment == 0:
            enchaname = ''
        elif enchantment > 0:
            enchaname = '+' + repr(enchantment) + ' '
        banename = ''
        for b in bane:
            banename += b + '-bane '
        name = enchaname + banename + material + ' staff'
        color = materials[material].color
        super().__init__(owner, x, y, name, '/', color)
        self.material = material
        self.wieldable = True
        self.weapon = True
        self.supporting = True
        self.bane = bane
        self.hitpropability = 0.8 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = int(materials[material].damage*1.2) + enchantment
        density = materials[material].density
        self.weight = 100*density
        self._info = 'A weapon made of ' + material + '. Better used with two hands (leave another hand free when wielding). When wielded, prevents getting imbalanced.'

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0 and not (part.destroyed() or part.incapacitated())]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'hit', 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'blunt', 100, self.bane, [], self)]
        else:
            return[Attack(self.name, 'hit', 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, 0.75*self.hitpropability, 1, self.mindamage, int(self.maxdamage*0.75), 'blunt', 100, self.bane, [], self)]

def randomstaff(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Staff(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment, bane)

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
        self.material = material
        self.wieldable = True
        self.weapon = True
        self.bane = bane
        self.hitpropability = 0.8 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = int(materials[material].damage*1.2) + enchantment
        density = materials[material].density
        self.weight = 50*density
        self._info = 'A weapon made of ' + material + '. Better used with two hands (leave another hand free when wielding). Because of its long sharp blade, can directly attack internal organs.'

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0 and not (part.destroyed() or part.incapacitated())]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'slashed', 'slashed', 'slash', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'sharp', 50, self.bane, [('internals-seeking',)], self)]
        else:
            return[Attack(self.name, 'slashed', 'slashed', 'slash', ' with a ' + self.name, ' with a ' + self.name, 0.75*self.hitpropability, 1, self.mindamage, int(self.maxdamage*0.75), 'sharp', 50, self.bane, [('internals-seeking',)], self)]

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
        self.material = material
        self.wieldable = True
        self.weapon = True
        self.bane = bane
        self.hitpropability = 0.7 + materials[material].hitbonus + 0.01*enchantment
        self.mindamage = 1 + enchantment
        self.maxdamage = int(materials[material].damage*1.75) + enchantment
        self._minespeed = materials[material].minespeed
        density = materials[material].density
        self.weight = 12*density + 500
        self._info = 'A weapon and a tool, made of ' + material + '. Better used with two hands (leave another hand free when wielding). Can be used for mining.'

    def attackslist(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0 and not (part.destroyed() or part.incapacitated())]) > 0:  # looking for free hands or other appendages capable of wielding.
            return[Attack(self.name, 'hit', 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1.25, self.mindamage, self.maxdamage, 'rough', 50, self.bane, [], self)]
        else:
            return[Attack(self.name, 'hit', 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, 0.67*self.hitpropability, 1.5, self.mindamage, int(0.67*self.maxdamage), 'rough', 50, self.bane, [], self)]

    def minespeed(self):
        if len([part for part in self.owner.owner.owner if part.capableofwielding and len(part.wielded) == 0 and not (part.destroyed() or part.incapacitated())]) > 0:  # looking for free hands or other appendages capable of wielding.
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

def randomweapon(owner, x, y, level): # If new weapon types are added here, also add them to magic.CreateWeapon!
    return np.random.choice([randomdagger, randomspear, randommace, randomstaff, randomsword, randompickaxe])(owner, x, y, level)

class Stone(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'stone', '.', (255, 255, 255))
        self.wieldable = True
        self.weapon = True
        self.throwable = True
        self.throwrange = 5
        self.hitpropability = 0.75
        self.mindamage = 1
        self.maxdamage = 8
        self.weight = 1000
        self._info = 'A blunt improvised weapon. Can be thrown up to five paces.'

    def attackslist(self):
        return[Attack(self.name, 'hit', 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'blunt', 0, [], [], self)]

    def thrownattackslist(self):
        return[Attack(self.name, 'threw a ' + self.name, 'threw a ' + self.name, 'throw a ' + self.name, '', '', self.hitpropability, 1, self.mindamage, self.maxdamage, 'blunt', 0, [], [], self)]

class Torch(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'torch', '/', (255, 204, 0))
        self.wieldable = True
        self.weapon = True
        self.hitpropability = 0.75
        self.mindamage = 1
        self.maxdamage = 8
        self.weight = 700
        self._info = 'A light source and an improvised weapon. When wielded, increases your range of vision, as long as you have eyes. Deals fire damage.'

    def attackslist(self):
        return[Attack(self.name, 'hit', 'hit', 'hit', ' with a ' + self.name, ' with a ' + self.name, self.hitpropability, 1, self.mindamage, self.maxdamage, 'fire', 50, [], [], self)]

    def sight(self):
        if len([part for part in self.owner.owner.owner if 'eye' in part.categories and not (part.destroyed() or part.incapacitated())]) > 0:
            return 1
        else:
            return 0

    def on_wearwield(self, creat):
        creat.fovuptodate = False

    def on_unwearunwield(self, creat):
        creat.fovuptodate = False

class GlassShards(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'glass shards', ',', (0, 255, 255))
        self.material = 'glass'
        self.trap = True
        self.mindamage = 1
        self.maxdamage = 5
        self.weight = 50
        self._info = 'A trap made of glass.'

    def entrap(self, creat, part):
        resistancemultiplier = 1 - part.resistance('sharp')
        totaldamage = np.random.randint(self.mindamage, self.maxdamage+1)
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
        alreadyimbalanced = creat.imbalanced()
        if 'leg' in part.categories:
            numlegs = len([p for p in creat.bodyparts if 'leg' in p.categories and not p.destroyed() and not p.incapacitated()])
            if np.random.rand() < 0.5 - 0.05*numlegs:
                part.imbalanceclock += 20*damage/part.maxhp
        if creat.imbalanced() and not alreadyimbalanced:
            imbalancedtext = ', imbalancing you'
        else:
            imbalancedtext = ''
        if part.parentalconnection != None:
            partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
        elif part == creat.torso:
            partname = 'torso'
        if not creat.dying():
            if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                creat.log().append('You stepped on ' + self.name + '. They incapacitated your ' + partname + imbalancedtext + '.')
                if armordamage > 0:
                    if not armor.destroyed():
                        creat.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                    else:
                        creat.log().append('Your ' + armor.name + ' was destroyed!')
                        armor.owner.remove(armor)
            elif not part.destroyed():
                creat.log().append('You stepped on ' + self.name + '. They dealt ' + repr(damage) + ' damage to your ' + partname + imbalancedtext + '.')
                if armordamage > 0:
                    if not armor.destroyed():
                        creat.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                    else:
                        creat.log().append('Your ' + armor.name + ' was destroyed!')
                        armor.owner.remove(armor)
            else:
                creat.log().append('You stepped on ' + self.name + '. They destroyed your ' + partname + imbalancedtext + '.')
                if armordamage > 0:
                    if not armor.destroyed():
                        creat.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                    else:
                        creat.log().append('Your ' + armor.name + ' was also destroyed!')
                        armor.owner.remove(armor)
                part.on_destruction(False)
            volume, details = creat.hurtphrase([part])
            if len(details) > 0 and volume > 0 and len([p for p in creat.bodyparts if hasattr(p, 'sound') and p.sound > 0 and not p.destroyed() and not p.incapacitated()]):
                if len(details) == 5:
                    creat.log().append('You ' + details[2] + ': "' + details[4] + '".')
                elif len(details) == 4:
                    creat.log().append('You ' + details[2] + '.')
                utils.infoblast(creat.world, creat.x, creat.y, volume, [creat], details)
        else:
            creat.log().append('You stepped on ' + self.name + '. They killed you.')
            creat.log().append('You are dead!')
            if part.destroyed():
                part.on_destruction(True)
            creat.die()
            creat.causeofdeath = ('step', self)

class Caltrops(Item):
    def __init__(self, owner, x, y, material, enchantment, bane):
        if enchantment == 0:
            enchaname = ''
        elif enchantment > 0:
            enchaname = '+' + repr(enchantment) + ' '
        banename = ''
        for b in bane:
            banename += b + '-bane '
        name = enchaname + banename + material + ' caltrops'
        color = materials[material].color
        super().__init__(owner, x, y, name, ',', color)
        self.material = material
        self.hidden = True
        self.trap = True
        self.bane = bane
        self.mindamage = 1 + enchantment
        self.maxdamage = int(materials[material].damage) + enchantment
        density = materials[material].density
        self.weight = 12*density
        self._info = 'A trap made of ' + material + '.'

    def entrap(self, creat, part):
        if np.any([faction in self.bane for faction in creat.factions]):
            banemultiplier = 2
        else:
            banemultiplier = 1
        resistancemultiplier = 1 - part.resistance('sharp')
        totaldamage = np.random.randint(self.mindamage, self.maxdamage+1)
        if part.armor() != None:
            armor = part.armor()
            armordamage = min(armor.hp(), min(totaldamage, np.random.randint(armor.mindamage, armor.maxdamage+1)))
            armor.damagetaken += armordamage
        else:
            armor = None
            armordamage = 0
        damage = min(int(banemultiplier*resistancemultiplier*(totaldamage - armordamage)), part.hp())
        alreadyincapacitated = part.incapacitated()
        part.damagetaken += damage
        alreadyimbalanced = creat.imbalanced()
        if 'leg' in part.categories:
            numlegs = len([p for p in creat.bodyparts if 'leg' in p.categories and not p.destroyed() and not p.incapacitated()])
            if np.random.rand() < 0.5 - 0.05*numlegs:
                part.imbalanceclock += 20*damage/part.maxhp
        if creat.imbalanced() and not alreadyimbalanced:
            imbalancedtext = ', imbalancing you'
        else:
            imbalancedtext = ''
        if part.parentalconnection != None:
            partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
        elif part == creat.torso:
            partname = 'torso'
        if not creat.dying():
            if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                creat.log().append('You stepped on ' + self.name + '. They incapacitated your ' + partname + imbalancedtext + '.')
                if armordamage > 0:
                    if not armor.destroyed():
                        creat.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                    else:
                        creat.log().append('Your ' + armor.name + ' was destroyed!')
                        armor.owner.remove(armor)
            elif not part.destroyed():
                creat.log().append('You stepped on ' + self.name + '. They dealt ' + repr(damage) + ' damage to your ' + partname + imbalancedtext + '.')
                if armordamage > 0:
                    if not armor.destroyed():
                        creat.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                    else:
                        creat.log().append('Your ' + armor.name + ' was destroyed!')
                        armor.owner.remove(armor)
            else:
                creat.log().append('You stepped on ' + self.name + '. They destroyed your ' + partname + imbalancedtext + '.')
                if armordamage > 0:
                    if not armor.destroyed():
                        creat.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                    else:
                        creat.log().append('Your ' + armor.name + ' was also destroyed!')
                        armor.owner.remove(armor)
                part.on_destruction(False)
            volume, details = creat.hurtphrase([part])
            if len(details) > 0 and volume > 0 and len([p for p in creat.bodyparts if hasattr(p, 'sound') and p.sound > 0 and not p.destroyed() and not p.incapacitated()]):
                if len(details) == 5:
                    creat.log().append('You ' + details[2] + ': "' + details[4] + '".')
                elif len(details) == 4:
                    creat.log().append('You ' + details[2] + '.')
                utils.infoblast(creat.world, creat.x, creat.y, volume, [creat], details)
        else:
            creat.log().append('You stepped on ' + self.name + '. They killed you.')
            creat.log().append('You are dead!')
            if part.destroyed():
                part.on_destruction(True)
            creat.die()
            creat.causeofdeath = ('step', self)

def randomcaltrops(owner, x, y, level):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    bane = []
    if np.random.rand() < 0.2:
        bane = [np.random.choice(utils.enemyfactions)]
    return Caltrops(owner, x, y, np.random.choice(weaponmaterials, p=utils.normalish(len(weaponmaterials), weaponmaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment, bane)

class LooseRoundPebbles(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'loose round pebbles', ':', (255, 255, 255))
        self.hidden = True
        self.trap = True
        self.weight = 10000
        self._info = 'A natural trap, can make you fall prone.'

    def pickableinstance(self):
        return Stone(None, self.x, self.y)

    def entrap(self, creat, part):
        part = np.random.choice([part for part in creat.bodyparts if not part.internal() and not part.destroyed()])
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
        alreadyimbalanced = creat.imbalanced()
        if 'leg' in part.categories:
            numlegs = len([p for p in creat.bodyparts if 'leg' in p.categories and not p.destroyed() and not p.incapacitated()])
            if np.random.rand() < 0.5 - 0.05*numlegs:
                part.imbalanceclock += 20*damage/part.maxhp
        if creat.imbalanced() and not alreadyimbalanced:
            imbalancedtext = ', imbalancing you'
        else:
            imbalancedtext = ''
        if part.parentalconnection != None:
            partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
        elif part == creat.torso:
            partname = 'torso'
        if not creat.dying():
            if part.incapacitated() and not alreadyincapacitated and not part.destroyed():
                creat.log().append('You stepped on ' + self.name + ', falling prone. It incapacitated your ' + partname + imbalancedtext + '.')
                if armordamage > 0:
                    if not armor.destroyed():
                        creat.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                    else:
                        creat.log().append('Your ' + armor.name + ' was destroyed!')
                        armor.owner.remove(armor)
            elif not part.destroyed():
                creat.log().append('You stepped on ' + self.name + ', falling prone. It dealt ' + repr(damage) + ' damage to your ' + partname + imbalancedtext + '.')
                if armordamage > 0:
                    if not armor.destroyed():
                        creat.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                    else:
                        creat.log().append('Your ' + armor.name + ' was destroyed!')
                        armor.owner.remove(armor)
            else:
                creat.log().append('You stepped on ' + self.name + ', falling prone. It destroyed your ' + partname + imbalancedtext + '.')
                if armordamage > 0:
                    if not armor.destroyed():
                        creat.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                    else:
                        creat.log().append('Your ' + armor.name + ' was also destroyed!')
                        armor.owner.remove(armor)
                part.on_destruction(False)
            volume, details = creat.hurtphrase([part])
            if len(details) > 0 and volume > 0 and len([p for p in creat.bodyparts if hasattr(p, 'sound') and p.sound > 0 and not p.destroyed() and not p.incapacitated()]):
                if len(details) == 5:
                    creat.log().append('You ' + details[2] + ': "' + details[4] + '".')
                elif len(details) == 4:
                    creat.log().append('You ' + details[2] + '.')
                utils.infoblast(creat.world, creat.x, creat.y, volume, [creat], details)
        else:
            creat.log().append('You stepped on ' + self.name + ', falling prone. It killed you.')
            creat.log().append('You are dead!')
            if part.destroyed():
                part.on_destruction(True)
            creat.die()
            creat.causeofdeath = ('trip', self)

class ExposedWires(Item):
    def __init__(self, owner, x, y, level):
        super().__init__(owner, x, y, 'exposed ' + repr(50*level) + ' V wires', '_', (184, 115, 51))
        self.hidden = True
        self.trap = True
        self.weight = 100
        self.maxdamage = 5*level
        self._info = 'An accidental trap, can shock you.'

    def pickableinstance(self):
        return None

    def entrap(self, creat, part):
        if part.nonconductive:
            if part.parentalconnection != None:
                partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
            elif part == creat.torso:
                partname = 'torso'
            creat.log().append('You stepped on ' + self.name + ', but as your ' + partname + ' is nonconductive, you were not shocked.')
        else:
            dmglist = []
            destroyedlist = []
            alreadyimbalanced = creat.imbalanced()
            shockedlist = []
            for part in [part for part in creat.bodyparts if not part.destroyed()]:
                resistancemultiplier = 1 - part.resistance('electric')
                totaldamage = np.random.randint(0, int(self.maxdamage*(1/2)**part.bottomheight())+1)
                damage = min(int(resistancemultiplier*totaldamage), part.hp())
                alreadyincapacitated = part.incapacitated()
                part.damagetaken += damage
                if damage > 0:
                    shockedlist.append(part)
                if 'leg' in part.categories:
                    numlegs = len([p for p in creat.bodyparts if 'leg' in p.categories and not p.destroyed() and not p.incapacitated()])
                    if np.random.rand() < 0.5 - 0.05*numlegs:
                        part.imbalanceclock += 20*damage/part.maxhp
                if part.parentalconnection != None:
                    partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
                elif part == creat.torso:
                    partname = 'torso'
                if part.destroyed():
                    dmglist.append('destroyed your ' + partname)
                    destroyedlist.append(part)
                elif not alreadyincapacitated and part.incapacitated():
                    dmglist.append('incapacitated your ' + partname)
                elif damage > 0:
                    dmglist.append('dealt ' + repr(damage) + ' damage to your ' + partname)
            if creat.imbalanced() and not alreadyimbalanced:
                dmglist.append('imbalanced you')
            if len(dmglist) > 1:
                dmglist[-1] = 'and ' + dmglist[-1]
            if len(dmglist) > 2:
                joiner = ', '
            else:
                joiner = ' '
            if not creat.dying():
                creat.log().append('You stepped on ' + self.name + ', getting shocked. The shock ' + joiner.join(dmglist) + '.')
                for part in destroyedlist:
                    part.on_destruction(False)
                volume, details = creat.hurtphrase(shockedlist)
                if len(details) > 0 and volume > 0 and len([p for p in creat.bodyparts if hasattr(p, 'sound') and p.sound > 0 and not p.destroyed() and not p.incapacitated()]):
                    if len(details) == 5:
                        creat.log().append('You ' + details[2] + ': "' + details[4] + '".')
                    elif len(details) == 4:
                        creat.log().append('You ' + details[2] + '.')
                    utils.infoblast(creat.world, creat.x, creat.y, volume, [creat], details)
            else:
                creat.log().append('You stepped on ' + self.name + ', getting shocked. It killed you.')
                creat.log().append('You are dead!')
                for part in destroyedlist:
                    part.on_destruction(True)
                creat.die()
                creat.causeofdeath = ('step', self)

def randomexposedwires(owner, x, y, level):
    level2 = max(1, np.random.randint(level-3, level+4))
    return ExposedWires(owner, x, y, level2)

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

        self._info = 'A piece of armor, made of ' + material + '.'

def randomarmor(owner, x, y, level, armortype=None):
    enchantment = 0
    while np.random.rand() < 0.5 + level/100:
        enchantment += 1
    if armortype == None:
        armortype = np.random.choice(['chest armor', 'barding', 'gauntlet', 'leg armor', 'wheel cover', 'helmet', 'tentacle armor'])
    return PieceOfArmor(owner, x, y, armortype, np.random.choice(armormaterials, p=utils.normalish(len(armormaterials), armormaterials.index(likeliestmaterialbylevel[level]), 3, 0.001)), enchantment)

class SchoolkidBackpack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'schoolkid backpack', '(', (255, 0, 255))
        self.wearable = True
        self.wearcategory = 'back'
        self.carryingcapacity = 10000
        self.weight = 500
        self._info = 'A backpack that can carry up to 10 kg of items.'

class TouristBackpack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'tourist backpack', '(', (0, 0, 255))
        self.wearable = True
        self.wearcategory = 'back'
        self.carryingcapacity = 20000
        self.weight = 1000
        self._info = 'A backpack that can carry up to 20 kg of items.'

class HikerBackpack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hiker backpack', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'back'
        self.carryingcapacity = 40000
        self.weight = 2000
        self._info = 'A backpack that can carry up to 40 kg of items.'

class MilitaryBackpack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'military backpack', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'back'
        self.carryingcapacity = 80000
        self.weight = 4000
        self._info = 'A backpack that can carry up to 80 kg of items.'

class BackpackOfHolding(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'backpack of holding', '(', (190, 110, 0))
        self.wearable = True
        self.wearcategory = 'back'
        self.carryingcapacity = 160000
        self.weight = 1000
        self._info = 'A magical backpack that can carry up to 160 kg of items.'

class GreaterBackpackOfHolding(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'greater backpack of holding', '(', (190, 110, 0))
        self.wearable = True
        self.wearcategory = 'back'
        self.carryingcapacity = 320000
        self.weight = 1000
        self._info = 'A magical backpack that can carry up to 320 kg of items.'

class CapeOfFlying(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cape of flying', '(', (255, 255, 255))
        self.wearable = True
        self.wearcategory = 'back'
        self.weight = 500
        self.stances = ['flying']
        self.flyingspeed = 1
        self._info = 'A magical cape. When worn, enables the flying stance with average speed.'

class CapeOfSmellNeutralizing(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'cape of smell neutralizing', '(', (255, 0, 255))
        self.wearable = True
        self.wearcategory = 'back'
        self.weight = 500
        self.smell = -np.inf
        self._info = 'A magical cape. When worn, prevents you from leaving a smell trace.'

class PriestlyChasuble(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'priestly chasuble', '(', (255, 255, 255))
        self.wearable = True
        self.wearcategory = 'back'
        self.weight = 1000
        self.godlylove = 1
        self._info = 'A back slot item. When worn, reduces the waiting period between successful prayers.'

class WizardlyRobe(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'wizardly robe', '(', (255, 0, 255))
        self.wearable = True
        self.wearcategory = 'back'
        self.weight = 1000
        self.intelligence = 1
        self.manacapacity = 5
        self._info = 'A back slot item. When worn, increases your intelligence by 1 and your mana capaciity by 5.'

def randomBackItem(owner, x, y):
    return np.random.choice([SchoolkidBackpack, TouristBackpack, HikerBackpack, MilitaryBackpack, BackpackOfHolding, GreaterBackpackOfHolding, CapeOfFlying, CapeOfSmellNeutralizing, PriestlyChasuble, WizardlyRobe])(owner, x, y)

class TouristFannyPack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'tourist fanny pack', '(', (0, 0, 255))
        self.wearable = True
        self.wearcategory = 'belt'
        self.carryingcapacity = 5000
        self.weight = 100
        self._info = 'A fanny pack that can carry up to 5 kg of items.'

class HikerFannyPack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'hiker fanny pack', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'belt'
        self.carryingcapacity = 10000
        self.weight = 200
        self._info = 'A fanny pack that can carry up to 10 kg of items.'

class MilitaryFannyPack(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'military fanny pack', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'belt'
        self.carryingcapacity = 20000
        self.weight = 400
        self._info = 'A fanny pack that can carry up to 20 kg of items.'

class FannyPackOfHolding(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'fanny pack of holding', '(', (190, 110, 0))
        self.wearable = True
        self.wearcategory = 'belt'
        self.carryingcapacity = 40000
        self.weight = 100
        self._info = 'A magical fanny pack that can carry up to 40 kg of items.'

class GreaterFannyPackOfHolding(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'greater fanny pack of holding', '(', (190, 110, 0))
        self.wearable = True
        self.wearcategory = 'belt'
        self.carryingcapacity = 80000
        self.weight = 100
        self._info = 'A magical fanny pack that can carry up to 80 kg of items.'

class MartialArtsBelt(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'martial arts belt', '(', (0, 0, 0))
        self.wearable = True
        self.wearcategory = 'belt'
        self.weight = 100
        self.martialartist = True
        self._info = 'A belt. When worn, makes your unarmed attacks ignore height differences.'

class QuickdrawProjectileBelt(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'quickdraw projectile belt', '(', (190, 110, 0))
        self.wearable = True
        self.wearcategory = 'belt'
        self.weight = 100
        self.quickdraw = True
        self._info = 'A belt. When worn, makes throwing unwielded items as fast as throwing wielded ones.'

def randomBelt(owner, x, y):
    return np.random.choice([TouristFannyPack, HikerFannyPack, MilitaryFannyPack, FannyPackOfHolding, GreaterFannyPackOfHolding, MartialArtsBelt, QuickdrawProjectileBelt])(owner, x, y)

class RingOfCarrying(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ring of carrying', '=', (255, 255, 0))
        self.wearable = True
        self.wearcategory = 'ring'
        self.carryingcapacity = 20000
        self.weight = 5
        self._info = 'A magical ring. When worn, increases your carrying capacity by 20 kg.'

class RingOfVision(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ring of vision', '=', (255, 255, 0))
        self.wearable = True
        self.wearcategory = 'ring'
        self.weight = 5
        self._info = 'A magical ring. When worn, increases your range of vision, regardless of whether you have eyes.'

    def sight(self):
        return 1

    def on_wearwield(self, creat):
        creat.fovuptodate = False

    def on_unwearunwield(self, creat):
        creat.fovuptodate = False

class RingOfSustenance(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ring of sustenance', '=', (255, 255, 0))
        self.wearable = True
        self.wearcategory = 'ring'
        self.weight = 5
        self.hungermultiplier = 0.5
        self._info = 'A magical ring. When worn, halves you hunger gaining rate.'

class RingOfBravery(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ring of bravery', '=', (255, 255, 0))
        self.wearable = True
        self.wearcategory = 'ring'
        self.weight = 5
        self.bravery = 0.5
        self._info = 'A magical ring. When worn, gives extra protection against fear.'

class RingOfMana(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ring of mana', '=', (255, 255, 0))
        self.wearable = True
        self.wearcategory = 'ring'
        self.weight = 5
        self.manacapacity = 5
        self._info = 'A magical ring. When worn, increases your mana capacity by 5.'

class RingOfIntelligence(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'ring of intelligence', '=', (255, 255, 0))
        self.wearable = True
        self.wearcategory = 'ring'
        self.weight = 5
        self.intelligence = 1
        self._info = 'A magical ring. When worn, increases your intelligence by 1.'

def randomRing(owner, x, y):
    return np.random.choice([RingOfCarrying, RingOfVision, RingOfSustenance, RingOfBravery, RingOfMana, RingOfIntelligence])(owner, x, y)

class Eyeglasses(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'eyeglasses', '(', (0, 255, 255))
        self.wearable = True
        self.wearcategory = 'face'
        self.weight = 9
        self._info = 'A face slot item. When worn, increases your range of vision, as long as you have eyes.'

    def sight(self):
        if len([part for part in self.owner.owner.owner if 'eye' in part.categories and not (part.destroyed() or part.incapacitated())]) > 0:
            return 1
        else:
            return 0

    def on_wearwield(self, creat):
        creat.fovuptodate = False

    def on_unwearunwield(self, creat):
        creat.fovuptodate = False

class NerdyEyeglasses(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'nerdy eyeglasses', '(', (0, 255, 255))
        self.wearable = True
        self.wearcategory = 'face'
        self.weight = 9
        self.intelligence = 1
        self._info = 'A face slot item. When worn, increases your range of vision, as long as you have eyes, and additionally increases your intelligence by 1.'

    def sight(self):
        if len([part for part in self.owner.owner.owner if 'eye' in part.categories and not (part.destroyed() or part.incapacitated())]) > 0:
            return 1
        else:
            return 0

    def on_wearwield(self, creat):
        creat.fovuptodate = False

    def on_unwearunwield(self, creat):
        creat.fovuptodate = False

class GasMask(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'gas mask', '(', (0, 155, 0))
        self.wearable = True
        self.wearcategory = 'face'
        self.weight = 900
        self.breathepoisonresistance = 1
        self._info = 'A face slot item. When worn, completely protects you from poison gas.'

class BerserkerMask(Item):
    def __init__(self, owner, x, y):
        super().__init__(owner, x, y, 'berserker mask', '(', (255, 0, 0))
        self.wearable = True
        self.wearcategory = 'face'
        self.weight = 200
        self.stances = ['berserk']
        self._info = 'A face slot item. When worn, enables the berserk stance.'

def randomFaceItem(owner, x, y):
    return np.random.choice([Eyeglasses, NerdyEyeglasses, GasMask, BerserkerMask])(owner, x, y)

def randomUtilityItem(owner, x, y):
    return np.random.choice([randomBackItem, randomBelt, randomRing, randomFaceItem])(owner, x, y)