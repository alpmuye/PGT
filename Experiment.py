import numpy as np
import pandas as pd
from scipy.stats import distributions
import random
import copy
from PyAnimation import *
from circles import Circle
from circles import Target

"""
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
			assert(len(self.centers.keys())==len(self.targets))
			for i in range(len(self.centers.keys())):
				rewardList = self.rewardDF[self.centers.keys()[i]].tolist()
				self.targets[i].rewardQueue= rewardList
		for i in range(5): #shuffle 20 times
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
		self.cueTimer=700 #ms
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
		pygame.mouse.set_visible(False)

		#reset Boolean switches for graphics control
		self.isRecordingMouseMotion=False
		self.isBackGroundBlack=False
		self.isMouseMotionTimeSet=False

		#now actually update the targets...
		for target in self.targets:
			target.update()

	def showFeedback(self, target, score, endpoint):
		def darkenColor(color):
			(r, g, b) = color
			(r, g, b) = (r/2, g/2, b/2)
			return (r, g, b)
		def lightenColor(color):
			(r,g,b) = color
			(r, g, b) = (r + (255-r)/10, g + (255-g)/10, b + (255-b)/10)
			return (r, g, b)

		self.screen.fill(self.bgColor)
		target.circles.update(darkenColor(target.color))
		target.circles.draw(self.screen)
		pygame.draw.circle(self.screen, (255,0,0), endpoint, 2) #red
		pygame.draw.circle(self.screen, target.color, (target.cx, target.cy), 4) #red
		myfont = pygame.font.SysFont("Arial", 55)
		label = myfont.render(str(score), True, target.color)

		self.mouseMovementData.append(pd.Series(self.mouseMovements)) #save trajectory
		self.mouseMovements=list() #reset trajectory.

		(posX, posY) = (target.cx-30, target.cy-150)
		thisColor = target.color

		for i in range(10):
			label=myfont.render(str(score), True, thisColor)
			self.screen.blit(label, (posX, posY))
			pygame.display.flip()
			label.fill(self.bgColor)
			self.screen.blit(label, (posX, posY))
			posY-=1
			thisColor = lightenColor(thisColor)
			pygame.time.delay(30)

		#pygame.time.wait(1500)
		target.circles.update(target.color)

	def calculateScore(self, x, y): #target indexing CCW, beginning at left
		def calculateDistancePenalty(offset): ##############
			return offset

		#calculate closest distance
		distancesFromCenters=list()
		for target in self.targets:
			thisDistance=target.getDistance(x, y)
			distancesFromCenters.append(thisDistance)

		closestDis = min(distancesFromCenters) #distance in pixels

		targetHit = self.targets[distancesFromCenters.index(closestDis)] #index!
		rawScore = targetHit.getScore()
		score = int(round(rawScore - calculateDistancePenalty(closestDis)))

		print rawScore, calculateDistancePenalty(closestDis)

		#data to append to trials df
		(targetX, targetY) = (targetHit.cx, targetHit.cy)
		(offsetX, offsetY) = (abs(targetX-x), abs(targetY-y))

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
		if self.cueTimer<=0:
			self.cueTimer=0
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
			self.screen.fill(self.bgColor)
			pygame.display.flip()
			pygame.time.delay(random.randint(250,2500))
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
