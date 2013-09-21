#! /usr/bin/env python

import pygame, sys
from pygame.locals import *

pygame.init()

FPS         = 30
NUMROWS     = 4
NUMCOLS     = 8
TILESIZE    = 30
WIDTH       = NUMCOLS * TILESIZE + 100
HEIGHT      = NUMROWS * TILESIZE + 100
YMARGIN     = (HEIGHT - TILESIZE * NUMROWS) / 2
XMARGIN     = (WIDTH - TILESIZE * NUMCOLS) / 2 

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

    level = []
    for cols in range(NUMCOLS):
        level.append([])
        for rows in range(NUMROWS):
            level[cols].append(0)

    pygame.display.set_caption("Splinter block")

    while 1:
        DISPLAYSURF.fill(BLACK)
        anisurf.fill(BLACK)

        for event in pygame.event.get():
            # if event.type == KEYUP:
            #     if event.key == K_LEFT:

            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        for row in range(NUMROWS):
            for col in range(NUMCOLS):
                tileRect = pygame.Rect(col * TILESIZE + XMARGIN, row * TILESIZE + YMARGIN,
                    TILESIZE, TILESIZE)
                if level[col][row] == 0:
                    pygame.draw.rect(anisurf, GRAY, tileRect)
                else:
                    pygame.draw.rect(anisurf, GREEN, tileRect)

        DISPLAYSURF.blit(anisurf, (0,0))
        pygame.display.update()
        fpsClock.tick()

if __name__ == '__main__':
    main()
