import os
import pygame

# load an image and return a handle and rectangle
def loadImage(name, dirlist=[], colorkey=None):
    fullname = ''
    dirlist = ['data'] + dirlist + [name]
    for dirpiece in dirlist:
        fullname = os.path.join(fullname, dirpiece)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print 'Cannot load image:', name
        raise SystemExit, message
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, pygame.locals.RLEACCEL)
    return image

#loads images like PNG with built in Per Pixel Alpha
def loadImageAlpha(name, dirlist=[]):
    fullname = ''
    dirlist = ['data'] + dirlist + [name]
    for dirpiece in dirlist:
        fullname = os.path.join(fullname, dirpiece)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print 'Cannot load image:', name
        raise SystemExit, message
    image = image.convert_alpha()
    return image

# render text to the screen
def drawText(text, size, color, surf, pos):
    surf.blit(getTextSurface(text, size, color), pos)
    return (text,size,color,pos)

def getTextSurface(text, size, color):
    font = pygame.font.Font(None, size)
    return font.render(text, 1, color)

def getDialogueSurface(text, size=10, color=(255,255,255)):
    return getTextSurface(wordWrap(text), size, color)

def wordWrap(text, charWidth):
    retLines = []
    text = text.strip()
    while len(text) > charWidth:
        for ind in range(charWidth-1,-1,-1):
            try:
                if text[ind] == ' ':
                    break
            except IndexError:
                continue
        if ind:
            retLines.append(text[:ind].strip())
            text = text[ind:].strip()
        else:
            retLines.append(text.strip())
            text = False
    text = text.strip()
    if text:
        retLines.append(text)
    return retLines
                

def distance(obj, dict, max=100):
    objlist = []
    x1 = obj.rect.center[0]
    y1 = obj.rect.center[1]
    for dependent in dict[obj]:
        x2 = dependent.rect.center[0]
        y2 = dependent.rect.center[1]
        deltax = (x1 - x2)
        deltay = (y1 - y2)
        if deltax > max or deltay > max or deltax < -max or deltay < -max:
            continue
        dist = (deltax**2 + deltay**2)**(.5)
        if dist <= 100:
            objlist.append(dependent)
    return objlist
