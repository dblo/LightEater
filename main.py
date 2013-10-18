#! /usr/bin/env python

import pygame, sys, fov, time
from pygame.locals import KEYDOWN, KEYUP, K_DOWN, K_UP, K_LEFT, K_RIGHT, \
    K_ESCAPE, K_RETURN
from constants import *
from player import Player
from agent import Agent
from crystal import Crystal

DEBUG  = False
if DEBUG:
    PLAYERSPEED *= 2

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("game")

        self.numRows        = 0
        self.numCols        = 0
        self.player         = None
        self.level          = 0
        self.spawnPos       = (0,0)
        self.yMargin        = 0
        self.xMargin        = 0
        self.numOfColors    = 0
        self.deathCount     = 0
        self.agents         = []
        self.crystals       = []
        self.visibilityMap  = []
        self.lightMap       = []
        self.colorDict      = {'R' : RED, 'B' : BLUE, 'P' : PURPLE,
                                'Y' : YELLOW, 'G' : GREEN, 'O' : ORANGE}
        self.currAlphaDict  = {}
        self.incAlphaDict   = {}
        self.colorsFound    = []
        self.bgColor        = None
        self.updateLightBar = False
        self.levelSurf      = None
        self.workSurf       = None
        self.lightBarSurf   = None
        self.displaySurf    = None
        self.width          = 0
        self.height         = 0
        self.maxLevel       = 4
        self.currLevel      = self.maxLevel
        self.bestTimes      = [[MAXTIME]*3 for i in range(self.maxLevel)]
        self.lightbarElemWid    = 0

        self.initWindow()
        #self.playMusic()
        self.readBestTimes()

    def initWindow(self):
        self.displaySurf    = pygame.display.set_mode((0,0))
        self.width          = 1600#self.displaySurf.get_width()
        self.height         = 900#self.displaySurf.get_height() # TODO

        # Workaround for linux >1 monitors
        if self.width > self.height * 2:
            self.width /= 2
        self.displaySurf = pygame.display.set_mode((self.width, self.height))

    def playMusic(self):
        pygame.mixer.init()
        pygame.mixer.music.load('music.mp3')
        pygame.mixer.music.play(-1)

    def loadLevel(self, levelNum):
        playerSpawnOffset = (TILESIZE - PLAYERSIZE) / 2

        level           = self.getLevel(levelNum)
        levelDims       = level[0].split()

        # +2 for surrounding walls
        self.numCols    = int(levelDims[0]) + 2
        self.numRows    = int(levelDims[1]) + 2
        self.spawnPos   = (int(level[1].split()[0]), int(level[1].split()[1]))
        self.player     = Player(TILESIZE*self.spawnPos[0] + playerSpawnOffset,
                                TILESIZE*self.spawnPos[1] + playerSpawnOffset,
                                PLAYERSPEED, PLAYERSIZE)
        self.yMargin    = (self.height - TILESIZE * self.numRows) / 2
        self.xMargin    = (self.width - TILESIZE  * self.numCols) / 2 
        self.level      = [[OPEN]*self.numRows for i in range(self.numCols)]
        self.bgColor    = BGCOLORS[1]
        self.updateLightBar = True

        self.agents         = []
        self.crystals       = []
        self.colorsFound    = []
        self.currAlphaDict  = {}
        self.incAlphaDict   = {}
        self.deathCount     = 0
        
        crystalsList = level[2].split()
        numOfCrystals = len(crystalsList) / 3
        for i in range(numOfCrystals):
            self.crystals.append(Crystal(int(crystalsList[i*3]), \
                int(crystalsList[i*3 + 1]), crystalsList[i*3 + 2]))

        agentCount = int(level[3])
        agentColorDict = self.addAgents(level, agentCount)

        if numOfCrystals is 3:
            self.numOfColors = 6
        elif numOfCrystals is 2:
            self.numOfColors = 3
        else:
            self.numOfColors = 1

        self.setColorAlphas(agentColorDict)
        self.setMap(level, agentCount)
        self.setSurfaces()
        self.setVisibilityMap()

    # Calculate by how much the alpha in the lightbar should increase when
    # the player eats a light, for that color
    def setColorAlphas(self, agentColorDict):
        alphaToFill = AGENT_MAX_ALPHA - BASE_ALPHA
        for color in agentColorDict:
            self.currAlphaDict[color] = 0
            if agentColorDict[color] is not 0:
                self.incAlphaDict[color]  = \
                    (alphaToFill / agentColorDict[color]) + 1

    # Return level as list
    def getLevel(self, levelNum):
        levelFile  = open('levels.txt')
        line       = levelFile.readline()
        level      = []
        levelString = "level " + str(levelNum) + "\n"

        # Find block of levelNum
        while line != levelString:
            line = levelFile.readline()
            assert line != "EOF\n", "Error reading level " + str(levelNum)

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
        levelDescriptLine = 4 + agentCount

        # set inner area of map
        for row in range(1, self.numRows-1):
            line = list(level[levelDescriptLine])
            for col in range(1, self.numCols-1):
                if line[col-1] == 'W':
                    self.level[col][row] = WALL
                elif line[col-1] == '-':
                    self.level[col][row] = OPEN
                elif line[col-1] == 'H':
                    self.level[col][row] = HOLE
                else: #S
                    self.level[col][row] = SAFE

            levelDescriptLine += 1

    # Return dictionary containing number of agents of each color
    def addAgents(self, level, agentCount):
        colorCountDict = {'B':0, 'R':0, 'Y':0, 'P':0, 'O':0, 'G':0}

        for i in range(agentCount):
            patrolList = []
            coordList = level[4+i].split()

            for j in range((len(coordList)-3)/2):
                patrolList.append((int(coordList[j*2]), int(coordList[j*2+1])))
            
            self.agents.append(Agent(patrolList, coordList[-3], \
                                 coordList[-2], coordList[-1]))
            colorCountDict[coordList[-3]] += 1
        return colorCountDict

    def setSurfaces(self):
        self.lightMap       = [[None]*self.numRows for i in range(self.numCols)]
        self.levelSurf      = pygame.Surface((self.numCols * TILESIZE, \
            self.numRows * TILESIZE))
        self.workSurf       = self.levelSurf.copy().convert_alpha()
        self.lightBarSurf   = pygame.Surface((self.numCols * TILESIZE, 
            TILESIZE)).convert()

        self.lightbarElemWid = (TILESIZE*self.numCols) / LIGHTBAR_ELEMS
        if self.lightbarElemWid % 2 is 1:
            self.lightbarElemWid += 1
        self.lightBarElem = pygame.Surface((self.lightbarElemWid, 
            TILESIZE)).convert()
        self.makeLevelSurf()
        self.displaySurf.fill(BLACK)

    def setVisibilityMap(self):
        if DEBUG:
            self.visibilityMap = [[[EXPLORED, LIT] \
            for j in range(self.numRows)] for i in range(self.numCols)]
        else:    
            self.visibilityMap = [[[UNEXPLORED, UNLIT] \
             for j in range(self.numRows)] for i in range(self.numCols)]

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
                    pygame.draw.rect(self.levelSurf, self.bgColor, tileRect)
                elif self.level[col][row] == HOLE:
                    pygame.draw.rect(self.levelSurf, BLACK, tileRect)
                else:
                    pygame.draw.rect(self.levelSurf, self.bgColor, tileRect)
                    pygame.draw.circle(self.levelSurf, SAFECOLOR, 
                        (x+TILESIZE/2, y+TILESIZE/2), TILESIZE / 4)

                    
    # Return true if player died or absorbed a light
    def checkInLight(self):
        agentList = self.lightMap[self.getPlayerCoordX()][self.getPlayerCoordY()]
        if not agentList:
            return False

        for agent in agentList:
            if agent.color not in self.colorsFound:
                self.respawn()
            else:
                self.absorbLight(agent)
        return True

    # Return true if all agents of given color has been absorbed
    def colorMaxed(self, color):
        return self.currAlphaDict[color] >= AGENT_MAX_ALPHA

    # Remove light and update lightbar color alpha
    def absorbLight(self, agent):
        absColor = agent.color
        self.currAlphaDict[absColor] += self.incAlphaDict[absColor]

        if self.numOfColors is 6:
            self.checkMaxedColors(absColor,1)
        elif self.numOfColors is 3:
            self.checkMaxedColors(absColor, 2)
        
        self.agents.remove(agent)
        self.updateLightBar = True

    # Check if 2 colors were maxed and should merge into a new color
    def checkMaxedColors(self, absColor, elemWid):
        self.checkMaxedColorsHelper(absColor, ['B', 'Y'], 'G', elemWid)
        self.checkMaxedColorsHelper(absColor, ['B', 'R'], 'P', elemWid)
        self.checkMaxedColorsHelper(absColor, ['R', 'Y'], 'O', elemWid)

    # compColors is a list of two colors that merge into newColor
    def checkMaxedColorsHelper(self, absColor, compColors, newColor, elemWid):
        if absColor in compColors:
            if self.colorMaxed(compColors[0]) and \
                self.colorMaxed(compColors[1]):
                self.colorsFound += list(newColor)*elemWid
                self.currAlphaDict[newColor] = BASE_ALPHA
                
    def run(self):
        fpsClock = pygame.time.Clock()
        gameMode = MENU

        while gameMode is not QUIT:
            self.displaySurf.fill(BLACK)
            if gameMode is MENU:
                gameMode = self.showMenu(fpsClock)
            elif gameMode is LEVEL:
                gameMode = self.showLevelsMenu(fpsClock)
            elif gameMode is PLAY:
                gameMode = self.playing(fpsClock)
            elif gameMode is CREDITS:
                gameMode = self.showCredits(fpsClock)

    def showLevelsMenu(self, fpsClock):
        font = pygame.font.Font(None,40)
        levelTextX = self.width / 2 - 150
        levelTextY = self.height / 2 - 20
        
        while 1:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_DOWN and self.currLevel < self.maxLevel:
                        self.currLevel += 1
                    elif event.key == K_UP and self.currLevel > 1:
                        self.currLevel -= 1
                    elif event.key == K_ESCAPE:
                        return MENU
                    elif event.key == K_RETURN:
                        return PLAY

                if event.type == pygame.locals.QUIT:
                    self.quitGame()
            self.displaySurf.fill(BLACK)

            levelText = font.render("Level " + str(self.currLevel), 1, ORANGE)
            bestTimeText = font.render("Best times: ", 1, GREEN)
            self.displaySurf.blit(bestTimeText, (levelTextX+150, levelTextY-50))

            for i in range(3):
                timeText = str(self.bestTimes[self.currLevel-1][i])
                if timeText == str(MAXTIME):
                    timeText = "--"

                bestTimeText = font.render(timeText + " seconds", 1, GREEN)
                self.displaySurf.blit(bestTimeText, (levelTextX+150, \
                                                        levelTextY+i*50))

            self.displaySurf.blit(levelText, (levelTextX, levelTextY))
            pygame.display.update()
            fpsClock.tick(FPS)

    def showCredits(self, fpsClock):
        font = pygame.font.Font(None,40)
        levelTextX = self.width / 2 - 200
        levelTextY = self.height / 2 - 20
        
        while 1:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        return MENU
                    elif event.key == K_RETURN:
                        return MENU

                if event.type == pygame.locals.QUIT:
                    self.quitGame()

            text = font.render("Game made by Olle Olsson", 1, YELLOW)
            self.displaySurf.fill(BLACK)
            self.displaySurf.blit(text, (levelTextX, levelTextY))
            pygame.display.update()
            fpsClock.tick(FPS)

    def showMenu(self, fpsClock):
        MAXALPHA        = 260
        MINALPHA        = 40
        activeChoice    = LEVEL
        playAlpha       = MAXALPHA
        creditsAlpha    = MINALPHA
        exitAlpha       = MINALPHA
        
        while 1:
            if activeChoice is LEVEL:
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

            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_DOWN and activeChoice < QUIT:
                        activeChoice += 1
                    elif event.key == K_UP and activeChoice > LEVEL:
                        activeChoice -= 1
                    elif event.key == K_ESCAPE:
                        return QUIT
                    elif event.key == K_RETURN:
                        return activeChoice

                if event.type == pygame.locals.QUIT:
                    self.quitGame()

            self.renderMainMenu(playAlpha, creditsAlpha, exitAlpha)
            fpsClock.tick(FPS)

    def renderMainMenu(self, playAlpha, creditsAlpha, exitAlpha):
        hi              = TILESIZE * 5
        wid             = TILESIZE * 19
        playPos         = (self.width / 2 - wid , self.height / 5)
        creditsPos      = (self.width / 2 - wid/4, self.height / 5 + hi*2)
        exitPos         = (self.width / 2 + (wid*6)/7, self.height / 5 + hi*4)
        playSurf        = pygame.Surface((wid, hi)).convert_alpha()
        creditsSurf     = pygame.Surface((wid, hi)).convert_alpha()
        exitSurf        = pygame.Surface((wid, hi)).convert_alpha()
        surf            = pygame.Surface((200, 100))
        font            = pygame.font.Font(None,80)
        infoFont        = pygame.font.Font(None,40)

        text = font.render("Play", 1, BLUE)
        surf.fill(BLACK)
        surf.set_alpha(playAlpha)
        surf.blit(text, (0, 0))
        playSurf.blit(surf, (0,0))
        
        text = font.render("Credits", 1, YELLOW)
        surf.fill(BLACK)
        surf.set_alpha(creditsAlpha)
        surf.blit(text, (0, 0))
        creditsSurf.blit(surf, (0,0))

        text = font.render("Exit", 1, RED)
        surf.fill(BLACK)
        surf.set_alpha(exitAlpha)
        surf.blit(text, (0, 0))
        exitSurf.blit(surf, (0,0))

        infoText = infoFont.render("Move with arrow keys, select with enter, back up with esc", 
            1, PURPLE)
        infoTextX = self.width / 2 - infoText.get_width() / 2
        infoTextY = self.height - infoText.get_height()
        self.displaySurf.blit(infoText, (infoTextX, infoTextY))
        self.displaySurf.blit(playSurf, playPos)
        self.displaySurf.blit(creditsSurf, creditsPos)
        self.displaySurf.blit(exitSurf, exitPos)
        pygame.display.update()

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
        debugY = 0
        debugX = 0

        while 1:
            quit = self.handleInput()
            if quit is True:
                return LEVEL
            if DEBUG:
                if debugX != self.getPlayerCoordX() or \
                   debugY != self.getPlayerCoordY():
                   debugX = self.getPlayerCoordX() 
                   debugY = self.getPlayerCoordY()

            self.movePlayer(self.player)
            
            if self.fellIntoHole():
                self.respawn()

            for agent in self.agents:
                agent.move()

            if not DEBUG and self.checkInLight():
                fovCounter = 0

            if fovCounter == 0:
                self.updateFOV(tileBlockes, markVisible)
                fovCounter = FOV_UPDATE_RATE
            else:
                fovCounter -= 1

            self.checkIfFoundCrystal()

            if self.checkLevelCompleted():
                newTime = float((int((time.time() - startTime)*100)))/100.0
                self.checkIfRecordTime(newTime)
                if self.currLevel < self.maxLevel:
                    self.currLevel += 1
                    self.loadLevel(self.currLevel)
                else:
                    return MENU

            self.render()
            fpsClock.tick(FPS)
            #print fpsClock.get_fps()

    # If time is new top3 time, store it and move other times appropriately
    def checkIfRecordTime(self, time):
        time += self.deathCount*DEATH_PENALTY
        i = 0
        while i < 3:
            if time < float(self.bestTimes[self.currLevel-1][i]):
                # new top3 time found, move others down in record list
                j = 2
                while j > i:
                    self.bestTimes[self.currLevel-1][j] = self.bestTimes[self.currLevel-1][j-1]
                    j -= 1

                self.bestTimes[self.currLevel-1][i] = time
                break
            i += 1

    def respawn(self):
        self.player.setPos(self.spawnPos[0] * TILESIZE,
            self.spawnPos[1] * TILESIZE)
        self.deathCount += 1

    # Check if a crystal was found, if so add it to found and remove from map
    def checkIfFoundCrystal(self):
        i = 0
        xCoord = self.getPlayerCoordX()
        yCoord = self.getPlayerCoordY()

        while i < len(self.crystals):
            crystal = self.crystals[i]

            if xCoord is crystal.x and yCoord is crystal.y:
                if self.numOfColors is 6:
                    self.colorsFound.append(crystal.color)
                elif self.numOfColors is 3:
                    self.colorsFound += list(crystal.color)*2
                else:
                    self.colorsFound += list(crystal.color)*6

                self.currAlphaDict[crystal.color] += BASE_ALPHA
                del self.crystals[i]
                self.updateLightBar = True
                break
            i += 1   

    # Return true if fell into hole
    def fellIntoHole(self):
        x = self.getPlayerCoordX()
        y = self.getPlayerCoordY()
        return self.level[x][y] == HOLE

    # Return true if level is completed
    def checkLevelCompleted(self):
        if not self.agents:
            return True
        return False

    def movePlayer(self, player):
        nextPlayerX = self.player.nextX()
        nextPlayerY = self.player.nextY()

        if player.movingLeft:
            if (self.isWall(nextPlayerX, self.player.y) or 
                self.isWall(nextPlayerX, self.player.y + PLAYERSIZE)):
                self.player.clampLeft(TILESIZE)
            else:
                self.player.moveLeft()

        if player.movingRight:
            if (self.isWall(nextPlayerX + PLAYERSIZE, self.player.y) or 
                self.isWall(nextPlayerX + PLAYERSIZE, self.player.y + PLAYERSIZE)):
                self.player.clampRight(TILESIZE)
            else:
                self.player.moveRight()

        if player.movingUp:
            if (self.isWall(self.player.x, nextPlayerY) or 
                self.isWall(self.player.x + PLAYERSIZE, nextPlayerY)):
                self.player.clampUp(TILESIZE)
            else:
                self.player.moveUp()

        if player.movingDown:
            if (self.isWall(self.player.x, nextPlayerY + PLAYERSIZE) or 
                self.isWall(self.player.x + PLAYERSIZE, nextPlayerY + PLAYERSIZE)):
                self.player.clampDown(TILESIZE)
            else:
                self.player.moveDown()
        
    def tileLit(self, x, y):
        if self.visibilityMap[x][y][1] is LIT:
            return True
        return False

    def tileExplored(self, x, y):
        if self.visibilityMap[x][y][0] is EXPLORED:
            return True
        return False

    def tileColored(self, x, y):
        if self.lightMap[x][y]:
            return True
        return False

    def render(self):
        fog = pygame.Surface((TILESIZE, TILESIZE))
        fog.fill(FOG_COLOR)
        self.workSurf.fill(NOCOLOR)

        self.renderPlayer()

        for row in range(self.numRows):
            for col in range(self.numCols):
                x = col * TILESIZE
                y = row * TILESIZE

                tileRect = pygame.Rect(x, y, TILESIZE, TILESIZE)
             
                if self.tileLit(col, row):
                    if self.tileColored(col, row):
                        for agent in self.lightMap[col][row]:
                            alpha =  MAX_ALPHA / ((self.get2pDist(x, y, agent.x, agent.y) \
                                / TILESIZESQ) + 1)

                            fog.fill(self.colorDict[agent.color])
                            fog.set_alpha(alpha)
                            self.workSurf.blit(fog, (x, y))
                            fog.fill(FOG_COLOR)

                    # Draw heavier fog the further a lit area is from player
                    if not DEBUG:
                        alpha = (self.getDist(x, y) / TILESIZESQ)*ALPHA_FACTOR
                        if alpha > FOG_ALPHA:
                            fog.set_alpha(FOG_ALPHA)
                        else:
                            fog.set_alpha(alpha)
                        self.workSurf.blit(fog, (x, y))
                elif self.tileExplored(col, row):
                    fog.set_alpha(FOG_ALPHA)
                    self.workSurf.blit(fog, (x, y))
                else:
                    pygame.draw.rect(self.workSurf, FOG_COLOR, tileRect)

        if(self.updateLightBar):
            self.renderLightbar()
            self.updateLightBar = False

        self.renderCrystals()
        self.displaySurf.blit(self.levelSurf, (self.xMargin, self.yMargin))
        self.displaySurf.blit(self.workSurf, (self.xMargin, self.yMargin))
        pygame.display.update()


    def renderLightbar(self):
        self.lightBarSurf.fill(BLACK)
        offset = 0
        for color in self.colorsFound:
            self.lightBarElem.set_alpha(self.currAlphaDict[color])
            self.lightBarElem.fill(self.colorDict[color])
            self.lightBarSurf.blit(self.lightBarElem, (offset*self.lightbarElemWid, 0))
            offset += 1

        self.displaySurf.blit(self.lightBarSurf, (self.xMargin, self.yMargin - TILESIZE))

    def renderCrystals(self):
        for crystal in self.crystals:
            if self.tileLit(crystal.x, crystal.y):
                rect = pygame.Rect(crystal.x*TILESIZE, crystal.y*TILESIZE, TILESIZE, TILESIZE)
                pygame.draw.polygon(self.workSurf, self.colorDict[crystal.color], \
                    [[rect.midleft[0], rect.midleft[1]], \
                    [rect.midtop[0], rect.midtop[1]], [rect.midright[0], rect.midright[1]], \
                    [rect.midbottom[0], rect.midbottom[1]]], 0)

    def renderPlayer(self):
        pygame.draw.rect(self.workSurf, WHITE, pygame.Rect(self.player.x, \
            self.player.y, PLAYERSIZE, PLAYERSIZE))

    # Return tilegrid x-coordinate
    def getAgentCoordX(self, pos):
        return (pos + HALF_GUARD_SIZE) / TILESIZE

    # Return tilegrid y-coordinate
    def getAgentCoordY(self, pos):
        return (pos + HALF_GUARD_SIZE) / TILESIZE

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
                    self.lightMap[col][row] = []
        else:
            for col in range(self.numCols):
                for row in range(self.numRows):
                    self.visibilityMap[col][row][1] = UNLIT
                    self.lightMap[col][row] = []

    def updateFOV(self, tileBlockes, markVisible):
        self.resetFOV()

        xCoord = self.getPlayerCoordX()
        yCoord = self.getPlayerCoordY()
        fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, PLAYER_RANGE, \
            markVisible, tileBlockes)

        for agent in self.agents:
            if DEBUG or self.guardFovInRange(agent):
                xCoord = self.getAgentCoordX(agent.x)
                yCoord = self.getAgentCoordY(agent.y)

                # TODO
                def markColored(x, y):
                    if self.tileLit(x, y) and not tileBlockes(x, y) and\
                        self.get2pDist(agent.x, agent.y, x*TILESIZE, y*TILESIZE) \
                        / TILESIZESQ <= agent.range**2:
                            self.lightMap[x][y].append(agent)

                fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, agent.range, \
                    markColored, tileBlockes)

    def guardFovInRange(self, agent):
        return self.getDist(agent.x, agent.y) <= \
            ((PLAYER_RANGE + agent.range) * TILESIZE)**2

    def quitGame(self):
        self.saveTimes()
        pygame.quit()
        sys.exit()

    def saveTimes(self):
        dataFile = open('data.txt', 'w')
        output = ""
        for i in self.bestTimes:
            for j in i:
                output += str(j) + " "
            output += "\n"
        dataFile.write(output)
        dataFile.close()

    def readBestTimes(self):
        dataFile = open('data.txt')
        i = 0
        for line in dataFile:
            line = line.split()
            self.bestTimes[i] = line
            i += 1
        dataFile.close()

def main():
    g = Game()
    g.run()
    g.quitGame()

if __name__ == '__main__':
    main()
