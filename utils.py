#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 21:37:14 2022

@author: surrealpartisan
"""

import numpy as np
import pygame.locals as lc

mapwidth, mapheight = 100, 40
numlevels = 5

enemyfactions = ['undead', 'mole', 'octopus', 'goblinoid', 'canine', 'robot']
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

def fov(walls, x, y, sight):
    fovmap = np.zeros((mapwidth, mapheight))
    fovmap[x,y] = 1
    for angle in np.arange(16*sight)*2*np.pi/(16*sight):
        cont = True
        r = 0
        while cont:
            r += 0.5
            x2 = round(x + r*np.cos(angle))
            y2 = round(y + r*np.sin(angle))
            fovmap[x2,y2] = 1
            if walls[x2,y2] == 1 or r >= sight: cont = False
    return fovmap

def anglebetween(point1, point2):
    newcoords = (point2[1] - point1[1], point2[0] - point1[0])
    return np.arctan2(*newcoords)%(2*np.pi)

class listwithowner(list):
    def __init__(self, iterable, owner):
        super().__init__(iterable)
        self.owner = owner

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