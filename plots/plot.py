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
    for sweepKey in dataset:
        for column in dataset[sweepKey]["metrics"]:
            for i in range(len(dataset[sweepKey]["metrics"][column])):
                if column not in dataset[sweepKey]["aggregates"]:
                    dataset[sweepKey]["aggregates"][column] = [0 for j in range(totalTimesteps + 1)]
                dataset[sweepKey]["aggregates"][column][i] = dataset[sweepKey]["metrics"][column][i] / dataset[sweepKey]["runs"]
    return dataset

def findMedians(dataset):
    print(f"Finding median values across {totalTimesteps} timesteps")
    for sweepKey in dataset:
        for column in dataset[sweepKey]["metrics"]:
            for i in range(len(dataset[sweepKey]["metrics"][column])):
                sortedColumn = sorted(dataset[sweepKey]["metrics"][column][i])
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
                if column not in dataset[sweepKey]["aggregates"]:
                    dataset[sweepKey]["aggregates"][column] = [0 for j in range(totalTimesteps + 1)]
                    dataset[sweepKey]["firstQuartiles"][column] = [0 for j in range(totalTimesteps + 1)]
                    dataset[sweepKey]["thirdQuartiles"][column] = [0 for j in range(totalTimesteps + 1)]
                dataset[sweepKey]["aggregates"][column][i] = median
    return dataset

def findNumberOfDecimals(number):
    decimalCount = 0
    decimals = str(number).split('.')
    if len(decimals) == 2:
        decimalCount = len(decimals[1])
    return decimalCount

def generatePlots(config, sweepParameter, totalTimesteps, dataset, statistic):
    titleStatistic = statistic.title()
    plotIncrement = config["plotIncrement"] if "plotIncrement" in config else None
    if "adoption" in config["plots"]:
        print(f"Generating {statistic} adoption plot")
        generateSimpleLinePlot(sweepParameter, dataset, totalTimesteps, f"{statistic}_adoption.pdf", "influenced", f"{titleStatistic} Adoption", "center right", plotIncrement, True)

def generateSimpleLinePlot(sweepParameter, dataset, totalTimesteps, outfile, column, label, positioning, plotIncrement=None, percentage=False):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 18
    figure, axes = matplotlib.pyplot.subplots()
    axes.set(xlabel="Timestep", ylabel=label, xlim=[0, totalTimesteps])
    x = [i for i in range(totalTimesteps + 1)]
    colorIndex = 0
    colorPalette = ["magenta", "cyan", "yellow", "black", "red", "green", "blue", "purple", "gray", "brown", "pink"]
    percentageDenominator = 1

    for sweepKey, dictValue in sorted(dataset.items()):
        if findNumberOfDecimals(sweepKey) == findNumberOfDecimals(plotIncrement):
            if percentage == True:
                percentageDenominator = dataset[sweepKey]["aggregates"]["agents"][0] / 100
            sweepKeyLabel = f"{sweepKey} {sweepParameter}"
            y = [dataset[sweepKey]["aggregates"][column][i] / percentageDenominator for i in range(totalTimesteps + 1)]
            axes.plot(x, y, color=colorPalette[colorIndex % len(colorPalette)], label=sweepKeyLabel)
            colorIndex += 1

    if percentage == True:
        axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    axes.legend(loc=positioning, labelspacing=0.1, frameon=False, fontsize=16)
    figure.savefig(outfile, format="pdf", bbox_inches="tight")

def generateSummaryTable(sweepParameter, totalTimesteps, adoptionThreshold, searchDirection, dataset):
    sweepRows = []
    finalAdoptionFraction = 0
    for sweepKey in dataset:
        agents = dataset[sweepKey]["aggregates"]["agents"][-1]
        influenced = dataset[sweepKey]["aggregates"]["influenced"][-1]
        if influenced > 0:
            finalAdoptionFraction = agents / influenced
            sweepRows.append((sweepKey, finalAdoptionFraction))
    sweepRows.sort()

    selectedSweepKey = None
    if searchDirection == "highest":
        for sweepKey, adoptionFraction in reversed(sweepRows):
            if adoptionFraction >= adoptionThreshold:
                selectedSweepKey = sweepKey
                break
    else:
        for sweepKey, adoptionFraction in sweepRows:
            if adoptionFraction >= adoptionThreshold:
                selectedSweepKey = sweepKey
                break

    if selectedSweepKey != None:
        adoptionRates = dataset[selectedSweepKey]["aggregates"]["adoptionRate"]
        meanDegreesNewlyInfluenced = dataset[selectedSweepKey]["aggregates"]["meanDegreeNewlyInfluenced"]
        meanDegreeAtPeak = 0
        peakAdoptionRate = 0
        timestepAtPeak = 0

        timestep = 0
        for adoptionRate in adoptionRates:
            if adoptionRate > peakAdoptionRate:
                peakAdoptionRate = adoptionRate
                timestepAtPeak = timestep
                meanDegreeAtPeak = meanDegreesNewlyInfluenced[timestepAtPeak]
            timestep += 1

        print(f"\n=== Summary Statistics ===\nSweep Parameter = {sweepParameter}\nTipping Point = {selectedSweepKey}\nPeak Adoption Rate = {peakAdoptionRate}\nTimestep at Peak Adoption Rate = {timestepAtPeak:.2f}\nMean Degree for Newly Influenced Agents at Peak Adoption Rate = {meanDegreeAtPeak:.2f}")
    else:
        print("No sweep value reached the adoption threshold.")

def parseDataset(path, dataset, totalTimesteps, statistic, skipExtinct=False):
    encodedDir = os.fsencode(path)
    fileCount = 1
    files = [f for f in os.listdir(encodedDir) if os.fsdecode(f).endswith("json") or os.fsdecode(f).endswith(".csv")]
    printFileLength = len(max(files, key=len))
    totalFiles = len(files)
    for file in files:
        filename = os.fsdecode(file)
        filePath = path + filename
        fileDecisionModel = re.compile(r"^(.+)-(\d+)\.(json|csv)")
        fileSearch = re.search(fileDecisionModel, filename)
        if fileSearch == None:
            continue
        sweepKey = fileSearch.group(1)
        if sweepKey not in dataset:
            dataset[sweepKey] = {"runs": 0, "timesteps": 0, "aggregates": {}, "firstQuartiles": {}, "thirdQuartiles": {}, "metrics": {}}
        seed = fileSearch.group(2)
        log = open(filePath)
        printProgress(filename, fileCount, totalFiles, printFileLength)
        fileCount += 1
        rawData = None
        if filename.endswith(".json"):
            rawData = json.loads(log.read())
        else:
            rawData = list(csv.DictReader(log))

        dataset[sweepKey]["runs"] += 1
        i = 1
        for item in rawData:
            if int(item["timestep"]) > totalTimesteps:
                break
            if int(item["timestep"]) > dataset[sweepKey]["timesteps"]:
                dataset[sweepKey]["timesteps"] += 1

            for entry in item:
                if entry not in dataset[sweepKey]["metrics"]:
                    if statistic == "mean":
                        dataset[sweepKey]["metrics"][entry] = [0 for j in range(totalTimesteps + 1)]
                    elif statistic == "median":
                        dataset[sweepKey]["metrics"][entry] = [[] for j in range(totalTimesteps + 1)]
                if item[entry] == "None":
                    item[entry] = 0
                if statistic == "mean":
                    dataset[sweepKey]["metrics"][entry][i-1] += float(item[entry])
                elif statistic == "median":
                    dataset[sweepKey]["metrics"][entry][i-1].append(float(item[entry]))
            i += 1
    for sweepKey in dataset:
        if dataset[sweepKey]["runs"] == 0:
            print(f"No simulation runs found for the {sweepKey} sweep value.")
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

def printProgress(filename, filesParsed, totalFiles, fileLength, decimals=2):
    barLength = os.get_terminal_size().columns // 2
    progress = round(((filesParsed / totalFiles) * 100), decimals)
    filledLength = (barLength * filesParsed) // totalFiles
    bar = '█' * filledLength + '-' * (barLength - filledLength)
    printString = f"\rParsing {filename:>{fileLength}}: |{bar}| {filesParsed} / {totalFiles} ({progress}%)"
    if filesParsed == totalFiles:
        print(f"\r{' ' * os.get_terminal_size().columns}", end='\r')
    else:
        print(f"\r{printString}", end='\r')

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    config = options["config"]
    skipExtinct = options["skip"]
    configFile = open(config)
    config = json.loads(configFile.read())
    configFile.close()
    dataConfig = config["dataCollectionOptions"]
    trendemicConfig = config["trendemicOptions"]
    adoptionThreshold = trendemicConfig["adoptionThreshold"]
    totalTimesteps = dataConfig["plotTimesteps"]
    searchDirection = "lowest"
    if "thresholdSearchDirection" in dataConfig:
        searchDirection = dataConfig["thresholdSearchDirection"]
    statistic = dataConfig["plotStatistic"]
    sweepParameter = dataConfig["sweepParameter"]
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

    generatePlots(dataConfig, sweepParameter, totalTimesteps, dataset, statistic)
    generateSummaryTable(sweepParameter, totalTimesteps, adoptionThreshold, searchDirection, dataset)
    exit(0)
