#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 21:37:14 2022

@author: surrealpartisan
"""

import numpy as np

mapwidth, mapheight = 80, 40
numlevels = 10

def drugname():
    syl1 = np.random.choice(['Ab', 'Bra', 'Cil', 'Tra', 'Cog', 'I', 'Bri'])
    syl2 = np.random.choice(['la', 'mo', 'de', 'ca', 'fe', 'ma', 'te'])
    syl3 = np.random.choice(['cil', 'xyl', 'max', 'xium', 'dal', 'dium', 'span', 'lix'])
    return syl1+syl2+syl3

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