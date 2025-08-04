import random

class Strategy:
    def __init__(self, configuration, trendemic):
        self.configuration = configuration
        self.trendemic = trendemic
        #local_weight=1.0, global_weight=0.0, heterogeneous_thresholds=False, threshold_distribution="uniform",
        #social_engineer_enabled=False, seeding_strategy=None, social_engineer_count=5

    # By default, randomize influencer seeding
    def seedAgents(self):
        influenced = 0
        influencers = []
        while influenced < self.trendemic.numInfluencers:
            index = random.randint(0, len(self.trendemic.agents) - 1)
            agent = self.trendemic.agents[index]
            if agent not in influencers:
                influencers.append(agent)
                agent.influenced = True
                agent.influencer = True
                influenced += 1

    def __str__(self):
        return f"{self.configuration}"

class MaxDegree(Strategy):
    def __init__(self, configuration, trendemic):
        super().__init__(configuration, trendemic)

    def seedAgents(self):
        maxDegreeAgents = []
        for agent in self.trendemic.agents:
            maxDegreeAgent = {"agent": agent, "degree": len(agent.neighbors)}
            maxDegreeAgents.append(maxDegreeAgent)
        maxDegreeAgents.sort(key=lambda agent: agent["degree"], reverse=True)
        for i in range(self.trendemic.numInfluencers):
            agent = maxDegreeAgents[i]["agent"]
            agent.influenced = True
            agent.influencer = True
