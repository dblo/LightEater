FPS             = 30
PLAYERSPEED     = 2
TILESIZE        = 20
TILESIZESQ      = TILESIZE**2
PLAYERSIZE      = TILESIZE
HALFPLAYERSIZE  = PLAYERSIZE / 2
GUARDSIZE       = TILESIZE
PLAYER_RANGE    = 6
GUARD_RANGE     = 3
WIDTH           = 1600
HEIGHT          = 800
WALL            = 0
OPEN            = 1
UNEXPLORED      = 0
EXPLORED        = 1
LIT             = 2
INLOS           = 1
UNKNOWN         = 0
MENU            = 0
PLAY            = 1
QUIT            = 3
CREDITS         = 2
FOG_ALPHA       = 200
FOV_UPDATE_RATE = FPS / 2

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (255, 0,   0)
GRAY    = (100, 100, 100)
GREEN   = (0,   255,   0)
BLUE    = (0,   0,   255)
FOW     = (10,  170, 10, 125)
NOCOLOR = (255, 0,  255, 0)

assert PLAYERSIZE % 2 == 0, "Playersize not even"
