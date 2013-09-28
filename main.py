#! /usr/bin/env python

import pygame, sys
from pygame.locals import *
import fov

FPS         = 30
NUMROWS     = 6
NUMCOLS     = 10
PLAYERSPEED = 1
PLAYERSIZE  = 10
TILESIZE    = PLAYERSIZE * 4
WIDTH       = NUMCOLS * TILESIZE + 100 + 100
HEIGHT      = NUMROWS * TILESIZE + 100 + 100
YMARGIN     = (HEIGHT - TILESIZE * NUMROWS) / 2
XMARGIN     = (WIDTH - TILESIZE * NUMCOLS) / 2 
TILEPLAYERRATIO = TILESIZE / PLAYERSIZE
WALL        = 0
UNEXPLORED  = 0
EXPLORED    = 1
LIT         = 2

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (255, 0,   0)
GRAY    = (100, 100, 100)
GREEN   = (0,   255,   0)
BLUE    = (0,   0,   255)
FOW     = (10, 170, 10, 125)

assert TILESIZE % PLAYERSPEED == 0, "Bad tilesize - playerspeed ratio"
assert TILESIZE % PLAYERSIZE == 0, "Bad tilesize - playersize ratio"

class Player:
    def __init__(self, x, y):
        self.x = x + TILESIZE / 2 - PLAYERSIZE / 2
        self.y = y + TILESIZE / 2 - PLAYERSIZE / 2
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

        offsetToCenter = TILESIZE / 2 - PLAYERSIZE / 2
        self.x = route[0][0] * TILESIZE + XMARGIN + offsetToCenter
        self.y = route[0][1] * TILESIZE + YMARGIN + offsetToCenter
        self.goalX = route[1][0] * TILESIZE + XMARGIN + offsetToCenter
        self.goalY = route[1][1] * TILESIZE + YMARGIN + offsetToCenter

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
            self.goalX = self.route[self.currInstr][0] * TILESIZE + XMARGIN \
                + TILESIZE / 2 - PLAYERSIZE / 2
            self.goalY = self.route[self.currInstr][1] * TILESIZE + YMARGIN \
                + TILESIZE / 2 - PLAYERSIZE / 2

class Game:
    def __init__(self):
        pygame.init()

        self.player1 = Player(XMARGIN + TILESIZE, YMARGIN + TILESIZE)
        self.level = [ [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 1, 0, 1, 0, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0] ]

        self.guards = []
        self.guards.append(Guard(((3,1), (3,4), (5,4), (5,1)), 1))
        self.guards.append(Guard(((5,4), (5,1), (3,1), (3,4)), 1))

        self.detLevel = [[0 for j in range(NUMROWS * TILEPLAYERRATIO)] \
                    for i in range(NUMCOLS * TILEPLAYERRATIO)]

        for row in range(NUMROWS):
            for col in range(NUMCOLS):
                if self.level[col][row] == 1:
                    for y in range(TILEPLAYERRATIO):
                        for x in range(TILEPLAYERRATIO):
                            self.detLevel[col * TILEPLAYERRATIO + x] \
                                [row * TILEPLAYERRATIO + y] = 1


        self.fovMap = [[0 for j in range(NUMROWS * TILEPLAYERRATIO)] \
                    for i in range(NUMCOLS * TILEPLAYERRATIO)]

        self.DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT))
        self.anisurf     = pygame.Surface((WIDTH, HEIGHT)).convert_alpha()            
        pygame.display.set_caption("Splinter block")
        self.run()

    def run(self):
        fpsClock = pygame.time.Clock()
        fovCounter = 0        

        def tileBlocked(x, y): 
            return self.detLevel[x][y] == WALL
        def markVisible(x, y): self.fovMap[x][y] = 1
        def markLit(x, y):
            if self.fovMap[x][y] == 1:
                self.fovMap[x][y] = 2

        while 1:
            self.handleInput()
            self.movePlayer(self.player1)
            for guard in self.guards:
                guard.move()

            if fovCounter == 0:
                self.updateFOV(tileBlocked, markVisible, markLit)
                fovCounter = FPS / 2
            else:
                fovCounter -= 1

            self.render()
            fpsClock.tick(FPS)

    def movePlayer(self, player):
        rect = pygame.Rect(player.x - XMARGIN, player.y - YMARGIN, \
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

    def render(self, ):
        self.anisurf.fill(BLACK)
        for row in range(NUMROWS):
            for col in range(NUMCOLS):
                tileRect = pygame.Rect(col * TILESIZE + XMARGIN, 
                    row * TILESIZE + YMARGIN, TILESIZE, TILESIZE)
                
                if self.level[col][row] == 0:
                    pygame.draw.rect(self.anisurf, GRAY, tileRect)
                elif self.level[col][row] == 1:
                    pygame.draw.rect(self.anisurf, GREEN, tileRect)

                for y in range(TILEPLAYERRATIO):
                    for x in range(TILEPLAYERRATIO):
                        fovMapX = col * TILEPLAYERRATIO + x
                        fovMapY = row * TILEPLAYERRATIO + y

                        if self.fovMap[fovMapX][fovMapY] < 2:
                            tileRect = pygame.Rect(fovMapX * PLAYERSIZE + XMARGIN, 
                                fovMapY * PLAYERSIZE + YMARGIN, PLAYERSIZE, PLAYERSIZE)
                            pygame.draw.rect(self.anisurf, (100, 100, 100, 100), tileRect)

                        # if self.fovMap[fovMapX][fovMapY] == 1:
                        #     # self.detLevel[fovMapX][fovMapY]== 1:
                        #     tileRect = pygame.Rect(fovMapX * PLAYERSIZE + XMARGIN, \
                        #         fovMapY * PLAYERSIZE + YMARGIN, PLAYERSIZE, PLAYERSIZE)
                        #     pygame.draw.rect(self.anisurf, FOW, tileRect)

        for guard in self.guards:
            if self.fovMap[(guard.x - XMARGIN) / PLAYERSIZE] \
                [(guard.y - YMARGIN) / PLAYERSIZE] == 2:
                pygame.draw.rect(self.anisurf, RED, pygame.Rect(guard.x, guard.y,
                    PLAYERSIZE, PLAYERSIZE))

        pygame.draw.rect(self.anisurf, BLUE, pygame.Rect(self.player1.x, self.player1.y, 
            PLAYERSIZE, PLAYERSIZE))

        self.DISPLAYSURF.fill(BLACK)
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
        self.fovMap = [[0 for j in range(NUMROWS * TILEPLAYERRATIO)] \
                    for i in range(NUMCOLS * TILEPLAYERRATIO)]

        xCoord = (self.player1.x - XMARGIN) / (TILESIZE / TILEPLAYERRATIO)
        yCoord = (self.player1.y - YMARGIN) / (TILESIZE / TILEPLAYERRATIO)
        
        fov.fieldOfView(xCoord, yCoord, \
            NUMCOLS * TILEPLAYERRATIO, NUMROWS * TILEPLAYERRATIO, TILEPLAYERRATIO*3, \
            markVisible, tileBlocked)

        # xCoord = (self.player1.x + PLAYERSIZE/2 - XMARGIN) / (TILESIZE / TILEPLAYERRATIO)
        # yCoord = (self.player1.y + PLAYERSIZE/2 - YMARGIN) / (TILESIZE / TILEPLAYERRATIO)

        # fov.fieldOfView(xCoord, yCoord, \
        #      NUMCOLS * TILEPLAYERRATIO, NUMROWS * TILEPLAYERRATIO, 1, \
        #      markLit, tileBlocked)

        # xCoord = (self.player1.x + PLAYERSIZE/2 - XMARGIN) / (TILESIZE / TILEPLAYERRATIO)
        # yCoord = (self.player1.y + PLAYERSIZE/2 - YMARGIN) / (TILESIZE / TILEPLAYERRATIO)

        # fov.fieldOfView(xCoord, yCoord, \
        #     NUMCOLS * TILEPLAYERRATIO, NUMROWS * TILEPLAYERRATIO, 1, \
        #     markLit, tileBlocked)

        for guard in self.guards:
            xCoord = (guard.x - XMARGIN) / (TILESIZE / TILEPLAYERRATIO)
            yCoord = (guard.y - YMARGIN) / (TILESIZE / TILEPLAYERRATIO)

            fov.fieldOfView(xCoord, yCoord, \
                NUMCOLS * TILEPLAYERRATIO, NUMROWS * TILEPLAYERRATIO, TILEPLAYERRATIO, \
                markLit, tileBlocked)

def main():
    Game()

if __name__ == '__main__':
    main()
