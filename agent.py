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

        self.behaviorModel = configuration["behaviorModel"]
        self.globalWeight = configuration["globalWeight"]
        self.influencer = configuration["influencer"]
        self.localWeight = configuration["localWeight"]
        self.threshold = configuration["threshold"]

        self.influenced = False
        self.nextInfluenced = False
        self.age = 0
        self.neighbors = []
        self.globalNeighbors = []
        self.localNeighbors = []

    def doInfluence(self):
        if len(self.neighbors) == 0:
            return
        # TODO: Replace starter influencer meme propagation
        if self.influencer:
            neighbor = self.neighbors[random.randint(0, len(self.neighbors) - 1)]
            if neighbor.influenced == False:
                neighbor.influenced = True
        fractionInfluenced = 0
        globalFractionInfluenced = 0
        localFractionInfluenced = 0
        for neighbor in self.neighbors:
            if neighbor.influenced == True:
                fractionInfluenced += 1
                if neighbor in self.globalNeighbors:
                    globalFractionInfluenced += 1
                if neighbor in self.localNeighbors:
                    localFractionInfluenced += 1

        fractionInfluenced = fractionInfluenced / len(self.neighbors)
        globalFractionInfluenced = globalFractionInfluenced / len(self.globalNeighbors) if len(self.globalNeighbors) > 0 else 0
        localFractionInfluenced = localFractionInfluenced / len(self.localNeighbors) if len(self.localNeighbors) > 0 else 0
        influenceThreshold = fractionInfluenced
        if self.trendemic.networkType == "hybrid":
            influencedThreshold = (self.globalWeight * globalFractionInfluenced) + (self.localWeight * localFractionInfluenced)

        # If enough neighbors are influenced, guarantee agent is influenced next timestep
        if fractionInfluenced >= self.threshold:
            self.influenced = True

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
        return f"{self.ID}: Behavior: {self.behaviorModel}, Influencer: {self.influencer}, Neighbors: {self.neighbors}"
