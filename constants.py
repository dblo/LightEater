# General
FPS             = 30
PLAYERSPEED     = 2
TILESIZE        = 20
TILESIZESQ      = TILESIZE**2
WIDTH           = 1600
HEIGHT          = 800
CRYSTAL_ALPHA   = 105
LIGHTBAR_ELEMS  = 6
# Entities
PLAYERSIZE      = 16
HALFPLAYERSIZE  = PLAYERSIZE / 2
GUARDSIZE       = TILESIZE
PLAYER_RANGE    = 5
GUARD_RANGE     = 1
# Level
WALL            = 0
OPEN            = 1
#lightMap
UNEXPLORED      = False
EXPLORED        = True
UNLIT           = False
LIT             = True
# Game mode
MENU            = 0
PLAY            = 1
QUIT            = 3
CREDITS         = 2
FOG_ALPHA       = 150
FOV_UPDATE_RATE = FPS / 4
# Colors
BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (255, 0,   0)
GRAY    = (100, 100, 100)
GREEN   = (0,   255,   0)
BLUE    = (0,   0,   255)
PURPLE  = (128, 0,   128)
YELLOW  = (255, 255, 0)
ORANGE  = (255, 102, 0)
FOW     = (10,  170, 10, 125)
NOCOLOR = (255, 255, 255, 0)

assert PLAYERSIZE % 2 == 0, "Playersize not even"
