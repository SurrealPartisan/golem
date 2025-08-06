#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 21:37:14 2022

@author: surrealpartisan
"""

import numpy as np
import pygame.locals as lc

mapwidth, mapheight = 100, 40
numlevels = 15
npcrelativebodyparthp = 2/3
npcrelativetotalhp = 1/2
smellhalflife = 5
smellmin = 0.01

enemyfactions = ['undead', 'mole', 'octopus', 'goblinoid', 'canine', 'robot', 'elemental', 'demon']
sins = ['pride', 'greed', 'wrath', 'envy', 'lust', 'gluttony', 'sloth']
letters = 'abcdefghijklmnopqrstuvwxyz'
consonants = 'bcdfghjklmnpqrstvwxyz'
vowels = 'aeiou'

def normalish(length, mu, sigma, base):
    a = [np.e**(-((i-mu)/sigma)**2)+base for i in range(length)]
    return np.array(a)/sum(a)

def drugname():
    syl1 = np.random.choice(['Ab', 'Bra', 'Cil', 'Tra', 'Cog', 'I', 'Bri'])
    syl2 = np.random.choice(['la', 'mo', 'de', 'ca', 'fe', 'ma', 'te'])
    syl3 = np.random.choice(['cil', 'xyl', 'max', 'xium', 'dal', 'dium', 'span', 'lix'])
    return syl1+syl2+syl3

def infusionname():
    return np.random.choice(list(vowels)).join(np.random.choice(list(consonants), 4)).capitalize()

def unpronounceablename(length):
    return ''.join(np.random.choice(list(letters), length)).capitalize()

magicwordlist = 'abracadabra ajji majji la tarajji alakazam chhu montor hocus pocus jantar mantar jadu mantar cary mary fuk presto chango hey bibbidi bobbidi boo azarath metrion zinthos boom zahramay klaatu barada nikto ostagazuzulum rampung ngising semar tilem shazam simsalabim sim sala bim anexhexeton ablanathanalba abraxas agape agla alhim ararita aumgn babalon hriliu iao ipsos jahbulon lashtal meithras nox on thelema viaov vitriol xnoubis micrato raepy sathonich anitay nalkri sator arepo tenet opera rotas in nomine dei benedicite fiat lux '

def markovword(wordlist):
    # wordlist is a string separated by spaces and ending in space
    word = ''
    while len(word) < 3 or word in wordlist.split():
        word = ''
        word += np.random.choice([w[0] for w in wordlist.split()])
        while word[-1] != ' ':
            newletter = np.random.choice([wordlist[i+1] for i in range(len(wordlist)) if wordlist[i] == word[-1]])
            if not (newletter == word[-1] and len(word) > 1 and newletter == word[-2]):
                word += newletter
    return word[:-1]

def magicwords():
    return markovword(magicwordlist).upper() + ' ' +  markovword(magicwordlist).upper()

def magicwords_old():
    length1 = np.random.randint(3, 11)
    length2 = np.random.randint(3, 11)
    return ''.join(np.random.choice(list(letters), length1)).upper() + ' ' + ''.join(np.random.choice(list(letters), length2)).upper()

godlynicknames = {'pride': ['Majestic', 'August', 'Self-Important', 'Self-Righteous', 'Vain', 'Pompous', 'Magnificent'],
                  'greed': ['Rich', 'Plentiful', 'Luxurious', 'Opulent', 'Selfish', 'Scrooge', 'Possessive'],
                  'wrath': ['Hateful', 'Hellish', 'Raving', 'Zealous', 'Furious', 'Warrior', 'Irascible'],
                  'envy': ['Green', 'Spiteful', 'Jealous', 'Coveter', 'Vizier', 'Disinherited', 'Jaundiced'],
                  'lust': ['Perverse', 'Sensual', 'Fetishized', 'Carnal', 'Fleshly', 'Horny', 'Sodomite'],
                  'gluttony': ['Hungry', 'Never-Satiated', 'Corpulent', 'Bloated', 'Black Hole', 'All-Eater', 'Ravenous'],
                  'sloth': ['Sleepy', 'Hibernating', 'Faineant', 'Indolent', 'Lazy', 'Napper', 'Restful']}

def fov(walls, x, y, sight, nowalls=False):
    fovmap = np.zeros((mapwidth, mapheight))
    fovmap[x,y] = 1
    for angle in np.arange(16*sight)*2*np.pi/(16*sight):
        cont = True
        r = 0
        while cont:
            r += 0.5
            x2 = round(x + r*np.cos(angle))
            y2 = round(y + r*np.sin(angle))
            if walls[x2,y2] == 0 or not nowalls:
                fovmap[x2,y2] = 1
            if walls[x2,y2] == 1 or r >= sight: cont = False
    return fovmap

def soundmap(walls, x, y, volume):
    smap = np.ones((mapwidth, mapheight))*(-np.inf)
    smap[x, y] = volume
    changes = True
    r = 0
    while changes:
        changes = False
        r = min(r+1, volume)
        for i in range(max(0, x-r), min(mapwidth, x+r+1)):
            for j in range(max(0, y-r), min(mapheight, y+r+1)):
                if smap[i, j] > 0:
                    dxdylist = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) and i-dx >= 0 and j-dy >= 0 and i+dx < mapwidth and j+dy < mapheight and not walls[i+dx, j+dy]]
                    for dx, dy in dxdylist:
                        newvol = smap[i, j] - np.sqrt(dx**2 + dy**2)
                        if smap[i+dx, j+dy] < newvol:
                            changes = True
                            smap[i+dx, j+dy] = newvol
    return smap

def infoblast(cave, x, y, volume, creatures_involved, details):
    if len(details) > 0:
        if details[0] != 'see only':
            smap = soundmap(cave.walls, x, y, volume)
        for creat in cave.creatures:
            if not creat in creatures_involved:
                if details[0] == 'see only':
                    if creat.fov()[x, y] and creat.sight() > 1:
                        txt = details[1]
                        for i in range(len(creatures_involved)):
                            if creatures_involved[i] in creat.creaturesseen():
                                txt = txt.replace('NAME_' + repr(i), 'the ' + creatures_involved[i].name)
                            else:
                                txt = txt.replace('NAME_' + repr(i), 'something')
                        txt = txt[0].upper() + txt[1:]
                        creat.log().append(txt)
                elif details[0] == 'hear only':
                    if (not creat.fov()[x, y]) and smap[creat.x, creat.y] >= creat.hearing():
                        txt = 'You heard ' + details[1] + '.'
                        for i in range(len(creatures_involved)):
                            if creatures_involved[i] in creat.creaturesseen():
                                txt = txt.replace('NAME_' + repr(i), 'the ' + creatures_involved[i].name)
                            else:
                                txt = txt.replace('NAME_' + repr(i), 'something')
                        creat.log().append(txt)
                elif details[0] == 'see and hear':
                    if creat.fov()[x, y] and creat.sight() > 1 and smap[creat.x, creat.y] >= creat.hearing():
                        if len(details) == 5:
                            txt = details[1] + ' ' + details[2] + ': "' + details[4] + '".'
                        elif len(details) == 4:
                            txt = details[1] + ' ' + details[2] + '.'
                        for i in range(len(creatures_involved)):
                            if creatures_involved[i] in creat.creaturesseen():
                                txt = txt.replace('NAME_' + repr(i), 'the ' + creatures_involved[i].name)
                            else:
                                txt = txt.replace('NAME_' + repr(i), 'something')
                        txt = txt[0].upper() + txt[1:]
                        creat.log().append(txt)
                    elif creat.fov()[x, y] and creat.sight() > 1:
                        if len(details) == 5:
                            txt = details[1] + ' ' + details[2] + ' something, but you couldn\'t hear what.'
                        elif len(details) == 4:
                            txt = 'You saw, but didn\'t hear ' + details[1] + ' ' + details[3] + '.'
                        for i in range(len(creatures_involved)):
                            if creatures_involved[i] in creat.creaturesseen():
                                txt = txt.replace('NAME_' + repr(i), 'the ' + creatures_involved[i].name)
                            else:
                                txt = txt.replace('NAME_' + repr(i), 'something')
                        txt = txt[0].upper() + txt[1:]
                        creat.log().append(txt)
                    elif smap[creat.x, creat.y] >= creat.hearing():
                        if len(details) == 5:
                            txt = 'You heard ' + details[1] + ' ' + details[3] + ': "' + details[4] + '".'
                        elif len(details) == 4:
                            txt = 'You heard ' + details[1] + ' ' + details[3] + '.'
                        for i in range(len(creatures_involved)):
                            if creatures_involved[i] in creat.creaturesseen():
                                txt = txt.replace('NAME_' + repr(i), 'the ' + creatures_involved[i].name)
                            else:
                                txt = txt.replace('NAME_' + repr(i), 'something')
                        creat.log().append(txt)

def constantfunction(c):
    def fun():
        return c
    return fun

def anglebetween(point1, point2):
    newcoords = (point2[1] - point1[1], point2[0] - point1[0])
    return np.arctan2(*newcoords)%(2*np.pi)

class listwithowner(list):
    def __init__(self, iterable, owner):
        super().__init__(iterable)
        self.owner = owner

class loglist(list):
    def append(self, item):
        if len(item) <= mapwidth:
            super().append(item)
        else:
            start = item[:mapwidth]
            end = item[mapwidth:]
            lastspace = start.rfind(' ')
            if lastspace == -1:
                super().append(start)
                self.append(end)
            else:
                super().append(start[:lastspace])
                self.append(start[lastspace+1:] + end)

directionnames = {(-1, -1): 'northwest',
                  (0, -1): 'north',
                  (1, -1): 'northeast',
                  (-1, 0): 'west',
                  (0, 0): 'here',
                  (1, 0): 'east',
                  (-1, 1): 'southwest',
                  (0, 1): 'south',
                  (1, 1): 'southeast',
                  }

bodypartshortnames = {'torso': 'torso',
                      'left arm': 'l arm',
                      'right arm': 'r arm',
                      'left leg': 'l leg',
                      'right leg': 'r leg',
                      'left wing': 'l wing',
                      'right wing': 'r wing',
                      'head': 'head',
                      'heart': 'heart',
                      'left lung': 'l lung',
                      'right lung': 'r lung',
                      'stomach': 'stomach',
                      'left eye': 'l eye',
                      'right eye': 'r eye',
                      'upper left eye': 'ul eye',
                      'upper right eye': 'ur eye',
                      'center left eye': 'cl eye',
                      'center right eye': 'cr eye',
                      'lower left eye': 'll eye',
                      'lower right eye': 'lr eye',
                      'brain': 'brain',
                      'central heart': 'c heart',
                      'left heart': 'l heart',
                      'right heart': 'r heart',
                      'left gills': 'l gills',
                      'right gills': 'r gills',
                      'front left limb': 'fl limb',
                      'center-front left limb': 'cfl limb',
                      'center-back left limb': 'cbl limb',
                      'back left limb': 'bl limb',
                      'front right limb': 'fr limb',
                      'center-front right limb': 'cfr limb',
                      'center-back right limb': 'cbr limb',
                      'back right limb': 'br limb',
                      'front left leg': 'fl leg',
                      'front right leg': 'fr leg',
                      'back left leg': 'bl leg',
                      'back right leg': 'br leg',
                      'tail': 'tail',
                      'front left wheel': 'fl wheel',
                      'front right wheel': 'fr wheel',
                      'back left wheel': 'bl wheel',
                      'back right wheel': 'br wheel',
                      'arm': 'arm',
                      'coolant pumping system': 'cool pump',
                      'coolant aerator system': 'cool aer',
                      'biomass processor': 'biom proc',
                      'left camera': 'l cam',
                      'right camera': 'r cam',
                      'central processor': 'c proc',
                      'left bellows': 'l bell',
                      'right bellows': 'r bell',
                      'eye': 'eye',
                      'left kidney': 'l kidn',
                      'right kidney': 'r kidn',
                      'left metanephridium': 'l metaneph',
                      'right metanephridium': 'r metaneph',
                      'coolant filtering system': 'cool filt'
                      }

keynames = {lc.K_BACKSPACE: 'backspace',
            lc.K_TAB: 'tab',
            lc.K_CLEAR: 'clear',
            lc.K_RETURN: 'return',
            lc.K_PAUSE: 'pause',
            lc.K_ESCAPE: 'escape',
            lc.K_SPACE: 'space',
            lc.K_EXCLAIM: 'exclaim',
            lc.K_QUOTEDBL: 'quotedbl',
            lc.K_HASH: 'hash',
            lc.K_DOLLAR: 'dollar',
            lc.K_AMPERSAND: 'ampersand',
            lc.K_QUOTE: 'quote',
            lc.K_LEFTPAREN: 'left parenthesis',
            lc.K_RIGHTPAREN: 'right parenthesis',
            lc.K_ASTERISK: 'asterisk',
            lc.K_PLUS: 'plus sign',
            lc.K_COMMA: 'comma',
            lc.K_MINUS: 'minus sign',
            lc.K_PERIOD: 'period',
            lc.K_SLASH: 'forward slash',
            lc.K_0: '0',
            lc.K_1: '1',
            lc.K_2: '2',
            lc.K_3: '3',
            lc.K_4: '4',
            lc.K_5: '5',
            lc.K_6: '6',
            lc.K_7: '7',
            lc.K_8: '8',
            lc.K_9: '9',
            lc.K_COLON: 'colon',
            lc.K_SEMICOLON: 'semicolon',
            lc.K_LESS: 'less-than sign',
            lc.K_EQUALS: 'equals sign',
            lc.K_GREATER: 'greater-than sign',
            lc.K_QUESTION: 'question mark',
            lc.K_AT: 'at',
            lc.K_LEFTBRACKET: 'left bracket',
            lc.K_BACKSLASH: 'backslash',
            lc.K_RIGHTBRACKET: 'right bracket',
            lc.K_CARET: 'caret',
            lc.K_UNDERSCORE: 'underscore',
            lc.K_BACKQUOTE: 'grave',
            lc.K_a: 'a',
            lc.K_b: 'b',
            lc.K_c: 'c',
            lc.K_d: 'd',
            lc.K_e: 'e',
            lc.K_f: 'f',
            lc.K_g: 'g',
            lc.K_h: 'h',
            lc.K_i: 'i',
            lc.K_j: 'j',
            lc.K_k: 'k',
            lc.K_l: 'l',
            lc.K_m: 'm',
            lc.K_n: 'n',
            lc.K_o: 'o',
            lc.K_p: 'p',
            lc.K_q: 'q',
            lc.K_r: 'r',
            lc.K_s: 's',
            lc.K_t: 't',
            lc.K_u: 'u',
            lc.K_v: 'v',
            lc.K_w: 'w',
            lc.K_x: 'x',
            lc.K_y: 'y',
            lc.K_z: 'z',
            lc.K_DELETE: 'delete',
            lc.K_KP0: 'keypad 0',
            lc.K_KP1: 'keypad 1',
            lc.K_KP2: 'keypad 2',
            lc.K_KP3: 'keypad 3',
            lc.K_KP4: 'keypad 4',
            lc.K_KP5: 'keypad 5',
            lc.K_KP6: 'keypad 6',
            lc.K_KP7: 'keypad 7',
            lc.K_KP8: 'keypad 8',
            lc.K_KP9: 'keypad 9',
            lc.K_KP_PERIOD: 'keypad period',
            lc.K_KP_DIVIDE: 'keypad divide',
            lc.K_KP_MULTIPLY: 'keypad multiply',
            lc.K_KP_MINUS: 'keypad minus',
            lc.K_KP_PLUS: 'keypad plus',
            lc.K_KP_ENTER: 'keypad enter',
            lc.K_KP_EQUALS: 'keypad equals',
            lc.K_UP: 'up arrow',
            lc.K_DOWN: 'down arrow',
            lc.K_RIGHT: 'right arrow',
            lc.K_LEFT: 'left arrow',
            lc.K_INSERT: 'insert',
            lc.K_HOME: 'home',
            lc.K_END: 'end',
            lc.K_PAGEUP: 'page up',
            lc.K_PAGEDOWN: 'page down',
            lc.K_F1: 'F1',
            lc.K_F2: 'F2',
            lc.K_F3: 'F3',
            lc.K_F4: 'F4',
            lc.K_F5: 'F5',
            lc.K_F6: 'F6',
            lc.K_F7: 'F7',
            lc.K_F8: 'F8',
            lc.K_F9: 'F9',
            lc.K_F10: 'F10',
            lc.K_F11: 'F11',
            lc.K_F12: 'F12',
            lc.K_F13: 'F13',
            lc.K_F14: 'F14',
            lc.K_F15: 'F15',
            lc.K_NUMLOCK: 'numlock',
            lc.K_CAPSLOCK: 'capslock',
            lc.K_SCROLLOCK: 'scrollock',
            lc.K_RSHIFT: 'right shift',
            lc.K_LSHIFT: 'left shift',
            lc.K_RCTRL: 'right control',
            lc.K_LCTRL: 'left control',
            lc.K_RALT: 'right alt',
            lc.K_LALT: 'left alt',
            lc.K_RMETA: 'right meta',
            lc.K_LMETA: 'left meta',
            lc.K_LSUPER: 'left Windows key',
            lc.K_RSUPER: 'right Windows key',
            lc.K_MODE: 'mode shift',
            lc.K_HELP: 'help',
            lc.K_PRINT: 'print screen',
            lc.K_SYSREQ: 'sysrq',
            lc.K_BREAK: 'break',
            lc.K_MENU: 'menu',
            lc.K_POWER: 'power',
            lc.K_EURO: 'Euro',
            lc.K_AC_BACK: 'Android back button'}

numkeys = {0: (lc.K_1, lc.K_KP1),
           1: (lc.K_2, lc.K_KP2),
           2: (lc.K_3, lc.K_KP3),
           3: (lc.K_4, lc.K_KP4),
           4: (lc.K_5, lc.K_KP5),
           5: (lc.K_6, lc.K_KP6),
           6: (lc.K_7, lc.K_KP7),
           7: (lc.K_8, lc.K_KP8),
           8: (lc.K_9, lc.K_KP9),
           9: (lc.K_0, lc.K_KP0)
           }