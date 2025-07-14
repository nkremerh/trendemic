#! /usr/bin/python

import agent
import behavior

import getopt
import hashlib
import json
import math
import random
import re
import sys

class Trendemic:
    def __init__(self, configuration):
        self.agentConfigHashes = None
        self.configuration = configuration
        self.maxTimestep = configuration["timesteps"]
        self.timestep = 0
        self.nextAgentID = 0
        self.seed = configuration["seed"]
        self.debug = configuration["debugMode"]
        self.keepAlive = configuration["keepAlivePostExtinction"]
        self.networkType = configuration["networkType"]

        self.agentEndowmentIndex = 0
        self.agentEndowments = []
        self.agents = []
        self.end = False # Simulation end flag
        self.log = None
        self.logFormat = configuration["logfileFormat"]
        self.run = False # Simulation start flag
        self.runtimeStats = {}

        self.configureAgents(configuration["numAgents"])
        self.configureInfluencers()
        self.configureLog()
        self.gui = gui.GUI(self, self.configuration["interfaceHeight"], self.configuration["interfaceWidth"]) if configuration["headlessMode"] == False else None

    def configureAgents(self, numAgents, editCell=None):
        # Ensure agent endowments are randomized across initial agent count to make replacements follow same distributions
        if len(self.agentEndowments) == 0:
            self.agentEndowments = self.randomizeAgentEndowments(numAgents)

        for i in range(numAgents):
            agentConfiguration = self.agentEndowments[self.agentEndowmentIndex % len(self.agentEndowments)]
            self.agentEndowmentIndex += 1
            agentID = self.generateAgentID()
            a = agent.Agent(agentID, self.timestep, agentConfiguration, self)
            self.agents.append(a)

        numNeighbors = random.randint(1, 3)
        for a in self.agents:
            for i in range(numNeighbors):
                neighborID = random.randint(0, len(self.agents) - 1)
                neighbor = self.agents[neighborID]
                if neighbor == self or neighbor in a.neighbors:
                    continue
                else:
                    a.neighbors.append(neighbor)
                    if a not in neighbor.neighbors:
                        neighbor.neighbors.append(a)
            a.localNeighbors = a.neighbors

    def configureLog(self):
        self.runtimeStats = {"timestep": 0, "population": len(self.agents)}
        self.log = open(self.configuration["logfile"], 'a') if self.configuration["logfile"] != None else None
        self.experimentalGroup = self.configuration["experimentalGroup"]
        if self.experimentalGroup != None:
            # Convert keys to Pythonic case scheme and initialize values
            groupRuntimeStats = {}
            for key in self.runtimeStats.keys():
                controlGroupKey = "control" + key[0].upper() + key[1:]
                experimentalGroupKey = self.experimentalGroup + key[0].upper() + key[1:]
                groupRuntimeStats[controlGroupKey] = 0
                groupRuntimeStats[experimentalGroupKey] = 0
            self.runtimeStats.update(groupRuntimeStats)

    def configureInfluencers(self):
        return

    def doTimestep(self):
        if self.timestep >= self.maxTimestep:
            self.toggleEnd()
            return
        if "all" in self.debug or "trendemic" in self.debug:
            print(f"Timestep: {self.timestep}\nLiving Agents: {len(self.agents)}")
        self.timestep += 1
        if self.end == True or (len(self.agents) == 0 and self.keepAlive == False):
            self.toggleEnd()
        else:
            turnOrder = self.agents.copy()
            random.shuffle(turnOrder)
            for agent in turnOrder:
                agent.doTimestep(self.timestep)
            self.updateRuntimeStats()
            if self.gui != None:
                self.gui.doTimestep()
            # If final timestep, do not write to log to cleanly close JSON array log structure
            if self.timestep != self.maxTimestep and len(self.agents) > 0:
                self.writeToLog()

    def endLog(self):
        if self.log == None:
            return
        # Update total wealth accumulation to include still living agents at simulation end
        logString = '\t' + json.dumps(self.runtimeStats) + "\n]"
        if self.logFormat == "csv":
            logString = ""
            # Ensure consistent ordering for CSV format
            for stat in sorted(self.runtimeStats):
                if logString == "":
                    logString += f"{self.runtimeStats[stat]}"
                else:
                    logString += f",{self.runtimeStats[stat]}"
            logString += "\n"
        self.log.write(logString)
        self.log.flush()
        self.log.close()

    def endSimulation(self):
        self.endLog()
        if "all" in self.debug or "trendemic" in self.debug:
            for agent in self.agents:
                print(agent)
            print(str(self))
        exit(0)

    def generateAgentID(self):
        agentID = self.nextAgentID
        self.nextAgentID += 1
        return agentID

    def pauseSimulation(self):
        while self.run == False:
            if self.gui != None and self.end == False:
                self.gui.window.update()
            if self.end == True:
                self.endSimulation()

    def randomizeAgentEndowments(self, numAgents):
        configs = self.configuration
        globalWeight = configs["agentGlobalWeight"]
        localWeight = configs["agentLocalWeight"]
        threshold = configs["agentThreshold"]
        configurations = {"globalWeight": {"endowments": [], "curr": globalWeight[0], "min": globalWeight[0], "max": globalWeight[1]},
                          "localWeight": {"endowments": [], "curr": localWeight[0], "min": localWeight[0], "max": localWeight[1]},
                          "threshold": {"endowments": [], "curr": threshold[0], "min": threshold[0], "max": threshold[1]}
                          }

        if self.agentConfigHashes == None:
            self.agentConfigHashes = {}
            # Map configuration to a random number via hash to make random number generation independent of iteration order
            for config in configurations.keys():
                hashed = hashlib.md5(config.encode())
                hashNum = int(hashed.hexdigest(), 16)
                self.agentConfigHashes[config] = hashNum

        for config in configurations:
            configMin = configurations[config]["min"]
            configMax = configurations[config]["max"]
            configMinDecimals = str(configMin).split('.')
            configMaxDecimals = str(configMax).split('.')
            decimalRange = []
            if len(configMinDecimals) == 2:
                configMinDecimals = len(configMinDecimals[1])
                decimalRange.append(configMinDecimals)
            if len(configMaxDecimals) == 2:
                configMaxDecimals = len(configMaxDecimals[1])
                decimalRange.append(configMaxDecimals)
            # If no fractional component to configuration item, assume increment of 1
            decimals = max(decimalRange) if len(decimalRange) > 0 else 0
            increment = 10 ** (-1 * decimals)
            configurations[config]["inc"] = increment
            configurations[config]["decimals"] = decimals

        numInfluencers = configs["numInfluencers"]
        influencers = []
        for i in range(numAgents):
            for config in configurations.values():
                config["endowments"].append(config["curr"])
                config["curr"] += config["inc"]
                config["curr"] = round(config["curr"], config["decimals"])
                if config["curr"] > config["max"]:
                    config["curr"] = config["min"]
            if numInfluencers > 0:
                influencers.append(True)
                numInfluencers -= 1
            else:
                influencers.append(False)

        endowments = []
        # Keep state of random numbers to allow extending agent endowments without altering original random object state
        randomNumberReset = random.getstate()
        for config in configurations:
            random.seed(self.agentConfigHashes[config] + self.timestep)
            random.shuffle(configurations[config]["endowments"])
        random.setstate(randomNumberReset)
        random.shuffle(influencers)

        for i in range(numAgents):
            agentEndowment = {"seed": self.seed, "influencer": influencers.pop()
                              }
            for config in configurations:
                agentEndowment[config] = configurations[config]["endowments"].pop()
            endowments.append(agentEndowment)
        return endowments

    def runSimulation(self, timesteps=5):
        self.startLog()
        if self.log == None:
            self.updateRuntimeStats()
        if self.gui != None:
            # Simulation begins paused until start button in GUI pressed
            self.gui.updateLabels()
            self.pauseSimulation()
        t = 1
        timesteps = timesteps - self.timestep
        screenshots = 0
        while t <= timesteps:
            if len(self.agents) == 0 and self.keepAlive == False:
                break
            if self.configuration["screenshots"] == True and self.configuration["headlessMode"] == False:
                self.gui.canvas.postscript(file=f"screenshot{screenshots}.ps", colormode="color")
                screenshots += 1
            self.doTimestep()
            t += 1
            if self.gui != None and self.run == False:
                self.pauseSimulation()
        self.endSimulation()

    def startLog(self):
        if self.log == None:
            return
        if self.logFormat == "csv":
            header = ""
            # Ensure consistent ordering for CSV format
            for stat in sorted(self.runtimeStats):
                if header == "":
                    header += f"{stat}"
                else:
                    header += f",{stat}"
            header += "\n"
            self.log.write(header)
        else:
            self.log.write("[\n")
        self.updateRuntimeStats()
        self.writeToLog()

    def toggleEnd(self):
        self.end = True

    def toggleRun(self):
        self.run = not self.run

    def updateRuntimeStats(self):
        # Log separate stats for experimental and control groups
        if self.experimentalGroup != None:
            self.updateRuntimeStatsPerGroup(self.experimentalGroup)
            self.updateRuntimeStatsPerGroup(self.experimentalGroup, True)
        self.updateRuntimeStatsPerGroup()

    def updateRuntimeStatsPerGroup(self, group=None, notInGroup=False):
        numAgents = 0
        for agent in self.agents:
            if group != None and agent.isInGroup(group, notInGroup) == False:
                continue
            numAgents += 1

        runtimeStats = {"population": numAgents
                        }

        if group == None:
            self.runtimeStats["timestep"] = self.timestep
        else:
            # Convert keys to Pythonic case scheme
            groupString = group if notInGroup == False else "control"
            groupStats = {}
            for key in runtimeStats.keys():
                groupKey = groupString + key[0].upper() + key[1:]
                groupStats[groupKey] = runtimeStats[key]
            runtimeStats = groupStats
            if notInGroup == True:
                runtimeStats.update(controlInteractionStats)
            else:
                runtimeStats.update(experimentalInteractionStats)

        for key in runtimeStats.keys():
            self.runtimeStats[key] = runtimeStats[key]

    def writeToLog(self):
        if self.log == None:
            return
        logString = '\t' + json.dumps(self.runtimeStats) + ",\n"
        if self.logFormat == "csv":
            logString = ""
            # Ensure consistent ordering for CSV format
            for stat in sorted(self.runtimeStats):
                if logString == "":
                    logString += f"{self.runtimeStats[stat]}"
                else:
                    logString += f",{self.runtimeStats[stat]}"
            logString += "\n"
        self.log.write(logString)

    def __str__(self):
        string = f"Seed: {self.seed}\nTimestep: {self.timestep}\nLiving Agents: {len(self.agents)}"
        return string

def parseConfiguration(configFile, configuration):
    file = open(configFile)
    options = json.loads(file.read())
    # If using the top-level config file, access correct JSON object
    if "trendemicOptions" in options:
        options = options["trendemicOptions"]

    # Keep compatibility with outdated configuration files
    optkeys = options.keys()
    if "agentEthicalTheory" in optkeys:
        options["agentDecisionModel"] = options["agentEthicalTheory"]
    if "agentEthicalFactor" in optkeys:
        options["agentDecisionModelFactor"] = options["agentEthicalFactor"]

    for opt in configuration:
        if opt in options:
            configuration[opt] = options[opt]
    return configuration

def parseOptions(configuration):
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:h:"
    longOptions = ["conf=", "help"]
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        printHelp()
    nextArg = 0
    for currArg, currVal in args:
        nextArg += 1
        if currArg in("-c", "--conf"):
            if currVal == "":
                print("No config file provided.")
                printHelp()
            parseConfiguration(currVal, configuration)
        elif currArg in ("-h", "--help"):
            printHelp()
    return configuration

def printHelp():
    print("Usage:\n\tpython trendemic.py --conf config.json\n\nOptions:\n\t-c,--conf\tUse specified config file for simulation settings.\n\t-h,--help\tDisplay this message.")
    exit(0)

def sortConfigurationTimeframes(configuration, timeframe):
    config = configuration[timeframe]
    if configuration != [0, 0]:
        start = config[0]
        end = config[1]
        # Ensure start and end are in correct order
        if start > end and end >= 0:
            swap = start
            start = end
            end = swap
            if "all" in configuration["debugMode"] or "trendemic" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Start and end values provided for {timeframe} in incorrect order. Switching values around.")
        # If provided a negative value, assume the start timestep is the very first of the simulation
        if start < 0:
            if "all" in configuration["debugMode"] or "trendemic" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Start timestep {start} for {timeframe} is invalid. Setting {timeframe} start timestep to 0.")
            start = 0
        # If provided a negative value, assume the end timestep is the very end of the simulation
        if end < 0:
            if "all" in configuration["debugMode"] or "trendemic" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"End timestep {end} for {timeframe} is invalid. Setting {timeframe} end timestep to {configuration['timesteps']}.")
            end = configuration["timesteps"]
        config = [start, end]
    return config

def verifyConfiguration(configuration):
    negativesAllowed = ["seed"]
    timeframes = []
    negativeFlag = 0
    for configName, configValue in configuration.items():
        if isinstance(configValue, list):
            if len(configValue) == 0:
                continue
            configType = type(configValue[0])
            if configName in timeframes:
                configuration[configName] = sortConfigurationTimeframes(configuration, configName)
            else:
                configValue.sort()
            if configName not in negativesAllowed and (configType == int or configType == float):
                for i in range(len(configValue)):
                    if configValue[i] < 0:
                        configValue[i] = 0
                        negativeFlag += 1
        else:
            configType = type(configValue)
            if configName not in negativesAllowed and (configType == int or configType == float) and configValue < 0:
                configValue = 0
                negativeFlag += 1
                print(f"{configName}: {configValue}")
    if negativeFlag > 0:
        print(f"Detected negative values provided for {negativeFlag} option(s). Setting these values to zero.")

    if configuration["numInfluencers"] > configuration["numAgents"]:
        configuration["numInfluencers"] = configuration["numAgents"]
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print("Cannot have more influencers than agents. Setting number of influencers to number of agents.")

    # Set timesteps to (seemingly) unlimited runtime
    if configuration["timesteps"] < 0:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print("Cannot have a negative amount of timesteps. Setting timesetup to unlimited runtime.")
        configuration["timesteps"] = sys.maxsize

    if configuration["logfile"] == "":
        configuration["logfile"] = None

    if configuration["seed"] == -1:
        configuration["seed"] = random.randrange(sys.maxsize)

    recognizedDebugModes = ["agent", "all", "behavior", "none", "trendemic"]
    validModes = True
    for mode in configuration["debugMode"]:
        if mode not in recognizedDebugModes:
            print(f"Debug mode {mode} not recognized")
            validModes = False
    if validModes == False:
        printHelp()

    if "all" in configuration["debugMode"] and "none" in configuration["debugMode"]:
        print("Cannot have \"all\" and \"none\" debug modes enabled at the same time")
        printHelp()
    elif "all" in configuration["debugMode"] and len(configuration["debugMode"]) > 1:
        configuration["debugMode"] = "all"
    elif "none" in configuration["debugMode"] and len(configuration["debugMode"]) > 1:
        configuration["debugMode"] = "none"

    # Ensure experimental group is properly defined or otherwise ignored
    if configuration["experimentalGroup"] == "":
        configuration["experimentalGroup"] = None
    groupList = ["influencers"]
    if configuration["experimentalGroup"] != None and configuration["experimentalGroup"] not in groupList and "disease" not in configuration["experimentalGroup"]:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot provide separate log stats for experimental group {configuration['experimentalGroup']}. Disabling separate log stats.")
        configuration["experimentalGroup"] = None
    return configuration

if __name__ == "__main__":
    # Set default values for simulation configuration
    configuration = {
                     "agentGlobalWeight": [0.0, 0.0],
                     "agentLocalWeight": [1.0, 1.0],
                     "agentThreshold": [0.2, 0.2],
                     "debugMode": ["none"],
                     "experimentalGroup": None,
                     "headlessMode": True,
                     "influenceBehaviorModel": ["inky"],
                     "interfaceHeight": 1000,
                     "interfaceWidth": 900,
                     "keepAliveAtEnd": False,
                     "keepAlivePostExtinction": False,
                     "logfile": None,
                     "logfileFormat": "json",
                     "networkType": "local",
                     "numAgents": 10,
                     "numInfluencers": 1,
                     "profileMode": False,
                     "screenshots": False,
                     "seed": -1,
                     "threshold": 0.2,
                     "timesteps": 200
                     }
    k = 2
    p = 3
    m = 4
    network_type = "hybrid"
    sweep_parameter = "threshold"
    sweep_start = 0.2
    sweep_end = 0.2
    sweep_step = 0.01
    num_trials = 10
    tipping_fraction = 0.75

    sweep_enabled = True
    evaluation_mode = "tipping_threshold"
 
    moreConfigs = {
                   "k": k,
                   "p": p,
                   "m": m,
                   "social_engineer_enabled": False,
                   "seeding_strategy": None,
                   }

    configuration = parseOptions(configuration)
    configuration = verifyConfiguration(configuration)
    if configuration["headlessMode"] == False:
        import gui
    random.seed(configuration["seed"])
    T = Trendemic(configuration)
    if configuration["profileMode"] == True:
        import cProfile
        import tracemalloc
        tracemalloc.start()
        cProfile.run("T.runSimulation(configuration[\"timesteps\"])")
        snapshot = tracemalloc.take_snapshot()
        memoryStats = snapshot.statistics("lineno", True)
        for stat in memoryStats[:100]:
            print(stat)
    else:
        T.runSimulation(configuration["timesteps"])
    exit(0)
