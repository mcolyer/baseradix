import pygame.locals
import utility
import sprites
import random, os, string

#Player Stuff

class Player(sprites.Character):
    def __init__(self, minmax, conversationManager, group=()): 
        #define necessary variables
        #this will hopefully be eliminated by xml, eventually
        self.conversationManager = conversationManager
        self.stop = 0
        self.type = -1
        self.wait = 0
        self.delay = 0

        #Load info from XML
        (imgDict, state, rect) = self.loadSpriteFromXML(os.path.join('xml','sprites.xml'),'brendan')

        #Set initial position        
        min = minmax[0]
        max = minmax[1]
        midx = 50*(-1*min[0]+max[0])/2
        midy = 50*(-1*min[1]+max[1])/2
        rect.topleft = (midx, midy)
        
        sprites.TopDownSprite.__init__(self, imgDict, rect, state, group)
        

    # execute performs actions regarding the player according to the events that the
    # KeyManager detects
    def execute(self, keydict, player, network):
        speed = 5
        moveDirs = []
        if not self.stop:
            if keydict.has_key(pygame.locals.K_UP) and keydict[pygame.locals.K_UP]:
                self.rect.move_ip(0,-speed)
                moveDirs.append('U')
            if keydict.has_key(pygame.locals.K_DOWN) and keydict[pygame.locals.K_DOWN]:
                self.rect.move_ip(0,speed)
                moveDirs.append('D')
            if keydict.has_key(pygame.locals.K_LEFT) and keydict[pygame.locals.K_LEFT]:
                self.rect.move_ip(-speed,0)
                moveDirs.append('L')
            if keydict.has_key(pygame.locals.K_RIGHT) and keydict[pygame.locals.K_RIGHT]:
                self.rect.move_ip(speed,0)
                moveDirs.append('R')
        if self.stop and not self.delay:
            if keydict.has_key(pygame.locals.K_SPACE) and keydict[pygame.locals.K_SPACE]:
                self.stopTalk()
        if not self.stop and not self.wait:
            if keydict.has_key(pygame.locals.K_SPACE) and keydict[pygame.locals.K_SPACE]:
                self.talk(player, network)
        if self.wait:
            self.wait += 1
            if self.wait > 30:
                self.wait = 0
        if self.delay:
            self.delay += 1
            if self.delay > 30:
                self.delay = 0
        #Set state with movedirs
        if 'D' in moveDirs and 'U' in moveDirs:
            moveDirs.remove('D')
            moveDirs.remove('U')
        if 'R' in moveDirs and 'L' in moveDirs:
            moveDirs.remove('R')
            moveDirs.remove('L')
        if moveDirs:
            #Walking
            stateName = 'walking-'
            for dir in moveDirs:
                stateName = stateName + dir
            self.setState(stateName)
        else:
            #Standing
            curDirs = string.split(self.getState(),'-')[1]
            self.setState('standing-'+curDirs)
        

    # talk is a function designed to handle what happens when the player wants to talk to
    # a node.  Talk currently stops both the player and the node.
    def talk(self, player, network):
        nodes = utility.distance(player, network) 
        if len(nodes) != 0:
            responder = random.choice(nodes)
            responder.stop = 1
            responder.talking = 1
            self.conversationManager.setText(responder.startDialog())
            self.conversationManager.setPosFromTalkerRect(responder.rect)
            self.stop = 1
            self.talkingwith = responder
            self.delay = 1
                
    def stopTalk(self):
        self.conversationManager.reset()
        self.stop = 0
        self.talkingwith.stop = 0
        self.talkingwith.talking = 0
        self.wait = 1
            
        
# vim:set ts=4 expandtab nowrap: 
