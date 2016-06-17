# rewardSchedules.py
'''
Generates a balanced reward schedule for 12 subjects and
high load (4 targets). Repeat the cycle for more subjects as factors
of 24 (== 4! == permutations of high load reward positions)
'''

import itertools
import numpy as np
import pandas as pd
import random

def generateRewardSchedules():
    dfList = list()
    rs = ["A", "B", "C", "D"] # high load
    permutations = np.array(list(itertools.permutations(rs)))
    #len(permutations) == 24 == 4!
    random.shuffle(permutations)
    shuffled = permutations.flatten()
    shuffled = np.concatenate((shuffled, shuffled), axis=0)
    for i in range(0,48,4):
        dfList.append(pd.Series(shuffled[i:i+16]))

    df = pd.DataFrame(dfList)
    fileName = "rewardSchedules.csv"
    df.to_csv(fileName)

generateRewardSchedules()
