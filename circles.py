import pygame
from pygame import gfxdraw
from scipy.stats import distributions

class Circle(pygame.sprite.Sprite): #Batch of circles is a sprite

    def __init__(self, x, y, color):
        super(Circle, self).__init__()
        self.x=x
        self.y=y
        self.r=4
        self.color=color
        self.rect = pygame.Rect(x - self.r, y - self.r, 2 * self.r, 2 * self.r)
        self.image = pygame.Surface((2*self.r, 2*self.r), pygame.SRCALPHA)
        pygame.gfxdraw.aacircle(self.image, self.r, self.r, self.r, self.color)
        pygame.gfxdraw.filled_circle(self.image, self.r, self.r, self.r, self.color)

    def antialias(self):
        pygame.gfxdraw.aacircle(self.image, self.r, self.r, self.r, (100,100,100))

    def update(self, color):
        pygame.gfxdraw.aacircle(self.image, self.r, self.r, self.r, color)
        pygame.gfxdraw.filled_circle(self.image, self.r, self.r, self.r, color)

class Target(object): #composed of circles, but has other specs too

    def getColor(self):
        if self.pos=="up": return (220, 80, 220) #light purple
        elif self.pos=="down": return (109, 137, 229) #light blue
        elif self.pos=="left": return (255, 186, 24) #light orange
        elif self.pos=="right": return (80, 209, 80) #light green
        else: assert(False)

    def __init__(self, pos, center, circleCount, scale):
        self.pos=pos
        (self.cx, self.cy) = center
        self.circleCount=circleCount
        self.scale = scale #metric for sparseness of circle distribution
        self.circles = pygame.sprite.Group()
        self.rewardQueue = None
        self.color=self.getColor()
        self.update()
    def __repr__(self):
        return self.pos

    def getScore(self):
        thisScore = self.rewardQueue.pop(0) #dequeue
        self.rewardQueue.append(thisScore) #enqueue
        return thisScore

    def generateCircles(self):
        self.circles = pygame.sprite.Group() #reset existing circles.
        (cx, cy, scale) = (self.cx, self.cy, self.scale)
        circleCount=self.circleCount
        #gaussian normal distribution of dots:
        f=distributions.norm(scale=self.scale)
        #numpy arrays of x, y coordinates:
        x = f.rvs(circleCount)
        y = f.rvs(circleCount)
        #add coordinates to pygame Sprite group:
        for i in range(circleCount):
            (incX, incY) = (x[i], y[i])
            (thisX, thisY) = (cx+incX, cy+incY)
            thisCircle=Circle(thisX, thisY, self.color) #Circle Class
            self.circles.add(thisCircle) #add to Pygame sprite group

    def getDistance(self, x, y):
        return ((self.cx-x)**2 + (self.cy-y)**2)**0.5

    def update(self):
        self.generateCircles()
