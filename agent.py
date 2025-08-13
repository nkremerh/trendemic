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

        self.scaleFreeWeight = configuration["scaleFreeWeight"]
        self.influencer = configuration["influencer"]
        self.smallWorldWeight = configuration["smallWorldWeight"]
        self.threshold = configuration["threshold"]

        self.age = 0
        self.influenced = True if self.influencer == True else False
        self.neighbors = []
        self.nextInfluenced = False
        self.scaleFreeNeighbors = []
        self.smallWorldNeighbors = []
        self.timestepInfluenced = -1

    def doInfluence(self):
        if len(self.neighbors) == 0:
            return
        fractionInfluenced = 0
        scaleFreeFractionInfluenced = 0
        smallWorldFractionInfluenced = 0
        for neighbor in self.neighbors:
            if neighbor.influenced == True:
                fractionInfluenced += 1
                if neighbor in self.scaleFreeNeighbors:
                    scaleFreeFractionInfluenced += 1
                if neighbor in self.smallWorldNeighbors:
                    smallWorldFractionInfluenced += 1

        scaleFreeFractionInfluenced = scaleFreeFractionInfluenced / len(self.scaleFreeNeighbors) if len(self.scaleFreeNeighbors) > 0 else 0
        smallWorldFractionInfluenced = smallWorldFractionInfluenced / len(self.smallWorldNeighbors) if len(self.smallWorldNeighbors) > 0 else 0
        fractionInfluenced = 0
        if "smallWorld" in self.trendemic.networkTypes:
            fractionInfluenced += self.smallWorldWeight * smallWorldFractionInfluenced
        if "scaleFree" in self.trendemic.networkTypes:
            fractionInfluenced += self.scaleFreeWeight * scaleFreeFractionInfluenced

        # If enough neighbors are influenced, guarantee agent is influenced next timestep
        if fractionInfluenced >= self.threshold:
            self.setInfluenced()

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

    def setInfluenced(self):
        self.influenced = True
        self.timestepInfluenced = self.trendemic.timestep

    def setInfluencer(self):
        self.influenced = True
        self.influencer = True
        self.timestepInfluenced = self.trendemic.timestep

    def updateValues(self):
        # Method to be used by child classes to do interesting things with agent behavior
        return

    def __str__(self):
        return f"{self.ID}: Influencer: {self.influencer}, Neighbors: {len(self.neighbors)}"
