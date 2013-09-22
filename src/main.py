#! /usr/bin/env python

import pygame, sys
from pygame.locals import *

pygame.init()

FPS         = 30
NUMROWS     = 6
NUMCOLS     = 10
TILESIZE    = 30
WIDTH       = NUMCOLS * TILESIZE + 100
HEIGHT      = NUMROWS * TILESIZE + 100
YMARGIN     = (HEIGHT - TILESIZE * NUMROWS) / 2
XMARGIN     = (WIDTH - TILESIZE * NUMCOLS) / 2 
PLAYERSPEED = TILESIZE / 6

assert TILESIZE % PLAYERSPEED == 0, "Bad tilesize - playerspeed ratio"
# assert YMARGIN + SECTORSIZE*NUMROWS == HEIGHT, "Height inconsistency"
# assert XMARGIN*2 + SECTORSIZE*NUMCOLS == WIDTH, "Width inconsistency"

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (255, 0,   0)
GRAY    = (100, 100, 100)
GREEN   = (0,   255,   0)
BLUE    = (0,   0,   255)

def main():
    DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT))
    anisurf = pygame.Surface((WIDTH, HEIGHT)).convert_alpha()
    fpsClock = pygame.time.Clock()

    level = [ [0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 0],
    [0, 1, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 0],
    [0, 1, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0] ]

    player1 = pygame.Rect(XMARGIN + TILESIZE, YMARGIN + TILESIZE, 5, 5)

    pygame.display.set_caption("Splinter block")

    while 1:
        DISPLAYSURF.fill(BLACK)
        anisurf.fill(BLACK)

        for event in pygame.event.get():
            if event.type == KEYUP:
                if event.key == K_LEFT :
                    player1.left -= PLAYERSPEED
                if event.key == K_RIGHT :
                    player1.left += PLAYERSPEED
                if event.key == K_UP :
                    player1.top -= PLAYERSPEED
                if event.key == K_DOWN :
                    player1.top += PLAYERSPEED

            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        for row in range(NUMROWS):
            for col in range(NUMCOLS):
                tileRect = pygame.Rect(col * TILESIZE + XMARGIN, row * TILESIZE + YMARGIN,
                    TILESIZE, TILESIZE)
                if level[col][row] == 0:
                    pygame.draw.rect(anisurf, GRAY, tileRect)
                elif level[col][row] == 1:
                    pygame.draw.rect(anisurf, GREEN, tileRect)
                

        pygame.draw.rect(anisurf, BLUE, player1)

        DISPLAYSURF.blit(anisurf, (0,0))
        pygame.display.update()
        fpsClock.tick()

def validPos(x, y, level):
    pass

if __name__ == '__main__':
    main()
