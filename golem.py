import sys
import pickle
from os.path import exists as file_exists
from os import remove as remove_file

import pygame
import pygcurse
import numpy as np

import item
import creature
import world
import bodypart
from utils import mapwidth, mapheight, numlevels, fov

pygame.init()

logheight = 8
statuslines = 3
win = pygcurse.PygcurseWindow(mapwidth, mapheight + statuslines + logheight, 'Golem: A Self-Made Person')
win.font = pygame.font.Font('Hack-Regular.ttf', 12)
win.autoupdate = False

if file_exists('savegame.pickle'):
    with open('savegame.pickle', 'rb') as f:
        caves, player = pickle.load(f)
    cave_i = player.world_i
    cave = caves[cave_i]
    remove_file('savegame.pickle')
else:
    caves = []
    for i in range(numlevels):
        cave = world.World(mapwidth, mapheight)
        cave.rooms()
    
        for j in range(10):
            x = y = 0
            while cave.walls[x, y] != 0:
                x = np.random.randint(mapwidth)
                y = np.random.randint(mapheight)
            item.create_medication(cave.items, x, y)
    
        for j in range(5):
            x = y = 0
            while cave.walls[x, y] != 0:
                x = np.random.randint(mapwidth)
                y = np.random.randint(mapheight)
            item.randomweapon(cave.items, x, y)
    
        for j in range(5):
            x = y = 0
            while cave.walls[x, y] != 0:
                x = np.random.randint(mapwidth)
                y = np.random.randint(mapheight)
            item.randomarmor(cave.items, x, y)
    
        for j in range(5):
            x = y = 0
            while cave.walls[x, y] != 0:
                x = np.random.randint(mapwidth)
                y = np.random.randint(mapheight)
            cave.creatures.append(creature.Zombie(cave, i, x, y))
    
        for j in range(5):
            x = y = 0
            while cave.walls[x, y] != 0:
                x = np.random.randint(mapwidth)
                y = np.random.randint(mapheight)
            cave.creatures.append(creature.MolePerson(cave, i, x, y))
    
        if i > 0:
            for j in range(5):
                x = y = 0
                while cave.walls[x, y] != 0:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                cave.creatures.append(creature.CaveOctopus(cave, i, x, y))
    
        if i > 1:
            for j in range(5):
                x = y = 0
                while cave.walls[x, y] != 0:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                cave.creatures.append(creature.Goblin(cave, i, x, y))
    
        caves.append(cave)
    cave_i = 0
    cave = caves[cave_i]
    
    player = creature.Creature(cave, cave_i)
    player.torso = bodypart.HumanTorso(player.bodyparts, 0, 0)
    player.bodyparts[0].connect('left arm', bodypart.HumanArm(player.bodyparts, 0, 0))
    player.bodyparts[0].connect('right arm', bodypart.HumanArm(player.bodyparts, 0, 0))
    player.bodyparts[0].connect('left leg', bodypart.HumanLeg(player.bodyparts, 0, 0))
    player.bodyparts[0].connect('right leg', bodypart.HumanLeg(player.bodyparts, 0, 0))
    player.bodyparts[0].connect('heart', bodypart.HumanHeart(player.bodyparts, 0, 0))
    player.bodyparts[0].connect('head', bodypart.HumanHead(player.bodyparts, 0, 0))
    player.bodyparts[-1].connect('brain', bodypart.HumanBrain(player.bodyparts, 0, 0))
    player.bodyparts[-2].connect('left eye', bodypart.HumanEye(player.bodyparts, 0, 0))
    player.bodyparts[-3].connect('right eye', bodypart.HumanEye(player.bodyparts, 0, 0))
    item.Backpack(player.torso.worn['backpack'], 0, 0)
    player.faction = 'player'
    player.x = cave.stairsupcoords[0]
    player.y = cave.stairsupcoords[1]
    cave.creatures.append(player)
    
    player.log().append('Welcome to the cave!')
    player.log().append("Press 'h' for help.")

logback = 0 # How far the log has been scrolled
chosen = 0 # Used for different item choosing gamestates
target = None # Target of an attack

gamestate = 'free'

def draw():
    fovmap = fov(cave.walls, player.x, player.y, player.sight())
    # Background
    # win.setscreencolors(None, (0,0,0), clear=True)
    for i in range(mapwidth):
        for j in range(mapheight + statuslines + logheight):
            win.putchars(' ', x=i, y=j, bgcolor='black')  # For some reason the above commented line doesn't work on Windows, so have to do it this way instead.
        for j in range(mapheight):
            if fovmap[i,j]:
                if cave.walls[i,j] == 1:
                    win.putchars(' ', x=i, y=j, bgcolor='white')
                else:
                    win.putchars(' ', x=i, y=j, bgcolor=(64,64,64))
                player.seen()[cave_i][i,j] = 1
            elif player.seen()[cave_i][i,j] == 1:
                if cave.walls[i,j] == 1:
                    win.putchars(' ', x=i, y=j, bgcolor=(128,128,128))
    i, j = cave.stairsdowncoords
    if fovmap[i,j]:
        win.putchars('>', x=i, y=j, bgcolor=(64,64,64), fgcolor='white')
    elif player.seen()[cave_i][i,j] == 1:
        win.putchars('>', x=i, y=j, bgcolor='black', fgcolor=(128,128,128))
    i, j = cave.stairsupcoords
    if fovmap[i,j]:
        win.putchars('<', x=i, y=j, bgcolor=(64,64,64), fgcolor='white')
    elif player.seen()[cave_i][i,j] == 1:
        win.putchars('<', x=i, y=j, bgcolor='black', fgcolor=(128,128,128))

    # Items
    for it in cave.items:
        if fovmap[it.x, it.y]:
            win.putchars(it.char, x=it.x, y=it.y, 
                 bgcolor=(64,64,64), fgcolor=it.color)
        elif player.seen()[cave_i][it.x,it.y] == 1:
            win.putchars('?', x=it.x, y=it.y, 
                 bgcolor='black', fgcolor=(128,128,128))

    # Creatures
    for npc in [creature for creature in cave.creatures if creature.faction != 'player']:
        if fovmap[npc.x, npc.y]:
            win.putchars(npc.char, npc.x, npc.y, bgcolor=(64,64,64),
                         fgcolor=npc.color)
            if not npc in player.creaturesseen():
                player.creaturesseen().append(npc)
                player.log().append('You see a ' + npc.name +'.')
    win.putchars(player.char, x=player.x, y=player.y, 
                 bgcolor=(64,64,64), fgcolor=player.color)

    # Status
    for i in range(mapwidth):
        for j in range(statuslines):
            win.putchars(' ', x=i, y=mapheight+j, bgcolor=((128,128,128)))
    win.putchars('hp: ', x=0, y = mapheight, bgcolor=((128,128,128)), fgcolor = 'white')
    hptext = repr(int(sum([part.maxhp for part in player.bodyparts])/2-sum([part.damagetaken for part in player.bodyparts]))) + '/' + repr(int(sum([part.maxhp for part in player.bodyparts])/2))
    win.putchars(hptext, x=4, y=mapheight, bgcolor=((128,128,128)), fgcolor=(255, 0, 0))
    textx = len(hptext) + 5
    win.putchars('(', x=textx, y = mapheight, bgcolor=((128,128,128)), fgcolor = 'white')
    textx += 1
    textx_original = textx
    texty = mapheight
    for part in player.bodyparts:
        if player.dying():
            textcolor = (0, 0, 0)
        elif part.vital():
            textcolor = (255, 0, 0)
        elif part.destroyed():
            textcolor = (0, 0, 0)
        else:
            textcolor = (0, 255, 0)
        hptext = repr(part.maxhp - part.damagetaken) + '/' + repr(part.maxhp)
        if textx + len(hptext) > mapwidth:
            texty += 1
            textx = textx_original
        win.putchars(hptext, x=textx, y=texty, bgcolor=((128,128,128)), fgcolor=textcolor)
        textx += len(hptext) + 1
    win.putchars(')', x=textx-1, y = texty, bgcolor=((128,128,128)), fgcolor = 'white')
    statuseffects = []
    if player.overloaded():
        statuseffects.append(('Overloaded', (255, 0, 0)))
    elif player.burdened():
        statuseffects.append(('Burdened', (255, 255, 0)))
    bleed = False
    for part in player.bodyparts:
        if len(part.bleedclocks) > 0:
            bleed = True
    if bleed:
        statuseffects.append(('Bleeding', (255, 0, 0)))
    textx = 0
    for effect in statuseffects:
        win.putchars(effect[0], x=textx, y = mapheight+2, bgcolor=((128,128,128)), fgcolor = effect[1])
        textx += len(effect[0]) + 1

    # log
    if gamestate == 'free' or gamestate == 'dead':
        logrows = min(logheight,len(player.log()))
        for i in range(logrows):
            j = i-logrows-logback
            c = 255 + (max(j+1, -logheight))*128//logheight
            win.write(player.log()[j], x=0, y=mapheight+statuslines+i, fgcolor=(c,c,c))

    elif gamestate == 'mine':
        minemessage = 'Choose the direction to mine!'
        win.write(minemessage, x=0, y=mapheight+statuslines, fgcolor=(255,255,255))

    elif gamestate == 'pick':
        pickmessage = 'Choose the item to pick:'
        win.write(pickmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        picklist = [it for it in cave.items if it.x == player.x and it.y == player.y]
        logrows = min(logheight-1,len(picklist))
        for i in range(logrows):
            if len(picklist) <= logheight-1:
                j = i
            else:
                j = len(picklist)+i-logrows-logback
            if j != chosen:
                win.write(picklist[j].name, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write(picklist[j].name, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'drop':
        dropmessage = 'Choose the item to drop:'
        win.write(dropmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len(player.inventory))
        for i in range(logrows):
            if len(player.inventory) <= logheight-1:
                j = i
            else:
                j = len(player.inventory)+i-logrows-logback
            if j != chosen:
                win.write(player.inventory[j].name, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write(player.inventory[j].name, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'consume':
        consumemessage = 'Choose the item to consume:'
        win.write(consumemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len([item for item in player.inventory if item.consumable]))
        for i in range(logrows):
            if len([item for item in player.inventory if item.consumable]) <= logheight-1:
                j = i
            else:
                j = len([item for item in player.inventory if item.consumable])+i-logrows-logback
            if j != chosen:
                win.write([item for item in player.inventory if item.consumable][j].name, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write([item for item in player.inventory if item.consumable][j].name, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'wieldchooseitem':
        wieldmessage = 'Choose the item to wield:'
        win.write(wieldmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len([item for item in player.inventory if item.wieldable]))
        for i in range(logrows):
            if len([item for item in player.inventory if item.wieldable]) <= logheight-1:
                j = i
            else:
                j = len([item for item in player.inventory if item.wieldable])+i-logrows-logback
            if j != chosen:
                win.write([item for item in player.inventory if item.wieldable][j].name, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write([item for item in player.inventory if item.wieldable][j].name, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'wieldchoosebodypart':
        wieldmessage = 'Choose where to wield the ' + selecteditem.name + ':'
        win.write(wieldmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()]))
        for i in range(logrows):
            if len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()]) <= logheight-1:
                j = i
            else:
                j = len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()])+i-logrows-logback
            if j != chosen:
                win.write([part.wearwieldname() for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()][j], x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write([part.wearwieldname() for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()][j], x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'unwield':
        wieldmessage = 'Choose the item to unwield:'
        win.write(wieldmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]))
        for i in range(logrows):
            if len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) <= logheight-1:
                j = i
            else:
                j = len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0])+i-logrows-logback
            if j != chosen:
                win.write([part.wielded[0].name + ' in the ' + part.wearwieldname() for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0][j], x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write([part.wielded[0].name + ' in the ' + part.wearwieldname() for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0][j], x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'wearchooseitem':
        wearmessage = 'Choose the item to wear:'
        win.write(wearmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len([item for item in player.inventory if item.wearable]))
        for i in range(logrows):
            if len([item for item in player.inventory if item.wearable]) <= logheight-1:
                j = i
            else:
                j = len([item for item in player.inventory if item.wearable])+i-logrows-logback
            if j != chosen:
                win.write([item for item in player.inventory if item.wearable][j].name, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write([item for item in player.inventory if item.wearable][j].name, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'wearchoosebodypart':
        wearmessage = 'Choose where to wear the ' + selecteditem.name + ':'
        win.write(wearmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len(partlist))
        for i in range(logrows):
            if len(partlist) <= logheight-1:
                j = i
            else:
                j = len(partlist)+i-logrows-logback
            if j != chosen:
                win.write(partlist[j].wearwieldname(), x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write(partlist[j].wearwieldname(), x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'undress':
        choosemessage = 'Choose the item to take off:'
        win.write(choosemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len(wornlist))
        for i in range(logrows):
            if len(wornlist) <= logheight-1:
                j = i
            else:
                j = len(wornlist)+i-logrows-logback
            if j != chosen:
                win.write(wornlist[j].name + ' on the ' + wornlist[j].owner.owner.wearwieldname(), x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write(wornlist[j].name + ' on the ' + wornlist[j].owner.owner.wearwieldname(), x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'chooseattack':
        attackmessage = 'Choose how to attack the ' + target.name + ':'
        win.write(attackmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len(player.attackslist()))
        for i in range(logrows):
            if len(player.attackslist()) <= logheight-1:
                j = i
            else:
                j = len(player.attackslist())+i-logrows-logback
            attackdescription = player.attackslist()[j].name + ' (' + repr(int(player.attackslist()[j].hitprobability * 100)) + '%, ' + repr(player.attackslist()[j].mindamage) + '-' + repr(player.attackslist()[j].maxdamage)
            for special in player.attackslist()[j].special:
                if special[0] == 'bleed':
                    attackdescription += ', bleed ' + repr(int(special[1] * 100)) + '%'
            attackdescription += ')'
            if j != chosen:
                win.write(attackdescription, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write(attackdescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'choosetargetbodypart':
        attackmessage = 'Choose where to attack the ' + target.name + ':'
        win.write(attackmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len([part for part in target.bodyparts if not part.destroyed()]))
        for i in range(logrows):
            if len([part for part in target.bodyparts if not part.destroyed()]) <= logheight-1:
                j = i
            else:
                j = len([part for part in target.bodyparts if not part.destroyed()])+i-logrows-logback
            targetbodypart = [part for part in target.bodyparts if not part.destroyed()][j]
            if targetbodypart.parentalconnection != None:
                partname = list(targetbodypart.parentalconnection.parent.childconnections.keys())[list(targetbodypart.parentalconnection.parent.childconnections.values()).index(targetbodypart.parentalconnection)]
            elif targetbodypart == target.torso:
                partname = 'torso'
            if j != chosen:
                win.write(partname, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write(partname, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'choosetorso':
        choosemessage = 'Choose your torso:'
        win.write(choosemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        torsolist = [part for part in player.bodyparts if 'torso' in part.categories and not part.destroyed()] + [it for it in player.inventory if it.bodypart and 'torso' in it.categories and not it.destroyed()]
        logrows = min(logheight-1,len(torsolist))
        for i in range(logrows):
            if len(torsolist) <= logheight-1:
                j = i
            else:
                j = len(torsolist)+i-logrows-logback
            if j != chosen:
                win.write(torsolist[j].name + ' (hp: ' + repr(torsolist[j].hp()) + '/' + repr(torsolist[j].maxhp) + ')', x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write(torsolist[j].name + ' (hp: ' + repr(torsolist[j].hp()) + '/' + repr(torsolist[j].maxhp) + ')', x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    elif gamestate == 'choosebodypart':
        choosemessage = 'Choose your ' + connectionname + ':'
        win.write(choosemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
        logrows = min(logheight-1,len(partslist))
        if logrows == 0:
            win.write('No suitable options for a vital bodypart. Press ESC to cancel the body building process', x=0, y=mapheight+statuslines+1, fgcolor=(255,255,255))
        for i in range(logrows):
            if len(partslist) <= logheight-1:
                j = i
            else:
                j = len(partslist)+i-logrows-logback
            if partslist[j] == None:
                partdescription = 'none'
            else:
                partdescription = partslist[j].name + ' (hp: ' + repr(partslist[j].hp()) + '/' + repr(partslist[j].maxhp) + ')'
            if j != chosen:
                win.write(partdescription, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
            if j == chosen:
                win.write(partdescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

    win.update()

def updatetime(time):
    player.bleed(time)
    for npc in [creature for creature in cave.creatures if creature.faction != 'player']:
        npc.update(time)

def checkitems(x,y):
    for it in cave.items:
        if it.x == x and it.y == y:
            player.log().append('There is a ' + it.name + ' here.')

def moveorattack(dx, dy):
    targets = [creature for creature in cave.creatures if creature.x == player.x+dx and creature.y == player.y+dy]
    if len(targets) > 0:
        target = targets[0]
        gamestate = 'chooseattack'
        logback = len(player.attackslist()) - logheight + 1
    elif player.overloaded():
        player.log().append('You are too overloaded to move!')
        logback = 0
        gamestate = 'free'
        target = None
    elif cave.walls[player.x+dx, player.y+dy]:
        player.log().append("There's a wall in your way.")
        logback = 0
        gamestate = 'free'
        target = None
    else:
        updatetime(np.sqrt(dx**2 + dy**2) * player.steptime())
        if not player.dying():
            creaturesintheway = [creature for creature in cave.creatures if creature.x == player.x+dx and creature.y == player.y+dy]
            if len(creaturesintheway) == 0:
                player.move(dx, dy)
                player.previousaction = 'move'
                checkitems(player.x,player.y)
            else:
                player.log().append("There's a " + creaturesintheway[0].name + " in your way.")
                player.previousaction = 'wait'
        logback = 0
        gamestate = 'free'
        target = None
    chosen = 0
    return(gamestate, logback, target, chosen)

def mine(dx, dy):
    if player.x+dx == 0 or player.x+dx == mapwidth-1 or player.y+dy == 0 or player.y+dy == mapheight-1:
        player.log().append('That is too hard for you to mine.')
    elif cave.walls[player.x+dx, player.y+dy] == 1:
        updatetime(player.minetime())
        if not player.dying():
            player.log().append('You mined a hole in the wall.')
            cave.walls[player.x+dx, player.y+dy] = 0
            player.previousaction = 'mine'
    else:
        player.log().append("There's no wall there.")
    return('free', 0)  # gamestate and logback



draw()
while True:
    for event in pygame.event.get():
        #try:
            if event.type == pygame.locals.KEYDOWN:
                if gamestate == 'free':
                    # Player movements
                    if event.key == pygame.locals.K_UP or event.key == pygame.locals.K_KP8:
                        gamestate, logback, target, chosen = moveorattack(0, -1)
                    if event.key == pygame.locals.K_DOWN or event.key == pygame.locals.K_KP2:
                        gamestate, logback, target, chosen = moveorattack(0, 1)
                    if event.key == pygame.locals.K_LEFT or event.key == pygame.locals.K_KP4:
                        gamestate, logback, target, chosen = moveorattack(-1, 0)
                    if event.key == pygame.locals.K_RIGHT or event.key == pygame.locals.K_KP6:
                        gamestate, logback, target, chosen = moveorattack(1, 0)
                    if event.key == pygame.locals.K_KP7:
                        gamestate, logback, target, chosen = moveorattack(-1, -1)
                    if event.key == pygame.locals.K_KP9:
                        gamestate, logback, target, chosen = moveorattack(1, -1)
                    if event.key == pygame.locals.K_KP1:
                        gamestate, logback, target, chosen = moveorattack(-1, 1)
                    if event.key == pygame.locals.K_KP3:
                        gamestate, logback, target, chosen = moveorattack(1, 1)

                    if event.key == pygame.locals.K_PERIOD or event.key == pygame.locals.K_KP5:
                        updatetime(1)
                        logback = 0
                        player.previousaction = 'wait'

                    if event.key == pygame.locals.K_GREATER or (event.key == pygame.locals.K_LESS and (event.mod & pygame.KMOD_SHIFT)):
                        if (player.x, player.y) != cave.stairsdowncoords:
                            player.log().append("You can't go down here!")
                            logback = 0
                        else:
                            if cave_i == numlevels - 1:
                                player.log().append("Lower levels not yet implemented!")
                                logback = 0
                            else:
                                cave_i += 1
                                cave.creatures.remove(player)
                                cave = caves[cave_i]
                                cave.creatures.append(player)
                                player.world = cave
                                player.world_i = cave_i
                                player.x = cave.stairsupcoords[0]
                                player.y = cave.stairsupcoords[1]
                                player.log().append('You went down the stairs.')
                                player.previousaction = 'move'
                                logback = 0

                    if event.key == pygame.locals.K_LESS and not (event.mod & pygame.KMOD_SHIFT):
                        if (player.x, player.y) != cave.stairsupcoords:
                            player.log().append("You can't go up here!")
                            logback = 0
                        else:
                            if cave_i == 0:
                                player.log().append("Overworld not yet implemented!")
                                logback = 0
                            else:
                                cave_i -= 1
                                cave.creatures.remove(player)
                                cave = caves[cave_i]
                                cave.creatures.append(player)
                                player.world = cave
                                player.world_i = cave_i
                                player.x = cave.stairsdowncoords[0]
                                player.y = cave.stairsdowncoords[1]
                                player.log().append('You went up the stairs.')
                                player.previousaction = 'move'
                                logback = 0

                    if event.key == pygame.locals.K_m:
                        if player.minespeed() > 0:
                            gamestate = 'mine'
                        else:
                            player.log().append('You lack the tools or appendages to mine.')
                            logback = 0

                    # Items
                    if event.key == pygame.locals.K_COMMA:
                        picklist = [it for it in cave.items if it.x == player.x and it.y == player.y]
                        if len(picklist) == 0:
                            player.log().append('Nothing to pick up here.')
                            logback = 0
                        elif len(picklist) == 1:
                            updatetime(0.5)
                            if not player.dying():
                                it = picklist[0]
                                cave.items.remove(it)
                                player.inventory.append(it)
                                it.owner = player.inventory
                                player.log().append('You pick up the ' + it.name + '.')
                                player.previousaction = 'pick'
                                logback = 0
                        else:
                            gamestate = 'pick'
                            logback = len(picklist) - logheight + 1
                            chosen = 0
                    if event.key == pygame.locals.K_d:
                        if len(player.inventory) > 0:
                            gamestate = 'drop'
                            logback = len(player.inventory) - logheight + 1
                            chosen = 0
                        else:
                            player.log().append('You have nothing to drop!')
                    if event.key == pygame.locals.K_i:
                        player.log().append('Items carried:')
                        if len(player.inventory) == 0:
                            player.log().append('  - nothing')
                        else:
                            for it in player.inventory:
                                if it.maxhp < np.inf:
                                    player.log().append('  - a ' + it.name + ' (wt: ' + repr(it.weight) + ' g,' + ' hp: ' + repr(it.hp()) + '/' + repr(it.maxhp) + ')')
                                else:
                                    player.log().append('  - a ' + it.name + ' (wt: ' + repr(it.weight) + ' g)')
                        player.log().append('Items wielded:')
                        wieldlist = [part.wielded[0] for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]
                        if len(wieldlist) == 0:
                            player.log().append('  - nothing')
                        else:
                            for it in wieldlist:
                                if it.maxhp < np.inf:
                                    player.log().append('  - a ' + it.name + ' (wt: ' + repr(it.weight) + ' g,' + ' hp: ' + repr(it.hp()) + '/' + repr(it.maxhp) + ')')
                                else:
                                    player.log().append('  - a ' + it.name + ' (wt: ' + repr(it.weight) + ' g)')
                        player.log().append('Items worn:')
                        wornlist = [it[0] for part in player.bodyparts for it in part.worn.values() if len(it) > 0]
                        if len(wornlist) == 0:
                            player.log().append('  - nothing')
                        else:
                            for it in wornlist:
                                if it.maxhp < np.inf:
                                    player.log().append('  - a ' + it.name + ' (wt: ' + repr(it.weight) + ' g,' + ' hp: ' + repr(it.hp()) + '/' + repr(it.maxhp) + ')')
                                else:
                                    player.log().append('  - a ' + it.name + ' (wt: ' + repr(it.weight) + ' g)')
                        if max(1, len(player.inventory)) + max(1, len(wieldlist)) + max(1, len(wornlist)) + 3 > logheight and len(player.log()) > 1:
                            logback = max(1, len(player.inventory)) + max(1, len(wieldlist)) + max(1, len(wornlist)) + 3 - logheight
                        else:
                            logback = 0
                    if event.key == pygame.locals.K_c:
                        if len([item for item in player.inventory if item.consumable]) > 0:
                            gamestate = 'consume'
                            logback = len([item for item in player.inventory if item.consumable]) - logheight + 1
                            chosen = 0
                        else:
                            player.log().append("You don't have anything to consume.")
                            logback = 0
                    if event.key == pygame.locals.K_w and not (event.mod & pygame.KMOD_SHIFT):
                        if len([item for item in player.inventory if item.wieldable]) > 0 and len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0]) > 0:
                            gamestate = 'wieldchooseitem'
                            logback = len([item for item in player.inventory if item.wieldable]) - logheight + 1
                            chosen = 0
                        else:
                            player.log().append("You cannot wield anything.")
                            logback = 0
                    if event.key == pygame.locals.K_w and (event.mod & pygame.KMOD_SHIFT):
                        if len([item for item in player.inventory if item.wearable]) > 0:
                            gamestate = 'wearchooseitem'
                            logback = len([item for item in player.inventory if item.wearable]) - logheight + 1
                            chosen = 0
                        else:
                            player.log().append('You have nothing to wear.')
                            logback = 0
                    if event.key == pygame.locals.K_u and not (event.mod & pygame.KMOD_SHIFT):
                        if len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) > 0:
                            gamestate = 'unwield'
                            logback = len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) - logheight + 1
                            chosen = 0
                        else:
                            player.log().append("You have nothing to unwield.")
                            logback = 0
                    if event.key == pygame.locals.K_u and (event.mod & pygame.KMOD_SHIFT):
                        wornlist = [it[0] for part in player.bodyparts for it in part.worn.values() if len(it) > 0]
                        if len(wornlist) > 0:
                            gamestate = 'undress'
                            logback = len(wornlist) - logheight + 1
                            chosen = 0
                        else:
                            player.log().append("You have nothing to undress.")
                            logback = 0

                    # Bodyparts:
                    if event.key == pygame.locals.K_b and not (event.mod & pygame.KMOD_SHIFT):
                        player.log().append('The parts of your body:')
                        for part in player.bodyparts:
                            player.log().append('  - a ' + part.name + ' (hp: ' + repr(part.hp()) + '/' + repr(part.maxhp) + ')')
                        if len(player.bodyparts) > logheight - 1 and len(player.log()) > 1:
                            logback = len(player.bodyparts) - logheight + 1
                        else:
                            logback = 0

                    if event.key == pygame.locals.K_b and (event.mod & pygame.KMOD_SHIFT):
                        gamestate = 'choosetorso'
                        len([part for part in player.bodyparts if 'torso' in part.categories and not part.destroyed()] + [it for it in player.inventory if it.bodypart and 'torso' in it.categories and not it.destroyed()]) - logheight + 1
                        chosen = 0

                    # Help
                    if event.key == pygame.locals.K_h:
                        player.log().append('Commands:')
                        player.log().append('  - page up, page down, home, end: explore the log')
                        player.log().append('  - arrows or numpad: move')
                        player.log().append('  - period or numpad 5: wait a moment')
                        player.log().append('  - < or >: go up or down')
                        player.log().append('  - m: mine')
                        player.log().append('  - comma: pick up an item')
                        player.log().append('  - d: drop an item')
                        player.log().append('  - i: check your inventory')
                        player.log().append('  - b: list your body parts')
                        player.log().append('  - B: choose your body parts')
                        player.log().append('  - c: take some medication')
                        player.log().append('  - w: wield an item')
                        player.log().append('  - u: unwield an item')
                        player.log().append('  - W: wear an item')
                        player.log().append('  - U: undress an item')
                        player.log().append('  - h: this list of commands')
                        if len(player.log()) > 1: # Prevent crash if the player is brainless
                            logback = 9 # Increase when adding commands
                    
                    # player.log() scrolling
                    if event.key == pygame.locals.K_PAGEUP:
                        if len(player.log()) >= logheight:
                            logback = min(logback+1, len(player.log())-logheight)
                    if event.key == pygame.locals.K_PAGEDOWN:
                        logback = max(logback-1, 0)
                    if event.key == pygame.locals.K_HOME:
                        if len(player.log()) >= logheight:
                            logback = len(player.log())-logheight
                    if event.key == pygame.locals.K_END:
                        logback = 0
                        
                elif gamestate == 'mine':
                    if event.key == pygame.locals.K_UP or event.key == pygame.locals.K_KP8:
                        gamestate, logback = mine(0, -1)
                    if event.key == pygame.locals.K_DOWN or event.key == pygame.locals.K_KP2:
                        gamestate, logback = mine(0, 1)
                    if event.key == pygame.locals.K_LEFT or event.key == pygame.locals.K_KP4:
                        gamestate, logback = mine(-1, 0)
                    if event.key == pygame.locals.K_RIGHT or event.key == pygame.locals.K_KP6:
                        gamestate, logback = mine(1, 0)
                    if event.key == pygame.locals.K_KP7:
                        gamestate, logback = mine(-1, -1)
                    if event.key == pygame.locals.K_KP9:
                        gamestate, logback = mine(1, -1)
                    if event.key == pygame.locals.K_KP1:
                        gamestate, logback = mine(-1, 1)
                    if event.key == pygame.locals.K_KP3:
                        gamestate, logback = mine(1, 1)
                
                elif gamestate == 'pick':
                    picklist = [it for it in cave.items if it.x == player.x and it.y == player.y]
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len(picklist) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len(picklist)-1, chosen+1)
                        if chosen == len(picklist) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        updatetime(0.5)
                        if not player.dying():
                            selected = picklist[chosen]
                            selected.owner = player.inventory
                            player.inventory.append(selected)
                            cave.items.remove(selected)
                            player.log().append('You picked up the ' + selected.name + '.')
                            player.previousaction = 'pick'
                            logback = 0
                        gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'
                
                elif gamestate == 'drop':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len(player.inventory) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len(player.inventory)-1, chosen+1)
                        if chosen == len(player.inventory) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        updatetime(0.5)
                        if not player.dying():
                            selected = player.inventory[chosen]
                            selected.owner = cave.items
                            cave.items.append(selected)
                            player.inventory.remove(selected)
                            selected.x = player.x
                            selected.y = player.y
                            player.log().append('You dropped the ' + selected.name + '.')
                            player.previousaction = 'drop'
                            logback = 0
                        gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'
                
                elif gamestate == 'consume':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len([item for item in player.inventory if item.consumable]) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len([item for item in player.inventory if item.consumable])-1, chosen+1)
                        if chosen == len([item for item in player.inventory if item.consumable]) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        updatetime(1)
                        if not player.dying():
                            selected = [item for item in player.inventory if item.consumable][chosen]
                            part, healed = selected.consume(player)
                            if part.parentalconnection != None:
                                partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
                            elif part == player.torso:
                                partname = 'torso'
                            player.log().append('You consumed a ' + selected.name + ', healing your ' + partname + ' ' + repr(healed) + ' points.')
                            player.previousaction = 'consume'
                            logback = 0
                        gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'wieldchooseitem':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len([item for item in player.inventory if item.wieldable]) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len([item for item in player.inventory if item.wieldable])-1, chosen+1)
                        if chosen == len([item for item in player.inventory if item.wieldable]) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        selecteditem = [item for item in player.inventory if item.wieldable][chosen]
                        logback = len([part for part in player.bodyparts if part.capableofwielding]) - logheight + 1
                        gamestate = 'wieldchoosebodypart'
                        chosen = 0
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'wieldchoosebodypart':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()]) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()])-1, chosen+1)
                        if chosen == len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()]) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        updatetime(1)
                        if not player.dying():
                            selected = [part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()][chosen]
                            player.inventory.remove(selecteditem)
                            selected.wielded.append(selecteditem)
                            selecteditem.owner = selected.wielded
                            player.log().append('You are now wielding the ' + selecteditem.name + ' in your ' + selected.wearwieldname() + '.')
                            player.previousaction = 'wield'
                            logback = 0
                        gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'unwield':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0])-1, chosen+1)
                        if chosen == len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        updatetime(1)
                        if not player.dying():
                            part = [part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0][chosen]
                            selected = part.wielded[0]
                            part.wielded.remove(selected)
                            player.inventory.append(selected)
                            selected.owner = player.inventory
                            player.log().append('You removed the ' + selected.name + ' from your ' + part.wearwieldname() + '.')
                            player.previousaction = 'unwield'
                            logback = 0
                        gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'wearchooseitem':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len([item for item in player.inventory if item.wearable]) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len([item for item in player.inventory if item.wearable])-1, chosen+1)
                        if chosen == len([item for item in player.inventory if item.wearable]) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        selecteditem = [item for item in player.inventory if item.wearable][chosen]
                        partlist = [part for part in player.bodyparts if selecteditem.wearcategory in part.worn.keys() and len(part.worn[selecteditem.wearcategory]) == 0 and not part.destroyed()]
                        if len(partlist) > 0:
                            logback = len(partlist) - logheight + 1
                            gamestate = 'wearchoosebodypart'
                            chosen = 0
                        else:
                            player.log().append('You have no suitable free body part for wearing that.')
                            logback = 0
                            gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'wearchoosebodypart':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len(partlist) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len(partlist)-1, chosen+1)
                        if chosen == len(partlist) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        updatetime(1)
                        if not player.dying():
                            selected = partlist[chosen]
                            player.inventory.remove(selecteditem)
                            selected.worn[selecteditem.wearcategory].append(selecteditem)
                            selecteditem.owner = selected.worn[selecteditem.wearcategory]
                            player.log().append('You are now wearing the ' + selecteditem.name + ' on your ' + selected.wearwieldname() + '.')
                            player.previousaction = 'wear'
                            logback = 0
                        gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'undress':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len(wornlist) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len(wornlist)-1, chosen+1)
                        if chosen == len(wornlist) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        updatetime(1)
                        if not player.dying():
                            selected = wornlist[chosen]
                            partname = selected.owner.owner.wearwieldname()
                            selected.owner.remove(selected)
                            player.inventory.append(selected)
                            selected.owner = player.inventory
                            player.log().append('You removed the ' + selected.name + ' from your ' + partname + '.')
                            player.previousaction = 'undress'
                            logback = 0
                        gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'chooseattack':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len(player.attackslist()) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len(player.attackslist())-1, chosen+1)
                        if chosen == len(player.attackslist()) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        selectedattack = player.attackslist()[chosen]
                        gamestate = 'choosetargetbodypart'
                        logback = len([part for part in target.bodyparts if not part.destroyed()]) - logheight + 1
                        chosen = 0
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'choosetargetbodypart':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len([part for part in target.bodyparts if not part.destroyed()]) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len([part for part in target.bodyparts if not part.destroyed()])-1, chosen+1)
                        if chosen == len([part for part in target.bodyparts if not part.destroyed()]) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        selected = [part for part in target.bodyparts if not part.destroyed()][chosen]
                        updatetime(selectedattack[6])
                        if not player.dying():
                            if not target.dead:
                                player.fight(target, selected, selectedattack)
                                player.previousaction = 'fight'
                            else:
                                player.log().append('The ' + target.name + ' is already dead.')
                                player.previousaction = 'wait'
                        logback = 0
                        gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'choosetorso':
                    torsolist = [part for part in player.bodyparts if 'torso' in part.categories and not part.destroyed()] + [it for it in player.inventory if it.bodypart and 'torso' in it.categories and not it.destroyed()]
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len(torsolist) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len(torsolist)-1, chosen+1)
                        if chosen == len(torsolist) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        selected = torsolist[chosen]
                        bodypartcandidates = [selected]
                        connectioncandidates = []
                        connectionname = list(selected.childconnections.keys())[0]
                        connection = selected.childconnections[connectionname]
                        partslist = [part for part in player.bodyparts if np.any([category in part.categories for category in connection.categories]) and not part.destroyed() and not part in bodypartcandidates] + [it for it in player.inventory if it.bodypart and np.any([category in it.categories for category in connection.categories]) and not it.destroyed() and not it in bodypartcandidates]
                        if not connection.vital:
                            partslist.append(None)
                        gamestate = 'choosebodypart'
                        logback = len(partslist) - logheight + 1
                        chosen = 0
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                elif gamestate == 'choosebodypart':
                    if event.key == pygame.locals.K_UP:
                        chosen = max(0, chosen-1)
                        if chosen == len(partslist) - logback - (logheight - 1) - 1:
                            logback += 1
                    if event.key == pygame.locals.K_DOWN:
                        chosen = min(len(partslist)-1, chosen+1)
                        if chosen == len(partslist) - logback:
                            logback -= 1
                    if event.key == pygame.locals.K_RETURN:
                        selected = partslist[chosen]
                        if selected != None:
                            bodypartcandidates.append(selected)
                        connectioncandidates.append((connection, selected))
                        connectionlist = [connection for part in bodypartcandidates for connection in [(name, part.childconnections[name]) for name in list(part.childconnections.keys())] if not connection[1] in [cn[0] for cn in connectioncandidates]]
                        if len(connectionlist) > 0:
                            connectionname = connectionlist[0][0]
                            connection = connectionlist[0][1]
                            partslist = [part for part in player.bodyparts if np.any([category in part.categories for category in connection.categories]) and not part.destroyed() and not part in bodypartcandidates] + [it for it in player.inventory if it.bodypart and np.any([category in it.categories for category in connection.categories]) and not it.destroyed() and not it in bodypartcandidates]
                            if not connection.vital:
                                partslist.append(None)
                            gamestate = 'choosebodypart'
                            logback = len(partslist) - logheight + 1
                            chosen = 0
                        else:
                            updatetime(5)
                            if not player.dying():
                                for it in [it[0] for part in player.bodyparts for it in part.worn.values() if len(it) > 0]:
                                    it.owner.remove(it)
                                    player.inventory.append(it)
                                    it.owner = player.inventory
                                for part in player.bodyparts:
                                    if not part.destroyed():
                                        part.owner = player.inventory
                                        player.inventory.append(part)
                                    part.parentalconnection = None
                                    for con in part.childconnections:
                                        part.childconnections[con].child = None
                                    if part.capableofwielding:
                                        for it in part.wielded:
                                            it.owner = player.inventory
                                            player.inventory.append(it)
                                            part.wielded.remove(it)
                                player.bodyparts = bodypartcandidates
                                player.torso = player.bodyparts[0]
                                for part in player.bodyparts:
                                    player.inventory.remove(part)
                                    part.owner = player.bodyparts
                                for connection, part in connectioncandidates:
                                    if part != None:
                                        connection.connect(part)
                                player.log().append('You have selected your bodyparts.')
                                player.previousaction = 'choosebody'
                                logback = 0
                                gamestate = 'free'
                    if event.key == pygame.locals.K_ESCAPE:
                        logback = 0
                        gamestate = 'free'

                if player.dying():
                    gamestate = 'dead'
                
                # Update window after any command or keypress
                draw()
            if event.type == pygame.QUIT:
                if gamestate != 'dead':
                    with open('savegame.pickle', 'wb') as f:
                        pickle.dump((caves, player), f)
                pygame.quit()
                sys.exit()
                
        
        # Make sure the window is closed if the game crashes
        #except Exception as e:
        #    pygame.quit()
        #    sys.exit()
        #    raise e