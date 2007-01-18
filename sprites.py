import pygame
import random
import utility
from xml.dom import minidom
from xml import xpath
#SPRITE STUFF


#Classes

class Tile(pygame.sprite.Sprite):
        
    def __init__(self, type, map, img, x=0, y=0):
        self.type = type
        self.map = map
        
        pygame.sprite.Sprite.__init__(self)
        
        self.image = img
        self.rect = self.image.get_rect()
        
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.topleft = x, y

class TopDownSprite(pygame.sprite.Sprite):
    
    """ Top Down Sprite
        This is the base class from which all sprites on the level will inherit.
        The rect is the collision rectangle, not the image rectangle. Images will
        automatically place themselves in relationship to the collision rect based on
        an offset defined for each image frame.

        imgdict structure =
            state           sequence img 1 dict                         etc...
        { 'running' => [{'img'=>imgObject,'frames'=>20,'offset'=>(x,y)},{...}] }
        """

    def __init__(self, imgdict, rect, state, group=()):
        pygame.sprite.Sprite.__init__(self, group)
        #Get image and rect for image
        self.__imgdict = imgdict
        self.__state = state
        self.__curframe = 1
        self.__curseqimg = 0
        self.rect = rect

    def getState(self):
        return self.__state

    def setState(self, state):
        if self.__state == state:
            return
        if self.__imgdict.has_key(state):
            self.__state = state
            self.__curframe = 1
            self.__curseqimg = 0
        else:
            raise ValueError

    def getStates(self):
        #Return the possible states for this sprite
        return self.__imgdict.keys()

    def update(self, *args):
        #Update the sprite's animation
        curstate = self.__imgdict[self.__state]
        self.__curframe = self.__curframe + 1
        if self.__curframe > curstate[self.__curseqimg]['frames']:
            #At the end of this sequence image, next
            self.__curframe = 1
            self.__curseqimg = self.__curseqimg + 1
        if self.__curseqimg >= len(curstate):
            #At end of sequence, start over
            self.__curseqimg = 0

    def getDrawObjects(self):
        #Returns the image and rect for drawing a sprite's current state
        seqimg = self.__imgdict[self.__state][self.__curseqimg]
        img = seqimg['img']
        rect = img.get_rect()
        rect.centerx = self.rect.centerx + seqimg['offset'][0]
        rect.bottom = self.rect.bottom - seqimg['offset'][1]
        return img, rect

    def collide(self, groups):
        crashed = []
        spritescollide = self.rect.colliderect
        for group in groups:
            for s in group.sprites():
                if s != self:
                    if spritescollide(s.rect):
                        crashed.append(s)
        return crashed

    def collideResolve(self, prevPos, groups):
        #Resolves any collisions. Should only be called if player has moved.
        #This assumes that each movement is symmetrical (x,0) (0,y) or (x,y) where x=y.
        #The faster you move, the slower this is.
        collideRects = self.collide(groups)
        if not collideRects:
            return
        collideRects = [s.rect for s in collideRects]
        tryMove = [-(self.rect.topleft[0] - prevPos[0]),-(self.rect.topleft[1] - prevPos[1])];
        cAx = [1,1]
        for n in (0,1):
            move = [0,0]
            move[n] = tryMove[n]
            tryRect = self.rect.move(move)
            tryCollides = tryRect.collidelistall(collideRects)
            if not tryCollides:
                cAx[n] = 0
        if cAx == [0,1]:
            #No collisions in x axis
            move = (tryMove[0]/abs(tryMove[0]),0)
            limit = abs(tryMove[0])
        elif cAx == [1,0]:
            #No collisions in y axis
            move = (0,tryMove[1]/abs(tryMove[1]))
            limit = abs(tryMove[1])
        elif cAx == [1,1]:
            #Collisions on both, move diagonal
            move = (tryMove[0]/abs(tryMove[0]),tryMove[1]/abs(tryMove[1]))
            limit = abs(tryMove[0])
        else:
            #Something weird, go previous position
            self.rect.topleft = prevPos
            return
        count = 0
        tryRect = pygame.rect.Rect(self.rect)
        while count < abs(limit):
            count = count+1
            tryRect.move_ip(move)
            tryCollides = tryRect.collidelistall(collideRects)
            if not tryCollides:
                #This position is good
                self.rect.topleft = tryRect.topleft
                return
        #If all else fails, go to previous position    
        self.rect.topleft = prevPos
    
##    def collideResolve(self, groups):
##        # THIS DOESN'T WORK YET! -Sean
##        
##        #Resolves any collisions. Should only be called if player has moved.
##        #May cause other collisions, but they should be resolved by THAT sprite's call to this.
##        collideRects = self.collide(groups)
##        collideRects = [s.rect for s in collideRects]
##        meRect = pygame.rect.Rect(self.rect)
##        badDirs = []
##        for tempCount in range(0,100):      #For loop ensures no inf loop
##            moveList = []
##            for cRect in collideRects:
##                rRect = cRect.clip(meRect)
##                if rRect.size == (0,0):
##                    #There is no overlap
##                    continue
##                dList = []
##                if 'U' not in badDirs:
##                    dD = rRect.bottom - meRect.top
##                    dList.append((abs(dD),(0,dD),'D'))
##                if 'R' not in badDirs:
##                    dD = rRect.right - meRect.left
##                    dList.append((abs(dD),(dD,0),'L'))
##                if 'D' not in badDirs:
##                    dD = rRect.top - meRect.bottom
##                    dList.append((abs(dD),(0,dD),'U'))
##                if 'L' not in badDirs:
##                    dD = rRect.left - meRect.right
##                    dList.append((abs(dD),(dD,0),'R'))
##                dList.sort()
##                if dList:
##                    moveList.append(dList[0])
##            if not moveList:
##                break
##            moveList.sort()
##            meRect.move_ip(moveList[0][1])
##            if moveList[0][2] not in badDirs:
##                badDirs.append(moveList[0][2])
##        #Set actual position to the good position this came up with
##        self.rect.topleft = meRect.topleft


class Character(TopDownSprite):

    #Load an image dictionary and collision rect defined in an xml file
    #Returns ( imgDict, defaultState, collisionRect )
    def loadSpriteFromXML(self, xmlpath, spriteName):
        #Set default variables
        imgDict = {}
        defaultState = False
        collisionRect = pygame.rect.Rect(0,0,0,0)
        #Load and parse XML
        document = minidom.parse(xmlpath)
        baseDir = document.documentElement.getAttribute('filedirectory')
        spriteNode = xpath.Evaluate('sprite[@name="'+spriteName+'"]',document.documentElement)
        if not spriteNode:
            return TypeError, 'No such sprite name in document.'
        spriteNode = spriteNode[0]
        spriteDir = spriteNode.getAttribute('filedirectory')
        collisionRect.width = int(spriteNode.getAttribute('rectwidth'))
        collisionRect.height = int(spriteNode.getAttribute('rectheight'))
        for stateNode in xpath.Evaluate('state',spriteNode):
            stateNodeName = stateNode.getAttribute('name')
            imgDict[stateNodeName] = []
            if xpath.Evaluate('@default',stateNode):
                defaultState = stateNodeName
            for imageNode in xpath.Evaluate('image',stateNode):
                iDict = {}
                iDict['img'] = utility.loadImage(imageNode.getAttribute('filename'),[baseDir,spriteDir],-1)
                iDict['frames'] = int(imageNode.getAttribute('frames'))
                iDict['offset'] = (int(imageNode.getAttribute('offsetx')),int(imageNode.getAttribute('offsety')))
                imgDict[stateNodeName].append(iDict)
        return (imgDict, defaultState, collisionRect)

    #Mo' Betta placement algorithm
    def place(self, minmax, group):
        firstpos = self.rect.topleft
        min = minmax[0]
        max = minmax[1]
        xmax = 50*(-1*min[0]+max[0])
        ymax = 50*(-1*min[1]+max[1])
        i = 1
        conflicts = []
        #add inflation to try to get characters away from the edges
        for lilgroup in group:
            for crite in lilgroup.sprites():
                conflicts.append(crite.rect)
        chect = self.rect.inflate(100,100)
        while chect.collidelist(conflicts):
            legal = range(-50*i,50*i+1,50)
            for xvalue in legal:
                if xvalue + firstpos[0] <= 0 or xvalue + firstpos[0] >= xmax:
                    continue
                for yvalue in legal:
                    if yvalue + firstpos[1] <= 0 or yvalue + firstpos[1] >= ymax:
                        continue
                    if xvalue == 0 and yvalue == 0:
                        continue
                    if xvalue != -50*i and xvalue != 50*i and yvalue != -50*i and yvalue != 50*i:
                        continue
                    self.rect.move_ip(xvalue,yvalue)
                    if self.collide(group):
                        self.rect.topleft = firstpos
                    else: return
            i += 1

class NPC(Character):
    #This is the class for all of the nodes who will be around on the map.
    def __init__(self, image, minmax, conversationList, group = ()):
        self.__conversationList = conversationList
        #for collision detection, no longer necessary when Sean completes his new version
        self.type = 9
        #for use in the network manager
        self.radix = 0
        self.stop = 0
        self.wait = 0
        self.rest = 0
        self.talking = 0
        #begin common init function with player
        image = utility.loadImage(image)
        rect = image.get_rect()
        savePos = (rect.centerx,rect.bottom)
        rect.width = 50
        rect.height = 50
        rect.centerx = savePos[0]
        rect.bottom = savePos[1]
        state = 'default'
        min = minmax[0]
        max = minmax[1]
        xmax = 50*(-1*min[0]+max[0])
        ymax = 50*(-1*min[1]+max[1])
        rect.topleft = (random.randint(0,xmax), random.randint(0,ymax))
        imgdict = {state:[{'img':image,'frames':1,'offset':(0,0)}]}
        TopDownSprite.__init__(self, imgdict, rect, state, group)

    def startDialog(self):
        talk = random.choice(self.__conversationList)
        if __debug__:
            print talk
        return talk

class Doodad(TopDownSprite):

    '''Doodad -
        The sprite class for rocks, trees, buildings, etc. '''
    
    pass

# vim:set ts=4 expandtab nowrap:

