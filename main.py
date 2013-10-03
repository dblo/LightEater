#! /usr/bin/env python

import pygame, sys
from pygame.locals import *
import fov, random

FPS         = 30
PLAYERSPEED = 2
TILESIZE    = 20
TILESIZESQ  = TILESIZE**2
PLAYERSIZE  = TILESIZE
HALFPLAYERSIZE = PLAYERSIZE / 2
GUARDSIZE   = TILESIZE
PLAYERRANGE = 4
GUARDRANGE  = 3
WIDTH       = 1600
HEIGHT      = 800
WALL        = 0
OPEN        = 1
UNEXPLORED  = 0
EXPLORED    = 1
LIT         = 2
INLOS       = 1
UNKNOWN     = 0

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (255, 0,   0)
GRAY    = (100, 100, 100)
GREEN   = (0,   255,   0)
BLUE    = (0,   0,   255)
FOW     = (10, 170, 10, 125)
NOCOLOR = (255, 0, 255, 0)

assert PLAYERSIZE % 2 == 0, "Playersize not even"
# assert TILESIZE % PLAYERSIZE == 0, "Bad tilesize - playersize ratio"

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.movingLeft     = False
        self.movingRight    = False
        self.movingUp       = False
        self.movingDown     = False

    def setMovingLeft(self, move):
        self.movingLeft = move

    def setMovingRight(self, move):
        self.movingRight = move

    def setMovingUp(self, move):
        self.movingUp = move

    def setMovingDown(self, move):
        self.movingDown = move

class Guard:
    def __init__(self, route, speed):
        self.route = route
        self.speed = speed
        self.currInstr = 1

        self.x = route[0][0] * TILESIZE
        self.y = route[0][1] * TILESIZE
        self.goalX = route[1][0] * TILESIZE
        self.goalY = route[1][1] * TILESIZE

    def move(self):
        if self.x < self.goalX:
            self.x += self.speed
        elif self.x > self.goalX:
            self.x -= self.speed

        if self.y < self.goalY:
            self.y += self.speed
        elif self.y > self.goalY:
            self.y -= self.speed

        if abs(self.x - self.goalX) < self.speed:
            self.x = self.goalX

        if abs(self.y - self.goalY) < self.speed:
            self.y = self.goalY

        if self.x == self.goalX and self.y == self.goalY:
            self.currInstr = (self.currInstr + 1) % len(self.route)
            self.goalX = self.route[self.currInstr][0] * TILESIZE
            self.goalY = self.route[self.currInstr][1] * TILESIZE

class Game:
    def __init__(self):
        pygame.init()

        self.numRows     = 20
        self.numCols     = 80
        self.yMargin     = (HEIGHT - TILESIZE * self.numRows) / 2
        self.xMargin     = (WIDTH - TILESIZE  * self.numCols) / 2 
        self.player1     = Player(TILESIZE, TILESIZE)
        self.level       = [[OPEN for j in range(self.numRows)] for i in range(self.numCols)]
        self.fogMap      = [[UNEXPLORED for j in range(self.numRows)] for i in range(self.numCols)]

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

        self.guards = []
        self.guards.append(Guard(((self.numCols-1,1), (self.numCols-1,18), (17,18), (17,1)), 1))
        self.guards.append(Guard(((17,18), (17,1), (self.numCols-1,1), (self.numCols-1,18)), 1))
        self.guards.append(Guard(((5,5), (5,19)), 1))

        self.fovMap = []

        self.displaySurf = pygame.display.set_mode((WIDTH, HEIGHT))
        self.levelSurf   = pygame.Surface((self.numCols * TILESIZE, \
            self.numRows * TILESIZE))
        self.makeLevelSurf()

        self.workSurf    = pygame.Surface((self.numCols * TILESIZE, \
            self.numRows * TILESIZE)).convert_alpha()

        pygame.display.set_caption("Splinter block")
        self.run()

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

    def run(self):
        fpsClock = pygame.time.Clock()
        fovCounter = 0        

        def tileBlockes(x, y): 
            return self.level[x][y] == WALL

        # Player has LOS on (x,y)
        def markVisible(x, y): 
            self.fovMap[x][y] = INLOS
            self.fogMap[x][y] = EXPLORED

        # Guard had LOS on (x,y)
        def markLit(x, y):
            if self.fovMap[x][y] == INLOS:
                self.fovMap[x][y] = LIT

        while 1:
            self.handleInput()
            self.movePlayer(self.player1)
            for guard in self.guards:
                guard.move()

            if fovCounter == 0:
                self.updateFOV(tileBlockes, markVisible, markLit)
                self.checkIfCaught()
                fovCounter = FPS / 2
            else:
                fovCounter -= 1
            self.render()
            fpsClock.tick(FPS)

    def checkIfCaught(self):
        if self.fovMap[(self.player1.x) / TILESIZE] \
            [(self.player1.y) / TILESIZE] == LIT:
            pass

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

        for row in range(self.numRows):
            for col in range(self.numCols):
                x = col * TILESIZE
                y = row * TILESIZE

                tileRect = pygame.Rect(x, y, TILESIZE, TILESIZE)
             
                if self.fovMap[col][row] is LIT:
                    pass #pygame.draw.rect(self.workSurf, RED, tileRect)

                if self.fovMap[col][row] >= INLOS:
                    fog.set_alpha((self.getDist(x, y) / TILESIZE**2)*7)
                    self.workSurf.blit(fog, (x, y))
                elif self.fogMap[col][row] is EXPLORED:
                    fog.set_alpha(220)
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

            if self.fovMap[x][y] == LIT:
                pygame.draw.rect(self.workSurf, RED, pygame.Rect(guard.x, \
                    guard.y, GUARDSIZE, GUARDSIZE))

    def getCoordX(self, pos):
        return (pos + HALFPLAYERSIZE) / TILESIZE

    def getCoordY(self, pos):
        return (pos + HALFPLAYERSIZE) / TILESIZE

    # Return distance between player and (x,y) as squaresum
    def getDist(self, x, y):
        return abs(self.player1.x - x)**2 + abs(self.player1.y - y)**2

    def setFogAlpha(self, fog, dist):
        alpha = (dist / (TILESIZE**2)) * 7
        fog.set_alpha(alpha)

    # x, y coordinates without margins
    def isWall(self, x, y):
        return self.level[x / TILESIZE][y / TILESIZE] == WALL

    def handleInput(self):
         for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_LEFT :
                        self.player1.setMovingLeft(True)
                    if event.key == K_RIGHT :
                        self.player1.setMovingRight(True)       
                    if event.key == K_UP :
                        self.player1.setMovingUp(True)                           
                    if event.key == K_DOWN :
                        self.player1.setMovingDown(True)       

                if event.type == KEYUP:
                    if event.key == K_LEFT :
                        self.player1.setMovingLeft(False)
                    if event.key == K_RIGHT :
                        self.player1.setMovingRight(False)       
                    if event.key == K_UP :
                        self.player1.setMovingUp(False)                           
                    if event.key == K_DOWN :
                        self.player1.setMovingDown(False)       

                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
    
    def updateFOV(self, tileBlocked, markVisible, markLit):
        self.fovMap = [[UNKNOWN for j in range(self.numRows)] for i in range(self.numCols)]

        xCoord = self.getCoordX(self.player1.x)
        yCoord = self.getCoordY(self.player1.y)
        
        fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, PLAYERRANGE, \
            markVisible, tileBlocked)

        for guard in self.guards:
            if self.guardFovInRange(guard):
                xCoord = self.getCoordX(guard.x)
                yCoord = self.getCoordY(guard.y)

                fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, GUARDRANGE, \
                    markLit, tileBlocked)

    def guardFovInRange(self, guard):
        return self.getDist(guard.x, guard.y) <= \
            ((PLAYERRANGE + GUARDRANGE) * TILESIZE)**2

def main():
    Game()

if __name__ == '__main__':
    main()
