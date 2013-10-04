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
        self.player1     = None
        self.level       = None
        self.spawnPos    = None
        self.guards      = []
        self.crystalsFound = []
        self.crystals    = []
        self.loadLevel()
        self.yMargin     = (HEIGHT - TILESIZE * self.numRows) / 2
        self.xMargin     = (WIDTH - TILESIZE  * self.numCols) / 2 
        self.fogMap      = [[UNEXPLORED]*self.numRows for i in range(self.numCols)]
        self.fovMap      = []
        self.lightMap    = [[None]*self.numRows for i in range(self.numCols)]

        self.displaySurf = pygame.display.set_mode((WIDTH, HEIGHT))
        self.levelSurf   = pygame.Surface((self.numCols * TILESIZE, \
            self.numRows * TILESIZE))
        self.workSurf    = self.levelSurf.copy().convert_alpha()

        self.makeLevelSurf()

        self.colorDict = {'R' : RED, 'B' : BLUE, 'P' : PURPLE}

        pygame.display.set_caption("Splinter block")

    def loadLevel(self):
        self.numRows    = 20
        self.numCols    = 80
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

        self.crystals.append((2,1))
        self.spawnPos   = (1, 1)
        self.player1    = Player(TILESIZE*self.spawnPos[0], TILESIZE*self.spawnPos[1])
        self.guards.append(Agent(((self.numCols-1,1), (self.numCols-1,18), (17,18), (17,1)), 1, 'R'))
        self.guards.append(Agent(((17,18), (17,1), (self.numCols-1,1), (self.numCols-1,18)), 1, 'B'))
        self.guards.append(Agent(((5,5), (5,19)), 1, 'P'))

    def makeLevelSurf(self):
        for row in range(self.numRows):
            for col in range(self.numCols):
                x        = col * TILESIZE
                y        = row * TILESIZE
                tileRect = pygame.Rect(x, y, TILESIZE, TILESIZE)

                if self.level[col][row] == WALL:
                    pygame.draw.rect(self.levelSurf, GRAY, tileRect)
                elif self.level[col][row] == OPEN:
                    pygame.draw.rect(self.levelSurf, GREEN, tileRect)

    def checkIfDied(self):
        color = self.lightMap[self.getPlayerCoordX()][self.getPlayerCoordY()]
        if color is not None and color not in self.crystalsFound:
            return True
        return False

    def run(self):
        fpsClock    = pygame.time.Clock()
        gameMode    = MENU

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
            self.fovMap[x][y] = VISIBLE
            self.fogMap[x][y] = EXPLORED

        while 1:
            quit = self.handleInput()
            if quit is True:
                return MENU

            self.movePlayer(self.player1)
            for guard in self.guards:
                guard.move()

            if fovCounter == 0:
                self.updateFOV(tileBlockes, markVisible)
                fovCounter = FOV_UPDATE_RATE
            else:
                fovCounter -= 1

            if self.checkIfDied():
                self.respawn()
                #Update fov immediatly after respawn
                fovCounter = 0

            self.checkIfFoundCrystal()

            if self.checkLevelCompleted():
                return MENU

            self.render()
            fpsClock.tick(FPS)

    def respawn(self):
        self.player1.x = self.spawnPos[0] * TILESIZE
        self.player1.y = self.spawnPos[1] * TILESIZE

    def checkIfFoundCrystal(self):
        if self.level[self.getPlayerCoordX()][self.getPlayerCoordY()] \
            is not OPEN:
            #add checks
            pass

    # Return true if level is completed
    def checkLevelCompleted(self):
        if not self.guards:
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
             
                #if self.fovMap[col][row] is LIT:
                 #   pass#pygame.draw.rect(self.workSurf, RED, tileRect)

                if self.fovMap[col][row] is VISIBLE:
                    if self.lightMap[col][row] is not None:
                        fog.fill(self.colorDict[self.lightMap[col][row]])
                        fog.set_alpha(255)
                        self.workSurf.blit(fog, (x, y))
                        fog.fill(BLACK)

                    alpha = (self.getDist(x, y) / TILESIZESQ)*6
                    if alpha > FOG_ALPHA:
                        fog.set_alpha(FOG_ALPHA)
                    else:
                        fog.set_alpha(alpha)
                    self.workSurf.blit(fog, (x, y))
                elif self.fogMap[col][row] is EXPLORED:
                    fog.set_alpha(FOG_ALPHA)
                    self.workSurf.blit(fog, (x, y))
                else:
                    pygame.draw.rect(self.workSurf, BLACK, tileRect)

        self.displaySurf.blit(self.levelSurf, (self.xMargin, self.yMargin))
        self.displaySurf.blit(self.workSurf, (self.xMargin, self.yMargin))
        pygame.display.update()

    def renderPlayer(self):
        pygame.draw.rect(self.workSurf, BLUE, pygame.Rect(self.player1.x, \
            self.player1.y, PLAYERSIZE, PLAYERSIZE))

    def renderGuards(self):
        for guard in self.guards:
            x = self.getCoordX(guard.x)
            y = self.getCoordY(guard.y)

            if self.fovMap[x][y] is guard.color:
                pygame.draw.rect(self.workSurf, self.colorDict[guard.color], \
                    pygame.Rect(guard.x, guard.y, GUARDSIZE, GUARDSIZE))

    # Return tilegrid x-coordinate
    def getCoordX(self, pos):
        return (pos + HALFPLAYERSIZE) / TILESIZE

    # Return tilegrid y-coordinate
    def getCoordY(self, pos):
        return (pos + HALFPLAYERSIZE) / TILESIZE

    # Return tilegrid x-coordinate
    def getPlayerCoordX(self):
        return (self.player1.x + HALFPLAYERSIZE) / TILESIZE

    # Return tilegrid y-coordinate
    def getPlayerCoordY(self):
        return (self.player1.y + HALFPLAYERSIZE) / TILESIZE

    # Return distance between player and (x,y) as squaresum
    # TODO? Currently uses player topleft not center
    def getDist(self, x, y):
        return abs(self.player1.x - x)**2 + abs(self.player1.y - y)**2

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
                    self.player1.setMovingLeft(True)
                if event.key == K_RIGHT:
                    self.player1.setMovingRight(True)       
                if event.key == K_UP:
                    self.player1.setMovingUp(True)                           
                if event.key == K_DOWN:
                    self.player1.setMovingDown(True)       
                if event.key == K_ESCAPE:
                    return True

            if event.type == KEYUP:
                if event.key == K_LEFT:
                    self.player1.setMovingLeft(False)
                if event.key == K_RIGHT:
                    self.player1.setMovingRight(False)       
                if event.key == K_UP:
                    self.player1.setMovingUp(False)                           
                if event.key == K_DOWN:
                    self.player1.setMovingDown(False)       

            if event.type == pygame.locals.QUIT:
                self.quitGame()
        return False
    
    def updateFOV(self, tileBlocked, markVisible):
        self.fovMap = [[NONE]*self.numRows for i in range(self.numCols)]
        self.lightMap    = [[None]*self.numRows for i in range(self.numCols)]

        xCoord = self.getPlayerCoordX()
        yCoord = self.getPlayerCoordY()
        
        fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, PLAYER_RANGE, \
            markVisible, tileBlocked)

        for guard in self.guards:
            if self.guardFovInRange(guard):
                xCoord = self.getCoordX(guard.x)
                yCoord = self.getCoordY(guard.y)

                def markLit(x, y):
                    if self.fovMap[x][y] == VISIBLE:
                        self.lightMap[x][y] = guard.color
                        #self.lightMap[x][y].append((guard.color, \
                         # (self.get2pDist(guard.x, guard.y, x*TILESIZE, y*TILESIZE) \
                          #  / TILESIZESQ)*6

                fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, GUARD_RANGE, \
                    markLit, tileBlocked)

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
