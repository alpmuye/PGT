import numpy as np
import pandas as pd
from scipy.stats import distributions
import random
import copy
from PyAnimation import *
from circles import Circle
from circles import Target


class Block(PygameGame):

	@staticmethod
	def checkInput(load, variance):
		assert(load=="low" or load=="high")
		assert(variance=="low" or variance=="high")

	def setRewardSchedule(self):
		if self.load=="high": self.rewardDF = pd.read_csv("rewards/high_load.csv")
		else: self.rewardDF = pd.read_csv("rewards/low_load.csv")

	def assignRewardSchedule(self):
		def getCol():
			return random.choice(self.rewards)
		def shuffleCols():
			fst = getCol()
			snd = getCol()
			self.rewardDF[[fst, snd]] = self.rewardDF[[snd, fst]]
		def assignRewards():
			assert(len(self.rewards))==len(self.targets)
			for i in range(len(self.centers.keys())):
				rewardList = self.rewardDF[self.rewards[i]].tolist()
				self.targets[i].rewardQueue= rewardList
		for i in range(15): #shuffle 20 times
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
			self.rewards = ["A", "B"]
		else: #self.load=="high"
			self.centers={"left":(width/4, height/2),
						"right":(3*width/4, height/2),
						"up":(width/2, height/4),
						"down":(width/2, 3*height/4)}
			self.rewards = ["A", "B", "C", "D"]

	def init(self):
		pygame.mouse.set_visible(False)
		Block.checkInput(self.load, self.variance)
		(width, height) = (self.width, self.height)

		self.assignCenters()

		self.setRewardSchedule()
		#self.rewardSchedule = pd.read_csv("rewardSchedules.csv")

		self.setTargets()
		self.ignoreMousePress = True

		#Later to be translated into a pandas dataframe.
		self.subjectData = {"idx":[], "block":[],
							"trial":[], "variance":[], "load":[],
							"time_stim":[], "time_cue":[],
							"rt_choice":[], "rt":[],
							"reach_time":[],
							"end_x":[], "end_y":[],
							"target_loc":[], "offset_x":[], "ReachOffsetY":[],
							"score":[]}

		#mouse trajectories indexed by trials is a distinct dataFrame

		self.mouseMovementData = list() #translated into pd.Series

		self.mouseMovements = list() #list of pd.Series
		self.isRecordingMouseMotion = False

		#stimulus data
		self.trial=1
		self.cueTimer=0
		self.score = 0

		#wait for event to start the experiment
		event = pygame.event.wait()
		event = pygame.event.wait()

		#generate first set of targets
		self.updateTargets()

		#Boolean switches
		self.isBackGroundBlack=False #to redraw a single time.
		self.cueTimeSet=False
		self.isMouseMotionTimeSet=False
		self.ignoreMousePress = False

	def setResponseTime(self):
		self.trial+=1
		cueTime = (0 if len(self.subjectData["time_cue"])==0
						else self.subjectData["time_cue"][-1])
		RTMove = (0 if len(self.subjectData["rt"])==0
					else self.subjectData["rt"][-1])

		clickOffset=(pygame.time.get_ticks()-cueTime)
		reach_time=clickOffset-RTMove
		#append to the dictionary
		self.subjectData["rt_choice"].append(clickOffset)
		self.subjectData["reach_time"].append(reach_time)

	def centerMouse(self):
		(cx, cy) = (self.width/2, self.height/2)
		pygame.mouse.set_pos([cx, cy])

	def setCueTimer(self):
		self.cueTimer=1000 #ms
		self.cueTimeSet=False
		return pygame.time.get_ticks()

	def updateTargets(self): #more like generateStimulus.
		#set subject data
		self.subjectData["idx"].append(self.subjectID)
		self.subjectData["block"].append(self.block)
		self.subjectData["trial"].append(self.trial)
		self.subjectData["variance"].append(self.variance)
		self.subjectData["load"].append(self.load)

		self.centerMouse()
		pygame.mouse.set_visible(False)

		#reset Boolean switches for graphics control
		self.isRecordingMouseMotion=False
		self.isBackGroundBlack=False
		self.isMouseMotionTimeSet=False

		#now actually update the targets...
		for target in self.targets:
			target.update()
		time = self.setCueTimer()
		self.subjectData["time_stim"].append(time)

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
		self.displayScore(self.screen)
		pygame.display.flip()

		#save trajectory as pd.Series
		self.mouseMovementData.append(pd.Series(self.mouseMovements))
		self.mouseMovements=list() #reset trajectory.

		(posX, posY) = (target.cx-30, target.cy-150)
		thisColor = target.color

		for i in range(20):
			label=myfont.render(str(score), True, thisColor)
			self.screen.blit(label, (posX, posY))
			pygame.display.flip()
			label.fill(self.bgColor)
			self.screen.blit(label, (posX, posY))
			posY-=1
			thisColor = lightenColor(thisColor)
			pygame.time.delay(18)

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

		targetHit = self.targets[distancesFromCenters.index(closestDis)]
		rawScore = targetHit.getScore()
		score = int(round(rawScore - calculateDistancePenalty(closestDis)))
		self.score+=score

		#data to append to trials df
		(targetX, targetY) = (targetHit.cx, targetHit.cy)
		(offsetX, offsetY) = (abs(targetX-x), abs(targetY-y))

		#set trial data
		self.subjectData["end_x"].append(x)
		self.subjectData["end_y"].append(y)
		self.subjectData["target_loc"].append(targetHit)
		self.subjectData["offset_x"].append(offsetX)
		self.subjectData["ReachOffsetY"].append(offsetY)
		self.subjectData["score"].append(score)

		#self.redrawAll(self.screen)
		self.showFeedback(targetHit, score, (x, y))

	#Keyboard / Mouse Interaction

	def timerFired(self, dt):
		if dt>=500:
			return #pause from previous call.
		if self.cueTimer<=0:
			self.cueTimer=0
			self.isRecordingMouseMotion=True
			if not self.isBackGroundBlack:
				self.redrawAll(self.screen)
			if not self.cueTimeSet:
				self.subjectData["time_cue"].append(pygame.time.get_ticks())
				self.cueTimeSet=True
		else:
			self.centerMouse()
			self.cueTimer-=dt

	def mouseMotion(self, x, y):
		if self.isRecordingMouseMotion:
			self.mouseMovements.append((x,y))
			if not self.isMouseMotionTimeSet:
				mouseOffset=(pygame.time.get_ticks() -
								self.subjectData["time_cue"][-1])
				self.subjectData["rt"].append(mouseOffset)
				self.isMouseMotionTimeSet=True
			if len(self.mouseMovements)%5==0: #flip screen every 5 times.
				self.redrawAll(self.screen)

	def mousePressed(self, x, y):
		if self.ignoreMousePress: return
		if self.cueTimer<=0:
			if not self.isMouseMotionTimeSet: #subject pressed click without moving.
				mouseOffset=(pygame.time.get_ticks() -
								self.subjectData["time_cue"][-1])
				self.subjectData["rt"].append(mouseOffset) #so rt becomes the click.
				self.isMouseMotionTimeSet=True
			self.setResponseTime()
			self.calculateScore(x, y)
			if self.trial==3:
					self.pandaify()
					self.isBlockOver = True
					return
			self.screen.fill(self.bgColor)
			self.displayScore(self.screen)
			pygame.display.flip()
			pygame.time.delay(1000)
			self.updateTargets()

	def keyPressed(self, keyCode, modifier): pass

	#make panda dfs out of block data
	def pandaify(self):
		df1 = pd.DataFrame(self.subjectData, columns=["idx", "block", "trial", "variance", "load",
													"time_stim", "time_cue", "rt_choice",
													"rt", "reach_time",
													"end_x", "end_y", "target_loc",
													"offset_x", "ReachOffsetY", "score"])
		df2 = pd.DataFrame(self.mouseMovementData)
		self.df1 = df1 #trials
		self.df2 = df2 #trajectories

	#Drawing Functions

	def displayScore(self, screen):
		score = self.score
		myfont = pygame.font.SysFont("Arial", 55)
		label = myfont.render(str(score), True, (255,255,255)) #white
		self.screen.blit(label, (50, 50))
		pygame.display.flip()

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
			self.displayScore(self.screen)
		else: #cueTimer=0
			if not self.isBackGroundBlack:
				self.screen.fill(self.bgColor) #black
				self.drawCrossHair(screen, (255,255,255)) #white
				self.centerMouse()
				self.isBackGroundBlack=True
		if not len(self.mouseMovements)==0: #draw trajectory
			pygame.draw.lines(self.screen, (120,120,120), False,
											self.mouseMovements, 4) #width=4
		pygame.display.flip()
