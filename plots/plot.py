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
        generateSimpleLinePlot(sweepParameter, dataset, totalTimesteps, f"{statistic}_adoption.pdf", "influenced", f"{titleStatistic} Adoption", "center right", True, config)

def generateSimpleLinePlot(sweepParameterName, datasetValues, totalTimestepsCount, outputFile, targetColumn, axisLabel, legendPosition, usePercentage = False, configuration = None):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 18
    figure, axes = matplotlib.pyplot.subplots()
    axes.set(xlabel = "Timestep", ylabel = axisLabel, xlim = [0, totalTimestepsCount])
    xAxisValues = [i for i in range(totalTimestepsCount + 1)]
    colorPalette = ["magenta", "cyan", "yellow", "black", "red", "green", "blue", "purple", "gray", "brown", "pink"]
    plotIncrement = configuration["plotIncrement"]

    sortableSweepItems = []
    for sweepKey in datasetValues.keys():
        try:
            numericValue = float(sweepKey)
            sortableSweepItems.append((0, numericValue, sweepKey))
        except Exception:
            sortableSweepItems.append((1, float("inf"), sweepKey))
    sortableSweepItems.sort()

    baseValue = None
    for flag, numericValue, sweepKey in sortableSweepItems:
        if flag == 0:
            baseValue = numericValue
            break

    tolerance = 1e-9
    colorIndex = 0
    for flag, numericValue, sweepKey in sortableSweepItems:
        if flag == 0 and baseValue is not None:
            estimatedSteps = (numericValue - baseValue) / plotIncrement
            integerSteps = int(round(estimatedSteps))
            snappedValue = baseValue + integerSteps * plotIncrement
            if abs(snappedValue - numericValue) > tolerance:
                continue
        if usePercentage:
            percentageDenominator = datasetValues[sweepKey]["aggregates"]["agents"][0] / 100.0
        else:
            percentageDenominator = 1.0
        sweepValueLabel = f"{sweepKey} {sweepParameterName}"
        yAxisValues = [datasetValues[sweepKey]["aggregates"][targetColumn][i] / percentageDenominator for i in range(totalTimestepsCount + 1)]
        axes.plot(xAxisValues, yAxisValues, color = colorPalette[colorIndex % len(colorPalette)], label = sweepValueLabel)
        colorIndex += 1

    if usePercentage:
        axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    axes.legend(loc = legendPosition, labelspacing = 0.1, frameon = False, fontsize = 16)
    figure.savefig(outputFile, format = "pdf", bbox_inches = "tight")

def generateSummaryTable(datasetValues, sweepParameterName, totalTimestepsCount, adoptionThreshold, outputPath, searchDirectionSetting):
    sweepRows = []
    for sweepKey in datasetValues.keys():
        agentsSeries = datasetValues[sweepKey]["aggregates"]["agents"]
        influencedSeries = datasetValues[sweepKey]["aggregates"]["influenced"]
        if not agentsSeries or not influencedSeries:
            finalAdoptionFraction = 0.0
        else:
            timestepIndex = min(totalTimestepsCount, len(agentsSeries) - 1, len(influencedSeries) - 1)
            agentsFinal = agentsSeries[timestepIndex]
            influencedFinal = influencedSeries[timestepIndex]
            finalAdoptionFraction = 0.0 if agentsFinal == 0 else float(influencedFinal) / float(agentsFinal)
        try:
            numericValue = float(sweepKey)
            sweepRows.append((0, numericValue, sweepKey, finalAdoptionFraction))
        except Exception:
            sweepRows.append((1, float("inf"), sweepKey, finalAdoptionFraction))
    sweepRows.sort()

    selectedSweepKey = None
    if searchDirectionSetting == "highest":
        for flag, numericValue, sweepKey, adoptionFraction in reversed(sweepRows):
            if adoptionFraction >= adoptionThreshold:
                selectedSweepKey = sweepKey
                break
    else:
        for flag, numericValue, sweepKey, adoptionFraction in sweepRows:
            if adoptionFraction >= adoptionThreshold:
                selectedSweepKey = sweepKey
                break

    if selectedSweepKey is None:
        print("No sweep value reached the adoptionThreshold.")
        return

    adoptionRateSeries = datasetValues[selectedSweepKey]["aggregates"].get("adoptionRate", [])
    meanDegreeNewlyInfluencedSeries = datasetValues[selectedSweepKey]["aggregates"].get("meanDegreeNewlyInfluenced", [])

    peakAdoptionRate = 0.0
    timestepAtPeakAdoption = 0
    for timestepIndex, adoptionValue in enumerate(adoptionRateSeries):
        if adoptionValue > peakAdoptionRate:
            peakAdoptionRate = adoptionValue
            timestepAtPeakAdoption = timestepIndex

    meanDegreeAtPeak = 0.0
    if meanDegreeNewlyInfluencedSeries and timestepAtPeakAdoption < len(meanDegreeNewlyInfluencedSeries):
        meanDegreeAtPeak = meanDegreeNewlyInfluencedSeries[timestepAtPeakAdoption]

    print("")
    print("=== One-row Summary ===")
    print("sweepParameter = {0}".format(sweepParameterName))
    print("tippingPoint = {0}".format(selectedSweepKey))
    print("peakAdoptionRate = {0:.2f}".format(peakAdoptionRate))
    print("timestepPeakAdoptionRate = {0}".format(timestepAtPeakAdoption))
    print("meanDegreeNewlyInfluencedPeak = {0:.2f}".format(meanDegreeAtPeak))

    summaryPdfPath = os.path.join(os.path.dirname(__file__), "summary.pdf")
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 14
    figure, axes = matplotlib.pyplot.subplots(figsize = (8.5, 2.2))
    axes.axis("off")
    summaryTableData = [
        ["sweepParameter", sweepParameterName],
        ["tippingPoint", str(selectedSweepKey)],
        ["peakAdoptionRate", "{0:.2f}".format(peakAdoptionRate)],
        ["timestepPeakAdoptionRate", str(timestepAtPeakAdoption)],
        ["meanDegreeNewlyInfluencedPeak", "{0:.2f}".format(meanDegreeAtPeak)]
    ]
    columnLabels = ["Metric", "Value"]
    summaryTable = axes.table(cellText = summaryTableData, colLabels = columnLabels, loc = "center")

    for tableCell in summaryTable.get_celld().values():
        tableCell.set_text_props(ha = "center", va = "center")

    summaryTable.auto_set_font_size(False)
    summaryTable.set_fontsize(12)
    summaryTable.scale(1.1, 1.4)
    figure.tight_layout()
    figure.savefig(summaryPdfPath, format = "pdf", bbox_inches = "tight")
    matplotlib.pyplot.close(figure)
    print("Summary PDF written to {0}".format(summaryPdfPath))

def parseDataset(path, dataset, totalTimesteps, statistic, skipExtinct=False):
    encodedDir = os.fsencode(path)
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not (filename.endswith(".json") or filename.endswith(".csv")):
            continue
        filePath = path + filename
        fileDecisionModel = re.compile(r"^(.+)-(\d+)\.(json|csv)")
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
    dataConfig = config["dataCollectionOptions"]
    trendemicConfig = config["trendemicOptions"]
    totalTimesteps = dataConfig["plotTimesteps"]
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
    adoption_threshold = trendemicConfig["adoptionThreshold"]
    search_direction = dataConfig.get("thresholdSearchDirection", "lowest")
    generateSummaryTable(dataset, sweepParameter, totalTimesteps, adoption_threshold, path, search_direction)
    exit(0)
