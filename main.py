#! /usr/bin/env python

import pygame, sys, fov, time
from pygame.locals import KEYDOWN, KEYUP, K_DOWN, K_UP, K_LEFT, K_RIGHT, K_ESCAPE, K_RETURN
from constants import *
from player import Player
from agent import Agent
from crystal import Crystal

DEBUG = False

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Color hunter")

        self.numRows        = None
        self.numCols        = None
        self.player         = None
        self.level          = None
        self.spawnPos       = None
        self.agents         = []
        self.colorsFound    = []
        self.crystals       = []
        self.colorDict      = {'R' : RED, 'B' : BLUE, 'P' : PURPLE, 'Y' : YELLOW, \
                                'G' : GREEN, 'O' : ORANGE}
        self.currAlphaDict  = {}
        self.incAlphaDict   = {}
        self.lightBarInfo   = {}
        self.currLevel      = 1
        self.maxLevel       = 3
        self.yMargin        = None
        self.xMargin        = None
        self.numOfColors    = 0
        self.visibilityMap  = None
        self.lightMap       = None
        self.updateLightBar = False
        self.displaySurf    = pygame.display.set_mode((WIDTH, HEIGHT))
        self.levelSurf      = None
        self.workSurf       = None
        self.lightBarSurf   = None
        self.elemWid        = 0
        self.levelTime      = 0

        pygame.mixer.init()
        pygame.mixer.music.load('music.mp3')
        pygame.mixer.music.play(-1)

    def loadLevel(self, levelNum):
        level = self.getLevel(levelNum)

        # +2 for surrounding walls
        self.numCols    = int(level[0]) + 2
        self.numRows    = int(level[1]) + 2
        self.spawnPos   = (int(level[2].split()[0]), int(level[2].split()[1]))
        self.player     = Player(TILESIZE*self.spawnPos[0]+1, TILESIZE*self.spawnPos[1]+1)
        self.yMargin    = (HEIGHT - TILESIZE * self.numRows) / 2
        self.xMargin    = (WIDTH - TILESIZE  * self.numCols) / 2 
        self.level      = [[OPEN]*self.numRows for i in range(self.numCols)]
        self.updateLightBar = True
        
        crystalsList = level[3].split()
        numOfCrystals = len(crystalsList) / 3
        for i in range(numOfCrystals):
            self.crystals.append(Crystal(int(crystalsList[i*3]), \
                int(crystalsList[i*3 + 1]), crystalsList[i*3 + 2]))

        if numOfCrystals > 2:
            self.numOfColors = 6
        elif numOfCrystals > 1:
            self.numOfColors = 3
        else:
            self.numOfColors = 1

        if len(self.crystals) is 1:
            self.lightBarInfo   = ['B']*LIGHTBAR_ELEMS
        elif len(self.crystals) is 2:
            self.lightBarInfo   = ['B']*3 + ['Y']*3
        else:
            self.lightBarInfo   = ['B']*2 + ['Y']*2 + ['R']*2

        agentCount = int(level[4])
        agentColorDict = self.addAgents(level, agentCount)
        self.setColorAlphas(agentColorDict)
        self.setMap(level, agentCount)
        self.setSurfaces()
        self.setVisibilityMap()

    def setColorAlphas(self, agentColorDict):
        alphaToFill = MAX_ALPHA - BASE_ALPHA
        for color in agentColorDict:
            if agentColorDict[color] is not 0:
                self.currAlphaDict[color] = 0
                self.incAlphaDict[color]  = \
                    alphaToFill / agentColorDict[color] + 1

    # Return level as list
    def getLevel(self, levelNum):
        levelFile  = open('levels.txt')
        line       = levelFile.readline()
        level      = []
        levelString = "level " + str(levelNum) + "\n"

        # Find block of levelNum
        while line != levelString:
            line = levelFile.readline()
            assert line is not "EOF\n", "Error reading level " + str(levelNum)

        # Store each line as element in the list level
        line = levelFile.readline()
        while line != "\n":
            level.append(line.strip())
            line = levelFile.readline()
        levelFile.close()
        return level

    def setSurroundingWall(self):
        for i in range(self.numCols):
            self.level[i][0] = WALL
            self.level[i][self.numRows-1] = WALL

        for i in range(self.numRows):
            self.level[0][i] = WALL
            self.level[self.numCols-1][i] = WALL

    def setMap(self, level, agentCount):
        self.setSurroundingWall()
        levelDescriptLine = 5 + agentCount

        # set inner area of map
        for row in range(1, self.numRows-1):
            line = list(level[levelDescriptLine])
            for col in range(1, self.numCols-1):
                if line[col-1] == 'W':
                    self.level[col][row] = WALL
                else:
                    self.level[col][row] = OPEN
            levelDescriptLine += 1

    # Return dictionary containing number of agents of each color
    def addAgents(self, level, agentCount):
        colorCountDict = {'B':0, 'Y':0, 'R':0, 'G':0, 'P':0, 'O':0}

        for i in range(agentCount):
            patrolList = []
            coordList = level[5+i].split()

            for j in range((len(coordList)-1)/2):
                patrolList.append((int(coordList[j*2]), int(coordList[j*2+1])))
            
            self.agents.append(Agent(patrolList, coordList[-1]))
            colorCountDict[coordList[-1]] += 1
        return colorCountDict

    def setSurfaces(self):
        self.lightMap       = [[None]*self.numRows for i in range(self.numCols)]
        self.colorsFound    = []
        self.levelSurf      = pygame.Surface((self.numCols * TILESIZE, \
            self.numRows * TILESIZE))
        self.workSurf       = self.levelSurf.copy().convert_alpha()
        self.lightBarSurf   = pygame.Surface((self.numCols * TILESIZE, TILESIZE)).convert()

        self.elemWid = (TILESIZE*self.numCols) / LIGHTBAR_ELEMS
        if self.elemWid % 2 is 1:
            self.elemWid += 1
        self.lightBarElem = pygame.Surface((self.elemWid, TILESIZE)).convert()
        self.makeLevelSurf()

    def setVisibilityMap(self):
        if DEBUG:
            self.visibilityMap = [[[EXPLORED, LIT] for j in range(self.numRows)] \
             for i in range(self.numCols)]
        else:    
            self.visibilityMap = [[[UNEXPLORED, UNLIT] for j in range(self.numRows)] \
             for i in range(self.numCols)]

        for i in range(self.numCols):
            self.visibilityMap[i][0][0] = EXPLORED
            self.visibilityMap[i][self.numRows-1][0] = EXPLORED

        for i in range(self.numRows):
            self.visibilityMap[0][i][0] = EXPLORED
            self.visibilityMap[self.numCols-1][i][0] = EXPLORED
    
    def makeLevelSurf(self):
        for row in range(self.numRows):
            for col in range(self.numCols):
                x        = col * TILESIZE
                y        = row * TILESIZE
                tileRect = pygame.Rect(x, y, TILESIZE, TILESIZE)

                if self.level[col][row] == WALL:
                    pygame.draw.rect(self.levelSurf, GRAY, tileRect)
                elif self.level[col][row] == OPEN:
                    pygame.draw.rect(self.levelSurf, (0, 153, 153), tileRect)

    # Return true if player died or absorbed a light
    def checkInLight(self):
        agent = self.lightMap[self.getPlayerCoordX()][self.getPlayerCoordY()]
        if agent is None:
            return False

        if agent.color not in self.colorsFound:
            self.respawn()
        else:
            self.absorbLight(agent)
        return True

    def colorMaxed(self, color):
        return self.currAlphaDict[color] >= MAX_ALPHA

    def absorbLight(self, agent):
        absColor = agent.color
        self.currAlphaDict[absColor] += self.incAlphaDict[absColor]

        if self.numOfColors is 6:
            if absColor in ['B', 'Y']:
                if self.colorMaxed('Y') and self.colorMaxed('B'):
                    self.lightBarInfo[1] = self.lightBarInfo[2] = 'G'
                    self.currAlphaDict['G'] = BASE_ALPHA
                    self.colorsFound.append('G')
            if absColor in ['B', 'R']:
                if self.colorMaxed('R') and self.colorMaxed('B'):
                    self.lightBarInfo[0] = self.lightBarInfo[5] = 'P'
                    self.currAlphaDict['P'] = BASE_ALPHA
                    self.colorsFound.append('P')
            if absColor in ['R', 'Y']:
                if self.colorMaxed('R') and self.colorMaxed('Y'):
                    self.lightBarInfo[3] = self.lightBarInfo[4] = 'O'
                    self.currAlphaDict['O'] = BASE_ALPHA
                    self.colorsFound.append('O')
        elif self.numOfColors is 3:
            if absColor in ['B', 'Y']:
                if self.colorMaxed('Y') and self.colorMaxed('B'):
                    self.lightBarInfo[2] = self.lightBarInfo[3] = 'G'
                    self.currAlphaDict['G'] = BASE_ALPHA
                    self.colorsFound.append('G')

        self.agents.remove(agent)
        self.updateLightBar = True

    def run(self):
        fpsClock = pygame.time.Clock()
        gameMode = MENU

        while gameMode is not QUIT:
            self.displaySurf.fill(BLACK)
            if gameMode is MENU:
                gameMode = self.showMenu(fpsClock)
            elif gameMode is PLAY:
                gameMode = self.playing(fpsClock)

            if gameMode is CREDITS: # Temp until handle credits
                gameMode = MENU

    def showMenu(self, fpsClock):
        MAXALPHA        = 260
        MINALPHA        = 90
        activeChoice    = PLAY
        playAlpha       = MAXALPHA
        creditsAlpha    = MINALPHA
        exitAlpha       = MINALPHA
        hi              = TILESIZE * 5
        wid             = TILESIZE * 20
        playPos         = (WIDTH / 2 - wid / 2, HEIGHT / 5)
        creditsPos      = (WIDTH / 2 - wid / 2, HEIGHT / 5 + hi*2)
        exitPos         = (WIDTH / 2 - wid / 2, HEIGHT / 5 + hi*4)
        playSurf        = pygame.Surface((wid, hi)).convert_alpha()
        creditsSurf     = pygame.Surface((wid, hi)).convert_alpha()
        exitSurf        = pygame.Surface((wid, hi)).convert_alpha()
        surf            = pygame.Surface((TILESIZE, TILESIZE))
        
        while 1:
            if activeChoice is PLAY:
                if playAlpha < MAXALPHA:
                    playAlpha += 10
            elif playAlpha > MINALPHA:
                    playAlpha -= 10

            if activeChoice is CREDITS:
                if creditsAlpha < MAXALPHA:
                    creditsAlpha += 10
            elif creditsAlpha > MINALPHA:
                    creditsAlpha -= 10
            
            if activeChoice is QUIT:
                if exitAlpha < MAXALPHA:
                    exitAlpha += 10
            elif exitAlpha > MINALPHA:
                    exitAlpha -= 10

            # self.handleMenuInput()
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_DOWN and activeChoice < QUIT:
                        activeChoice += 1
                    elif event.key == K_UP and activeChoice > PLAY:
                        activeChoice -= 1
                    elif event.key == K_ESCAPE:
                        return QUIT
                    elif event.key == K_RETURN:
                        return activeChoice

                if event.type == KEYUP:
                    pass
            
                if event.type == pygame.locals.QUIT:
                    self.quitGame()

            playSurf.fill(BLACK)
            surf.set_alpha(playAlpha)
            surf.fill(BLUE)
            for x in range(20):
                for y in range(5):
                    playSurf.blit(surf, (x*TILESIZE, y*TILESIZE))
            
            creditsSurf.fill(BLACK)
            surf.set_alpha(creditsAlpha)
            surf.fill(GREEN)
            for x in range(20):
                for y in range(5):
                    creditsSurf.blit(surf, (x*TILESIZE, y*TILESIZE))

            exitSurf.fill(BLACK)
            surf.set_alpha(exitAlpha)
            surf.fill(RED)
            for x in range(20):
                for y in range(5):
                    exitSurf.blit(surf, (x*TILESIZE, y*TILESIZE))

            self.displaySurf.blit(playSurf, playPos)
            self.displaySurf.blit(creditsSurf, creditsPos)
            self.displaySurf.blit(exitSurf, exitPos)

            pygame.display.update()
            fpsClock.tick(FPS)
            #print fpsClock.get_fps()

    def playing(self, fpsClock):
        fovCounter = 0        
        self.loadLevel(self.currLevel)

        def tileBlockes(x, y): 
            return self.level[x][y] == WALL

        # Player has LOS on (x,y)
        def markVisible(x, y): 
            if self.getDist(x*TILESIZE, y*TILESIZE) / TILESIZESQ \
                < PLAYER_RANGE**2:
                self.visibilityMap[x][y] = [EXPLORED, LIT]

        startTime = time.time()
        while 1:
            quit = self.handleInput()
            if quit is True:
                return MENU

            self.movePlayer(self.player)
            for guard in self.agents:
                guard.move()

            if fovCounter == 0:
                self.updateFOV(tileBlockes, markVisible)
                fovCounter = FOV_UPDATE_RATE
            else:
                fovCounter -= 1

            if not DEBUG and self.checkInLight():
                fovCounter = 0

            self.checkIfFoundCrystal()

            if self.checkLevelCompleted():
                if self.currLevel < self.maxLevel:
                    self.levelTime = time.time() - startTime
                    self.currLevel += 1
                    self.loadLevel(self.currLevel)
                else:
                    return MENU

            self.render()
            fpsClock.tick(FPS)

    def respawn(self):
        self.player.x = self.spawnPos[0] * TILESIZE
        self.player.y = self.spawnPos[1] * TILESIZE

    def checkIfFoundCrystal(self):
        i = 0
        while i < len(self.crystals):
            xCoord = self.getPlayerCoordX()
            yCoord = self.getPlayerCoordY()
            crystal = self.crystals[i]

            if xCoord is crystal.x and yCoord is crystal.y:
                self.colorsFound.append(crystal.color)
                self.currAlphaDict[crystal.color] += BASE_ALPHA
                del self.crystals[i]
                self.updateLightBar = True
                break
            i += 1   

    # Return true if level is completed
    def checkLevelCompleted(self):
        if not self.agents:
            return True
        return False

    def movePlayer(self, player):
        rect = pygame.Rect(player.x, player.y, PLAYERSIZE-1, PLAYERSIZE-1)

        if player.movingLeft:
            if self.isWall(rect.left - PLAYERSPEED, rect.top) or \
                self.isWall(rect.left - PLAYERSPEED, rect.bottom):
                player.x -= rect.left % TILESIZE
            else:
                player.x -= PLAYERSPEED

        if player.movingRight:
            if self.isWall(rect.right + PLAYERSPEED, rect.top) or \
                self.isWall(rect.right + PLAYERSPEED, rect.bottom):
                player.x += PLAYERSPEED - (rect.right + PLAYERSPEED) \
                % TILESIZE -1
            else:
                player.x += PLAYERSPEED

        if player.movingUp:
            if self.isWall(rect.left, rect.top - PLAYERSPEED) or \
                self.isWall(rect.right, rect.top - PLAYERSPEED):
                player.y -= rect.top % TILESIZE
            else:
                player.y -= PLAYERSPEED

        if player.movingDown:
            if self.isWall(rect.left, rect.bottom + PLAYERSPEED) or \
                self.isWall(rect.right, rect.bottom + PLAYERSPEED):
                player.y += PLAYERSPEED - (rect.bottom + PLAYERSPEED) \
                % TILESIZE -1
            else:
                player.y += PLAYERSPEED

    def tileLit(self, x, y):
        if self.visibilityMap[x][y][1] is LIT:
            return True
        return False

    def tileExplored(self, x, y):
        if self.visibilityMap[x][y][0] is EXPLORED:
            return True
        return False

    def tileColored(self, x, y):
        if self.lightMap[x][y] is None:
            return False
        return True

    def render(self):
        fog = pygame.Surface((TILESIZE, TILESIZE))

        fog.fill(BLACK)
        self.workSurf.fill(NOCOLOR)#, None, pygame.BLEND_RGBA_MULT)
        self.renderGuards()
        self.renderPlayer()

        #TODO only update tiles within player range + some
        for row in range(self.numRows):
            for col in range(self.numCols):
                x = col * TILESIZE
                y = row * TILESIZE

                tileRect = pygame.Rect(x, y, TILESIZE, TILESIZE)
             
                if self.tileLit(col, row):
                    if self.tileColored(col, row) and self.level[col][row] is OPEN:
                        agent = self.lightMap[col][row]
                        alpha =  abs(255 - (self.get2pDist(x, y, agent.x, agent.y) \
                            / TILESIZESQ)*12)
                        fog.fill(self.colorDict[agent.color])
                        fog.set_alpha(alpha)
                        self.workSurf.blit(fog, (x, y))
                        fog.fill(BLACK)

                    alpha = (self.getDist(x, y) / TILESIZESQ)*6
                    if alpha > FOG_ALPHA:
                        fog.set_alpha(FOG_ALPHA)
                    else:
                        fog.set_alpha(alpha)
                    self.workSurf.blit(fog, (x, y))
                elif self.tileExplored(col, row):
                    fog.set_alpha(FOG_ALPHA)
                    self.workSurf.blit(fog, (x, y))
                else:
                    pygame.draw.rect(self.workSurf, BLACK, tileRect)

        if(self.updateLightBar):
            self.lightBarSurf.fill(BLACK)
            offset = 0
            for color in self.lightBarInfo:
                self.lightBarElem.set_alpha(self.currAlphaDict[color])
                self.lightBarElem.fill(self.colorDict[color])
                self.lightBarSurf.blit(self.lightBarElem, (offset*self.elemWid, 0))
                offset += 1

            self.displaySurf.blit(self.lightBarSurf, (self.xMargin, self.yMargin - TILESIZE))
            self.updateLightBar = False

        self.renderCrystals()
        self.displaySurf.blit(self.levelSurf, (self.xMargin, self.yMargin))
        self.displaySurf.blit(self.workSurf, (self.xMargin, self.yMargin))
        pygame.display.update()

    def renderCrystals(self):
        for crystal in self.crystals:
            if self.tileLit(crystal.x, crystal.y):
                rect = pygame.Rect(crystal.x*TILESIZE, crystal.y*TILESIZE, TILESIZE, TILESIZE)
                pygame.draw.polygon(self.workSurf, self.colorDict[crystal.color], \
                    [[rect.midleft[0], rect.midleft[1]], \
                    [rect.midtop[0], rect.midtop[1]], [rect.midright[0], rect.midright[1]], \
                    [rect.midbottom[0], rect.midbottom[1]]], 0)

    def renderPlayer(self):
        pygame.draw.rect(self.workSurf, BLACK, pygame.Rect(self.player.x, \
            self.player.y, PLAYERSIZE, PLAYERSIZE))
        # pygame.draw.rect(self.workSurf, BLUE, pygame.Rect(self.player.x, \
        #     self.player.y, PLAYERSIZE, PLAYERSIZE/3))
        # pygame.draw.rect(self.workSurf, RED, pygame.Rect(self.player.x, \
        #     self.player.y + PLAYERSIZE/3, PLAYERSIZE, PLAYERSIZE/3))
        # pygame.draw.rect(self.workSurf, (255, 255, 0), pygame.Rect(self.player.x, \
        #      self.player.y + (PLAYERSIZE*2)/3, PLAYERSIZE, PLAYERSIZE/3))

    def renderGuards(self): pass
        # for guard in self.agents:
        #     x = self.getCoordX(guard.x)
        #     y = self.getCoordY(guard.y)
        #
            # if self.fovMap[x][y] is guard.color:
            #     pygame.draw.rect(self.workSurf, self.colorDict[guard.color], \
            #         pygame.Rect(guard.x, guard.y, GUARDSIZE, GUARDSIZE))

    # Return tilegrid x-coordinate
    def getCoordX(self, pos):
        return (pos + HALFPLAYERSIZE) / TILESIZE

    # Return tilegrid y-coordinate
    def getCoordY(self, pos):
        return (pos + HALFPLAYERSIZE) / TILESIZE

    # Return tilegrid x-coordinate
    def getPlayerCoordX(self):
        return (self.player.x + HALFPLAYERSIZE) / TILESIZE

    # Return tilegrid y-coordinate
    def getPlayerCoordY(self):
        return (self.player.y + HALFPLAYERSIZE) / TILESIZE

    # Return distance between player and (x,y) as squaresum
    # TODO? Currently uses player topleft not center
    def getDist(self, x, y):
        return abs(self.player.x - x)**2 + abs(self.player.y - y)**2

    def get2pDist(self, x, y, x1, y1):
        return abs(x1 - x)**2 + abs(y1 - y)**2

    def setFogAlpha(self, fog, dist):
        alpha = (dist / (TILESIZE**2)) * 7
        fog.set_alpha(alpha)

    # x, y coordinates without margins
    def isWall(self, x, y):
        return self.level[x / TILESIZE][y / TILESIZE] == WALL

    # Return true if esc was pressed
    def handleInput(self):
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_LEFT:
                    self.player.setMovingLeft(True)
                if event.key == K_RIGHT:
                    self.player.setMovingRight(True)       
                if event.key == K_UP:
                    self.player.setMovingUp(True)                           
                if event.key == K_DOWN:
                    self.player.setMovingDown(True)       
                if event.key == K_ESCAPE:
                    return True

            if event.type == KEYUP:
                if event.key == K_LEFT:
                    self.player.setMovingLeft(False)
                if event.key == K_RIGHT:
                    self.player.setMovingRight(False)       
                if event.key == K_UP:
                    self.player.setMovingUp(False)                           
                if event.key == K_DOWN:
                    self.player.setMovingDown(False)       

            if event.type == pygame.locals.QUIT:
                self.quitGame()
        return False

    # Set all tiles to be unlit and uncolored
    def resetFOV(self):
        if DEBUG:
            for col in range(self.numCols):
                for row in range(self.numRows):
                    self.lightMap[col][row] = None
        else:
            for col in range(self.numCols):
                for row in range(self.numRows):
                    self.visibilityMap[col][row][1] = UNLIT
                    self.lightMap[col][row] = None

    def updateFOV(self, tileBlocked, markVisible):
        if DEBUG:
            print "coords: ", self.getPlayerCoordX(), self.getPlayerCoordY()
        self.resetFOV()

        xCoord = self.getPlayerCoordX()
        yCoord = self.getPlayerCoordY()
        
        fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, PLAYER_RANGE, \
            markVisible, tileBlocked)

        for guard in self.agents:
            if self.guardFovInRange(guard):
                xCoord = self.getCoordX(guard.x)
                yCoord = self.getCoordY(guard.y)

                def markColored(x, y):
                    if self.tileLit(x, y) and \
                        self.get2pDist(guard.x, guard.y, x*TILESIZE, y*TILESIZE) \
                        / TILESIZESQ <= GUARD_RANGE**2:
                            self.lightMap[x][y] = guard

                fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, GUARD_RANGE, \
                    markColored, tileBlocked)

    def guardFovInRange(self, guard):
        return self.getDist(guard.x, guard.y) <= \
            ((PLAYER_RANGE + GUARD_RANGE) * TILESIZE)**2

    def quitGame(self):
        pygame.quit()
        sys.exit()

def main():
    g = Game()
    g.run()
    g.quitGame()

if __name__ == '__main__':
    main()
