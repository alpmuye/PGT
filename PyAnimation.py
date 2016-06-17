'''
pygamegame.py
created by Lukas Peraza, Carnegie Mellon University
 for 15-112 F15 Pygame Optional Lecture, 11/11/15

Adapted by Alp Muyesser in 05/16, Carnegie Mellon University,
 for the Cognitive Axon Laboratory
'''
import pygame

class PygameGame(object):

    def init(self): pass

    def mousePressed(self, x, y): pass

    def mouseReleased(self, x, y): pass

    def mouseMotion(self, x, y): pass

    def mouseDrag(self, x, y): pass

    def keyPressed(self, keyCode, modifier): pass

    def keyReleased(self, keyCode, modifier): pass

    def timerFired(self, dt): pass

    def redrawAll(self, screen): pass

    def isKeyPressed(self, key):
        ''' return whether a specific key is being held '''
        return self._keys.get(key, False)

    def __init__(self, subjectID, load="low", variance="low",
                block=1, circleCount=70,
                width=900, height=700, fps=200, title="CoAx Experiment"):
        self.width = width
        self.height = height
        self.fps = fps
        self.title = title
        self.bgColor = (0, 0, 0)
        self.isBlockOver = False #for control over event flow in Blocks.py

        #experiment data
        self.load=load
        self.variance=variance
        self.circleCount=circleCount
        self.subjectID=subjectID
        self.block = block

        print "Initializing block" + str(block)
        pygame.init()

    def run(self):
        clock = pygame.time.Clock()
        screen = pygame.display.set_mode((self.width, self.height))
        self.screen=screen
        # set the title of the window
        pygame.display.set_caption(self.title)

        # stores all the keys currently being held down
        self._keys = dict()

        # call game-specific initialization
        self.init()
        playing = True
        screen.fill(self.bgColor)
        self.redrawAll(screen)

        while playing:
            time = clock.tick(self.fps)
            #print(clock.get_time())
            self.timerFired(time)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.mousePressed(*(event.pos))
                    screen.fill(self.bgColor)
                    self.redrawAll(screen)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.mouseReleased(*(event.pos))
                elif (event.type == pygame.MOUSEMOTION and
                      event.buttons == (0, 0, 0)):
                    self.mouseMotion(*(event.pos))
                elif (event.type == pygame.MOUSEMOTION and
                      event.buttons[0] == 1):
                    self.mouseDrag(*(event.pos))
                elif event.type == pygame.KEYDOWN:
                    self._keys[event.key] = True
                    self.keyPressed(event.key, event.mod)
                elif event.type == pygame.KEYUP:
                    self._keys[event.key] = False
                    self.keyReleased(event.key, event.mod)
                elif event.type == pygame.QUIT:
                    playing = False
            if self.isBlockOver:
                playing = False
        pygame.quit()


def main():
    game = PygameGame()
    game.run()

if __name__ == '__main__':
    main()
