import pygame, os
import random
import utility
from xml.dom import minidom
from xml.dom.minidom import Document
from xml import xpath

#The class that popped this one's cherry
class NetworkManager:
    def __init__(self, network, objects, minmax):
        self.network = network
        self.objects = objects
        self.minmax = minmax
        
    def manage(self):
        for node in self.network.keys():
            if not node.stop and not node.talking:
                if node.rest:
                    node.wait += 1
                    if node.wait > 300:
                        node.wait = 0
                        node.rest = 0
                else:
                    friendlist = utility.distance(node, self.network)
                    if friendlist:
                        node.stop = 1
                        for friend in friendlist:
                            friend.stop = 1
                prevPos = node.rect.topleft
                self.walkPath(node)
                if node.collide(self.objects):
                    node.rect.topleft = prevPos
                    if node.reverse:
                        node.reverse = 0
                    else:
                        node.reverse = 1
            else:
                node.wait += 1
            if node.wait > 300:
                node.wait = 0
                node.stop = 0
                node.rest = 1

    #Called from main to setup predefined paths.
    def findPaths(self):
        for npc in self.network.keys():
            npc.pathindex = 1
            npc.walkindex = 1
            npc.reverse = 0
            paths = {}
            friendlist = self.network[npc]
            i = 1
            for friend in friendlist:
                path = self.pathFind(npc, friend)
                paths[i] = path
                i += 1
##            pathcheck = 0
##            for path in paths.values():
##                if len(path) > 10:
##                    pathcheck = 1
            #artificial paths here in here in case all paths to friends
            #are blocked by doodads, just try 4 cardinals and 4 diagonals
         #   if not pathcheck:
            morepaths = self.fakePaths(npc)
            for path in morepaths:
                paths[i] = path
                i += 1
            paths[0] = len(paths.keys())
            npc.paths = paths
                

    #find a path to each friend and record it for later use
    def pathFind(self, node, friend):
        stepsize = random.choice(range(1,3,1))
        firstpos = node.rect.topleft
        #nodepos = node.rect.topleft
        friendpos = friend.rect.topleft
        posdict = {}
        deltax = ((friendpos[0] - firstpos[0])**2)**.5
        deltay = ((friendpos[1] - firstpos[1])**2)**.5
        xsteps = range(0, int(deltax), stepsize)
        ysteps = range(0, int(deltay), stepsize)
        maxy = len(ysteps)
	maxx = len(xsteps)
	i = 1
	yin = 0
	xin = 0
        for xstep in xsteps:
		if yin < maxy:
			ydir = stepsize
			yin += 1
		else:
			ydir = 0
                posdict[i] = [stepsize, ydir]
		i += 1
		xin += 1
	if yin <= maxy:
		for step in range(0,maxy - yin, 1):
			if xin < maxx:
				xdir = stepsize
				xin += 1
			else:
				xdir = 0
			posdict[i] = [xdir, stepsize]
			i += 1
			yin += 1
        posdict[0] = len(posdict.keys())
        return posdict

    def fakePaths(self, node):
        paths = []
        possiblepaths = range(300,1000,10)
        possiblesteps = range(1,3,1)
        xvals = [0,1,-1]
        yvals = [0,1,-1]
        for x in xvals:
            for y in yvals:
                if x == 0 and y == 0:
                    continue
                i = 1
                movedict = {}
                stepsize = random.choice(possiblesteps)
                pathlength = random.choice(possiblepaths)
                steps = range(0, pathlength, stepsize)
                for step in steps:
                    movedict[i] = [x*stepsize, y*stepsize]
                    i += 1
                movedict[0] = len(movedict.keys())
                paths.append(movedict)
        return paths

    def walkPath(self, node):
        #if node.pathindex >= len(node.paths):
        if node.pathindex > node.paths[0]:
            node.pathindex = 1
        if node.reverse:
            node.rect.move_ip(node.paths[node.pathindex][node.walkindex])
            node.walkindex -= 1
            if node.walkindex <= 1:
                node.pathindex += 1
                node.reverse = 0
                node.walkindex = 1
                return
        else:
            x = -node.paths[node.pathindex][node.walkindex][0]
            y = -node.paths[node.pathindex][node.walkindex][1]
            node.rect.move_ip(x, y)
            node.walkindex += 1
        #if node.walkindex >= len(node.paths[node.pathindex]):
        if node.walkindex > node.paths[node.pathindex][0]:
            node.reverse = 1
            node.walkindex -= 1


class KeyManager:
    def __init__(self, player):
        self.keystates = {}
        self.player = player

    def detect(self, menu):
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                return 1
            elif event.type == pygame.locals.KEYDOWN and event.key == pygame.locals.K_ESCAPE:
                return 1
            elif event.type == pygame.locals.KEYDOWN:
                self.keystates[event.key] = True
                continue
                #self.player.execute(self.keystates, self.player)
            elif event.type == pygame.locals.KEYUP:
                self.keystates[event.key] = False
                continue
                #self.player.execute(self.keystates, self.player)
            else:
                continue

#This class manages the images in the game so that only one instance of each exists.
#This ensures that we don't have 100+ instances of the same image loaded in memory.
#All sprites and things should request their images through this thing.
class ImageManager:
    def __init__(self):
        self.imgDict = {}

    def getFullPath(self, name, dirList=[]):
        fullName = ''
        dirList = dirList + [name]
        for dirPiece in dirList:
            fullName = os.path.join(fullName, dirPiece)
        return fullName

    def getImage(self, name, dirList=[], colorKey=None):
        #Request an image object reference (uniqueness by filepath and colorKey)
        imgKey = (self.getFullPath(name, dirList), colorKey)
        if not self.imgDict.has_key(imgKey):
            self.imgDict[imgKey] = utility.loadImage(name, dirList, colorKey)
        return self.imgDict[imgKey]

class ConversationManager:
    def __init__(self):
        self.reset()
        self.size = 24
        self.color = (255,255,255)
        self.wrapLen = 40

    def setText(self, text):
        self.setLines(utility.wordWrap(text, self.wrapLen))

    def setPosFromTalkerRect(self, tRect):
        #Pass this the rect of the talking sprite to position the text below
        self.__posTop = tRect.bottom + 10
        self.__posCenterX = tRect.centerx

    def setLines(self, lines):
        self.reset()
        self.__lineSurfs = [ utility.getTextSurface(line, self.size, self.color) for line in lines ]
        for line in self.__lineSurfs:
            lineRect = line.get_rect()
            self.__lineRects.append(lineRect)
            if lineRect.width > self.__maxwidth:
                self.__maxwidth = lineRect.width
            self.__totalHeight = self.__totalHeight + lineRect.height

    def reset(self):
        self.__posTop = 0
        self.__posCenterX = 0
        self.__totalHeight = 0
        self.__maxwidth = 0
        self.__lineSurfs = []
        self.__lineRects = []

    def draw(self, surf, screenRect):
        if not self.__lineSurfs:
            return
        curY = self.__posTop - screenRect.top
        centX = self.__posCenterX - screenRect.left
        for ind in range(len(self.__lineSurfs)):
            curRect = self.__lineRects[ind]
            curSurf = self.__lineSurfs[ind]
            curRect.top = curY
            curY = curY + curRect.height
            curRect.left = int(centX-(curRect.width/2))
            surf.blit(curSurf, curRect)


# vim:set ts=4 expandtab nowrap: 
