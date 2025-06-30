import hashlib
import math
import random
import re
import sys

class Agent:
    def __init__(self, agentID, birthday, configuration, trendemic):
        self.ID = agentID
        self.born = birthday
        self.debug = trendemic.debug
        self.trendemic = trendemic

        self.testAttribute = configuration["testAttribute"]
        self.influencer = False#configuration["influencer"]

        self.age = 0
        self.neighbors = []

    def doInfluence(self):
        return True

    def doTimestep(self, timestep):
        self.timestep = timestep
        self.doInfluence()
        #self.updateNeighbors()
        self.updateValues()

    def isInGroup(self, group, notInGroup=False):
        membership = False
        if group == "influencer":
            membership = self.influencer

        if notInGroup == True:
            membership = not membership
        return membership

    def updateValues(self):
        # Method to be used by child classes to do interesting things with agent behavior
        return

    def __str__(self):
        return f"{self.ID}"
