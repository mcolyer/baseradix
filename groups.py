import pygame
from math import ceil

class TileRenderGroup(pygame.sprite.Group):
    """ This is a special class to hold and draw the sprites that make up the
        tiles of the world. Sprites must have rect attributes. In addition, no
        two sprites in the group can have the same rect.topleft position.

        Sprites are considered unique by their rect.topleft position and nothing else. """

    def __init__(self, sprite=(), twidth=0, theight=0, torigin=(0,0)):
        """ Pass twidth and theight for tile dimensions.
            Pass torigin for different world top left tile position.
            If not passed, default to 0 and (0,0). """
        pygame.sprite.Group.__init__(self, sprite)
        self.twidth = twidth
        self.theight = theight
        self.torigin = torigin
        self.prevpos = False    #Holds the previous screen position (x,y)
        self.todraw = []        #Holds the sprites to be drawn

    def copy(self):
        """copy() -> Group
           copy a group with all the same sprites

           Returns a copy of the group that is the same class
           type, and has the same contained sprites."""
        return self.__class__(self.sprites())

    def sprites(self):
        """sprites() -> iterator
           return an object to loop over each sprite

           Returns an object that can be looped over with
           a 'for' loop. """
        return self.spritedict.values()

    def add(self, sprite):
        """add(sprite)
           add sprite to group

           Add a sprite or sequence of sprites to a group."""
        has = self.has_internal
        if hasattr(sprite, '_spritegroup'):
            for sprite in sprite.sprites():
                if not has(sprite):
                    self.add_internal(sprite)
                    sprite.add_internal(self)
        else:
            try: len(sprite) #see if its a sequence
            except (TypeError, AttributeError):
                if not has(sprite):
                        self.add_internal(sprite)
                        sprite.add_internal(self)
            else:
                for sprite in sprite:
                    if not has(sprite):
                        self.add_internal(sprite)
                        sprite.add_internal(self)

    def remove(self, sprite):
        """remove(sprite)
           remove sprite from group

           Remove a sprite or sequence of sprites from a group."""
        has = self.has_internal
        if hasattr(sprite, '_spritegroup'):
            for sprite in sprite.sprites():
                if has(sprite):
                    self.remove_internal(sprite)
                    sprite.remove_internal(self)
        else:
            try: len(sprite) #see if its a sequence
            except (TypeError, AttributeError):
                if has(sprite):
                    self.remove_internal(sprite)
                    sprite.remove_internal(self)
            else:
                for sprite in sprite:
                    if has(sprite):
                        self.remove_internal(sprite)
                        sprite.remove_internal(self)

    def add_internal(self, sprite):
        self.spritedict[sprite.rect.topleft] = sprite

    def remove_internal(self, sprite):
        del self.spritedict[sprite.rect.topleft]

    def has_internal(self, sprite):
        return self.spritedict.has_key(sprite.rect.topleft)

    def has(self, sprite):
        """has(sprite) -> bool
           ask if group has sprite

           Returns true if the given sprite or sprites are
           contained in the group"""
        has = self.has_internal
        if hasattr(sprite, '_spritegroup'):
            for sprite in sprite.sprites():
                if not has(sprite):
                    return 0
        else:
            try: len(sprite) #see if its a sequence
            except (TypeError, AttributeError):
                return has(sprite)
            else:
                for sprite in sprite:
                    if not has(sprite):
                        return 0
        return 1

        if hasattr(sprite, '_spritegroup'):
            return sprite in has(sprite)
        sprites = sprite
        for sprite in sprites:
            if not has(sprite):
                return 0
        return 1

    def empty(self):
        """empty()
           remove all sprites

           Removes all the sprites from the group."""
        for s in self.spritedict.keys():
            self.remove_internal(s)
            s.remove_internal(self)
        self.spritedict.clear()

    def update(self, *args):
        """update(...)
           call update for all member sprites

           calls the update method for all sprites in the group.
           Passes all arguments on to the Sprite update function."""
        if args:
            a=apply
            for s in self.sprites():
                a(s.update, args)
        else:
            for s in self.sprites():
                s.update()

    def __updatetodraw(self, screenrect):
        """ Calculates which tiles should be visible and populates the todraw list.
                screenrect - a rect defining the size and position of the screen's view on the world """

        if screenrect.topleft != self.prevpos:
            #The position has changed, get list of what should be visible
            self.todraw = []
            topLeft = ( screenrect.left - (screenrect.left % self.twidth), screenrect.top - (screenrect.top % self.theight))
            numDir = ( int(ceil(screenrect.width / float(self.twidth)))+1, int(ceil(screenrect.height / float(self.theight)))+1 )
            for ty in range(topLeft[1], topLeft[1]+(numDir[1]*self.theight), self.theight):
                for tx in range(topLeft[0], topLeft[0]+(numDir[0]*self.twidth), self.twidth):
                    if self.spritedict.has_key((tx,ty)):
                        self.todraw.append(self.spritedict[(tx,ty)])
        
        #Set prevpos for next time
        self.prevpos = screenrect.topleft

    def draw(self, surface, screenrect):
        """draw takes surface and 2 tuples -
                surface - the surface object to draw to
                screenrect - a rect defining the size and position of the screen's view on the world

            Calculates which tiles should be visible and draws them to surface."""

        self.__updatetodraw(screenrect)

        #Now draw the sprites in todraw to the screen in proper positions
        sprite_list = self.todraw
        surface_blit = surface.blit
        shiftx, shifty = screenrect.topleft
        shiftx = shiftx * -1
        shifty = shifty * -1
        for s in sprite_list:
            shiftrect = s.rect.move(shiftx, shifty)
            surface_blit(s.image, shiftrect)


class ObjectRenderGroup(pygame.sprite.Group):
    ''' ObjectRenderGroup

        The group for holding and drawing all TopDownSprites
        on the map.

    '''

    def draw(self, surface, screenRect):
        """draw takes surface and 2 tuples -
                surface - the surface object to draw to
                screenRect - a rect defining the size and position of the screen's view on the world

            Calculates which sprites should be visible and draws them to surface in layered order."""

        surfaceBlit = surface.blit
        shiftx, shifty = screenRect.topleft
        shiftx = shiftx * -1
        shifty = shifty * -1

        #Which sprites to draw and
        toDrawList = self.collideWith(screenRect, True)
        toDraw = {}
        #Sort todraw as lists of sprites on horiz pixel rows
        for objTuple in toDrawList:
            key = objTuple[0].rect.bottom
            if not toDraw.has_key(key):
                toDraw[key] = []
            toDraw[key].append(objTuple)

        #Draw horiz rows from low to high (top to bottom)
        toDrawRows = toDraw.keys()
        toDrawRows.sort()
        for rowKey in toDrawRows:
            thisRow = toDraw[rowKey]
            for objTuple in thisRow:
                shiftRect = objTuple[2].move(shiftx, shifty)
                surfaceBlit(objTuple[1], shiftRect)


    def collideWith(self, rect, bigReturn=False):
        """collideWith(rect) -> list
           collision detection between rect and this group

           Given a rect, this will return a list of all the
           sprites whose current image intersects the rect.
           All sprites must be TopDownSprites.

            If bigReturn is true, then the function will return
            a list of tuples with (sprite, imgObject, dispRect)
            for efficincy (so TopDownSprite.getDrawObjects only
            has to be called once.)
           """
        crashed = []
        spritecollide = rect.colliderect
        for s in self.sprites():
            sdo = s.getDrawObjects()
            if spritecollide(sdo[1]):
                if bigReturn:
                    crashed.append((s,sdo[0],sdo[1]))
                else:
                    crashed.append(s)
        return crashed

# vim:set ts=4 expandtab nowrap: 
