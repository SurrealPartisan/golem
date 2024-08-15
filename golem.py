import sys
import dill as pickle
from os.path import exists as file_exists
from os import remove as remove_file

import pygame
import pygcurse
import numpy as np

import item
import creature
import world
import bodypart
import god
from utils import mapwidth, mapheight, numlevels, fov, sins, keynames, numkeys, drugname, infusionname, bodypartshortnames, listwithowner

pygame.init()

logheight = 8
statuslines = 3
hpbarwidth = 10
hpmargin = 1
icon = pygame.image.load('icon.png')
pygame.display.set_icon(icon)
win = pygcurse.PygcurseWindow(mapwidth + hpbarwidth + hpmargin, mapheight + statuslines + logheight, 'Golem: A Self-Made Person!')
if file_exists('options.pickle'):
    with open('options.pickle', 'rb') as f:
        font, fontsize, showsequentially = pickle.load(f)
else:
    font, fontsize, showsequentially = ('courier-prime-sans.regular.ttf', 12, False)
win.font = pygame.font.Font(font, fontsize)
win.autoupdate = False

keybindings_default = {'move north': ((pygame.locals.K_UP, False, False), (pygame.locals.K_KP8, False, True)),  # Key, shift, editable
                       'move south': ((pygame.locals.K_DOWN, False, False), (pygame.locals.K_KP2, False, True)),
                       'move west': ((pygame.locals.K_LEFT, False, False), (pygame.locals.K_KP4, False, True)),
                       'move east': ((pygame.locals.K_RIGHT, False, False), (pygame.locals.K_KP6, False, True)),
                       'move northwest': ((None, False, True), (pygame.locals.K_KP7, False, True)),
                       'move northeast': ((None, False, True), (pygame.locals.K_KP9, False, True)),
                       'move southwest': ((None, False, True), (pygame.locals.K_KP1, False, True)),
                       'move southeast': ((None, False, True), (pygame.locals.K_KP3, False, True)),
                       'wait': ((pygame.locals.K_PERIOD, False, True), (pygame.locals.K_KP5, False, True)),
                       'repeat last attack': ((pygame.locals.K_r, False, True), (None, False, True)),
                       'repeat second last attack': ((pygame.locals.K_r, True, True), (None, False, True)),
                       'look': ((pygame.locals.K_l, False, True), (None, False, True)),
                       'go down': ((pygame.locals.K_GREATER, False, True), (pygame.locals.K_LESS, True, True)),
                       'go up': ((pygame.locals.K_LESS, False, True), (None, False, True)),
                       'mine': ((pygame.locals.K_m, False, True), (None, False, True)),
                       'pick up': ((pygame.locals.K_COMMA, False, True), (None, False, True)),
                       'drop': ((pygame.locals.K_d, False, True), (None, False, True)),
                       'throw': ((pygame.locals.K_t, False, True), (None, False, True)),
                       'inventory': ((pygame.locals.K_i, False, True), (None, False, True)),
                       'information': ((pygame.locals.K_i, True, True), (None, False, True)),
                       'consume': ((pygame.locals.K_c, False, True), (None, False, True)),
                       'cook': ((pygame.locals.K_c, True, True), (None, False, True)),
                       'wield': ((pygame.locals.K_w, False, True), (None, False, True)),
                       'wear': ((pygame.locals.K_w, True, True), (None, False, True)),
                       'unwield': ((pygame.locals.K_u, False, True), (None, False, True)),
                       'undress': ((pygame.locals.K_u, True, True), (None, False, True)),
                       'choose stance': ((pygame.locals.K_s, False, True), (None, False, True)),
                       'pray': ((pygame.locals.K_p, False, True), (None, False, True)),
                       'frighten': ((pygame.locals.K_f, False, True), (None, False, True)),
                       'list bodyparts': ((pygame.locals.K_b, False, True), (None, False, True)),
                       'choose bodyparts': ((pygame.locals.K_b, True, True), (None, False, True)),
                       'help': ((pygame.locals.K_h, False, True), (None, False, True)),
                       'log up': ((pygame.locals.K_PAGEUP, False, True), (None, False, True)),
                       'log down': ((pygame.locals.K_PAGEDOWN, False, True), (None, False, True)),
                       'log start': ((pygame.locals.K_HOME, False, True), (None, False, True)),
                       'log end': ((pygame.locals.K_END, False, True), (None, False, True)),
                       'list up': ((pygame.locals.K_UP, False, False), (None, False, True)),
                       'list down': ((pygame.locals.K_DOWN, False, False), (None, False, True)),
                       'list select': ((pygame.locals.K_RETURN, False, False), (None, False, True)),
                       'escape': ((pygame.locals.K_ESCAPE, False, False), (None, False, True)),
                       }
reservedkeys = [pygame.locals.K_UP, pygame.locals.K_DOWN, pygame.locals.K_LEFT, pygame.locals.K_RIGHT, pygame.locals.K_RETURN, pygame.locals.K_ESCAPE, pygame.locals.K_LSHIFT]

if file_exists('keybindings.pickle'):
    with open('keybindings.pickle', 'rb') as f:
        keybindings = pickle.load(f)
else:
    keybindings = {}
for command in keybindings_default:
    if not command in keybindings:
        keybindings[command] = keybindings_default[command]

def game():
    if file_exists('savegame.pickle'):
        with open('savegame.pickle', 'rb') as f:
            caves, player, gods = pickle.load(f)
        cave_i = player.world_i
        cave = caves[cave_i]
        remove_file('savegame.pickle')
    else:
        gods = []
        for sin in sins:
            gods.append(god.God(None, np.nan, sin))
        curetypes = []
        medicinenames = []
        while len(np.unique(medicinenames)) != 13:
            medicinenames = []
            for i in range(13):
                medicinenames.append(drugname())
        drugtypes = []
        for i in range(13):
            ct = item.CureType('living flesh', medicinenames[i], i-2, np.random.choice([1, 5, 10, 25, 50]))
            curetypes.append(ct)
            drugtypes.append(ct)
        infusionnames = []
        while len(np.unique(infusionnames)) != 13:
            infusionnames = []
            for i in range(13):
                infusionnames.append(infusionname())
        infusiontypes = []
        for i in range(13):
            ct = item.CureType('undead flesh', infusionnames[i], i-2, np.random.randint(1,500))
            curetypes.append(ct)
            infusiontypes.append(ct)
        caves = []
        for i in range(numlevels):
            cave = world.World(mapwidth, mapheight)
            cave.rooms()
            cave.curetypes = curetypes
            altarcoords = []
            for j in range(np.random.randint(4)):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or (x, y) == cave.stairsdowncoords or (x, y) == cave.stairsupcoords:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                altarcoords.append((x, y))
                cave.altars.append(world.Altar(x, y, np.random.choice(gods)))

            for j in range(np.random.randint(41)):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.largerocks[x, y] != 0 or (x, y) == cave.stairsdowncoords or (x, y) == cave.stairsupcoords or (x, y) in altarcoords:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                cave.largerocks[x, y] = 1

            for j in range(np.random.randint(4)):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.largerocks[x, y] != 0 or cave.spiderwebs[x, y] != 0 or cave.campfires[x, y] != 0 or (x, y) == cave.stairsdowncoords or (x, y) == cave.stairsupcoords or (x, y) in altarcoords:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                cave.campfires[x, y] = 1

            caltropscoords = []
            for j in range(np.random.randint(11)):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.campfires[x, y] != 0 or (x, y) in caltropscoords:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                caltropscoords.append((x, y))
                item.randomcaltrops(cave.items, x, y, i)

            pebblescoords = []
            for j in range(np.random.randint(11)):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.campfires[x, y] != 0 or (x, y) in caltropscoords or (x, y) in pebblescoords:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                pebblescoords.append((x, y))
                item.LooseRoundPebbles(cave.items, x, y)

            for j in range(10):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.campfires[x, y] != 0:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                item.Cure(cave.items, x, y, drugtypes[np.random.randint(13)], np.random.randint(max(1, i), i+3))

            for j in range(5):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.campfires[x, y] != 0:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                item.Cure(cave.items, x, y, infusiontypes[np.random.randint(13)], np.random.randint(max(1, i), i+3))

            for j in range(np.random.randint(6,11)):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.campfires[x, y] != 0:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                item.randomfood(cave.items, x, y)

            for j in range(5):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.campfires[x, y] != 0:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                item.randomweapon(cave.items, x, y, i)

            for j in range(5):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.campfires[x, y] != 0:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                item.randomarmor(cave.items, x, y, i)

            for j in range(np.random.randint(1,4)):
                x = y = 0
                while cave.walls[x, y] != 0 or cave.lavapits[x, y] != 0 or cave.campfires[x, y] != 0:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                item.randomUtilityItem(cave.items, x, y)

            for j in range(10):
                x = y = 0
                enemytypes = [typ[0] for typ in creature.enemytypesbylevel[i]]
                p = np.array([typ[1] for typ in creature.enemytypesbylevel[i]])
                p = p/sum(p)
                while cave.walls[x, y] != 0  or cave.lavapits[x, y] != 0 or cave.campfires[x, y] != 0:
                    x = np.random.randint(mapwidth)
                    y = np.random.randint(mapheight)
                cave.creatures.append(np.random.choice(enemytypes, p=p)(cave, i, x, y))

            for creat in cave.creatures:
                for gd in gods:
                    if creat.faction == gd.faction:
                        creat.godsknown().append(gd)

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
        player.bodyparts[0].connect('left lung', bodypart.HumanLung(player.bodyparts, 0, 0))
        player.bodyparts[0].connect('right lung', bodypart.HumanLung(player.bodyparts, 0, 0))
        player.bodyparts[0].connect('left kidney', bodypart.HumanKidney(player.bodyparts, 0, 0))
        player.bodyparts[0].connect('right kidney', bodypart.HumanKidney(player.bodyparts, 0, 0))
        player.bodyparts[0].connect('stomach', bodypart.HumanStomach(player.bodyparts, 0, 0))
        player.bodyparts[0].connect('head', bodypart.HumanHead(player.bodyparts, 0, 0))
        player.bodyparts[-1].connect('brain', bodypart.HumanBrain(player.bodyparts, 0, 0))
        player.bodyparts[-2].connect('left eye', bodypart.HumanEye(player.bodyparts, 0, 0))
        player.bodyparts[-3].connect('right eye', bodypart.HumanEye(player.bodyparts, 0, 0))
        #item.Backpack(player.torso.worn['backpack'], 0, 0)
        player.faction = 'player'
        player.x = cave.stairsupcoords[0]
        player.y = cave.stairsupcoords[1]
        cave.creatures.append(player)

        player.log().append('You are a golem, a Frankensteinian creature. The humans saw you as a monster and exiled you into these caves. Now your short-term goal is to survive, and the long-term goal is to gather power for revenge. Your ability to change your bodyparts should become useful.')
        player.log().append("Press 'h' for help.")

        for i in range(mapwidth + hpbarwidth + hpmargin):
            for j in range(mapheight + statuslines + logheight):
                win.putchars(' ', x=i, y=j, bgcolor='black')  # For some reason the above commented line doesn't work on Windows, so have to do it this way instead.
        prompt = 'Give your character a name:'
        win.autoupdate = True
        win.write(prompt, x=0, y=0, fgcolor=(255,255,255))
        while player.individualname == '':
            player.individualname = win.input()
        win.autoupdate = False

    logback = 0 # How far the log has been scrolled
    chosen = 0 # Used for different item choosing gamestates
    numchosen = False # Also used for different item choosing gamestates
    target = None # Target of an attack
    lookx = looky = 0 # Coords of looking
    lastattack = None
    secondlastattack = None

    gamestate = 'free'

    def draw():
        if not player.dead:
            fovmap = fov(cave.walls, player.x, player.y, player.sight())
        else:
            fovmap = np.ones((mapwidth, mapheight))
        # Background
        # win.setscreencolors(None, (0,0,0), clear=True)
        win.settint(0, 0, 0, (0, 0, mapwidth + hpbarwidth + hpmargin, mapheight + statuslines + logheight))
        for i in range(mapwidth + hpbarwidth + hpmargin):
            for j in range(mapheight + statuslines + logheight):
                win.putchars(' ', x=i, y=j, bgcolor='black')  # For some reason the above commented line doesn't work on Windows, so have to do it this way instead.
        if not player.dead:
            seen = player.seen() # This should prevent at least some of the lag when the player has no brain.
        else:
            seen = []
            for i in range(numlevels):
                seen.append([[(' ', (255, 255, 255), (0, 0, 0), (0, 0, 0))]*mapheight for i in range(mapwidth)])
        for i in range(mapwidth):
            for j in range(mapheight):
                if fovmap[i,j]:
                    if cave.lavapits[i,j]:
                        visiblebgcolor = (255, 0, 0)
                        nonvisiblebgcolor = (128, 0, 0)
                    else:
                        visiblebgcolor = (64, 64, 64)
                        nonvisiblebgcolor = (0, 0, 0)
                    if cave.walls[i,j]:
                        win.putchars(' ', x=i, y=j, bgcolor='white')
                        seen[cave_i][i][j] = (' ', (0, 0, 0), (128, 128, 128), (0, 0, 0))
                    elif cave.spiderwebs[i,j]:
                        win.putchars('#', x=i, y=j, bgcolor=(64,64,64), fgcolor='white')
                        seen[cave_i][i][j] = ('#', (128, 128, 128), (0, 0, 0), (0, 0, 0))
                    elif cave.largerocks[i,j]:
                        win.putchars('%', x=i, y=j, bgcolor=(64,64,64), fgcolor='white')
                        seen[cave_i][i][j] = ('%', (128, 128, 128), (0, 0, 0), (0, 0, 0))
                    elif cave.campfires[i,j]:
                        win.putchars('%', x=i, y=j, bgcolor=(64,64,64), fgcolor=(255, 204, 0))
                        seen[cave_i][i][j] = ('%', (128, 102, 0), (0, 0, 0), (0, 0, 0))
                    else:
                        win.putchars(' ', x=i, y=j, bgcolor=visiblebgcolor)
                        seen[cave_i][i][j] = (' ', (255, 255, 255), nonvisiblebgcolor, (0, 0, 0))
                else:
                    win.putchars(seen[cave_i][i][j][0], x=i, y=j, fgcolor=seen[cave_i][i][j][1], bgcolor = seen[cave_i][i][j][2])
                    win.settint(seen[cave_i][i][j][3][0], seen[cave_i][i][j][3][1], seen[cave_i][i][j][3][2], (i,j,1,1))
        i, j = cave.stairsdowncoords
        if fovmap[i,j]:
            win.putchars('>', x=i, y=j, bgcolor=(64,64,64), fgcolor='white')
            seen[cave_i][i][j] = ('>', (128, 128, 128), (0, 0, 0), (0, 0, 0))
        i, j = cave.stairsupcoords
        if fovmap[i,j]:
            win.putchars('<', x=i, y=j, bgcolor=(64,64,64), fgcolor='white')
            seen[cave_i][i][j] = ('<', (128, 128, 128), (0, 0, 0), (0, 0, 0))
        for i, j, _ in cave.altars:
            if fovmap[i,j]:
                win.putchars('%', x=i, y=j, bgcolor=(64,64,64), fgcolor=(0, 255, 255))
                seen[cave_i][i][j] = ('%', (0, 128, 128), (0, 0, 0), (0, 0, 0))

        # Items
        for it in cave.items:
            if fovmap[it.x, it.y]:
                if not player.dead and not it in player.itemsseen() and not it.hidden:
                    brains = [part for part in player.bodyparts if 'brain' in part.categories and not part.destroyed()]
                    if len(brains) > 0:
                        player.itemsseen().append(it)
                if player.dead or it in player.itemsseen() or not it.hidden:
                    if cave.lavapits[it.x,it.y]:
                        visiblebgcolor = (255, 0, 0)
                        nonvisiblebgcolor = (128, 0, 0)
                    else:
                        visiblebgcolor = (64, 64, 64)
                        nonvisiblebgcolor = (0, 0, 0)
                    win.putchars(it.char, x=it.x, y=it.y, 
                         bgcolor=visiblebgcolor, fgcolor=it.color)
                    seen[cave_i][it.x][it.y] = ('?', (128, 128, 128), nonvisiblebgcolor, (0, 0, 0))

        # Creatures
        for npc in [creature for creature in cave.creatures if creature.faction != 'player']:
            if fovmap[npc.x, npc.y]:
                if cave.lavapits[npc.x,npc.y]:
                        bgcolor = (255, 0, 0)
                else:
                    bgcolor = (64, 64, 64)
                win.putchars(npc.char, npc.x, npc.y, bgcolor=bgcolor,
                             fgcolor=npc.color)
                if not player.dead and not npc in player.creaturesseen():
                    player.creaturesseen().append(npc)
                    if player in npc.creaturesseen():
                            player.log().append('You see a ' + npc.name +'. It has noticed you.')
                            fovmap2 = fov(npc.world.walls, npc.x, npc.y, npc.sight())
                            if fovmap2[player.x, player.y]:
                                npc.log().append('The ' + player.name + ' noticed you!')
                    else:
                        player.log().append('You see a ' + npc.name +'. It hasn\'t noticed you.')
        if cave.lavapits[player.x,player.y]:
            bgcolor = (255, 0, 0)
        else:
            bgcolor = (64, 64, 64)
        win.putchars(player.char, x=player.x, y=player.y, 
                     bgcolor=bgcolor, fgcolor=player.color)

        # Poison gas
        for i in range(mapwidth):
            for j in range(mapheight):
                if fovmap[i,j]:
                    if cave.poisongas[i,j]:
                        win.settint(0, 128, 0, (i, j, 1, 1))
                        seen[cave_i][i][j] = (seen[cave_i][i][j][0], seen[cave_i][i][j][1], seen[cave_i][i][j][2], (0, 64, 0))

        # Status
        for i in range(mapwidth):
            for j in range(statuslines):
                win.putchars(' ', x=i, y=mapheight+j, bgcolor=((128,128,128)))
        for i in range(hpmargin):
            for j in range(mapheight + statuslines + logheight):
                win.putchars(' ', x=mapwidth+i, y=j, bgcolor=((128,128,128)))
        if not player.dying():
            win.putchars('HP', x=mapwidth + hpmargin + hpbarwidth//2 - 1, y = 0, fgcolor = 'white')
            hptext = repr(int(sum([part.maxhp for part in player.bodyparts])/2-sum([part.damagetaken for part in player.bodyparts]))) + '/' + repr(int(sum([part.maxhp for part in player.bodyparts])/2))
            win.putchars('total:', x=mapwidth + hpmargin, y=1, fgcolor=(255, 0, 0))
            win.putchars(hptext, x=mapwidth + hpmargin + hpbarwidth - len(hptext), y=2, fgcolor=(255, 0, 0))
            texty = 3
            for part in player.bodyparts:
                if player.dying():
                    textcolor = (128,128,128)
                elif part.vital():
                    textcolor = (255, 0, 0)
                elif part.destroyed():
                    textcolor = (128,128,128)
                else:
                    textcolor = (0, 255, 0)
                if part.parentalconnection != None:
                    partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
                elif part == player.torso:
                    partname = 'torso'
                shortname = bodypartshortnames[partname]
                win.putchars(shortname + ':', x=mapwidth + hpmargin, y=texty, fgcolor=textcolor)
                hptext = repr(part.maxhp - part.damagetaken) + '/' + repr(part.maxhp)
                win.putchars(hptext, x=mapwidth + hpmargin + hpbarwidth - len(hptext), y=texty+1, fgcolor=textcolor)
                texty += 2

        win.putchars(player.individualname + ' the golem', x=0, y=mapheight, fgcolor='white', bgcolor=(128,128,128))
        win.putchars('Score: ' + repr(player.xp), x=30, y=mapheight, fgcolor='white', bgcolor=(128,128,128))
        win.putchars('Dungeon level ' + repr(cave_i + 1), x=50, y=mapheight, fgcolor='white', bgcolor=(128,128,128))

        textx = 0
        texty = mapheight + 1
        if not player.dying():
            statuseffects = []
            if player.stance != 'neutral':
                statuseffects.append((player.stance.capitalize(), (0, 255, 0)))
            if player.panicked():
                statuseffects.append(('Panicked', (255, 0, 0)))
            elif player.scared():
                statuseffects.append(('Scared', (255, 255, 0)))
            elif player.imbalanced():
                statuseffects.append(('Imbalanced', (255, 255, 0)))
            if player.overloaded():
                statuseffects.append(('Overloaded', (255, 0, 0)))
            elif player.burdened():
                statuseffects.append(('Burdened', (255, 255, 0)))
            if player.suffocating():
                statuseffects.append(('Suffocating', (255, 0, 0)))
            bleed = False
            for part in player.bodyparts:
                if len(part.bleedclocks) > 0 and not part.destroyed():
                    bleed = True
            if bleed:
                statuseffects.append(('Bleeding', (255, 0, 0)))
            if player.starving():
                statuseffects.append(('Starving', (255, 0, 0)))
            elif player.hungry():
                statuseffects.append(('Hungry', (255, 255, 0)))
            if player.accumulatedpoison > 5:
                if len([part for part in player.bodyparts if part.material == 'living flesh']) > 0:
                    statuseffects.append(('Poisoned', (255, 0, 0)))
                else:
                    statuseffects.append(('Poisoned', (0, 0, 0)))
            if player.slowed() == 1:
                statuseffects.append(('Slowed', (255, 255, 0)))
            if player.slowed() > 1:
                statuseffects.append(('Slowed', (255, 0, 0)))
            if player.weakened():
                statuseffects.append(('Weakened', (255, 255, 0)))
            if player.vomitclock > 0:
                statuseffects.append(('Vomiting', (255, 255, 0)))
            if player.disorientedclock > 0:
                statuseffects.append(('Disoriented', (255, 255, 0)))
            for effect in statuseffects:
                if textx + len(effect[0]) > mapwidth:
                    textx = 0
                    texty += 1
                win.putchars(effect[0], x=textx, y=texty, bgcolor=((128,128,128)), fgcolor=effect[1])
                textx += len(effect[0]) + 1
        else:
            win.putchars('Dead', x=textx, y=texty, bgcolor=((128,128,128)), fgcolor=(255, 0, 0))

        # log
        if gamestate == 'free' or gamestate == 'dead' or gamestate == 'win':
            logrows = min(logheight,len(player.log()))
            for i in range(logrows):
                j = i-logrows-logback
                c = 255 + (max(j+1, -logheight))*128//logheight
                win.write(player.log()[j], x=0, y=mapheight+statuslines+i, fgcolor=(c,c,c))

        elif gamestate == 'look':
            win.settint(128, 128, 0, (lookx, looky, 1, 1))

            instructions = 'Move the looking cursor with the movement keys. ESC to stop looking.'
            win.write(instructions, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            lookinglist = []
            if cave.walls[lookx, looky]:
                lookinglist.append('a wall')
            if cave.lavapits[lookx, looky]:
                lookinglist.append('a lava pit')
            if cave.spiderwebs[lookx, looky]:
                lookinglist.append('spiderweb')
            if cave.poisongas[lookx, looky]:
                lookinglist.append('poison gas')
            if cave.stairsupcoords == (lookx, looky):
                lookinglist.append('stairs up')
            if cave.stairsdowncoords == (lookx, looky):
                lookinglist.append('stairs down')
            if cave.largerocks[lookx, looky]:
                lookinglist.append('a large rock')
            if cave.campfires[lookx, looky]:
                lookinglist.append('a campfire')
            for x, y, gd in cave.altars:
                if (lookx, looky) == (x, y):
                    lookinglist.append('an altar of ' + gd.name)
            for it in cave.items:
                if it.x == lookx and it.y == looky and (it in player.itemsseen() or not it.hidden):
                    lookinglist.append('a ' + it.name)
            for creat in cave.creatures:
                if creat.x == lookx and creat.y == looky:
                    lookinglist.append('a ' + creat.name)
            if player.sight() > 1:
                verb = 'see '
            else:
                verb = 'sense '
            if len(lookinglist) > 10:
                win.write('You ' + verb + 'a large pile of things here.', x=0, y=mapheight+statuslines+1, fgcolor=(255,255,255))
            elif len(lookinglist) == 0:
                win.write('You ' + verb + 'nothing here.', x=0, y=mapheight+statuslines+1, fgcolor=(255,255,255))
            else:
                if len(lookinglist) > 1:
                    lookinglist[-1] = 'and ' + lookinglist[-1]
                if len(lookinglist) > 2:
                    joiner = ', '
                else:
                    joiner = ' '
                looktext = 'You ' + verb + joiner.join(lookinglist) + ' here.'
                if len(looktext) <= mapwidth:
                    win.write(looktext, x=0, y=mapheight+statuslines+1, fgcolor=(255,255,255))
                else:
                    texty = mapheight+statuslines+1
                    while len(looktext) > mapwidth:
                        start = looktext[:mapwidth]
                        end = looktext[mapwidth:]
                        lastspace = start.rfind(' ')
                        if lastspace != -1:
                            looktext = start[lastspace+1:] + end
                            start = start[:lastspace]
                        else:
                            looktext = end
                        win.write(start, x=0, y=texty, fgcolor=(255,255,255))
                        texty += 1
                    win.write(looktext, x=0, y=texty, fgcolor=(255,255,255))

        elif gamestate == 'mine':
            minemessage = 'Choose the direction to mine!'
            win.write(minemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))

        elif gamestate == 'pick':
            pickmessage = 'Choose the item to pick:'
            win.write(pickmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len(picklist))
            for i in range(logrows):
                if len(picklist) <= logheight-1:
                    j = i
                else:
                    j = len(picklist)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if picklist[j].maxhp < np.inf:
                    itname = num + picklist[j].name + ' (wt: ' + repr(picklist[j].weight) + ' g,' + ' hp: ' + repr(picklist[j].hp()) + '/' + repr(picklist[j].maxhp) + ')'
                else:
                    itname = num + picklist[j].name + ' (wt: ' + repr(picklist[j].weight) + ' g)'
                if j != chosen:
                    win.write(itname, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(itname, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'drop':
            dropmessage = 'Choose the item to drop:'
            win.write(dropmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len(player.inventory))
            for i in range(logrows):
                if len(player.inventory) <= logheight-1:
                    j = i
                else:
                    j = len(player.inventory)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if player.inventory[j].maxhp < np.inf:
                    itname = num + player.inventory[j].name + ' (wt: ' + repr(player.inventory[j].weight) + ' g,' + ' hp: ' + repr(player.inventory[j].hp()) + '/' + repr(player.inventory[j].maxhp) + ')'
                else:
                    itname = num + player.inventory[j].name + ' (wt: ' + repr(player.inventory[j].weight) + ' g)'
                if j != chosen:
                    win.write(itname, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(itname, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'information':
            infomessage = 'Choose the item to get information about:'
            win.write(infomessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len(itemlist))
            for i in range(logrows):
                if len(itemlist) <= logheight-1:
                    j = i
                else:
                    j = len(itemlist)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if itemlist[j].maxhp < np.inf:
                    itname = num + itemlist[j].name + ' (wt: ' + repr(itemlist[j].weight) + ' g,' + ' hp: ' + repr(itemlist[j].hp()) + '/' + repr(itemlist[j].maxhp) + ')'
                else:
                    itname = num + itemlist[j].name + ' (wt: ' + repr(itemlist[j].weight) + ' g)'
                if j != chosen:
                    win.write(itname, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(itname, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'consume':
            consumemessage = 'Choose the item to consume:'
            win.write(consumemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len([item for item in player.inventory if item.consumable]))
            for i in range(logrows):
                if len([item for item in player.inventory if item.consumable]) <= logheight-1:
                    j = i
                else:
                    j = len([item for item in player.inventory if item.consumable])+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                it = [item for item in player.inventory if item.consumable][j]
                itemdescription = num + it.name
                if it.cure and it.curetype in player.curesknown():
                    itemdescription += '('
                    if it.hpgiven() >= 0:
                        itemdescription += '+'
                    itemdescription += repr(it.hpgiven()) + ' hp to ' + it.curedmaterial + ')'
                if j != chosen:
                    win.write(itemdescription, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(itemdescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'cook':
            cookmessage = 'Choose the item to cook:'
            win.write(cookmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len([item for item in player.inventory if item.material == 'living flesh']))
            for i in range(logrows):
                if len([item for item in player.inventory if item.material == 'living flesh']) <= logheight-1:
                    j = i
                else:
                    j = len([item for item in player.inventory if item.material == 'living flesh'])+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                it = [item for item in player.inventory if item.material == 'living flesh'][j]
                itemdescription = num + it.name
                if j != chosen:
                    win.write(itemdescription, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(itemdescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'wieldchooseitem':
            wieldmessage = 'Choose the item to wield:'
            win.write(wieldmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len([item for item in player.inventory if item.wieldable]))
            for i in range(logrows):
                if len([item for item in player.inventory if item.wieldable]) <= logheight-1:
                    j = i
                else:
                    j = len([item for item in player.inventory if item.wieldable])+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if j != chosen:
                    win.write(num + [item for item in player.inventory if item.wieldable][j].name, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(num + [item for item in player.inventory if item.wieldable][j].name, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'wieldchoosebodypart':
            wieldmessage = 'Choose where to wield the ' + selecteditem.name + ':'
            win.write(wieldmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()]))
            for i in range(logrows):
                if len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()]) <= logheight-1:
                    j = i
                else:
                    j = len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()])+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if j != chosen:
                    win.write(num + [part.wearwieldname() for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()][j], x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(num + [part.wearwieldname() for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()][j], x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'unwield':
            wieldmessage = 'Choose the item to unwield:'
            win.write(wieldmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]))
            for i in range(logrows):
                if len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) <= logheight-1:
                    j = i
                else:
                    j = len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0])+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if j != chosen:
                    win.write(num + [part.wielded[0].name + ' in the ' + part.wearwieldname() for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0][j], x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(num + [part.wielded[0].name + ' in the ' + part.wearwieldname() for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0][j], x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'wearchooseitem':
            wearmessage = 'Choose the item to wear:'
            win.write(wearmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len([item for item in player.inventory if item.wearable]))
            for i in range(logrows):
                if len([item for item in player.inventory if item.wearable]) <= logheight-1:
                    j = i
                else:
                    j = len([item for item in player.inventory if item.wearable])+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if j != chosen:
                    win.write(num + [item for item in player.inventory if item.wearable][j].name, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(num + [item for item in player.inventory if item.wearable][j].name, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'wearchoosebodypart':
            wearmessage = 'Choose where to wear the ' + selecteditem.name + ':'
            win.write(wearmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len(partlist))
            for i in range(logrows):
                if len(partlist) <= logheight-1:
                    j = i
                else:
                    j = len(partlist)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if j != chosen:
                    win.write(num + partlist[j].wearwieldname() + ' (' + selecteditem.wearcategory + ' slot)', x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(num + partlist[j].wearwieldname() + ' (' + selecteditem.wearcategory + ' slot)', x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'undress':
            choosemessage = 'Choose the item to take off:'
            win.write(choosemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            wornlist = [it[0] for part in player.bodyparts for it in part.worn.values() if len(it) > 0]
            logrows = min(logheight-1,len(wornlist))
            for i in range(logrows):
                if len(wornlist) <= logheight-1:
                    j = i
                else:
                    j = len(wornlist)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if j != chosen:
                    win.write(num + wornlist[j].name + ' on the ' + wornlist[j].owner.owner.wearwieldname(), x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(num + wornlist[j].name + ' on the ' + wornlist[j].owner.owner.wearwieldname(), x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'chooseattack':
            attackmessage = 'Choose how to attack the ' + target.name + ':'
            win.write(attackmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len(player.attackslist()))
            for i in range(logrows):
                if len(player.attackslist()) <= logheight-1:
                    j = i
                else:
                    j = len(player.attackslist())+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                attacktime = player.attackslist()[j].time * (1 + player.slowed())
                if int(attacktime) == attacktime:
                    attacktime = int(attacktime)
                else:
                    attacktime = round(attacktime, 2)
                if player.stance == 'aggressive':
                    attackerstancecoefficient = 1.25
                elif player.stance == 'defensive':
                    attackerstancecoefficient = 0.9
                elif player.stance == 'berserk':
                    attackerstancecoefficient = 1.5
                else:
                    attackerstancecoefficient = 1
                if (player.stance == 'flying' or cave.largerocks[player.x, player.y]) and target.stance != 'flying' and not cave.largerocks[target.x, target.y]:
                    highgroundcoefficient = 1.05
                elif player.stance != 'flying' and not cave.largerocks[player.x, player.y] and (target.stance == 'flying' or cave.largerocks[target.x, target.y]):
                    highgroundcoefficient = 0.95
                else:
                    highgroundcoefficient = 1
                attackdescription = num + player.attackslist()[j].name + ' (' + repr(int(attackerstancecoefficient*highgroundcoefficient*player.attackslist()[j].hitprobability * 100)) + '%, ' + repr(player.attackslist()[j].mindamage) + '-' + repr(player.attackslist()[j].maxdamage) + ' ' + player.attackslist()[j].damagetype + ', ' + repr(attacktime) + ' s'
                for special in player.attackslist()[j].special:
                    if special[0] == 'bleed':
                        attackdescription += ', bleed ' + repr(int(special[1] * 100)) + '%'
                    if special[0] == 'knockback':
                        attackdescription += ', knockback ' + repr(int(special[1] * 100)) + '%'
                    if special[0] == 'charge':
                        attackdescription += ', charge'
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
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                targetbodypart = [part for part in target.bodyparts if not part.destroyed()][j]
                if targetbodypart.parentalconnection != None:
                    partname = list(targetbodypart.parentalconnection.parent.childconnections.keys())[list(targetbodypart.parentalconnection.parent.childconnections.values()).index(targetbodypart.parentalconnection)]
                elif targetbodypart == target.torso:
                    partname = 'torso'
                if target.stance == 'aggressive':
                    defenderstancecoefficient = 1.111
                elif target.stance == 'defensive':
                    defenderstancecoefficient = 0.80
                elif target.stance == 'berserk':
                    defenderstancecoefficient = 1.222
                else:
                    defenderstancecoefficient = 1
                if selectedattack.weapon in player.bodyparts:
                    attackingpart = selectedattack.weapon
                elif selectedattack.weapon.owner != cave.items:
                    attackingpart = selectedattack.weapon.owner.owner
                upperpoorlimit = attackingpart.baseheight() + attackingpart.upperpoorlimit + selectedattack.weaponlength
                upperfinelimit = attackingpart.baseheight() + attackingpart.upperfinelimit + selectedattack.weaponlength
                lowerfinelimit = attackingpart.baseheight() + attackingpart.lowerfinelimit - selectedattack.weaponlength
                lowerpoorlimit = attackingpart.baseheight() + attackingpart.lowerpoorlimit - selectedattack.weaponlength
                if upperfinelimit >= targetbodypart.topheight() >= lowerfinelimit or upperfinelimit >= targetbodypart.bottomheight() >= lowerfinelimit or targetbodypart.topheight() >= upperfinelimit >= targetbodypart.bottomheight():
                    heightcoefficient = 1
                elif targetbodypart.bottomheight() >= upperpoorlimit or targetbodypart.topheight() <= lowerpoorlimit:
                    heightcoefficient = 0.5
                elif upperpoorlimit > targetbodypart.bottomheight() > upperfinelimit:
                    heightcoefficient = 0.5 + 0.5*(upperpoorlimit - targetbodypart.bottomheight())/(upperpoorlimit - upperfinelimit)
                elif lowerpoorlimit < targetbodypart.topheight() < lowerfinelimit:
                    heightcoefficient = 0.5 + 0.5*(targetbodypart.topheight() - lowerpoorlimit)/(lowerfinelimit - lowerpoorlimit)
                speedcoefficient = 1/np.sqrt(target.speed()+0.1)
                if target.imbalanced():
                    imbalancedcoefficient = 1.25
                else:
                    imbalancedcoefficient = 1
                if player.previousaction[0] == 'fight' and player.previousaction[1] == selectedattack.weapon and player.previousaction[2] == targetbodypart:
                    targetdescription = num + partname + ' (' + repr(int(defenderstancecoefficient*heightcoefficient*speedcoefficient*imbalancedcoefficient*targetbodypart.defensecoefficient() * 100)) + '%, time x1.5)'
                else:
                    targetdescription = num + partname + ' (' + repr(int(defenderstancecoefficient*heightcoefficient*speedcoefficient*imbalancedcoefficient*targetbodypart.defensecoefficient() * 100)) + '%)'
                if targetbodypart.incapacitated():
                    targetdescription += ' [INCAPACITATED]'
                if j != chosen:
                    win.write(targetdescription, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(targetdescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'throwchoosemissile':
            attackmessage = 'Choose the item to throw:'
            win.write(attackmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len(player.thrownattackslist()))
            for i in range(logrows):
                if len(player.thrownattackslist()) <= logheight-1:
                    j = i
                else:
                    j = len(player.thrownattackslist())+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if player.stance == 'aggressive':
                    attackerstancecoefficient = 1.25
                elif player.stance == 'defensive':
                    attackerstancecoefficient = 0.9
                elif player.stance == 'berserk':
                    attackerstancecoefficient = 1.5
                else:
                    attackerstancecoefficient = 1
                attackdescription = num + player.thrownattackslist()[j].name + ' (' + repr(int(attackerstancecoefficient*player.thrownattackslist()[j].hitprobability * 100)) + '%, ' + repr(player.thrownattackslist()[j].mindamage) + '-' + repr(player.thrownattackslist()[j].maxdamage) + ' ' + player.thrownattackslist()[j].damagetype + ', ' + repr(int(player.thrownattackslist()[j].weapon.throwrange)) + ' paces'
                for special in player.thrownattackslist()[j].special:
                    if special[0] == 'bleed':
                        attackdescription += ', bleed ' + repr(int(special[1] * 100)) + '%'
                    if special[0] == 'knockback':
                        attackdescription += ', knockback ' + repr(int(special[1] * 100)) + '%'
                    if special[0] == 'charge':
                        attackdescription += ', charge'
                attackdescription += ')'
                if j != chosen:
                    win.write(attackdescription, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(attackdescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'throwchoosetarget':
            fovmap = fov(cave.walls, player.x, player.y, player.sight())
            fovmap2 = fov(cave.walls, player.x, player.y, selectedattack.weapon.throwrange, nowalls=True)
            for i in range(mapwidth):
                for j in range(mapheight):
                    if fovmap[i, j] and fovmap2[i, j]:
                        win.settint(64, 64, 0, (i, j, 1, 1))
            win.settint(128, 128, 0, (lookx, looky, 1, 1))

            instructions = 'Move the cursor with the movement keys to choose the target, then press Enter. ESC to cancel.'
            win.write(instructions, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))

        elif gamestate == 'throwchoosetargetbodypart':
            attackmessage = 'Choose where to attack the ' + target.name + ':'
            win.write(attackmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len([part for part in target.bodyparts if not part.destroyed()]))
            for i in range(logrows):
                if len([part for part in target.bodyparts if not part.destroyed()]) <= logheight-1:
                    j = i
                else:
                    j = len([part for part in target.bodyparts if not part.destroyed()])+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                targetbodypart = [part for part in target.bodyparts if not part.destroyed()][j]
                if targetbodypart.parentalconnection != None:
                    partname = list(targetbodypart.parentalconnection.parent.childconnections.keys())[list(targetbodypart.parentalconnection.parent.childconnections.values()).index(targetbodypart.parentalconnection)]
                elif targetbodypart == target.torso:
                    partname = 'torso'
                if target.stance == 'aggressive':
                    defenderstancecoefficient = 1.111
                elif target.stance == 'defensive':
                    defenderstancecoefficient = 0.80
                elif target.stance == 'berserk':
                    defenderstancecoefficient = 1.222
                else:
                    defenderstancecoefficient = 1
                speedcoefficient = 1/np.sqrt(target.speed()+0.1)
                if target.imbalanced():
                    imbalancedcoefficient = 1.25
                else:
                    imbalancedcoefficient = 1
                targetdescription = num + partname + ' (' + repr(int(defenderstancecoefficient*speedcoefficient*imbalancedcoefficient*targetbodypart.defensecoefficient() * 100)) + '%)'
                if targetbodypart.incapacitated():
                    targetdescription += ' [INCAPACITATED]'
                if j != chosen:
                    win.write(targetdescription, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(targetdescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'throwchooselimb':
            attackmessage = 'Choose the limb to use for throwing:'
            win.write(attackmessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len(limblist))
            for i in range(logrows):
                if len(limblist) <= logheight-1:
                    j = i
                else:
                    j = len(limblist)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                limb = limblist[j]
                if limb.parentalconnection != None:
                    partname = list(limb.parentalconnection.parent.childconnections.keys())[list(limb.parentalconnection.parent.childconnections.values()).index(limb.parentalconnection)]
                elif limb == player.torso:
                    partname = 'torso'
                if (player.stance == 'flying' or cave.largerocks[player.x, player.y]) and target.stance != 'flying' and not cave.largerocks[target.x, target.y]:
                    highgroundcoefficient = 1.05
                elif player.stance != 'flying' and not cave.largerocks[player.x, player.y] and (target.stance == 'flying' or cave.largerocks[target.x, target.y]):
                    highgroundcoefficient = 0.95
                else:
                    highgroundcoefficient = 1
                distance = np.sqrt((targetcoords[0] - player.x)**2 + (targetcoords[1] - player.y)**2)
                wornlist = [it[0] for part in player.bodyparts for it in part.worn.values() if len(it) > 0]
                notwielded = selectedattack.weapon.owner == player.inventory and not np.any([hasattr(it, 'quickdraw') and it.quickdraw for it in wornlist])
                throwtime = (1/limb.throwspeed + notwielded) * (1 + player.slowed())
                if int(throwtime) == throwtime:
                    throwtime = int(throwtime)
                else:
                    throwtime = round(throwtime, 2)
                limbdescription = num + partname + ' (' + repr(int(highgroundcoefficient*limb.throwaccuracy**distance * 100)) + '%, ' + repr(throwtime) + ' s)'
                if j != chosen:
                    win.write(limbdescription, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(limbdescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'choosetorso':
            choosemessage = 'Choose your torso:'
            win.write(choosemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            torsolist = [part for part in player.bodyparts if 'torso' in part.categories and part.usable and not part.destroyed()] + [it for it in player.inventory if it.bodypart and 'torso' in it.categories and it.usable and not it.destroyed()]
            logrows = min(logheight-1,len(torsolist))
            for i in range(logrows):
                if len(torsolist) <= logheight-1:
                    j = i
                else:
                    j = len(torsolist)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if j != chosen:
                    win.write(num + torsolist[j].name + ' (hp: ' + repr(torsolist[j].hp()) + '/' + repr(torsolist[j].maxhp) + ')', x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(num + torsolist[j].name + ' (hp: ' + repr(torsolist[j].hp()) + '/' + repr(torsolist[j].maxhp) + ')', x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'choosebodypartconnection':
            choosemessage = 'Choose the bodypart to change (when you are done, choose "Ready!"):'
            win.write(choosemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1, len(connectioncandidates))
            for i in range(logrows):
                if len(connectioncandidates) <= logheight-1:
                    j = i
                else:
                    j = len(connectioncandidates)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if j == 0:
                    part = [part for part in bodypartcandidates if 'torso' in part.categories][0]
                    connectiondescription = 'torso: ' + part.name + ' (hp: ' + repr(part.hp()) + '/' + repr(part.maxhp) + ')'
                    fgcolorchosen = (0,0,0)
                    fgcolorunchosen = (255,255,255)
                elif j == len(connectioncandidates) - 1:
                    connectiondescription = 'Ready!'
                    if len([cn for cn in connectioncandidates if cn != None and cn[0].vital and cn[1] == None]) == 0:
                        fgcolorchosen = (0,0,0)
                        fgcolorunchosen = (255,255,255)
                    else:
                        fgcolorchosen = (128,128,128)
                        fgcolorunchosen = (128,128,128)
                else:
                    connectionname2 = list(connectioncandidates[j][0].parent.childconnections.keys())[list(connectioncandidates[j][0].parent.childconnections.values()).index(connectioncandidates[j][0])]
                    part = connectioncandidates[j][1]
                    if part != None:
                        connectiondescription = connectionname2 + ': ' + part.name + ' (hp: ' + repr(part.hp()) + '/' + repr(part.maxhp) + ')'
                    else:
                        connectiondescription = connectionname2 + ': ' + 'none'
                    if connectioncandidates[j][0].vital and connectioncandidates[j][1] == None:
                        fgcolorchosen = (255,0,0)
                        fgcolorunchosen = (255,0,0)
                    elif connectioncandidates[j][1] == None or connectioncandidates[j][1].hp() == 0:
                        fgcolorchosen = (255,255,0)
                        fgcolorunchosen = (255,255,0)
                    else:
                        fgcolorchosen = (0,0,0)
                        fgcolorunchosen = (255,255,255)
                if j != chosen:
                    win.write(num + connectiondescription, x=0, y=mapheight+statuslines+i+1, fgcolor=fgcolorunchosen)
                if j == chosen:
                    win.write(num + connectiondescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=fgcolorchosen)

        elif gamestate == 'choosebodypart':
            choosemessage = 'Choose your ' + connectionname + ':'
            win.write(choosemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len(partslist))
            if logrows == 0:
                win.write('No suitable options for a vital bodypart. Press ESC to cancel.', x=0, y=mapheight+statuslines+1, fgcolor=(255,255,255))
            for i in range(logrows):
                if len(partslist) <= logheight-1:
                    j = i
                else:
                    j = len(partslist)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if partslist[j] == None:
                    partdescription = 'none'
                else:
                    partdescription = partslist[j].name + ' (hp: ' + repr(partslist[j].hp()) + '/' + repr(partslist[j].maxhp) + ')'
                if j != chosen:
                    win.write(num + partdescription, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(num + partdescription, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'choosestance':
            stancemessage = 'Which stance do you want to be in'
            win.write(stancemessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,len(player.stancesknown()))
            for i in range(logrows):
                if len(player.stancesknown()) <= logheight-1:
                    j = i
                else:
                    j = len(player.stancesknown())+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if player.stancesknown()[j] == 'aggressive':
                    stancetext = 'Aggressive (+25% to hit, +11.1% to get hit)'
                elif player.stancesknown()[j] == 'defensive':
                    stancetext = 'Defensive (-20% to get hit, -10% to hit)'
                elif player.stancesknown()[j] == 'running':
                    stancetext = 'Running (move double speed, charge with any attack (proper charge attacks deal even more damage))'
                elif player.stancesknown()[j] == 'berserk':
                    stancetext = 'Berserk (+50% to hit, +22.2% to get hit)'
                elif player.stancesknown()[j] == 'fasting':
                    stancetext = 'Fasting (deal 2x damage on unarmed attacks when hungry, 3x when starving)'
                elif player.stancesknown()[j] == 'flying':
                    stancetext = 'Flying (avoid traps etc., see farther, and gain high ground (+5% to hit, -5% to get hit))'
                else:
                    stancetext = player.stancesknown()[j].capitalize()
                if j != chosen:
                    win.write(num + stancetext, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    win.write(num + stancetext, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        elif gamestate == 'pray':
            praymessage = 'To which sinful god of the underground do you wish to pray?'
            win.write(praymessage, x=0, y=mapheight+statuslines, fgcolor=(0,255,255))
            logrows = min(logheight-1,min(7, len(player.godsknown()) + 1))
            for i in range(logrows):
                if len(player.godsknown()) <= logheight-1:
                    j = i
                else:
                    j = min(7, len(player.godsknown()) + 1)+i-logrows-logback
                if j < 9:
                    num = repr(j + 1) + ': '
                elif j == 9:
                    num = '0: '
                else:
                    num = ''
                if j != chosen:
                    if j < len(player.godsknown()):
                        win.write(num + player.godsknown()[j].name + ', the ' + player.godsknown()[j].faction + '-god of ' + player.godsknown()[j].sin, x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                    else:
                        win.write(num + 'whomever listens', x=0, y=mapheight+statuslines+i+1, fgcolor=(255,255,255))
                if j == chosen:
                    if j < len(player.godsknown()):
                        win.write(num + player.godsknown()[j].name + ', the ' + player.godsknown()[j].faction + '-god of ' + player.godsknown()[j].sin, x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))
                    else:
                        win.write(num + 'whomever listens', x=0, y=mapheight+statuslines+i+1, bgcolor=(255,255,255), fgcolor=(0,0,0))

        win.update()

    def _updatetime(time):
        if player.preferredstance in player.stancesknown():
            player.stance = player.preferredstance
        if not player.stance in player.stancesknown() or (player.stance == 'running' and player.runstaminaused >= player.maxrunstamina()):
            oldstance = player.stance
            if 'neutral' in player.stancesknown():
                player.stance = 'neutral'
            elif 'defensive' in player.stancesknown():
                player.stance = 'defensive'
            elif 'running' in player.stancesknown():
                player.stance = 'running'
            else: # Shouldn't happen, but just in case
                player.stance = 'neutral'
            if oldstance == 'flying':
                for it in cave.items:
                    if (it.x, it.y) == (player.x, player.y) and it.trap:
                        part = player.approxfastestpart()
                        if it in player.itemsseen() or not it.hidden:
                            if np.random.rand() < part.carefulness:
                                player.log().append('You managed to land carefully and avoided the ' + it.name + '.')
                            else:
                                it.entrap(player, part)
                        else:
                            it.entrap(player, part)
                            player.itemsseen().append(it)
        cave.fadesmells(time)
        player.bleed(time)
        if cave.campfires[player.x, player.y] and player.stance != 'flying':
            player.burn('campfire', time)
        if cave.lavapits[player.x, player.y] and player.stance != 'flying':
            player.burn('lava', time)
        imbalanced = player.imbalanced()
        for part in player.bodyparts:
            part.imbalanceclock = max(0, part.imbalanceclock - time)
        if imbalanced and not player.imbalanced():
            player.log().append('You regained your balance.')
        player.applypoison(time)
        player.weakenedclock = max(0, player.weakenedclock - time)
        player.disorientedclock = max(0, player.disorientedclock - time)
        player.slowedclock = max(0, player.slowedclock - time)
        player.gainhunger(time)
        vomiting = player.vomitclock > 0
        player.vomitclock = max(0, player.vomitclock - time)
        if vomiting and player.vomitclock == 0:
            player.log().append('You stopped vomiting.')
        if player.starving():
            player.starvationclock += time
            for i in range(int(player.starvationclock // 1)):
                player.starve()
            player.starvationclock = player.starvationclock % 1
        player.suffocate(time)
        if player.stance != 'running' and not player.hungry():
            player.runstaminaused = max(0, player.runstaminaused - time*player.runstaminarecoveryspeed())
        elif player.stance != 'running' and not player.starving():
            player.runstaminaused = max(0, player.runstaminaused - time*0.5*player.runstaminarecoveryspeed())
        if player.panicked():
            player.panickedclock = max(0, player.panickedclock - time)
        elif player.scared():
            player.scaredclock = max(0, player.scaredclock - time)
        if cave.poisongas[player.x, player.y]:
            livingparts = [part for part in player.bodyparts if part.material == 'living flesh' and not part.destroyed()]
            lungs = [part for part in player.bodyparts if 'lung' in part.categories and not part.destroyed()]
            if np.random.rand() > player.breathepoisonresistance() and len(livingparts) > 0 and len(lungs) > 0:
                oldaccumulation = player.accumulatedpoison
                player.accumulatedpoison = min(50, player.accumulatedpoison + np.random.rand()*40)
                if player.accumulatedpoison > 5 and oldaccumulation <= 5:
                    player.log().append('You were poisoned by the gas.')
        for gd in gods:
            for creat in gd.prayerclocks:
                gd.prayerclocks[creat] += time
        for npc in [creature for creature in cave.creatures if creature.faction != 'player']:
            fovmap = fov(cave.walls, player.x, player.y, player.sight())
            seenbefore = fovmap[npc.x, npc.y]
            npc.update(time)
            seenafter = fovmap[npc.x, npc.y]
            if (seenbefore or seenafter) and showsequentially:
                draw()

    def updatetime(time):
        #for i in range(int(time // 0.1)):
        #    _updatetime(0.1)
        #_updatetime(time % 0.1)
        _updatetime(time)

    def detecthiddenitems():
        if not player.dead:
            fovmap = fov(cave.walls, player.x, player.y, player.sight())
        else:
            fovmap = np.ones((mapwidth, mapheight))
        for it in cave.items:
            if fovmap[it.x, it.y]:
                if not it in player.itemsseen() and it.hidden:
                    for part in player.bodyparts:
                        if np.sqrt((it.x-player.x)**2 + (it.y-player.y)**2) < part.detectiondistance and np.random.rand() < part.detectionprobability:
                            player.log().append('You noticed ' + it.name + '!')
                            player.itemsseen().append(it)

    def moveorattack(dx, dy):
        stumbling = False
        if (player.disorientedclock > 0 and np.random.rand() < 0.5) or (player.imbalanced() and np.random.rand() < 0.2):
            stumbling = True
            player.log().append('You stumble around.')
            originaldxdy = (dx, dy)
            while (dx,dy) == (0,0) or (dx,dy) == originaldxdy:
                dx = np.random.choice([-1,0,1])
                dy = np.random.choice([-1,0,1])
        targets = [creature for creature in cave.creatures if creature.x == player.x+dx and creature.y == player.y+dy]
        if len(targets) > 0 and not stumbling:
            if not player.panicked():
                target = targets[0]
                gamestate = 'chooseattack'
                logback = len(player.attackslist()) - logheight + 1
            else:
                player.log().append('You cannot attack while panicked!')
                logback = 0
                gamestate = 'free'
                target = None
        elif player.speed() == 0:
            player.log().append('You are unable to move!')
            logback = 0
            gamestate = 'free'
            target = None
        elif player.overloaded():
            player.log().append('You are too overloaded to move!')
            logback = 0
            gamestate = 'free'
            target = None
        elif cave.walls[player.x+dx, player.y+dy]:
            logback = 0
            gamestate = 'free'
            updatetime((np.sqrt(dx**2 + dy**2) * player.steptime() * (1 + player.slowed()) * (1 + (cave.largerocks[player.x+dx, player.y+dy] and player.stance != 'flying')))/2)
            if not player.dying():
                if player.stance == 'running':
                    player.runstaminaused += np.sqrt(dx**2 + dy**2) * player.steptime() * (1 + player.slowed()) * (1 + (cave.largerocks[player.x+dx, player.y+dy] and player.stance != 'flying')) * (1 + player.burdened()) / 2
                if player.stance != 'running':
                    player.log().append("You bumped into a wall.")
                else:
                    part = np.random.choice([part for part in player.bodyparts if not part.destroyed()])
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
                    part.damagetaken += damage
                    alreadyimbalanced = player.imbalanced()
                    if 'leg' in part.categories:
                        numlegs = len([p for p in player.bodyparts if 'leg' in p.categories and not p.destroyed() and not p.incapacitated()])
                        if np.random.rand() < 0.5 - 0.05*numlegs:
                            part.imbalanceclock += 10*damage/part.maxhp
                    if player.imbalanced() and not alreadyimbalanced:
                        imbalancedtext = ', imbalancing you'
                    else:
                        imbalancedtext = ''
                    if part.parentalconnection != None:
                        partname = list(part.parentalconnection.parent.childconnections.keys())[list(part.parentalconnection.parent.childconnections.values()).index(part.parentalconnection)]
                    elif part == player.torso:
                        partname = 'torso'
                    if not player.dying():
                        if not part.destroyed():
                            player.log().append('You ran into wall. It dealt ' + repr(damage) + ' damage to your ' + partname + imbalancedtext + '.')
                            if armordamage > 0:
                                if not armor.destroyed():
                                    player.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                                else:
                                    player.log().append('Your ' + armor.name + ' was destroyed!')
                                    armor.owner.remove(armor)
                        else:
                            player.log().append('You ran into wall. It destroyed your ' + partname + imbalancedtext + '.')
                            if armordamage > 0:
                                if not armor.destroyed():
                                    player.log().append('Your ' + armor.name + ' took ' +repr(armordamage) + ' damage!')
                                else:
                                    player.log().append('Your ' + armor.name + ' was also destroyed!')
                                    armor.owner.remove(armor)
                            part.on_destruction(False)
                    else:
                        player.log().append('You ran into wall ' + partname + ' first. It killed you.')
                        player.log().append('You are dead!')
                        if part.destroyed():
                            part.on_destruction(True)
                        player.die()
                        player.causeofdeath = ('ranintowall', partname)
            if not player.dying():
                player.previousaction = ('wait',)
                detecthiddenitems()
            target = None
        else:
            logback = 0
            gamestate = 'free'
            updatetime(np.sqrt(dx**2 + dy**2) * player.steptime() * (1 + player.slowed()) * (1 + (cave.largerocks[player.x+dx, player.y+dy] and player.stance != 'flying')))
            if not player.dying():
                if player.stance == 'running':
                    player.runstaminaused += np.sqrt(dx**2 + dy**2) * player.steptime() * (1 + player.slowed()) * (1 + (cave.largerocks[player.x+dx, player.y+dy] and player.stance != 'flying')) * (1 + player.burdened())
                creaturesintheway = [creature for creature in cave.creatures if creature.x == player.x+dx and creature.y == player.y+dy]
                if len(creaturesintheway) == 0:
                    player.move(dx, dy)
                    player.previousaction = ('move',)
                else:
                    player.log().append("There's a " + creaturesintheway[0].name + " in your way.")
                    player.previousaction = ('wait',)
                detecthiddenitems()
            target = None
        chosen = 0
        return(gamestate, logback, target, chosen)

    def mine(dx, dy):
        if player.x+dx == 0 or player.x+dx == mapwidth-1 or player.y+dy == 0 or player.y+dy == mapheight-1:
            player.log().append('That is too hard for you to mine.')
        elif cave.walls[player.x+dx, player.y+dy] == 1:
            updatetime(player.minetime() * (1 + player.slowed()))
            if not player.dying():
                player.log().append('You mined a hole in the wall.')
                cave.walls[player.x+dx, player.y+dy] = 0
                found = np.random.choice([0, 1, 2, 3], p=[0.79-0.01*(cave_i%5), 0.1, 0.1, 0.01+0.01*(cave_i%5)])
                if found == 1:
                    cave.largerocks[player.x+dx, player.y+dy] = 1
                if found == 2:
                    pebbles = item.LooseRoundPebbles(cave.items, player.x+dx, player.y+dy)
                    player.itemsseen().append(pebbles)
                if found == 3:
                    if cave_i < 5:
                        bodypart.VelociraptorSkull(cave.items, player.x+dx, player.y+dy)
                    elif cave_i < 10:
                        bodypart.DeinonychusSkull(cave.items, player.x+dx, player.y+dy)
                    elif cave_i < 15:
                        bodypart.CeratosaurusSkull(cave.items, player.x+dx, player.y+dy)
                    elif cave_i < 20:
                        bodypart.AllosaurusSkull(cave.items, player.x+dx, player.y+dy)
                    else:
                        bodypart.TyrannosaurusSkull(cave.items, player.x+dx, player.y+dy)
                player.previousaction = ('mine',)
            detecthiddenitems()
        else:
            player.log().append("There's no wall there.")
        return('free', 0)  # gamestate and logback



    draw()
    gamegoeson = True
    while gamegoeson:
        for event in pygame.event.get():
            #try:
                if event.type == pygame.locals.KEYDOWN:
                    
                    if player.dying() and gamestate != 'dead':
                        if file_exists('highscores.pickle'):
                            with open('highscores.pickle', 'rb') as f:
                                highscores = pickle.load(f)
                        else:
                            highscores = []
                        if player.causeofdeath[0] == 'attack':
                            deathmessage = 'killed by a ' + player.causeofdeath[1].name
                        elif player.causeofdeath[0] == 'smite':
                            deathmessage = 'smitten to death by ' + player.causeofdeath[1].name+ ', the ' + player.causeofdeath[1].faction + '-god of ' + player.causeofdeath[1].sin
                        elif player.causeofdeath[0] == 'bloodloss':
                            deathmessage = 'bled to death after being attacked by a ' + ' and a '.join([creat.name for creat in player.causeofdeath[1]])
                        elif player.causeofdeath[0] == 'starvation':
                            deathmessage = 'starved to death'
                        elif player.causeofdeath[0] == 'starvation':
                            deathmessage = 'starved to death'
                        elif player.causeofdeath[0] == 'suffocation':
                            deathmessage = 'suffocated to death'
                        elif player.causeofdeath[0] == 'consumption':
                            deathmessage = 'died from adverse effects of ' + player.causeofdeath[1].curetype.name
                        elif player.causeofdeath[0] == 'burning':
                            deathmessage = 'burned to death ' + player.causeofdeath[1]
                        elif player.causeofdeath[0] == 'step':
                            deathmessage = 'died from stepping on ' + player.causeofdeath[1].name
                        elif player.causeofdeath[0] == 'trip':
                            deathmessage = 'died from tripping on ' + player.causeofdeath[1].name
                        elif player.causeofdeath[0] == 'ranintowall':
                            deathmessage = 'died from running into wall ' + player.causeofdeath[1] + ' first'
                        else:
                            deathmessage = 'died from unknown causes'
                        deathmessage += (' on dungeon level ' + repr(player.world_i+1) + '.')
                        highscores.append((player.xp, player.individualname, deathmessage))
                        with open('highscores.pickle', 'wb') as f:
                            pickle.dump(highscores, f)
                        gamestate = 'dead'
                        numchosen = False
                        player.log().append('Press escape to end.')
                        logback = 0

                    if gamestate == 'free':
                        # Player movements
                        if (event.key == keybindings['move north'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move north'][0][1])) or (event.key == keybindings['move north'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move north'][1][1])):
                            gamestate, logback, target, chosen = moveorattack(0, -1)
                            numchosen = False
                        if (event.key == keybindings['move south'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move south'][0][1])) or (event.key == keybindings['move south'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move south'][1][1])):
                            gamestate, logback, target, chosen = moveorattack(0, 1)
                            numchosen = False
                        if (event.key == keybindings['move west'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move west'][0][1])) or (event.key == keybindings['move west'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move west'][1][1])):
                            gamestate, logback, target, chosen = moveorattack(-1, 0)
                            numchosen = False
                        if (event.key == keybindings['move east'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move east'][0][1])) or (event.key == keybindings['move east'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move east'][1][1])):
                            gamestate, logback, target, chosen = moveorattack(1, 0)
                            numchosen = False
                        if (event.key == keybindings['move northwest'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northwest'][0][1])) or (event.key == keybindings['move northwest'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northwest'][1][1])):
                            gamestate, logback, target, chosen = moveorattack(-1, -1)
                            numchosen = False
                        if (event.key == keybindings['move northeast'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northeast'][0][1])) or (event.key == keybindings['move northeast'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northeast'][1][1])):
                            gamestate, logback, target, chosen = moveorattack(1, -1)
                            numchosen = False
                        if (event.key == keybindings['move southwest'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southwest'][0][1])) or (event.key == keybindings['move southwest'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southwest'][1][1])):
                            gamestate, logback, target, chosen = moveorattack(-1, 1)
                            numchosen = False
                        if (event.key == keybindings['move southeast'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southeast'][0][1])) or (event.key == keybindings['move southeast'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southeast'][1][1])):
                            gamestate, logback, target, chosen = moveorattack(1, 1)
                            numchosen = False

                        if (event.key == keybindings['wait'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['wait'][0][1])) or (event.key == keybindings['wait'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['wait'][1][1])):
                            updatetime(1)
                            if not player.dying():
                                player.log().append('You waited a second.')
                                detecthiddenitems()
                            logback = 0
                            player.previousaction = ('wait',)

                        if (event.key == keybindings['repeat last attack'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['repeat last attack'][0][1])) or (event.key == keybindings['repeat last attack'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['repeat last attack'][1][1])):
                            if lastattack != None:
                                target, selected, selectedattack = lastattack
                                if not target.dead and abs(target.x - player.x) <= 1 and abs(target.y - player.y) <= 1 and selected in target.bodyparts and not selected.destroyed() and selectedattack in player.attackslist():
                                    secondlastattack = lastattack
                                    if player.previousaction[0] == 'fight' and player.previousaction[1] == selectedattack.weapon and player.previousaction[2] == selected:
                                        repetitionmultiplier = 1.5
                                    else:
                                        repetitionmultiplier = 1
                                    logback = 0
                                    gamestate = 'free'
                                    numchosen = False
                                    updatetime(selectedattack[6] * repetitionmultiplier * (1 + player.slowed()))
                                    if not player.dying():
                                        if not target.dead:
                                            player.fight(target, selected, selectedattack)
                                            player.previousaction = ('fight', selectedattack.weapon, selected)
                                        else:
                                            player.log().append('The ' + target.name + ' is already dead.')
                                            player.previousaction = ('wait',)
                                        detecthiddenitems()
                                    logback = 0
                                else:
                                    player.log().append('Cannot repeat that attack now.')
                                    logback = 0
                                    gamestate = 'free'
                            else:
                                player.log().append('No attack to repeat.')
                                logback = 0
                                gamestate = 'free'
                                

                        if (event.key == keybindings['repeat second last attack'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['repeat second last attack'][0][1])) or (event.key == keybindings['repeat second last attack'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['repeat second last attack'][1][1])):
                            if secondlastattack != None:
                                target, selected, selectedattack = secondlastattack
                                if not target.dead and abs(target.x - player.x) <= 1 and abs(target.y - player.y) <= 1 and selected in target.bodyparts and not selected.destroyed() and selectedattack in player.attackslist():
                                    secondlastattack = lastattack
                                    lastattack = (target, selected, selectedattack)
                                    if player.previousaction[0] == 'fight' and player.previousaction[1] == selectedattack.weapon and player.previousaction[2] == selected:
                                        repetitionmultiplier = 1.5
                                    else:
                                        repetitionmultiplier = 1
                                    logback = 0
                                    gamestate = 'free'
                                    numchosen = False
                                    updatetime(selectedattack[6] * repetitionmultiplier * (1 + player.slowed()))
                                    if not player.dying():
                                        if not target.dead:
                                            player.fight(target, selected, selectedattack)
                                            player.previousaction = ('fight', selectedattack.weapon, selected)
                                        else:
                                            player.log().append('The ' + target.name + ' is already dead.')
                                            player.previousaction = ('wait',)
                                        detecthiddenitems()
                                    logback = 0
                                else:
                                    player.log().append('Cannot repeat that attack now.')
                                    logback = 0
                                    gamestate = 'free'
                            else:
                                player.log().append('No attack to repeat.')
                                logback = 0
                                gamestate = 'free'

                        if (event.key == keybindings['go down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['go down'][0][1])) or (event.key == keybindings['go down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['go down'][1][1])):
                            if (player.x, player.y) != cave.stairsdowncoords:
                                player.log().append("You can't go down here!")
                                logback = 0
                            else:
                                if cave_i == numlevels - 1:
                                    player.log().append("Lower levels not yet implemented!")
                                    player.log().append("You won the current alpha!")
                                    player.log().append("Congratulations!")
                                    player.log().append("Press escape to end.")
                                    gamestate = 'win'
                                    numchosen = False
                                    if file_exists('highscores.pickle'):
                                        with open('highscores.pickle', 'rb') as f:
                                            highscores = pickle.load(f)
                                    else:
                                        highscores = []
                                    highscores.append((player.xp, player.individualname, 'won the game!'))
                                    with open('highscores.pickle', 'wb') as f:
                                        pickle.dump(highscores, f)
                                    logback = 0
                                else:
                                    cave_i += 1
                                    cave.creatures.remove(player)
                                    cave = caves[cave_i]
                                    cave.creatures.append(player)
                                    player.world = cave
                                    player.world_i = cave_i
                                    if player.max_world_i < cave_i:
                                        player.max_world_i = cave_i
                                        player.xp += 1000
                                    player.x = cave.stairsupcoords[0]
                                    player.y = cave.stairsupcoords[1]
                                    player.log().append('You went down the stairs.')
                                    detecthiddenitems()
                                    player.previousaction = ('move',)
                                    logback = 0

                        if (event.key == keybindings['go up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['go up'][0][1])) or (event.key == keybindings['go up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['go up'][1][1])):
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
                                    detecthiddenitems()
                                    player.previousaction = ('move',)
                                    logback = 0

                        if (event.key == keybindings['look'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['look'][0][1])) or (event.key == keybindings['look'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['look'][1][1])):
                            gamestate = 'look'
                            numchosen = False
                            lookx = player.x
                            looky = player.y

                        if (event.key == keybindings['mine'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['mine'][0][1])) or (event.key == keybindings['mine'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['mine'][1][1])):
                            if player.minespeed() > 0:
                                gamestate = 'mine'
                                numchosen = False
                            else:
                                player.log().append('You lack the tools or appendages to mine.')
                                logback = 0

                        # Items
                        if (event.key == keybindings['pick up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['pick up'][0][1])) or (event.key == keybindings['pick up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['pick up'][1][1])):
                            picklist = [it.pickableinstance() for it in cave.items if abs(it.x - player.x) <= 1 and abs(it.y - player.y) <= 1 and (it in player.itemsseen() or not it.hidden)]
                            torchdistance = np.inf
                            torchx = torchy = 0
                            for dx in [-1, 0, 1]:
                                for dy in [-1, 0, 1]:
                                    if cave.campfires[player.x+dx, player.y+dy] and np.sqrt(dx**2+dy**2) < torchdistance:
                                        torchdistance = np.sqrt(dx**2+dy**2)
                                        torchx = player.x+dx
                                        torchy = player.y+dy
                            if torchdistance < np.inf:
                                picklist.append(item.Torch(None, torchx, torchy))
                            if len(picklist) == 0:
                                player.log().append('Nothing to pick up here.')
                                logback = 0
                            elif len(picklist) == 1:
                                distance = np.sqrt((player.x - picklist[0].x)**2 + (player.y - picklist[0].y)**2)
                                updatetime(0.5 * (1 + distance) * (1 + player.slowed()))
                                if not player.dying():
                                    it = picklist[0]
                                    if it.owner != None:
                                        it.owner.remove(it)
                                    player.inventory.append(it)
                                    it.owner = player.inventory
                                    player.log().append('You picked up the ' + it.name + '.')
                                    detecthiddenitems()
                                    player.previousaction = ('pick',)
                                    logback = 0
                            else:
                                gamestate = 'pick'
                                logback = len(picklist) - logheight + 1
                                chosen = 0
                                numchosen = False

                        if (event.key == keybindings['drop'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['drop'][0][1])) or (event.key == keybindings['drop'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['drop'][1][1])):
                            if len(player.inventory) > 0:
                                gamestate = 'drop'
                                logback = len(player.inventory) - logheight + 1
                                chosen = 0
                                numchosen = False
                            else:
                                player.log().append('You have nothing to drop!')

                        if (event.key == keybindings['inventory'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['inventory'][0][1])) or (event.key == keybindings['inventory'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['inventory'][1][1])):
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

                        if (event.key == keybindings['information'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['information'][0][1])) or (event.key == keybindings['information'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['information'][1][1])):
                            itemlist = player.inventory + [part.wielded[0] for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0] + [it[0] for part in player.bodyparts for it in part.worn.values() if len(it) > 0] + player.bodyparts
                            gamestate = 'information'
                            logback = len(itemlist) - logheight + 1
                            chosen = 0
                            numchosen = False

                        if (event.key == keybindings['consume'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['consume'][0][1])) or (event.key == keybindings['consume'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['consume'][1][1])):
                            if len([item for item in player.inventory if item.consumable]) > 0:
                                gamestate = 'consume'
                                logback = len([item for item in player.inventory if item.consumable]) - logheight + 1
                                chosen = 0
                                numchosen = False
                            else:
                                player.log().append("You don't have anything to consume.")
                                logback = 0

                        if (event.key == keybindings['cook'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['cook'][0][1])) or (event.key == keybindings['cook'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['cook'][1][1])):
                            campfiresnear = False
                            for x in range(player.x-1, player.x+2):
                                for y in range(player.y-1, player.y+2):
                                    if cave.campfires[x, y]:
                                        campfiresnear = True
                            if not campfiresnear:
                                player.log().append("You need a campfire for cooking.")
                                logback = 0
                            elif len([item for item in player.inventory if item.material == 'living flesh']) == 0:
                                player.log().append("You have nothing to cook.")
                                logback = 0
                            else:
                                gamestate = 'cook'
                                logback = len([item for item in player.inventory if item.material == 'living flesh']) - logheight + 1
                                chosen = 0
                                numchosen = False

                        if (event.key == keybindings['wield'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['wield'][0][1])) or (event.key == keybindings['wield'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['wield'][1][1])):
                            if len([item for item in player.inventory if item.wieldable]) > 0 and len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0]) > 0:
                                gamestate = 'wieldchooseitem'
                                logback = len([item for item in player.inventory if item.wieldable]) - logheight + 1
                                chosen = 0
                                numchosen = False
                            else:
                                player.log().append("You cannot wield anything.")
                                logback = 0

                        if (event.key == keybindings['wear'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['wear'][0][1])) or (event.key == keybindings['wear'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['wear'][1][1])):
                            if len([item for item in player.inventory if item.wearable]) > 0:
                                gamestate = 'wearchooseitem'
                                logback = len([item for item in player.inventory if item.wearable]) - logheight + 1
                                chosen = 0
                                numchosen = False
                            else:
                                player.log().append('You have nothing to wear.')
                                logback = 0

                        if (event.key == keybindings['unwield'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['unwield'][0][1])) or (event.key == keybindings['unwield'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['unwield'][1][1])):
                            if len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) > 0:
                                gamestate = 'unwield'
                                logback = len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) - logheight + 1
                                chosen = 0
                                numchosen = False
                            else:
                                player.log().append("You have nothing to unwield.")
                                logback = 0

                        if (event.key == keybindings['undress'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['undress'][0][1])) or (event.key == keybindings['undress'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['undress'][1][1])):
                            wornlist = [it[0] for part in player.bodyparts for it in part.worn.values() if len(it) > 0]
                            if len(wornlist) > 0:
                                gamestate = 'undress'
                                logback = len(wornlist) - logheight + 1
                                chosen = 0
                                numchosen = False
                            else:
                                player.log().append("You have nothing to undress.")
                                logback = 0

                        if (event.key == keybindings['throw'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['throw'][0][1])) or (event.key == keybindings['throw'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['throw'][1][1])):
                            if len(player.thrownattackslist()) > 0:
                                gamestate = 'throwchoosemissile'
                                logback = len(player.thrownattackslist()) - logheight + 1
                                chosen = 0
                                numchosen = False
                            else:
                                player.log().append("You cannot throw anything.")
                                logback = 0

                        # Stance:
                        if (event.key == keybindings['choose stance'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['choose stance'][0][1])) or (event.key == keybindings['choose stance'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['choose stance'][1][1])):
                                gamestate = 'choosestance'
                                logback = len(player.stancesknown()) - logheight + 1
                                chosen = 0
                                numchosen = False

                        # Praying:
                        if (event.key == keybindings['pray'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['pray'][0][1])) or (event.key == keybindings['pray'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['pray'][1][1])):
                            gamestate = 'pray'
                            logback = min(7, len(player.godsknown()) + 1) - logheight + 1
                            chosen = 0
                            numchosen = False

                        # Frightening:
                        if (event.key == keybindings['frighten'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['frighten'][0][1])) or (event.key == keybindings['frighten'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['frighten'][1][1])):
                            if player.scariness() == 0:
                                player.log().append('You are not scary enough to frighten anything.')
                                logback = 0
                            else:
                                updatetime(0.75)
                                if not player.dying():
                                    player.frighten()
                                    detecthiddenitems()
                                    player.previousaction = ('frighten',)
                                    logback = 0

                        # Bodyparts:
                        if (event.key == keybindings['list bodyparts'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list bodyparts'][0][1])) or (event.key == keybindings['list bodyparts'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list bodyparts'][1][1])):
                            player.log().append('The parts of your body:')
                            for part in player.bodyparts:
                                player.log().append('  - a ' + part.name + ' (hp: ' + repr(part.hp()) + '/' + repr(part.maxhp) + ', ' + repr(part.bottomheight()) + ' to ' + repr(part.topheight()) + ' cm from ground)')
                            if len(player.bodyparts) > logheight - 1 and len(player.log()) > 1:
                                logback = len(player.bodyparts) - logheight + 1
                            else:
                                logback = 0

                        if (event.key == keybindings['choose bodyparts'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['choose bodyparts'][0][1])) or (event.key == keybindings['choose bodyparts'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['choose bodyparts'][1][1])):
                            #gamestate = 'choosetorso'
                            #len([part for part in player.bodyparts if 'torso' in part.categories and not part.destroyed()] + [it for it in player.inventory if it.bodypart and 'torso' in it.categories and not it.destroyed()]) - logheight + 1
                            #chosen = 0
                            gamestate = 'choosebodypartconnection'
                            bodypartcandidates = listwithowner([part for part in player.bodyparts], player)
                            connectioncandidates = [None] + [(connection, connection.child) for part in bodypartcandidates for connection in part.childconnections.values()] + [None]
                            logback = len(connectioncandidates) - logheight + 1
                            chosen = 0
                            numchosen = False
                            bodypartchoosingtime = 0

                        # Help
                        if (event.key == keybindings['help'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['help'][0][1])) or (event.key == keybindings['help'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['help'][1][1])):
                            player.log().append('Default keybindings (change in options):')
                            player.log().append('  - page up, page down, home, end: explore the log')
                            player.log().append('  - arrows or numpad: move or attack')
                            player.log().append('  - period or numpad 5: wait a moment')
                            player.log().append('  - < or >: go up or down')
                            player.log().append('  - r: repeat last attack')
                            player.log().append('  - R: repeat second last attack')
                            player.log().append('  - l: look')
                            player.log().append('  - m: mine')
                            player.log().append('  - comma: pick up an item')
                            player.log().append('  - d: drop an item')
                            player.log().append('  - t: throw something')
                            player.log().append('  - i: check your inventory')
                            player.log().append('  - I: information on your items and bodyparts')
                            player.log().append('  - b: list your body parts')
                            player.log().append('  - B: choose your body parts')
                            player.log().append('  - c: consume')
                            player.log().append('  - C: cook')
                            player.log().append('  - w: wield an item')
                            player.log().append('  - u: unwield an item')
                            player.log().append('  - W: wear an item')
                            player.log().append('  - U: undress an item')
                            player.log().append('  - s: choose stance')
                            player.log().append('  - p: pray')
                            player.log().append('  - f: frighten')
                            player.log().append('  - h: this list of commands')
                            if len(player.log()) > 1: # Prevent crash if the player is brainless
                                logback = 18 # Increase when adding commands

                        # log scrolling
                        if (event.key == keybindings['log up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log up'][0][1])) or (event.key == keybindings['log up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log up'][1][1])):
                            if len(player.log()) >= logheight:
                                logback = min(logback+1, len(player.log())-logheight)
                        if (event.key == keybindings['log down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log down'][0][1])) or (event.key == keybindings['log down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log down'][1][1])):
                            logback = max(logback-1, 0)
                        if (event.key == keybindings['log start'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log start'][0][1])) or (event.key == keybindings['log start'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log start'][1][1])):
                            if len(player.log()) >= logheight:
                                logback = len(player.log())-logheight
                        if (event.key == keybindings['log end'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log end'][0][1])) or (event.key == keybindings['log end'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log end'][1][1])):
                            logback = 0

                        if event.key == pygame.locals.K_ESCAPE:
                            with open('savegame.pickle', 'wb') as f:
                                pickle.dump((caves, player, gods), f)
                            gamegoeson = False

                    elif gamestate == 'look':
                        fovmap = fov(cave.walls, player.x, player.y, player.sight())
                        if (event.key == keybindings['move north'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move north'][0][1])) or (event.key == keybindings['move north'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move north'][1][1])):
                            if fovmap[lookx, looky-1]:
                                looky -= 1
                        if (event.key == keybindings['move south'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move south'][0][1])) or (event.key == keybindings['move south'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move south'][1][1])):
                            if fovmap[lookx, looky+1]:
                                looky += 1
                        if (event.key == keybindings['move west'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move west'][0][1])) or (event.key == keybindings['move west'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move west'][1][1])):
                            if fovmap[lookx-1, looky]:
                                lookx -= 1
                        if (event.key == keybindings['move east'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move east'][0][1])) or (event.key == keybindings['move east'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move east'][1][1])):
                            if fovmap[lookx+1, looky]:
                                lookx += 1
                        if (event.key == keybindings['move northwest'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northwest'][0][1])) or (event.key == keybindings['move northwest'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northwest'][1][1])):
                            if fovmap[lookx-1, looky-1]:
                                lookx -= 1
                                looky -= 1
                        if (event.key == keybindings['move northeast'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northeast'][0][1])) or (event.key == keybindings['move northeast'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northeast'][1][1])):
                            if fovmap[lookx+1, looky-1]:
                                lookx += 1
                                looky -= 1
                        if (event.key == keybindings['move southwest'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southwest'][0][1])) or (event.key == keybindings['move southwest'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southwest'][1][1])):
                            if fovmap[lookx-1, looky+1]:
                                lookx -= 1
                                looky += 1
                        if (event.key == keybindings['move southeast'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southeast'][0][1])) or (event.key == keybindings['move southeast'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southeast'][1][1])):
                            if fovmap[lookx+1, looky+1]:
                                lookx += 1
                                looky += 1
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'mine':
                        if (event.key == keybindings['move north'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move north'][0][1])) or (event.key == keybindings['move north'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move north'][1][1])):
                            gamestate, logback = mine(0, -1)
                        if (event.key == keybindings['move south'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move south'][0][1])) or (event.key == keybindings['move south'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move south'][1][1])):
                            gamestate, logback = mine(0, 1)
                        if (event.key == keybindings['move west'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move west'][0][1])) or (event.key == keybindings['move west'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move west'][1][1])):
                            gamestate, logback = mine(-1, 0)
                        if (event.key == keybindings['move east'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move east'][0][1])) or (event.key == keybindings['move east'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move east'][1][1])):
                            gamestate, logback = mine(1, 0)
                        if (event.key == keybindings['move northwest'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northwest'][0][1])) or (event.key == keybindings['move northwest'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northwest'][1][1])):
                            gamestate, logback = mine(-1, -1)
                        if (event.key == keybindings['move northeast'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northeast'][0][1])) or (event.key == keybindings['move northeast'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northeast'][1][1])):
                            gamestate, logback = mine(1, -1)
                        if (event.key == keybindings['move southwest'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southwest'][0][1])) or (event.key == keybindings['move southwest'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southwest'][1][1])):
                            gamestate, logback = mine(-1, 1)
                        if (event.key == keybindings['move southeast'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southeast'][0][1])) or (event.key == keybindings['move southeast'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southeast'][1][1])):
                            gamestate, logback = mine(1, 1)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'pick':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(picklist) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(picklist)-1, chosen+1)
                            if chosen == len(picklist) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(picklist):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            distance = np.sqrt((player.x - picklist[chosen].x)**2 + (player.y - picklist[chosen].y)**2)
                            updatetime(0.5 * (1 + distance) * (1 + player.slowed()))
                            if not player.dying():
                                selected = picklist[chosen]
                                if selected.owner != None:
                                    selected.owner.remove(selected)
                                selected.owner = player.inventory
                                player.inventory.append(selected)
                                player.log().append('You picked up the ' + selected.name + '.')
                                detecthiddenitems()
                                player.previousaction = ('pick',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'drop':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(player.inventory) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(player.inventory)-1, chosen+1)
                            if chosen == len(player.inventory) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(player.inventory):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            updatetime(0.5 * (1 + player.slowed()))
                            if not player.dying():
                                selected = player.inventory[chosen]
                                selected.owner = cave.items
                                cave.items.append(selected)
                                player.inventory.remove(selected)
                                selected.x = player.x
                                selected.y = player.y
                                player.log().append('You dropped the ' + selected.name + '.')
                                detecthiddenitems()
                                player.previousaction = ('drop',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'information':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(itemlist) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(itemlist)-1, chosen+1)
                            if chosen == len(itemlist) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(itemlist):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            selected = itemlist[chosen]
                            player.log().append('Information about the ' + selected.name + ': ' + selected.info())
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'consume':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len([item for item in player.inventory if item.consumable]) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len([item for item in player.inventory if item.consumable])-1, chosen+1)
                            if chosen == len([item for item in player.inventory if item.consumable]) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len([item for item in player.inventory if item.consumable]):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            updatetime(1 * (1 + player.slowed()))
                            if not player.dying():
                                selected = [item for item in player.inventory if item.consumable][chosen]
                                if selected.cure:
                                    if not selected.curetype in player.curesknown():
                                        player.curesknown().append(selected.curetype)                                    
                                    player.log().append('You consumed a ' + selected.name + '.')
                                    selected.consume(player)
                                    player.previousaction = ('consume',)
                                    logback = 0
                                    if player.dying():
                                        player.causeofdeath = ('consumption', selected)
                                elif selected.edible:
                                    stomachs = [part for part in player.bodyparts if 'stomach' in part.categories and not part.destroyed()]
                                    if len(stomachs) > 0:
                                        stomach = stomachs[0]
                                        if int(player.hunger) == 0:
                                            player.log().append('You are already satiated.')
                                        elif stomach.foodprocessing[selected.material][0] == 1:
                                            selected.consume(player, stomach.foodprocessing[selected.material][1])
                                            if stomach.foodprocessing[selected.material][2] != None:
                                                player.log().append(stomach.foodprocessing[selected.material][2])
                                        elif stomach.foodprocessing[selected.material][0] == 0 and player.starving():
                                            selected.consume(player, stomach.foodprocessing[selected.material][1])
                                            if np.random.rand() > 0.2:
                                                if stomach.foodprocessing[selected.material][2] != None:
                                                    player.log().append(stomach.foodprocessing[selected.material][2])
                                            else:
                                                player.log().append('You got food poisoning and started vomiting!')
                                                player.vomitclock += np.random.rand()*20
                                        elif stomach.foodprocessing[selected.material][0] == 0:
                                            player.log().append('Your stomach doesn\'t tolerate ' + selected.material + ' very well, and you are not desperate enough to try.')
                                        elif stomach.foodprocessing[selected.material][0] == -1:
                                            player.log().append('Your stomach doesn\'t tolerate ' + selected.material + ' under any circumstances.')
                                    else:
                                        player.log().append('You have no stomach, so you cannot eat!')
                                    logback = 0
                                detecthiddenitems()
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'cook':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len([item for item in player.inventory if item.material == 'living flesh']) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len([item for item in player.inventory if item.material == 'living flesh'])-1, chosen+1)
                            if chosen == len([item for item in player.inventory if item.material == 'living flesh']) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len([item for item in player.inventory if item.material == 'living flesh']):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            updatetime(5 * (1 + player.slowed()))
                            if not player.dying():
                                selected = [item for item in player.inventory if item.material == 'living flesh'][chosen]
                                player.inventory.remove(selected)
                                newname = 'roast ' + selected.name
                                if newname[-11:] == ' [UNUSABLE]':
                                    newname = newname[:-11]
                                item.Food(player.inventory, 0, 0, newname, selected.char, ((97+selected.color[0])//2, (23+selected.color[1])//2, (23+selected.color[2])//2), selected.maxhp, 'cooked meat', selected.weight)
                                player.log().append('You roasted the ' + selected.name + '.')
                                detecthiddenitems()
                                player.previousaction = ('cook',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'wieldchooseitem':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len([item for item in player.inventory if item.wieldable]) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len([item for item in player.inventory if item.wieldable])-1, chosen+1)
                            if chosen == len([item for item in player.inventory if item.wieldable]) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len([item for item in player.inventory if item.wieldable]):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            selecteditem = [item for item in player.inventory if item.wieldable][chosen]
                            logback = len([part for part in player.bodyparts if part.capableofwielding]) - logheight + 1
                            gamestate = 'wieldchoosebodypart'
                            numchosen = False
                            chosen = 0
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'wieldchoosebodypart':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()]) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()])-1, chosen+1)
                            if chosen == len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()]) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()]):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            updatetime(1 * (1 + player.slowed()))
                            if not player.dying():
                                selected = [part for part in player.bodyparts if part.capableofwielding and len(part.wielded) == 0 and not part.destroyed()][chosen]
                                player.inventory.remove(selecteditem)
                                selected.wielded.append(selecteditem)
                                selecteditem.owner = selected.wielded
                                player.log().append('You are now wielding the ' + selecteditem.name + ' in your ' + selected.wearwieldname() + '.')
                                detecthiddenitems()
                                player.previousaction = ('wield',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'unwield':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0])-1, chosen+1)
                            if chosen == len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len([part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0]):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            updatetime(1 * (1 + player.slowed()))
                            if not player.dying():
                                part = [part for part in player.bodyparts if part.capableofwielding and len(part.wielded) > 0][chosen]
                                selected = part.wielded[0]
                                part.wielded.remove(selected)
                                player.inventory.append(selected)
                                selected.owner = player.inventory
                                player.log().append('You removed the ' + selected.name + ' from your ' + part.wearwieldname() + '.')
                                detecthiddenitems()
                                player.previousaction = ('unwield',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'wearchooseitem':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len([item for item in player.inventory if item.wearable]) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len([item for item in player.inventory if item.wearable])-1, chosen+1)
                            if chosen == len([item for item in player.inventory if item.wearable]) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len([item for item in player.inventory if item.wearable]):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            selecteditem = [item for item in player.inventory if item.wearable][chosen]
                            partlist = [part for part in player.bodyparts if selecteditem.wearcategory in part.worn.keys() and len(part.worn[selecteditem.wearcategory]) == 0 and not part.destroyed()]
                            if len(partlist) > 0:
                                logback = len(partlist) - logheight + 1
                                gamestate = 'wearchoosebodypart'
                                chosen = 0
                                numchosen = False
                            else:
                                player.log().append('You have no free ' + selecteditem.wearcategory + ' slot.')
                                logback = 0
                                gamestate = 'free'
                                numchosen = False
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'wearchoosebodypart':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(partlist) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(partlist)-1, chosen+1)
                            if chosen == len(partlist) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(partlist):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            updatetime(1 * (1 + player.slowed()))
                            if not player.dying():
                                selected = partlist[chosen]
                                player.inventory.remove(selecteditem)
                                selected.worn[selecteditem.wearcategory].append(selecteditem)
                                selecteditem.owner = selected.worn[selecteditem.wearcategory]
                                player.log().append('You are now wearing the ' + selecteditem.name + ' on your ' + selected.wearwieldname() + '.')
                                detecthiddenitems()
                                player.previousaction = ('wear',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'undress':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(wornlist) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(wornlist)-1, chosen+1)
                            if chosen == len(wornlist) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(wornlist):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            updatetime(1 * (1 + player.slowed()))
                            if not player.dying():
                                selected = wornlist[chosen]
                                partname = selected.owner.owner.wearwieldname()
                                selected.owner.remove(selected)
                                player.inventory.append(selected)
                                selected.owner = player.inventory
                                player.log().append('You removed the ' + selected.name + ' from your ' + partname + '.')
                                detecthiddenitems()
                                player.previousaction = ('undress',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'chooseattack':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(player.attackslist()) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(player.attackslist())-1, chosen+1)
                            if chosen == len(player.attackslist()) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(player.attackslist()):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            selectedattack = player.attackslist()[chosen]
                            gamestate = 'choosetargetbodypart'
                            numchosen = False
                            logback = len([part for part in target.bodyparts if not part.destroyed()]) - logheight + 1
                            chosen = 0
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'choosetargetbodypart':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len([part for part in target.bodyparts if not part.destroyed()]) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len([part for part in target.bodyparts if not part.destroyed()])-1, chosen+1)
                            if chosen == len([part for part in target.bodyparts if not part.destroyed()]) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len([part for part in target.bodyparts if not part.destroyed()]):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            selected = [part for part in target.bodyparts if not part.destroyed()][chosen]
                            secondlastattack = lastattack
                            lastattack = (target, selected, selectedattack)
                            if player.previousaction[0] == 'fight' and player.previousaction[1] == selectedattack.weapon and player.previousaction[2] == selected:
                                repetitionmultiplier = 1.5
                            else:
                                repetitionmultiplier = 1
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            updatetime(selectedattack[6] * repetitionmultiplier * (1 + player.slowed()))
                            if not player.dying():
                                if not target.dead:
                                    player.fight(target, selected, selectedattack)
                                    player.previousaction = ('fight', selectedattack.weapon, selected)
                                else:
                                    player.log().append('The ' + target.name + ' is already dead.')
                                    player.previousaction = ('wait',)
                                detecthiddenitems()
                            logback = 0
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'throwchoosemissile':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(player.thrownattackslist()) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(player.thrownattackslist())-1, chosen+1)
                            if chosen == len(player.thrownattackslist()) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(player.thrownattackslist()):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            selectedattack = player.thrownattackslist()[chosen]
                            gamestate = 'throwchoosetarget'
                            numchosen = False
                            logback = 0
                            chosen = 0
                            lookx = player.x
                            looky = player.y
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'throwchoosetarget':
                        fovmap = fov(cave.walls, player.x, player.y, player.sight())
                        fovmap2 = fov(cave.walls, player.x, player.y, selectedattack.weapon.throwrange, nowalls=True)
                        if (event.key == keybindings['move north'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move north'][0][1])) or (event.key == keybindings['move north'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move north'][1][1])):
                            if fovmap[lookx, looky-1] and fovmap2[lookx, looky-1]:
                                looky -= 1
                        if (event.key == keybindings['move south'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move south'][0][1])) or (event.key == keybindings['move south'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move south'][1][1])):
                            if fovmap[lookx, looky+1] and fovmap2[lookx, looky+1]:
                                looky += 1
                        if (event.key == keybindings['move west'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move west'][0][1])) or (event.key == keybindings['move west'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move west'][1][1])):
                            if fovmap[lookx-1, looky] and fovmap2[lookx-1, looky]:
                                lookx -= 1
                        if (event.key == keybindings['move east'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move east'][0][1])) or (event.key == keybindings['move east'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move east'][1][1])):
                            if fovmap[lookx+1, looky] and fovmap2[lookx+1, looky]:
                                lookx += 1
                        if (event.key == keybindings['move northwest'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northwest'][0][1])) or (event.key == keybindings['move northwest'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northwest'][1][1])):
                            if fovmap[lookx-1, looky-1] and fovmap2[lookx-1, looky-1]:
                                lookx -= 1
                                looky -= 1
                        if (event.key == keybindings['move northeast'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northeast'][0][1])) or (event.key == keybindings['move northeast'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move northeast'][1][1])):
                            if fovmap[lookx+1, looky-1] and fovmap2[lookx+1, looky-1]:
                                lookx += 1
                                looky -= 1
                        if (event.key == keybindings['move southwest'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southwest'][0][1])) or (event.key == keybindings['move southwest'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southwest'][1][1])):
                            if fovmap[lookx-1, looky+1] and fovmap2[lookx-1, looky+1]:
                                lookx -= 1
                                looky += 1
                        if (event.key == keybindings['move southeast'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southeast'][0][1])) or (event.key == keybindings['move southeast'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['move southeast'][1][1])):
                            if fovmap[lookx+1, looky+1] and fovmap2[lookx+1, looky+1]:
                                lookx += 1
                                looky += 1
                        if (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            target = None
                            targetingcreature = False
                            targetcoords = (lookx, looky)
                            for creat in cave.creatures:
                                if creat.x == lookx and creat.y == looky and creat != player:
                                    target = creat
                                    targetingcreature = True
                            if targetingcreature:
                                gamestate = 'throwchoosetargetbodypart'
                                logback = len([part for part in target.bodyparts if not part.destroyed()]) - logheight + 1
                            else:
                                gamestate = 'throwchooselimb'
                                limblist = [part for part in player.bodyparts if part.capableofwielding and part.capableofthrowing and len(part.wielded) == 0]
                                if selectedattack.weapon.owner != player.inventory:
                                    limblist = [selectedattack.weapon.owner.owner] + limblist
                                logback = len(limblist) - logheight + 1
                            numchosen = False
                            chosen = 0
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'throwchoosetargetbodypart':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len([part for part in target.bodyparts if not part.destroyed()]) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len([part for part in target.bodyparts if not part.destroyed()])-1, chosen+1)
                            if chosen == len([part for part in target.bodyparts if not part.destroyed()]) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len([part for part in target.bodyparts if not part.destroyed()]):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            selectedbodypart = [part for part in target.bodyparts if not part.destroyed()][chosen]
                            gamestate = 'throwchooselimb'
                            limblist = [part for part in player.bodyparts if part.capableofwielding and part.capableofthrowing and len(part.wielded) == 0]
                            if selectedattack.weapon.owner != player.inventory:
                                limblist = [selectedattack.weapon.owner.owner] + limblist
                            logback = len([part for part in target.bodyparts if not part.destroyed()]) - logheight + 1
                            numchosen = False
                            chosen = 0
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'throwchooselimb':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(limblist) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(limblist)-1, chosen+1)
                            if chosen == len(limblist) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(limblist):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            selected = limblist[chosen]
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            wornlist = [it[0] for part in player.bodyparts for it in part.worn.values() if len(it) > 0]
                            notwielded = selectedattack.weapon.owner == player.inventory and not np.any([hasattr(it, 'quickdraw') and it.quickdraw for it in wornlist])
                            updatetime((1/selected.throwspeed + notwielded) * (1 + player.slowed()))
                            if not player.dying():
                                if target != None and not target.dead:
                                    player.throwatenemy(target, selectedbodypart, selectedattack, selected)
                                    player.previousaction = ('throw',)
                                else:
                                    player.throwatsquare(targetcoords[0], targetcoords[1], selectedattack.weapon, selected)
                                    player.previousaction = ('throw',)
                                detecthiddenitems()
                            logback = 0
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'choosebodypartconnection':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(connectioncandidates) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(connectioncandidates)-1, chosen+1)
                            if chosen == len(connectioncandidates) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(connectioncandidates):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            if connectioncandidates[chosen] != None:
                                connection = connectioncandidates[chosen][0]
                                connectedpart = connectioncandidates[chosen][1]
                            else:
                                connection = None
                                connectedpart = [part for part in bodypartcandidates if 'torso' in part.categories][0]  # I think this could be just bodypartcandidates[0], but just in case...
                            if chosen < len(connectioncandidates)-1:
                                if connection != None:
                                    connectionname = list(connection.parent.childconnections.keys())[list(connection.parent.childconnections.values()).index(connection)]
                                    partslist = [part for part in player.bodyparts if np.any([category in part.categories for category in connection.categories]) and part.usable and not part.destroyed() and (part == connectedpart or not part in bodypartcandidates)] + [it for it in player.inventory if it.bodypart and np.any([category in it.categories for category in connection.categories]) and it.usable and not it.destroyed() and (it == connectedpart or not it in bodypartcandidates)]
                                    if not connection.vital:
                                        partslist.append(None)
                                else:
                                    connectionname = 'torso'
                                    partslist = [part for part in player.bodyparts if 'torso' in part.categories and part.usable and not part.destroyed()] + [it for it in player.inventory if it.bodypart and 'torso' in it.categories and it.usable and not it.destroyed()]
                                gamestate = 'choosebodypart'
                                logback = len(partslist) - logheight + 1
                                chosen = 0
                                numchosen = False
                            elif len([connection for connection in connectioncandidates if connection != None and connection[0].vital and connection[1] == None]) == 0:
                                logback = 0
                                gamestate = 'free'
                                numchosen = False
                                updatetime(bodypartchoosingtime * (1 + player.slowed()))
                                if not player.dying():
                                    for it in [it[0] for part in player.bodyparts for it in part.worn.values() if not part in bodypartcandidates and len(it) > 0]:
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
                                        if part.capableofwielding and not part in bodypartcandidates:
                                            for it in part.wielded:
                                                it.owner = player.inventory
                                                player.inventory.append(it)
                                                part.wielded.remove(it)
                                    player.bodyparts = bodypartcandidates
                                    player.torso = player.bodyparts[0]
                                    for part in player.bodyparts:
                                        if part in player.inventory:
                                            player.inventory.remove(part)
                                        part.owner = player.bodyparts
                                    for connection, part in connectioncandidates[1:-1]:
                                        if part != None:
                                            connection.connect(part)
                                    player.log().append('You have selected your bodyparts.')
                                    detecthiddenitems()
                                    player.previousaction = ('choosebody',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'choosebodypart':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(partslist) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(partslist)-1, chosen+1)
                            if chosen == len(partslist) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(partslist):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            selected = partslist[chosen]
                            if selected != connectedpart:
                                connectioncandidates = connectioncandidates[:-1]
                                if connection != None:
                                    connectioncandidates.remove((connection, connectedpart))
                                if connectedpart != None:
                                    bodypartcandidates.remove(connectedpart)
                                    connectionstoremove = [cn for cn in connectioncandidates if cn != None and cn[0].parent == connectedpart]
                                    while len(connectionstoremove) > 0:
                                        cnn = connectionstoremove[0]
                                        connectioncandidates.remove(cnn)
                                        bodypartcandidates.remove(cnn[1])
                                        connectionstoremove.remove(cnn)
                                        connectionstoremove += [cn for cn in connectioncandidates if cn != None and cn[0].parent == cnn[1]]
                                if selected != None:
                                    bodypartcandidates.append(selected)
                                    for cn in selected.childconnections:
                                        connectioncandidates.append((selected.childconnections[cn], None))
                                if connection != None:
                                    connectioncandidates.append((connection, selected))
                                connectioncandidates.append(None)
                                bodypartchoosingtime += 1
                            logback = len(connectioncandidates) - logheight + 1
                            chosen = 0
                            gamestate = 'choosebodypartconnection'
                            numchosen = False
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = len(connectioncandidates) - logheight + 1
                            chosen = 0
                            gamestate = 'choosebodypartconnection'
                            numchosen = False

                    elif gamestate == 'choosestance':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == len(player.stancesknown()) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(len(player.stancesknown())-1, chosen+1)
                            if chosen == len(player.stancesknown()) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(player.stancesknown()):
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            updatetime(0.5)
                            if not player.dying():
                                selected = player.stancesknown()[chosen]
                                oldstance = player.stance
                                player.stance = selected
                                player.preferredstance = selected
                                if oldstance == 'flying' and player.stance != 'flying':
                                    for it in cave.items:
                                        if (it.x, it.y) == (player.x, player.y) and it.trap:
                                            part = player.approxfastestpart()
                                            if it in player.itemsseen() or not it.hidden:
                                                if np.random.rand() < part.carefulness:
                                                    player.log().append('You managed to land carefully and avoided the ' + it.name + '.')
                                                else:
                                                    it.entrap(player, part)
                                            else:
                                                it.entrap(player, part)
                                                player.itemsseen().append(it)
                                detecthiddenitems()
                                player.previousaction = ('choosestance',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'pray':
                        if (event.key == keybindings['list up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][0][1])) or (event.key == keybindings['list up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list up'][1][1])):
                            chosen = max(0, chosen-1)
                            if chosen == min(7, len(player.godsknown()) + 1) - logback - (logheight - 1) - 1:
                                logback += 1
                        if (event.key == keybindings['list down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][0][1])) or (event.key == keybindings['list down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list down'][1][1])):
                            chosen = min(min(7, len(player.godsknown()) + 1)-1, chosen+1)
                            if chosen == min(7, len(player.godsknown()) + 1) - logback:
                                logback -= 1
                        for i in range(10):
                            if event.key in numkeys[i] and i < len(player.godsknown()) + 1:
                                chosen = i
                                numchosen = True
                        if numchosen or (event.key == keybindings['list select'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][0][1])) or (event.key == keybindings['list select'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['list select'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False
                            updatetime(1)
                            if not player.dying():
                                if chosen < len(player.godsknown()):
                                    selected = player.godsknown()[chosen]
                                    player.pray(selected)
                                else:
                                    if np.random.rand() < 0.05:
                                        gd = np.random.choice([gd for gd in gods if not gd in player.godsknown()])
                                        player.log().append('You prayed, and someone answered!')
                                        player.godsknown().append(gd)
                                        player.log().append('You learn the ways of ' + gd.name + ', the ' + gd.faction + '-god of ' + gd.sin + '.')
                                        player.log().append(gd.pronoun.capitalize() + ' ' + gd.copula + ' a ' + gd.power + ' and ' + gd.attitude + ' god.')
                                        player.pray(gd)
                                    else:
                                        player.log().append('You prayed, but no one answered.')
                                detecthiddenitems()
                                player.previousaction = ('pray',)
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            logback = 0
                            gamestate = 'free'
                            numchosen = False

                    elif gamestate == 'dead' or gamestate == 'win':
                        if (event.key == keybindings['escape'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][0][1])) or (event.key == keybindings['escape'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['escape'][1][1])):
                            gamegoeson = False

                        # log scrolling
                        if (event.key == keybindings['log up'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log up'][0][1])) or (event.key == keybindings['log up'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log up'][1][1])):
                            if len(player.log()) >= logheight:
                                logback = min(logback+1, len(player.log())-logheight)
                        if (event.key == keybindings['log down'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log down'][0][1])) or (event.key == keybindings['log down'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log down'][1][1])):
                            logback = max(logback-1, 0)
                        if (event.key == keybindings['log start'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log start'][0][1])) or (event.key == keybindings['log start'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log start'][1][1])):
                            if len(player.log()) >= logheight:
                                logback = len(player.log())-logheight
                        if (event.key == keybindings['log end'][0][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log end'][0][1])) or (event.key == keybindings['log end'][1][0] and ((event.mod & pygame.KMOD_SHIFT) == keybindings['log end'][1][1])):
                            logback = 0

                    # Update window after any command or keypress
                    draw()
                if event.type == pygame.QUIT:
                    if gamestate != 'dead':
                        with open('savegame.pickle', 'wb') as f:
                            pickle.dump((caves, player, gods), f)
                    pygame.quit()
                    sys.exit()


        # Make sure the window is closed if the game crashes
        #except Exception as e:
        #    pygame.quit()
        #    sys.exit()
        #    raise e

    if gamestate == 'dead' or gamestate == 'win':
        halloffame()

def halloffame():
    cont = False
    while not cont:
        win.settint(0, 0, 0, (0, 0, mapwidth + hpbarwidth + hpmargin, mapheight + statuslines + logheight))
        for i in range(mapwidth + hpbarwidth + hpmargin):
            for j in range(mapheight + statuslines + logheight):
                win.putchars(' ', x=i, y=j, bgcolor='black')
        title = 'GOLEM HALL OF FAME'
        win.write(title, x=(mapwidth + hpbarwidth + hpmargin - len(title)) // 2, y=0, fgcolor=(255, 255, 255))
        if file_exists('highscores.pickle'):
            with open('highscores.pickle', 'rb') as f:
                highscores = pickle.load(f)
        else:
            highscores = []
        highscores_sorted = sorted(highscores, reverse=True)
        if len(highscores_sorted) > 0 and highscores_sorted.index(highscores[-1]) >=  mapheight + statuslines + logheight - 1:
            listlength = mapheight + statuslines + logheight - 3
            latestoutoftop = True
        else:
            listlength = min(len(highscores_sorted), mapheight + statuslines + logheight - 1)
            latestoutoftop = False
        for i in range(listlength):
            score = highscores_sorted[i]
            if score == highscores[-1]:
                fgcolor = (0, 255, 255)
            else:
                fgcolor = (255, 255, 255)
            win.write(repr(i+1), x=0, y = i+1, fgcolor=fgcolor, bgcolor=(0, 0, 0))
            win.write(repr(score[0]), x=5, y = i+1, fgcolor=fgcolor, bgcolor=(0, 0, 0))
            win.write(score[1] + ', ' + score[2], x=15, y = i+1, fgcolor=fgcolor, bgcolor=(0, 0, 0))
        if latestoutoftop:
            win.write('...', x=0, y=mapheight + statuslines + logheight - 2, fgcolor=(255, 255, 255), bgcolor=(0, 0, 0))
            i = highscores_sorted.index(highscores[-1])
            score = highscores[-1]
            fgcolor = (0, 255, 255)
            win.write(repr(i+1), x=0, y=mapheight + statuslines + logheight - 1, fgcolor=fgcolor, bgcolor=(0, 0, 0))
            win.write(repr(score[0]), x=5, y=mapheight + statuslines + logheight - 1, fgcolor=fgcolor, bgcolor=(0, 0, 0))
            win.write(score[1] + ', ' + score[2], x=15, y=mapheight + statuslines + logheight - 1, fgcolor=fgcolor, bgcolor=(0, 0, 0))
        win.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.locals.KEYDOWN:
                cont = True

def keybingsoptions():
    global keybindings
    cont = False
    selected = (0, 0)
    state = 0
    while not cont:
        for i in range(mapwidth + hpbarwidth + hpmargin):
            for j in range(mapheight + statuslines + logheight):
                win.putchars(' ', x=i, y=j, bgcolor='black')
        text = 'KEYBINDINGS'
        win.write(text, x=(mapwidth + hpbarwidth + hpmargin - len(text)) // 2, y=0, fgcolor=(255, 255, 255))
        text = 'Arrow keys, return, and escape are reserved keys. Left shift can be used as a modifier.'
        win.write(text, x=(mapwidth + hpbarwidth + hpmargin - len(text)) // 2, y=1, fgcolor=(255, 255, 255))
        text = 'Select with arrows, edit with return.'
        win.write(text, x=(mapwidth + hpbarwidth + hpmargin - len(text)) // 2, y=2, fgcolor=(255, 255, 255))
        longest = max([len(command) for command in keybindings])
        for i in range(len(keybindings)):
            if selected[0] == i:
                fgcolor = (0, 0, 0)
                bgcolor = (255, 255, 255)
            else:
                fgcolor = (255, 255, 255)
                bgcolor = (0, 0, 0)
            win.write(list(keybindings.keys())[i], x=15+longest-len(list(keybindings.keys())[i]), y=i+4, fgcolor=fgcolor, bgcolor=bgcolor)
            for j in (0, 1):
                if selected == (i, j):
                    fgcolor = (0, 0, 0)
                    bgcolor = (255, 255, 255)
                else:
                    fgcolor = (255, 255, 255)
                    bgcolor = (0, 0, 0)
                if not keybindings[list(keybindings.keys())[i]][j][2]:
                    fgcolor = (127, 127, 127)
                if keybindings[list(keybindings.keys())[i]][j][1]:
                    shifttext = 'shift + '
                else:
                    shifttext = ''
                if keybindings[list(keybindings.keys())[i]][j][0] in keynames:
                    keytext = shifttext + keynames[keybindings[list(keybindings.keys())[i]][j][0]]
                elif keybindings[list(keybindings.keys())[i]][j][0] == None:
                    keytext = 'None'
                else:
                    keytext = shifttext + 'unnamed key'
                if state == 1 and selected == (i, j):
                    keytext = '?????'
                win.write(keytext, x=15+longest+5+j*30, y=i+4, fgcolor=fgcolor, bgcolor=bgcolor)
            if selected == (len(keybindings), 0):
                fgcolor = (0, 0, 0)
                bgcolor = (255, 255, 255)
            else:
                fgcolor = (255, 255, 255)
                bgcolor = (0, 0, 0)
            win.write('Save and return', x=15+longest+5, y=len(keybindings)+5, fgcolor=fgcolor, bgcolor=bgcolor)
        if selected == (len(keybindings), 1):
            fgcolor = (0, 0, 0)
            bgcolor = (255, 255, 255)
        else:
            fgcolor = (255, 255, 255)
            bgcolor = (0, 0, 0)
        win.write('Reset to defaults', x=15+longest+5+30, y=len(keybindings)+5, fgcolor=fgcolor, bgcolor=bgcolor)
        win.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                with open('keybindings.pickle', 'wb') as f:
                    pickle.dump(keybindings, f)
                pygame.quit()
                sys.exit()
            if event.type == pygame.locals.KEYDOWN:
                if state == 0:
                    if event.key == pygame.locals.K_ESCAPE:
                        with open('keybindings.pickle', 'wb') as f:
                            pickle.dump(keybindings, f)
                        cont = True
                    if event.key == pygame.locals.K_UP:
                        selected = (max(selected[0]-1, 0), selected[1])
                    if event.key == pygame.locals.K_DOWN:
                        selected = (min(selected[0]+1, len(keybindings)), selected[1])
                    if event.key == pygame.locals.K_LEFT:
                        selected = (selected[0], max(0, selected[1]-1))
                    if event.key == pygame.locals.K_RIGHT:
                        selected = (selected[0], min(1, selected[1]+1))
                    if event.key == pygame.locals.K_RETURN:
                        if selected[0] < len(keybindings):
                            if keybindings[list(keybindings.keys())[selected[0]]][selected[1]][2]:
                                state = 1
                        elif selected[1] == 0:
                            with open('keybindings.pickle', 'wb') as f:
                                pickle.dump(keybindings, f)
                            cont = True
                        else:
                            for command in keybindings_default:
                                keybindings[command] = keybindings_default[command]
                else:
                    if not event.key in reservedkeys:
                        keys = [keybindings[list(keybindings.keys())[selected[0]]][0], keybindings[list(keybindings.keys())[selected[0]]][1]]
                        keys[selected[1]] = (event.key, (event.mod & pygame.KMOD_SHIFT), True)
                        keybindings[list(keybindings.keys())[selected[0]]] = (keys[0], keys[1])
                        for i in range(len(keybindings)):
                            for j in (0, 1):
                                if (i, j) != selected and keybindings[list(keybindings.keys())[i]][j][2] and keybindings[list(keybindings.keys())[i]][j][0] == event.key and keybindings[list(keybindings.keys())[i]][j][1] == (event.mod & pygame.KMOD_SHIFT):
                                    keys = [keybindings[list(keybindings.keys())[i]][0], keybindings[list(keybindings.keys())[i]][1]]
                                    keys[j] = (None, False, True)
                                    keybindings[list(keybindings.keys())[i]] = (keys[0], keys[1])
                        state = 0
                    elif event.key == pygame.locals.K_ESCAPE:
                        state = 0
                    elif event.key == pygame.locals.K_RETURN:
                        keys = [keybindings[list(keybindings.keys())[selected[0]]][0], keybindings[list(keybindings.keys())[selected[0]]][1]]
                        keys[selected[1]] = (None, False, True)
                        keybindings[list(keybindings.keys())[selected[0]]] = (keys[0], keys[1])
                        state = 0

def options():
    global font
    global fontsize
    global showsequentially
    cont = False
    selected = 0
    fonts = ('Hack-Regular.ttf', 'software_tester_7.ttf', 'courier-prime-sans.regular.ttf', 'square.ttf', 'PressStart2P-Regular.ttf')
    fontnames = ('Hack', 'Software Tester 7', 'Courier Prime Sans', 'Square', 'Press Start 2P')
    font_i = fonts.index(font)
    while not cont:
        for i in range(mapwidth + hpbarwidth + hpmargin):
            for j in range(mapheight + statuslines + logheight):
                win.putchars(' ', x=i, y=j, bgcolor='black')
        title = 'OPTIONS'
        win.write(title, x=(mapwidth + hpbarwidth + hpmargin-len(title))//2, y=20, fgcolor=(255, 255, 255))
        fonttext = 'Font: < ' + fontnames[font_i] + ' >'
        if selected == 0:
            bgcolor = (255, 255, 255)
            fgcolor = (0, 0, 0)
        else:
            bgcolor = (0, 0, 0)
            fgcolor = (255, 255, 255)
        win.write(fonttext, x=(mapwidth + hpbarwidth + hpmargin-len(fonttext))//2, y=22, fgcolor=fgcolor, bgcolor=bgcolor)
        fontsizetext = 'Font size: < ' + repr(fontsize) + ' >'
        if selected == 1:
            bgcolor = (255, 255, 255)
            fgcolor = (0, 0, 0)
        else:
            bgcolor = (0, 0, 0)
            fgcolor = (255, 255, 255)
        win.write(fontsizetext, x=(mapwidth + hpbarwidth + hpmargin-len(fontsizetext))//2, y=24, fgcolor=fgcolor, bgcolor=bgcolor)
        showsequentiallytext = 'Show enemy movements sequentially: < ' + repr(showsequentially) + ' >'
        if selected == 2:
            bgcolor = (255, 255, 255)
            fgcolor = (0, 0, 0)
        else:
            bgcolor = (0, 0, 0)
            fgcolor = (255, 255, 255)
        win.write(showsequentiallytext, x=(mapwidth + hpbarwidth + hpmargin-len(showsequentiallytext))//2, y=26, fgcolor=fgcolor, bgcolor=bgcolor)
        keybindingstext = 'Keybindings'
        if selected == 3:
            bgcolor = (255, 255, 255)
            fgcolor = (0, 0, 0)
        else:
            bgcolor = (0, 0, 0)
            fgcolor = (255, 255, 255)
        win.write(keybindingstext, x=(mapwidth + hpbarwidth + hpmargin-len(keybindingstext))//2, y=28, fgcolor=fgcolor, bgcolor=bgcolor)
        backtomenutext = 'Save and return'
        if selected == 4:
            bgcolor = (255, 255, 255)
            fgcolor = (0, 0, 0)
        else:
            bgcolor = (0, 0, 0)
            fgcolor = (255, 255, 255)
        win.write(backtomenutext, x=(mapwidth + hpbarwidth + hpmargin-len(backtomenutext))//2, y=30, fgcolor=fgcolor, bgcolor=bgcolor)
        win.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                with open('options.pickle', 'wb') as f:
                    pickle.dump((font, fontsize, showsequentially), f)
                pygame.quit()
                sys.exit()
            if event.type == pygame.locals.KEYDOWN:
                if event.key == pygame.locals.K_ESCAPE:
                    with open('options.pickle', 'wb') as f:
                        pickle.dump((font, fontsize, showsequentially), f)
                    cont = True
                if event.key == pygame.locals.K_LEFT and selected == 0:
                    font_i = (font_i - 1) % 5
                    font = fonts[font_i]
                    win.font = pygame.font.Font(font, fontsize)
                if event.key == pygame.locals.K_RIGHT and selected == 0:
                    font_i = (font_i + 1) % 5
                    font = fonts[font_i]
                    win.font = pygame.font.Font(font, fontsize)
                if event.key == pygame.locals.K_LEFT and selected == 1:
                    fontsize -= 1
                    win.font = pygame.font.Font(font, fontsize)
                if event.key == pygame.locals.K_RIGHT and selected == 1:
                    fontsize += 1
                    win.font = pygame.font.Font(font, fontsize)
                if event.key == pygame.locals.K_LEFT and selected == 2:
                    showsequentially = not showsequentially
                if event.key == pygame.locals.K_RIGHT and selected == 2:
                    showsequentially = not showsequentially
                if event.key == pygame.locals.K_UP:
                    selected = max(selected-1, 0)
                if event.key == pygame.locals.K_DOWN:
                    selected = min(selected+1, 4)
                if event.key == pygame.locals.K_RETURN:
                    if selected == 3:
                        keybingsoptions()
                    if selected == 4:
                        with open('options.pickle', 'wb') as f:
                            pickle.dump((font, fontsize, showsequentially), f)
                        cont = True


def credits():
    cont = False
    while not cont:
        for i in range(mapwidth + hpbarwidth + hpmargin):
            for j in range(mapheight + statuslines + logheight):
                win.putchars(' ', x=i, y=j, bgcolor='black')
        x0 = (mapwidth + hpbarwidth + hpmargin - 29)/2
        y0 = 5

        win.write('     ', x=x0, y=y0, bgcolor='red')
        win.write(' ', x=x0, y=y0+1, bgcolor='red')
        win.write(' ', x=x0, y=y0+2, bgcolor='red')
        win.write('  ', x=x0+3, y=y0+2, bgcolor='red')
        win.write(' ', x=x0, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+4, y=y0+3, bgcolor='red')
        win.write('     ', x=x0, y=y0+4, bgcolor='red')

        win.write('     ', x=x0+6, y=y0, bgcolor='red')
        win.write(' ', x=x0+6, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+6+4, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+6, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+6+4, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+6, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+6+4, y=y0+3, bgcolor='red')
        win.write('     ', x=x0+6, y=y0+4, bgcolor='red')

        win.write(' ', x=x0+12, y=y0, bgcolor='red')
        win.write(' ', x=x0+12, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+12, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+12, y=y0+3, bgcolor='red')
        win.write('     ', x=x0+12, y=y0+4, bgcolor='red')

        win.write('     ', x=x0+18, y=y0, bgcolor='red')
        win.write(' ', x=x0+18, y=y0+1, bgcolor='red')
        win.write('     ', x=x0+18, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+18, y=y0+3, bgcolor='red')
        win.write('     ', x=x0+18, y=y0+4, bgcolor='red')

        win.write('     ', x=x0+24, y=y0, bgcolor='red')
        win.write(' ', x=x0+24, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+24+2, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+24+4, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+24, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+24+2, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+24+4, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+24, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+24+2, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+24+4, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+24, y=y0+4, bgcolor='red')
        win.write(' ', x=x0+24+2, y=y0+4, bgcolor='red')
        win.write(' ', x=x0+24+4, y=y0+4, bgcolor='red')
        
        win.write('A Self-Made Person!', x=x0+5, y=y0+6, fgcolor='red')
        win.write('Alpha 2', x=x0+11, y=y0+8, fgcolor='red')

        credlist = ['Programmer and main innovator:',
                    'Mieli "SurrealPartisan" Luukinen',
                    '',
                    'Biology consultant:',
                    'Otto Stenberg',
                    '',
                    'Language consultant:',
                    'Eero Nurmi',
                    '',
                    'Made with:',
                    'Python 3',
                    'pygame',
                    'Pygcurse',
                    'NumPy',
                    'dill',
                    'PyInstaller',
                    '',
                    'Fonts:',
                    'Courier Prime Sans by Quote-Unquote Apps. OFL License.',
                    'Hack by Source Foundry Authors. MIT License.',
                    'Press Start 2P by CodeMan38. OFL License.',
                    'Software Tester 7 by Sizenko Alexander, Style-7. Freeware.',
                    'Square by Wouter van Oortmerssen. CC BY 3.0 Deed license.',
                    '',
                    'This game is dedicated to the transgender community.']
        for i in range(len(credlist)):
            cred = credlist[i]
            win.write(cred, x=(mapwidth + hpbarwidth + hpmargin-len(cred))//2, y=y0+10+i, fgcolor='white')

        win.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.locals.KEYDOWN:
                cont = True

def quitgame():
    pygame.quit()
    sys.exit()

def mainmenu():
    buttontexts = ['Play Game', 'Hall of Fame', 'Options', 'Credits', 'Quit']
    buttonfunctions = [game, halloffame, options, credits, quitgame]
    selected = 0
    while True:
        win.settint(0, 0, 0, (0, 0, mapwidth + hpbarwidth + hpmargin, mapheight + statuslines + logheight))
        for i in range(mapwidth + hpbarwidth + hpmargin):
            for j in range(mapheight + statuslines + logheight):
                win.putchars(' ', x=i, y=j, bgcolor='black')
        x0 = (mapwidth + hpbarwidth + hpmargin - 29)/2
        y0 = 15

        win.write('     ', x=x0, y=y0, bgcolor='red')
        win.write(' ', x=x0, y=y0+1, bgcolor='red')
        win.write(' ', x=x0, y=y0+2, bgcolor='red')
        win.write('  ', x=x0+3, y=y0+2, bgcolor='red')
        win.write(' ', x=x0, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+4, y=y0+3, bgcolor='red')
        win.write('     ', x=x0, y=y0+4, bgcolor='red')

        win.write('     ', x=x0+6, y=y0, bgcolor='red')
        win.write(' ', x=x0+6, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+6+4, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+6, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+6+4, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+6, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+6+4, y=y0+3, bgcolor='red')
        win.write('     ', x=x0+6, y=y0+4, bgcolor='red')

        win.write(' ', x=x0+12, y=y0, bgcolor='red')
        win.write(' ', x=x0+12, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+12, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+12, y=y0+3, bgcolor='red')
        win.write('     ', x=x0+12, y=y0+4, bgcolor='red')

        win.write('     ', x=x0+18, y=y0, bgcolor='red')
        win.write(' ', x=x0+18, y=y0+1, bgcolor='red')
        win.write('     ', x=x0+18, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+18, y=y0+3, bgcolor='red')
        win.write('     ', x=x0+18, y=y0+4, bgcolor='red')

        win.write('     ', x=x0+24, y=y0, bgcolor='red')
        win.write(' ', x=x0+24, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+24+2, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+24+4, y=y0+1, bgcolor='red')
        win.write(' ', x=x0+24, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+24+2, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+24+4, y=y0+2, bgcolor='red')
        win.write(' ', x=x0+24, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+24+2, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+24+4, y=y0+3, bgcolor='red')
        win.write(' ', x=x0+24, y=y0+4, bgcolor='red')
        win.write(' ', x=x0+24+2, y=y0+4, bgcolor='red')
        win.write(' ', x=x0+24+4, y=y0+4, bgcolor='red')
        
        win.write('A Self-Made Person!', x=x0+5, y=y0+6, fgcolor='red')
        win.write('Alpha 2', x=x0+11, y=y0+8, fgcolor='red')

        for i in range(len(buttontexts)):
            y = 30+2*i
            x = (mapwidth + hpbarwidth + hpmargin-len(buttontexts[i]))/2
            if i == selected:
                fgcolor=(0,0,0)
                bgcolor=(255,255,255)
            else:
                fgcolor=(255,255,255)
                bgcolor=(0,0,0)
            win.write(buttontexts[i], x=x, y=y, fgcolor=fgcolor, bgcolor=bgcolor)

        win.update()

        for event in pygame.event.get():
            if event.type == pygame.locals.KEYDOWN:
                if event.key == pygame.locals.K_UP:
                    selected = max(selected-1, 0)
                if event.key == pygame.locals.K_DOWN:
                    selected = min(selected+1, len(buttontexts)-1)
                if event.key == pygame.locals.K_RETURN:
                    buttonfunctions[selected]()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

if __name__=='__main__':
    mainmenu()