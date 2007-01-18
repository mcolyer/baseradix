import pygame
import random
import sprites
import utility
import os
from xml.dom import minidom
from xml import xpath

class MenuCreator:
    #if you don't like the way this looks, works, or is coded
    #please feel free to change it however you would like
    #just document it and tell us what you did ~ Brendan
    def __init__(self, screen, background):
        self.screen = screen
        self.background = background
        self.result = None
        self.running = 0
        self.background.fill((255, 255, 255))
        self.welcome = utility.loadImage('welcome.bmp')
        self.choices = []
        #newgame must be first and quit must be last
        self.choices.append(utility.drawText('New Game', 50, (0,255,0), self.screen, (327,300)))
        self.choices.append(utility.drawText('Save Game', 50, (0,255,0), self.screen, (325,350)))
        self.choices.append(utility.drawText('Load Game', 50, (0,0,0), self.screen, (320,400)))
        self.choices.append(utility.drawText('Options', 50, (0,0,0), self.screen, (347,450)))
        self.choices.append(utility.drawText('Credits', 50, (0,0,0), self.screen, (354,500)))
        self.choices.append(utility.drawText('Quit', 50, (0,0,0), self.screen, (375,550)))

    def drawMenu(self, hl):
        self.screen.blit(self.welcome, (0, 0))
        for choice in self.choices:
                utility.drawText(choice[0], choice[1], (0,0,0), self.screen, choice[3])
        utility.drawText(self.choices[hl][0], self.choices[hl][1], (0,255,0), self.screen, self.choices[hl][3])
        pygame.display.flip()

    def menuLoop(self, hl=0):
        self.drawMenu(hl)
        keystates = {}
        i = hl
        current = self.choices[i]
        #loop - this and perhaps most of this function should actually be moved to managers
        #so that the menu can be accessed and interacted with during runtime from main
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.locals.KEYDOWN:
                    keystates[event.key] = True
                    continue
                elif event.type == pygame.locals.KEYUP:
                    keystates[event.key] = False
                    continue
                else:
                    continue
            if keystates.has_key(pygame.locals.K_UP) and keystates[pygame.locals.K_UP]:
                if i == 0:
                    i = len(self.choices)-1
                else:
                    i -= 1
                current = self.choices[i]
                self.drawMenu(i)
            elif keystates.has_key(pygame.locals.K_DOWN) and keystates[pygame.locals.K_DOWN]:
                if i == len(self.choices)-1:
                    i = 0
                else:
                    i += 1
                current = self.choices[i]
                self.drawMenu(i)
            elif keystates.has_key(pygame.locals.K_ESCAPE) and keystates[pygame.locals.K_ESCAPE]:
                if self.running:
                    return 'running'
                else:
                    pass
            elif keystates.has_key(pygame.locals.K_RETURN) and keystates[pygame.locals.K_RETURN]:
                if current == self.choices[0]:
                    return 'newgame'
                elif current == self.choices[len(self.choices)-1]:
                    return 'quit'
                elif current == self.choices[4]:
                    return 'credits'
                elif current == self.choices[1] and self.running:
                    print 'Saving is still being developed.'
                    return 'savegame'
                elif current == self.choices[2]:
                    print 'Loading is still being developed.'
                    return 'loadgame'
                elif current == self.choices[3]:
                    print 'Sorry, you can\'t use options yet.'
            keystates = {}
        #return choice

    def credits(self):
        credits = utility.loadImage('credits.bmp')
        self.screen.blit(credits, (0, 0))
        pygame.display.flip()
        keystates = {}
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.locals.KEYDOWN:
                    keystates[event.key] = True
                    continue
                elif event.type == pygame.locals.KEYUP:
                    keystates[event.key] = False
                    continue
            if keystates.has_key(pygame.locals.K_RETURN) and keystates[pygame.locals.K_RETURN]:
                return
        return

class MapCreator(dict):
    def __init__ (self, XMLFilename, imageManager, size, water=1.0):
        dict.__init__(self)

        #Load XML image info into dicts
        self.__tImgClassDict = {}
        self.__tImgDict = {}
        self.__loadObjects(XMLFilename)

        #Save reference to imageManager to use when getting tile images
        self.imageManager = imageManager

        #Build maps until all land is one piece (or fill with water if less than 1% of map is cut off)
        while not self.__checkbody(1,.01,2):

            #Build the map
            self.clear()
            self.__createbody(size, 1) #Make land
            landkeys = self.keys()
            for i in range(random.randint(2,5)): #Make bodies of water (number range fixed, size based on total size)
                self.__createbody(random.randint(int(size*water/30),int(size*water/20)),2,random.choice(landkeys))

            #Fill any "holes"
            self.__fillholes()

        #Fill in border region of map with tiles of type 0
        self.__addBorders()

        #Assign proper images here
        for xy in self.keys():
            self.__setFinalTileImg(xy)

        #Finally, set map tiles rects to proper position (w/ 0,0 at top left)
        self.__zeromaptiles()

    def __setFinalTileImg(self, xy):
        #Sets the proper final image for tile based on surroundings
        #Returns true if image was set to new (instead of default for type)
        edgeTypes = tuple([int(a) for a in self.__getedgetypes(xy, True)])
        tType = self[xy].type
        pImgs = self.__getPossibleImgList(tType, edgeTypes)
        if pImgs:
            tImg = random.choice(pImgs)
            self[xy].image = self.imageManager.getImage(tImg['filepath'])
            self[xy].rect = self[xy].image.get_rect()
            return True
        return False

    def __getPossibleImgList(self, type, edgeTypes):
        #Gets the possible images all in one list (takes into account As in side lists)
        pKeys = self.__tImgDict.keys()
        pKeys = [k for k in pKeys if k[0] == type] #Filter on correct type
        for ind in range(len(edgeTypes)): #Filter on each edge (include if "all" for that edge)
            pKeys = [k for k in pKeys if (k[1][ind] == edgeTypes[ind] or k[1][ind] == 'A')]
        res = []
        for pK in pKeys:
            res = res + self.__tImgDict[pK]
        return res

    def __loadObjects(self, filename):
        document = minidom.parse(filename)
        baseDir = document.documentElement.getAttribute('filedirectory')
        tClasses = xpath.Evaluate('tileclasses/tileclass',document.documentElement)
        for tClass in tClasses:
            tId = int(tClass.getAttribute('id'))
            tName = tClass.getAttribute('name')
            tFilepath = os.path.join(baseDir,tClass.getAttribute('defaultfilename'))
            self.__tImgClassDict[tId] = {'name':tName, 'defaultfilepath':tFilepath }
        tTypes = xpath.Evaluate('tiletype',document.documentElement)
        for tType in tTypes:
            tId = int(tType.getAttribute('id'))
            tSides = [a for a in tType.getAttribute('sides')]
            for ind in range(len(tSides)): #Convert all but As in tSides to integers
                if tSides[ind] != 'A':
                    tSides[ind] = int(tSides[ind])
            tSides = tuple(tSides)
            tDir = tType.getAttribute('filedirectory')
            self.__tImgDict[(tId,tSides)] = []
            tiles = xpath.Evaluate('tile',tType)
            for tt in tiles:
                ttRef = {}
                for attName in tt.attributes.keys():
                    ttRef[attName] = tt.getAttribute(attName)
                ttRef['filepath'] = os.path.join(baseDir, tDir, ttRef['filename'])
                #To account for weight, duplicate record 'weight' number of times
                for wCount in range(int(ttRef['weight'])):
                    self.__tImgDict[(tId,tSides)].append(ttRef)

    def __createbody(self, size, type, initpoint=(0,0)):
        #Build a body of a type
        todo = [initpoint]
        size = size - 1
        #Get default type image
        tileImg = self.imageManager.getImage(self.__tImgClassDict[type]['defaultfilepath'])
        while todo:
            #Create current square
            #print 'use',
            cur = todo.pop(0)
            self[cur] = sprites.Tile(type, self, tileImg)
            #Add adjacent squares if they don't exist yet (in random order)
            for adjtile in self.__getedgexy(cur):
                if (not (self.has_key(adjtile) and self[adjtile].type == type)) and (not adjtile in todo) and size > 0:
                    todo.append(adjtile)
                    size = size - 1
                    #print (size,len(todo)),
            random.shuffle(todo) #Mix up the todo list for random map shape
    
    def __filltiles(self, tiles, type):
        #Fill the tiles at coords in list "tiles" with Tiles of type "type"
        tileImg = self.imageManager.getImage(self.__tImgClassDict[type]['defaultfilepath'])
        for tile in tiles:
            self[tile] = sprites.Tile(type, self, tileImg)
    
    def __fillholes(self):
        #Eliminate "holes" in the map (empties with 4 sides)
        min,max = self.minmaxxy()
        for y in range(min[1],max[1]+1):
            for x in range(min[0],max[0]+1):
                edges = self.__getedgetypes((x,y))
                if (not False in edges) and (not self.has_key((x,y))):
                    #This square needs filling
                    tType = random.choice(edges)
                    tileImg = self.imageManager.getImage(self.__tImgClassDict[tType]['defaultfilepath'])
                    self[x,y] = sprites.Tile(tType, map, tileImg)
    
    def __checkbody(self, type, fillfrac=0, filltype=1):
        #Determines if all of the squares of 'type' are connected
        #If leftover tiles are less than fillfrac of the total map area, they will be filled with filltype
        typetiles = [xy for xy in self.keys() if self[xy].type == type] #Find all tiles of type
        if len(typetiles) < 1:
            return False #No tiles of that type exist
        checktiles = self.__getbody(typetiles[0])
        lefttiles = [x for x in typetiles if x not in checktiles]
        #print (len(lefttiles)*1.0)/len(self), lefttiles
        if (len(lefttiles)*1.0)/len(self) < fillfrac:
            #There are few enough squares, fill them
            self.__filltiles(lefttiles, filltype)
            return True
        if len(typetiles) == len(checktiles):
            return True
        else:
            return False
    
    def __getbody(self, xy):
        #Returns a list of the tiles of a type connected to the argument one
        if not self.has_key(xy):
            return False #No such key in the map
        searchtype = self[xy].type
        ret = []
        checklist = [xy]
        while checklist:
            cur = checklist.pop()
            if self.has_key(cur) and self[cur].type == searchtype:
                ret.append(cur)
                sur = self.__getedgexy(cur)
                for tsur in sur:
                    if (not tsur in ret) and (not tsur in checklist):
                        checklist.append(tsur)
        return ret
    
    def __getedgexy(self, xy, eightWay=False):
        #Get coords of surrounding tile spots
        ret = []
        if not eightWay:
            ds = [(0,-1),(1,0),(0,1),(-1,0)]
        else:
            ds = [(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]
        for d in ds:
            ret.append((xy[0]+d[0], xy[1]+d[1]))
        return ret
    
    def __getedgetypes(self, xy, eightWay=False):
        #Return edge types for coords. If no square, return False
        ret = []
        for curxy in self.__getedgexy(xy, eightWay):
            if self.has_key(curxy):
                ret.append(self[curxy].type)
            else:
                ret.append(False)
        return ret
    
    def minmaxxy(self):
        #Return min and max x and y vals in this map
        xs = [xy[0] for xy in self.keys()]
        xs.sort()
        ys = [xy[1] for xy in self.keys()]
        ys.sort()
        return [(xs[0],ys[0]),(xs[-1],ys[-1])]
    
    def printMap(self):
        #Output the map as grid of squaretypes
        min,max = self.minmaxxy()
        for y in range(min[1], max[1]+1):
            for x in range(min[0], max[0]+1):
                if self.has_key((x,y)):
                    print self[(x,y)].type,
                else:
                    print ' ',
            print
    
    def getTileList(self):
        #Returns a list of the tiles in drawing order (for moving into a group)
        min,max = self.minmaxxy()
        ret = []
        for y in range(min[1],max[1]+1):
            for x in range(min[0],max[0]+1):
                if self.has_key((x,y)):
                    ret.append(self[x,y])
        return ret
    
    def __zeromaptiles(self):
        min,max = self.minmaxxy()
        for key in self.keys():
            x = key[0] + min[0] * -1
            y = key[1] + min[1] * -1
            self[key].rect.topleft = x*self[key].rect.width,y*self[key].rect.height

    def __addBorders(self):
        bType = 0
        tileImg = self.imageManager.getImage(self.__tImgClassDict[bType]['defaultfilepath'])
        min,max = self.minmaxxy()
        for y in range(min[1]-1,max[1]+2):
            for x in range(min[0]-1,max[0]+2):
                if not self.has_key((x,y)):
                    self[(x,y)] = sprites.Tile(bType, self, tileImg)

class NetworkCreator:
    """Network Creator creates a dictionary of the social network.  It takes two
    parameters, self and nodeCount.  Self can be a name assigned to the NewNetwork
    instance, while nodeCount is an integer specifying how many nodes the network
    will contain."""
    
    def __init__(self, conversationManager):
        self.nodeDict = {}
        self.nodeCount = 10
        self.radixCount = 5
        self.__conversationManager = conversationManager

    #create actually builds the network.  Unless create is called, nodeDict stays empty!    
    def create(self, minmax, group, collide):
        i = 1
        while i <= self.nodeCount:
            npc = sprites.NPC(os.path.join('tiles','green'+str(i)+'.bmp'), minmax, self.__conversationManager.getBanterList(2), group)
            npc.place(minmax, collide)
            self.nodeDict[npc] = self.nodeDict.get(npc, [])
            i += 1
        for node in self.nodeDict.keys():
            self.addNode(node)
        br = sprites.NPC(os.path.join('tiles','blue.bmp'), minmax, self.__conversationManager.getBanterList(2), group)
        br.place(minmax, collide)
        br.radix = 1
        self.nodeDict[br] = self.nodeDict.get(br, [])
        self.addNode(br, self.radixCount)
        network = self.nodeDict
        return network

    #addNode actually appends a particular node to the keys of nodeDict, and then goes about
    #calling the connect method, which actually tells us what relationships exist for a certain node.
    def addNode(self, node, n=0):
        connections = self.connect(self.nodeDict.keys(), n)
        if len(connections) != 0:
            for connection in connections:
                if connection == node:
                    continue
                else:
                    self.nodeDict[node].append(connection)
                    self.nodeDict[connection].append(node)
        
    #connect takes the length of the existing nodeDict key list and selects a random integer f between
    #1 and that length, then creates one-way connections between the node in question and a random
    #sampling of f nodes from the nodeDict key list.
    def connect(self, network, n):
        if len(network) <= int(self.nodeCount*.25):
            return []
        else:
            if n == 0:
                f = random.randint(3,int(self.nodeCount))
            else:
                f = n
            friends = random.sample(network, f)
            return friends

class DoodadCreator:

    '''Doodad Creator -
       This class reads the doodad xml file and parses it to build a
       database of the doodads available. It can pass random doodads
       or specific ones on to the Level class which places them onto the
       map.'''

    def __init__(self, filename, imageManager):
        self.__objDict = {}
        self.imageManager = imageManager
        self.__loadObjects(filename)

    def __loadObjects(self, filename):
        document = minidom.parse(filename)
        baseDir = document.documentElement.getAttribute('filedirectory')
        ddTypes = xpath.Evaluate('doodadtype',document.documentElement)
        for ddType in ddTypes:
            typeName = ddType.getAttribute('name')
            typeDir = ddType.getAttribute('filedirectory')
            self.__objDict[typeName] = []
            doodads = xpath.Evaluate('doodad',ddType)
            for dd in doodads:
                ddRef = {}
                for attName in dd.attributes.keys():
                    ddRef[attName] = dd.getAttribute(attName)
                ddRef['filepath'] = os.path.join(baseDir, typeDir, ddRef['filename'])
                self.__objDict[typeName].append(ddRef)

    def getTypes(self):
        return self.__objDict.keys()

    def getDoodadInfos(self, type=False):
        if not type:
            ret = []
            for typeList in self.__objDict.values():
                ret = ret + typeList
            return ret
        else:
            return self.__objDict[type]

    def getRandDoodadInfo(self, type=False):
        if not type:
            type = random.choice(self.__objDict.keys())
        return random.choice(self.__objDict[type])

    # getRandDoodadSprite -
    #   This is the one we'll want to use most often. It returns a ready made
    #   instance of the sprites.Doodad class with the appropriate image loaded
    #   and ready to go.
    def getRandDoodadSprite (self, type=False):
        dInfo = self.getRandDoodadInfo(type)
        #Turn the dInfo into a doodad sprite
        dRect = pygame.rect.Rect(0,0,int(dInfo['rectwidth']),int(dInfo['rectheight']))
        dState = 'default'
        dImg = self.imageManager.getImage(dInfo['filepath'],[],-1)
        dImgDict = {'default':[{'img':dImg,'frames':1,'offset':(int(dInfo['offsetx']),int(dInfo['offsety']))}]}
        return sprites.Doodad(dImgDict, dRect, dState)

    # placeDoodad -
    #   Placement algorithm for doodads.
    #   Places within square containing sprites in groups passed, but not
    #   colliding within the padding of the doodad.
    #   Returns True if successfully placed within maxTrys and False otherwise.
    def placeDoodad(self, doodad, maxTrys, collideGroups = []):
        #Get all rects in groups
        doodadPadding = 50
        collideRects = []
        for cGroup in collideGroups:
            for cSprite in cGroup.sprites():
                collideRects.append(cSprite.rect)
        containRect = pygame.rect.Rect(0,0,0,0)
        containRect.unionall_ip(collideRects)
        dCheckRect = doodad.rect.inflate(doodadPadding*2,doodadPadding*2)
        while dCheckRect.collidelist(collideRects) != -1 or not containRect.contains(dCheckRect):
            maxTrys = maxTrys - 1
            newpos = (random.randint(containRect.left,containRect.right),random.randint(containRect.top,containRect.bottom))
            dCheckRect.topleft = newpos
            if maxTrys <= 0:
                #Couldn't place doodad in maxTrys trys
                return False
        #Placed doodad successfully
        dCheckRect.inflate_ip(-doodadPadding*2,-doodadPadding*2)
        doodad.rect.topleft = dCheckRect.topleft
        return True

    # populateMap -
    #   A simple function to fill the map with random doodads.
    def populateMap(self, addGroup, maxTrys, collideGroups=[]):
        popCollGroups = collideGroups + [addGroup]
        while 1:
            newDoodad = self.getRandDoodadSprite()
            if not self.placeDoodad(newDoodad, maxTrys, popCollGroups):
                return
            addGroup.add(newDoodad)


class ConversationCreator:
    def __init__(self):
        path = ["xml","conversation.xml"]
        filename = ""
        for part in path:
            filename = os.path.join(filename, part)
        self.__banterAssembler = XMLCFGAssembler(filename)

    def getBanter(self):
        """Gets a random banter string from the assembler.
           Returns a string"""
        return self.__banterAssembler.assembleString()

    def getBanterList(self, num):
        """Gets a list of random banter strings from the assembler.
           Returns a list"""
        return [self.__banterAssembler.assembleString() for a in range(num)]

    def getClue(self):
        """Gets a random clue string from the database.
           Returns a string"""
        return ''


class XMLCFGAssembler:

    def __init__(self, xmlpath):
        self.doc = minidom.parse(xmlpath)

    def getBaseNTName(self):
        #Get starting Non-Terminal
        return xpath.Evaluate('ntlist/nt[@base = "true"]/@name/text()',self.doc.documentElement)[0].data

    def getNTNameList(self):
        #Get list of all Non-Terminals
        return [a.data for a in xpath.Evaluate('ntlist/nt/@name/text()',self.doc.documentElement)]

    def convertNT(self, ntname):
        #Converts Non-Terminals to Terminals (recursively)
        ntDefList = xpath.Evaluate('ntdef[@name = "'+str(ntname)+'"]',self.doc.documentElement)
        nodeList = random.choice(ntDefList).childNodes
        finalList = []
        for node in nodeList:
            if node.nodeType != node.TEXT_NODE:
                #Convert this node to terminals (text nodes)
                finalList.extend(self.convertNT(node.getAttribute('name')))
            else:
                finalList.append(node)
        return finalList

    def assemble(self):
        #Assemble a full result from CFG starting at the base
        return self.convertNT(self.getBaseNTName())

    def assembleString(self):
        #Returns assemble compiled together as a single string
        res = ''
        for tNode in self.assemble():
            res = res + tNode.data
        return res
            
        
# vim:set ts=4 expandtab nowrap: 
