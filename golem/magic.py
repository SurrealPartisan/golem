#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 19:25:21 2024

@author: surrealpartisan
"""

import numpy as np
from roman import toRoman
from golem import item
from golem.utils import numlevels, mapwidth, mapheight, magicwords, infoblast


class Spell():
    def __init__(self, name, intelligencerequirement, manarequirement, castingtime, scalable):
        if scalable:
            self.name = name + ' ' + toRoman(intelligencerequirement)
        else:
            self.name = name
        self.intelligencerequirement = intelligencerequirement
        self.manarequirement = manarequirement
        self.castingtime = castingtime
        self.words = magicwords()
        self._info = 'No information available.'

    def cast(self, caster):
        caster.manaused += self.manarequirement
        if caster.speech and len([p for p in caster.bodyparts if hasattr(p, 'sound') and p.sound > 0 and not p.destroyed() and not p.incapacitated()]):
            caster.log().append('You said the magic words: "' + self.words + '"!')
            infoblast(caster.world, caster.x, caster.y, 15, [
                      caster], ('see and hear', 'NAME_0', 'casted a spell saying', 'cast a spell saying', self.words))
        else:
            caster.log().append('You casted a spell without words.')
            infoblast(caster.world, caster.x, caster.y, 15, [
                      caster], ('see only', 'NAME_0 casted a spell without words.'))

    def info(self):
        return self._info


class ChoiceSpell(Spell):
    def __init__(self, name, intelligencerequirement, manarequirement, castingtime, scalable):
        super().__init__(name, intelligencerequirement,
                         manarequirement, castingtime, scalable)
        self.choiceprompt = ''
        self.nochoicesmessage = ''

    def choices(self, caster):
        return []

    def choicedescription(self, caster, choice):
        return ''

    def cast(self, caster, choice):
        super().cast(caster)


class TargetedSpell(Spell):
    def __init__(self, name, intelligencerequirement, manarequirement, castingtime, scalable):
        super().__init__(name, intelligencerequirement,
                         manarequirement, castingtime, scalable)
        self.targetchoiceprompt = ''
        self.notargetmessage = ''

    def suitabletargetmessage(self, target):
        return ''

    def cast(self, caster, target):
        super().cast(caster)


class BodypartTargetedSpell(Spell):
    def __init__(self, name, intelligencerequirement, manarequirement, castingtime, scalable):
        super().__init__(name, intelligencerequirement,
                         manarequirement, castingtime, scalable)
        self.targetchoiceprompt = ''
        self.notargetmessage = ''

    def partchoiceprompt(self, target):
        return ''

    def suitabletargetmessage(self, target):
        return ''

    def partchoices(self, target):
        return []

    def partdescription(self, target, targetbodypart, caster):
        return ''

    def cast(self, caster, target, targetbodypart):
        super().cast(caster)


class AreaSpell(Spell):
    def __init__(self, name, intelligencerequirement, manarequirement, castingtime, scalable):
        super().__init__(name, intelligencerequirement,
                         manarequirement, castingtime, scalable)
        self.locationchoiceprompt = ''
        self.suitablelocationmessage = ''
        self.unsuitablelocationmessage = ''
        self.radius = 0

    def suitablelocation(self, cave, x, y):
        return True

    def cast(self, caster, cave, x, y):
        super().cast(caster)


class HealThyself(ChoiceSpell):
    def __init__(self, level):
        super().__init__('Heal Thyself', level, 5, 1, True)
        self.choiceprompt = 'Choose the bodypart to heal:'
        self.nochoicesmessage = 'You have no bodyparts suitable for healing.'
        self.hpgiven = 3*level
        self._info = 'Heal chosen bodypart (fleshy or elemental) by up to ' + repr(
            self.hpgiven) + ' points.'

    def choices(self, caster):
        return [part for part in caster.bodyparts if not part.destroyed() and part.material in ['living flesh', 'undead flesh', 'elemental'] and part.damagetaken > 0]

    def choicedescription(self, caster, choice):
        if choice.parentalconnection != None:
            partname = list(choice.parentalconnection.parent.childconnections.keys())[list(
                choice.parentalconnection.parent.childconnections.values()).index(choice.parentalconnection)]
        elif choice == caster.torso:
            partname = 'torso'
        return partname + ' (hp: ' + repr(choice.hp()) + '/' + repr(choice.maxhp) + ')'

    def cast(self, caster, choice):
        super().cast(caster, choice)
        caster.log().append('You cast ' + self.name + '.')
        caster.heal(choice, self.hpgiven)


class CreateWeapon(ChoiceSpell):
    def __init__(self, level):
        super().__init__('Create Weapon', level, 15, 3, True)
        self.choiceprompt = 'Choose the type of weapon to create:'
        self.nochoicesmessage = ''
        self._info = 'Create a random weapon of the chosen type.'

    def choices(self, caster):
        return [item.randomdagger, item.randomspear, item.randommace, item.randomsword, item.randompickaxe]

    def choicedescription(self, caster, choice):
        if choice == item.randomdagger:
            return 'Dagger'
        if choice == item.randomspear:
            return 'Spear'
        if choice == item.randommace:
            return 'Mace'
        if choice == item.randomsword:
            return 'Sword'
        if choice == item.randompickaxe:
            return 'Pickaxe'

    def cast(self, caster, choice):
        super().cast(caster, choice)
        creation = choice(caster.inventory, 0, 0, self.intelligencerequirement)
        caster.log().append('You magically created a ' + creation.name)


class CreateArmor(ChoiceSpell):
    def __init__(self, level):
        super().__init__('Create Armor', level, 15, 3, True)
        self.choiceprompt = 'Choose the type of piece of armor to create:'
        self.nochoicesmessage = ''
        self._info = 'Create a random piece of armor of the chosen type.'

    def choices(self, caster):
        return ['chest armor', 'barding', 'gauntlet', 'leg armor', 'wheel cover', 'helmet', 'tentacle armor']

    def choicedescription(self, caster, choice):
        return choice

    def cast(self, caster, choice):
        super().cast(caster, choice)
        creation = item.randomarmor(
            caster.inventory, 0, 0, self.intelligencerequirement, armortype=choice)
        caster.log().append('You magically created a ' + creation.name)


class CurseOfSlowness(TargetedSpell):
    def __init__(self, level):
        super().__init__('Curse of Slowness', level, 7, 0.75, True)
        self.targetchoiceprompt = 'Choose who to slow down using movement keys:'
        self.notargetmessage = 'No suitable targets observed here.'
        self.maxslowtime = 3*level
        self._info = 'Make an enemy slowed for up to ' + \
            repr(self.maxslowtime) + ' seconds. No miss chance.'

    def suitabletargetmessage(self, target):
        return 'Press Return to target the ' + target.name + '.'

    def cast(self, caster, target):
        super().cast(caster, target)
        if not target.dead:
            target.slowedclock += np.random.randint(1, self.maxslowtime+1)
            caster.log().append('You cursed the ' + target.name + ' to be slowed!')
            target.log().append('The ' + caster.name + ' cursed you to be slowed!')
        else:
            caster.log().append('The ' + target.name + ' died while you were casting the spell.')


class CurseOfWeakness(TargetedSpell):
    def __init__(self, level):
        super().__init__('Curse of Weakness', level, 7, 0.75, True)
        self.targetchoiceprompt = 'Choose who to weaken using movement keys:'
        self.notargetmessage = 'No suitable targets observed here.'
        self.maxweakentime = 3*level
        self._info = 'Make an enemy weakened for up to ' + \
            repr(self.maxweakentime) + ' seconds. No miss chance.'

    def suitabletargetmessage(self, target):
        return 'Press Return to target the ' + target.name + '.'

    def cast(self, caster, target):
        super().cast(caster, target)
        if not target.dead:
            target.weakenedclock += np.random.randint(1, self.maxweakentime+1)
            caster.log().append('You cursed the ' + target.name + ' to be weakened!')
            target.log().append('The ' + caster.name + ' cursed you to be weakened!')
        else:
            caster.log().append('The ' + target.name + ' died while you were casting the spell.')


class ReadMemories(TargetedSpell):
    def __init__(self):
        super().__init__('Read Memories', 1, 20, 1, False)
        self.targetchoiceprompt = 'Choose whose memories to read using movement keys:'
        self.notargetmessage = 'No suitable targets observed here.'
        self._info = 'Learn the religious rituals, spells, detected hidden items, and location history of the target.'

    def suitabletargetmessage(self, target):
        return 'Press Return to target the ' + target.name + '.'

    def cast(self, caster, target):
        super().cast(caster, target)
        if not target.dead:
            targetbrains = [part for part in target.bodyparts if 'brain' in part.categories and not (
                part.destroyed() or part.incapacitated())]
            if len(targetbrains) > 0:
                for gd in target.godsknown():
                    if not gd in caster.godsknown():
                        caster.godsknown().append(gd)
                for spell in target.spellsknown():
                    if not spell.name in [spll.name for spll in caster.spellsknown()]:
                        caster.spellsknown().append(spell)
                for it in target.itemsseen():
                    if not it in caster.itemsseen():
                        caster.itemsseen().append(it)
                for z in range(numlevels):
                    for x in range(mapwidth):
                        for y in range(mapheight):
                            if caster.seen()[z][x][y] == (' ', (255, 255, 255), (0, 0, 0), (0, 0, 0)) and target.seen()[z][x][y] != (' ', (255, 255, 255), (0, 0, 0), (0, 0, 0)):
                                caster.seen()[z][x][y] = target.seen()[z][x][y]
                caster.log().append('You successfully read the memories of the ' + target.name + '.')
            else:
                caster.log().append('The ' + target.name +
                                    ' has no working brain, so you were unable to read its memories.')
        else:
            caster.log().append('The ' + target.name + ' died while you were casting the spell.')


class MissileSpell(BodypartTargetedSpell):
    def __init__(self, level, damagetype):
        super().__init__(damagetype.capitalize() + ' Missile', level, 10, 0.5, True)
        self.targetchoiceprompt = 'Choose who to attack with ' + \
            self.name + ' using movement keys:'
        self.notargetmessage = 'No suitable targets observed here.'
        self.damagetype = damagetype
        self.mindamage = 1
        self.maxdamage = 3*level
        self.hitprobability = 0.8 + 0.02*level
        self._info = 'Do a ranged attack to deal up to ' + \
            repr(self.maxdamage) + self.damagetype + ' damage.'

    def partchoiceprompt(self, target):
        return 'Choose where to attack the ' + target.name + ':'

    def suitabletargetmessage(self, target):
        return 'Press Return to target the ' + target.name + '.'

    def partchoices(self, target):
        return [part for part in target.bodyparts if not part.internal() and not part.destroyed()]

    def partdescription(self, target, targetbodypart, caster):
        if targetbodypart.parentalconnection != None:
            partname = list(targetbodypart.parentalconnection.parent.childconnections.keys())[list(
                targetbodypart.parentalconnection.parent.childconnections.values()).index(targetbodypart.parentalconnection)]
        elif targetbodypart == target.torso:
            partname = 'torso'
        if caster.stance == 'aggressive':
            attackerstancecoefficient = 1.25
        elif caster.stance == 'defensive':
            attackerstancecoefficient = 0.9
        elif caster.stance == 'berserk':
            attackerstancecoefficient = 1.5
        else:
            attackerstancecoefficient = 1
        if (caster.stance == 'flying' or caster.world.largerocks[caster.x, caster.y]) and target.stance != 'flying' and not caster.world.largerocks[target.x, target.y]:
            highgroundcoefficient = 1.05
        elif caster.stance != 'flying' and not caster.world.largerocks[caster.x, caster.y] and (target.stance == 'flying' or caster.world.largerocks[target.x, target.y]):
            highgroundcoefficient = 0.95
        else:
            highgroundcoefficient = 1
        if target.stance == 'aggressive':
            defenderstancecoefficient = 1.111
        elif target.stance == 'defensive':
            defenderstancecoefficient = 0.80
        elif target.stance == 'berserk':
            defenderstancecoefficient = 1.222
        else:
            defenderstancecoefficient = 1
        if hasattr(targetbodypart, 'protectiveness'):
            protectioncoefficient = 1 + targetbodypart.protectiveness
        else:
            protectioncoefficient = 1
            for part in [part for part in target.bodyparts if hasattr(part, 'protectiveness') and part != targetbodypart and not part.destroyed() and not part.incapacitated()]:
                upperlimit = part.baseheight() + part.upperpoorlimit
                lowerlimit = part.baseheight() + part.lowerpoorlimit
                if upperlimit >= targetbodypart.topheight() >= lowerlimit or upperlimit >= targetbodypart.bottomheight() >= lowerlimit or targetbodypart.topheight() >= upperlimit >= targetbodypart.bottomheight():
                    protectioncoefficient *= (1 - part.protectiveness)
        speedcoefficient = 1/np.sqrt(target.speed()+0.1)
        if target.imbalanced():
            imbalancedcoefficient = 1.25
        else:
            imbalancedcoefficient = 1
        targetdescription = partname + ' (' + repr(int(self.hitprobability*attackerstancecoefficient*highgroundcoefficient*defenderstancecoefficient *
                                                       protectioncoefficient*speedcoefficient*imbalancedcoefficient*targetbodypart.defensecoefficient() * 100)) + '%)'
        if targetbodypart.incapacitated():
            targetdescription += ' [INCAPACITATED]'
        return targetdescription

    def cast(self, caster, target, targetbodypart):
        super().cast(caster, target, targetbodypart)
        if not target.dead:
            caster.fight(target, targetbodypart, item.Attack(self.name, 'blasted', 'blasted', 'blast', ' with ' + self.name, ' with ' + self.name,
                         self.hitprobability, 0, self.mindamage, self.maxdamage, self.damagetype, 0, [], [], None), magical=True, sound=False, kiai=False)
        else:
            caster.log().append('The ' + target.name + ' died while you were casting the spell.')


class SharpMissile(MissileSpell):
    def __init__(self, level):
        super().__init__(level, 'sharp')


class BluntMissile(MissileSpell):
    def __init__(self, level):
        super().__init__(level, 'blunt')


class RoughMissile(MissileSpell):
    def __init__(self, level):
        super().__init__(level, 'rough')


class FireMissile(MissileSpell):
    def __init__(self, level):
        super().__init__(level, 'fire')


class ElectricMissile(MissileSpell):
    def __init__(self, level):
        super().__init__(level, 'electric')


class CurseOfBleeding(BodypartTargetedSpell):
    def __init__(self, level):
        super().__init__('Curse of Bleeding', level, 12, 1, True)
        self.targetchoiceprompt = 'Choose who to attack with ' + \
            self.name + ' using movement keys:'
        self.notargetmessage = 'No suitable targets observed here.'
        self.hitprobability = 0.8 + 0.02*level
        self.maxbleedtime = 5*level
        self._info = 'Make any bodypart of an enemy bleed for up to ' + \
            repr(self.maxbleedtime) + \
            ' seconds as a ranged attack that ignores most of the factors usually affecting hit probability.'

    def partchoiceprompt(self, target):
        return 'Choose the part of the ' + target.name + ' to make bleed:'

    def suitabletargetmessage(self, target):
        return 'Press Return to target the ' + target.name + '.'

    def partchoices(self, target):
        return [part for part in target.bodyparts if not part.destroyed()]

    def partdescription(self, target, targetbodypart, caster):
        if targetbodypart.parentalconnection != None:
            partname = list(targetbodypart.parentalconnection.parent.childconnections.keys())[list(
                targetbodypart.parentalconnection.parent.childconnections.values()).index(targetbodypart.parentalconnection)]
        elif targetbodypart == target.torso:
            partname = 'torso'
        targetdescription = partname + \
            ' (' + repr(int(self.hitprobability *
                            targetbodypart.defensecoefficient() * 100)) + '%)'
        if targetbodypart.incapacitated():
            targetdescription += ' [INCAPACITATED]'
        return targetdescription

    def cast(self, caster, target, targetbodypart):
        super().cast(caster, target, targetbodypart)
        if not target.dead:
            if targetbodypart in target.bodyparts and not targetbodypart.destroyed():
                if np.random.rand() < max(min(self.hitprobability*targetbodypart.defensecoefficient(), 0.95), 0.05):
                    targetbodypart.bleedclocks.append(
                        (np.random.randint(1, self.maxbleedtime+1), 0, caster))
                    if targetbodypart.parentalconnection != None:
                        partname = list(targetbodypart.parentalconnection.parent.childconnections.keys())[list(
                            targetbodypart.parentalconnection.parent.childconnections.values()).index(targetbodypart.parentalconnection)]
                    elif targetbodypart == target.torso:
                        partname = 'torso'
                    caster.log().append('You cursed the ' + target.name +
                                        ' to bleed from its ' + partname + '!')
                    target.log().append('The ' + caster.name +
                                        ' cursed you to bleed from your ' + partname + '!')
                else:
                    caster.log().append('Your curse missed the ' + target.name + '.')
            elif targetbodypart.destroyed():
                caster.log().append('The target body part is already destroyed!')
            else:
                caster.log().append('The ' + target.name + ' no longer has that part!')
        else:
            caster.log().append('The ' + target.name + ' died while you were casting the spell.')


class CreateSpiderweb(AreaSpell):
    def __init__(self):
        super().__init__('Create Spiderweb', 1, 10, 2, False)
        self.locationchoiceprompt = 'Choose the location where you want to create the spiderweb using the movement keys:'
        self.suitablelocationmessage = 'Press Return to create a spiderweb here.'
        self.unsuitablelocationmessage = 'You cannot create a spiderweb here.'

    def suitablelocation(self, cave, x, y):
        return not cave.walls[x, y] and not cave.lavapits[x, y] and not cave.campfires[x, y] and not cave.spiderwebs[x, y]

    def cast(self, caster, cave, x, y):
        super().cast(caster, cave, x, y)
        cave.spiderwebs[x, y] = 1
        caster.log().append('You magically created a spiderweb.')


def randomspell(level):
    level2 = max(1, np.random.randint(level-3, level+4))
    return np.random.choice([HealThyself(level2), CreateWeapon(level2), CreateArmor(level2), CurseOfSlowness(level2), CurseOfWeakness(level2), ReadMemories(), SharpMissile(level2), BluntMissile(level2), RoughMissile(level2), FireMissile(level2), ElectricMissile(level2), CurseOfBleeding(level2), CreateSpiderweb()])
