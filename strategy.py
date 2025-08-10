import random

class Strategy:
    def __init__(self, configuration, trendemic):
        self.configuration = configuration
        self.strategy = configuration["strategy"]
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
                agent.setInfluencer()
                influenced += 1

    def __str__(self):
        return f"{self.configuration}"

class MaxCommunity(Strategy):
    def __init__(self, configuration, trendemic):
        super().__init__(configuration, trendemic)

    def bronKerboschCliqueDetection(self, requiredNodes, permittedNodes, excludedNodes, graph, communities):
        if len(permittedNodes) == 0 and len(excludedNodes) == 0:
            if len(requiredNodes) > 2:
                communities.append(sorted(requiredNodes))
            return

        (degree, pivotNode) = max([(len(graph[node]), node) for node in permittedNodes.union(excludedNodes)])
        for node in permittedNodes.difference(graph[pivotNode]):
            self.bronKerboschCliqueDetection(requiredNodes.union(set([node])), permittedNodes.intersection(graph[node]), excludedNodes.intersection(graph[node]), graph, communities)
            permittedNodes.remove(node)
            excludedNodes.add(node)

    def seedAgents(self):
        # Rely on updating the communities by reference in Bron-Kerbosch clique detection
        communities = []
        graph = {}
        for agent in self.trendemic.agents:
            graph[agent.ID] = set()
            neighborhood = agent.neighbors
            if "SmallWorld" in self.strategy:
                neighborhood = agent.smallWorldNeighbors
            elif "ScaleFree" in self.strategy:
                neighborhood = agent.scaleFreeNeighbors
            for neighbor in neighborhood:
                graph[agent.ID].add(neighbor.ID)
        self.bronKerboschCliqueDetection(set(), set(graph.keys()), set(), graph, communities)
        communityDegrees = [len(community) for community in communities]
        totalCommunityDegree = sum(communityDegrees)
        communityWeights = [communityDegree / totalCommunityDegree for communityDegree in communityDegrees]
        communities = random.choices(communities, weights=communityWeights, k=self.trendemic.numInfluencers)

        seededNodes = []
        community = communities.pop()
        random.shuffle(community)
        for i in range(self.trendemic.numInfluencers):
            if len(community) == 0:
                community = communities.pop()
                community = [node for node in community if node not in seededNodes]
                random.shuffle(community)
            agentID = community.pop()
            agent = self.trendemic.agents[agentID]
            agent.setInfluencer()
            seededNodes.append(agentID)

class MaxDegree(Strategy):
    def __init__(self, configuration, trendemic):
        super().__init__(configuration, trendemic)

    def seedAgents(self):
        maxDegreeAgents = []
        for agent in self.trendemic.agents:
            neighborhood = agent.neighbors
            if "SmallWorld" in self.strategy:
                neighborhood = agent.smallWorldNeighbors
            elif "ScaleFree" in self.strategy:
                neighborhood = agent.scaleFreeNeighbors
            maxDegreeAgent = {"agent": agent, "degree": len(neighborhood)}
            maxDegreeAgents.append(maxDegreeAgent)
        maxDegreeAgents.sort(key=lambda agent: agent["degree"], reverse=True)
        for i in range(self.trendemic.numInfluencers):
            agent = maxDegreeAgents[i]["agent"]
            agent.setInfluencer()
