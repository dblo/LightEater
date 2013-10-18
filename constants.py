# General
FPS             = 30
TILESIZE        = 20
TILESIZESQ      = TILESIZE**2
BASE_ALPHA      = 105
MAX_ALPHA       = 255
AGENT_MAX_ALPHA = 220
LIGHTBAR_ELEMS  = 6
MAXTIME         = 10000
DEATH_PENALTY   = 5
FOG_ALPHA       = 150
FOV_UPDATE_RATE = FPS / 8
ALPHA_FACTOR    = 16
# Entities
PLAYERSPEED     = 2
PLAYERSIZE      = 10
HALFPLAYERSIZE  = PLAYERSIZE / 2
GUARDSIZE       = TILESIZE
HALF_GUARD_SIZE = GUARDSIZE / 2
PLAYER_RANGE    = 4
# Level
WALL            = 0
OPEN            = 1
HOLE            = 2
SAFE            = 3
#lightMap
UNEXPLORED      = False
EXPLORED        = True
UNLIT           = False
LIT             = True
# Game mode
MENU            = 0
PLAY            = 1
LEVEL           = 2
CREDITS         = 3
QUIT            = 4
# Colors
BLACK        = (0,   0,   0)
WHITE        = (255, 255, 255)
RED          = (175, 0,   0)
GRAY         = (100, 100, 100)
GREEN        = (0,   255,   0)
BLUE         = (0,   0,   255)
PURPLE       = (128, 0,   128)
YELLOW       = (255, 255, 0)
ORANGE       = (255, 120, 0)
NOCOLOR      = (255, 255, 255, 0)
BGCOLORS     = [WHITE, (0,102,102)]
SAFECOLOR    = (0, 122, 122)
FOG_COLOR    = BLACK#(50,50,50)
assert PLAYERSIZE % 2 == 0, "Playersize not even"
