import numpy as np
import pandas as pd
from scipy.stats import distributions
import random
import copy
from PyAnimation import *
from circles import Circle
from circles import Target
"""
def getDistance(point1, point2): #gets the distance between two points
								 #represented by tuples.
	(x0, y0)= point1
	(x1, y1)= point2
	return ((x1-x0)**2 + (y1-y0)**2)**0.5



To do:
- Score calculation algorithm
- Score feedback to user.
"""

def setSubjectData():
		subjectID = raw_input('Please enter the subject ID: ')
		print("The subject ID is %s" %subjectID)
		return subjectID

class Experiment(PygameGame):

	@staticmethod
	def checkInput(load, variance):
		assert(load=="low" or load=="high")
		assert(variance=="low" or variance=="high")

	def assignRewardSchedule(self):
		def getCol():
			if self.load=="low":
				return random.choice(self.centers.keys())
				assert(False)
			else: #self.load=="high"
				return random.choice(self.centers.keys())
		def shuffleCols():
			fst = getCol()
			snd = getCol()
			self.rewardDF[[fst, snd]] = self.rewardDF[[snd, fst]]
		def assignRewards():
			for center in self.centers.keys():
				for target in self.targets:
					target.rewardQueue=self.rewardDF[center].tolist()
		for i in range(100):
			shuffleCols()

		assignRewards()

	def setTargets(self): #targets indexed COUNTER CLOCKWISE, starting from left
		sc = 20 if self.variance=="low" else 40 #high variance
		cc=self.circleCount
		self.targets=[]

		for key in self.centers:
			self.targets.append(Target(key, self.centers[key], cc, sc))

		self.assignRewardSchedule()

	def assignCenters(self):
		(width, height) = (self.width, self.height)
		if self.load=="low":
			self.centers = {"left":(width/4, height/2),
							"right":(3*width/4, height/2)}
		else: #self.load=="high"
			self.centers={"left":(width/4, height/2),
						"right":(3*width/4, height/2),
						"up":(width/2, height/4),
						"down":(width/2, 3*height/4)}

	def init(self):
		Experiment.checkInput(self.load, self.variance)
		(width, height) = (self.width, self.height)

		self.assignCenters()

		self.rewardDF = pd.read_csv("IGTCards.csv") #################x

		self.setTargets()
		self.ignoreMousePress = True

		#Later to be translated into a pandas dataframe.
		self.subjectData = {"Id":[], "Trial":[], "Variance":[], "Load":[],
							"Time(Stim)":[], "Time(Cue)":[],
							"ResponseTime(Click)":[], "ResponseTime(Move)":[],
							"MovementClickOffset":[],
							"EndpointX":[], "EndpointY":[],
							"CenterReached":[], "ReachOffsetX":[], "ReachOffsetY":[],
							"Score":[]}

		#mouse trajectories indexed by trials is a distinct dataFrame
		self.mouseMovementData = list() #this will be list of pd.Series
										#to make up for unequal dist. with NaN.
		#reach trajectory
		self.mouseMovements = list()
		self.isRecordingMouseMotion = False

		#stimulus data
		self.trial=1

		self.cueTimer=0

		self.updateTargets()
		#Boolean switches
		self.isBackGroundBlack=False #to redraw a single time.
		self.cueTimeSet=False
		self.isMouseMotionTimeSet=False
		self.ignoreMousePress = False

	def setCueTimer(self):
		self.cueTimer=2000 #ms
		self.cueTimeSet=False

	def setResponseTime(self):
		self.trial+=1
		cueTime = (0 if len(self.subjectData["Time(Cue)"])==0
						else self.subjectData["Time(Cue)"][-1])
		RTMove = (0 if len(self.subjectData["ResponseTime(Move)"])==0
					else self.subjectData["ResponseTime(Move)"][-1])

		clickOffset=(pygame.time.get_ticks()-cueTime)
		MovementClickOffset=clickOffset-RTMove
		#append to the dictionary
		self.subjectData["ResponseTime(Click)"].append(clickOffset)
		self.subjectData["MovementClickOffset"].append(MovementClickOffset)

	def centerMouse(self):
		(cx, cy) = (self.width/2, self.height/2)
		pygame.mouse.set_pos([cx, cy])

	def updateTargets(self): #more like generateStimulus.
		self.setCueTimer()

		#set subject data
		self.subjectData["Id"].append(self.subjectID)
		self.subjectData["Trial"].append(self.trial)
		self.subjectData["Variance"].append(self.variance)
		self.subjectData["Load"].append(self.load)
		self.subjectData["Time(Stim)"].append(pygame.time.get_ticks())

		self.centerMouse()
		pygame.mouse.set_visible(False) #Don't show the mouse during stimulus.

		#reset Boolean switches for graphics control
		self.isRecordingMouseMotion=False
		self.isBackGroundBlack=False
		self.isMouseMotionTimeSet=False

		#self.mouseMovementData.append(pd.Series(self.mouseMovements)) #save trajectory
		#self.mouseMovements=list() #reset trajectory.

		#now actually update the targets...
		for target in self.targets:
			target.update()

	def showFeedback(self, target, score, endpoint):
		self.screen.fill(self.bgColor)
		target.circles.draw(self.screen)
		pygame.draw.circle(self.screen, (255,0,0), endpoint, 2) #red
		myfont = pygame.font.SysFont("Arial", 35)
		label = myfont.render("Some text!", True, (255,255,255))

		self.mouseMovementData.append(pd.Series(self.mouseMovements)) #save trajectory
		self.mouseMovements=list() #reset trajectory.

		self.screen.blit(label, endpoint)
		self.redrawAll(self.screen)

		pygame.time.wait(800)

	def calculateScore(self, x, y): #target indexing CCW, beginning at left
		distancesFromCenters=list()
		for target in self.targets:
			thisDistance=target.getDistance(x, y)
			distancesFromCenters.append(thisDistance)
		closest = min(distancesFromCenters) #distance in pixels
		assert(closest in distancesFromCenters)
		targetHit = self.targets[distancesFromCenters.index(closest)] #index!
		(targetX, targetY) = (targetHit.cx, targetHit.cy)
		(offsetX, offsetY) = (abs(targetX-x), abs(targetY-y))
		score = (50 - closest) * 2

		print score, self.trial

		#set trial data
		self.subjectData["EndpointX"].append(x)
		self.subjectData["EndpointY"].append(y)
		self.subjectData["CenterReached"].append(targetHit)
		self.subjectData["ReachOffsetX"].append(offsetX)
		self.subjectData["ReachOffsetY"].append(offsetY)
		self.subjectData["Score"].append(score)

		self.showFeedback(targetHit, score, (x, y))

	#Keyboard / Mouse Interaction

	def timerFired(self, dt):
		if dt>=500:
			print "Called with big dt"
			return #pause from previous call.
		if self.cueTimer%3==0: print self.cueTimer
		if self.cueTimer<=0:
			self.cueTimer=0
			pygame.mouse.set_visible(True)
			self.isRecordingMouseMotion=True
			if not self.isBackGroundBlack: self.redrawAll(self.screen)
		else:
			self.cueTimer-=dt

	def mouseMotion(self, x, y):
		if self.isRecordingMouseMotion:
			self.mouseMovements.append((x,y))
			if not self.isMouseMotionTimeSet:
				mouseOffset=(pygame.time.get_ticks() -
								self.subjectData["Time(Cue)"][-1])
				self.subjectData["ResponseTime(Move)"].append(mouseOffset)
				self.isMouseMotionTimeSet=True
			if len(self.mouseMovements)%5==0: #flip screen every 5 times.
				self.redrawAll(self.screen)

	def mousePressed(self, x, y):
		if self.ignoreMousePress: return
		if self.cueTimer<=0:
			self.setResponseTime()
			self.calculateScore(x, y)
			if self.trial==11:
				self.pandaify()
			#SHOW SCORE FEEDBACK SOMEWHERE HERE
			self.updateTargets()

	def keyPressed(self, keyCode, modifier): pass

	def pandaify(self):
		fileName1 = self.subjectID + "_" +"trialsDF" +  ".csv"
		fileName2 = self.subjectID + "_" + "trajDF" +  ".csv"
		df1 = pd.DataFrame(self.subjectData, columns=["Id", "Trial", "Variance", "Load",
													"Time(Stim)", "Time(Cue)", "ResponseTime(Click)",
													"ResponseTime(Move)", "MovementClickOffset",
													"EndpointX", "EndpointY", "CenterReached",
													"ReachOffsetX", "ReachOffsetY", "Score"])
		df2 = pd.DataFrame(self.mouseMovementData)
		df1.to_csv(fileName1)
		df2.to_csv(fileName2)

	def drawCrossHair(self, screen, color):
		size=7
		(cx, cy)=(self.width/2, self.height/2)
		pygame.draw.line(screen, color, (cx, cy-size), (cx, cy+size), 3) #width=3
		pygame.draw.line(screen, color, (cx-size, cy), (cx+size, cy), 3) #width=3

	def redrawAll(self, screen):
		if self.cueTimer>0:
			self.screen.fill(self.bgColor) #black
			for target in self.targets:
				target.circles.draw(screen)
			self.drawCrossHair(screen, (120,120,120))
		else: #cueTimer=0
			if not self.isBackGroundBlack:
				self.screen.fill(self.bgColor) #black
				self.drawCrossHair(screen, (255,255,255)) #white
				self.centerMouse()
				self.isBackGroundBlack=True
			if not self.cueTimeSet:
				self.subjectData["Time(Cue)"].append(pygame.time.get_ticks())
				self.cueTimeSet=True
		if not len(self.mouseMovements)==0: #draw trajectory
			pygame.draw.lines(self.screen, (120,120,120), False,
											self.mouseMovements, 4) #width=4
		pygame.display.flip()

subjectID=setSubjectData()
Experiment(subjectID, load="high", variance="high").run()
