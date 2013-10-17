class Player:
    def __init__(self, x, y, speed, size):
        self.x = x
        self.y = y
        self.speed = speed
        self.size  = size
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

    def nextX(self):
        retVal = self.x
        if self.movingRight:
            retVal += self.speed
        if self.movingLeft:
            retVal -= self.speed
        return retVal

    def nextY(self):
        retVal = self.y
        if self.movingDown:
            retVal += self.speed
        if self.movingUp:
            retVal -= self.speed
        return retVal

    def moveRight(self):
        self.x += self.speed

    def moveDown(self):
        self.y += self.speed

    def moveLeft(self):
        self.x -= self.speed

    def moveUp(self):
        self.y -= self.speed

    def clampLeft(self, tileSize):
        self.x -= self.x % tileSize

    def clampRight(self, tileSize):
        self.x += tileSize - self.x % tileSize - self.size - 1

    def clampUp(self, tileSize):
        self.y -= self.y % tileSize

    def clampDown(self, tileSize):
        self.y += tileSize - self.y % tileSize - self.size - 1

