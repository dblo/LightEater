#! /usr/bin/env python

import pygame, sys
from pygame.locals import *
import fov, random

FPS         = 30
PLAYERSPEED = 2
TILESIZE    = 20
PLAYERSIZE  = TILESIZE
GUARDSIZE   = TILESIZE
PLAYERRANGE = 5
GUARDRANGE  = 4
WIDTH       = 1800
HEIGHT      = 900
WALL        = 0
OPEN        = 1
UNEXPLORED  = 0
EXPLORED    = 1
LIT         = 2
INLOS       = 1

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (255, 0,   0)
GRAY    = (100, 100, 100)
GREEN   = (0,   255,   0)
BLUE    = (0,   0,   255)
FOW     = (10, 170, 10, 125)

# assert TILESIZE % PLAYERSPEED == 0, "Bad tilesize - playerspeed ratio"
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
    def __init__(self, route, speed, xMargin, yMargin):
        self.route = route
        self.speed = speed
        self.currInstr = 1

        self.x = route[0][0] * TILESIZE + xMargin
        self.y = route[0][1] * TILESIZE + yMargin
        self.goalX = route[1][0] * TILESIZE + xMargin
        self.goalY = route[1][1] * TILESIZE + yMargin

    def move(self, xMargin, yMargin):
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
            self.goalX = self.route[self.currInstr][0] * TILESIZE + xMargin
            self.goalY = self.route[self.currInstr][1] * TILESIZE + yMargin

class Game:
    def __init__(self):
        pygame.init()

        self.numRows     = 20
        self.numCols     = 80
        self.yMargin     = (HEIGHT - TILESIZE * self.numRows) / 2
        self.xMargin     = (WIDTH - TILESIZE  * self.numCols) / 2 
        self.player1     = Player(self.xMargin + TILESIZE, self.yMargin + TILESIZE)
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
        self.guards.append(Guard(((self.numCols-1,1), (self.numCols-1,18), (17,18), (17,1)), 4, \
            self.xMargin, self.yMargin))
        self.guards.append(Guard(((17,18), (17,1), (self.numCols-1,1), (self.numCols-1,18)), 4, \
            self.xMargin, self.yMargin))

        self.fovMap = []

        self.DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT))
        self.anisurf     = pygame.Surface((WIDTH, HEIGHT)).convert_alpha()            
        pygame.display.set_caption("Splinter block")
        self.run()

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
                guard.move(self.xMargin, self.yMargin)

            if fovCounter == 0:
                self.updateFOV(tileBlockes, markVisible, markLit)
                self.checkIfCaught()
                fovCounter = FPS / 2
            else:
                fovCounter -= 1
            self.render()
            fpsClock.tick(FPS)

    def checkIfCaught(self):
        if self.fovMap[(self.player1.x - self.xMargin) / TILESIZE] \
            [(self.player1.y - self.yMargin) / TILESIZE] == LIT:
            print "caught"
            
    def movePlayer(self, player):
        rect = pygame.Rect(player.x - self.xMargin, player.y - self.yMargin, \
            PLAYERSIZE-1, PLAYERSIZE-1)

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
                % TILESIZE - 1
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
                % TILESIZE - 1
            else:
                player.y += PLAYERSPEED

    def render(self):
        fog = pygame.Surface((TILESIZE, TILESIZE))
        fog.set_alpha(220)
        fog.fill(BLACK)
        self.anisurf.fill(BLACK)

        for row in range(self.numRows):
            for col in range(self.numCols):
                x = col * TILESIZE + self.xMargin
                y = row * TILESIZE + self.yMargin

                tileRect = pygame.Rect(x, y, TILESIZE, TILESIZE)
                
                if self.level[col][row] == WALL:
                    pygame.draw.rect(self.anisurf, GRAY, tileRect)
                elif self.level[col][row] == OPEN:
                    pygame.draw.rect(self.anisurf, GREEN, tileRect)

                if not self.fovMap[col][row] == LIT:
                    if self.fogMap[col][row] == EXPLORED:
                        self.anisurf.blit(fog, (x, y))
                    else:
                        tileRect = pygame.Rect(x, y, PLAYERSIZE, PLAYERSIZE)
                        pygame.draw.rect(self.anisurf, BLACK, tileRect)

        for guard in self.guards:
            # todo: Check dist to player

            x = (guard.x - self.xMargin) / TILESIZE
            y = (guard.y - self.yMargin) / TILESIZE

            if self.fovMap[x][y] == LIT:
                pygame.draw.rect(self.anisurf, RED, pygame.Rect(guard.x, guard.y,
                    PLAYERSIZE, PLAYERSIZE))

        pygame.draw.rect(self.anisurf, BLUE, pygame.Rect(self.player1.x, self.player1.y, 
            GUARDSIZE, GUARDSIZE))

        self.DISPLAYSURF.blit(self.anisurf, (0,0))
        pygame.display.update()

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
        self.fovMap = [[0 for j in range(self.numRows)] \
                    for i in range(self.numCols)]

        xCoord = (self.player1.x - self.xMargin + PLAYERSIZE / 2) / TILESIZE
        yCoord = (self.player1.y - self.yMargin + PLAYERSIZE / 2) / TILESIZE
        
        fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, PLAYERRANGE, \
            markVisible, tileBlocked)

        for guard in self.guards:
            xCoord = (guard.x - self.xMargin + PLAYERSIZE / 2) / TILESIZE
            yCoord = (guard.y - self.yMargin + PLAYERSIZE / 2) / TILESIZE

            fov.fieldOfView(xCoord, yCoord, self.numCols, self.numRows, GUARDRANGE, \
                markLit, tileBlocked)

def main():
    Game()

if __name__ == '__main__':
    main()
