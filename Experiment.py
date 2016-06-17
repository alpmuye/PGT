from Blocks import *

def setSubjectData():
		subjectID = raw_input('Please enter the subject ID: ')
		print("The subject ID is %s" %subjectID)
		return subjectID

class Experiment(object):
    def __init__(self):
        subjectID = setSubjectData()
        block1 = Block(subjectID, load="high", variance="high", block=1)
        block1.run()
        block2 = Block(subjectID, load="low", variance="high", block=2)
        block2.run()

        block3 = Block(subjectID, load="high", variance="low", block=3)
        block3.run()
        block4 = Block(subjectID, load="high", variance="low", block=4)
        block4.run()

        #df1 is trial data, df2 is the mouse trajectory for each block

#start Experiment
Experiment()
