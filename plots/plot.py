import csv
import getopt
import json
import math
import matplotlib.pyplot
import matplotlib.ticker
import os
import re
import sys

def findMeans(dataset):
    print(f"Finding mean values across {totalTimesteps} timesteps")
    for sweepValue in dataset:
        print(sweepValue)
        for column in dataset[sweepValue]["metrics"]:
            for i in range(len(dataset[sweepValue]["metrics"][column])):
                if column not in dataset[sweepValue]["aggregates"]:
                    dataset[sweepValue]["aggregates"][column] = [0 for j in range(totalTimesteps + 1)]
                dataset[sweepValue]["aggregates"][column][i] = dataset[sweepValue]["metrics"][column][i] / dataset[sweepValue]["runs"]
    return dataset

def findMedians(dataset):
    print(f"Finding median values across {totalTimesteps} timesteps")
    for sweepValue in dataset:
        for column in dataset[sweepValue]["metrics"]:
            for i in range(len(dataset[sweepValue]["metrics"][column])):
                sortedColumn = sorted(dataset[sweepValue]["metrics"][column][i])
                columnLength = len(sortedColumn)
                midpoint = math.floor(columnLength / 2)
                median = sortedColumn[midpoint]
                quartile = math.floor(columnLength / 4)
                firstQuartile = sortedColumn[quartile]
                thirdQuartile = sortedColumn[midpoint + quartile]
                if columnLength % 2 == 0:
                    median = round((sortedColumn[midpoint - 1] + median) / 2, 2)
                    firstQuartile = round((sortedColumn[quartile - 1] + firstQuartile) / 2, 2)
                    thirdQuartile = round((sortedColumn[(midpoint + quartile) - 1] + thirdQuartile) / 2, 2)
                if column not in dataset[sweepValue]["aggregates"]:
                    dataset[sweepValue]["aggregates"][column] = [0 for j in range(totalTimesteps + 1)]
                    dataset[sweepValue]["firstQuartiles"][column] = [0 for j in range(totalTimesteps + 1)]
                    dataset[sweepValue]["thirdQuartiles"][column] = [0 for j in range(totalTimesteps + 1)]
                dataset[sweepValue]["aggregates"][column][i] = median
    return dataset

def generatePlots(config, sweepParameter, totalTimesteps, dataset, statistic):
    titleStatistic = statistic.title()
    if "adoption" in config["plots"]:
        print(f"Generating {statistic} adoption plot")
        generateSimpleLinePlot(sweepParameter, dataset, totalTimesteps, f"{statistic}_adoption.pdf", "influenced", f"{titleStatistic} Adoption", "center right", True)

def generateSimpleLinePlot(sweepParameter, dataset, totalTimesteps, outfile, column, label, positioning, percentage=False):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 18
    figure, axes = matplotlib.pyplot.subplots()
    axes.set(xlabel = "Timestep", ylabel = label, xlim = [0, totalTimesteps])
    x = [i for i in range(totalTimesteps + 1)]
    y = [0 for i in range(totalTimesteps + 1)]
    lines = []
    colors = ["magenta", "cyan", "yellow", "black", "red", "green", "blue"]
    colorIndex = 0
    for sweepValue in dataset:
        percentageDenominator = dataset[sweepValue]["aggregates"]["agents"][0]  / 100 if percentage == True else 1
        sweepValueString = f"{sweepValue} {sweepParameter}"
        y = [dataset[sweepValue]["aggregates"][column][i] / percentageDenominator for i in range(totalTimesteps + 1)]
        print(y)
        axes.plot(x, y, color=colors[colorIndex % len(colors)], label=sweepValueString)
        colorIndex += 1
    if percentage == True:
        axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    axes.legend(loc=positioning, labelspacing=0.1, frameon=False, fontsize=16)
    figure.savefig(outfile, format="pdf", bbox_inches="tight")

def parseDataset(path, dataset, totalTimesteps, statistic, skipExtinct=False):
    encodedDir = os.fsencode(path)
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not (filename.endswith(".json") or filename.endswith(".csv")):
            continue
        filePath = path + filename
        fileDecisionModel = re.compile(r"^(\d+\.\d+)-(\d+)\.(json|csv)")
        fileSearch = re.search(fileDecisionModel, filename)
        if fileSearch == None:
            continue
        sweepValue = fileSearch.group(1)
        if sweepValue not in dataset:
            dataset[sweepValue] = {"runs": 0, "timesteps": 0, "aggregates": {}, "firstQuartiles": {}, "thirdQuartiles": {}, "metrics": {}}
        seed = fileSearch.group(2)
        log = open(filePath)
        print(f"Reading log {filePath}")
        rawData = None
        if filename.endswith(".json"):
            rawData = json.loads(log.read())
        else:
            rawData = list(csv.DictReader(log))

        dataset[sweepValue]["runs"] += 1
        i = 1
        for item in rawData:
            if int(item["timestep"]) > totalTimesteps:
                break
            if int(item["timestep"]) > dataset[sweepValue]["timesteps"]:
                dataset[sweepValue]["timesteps"] += 1

            for entry in item:
                if entry not in dataset[sweepValue]["metrics"]:
                    if statistic == "mean":
                        dataset[sweepValue]["metrics"][entry] = [0 for j in range(totalTimesteps + 1)]
                    elif statistic == "median":
                        dataset[sweepValue]["metrics"][entry] = [[] for j in range(totalTimesteps + 1)]
                if item[entry] == "None":
                    item[entry] = 0
                if statistic == "mean":
                    dataset[sweepValue]["metrics"][entry][i-1] += float(item[entry])
                elif statistic == "median":
                    dataset[sweepValue]["metrics"][entry][i-1].append(float(item[entry]))
            i += 1
    for sweepValue in dataset:
        if dataset[sweepValue]["runs"] == 0:
            print(f"No simulation runs found for the {sweepValue} sweep value.")
    return dataset

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:p:s:t:h"
    longOptions = ("conf=", "path=", "help", "skip")
    options = {"config": None, "path": None, "skip": False}
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        exit(0)
    for currArg, currVal in args:
        if currArg in ("-c", "--conf"):
            if currVal == "":
                print("No config file provided.")
                printHelp()
            options["config"] = currVal
        elif currArg in ("-p", "--path"):
            options["path"] = currVal
            if currVal == "":
                print("No dataset path provided.")
                printHelp()
        elif currArg in ("-h", "--help"):
            printHelp()
    flag = 0
    if options["path"] == None:
        print("Dataset path required.")
        flag = 1
    if options["config"] == None:
        print("Configuration file path required.")
        flag = 1
    if flag == 1:
        printHelp()
    return options

def printHelp():
    print("Usage:\n\tpython plot.py --path /path/to/data --conf /path/to/config > results.dat\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-p,--path\tUse the specified path to find dataset JSON files.\n\t-h,--help\tDisplay this message.")
    exit(0)

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    config = options["config"]
    skipExtinct = options["skip"]
    configFile = open(config)
    config = json.loads(configFile.read())
    configFile.close()
    config = config["dataCollectionOptions"]
    totalTimesteps = config["plotTimesteps"]
    statistic = config["plotStatistic"]
    sweepParameter = config["sweepParameter"]
    dataset = {}

    if not os.path.exists(path):
        print(f"Path {path} not recognized.")
        printHelp()

    dataset = parseDataset(path, dataset, totalTimesteps, statistic, skipExtinct)
    if statistic == "mean":
        dataset = findMeans(dataset)
    elif statistic == "median":
        dataset = findMedians(dataset)
    else:
        print(f"Plotting statistic {statistic} not recognized.")
        printHelp()

    generatePlots(config, sweepParameter, totalTimesteps, dataset, statistic)
    exit(0)
