import sys

import pygame
from pygame.locals import *
import pygcurse
import numpy as np

import item
import creature

pygame.init()

mapwidth, mapheight = 80, 40
logheight = 8
statuslines = 1
win = pygcurse.PygcurseWindow(mapwidth, mapheight + statuslines + logheight, 'Golem: A Self-Made Person')
win.autoupdate = False
cave = np.ones((mapwidth, mapheight))

def rooms():
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
            cave[x1:x2, y1:y2] = 0
            roomcenters.append([int((x1+x2)/2), int((y1+y2)/2)])
    
    binroom([1, 1, mapwidth, mapheight], 0)
    
    def erode(x, y):
        cave[x, y] = 0
        for neighbor in [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]:
            if 0 < neighbor[0] < mapwidth-1 and 0 < neighbor[1] < mapheight-1 and cave[neighbor] == 1 and np.random.randint(4) == 0:
                erode(neighbor[0], neighbor[1])
    for i in range(mapwidth):
        for j in range(mapheight):
            if cave[i,j] == 0:
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
            cave[coords[0], coords[1]] = 0
        roomsconnected[i] = 1
    
rooms()     

player = creature.Creature(cave)
while cave[player.x, player.y] != 0:
    player.x= np.random.randint(mapwidth)
    player.y = np.random.randint(mapheight)

caveitems = []
for i in range(10):
    x = y = 0
    while cave[x, y] != 0:
        x = np.random.randint(mapwidth)
        y = np.random.randint(mapheight)
    item.create_medication(caveitems, x, y)

log = ['Welcome to the cave!', "Press 'h' for help."]
logback = 0 # How far the log has been scrolled

gamestate = 'free'


def draw():
    # Background
    win.setscreencolors(None, 'black', clear=True)
    for i in range(mapwidth):
        for j in range(mapheight):
            if cave[i,j] == 1:
                win.putchars(' ', x=i, y=j, bgcolor='white')
    
    # Items
    for it in caveitems:
        win.putchars(it.char, x=it.x, y=it.y, 
                 bgcolor='black', fgcolor=it.color)
    
    # Creatures
    win.putchars(player.char, x=player.x, y=player.y, 
                 bgcolor='black', fgcolor='white')
    
    # Status
    for i in range(mapwidth):
        win.putchars(' ', x=i, y=mapheight, bgcolor=((128,128,128)))
    win.putchars('hp: ' + repr(player.hp), x=2, y=mapheight, bgcolor=((128,128,128)), fgcolor=(0, 255, 0))
    win.putchars('items in inventory: ' + repr(len(player.inventory)), x=15, y=mapheight, bgcolor=((128,128,128)), fgcolor=(0, 255, 0))
    win.putchars('items in the cave: ' + repr(len(caveitems)), x=40, y=mapheight, bgcolor=((128,128,128)), fgcolor=(0, 255, 0))
    
    # Log
    if gamestate == 'free':
        logrows = min(logheight,len(log))
        for i in range(logrows):
            j = i-logrows-logback
            c = 255 + (max(j+1, -logheight))*128//logheight
            win.write(log[j], x=0, y=mapheight+statuslines+i, fgcolor=(c,c,c))
    elif gamestate == 'mine':
        minemessage = 'Choose the direction to mine!'
        win.write(minemessage, x=0, y=mapheight+statuslines, fgcolor=(255,255,255))
        
    win.update()

def checkitems(x,y):
    for it in caveitems:
        if it.x == x and it.y == y:
            log.append('There is a ' + it.name + ' here.')
            logback = 0

draw()
while True:
    for event in pygame.event.get():
        try:
            if event.type == KEYDOWN:
                if gamestate == 'free':
                    # Player movements. This code needs some drying.
                    if event.key == K_UP:
                        if player.move(0, -1):
                            log.append('You moved north.')
                            logback = 0
                            checkitems(player.x,player.y)
                        else:
                            log.append("There's a wall in your way.")
                            logback = 0
                    if event.key == K_DOWN:
                        if player.move(0, 1):
                            log.append('You moved south.')
                            logback = 0
                            checkitems(player.x,player.y)
                        else:
                            log.append("There's a wall in your way.")
                            logback = 0
                    if event.key == K_LEFT:
                        if player.move(-1, 0):
                            log.append('You moved west.')
                            logback = 0
                            checkitems(player.x,player.y)
                        else:
                            log.append("There's a wall in your way.")
                            logback = 0
                    if event.key == K_RIGHT:
                        if player.move(1, 0):
                            log.append('You moved east.')
                            logback = 0
                            checkitems(player.x,player.y)
                        else:
                            log.append("There's a wall in your way.")
                            logback = 0
                    
                    if event.key == K_m:
                        gamestate = 'mine'
                    
                    # Items
                    if event.key == K_COMMA:
                        pickcount = 0
                        for it in caveitems:
                            if it.x == player.x and it.y == player.y:
                                pickcount += 1
                                caveitems.remove(it)
                                player.inventory.append(it)
                                it.owner = player.inventory
                                log.append('You pick up the ' + it.name + '.')
                                logback = 0
                        if pickcount == 0:
                            log.append('Nothing to pick up here.')
                            logback = 0
                    if event.key == K_i:
                        log.append('Items in your backpack:')
                        if len(player.inventory) == 0:
                            log.append('  - nothing')
                            logback = 0
                        else:
                            for it in player.inventory:
                                log.append('  - a ' + it.name)
                                if len(player.inventory) > logheight - 1:
                                    logback = len(player.inventory) - logheight + 1
                                else:
                                    logback = 0
                    if event.key == K_c:
                        medicated = 0
                        selected = None
                        for it in player.inventory:
                            if medicated == 0 and it.consumable and it.hpgiven() > 0:
                                medicated = 1
                                selected = it
                        if medicated == 1:
                            selected.consume(player)
                            log.append('You consumed a ' + it.name + ', healing ' + repr(it.hpgiven()) + ' points.')
                        else:
                            log.append("You don't have any drugs to take.")
                        logback = 0
                    
                    # Help
                    if event.key == K_h:
                        log.append('Commands:')
                        log.append('  - arrows: move')
                        log.append('  - comma: pick up an item')
                        log.append('  - i: check your inventory')
                        log.append('  - c: take some medication')
                        log.append('  - page up, page down, home, end: explore the log')
                        log.append('  - h: this list of commands')
                        logback = 0 # Increase when adding commands
                    
                    # Log scrolling
                    if event.key == K_PAGEUP:
                        if len(log) >= logheight:
                            logback = min(logback+1, len(log)-logheight)
                    if event.key == K_PAGEDOWN:
                        logback = max(logback-1, 0)
                    if event.key == K_HOME:
                        if len(log) >= logheight:
                            logback = len(log)-logheight
                    if event.key == K_END:
                        logback = 0
                        
                elif gamestate == 'mine':
                    if event.key == K_UP:
                        if player.y-1 == 0:
                            log.append('That is too hard for you to mine.')
                            logback = 0
                        elif cave[player.x, player.y-1] == 1:
                            log.append('You mined north.')
                            logback = 0
                            cave[player.x, player.y-1] = 0
                        else:
                            log.append("There's no wall there.")
                            logback = 0
                        gamestate = 'free'
                    if event.key == K_DOWN:
                        if player.y+1 == mapheight-1:
                            log.append('That is too hard for you to mine.')
                            logback = 0
                        elif cave[player.x, player.y+1] == 1:
                            log.append('You mined south.')
                            logback = 0
                            cave[player.x, player.y+1] = 0
                        else:
                            log.append("There's no wall there.")
                            logback = 0
                        gamestate = 'free'
                    if event.key == K_LEFT:
                        if player.x-1 == 0:
                            log.append('That is too hard for you to mine.')
                            logback = 0
                        elif cave[player.x-1, player.y] == 1:
                            log.append('You mined west.')
                            logback = 0
                            cave[player.x-1, player.y] = 0
                        else:
                            log.append("There's no wall there.")
                            logback = 0
                        gamestate = 'free'
                    if event.key == K_RIGHT:
                        if player.x+1 == mapwidth-1:
                            log.append('That is too hard for you to mine.')
                            logback = 0
                        elif cave[player.x+1, player.y] == 1:
                            log.append('You mined east.')
                            logback = 0
                            cave[player.x+1, player.y] = 0
                        else:
                            log.append("There's no wall there.")
                            logback = 0
                        gamestate = 'free'
                
                # Quitting via Esc
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                
                # Update window after any command or keypress
                draw()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        
        # Make sure the window is closed if the game crashes
        except Exception as e:
            pygame.quit()
            sys.exit()
            raise e