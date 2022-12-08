#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 17:32:51 2022

@author: surrealpartisan
"""

import numpy as np

class World():
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.walls = np.ones((width, height))
        self.items = []
        self.creatures = []
    
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
            i = np.random.choice(np.where(1 - roomsconnected)[0])
            start = roomcenters[i]
            j = np.random.choice(np.where(roomsconnected)[0])
            end = roomcenters[j]
            coords = [start[0], start[1]]
            while not coords == end:
                axis = np.random.randint(2)
                if coords[axis] < end[axis]:
                    coords[axis] += 1
                elif coords[axis] > end[axis]:
                    coords[axis] -= 1
                self.walls[coords[0], coords[1]] = 0
            roomsconnected[i] = 1