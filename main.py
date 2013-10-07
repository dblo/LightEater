#! /usr/bin/env python

import pygame, sys, fov, random
from pygame.locals import KEYDOWN, KEYUP, K_DOWN, K_UP, K_LEFT, K_RIGHT, K_ESCAPE, K_RETURN
from constants import *
from player import Player
from agent import Agent

class Game:
    def __init__(self):
        pygame.init()
        self.numRows     = None
        self.numCols     = None
        self.player      = None
        self.level       = None
        self.spawnPos    = None
        self.agents      = []
        self.crystalsFound = []
        self.crystals    = []
        self.lightBarInfo = []
        self.colorDict = {'R' : RED, 'B' : BLUE, 'P' : PURPLE, 'Y' : YELLOW}
        self.currAlphaDict = {'R' : 0, 'B' : 0, 'P' : 0, 'Y' : 0}
        self.incAlphaDict = {'R' : 0, 'B' : 0, 'P' : 0, 'Y' : 0}

        self.loadLevel1()
        self.yMargin     = (HEIGHT - TILESIZE * self.numRows) / 2
        self.xMargin     = (WIDTH - TILESIZE  * self.numCols) / 2 
        self.visibilityMap = None
        self.lightMap    = [[None]*self.numRows for i in range(self.numCols)]
        self.setVisibilityMap()

        self.displaySurf = pygame.display.set_mode((WIDTH, HEIGHT))
        self.levelSurf   = pygame.Surface((self.numCols * TILESIZE, \
            self.numRows * TILESIZE))
        self.workSurf    = self.levelSurf.copy().convert_alpha()
        self.lightBarSurf = pygame.Surface((self.numCols * TILESIZE, TILESIZE)).convert()
        self.makeLevelSurf()
        pygame.display.set_caption("Splinter block")

    def loadLevel(self):
        self.numRows    = 10
        self.numCols    = 20
        self.level      = [[OPEN]*self.numRows for i in range(self.numCols)]

        for i in range(100):
            x = random.randint(1, self.numCols-1)
            y = random.randint(1, self.numRows-1)
            self.level[x][y] = WALL

        for i in range(self.numCols):
            self.level[i][0] = WALL
            self.level[i][self.numRows-1] = WALL

        for i in range(self.numRows):
            self.level[0][i] = WALL
            self.level[self.numCols-1][i] = WALL

        self.spawnPos   = (1, 1)
        self.player     = Player(TILESIZE*self.spawnPos[0]+1, TILESIZE*self.spawnPos[1]+1)
        self.agents.append(Agent(((-1,1), (self.numCols-1,18), (17,18), (17,1)), 1, 'B'))
        self.agents.append(Agent(((17,18), (17,1), (self.numCols-1,1), (self.numCols-1,18)), 1, 'B'))
        self.crystals.append((3,1,'B'))

    def loadLevel1(self):
        self.numRows    = 10
        self.numCols    = 10
        self.level      = [[OPEN]*self.numRows for i in range(self.numCols)]

        for i in range(self.numCols):
            self.level[i][0] = WALL
            self.level[i][self.numRows-1] = WALL

        for i in range(self.numRows):
            self.level[0][i] = WALL
            self.level[self.numCols-1][i] = WALL

        for i in range(6):
            self.level[3][i+1] = WALL

        for i in range(4):
            self.level[6][i+3] = WALL

        self.lightBarInfo = [['B', 0]]*6

        self.spawnPos   = (1, 1)
        self.player     = Player(TILESIZE*self.spawnPos[0], TILESIZE*self.spawnPos[1])
        self.agents.append(Agent(((2,7), (2,8), (7,8), (7,7)), 1, 'B'))
        self.agents.append(Agent(((5,2), (5,7), (7,7), (7,2)), 1, 'B'))
        self.crystals.append((8,1,'B',55))
        self.incAlphaDict['B'] = 100

    def setVisibilityMap(self):
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

        if agent.color not in self.crystalsFound:
            self.respawn()
        else:
            self.absorbLight(agent)
        return True

    def absorbLight(self, agent):
        self.currAlphaDict[agent.color] += self.incAlphaDict[agent.color]
        self.agents.remove(agent)

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

    #def handleMenuInput(self, activeChoice):

    def playing(self, fpsClock):
        fovCounter  = 0        

        def tileBlockes(x, y): 
            return self.level[x][y] == WALL

        # Player has LOS on (x,y)
        def markVisible(x, y): 
            if self.getDist(x*TILESIZE, y*TILESIZE) / TILESIZESQ \
                < PLAYER_RANGE**2:
                self.visibilityMap[x][y] = [EXPLORED, LIT]

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

            if self.checkInLight():
                fovCounter = 0

            self.checkIfFoundCrystal()

            if self.checkLevelCompleted():
                pass#return MENU

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
            if xCoord is self.crystals[i][0] and yCoord is self.crystals[i][1]:
                self.crystalsFound.append(self.crystals[i][2])
                self.currAlphaDict[self.crystals[i][2]] += self.crystals[i][3]
                del self.crystals[i]
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
                    if self.tileColored(col, row):
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


        #for area in self.lightBarInfo:
        #fog.set_alpha(area[1])
        #fog.fill(area[0])
        self.lightBarSurf.fill(BLACK)
        fog.set_alpha(self.currAlphaDict['B'])
        fog.fill(BLUE)
        for i in range(self.numCols):
            self.lightBarSurf.blit(fog, (i*TILESIZE, 0))

        self.renderCrystals()
        self.displaySurf.blit(self.lightBarSurf, (self.xMargin, self.yMargin - TILESIZE))
        self.displaySurf.blit(self.levelSurf, (self.xMargin, self.yMargin))
        self.displaySurf.blit(self.workSurf, (self.xMargin, self.yMargin))
        pygame.display.update()

    def renderCrystals(self):
        for crystal in self.crystals:
            if self.tileLit(crystal[0], crystal[1]):
                rect = pygame.Rect(crystal[0]*TILESIZE, crystal[1]*TILESIZE, TILESIZE, TILESIZE)
                pygame.draw.polygon(self.workSurf, self.colorDict[crystal[2]], \
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
        for col in range(self.numCols):
            for row in range(self.numRows):
                self.visibilityMap[col][row][1] = UNLIT
                self.lightMap[col][row] = None

    def updateFOV(self, tileBlocked, markVisible):
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
