#! /usr/bin/env python

import pygame, sys
from pygame.locals import *

pygame.init()

WIDTH       = 1000 #1920
HEIGHT      = 600 #1080
FPS         = 30
NUMROWS     = 3
NUMCOLS     = 4
TOPAREA     = (WIDTH * 19) / 20 + ((HEIGHT - (WIDTH * 19) / 20)) % NUMROWS
SECTORSIZE  = (HEIGHT - TOPAREA) / NUMROWS
XMARGIN     = (WIDTH - SECTORSIZE*NUMCOLS) / 2

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (255, 0,   0)
GREEN   = (0,   255, 0)
BLUE    = (0,   0,   255)

DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT))

def init():
    pass

def main():
    anisurf = pygame.Surface((WIDTH, HEIGHT)).convert_alpha()
    fpsClock = pygame.time.Clock()

    alphas = []
    rects = []
    while 1:
        DISPLAYSURF.fill(WHITE)
        anisurf.fill(WHITE)

        for event in pygame.event.get():
            if event.type == MOUSEBUTTONUP:
                mousex, mousey = event.pos
                rects.append(pygame.Rect(mousex, mousey, 30, 54))
                alphas.append(255)
            elif event.type == QUIT:
                pygame.quit()
                sys.exit()

        i = len(rects)-1
        for r in range(len(rects)-1, -1, -1):
            pygame.draw.rect(anisurf, (255,0,0, alphas[i]), rects[r])
            if alphas[i] == 1:
                del rects[i]
                del alphas[i]
            else:
                alphas[i] = alphas[i]-1
                i = i-1

        DISPLAYSURF.blit(anisurf, (0,0))
        pygame.display.update()
        fpsClock.tick()

if __name__ == '__main__':
    main()
