#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 17:32:51 2022

@author: surrealpartisan
"""

from collections import namedtuple
import numpy as np

Altar = namedtuple('Altar', ['x', 'y', 'god'])

class World():

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.walls = np.ones((width, height))
        self.spiderwebs = np.zeros((width, height))
        self.poisongas = np.zeros((width, height))
        self.items = []
        self.creatures = []
        self.altars = []
        self.stairsupcoords = None
        self.stairsdowncoords = None
        self.curetypes = []

    def rooms(self):
        self.walls = np.ones((self.width, self.height))
        roomcenters = []
        def binroom(corners, axis):
            #print(repr(corners))
            if np.random.randint(5) < 4 and corners[axis+2] - corners[axis] > 7:
                lim = np.random.randint(corners[axis]+2, corners[axis+2]-2)
                newax = int(not axis)
                newcors1 = [0, 0, 0, 0]
                newcors2 = [0, 0, 0, 0]
                newcors1[newax], newcors1[newax+2] = corners[newax], corners[newax+2]
                newcors1[axis], newcors1[axis+2] = corners[axis], lim
                newcors2[newax], newcors2[newax+2] = corners[newax], corners[newax+2]
                newcors2[axis], newcors2[axis+2] = lim+1, corners[axis+2]
                binroom(newcors1, newax)
                binroom(newcors2, newax)
            else:
                #print('rageg')
                x1 = np.random.randint(corners[0], (corners[2] + corners[0])/2)
                x2 = np.random.randint((corners[2] + corners[0])/2, corners[2])
                y1 = np.random.randint(corners[1], (corners[3] + corners[1])/2)
                y2 = np.random.randint((corners[3] + corners[1])/2, corners[3])
                self.walls[x1:x2, y1:y2] = 0
                roomcenters.append([int((x1+x2)/2), int((y1+y2)/2)])

        binroom([1, 1, self.width, self.height], 0)

        def erode(x, y):
            self.walls[x, y] = 0
            for neighbor in [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]:
                if 0 < neighbor[0] < self.width-1 and 0 < neighbor[1] < self.height-1 and self.walls[neighbor] == 1 and np.random.randint(4) == 0:
                    erode(neighbor[0], neighbor[1])
        for i in range(self.width):
            for j in range(self.height):
                if self.walls[i,j] == 0:
                    erode(i, j)

        roomsconnected = np.zeros(len(roomcenters))
        roomsconnected[np.random.randint(len(roomcenters))] = 1
        while not roomsconnected.all():
            #i = np.random.choice(np.where(1 - roomsconnected)[0])
            #start = roomcenters[i]
            #j = np.random.choice(np.where(roomsconnected)[0])
            #end = roomcenters[j]
            dist = np.inf
            start = [0,0]
            end = [0,0]
            newroom = 0
            for i in [i for i in range(len(roomcenters)) if not roomsconnected[i]]:
                for j in [i for i in range(len(roomcenters)) if roomsconnected[i]]:
                    newdist = np.sqrt((roomcenters[i][0] - roomcenters[j][0])**2 + (roomcenters[i][1] - roomcenters[j][1])**2)
                    if newdist < dist:
                        dist = newdist
                        start = roomcenters[i]
                        end = roomcenters[j]
                        newroom = i
            coords = [start[0], start[1]]
            while not coords == end:
                axis = np.random.randint(2)
                if coords[axis] < end[axis]:
                    coords[axis] += 1
                elif coords[axis] > end[axis]:
                    coords[axis] -= 1
                self.walls[coords[0], coords[1]] = 0
            roomsconnected[newroom] = 1

        def spreadwebs(x, y):
            self.spiderwebs[x, y] = 1
            for neighbor in [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]:
                if 0 < neighbor[0] < self.width-1 and 0 < neighbor[1] < self.height-1 and self.walls[neighbor] == 0 and self.spiderwebs[neighbor] == 0 and np.random.randint(3) == 0:
                    spreadwebs(neighbor[0], neighbor[1])
        for i in range(np.random.randint(10)):
            x = y = 0
            while self.walls[x, y] != 0:
                x = np.random.randint(self.width)
                y = np.random.randint(self.height)
            spreadwebs(x, y)

        def spreadgas(x, y):
            self.poisongas[x, y] = 1
            for neighbor in [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]:
                if 0 < neighbor[0] < self.width-1 and 0 < neighbor[1] < self.height-1 and self.walls[neighbor] == 0 and self.poisongas[neighbor] == 0 and np.random.randint(3) == 0:
                    spreadgas(neighbor[0], neighbor[1])
        for i in range(np.random.randint(10)):
            x = y = 0
            while self.walls[x, y] != 0:
                x = np.random.randint(self.width)
                y = np.random.randint(self.height)
            spreadgas(x, y)

        x = y = 0
        while self.walls[x, y] != 0:
            x = np.random.randint(self.width)
            y = np.random.randint(self.height)
        self.stairsdowncoords = (x, y)
        x = y = 0
        while self.walls[x, y] != 0 or (x, y) == self.stairsdowncoords:
            x = np.random.randint(self.width)
            y = np.random.randint(self.height)
        self.stairsupcoords = (x, y)