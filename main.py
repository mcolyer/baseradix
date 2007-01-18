import pygame, os
import utility
import creators
import managers
import groups
import player

class BaseRadix:
    def __init__(self):
        pygame.init()

        #Create a 800x600 Full-Screen Doublebuffered screen
        self.screen = pygame.display.set_mode((800,600), pygame.DOUBLEBUF) #| pygame.FULLSCREEN)
        self.visibleRect = pygame.locals.Rect(0,0,800,600) 
        pygame.display.set_caption('Base Radix')
        pygame.mouse.set_visible(0)

        self.background = pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()

        self.menu = creators.MenuCreator(self.screen, self.background)      
        

    def mainLoop(self):
        while 1:
            self.clock.tick(60)

            #Manage
            self.managedNetwork.manage()

            #Save position for collision detection
            prevPos = self.player.rect.topleft

            #detect keystates and exit if the quit event is called
            flag = self.managedKeys.detect(self.menu)
            if flag:
                choice = self.menu.menuLoop()
                return choice
                
            self.player.execute(self.managedKeys.keystates, self.player, self.refnetwork)

            #Check for collisions and stop movement backup player if true
            #if self.player.collide([self.badTiles, self.allSprites]):
            #    self.player.rect.topleft = prevPos
            self.player.collideResolve(prevPos, [self.badTiles, self.allSprites])
            
            #Center screen on player
            self.visibleRect.center = self.player.rect.center

            #Run update on all sprites
            self.allSprites.update()
            
            self.screen.blit(self.background, (0, 0))
            self.tiles.draw(self.screen, self.visibleRect)
            self.allSprites.draw(self.screen, self.visibleRect)
            self.conversationManager.draw(self.screen, self.visibleRect)
            if __debug__:
                utility.drawText('FPS:'+str(round(self.clock.get_fps(),5)), 18, (255,255,255), self.screen, (700,5))
            pygame.display.flip()

    def newGame(self):
        #draw and determine everything
        #Make game...
        self.background.fill((0, 0, 0))
        self.screen.blit(self.background, (0,0))
        pygame.display.flip()

        #this blit is necessary to get the menu out of the buffer entirely
        self.screen.blit(self.background, (0,0))
        utility.drawText('LOADING...', 50, (255,255,255), self.screen, (200,100))
        #this redundancy is necessary because of the double buffering
        pygame.display.flip()
        pygame.display.flip()
        
        #Create a label to display while loading
        utility.drawText('BUILDING MAP', 50, (255,255,255), self.screen, (200,150))
        pygame.display.flip()

        #Create the imageManager - only used for Map Tiles right now
        self.imageManager = managers.ImageManager()

        #Generate a map
        tilesFileName = os.path.join('xml','tiles.xml')
        tmap = creators.MapCreator(tilesFileName, self.imageManager, 1000)
        self.tiles = groups.TileRenderGroup(tmap.getTileList(), 50, 50)
        self.badTiles = pygame.sprite.Group([t for t in self.tiles.sprites() if t.type!=1])

        minmax = tmap.minmaxxy()
        
        #Create the ObjectRenderGroup
        self.allSprites = groups.ObjectRenderGroup()

        #Create the Doodads and Doodad group
        self.doodads = pygame.sprite.Group()
        doodadFileName = os.path.join('xml','doodads.xml')
        doodadCreator = creators.DoodadCreator(doodadFileName,self.imageManager)
        doodadCreator.populateMap(self.doodads, 10, [self.badTiles])
        self.allSprites.add(self.doodads)
        print 'Loaded Doodads:',len(self.doodads.sprites())

        pygame.display.flip()

        utility.drawText('CREATING NPCs', 50, (255,255,255), self.screen, (200,200))
        pygame.display.flip()
        #pygame.display.flip()

        #Create conversation database
        conversationCreator = creators.ConversationCreator()

        #Create conversation manager
        self.conversationManager = managers.ConversationManager()

        #Make NPCs
        society = creators.NetworkCreator(conversationCreator)
        self.network = society.create(minmax, [self.allSprites], [self.badTiles, self.allSprites])
        self.refnetwork = {}
        for key in self.network.keys():
            self.refnetwork[key] = self.network.get(key, [])

        pygame.display.flip()
        utility.drawText('RESURRECTING PLAYER', 50, (255,255,255), self.screen, (200,250))
        pygame.display.flip()


        #Make the player
        self.player = player.Player(minmax, self.conversationManager, [self.allSprites])
        self.player.place(minmax, [self.badTiles, self.allSprites])
        self.refnetwork[self.player] = self.network.keys()

        pygame.display.flip()
        utility.drawText('MANAGING NPCs', 50, (255,255,255), self.screen, (200,300))
        pygame.display.flip()
        
        #Start Managers
        self.managedNetwork = managers.NetworkManager(self.network, [self.badTiles,self.allSprites], minmax)
        self.managedNetwork.findPaths()
        self.managedKeys = managers.KeyManager(self.player)

        #For Brian
        utility.drawText('RETICULATING SPLINES', 50, (255,255,255), self.screen, (200,350))
        pygame.display.flip()
        #pygame.display.flip()

        #Draw tiles before game start
        self.tiles.draw(self.screen, self.visibleRect)

        #Start clock
        self.clock = pygame.time.Clock()

        #Tell the menu the game is running
        self.menu.running = 1

    def loadGame(self):
        pass
        #redraw maps based on saved version, reconstruct everything in correct order
        #   unpickle self.imageManager
        #   unpickle self.tiles, self.badTiles, self.allSprites, self.doodads
        #   unpickle self.network, self.refnetwork, self.managedNetwork
        #   unpickle self.player, self.managedKeys

    def saveGame(self):
        pass
        #save generated map tile types
        #   pickle self.imageManager
        #   pickle self.tiles, self.badTiles, self.allSprites, self.doodads
        #   pickle self.network, self.refnetwork, self.managedNetwork
        #   pickle self.player, self.managedKeys


class Level:
    """This class collects all level specific items together."""
    pass

baseradix = BaseRadix()
choice = baseradix.menu.menuLoop()
#wrap this loop up in a handle choice function?
while 1:
    if choice == 'newgame':
        baseradix.newGame()
        choice = baseradix.mainLoop()
    elif choice == 'savegame':
        baseradix.saveGame()
        choice = baseradix.menu.menuLoop(hl=1)
    elif choice == 'loadgame':
        baseradix.loadGame()
        #temporarily put the game back to the menu after 'loading'
        #change to 'choice = baseradix.mainLoop' when done
        choice = baseradix.menu.menuLoop(hl=2)
    elif choice == 'credits':
        baseradix.menu.credits()
        choice = baseradix.menu.menuLoop(hl=4)
    elif choice == 'running':
        choice = baseradix.mainLoop()
    elif choice == 'quit':
        break
    

# vim:set ts=4 expandtab nowrap: 
