import math
import tkinter

class GUI:
    def __init__(self, trendemic, screenHeight=1000, screenWidth=900):
        self.trendemic = trendemic
        self.screenHeight = screenHeight
        self.screenWidth = screenWidth
        self.canvas = None
        self.graph = [None for i in range(len(self.trendemic.agents))]
        self.window = None
        self.doubleClick = False
        self.resizeID = None

        self.palette = ["#FA3232", "#3232FA", "#32FA32", "#32FAFA", "#FA32FA", "#AA3232", "#3232AA", "#32AA32", "#32AAAA", "#AA32AA", "#FA8800", "#00FA88", "#8800FA", "#FA8888", "#8888FA", "#88FA88", "#FA3288", "#3288FA", "#88FA32", "#AA66AA", "#66AAAA", "#3ED06E", "#6E3ED0", "#D06E3E", "#000000"]
        self.colors = {"default": self.palette[0], "influencer": self.palette[1]}

        # Set the default strings for interface at simulation start
        self.defaultAgentString = "Agent: - | Age: -"
        self.defaultSimulationString = "Timestep: - | Agents: -"

        self.widgets = {}
        self.activeNetwork = None
        self.activeGraph = None
        self.borderEdge = 5
        self.graphObjects = {}
        self.graphBorder = 90
        self.xTicks = 10
        self.yTicks = 2
        self.lastSelectedAgentColor = None
        self.lastSelectedEnvironmentColor = None
        self.activeColorOptions = {"agent": None, "environment": None}
        self.highlightedAgent = None
        self.highlightedCell = None
        self.highlightRectangle = None
        self.menuTrayColumns = 6
        self.siteHeight = 0
        self.siteWidth = 0
        self.stopSimulation = False
        self.configureWindow()

    def clamp(self, value, mininum, maximum):
        if value < mininum:
            return mininum
        elif value > maximum:
            return maximum
        return value

    def clearHighlight(self):
        self.highlightedAgent = None
        self.highlightedCell = None
        if self.highlightRectangle != None:
            self.canvas.delete(self.highlightRectangle)
            self.highlightRectangle = None
        self.updateHighlightedCellStats()

    def configureAgentColorNames(self):
        return ["Decision Models", "Depression", "Disease", "Metabolism", "Movement", "Sex", "Tribes", "Vision"]

    def configureButtons(self, window):
        playButton = tkinter.Button(window, text="Play Simulation", command=self.doPlayButton)
        playButton.grid(row=0, column=0, sticky="nsew")
        stepButton = tkinter.Button(window, text="Step Forward", command=self.doStepForwardButton, relief=tkinter.RAISED)
        stepButton.grid(row=0, column=1, sticky="nsew")

        networkButton = tkinter.Menubutton(window, text="Networks", relief=tkinter.RAISED)
        networkMenu = tkinter.Menu(networkButton, tearoff=0)
        networkButton.configure(menu=networkMenu)
        networkNames = self.configureNetworkNames()
        networkNames.insert(0, "None")
        self.activeNetwork = tkinter.StringVar(window)

        # Use first item as default name
        self.activeNetwork.set(networkNames[0])
        for network in networkNames:
            networkMenu.add_checkbutton(label=network, onvalue=network, offvalue=network, variable=self.activeNetwork, command=self.doNetworkMenu, indicatoron=True)
        networkButton.grid(row=0, column=2, sticky="nsew") 

        graphButton = tkinter.Menubutton(window, text="Graphs", relief=tkinter.RAISED)
        graphMenu = tkinter.Menu(graphButton, tearoff=0)
        graphButton.configure(menu=graphMenu)
        graphNames = self.configureGraphNames()
        graphNames.insert(0, "None")
        self.activeGraph = tkinter.StringVar(window)

        # Use first item as default name
        self.activeGraph.set(graphNames[0])
        for graph in graphNames:
            graphMenu.add_checkbutton(label=graph, onvalue=graph, offvalue=graph, variable=self.activeGraph, command=self.doGraphMenu, indicatoron=True)
        graphButton.grid(row=0, column=3, sticky="nsew") 

        agentColorButton = tkinter.Menubutton(window, text="Agent Coloring", relief=tkinter.RAISED)
        agentColorMenu = tkinter.Menu(agentColorButton, tearoff=0)
        agentColorButton.configure(menu=agentColorMenu)
        agentColorNames = self.configureAgentColorNames()
        agentColorNames.sort()
        agentColorNames.insert(0, "Default")
        self.lastSelectedAgentColor = tkinter.StringVar(window)

        # Use first item as default name
        self.lastSelectedAgentColor.set(agentColorNames[0])
        for name in agentColorNames:
            agentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=self.lastSelectedAgentColor, command=self.doAgentColorMenu, indicatoron=True)
        agentColorButton.grid(row=0, column=4, sticky="nsew")

        editingButton = tkinter.Menubutton(window, text="Editing Mode", relief=tkinter.RAISED)
        editingMenu = tkinter.Menu(editingButton, tearoff=0)
        editingButton.configure(menu=editingMenu)
        editingModes = self.configureEditingModes()
        editingModes.sort()
        editingModes.insert(0, "None")
        self.lastSelectedEditingMode = tkinter.StringVar(window)

        # Use first item as default name
        self.lastSelectedEditingMode.set(editingModes[0])
        for mode in editingModes:
            editingMenu.add_checkbutton(label=mode, onvalue=mode, offvalue=mode, variable=self.lastSelectedEditingMode, command=self.doEditingMenu, indicatoron=True)
        editingButton.grid(row=0, column=5, sticky="nsew")

        statsLabel = tkinter.Label(window, text=self.defaultSimulationString, font="Roboto 10", justify=tkinter.CENTER)

        self.widgets["playButton"] = playButton
        self.widgets["stepButton"] = stepButton
        self.widgets["networkButton"] = networkButton
        self.widgets["graphButton"] = graphButton
        self.widgets["agentColorButton"] = agentColorButton
        self.widgets["editingButton"] = editingButton
        self.widgets["agentColorMenu"] = agentColorMenu
        self.widgets["statsLabel"] = statsLabel

    def configureCanvas(self):
        canvas = tkinter.Canvas(self.window, background="white")
        canvas.grid(row=3, column=0, columnspan=self.menuTrayColumns, sticky="nsew")
        if self.activeGraph.get() == "None":
            canvas.bind("<Button-1>", self.doClick)
            canvas.bind("<Double-Button-1>", self.doDoubleClick)
            canvas.bind("<Control-Button-1>", self.doControlClick)
            self.doubleClick = False
        self.canvas = canvas

    def configureEditingModes(self):
        return ["Add Agent"]

    def configureGraph(self):
        i = 1
        j = 1
        print(f"Width: {self.siteWidth}\tHeight: {self.siteHeight}")
        for agent in self.trendemic.agents:
            fillColor = self.lookupFillColor(agent)
            x1 = i * self.siteWidth
            y1 = j * self.siteHeight
            x2 = x1 + self.siteWidth
            y2 = y1 + self.siteHeight
            print(f"({x1},{y1})->({x2},{y2})")
            if self.activeNetwork.get() != "None":
                self.graph[agent.ID] = {"object": self.canvas.create_oval(x1, y1, x2, y1, fill=self.colors["default"], outline=""), "agent": agent, "color": fillColor}
            else:
                self.graph[agent.ID] = {"object": self.canvas.create_oval(x1, y1, x2, y2, fill=self.colors["default"], outline="#c0c0c0", activestipple="gray50"), "agent": agent, "color": fillColor}
            i += 1
            j += 1
        if self.activeNetwork.get() != "None":
            self.drawLines()

        if self.highlightedCell != None:
            self.highlightCell(self.highlightedCell)

    def configureGraphNames(self):
        return ["TODO"]

    def configureNetworkNames(self):
        return ["TODO"]

    def configureWindow(self):
        window = tkinter.Tk()
        self.window = window
        window.title("Sugarscape")
        window.minsize(width=150, height=250)
        # Do one-quarter window sizing only after initial window object is created to get user's monitor dimensions
        if self.screenWidth < 0:
            self.screenWidth = math.ceil(window.winfo_screenwidth() / 2) - self.borderEdge
        if self.screenHeight < 0:
            self.screenHeight = math.ceil(window.winfo_screenheight() / 2) - self.borderEdge
        window.geometry(f"{self.screenWidth + self.borderEdge}x{self.screenHeight + self.borderEdge}")
        window.option_add("*font", "Roboto 10")
        # Make the canvas and buttons fill the window
        window.grid_rowconfigure(3, weight=1)
        window.grid_columnconfigure(list(range(self.menuTrayColumns)), weight=1)
        self.configureButtons(window)
        self.configureCanvas()

        self.updateSiteDimensions()
        self.configureGraph()

        self.window.protocol("WM_DELETE_WINDOW", self.doWindowClose)
        self.window.bind("<Escape>", self.doWindowClose)
        self.window.bind("<space>", self.doPlayButton)
        self.window.bind("<Right>", self.doStepForwardButton)
        self.window.bind("<Configure>", self.doResize)

        self.doCrossPlatformWindowSizing()

    def deleteLines(self):
        self.canvas.delete("line")

    def destroyCanvas(self):
        self.canvas.destroy()

    def doAgentColorMenu(self, *args):
        self.activeColorOptions["agent"] = self.lastSelectedAgentColor.get()
        self.doTimestep()

    def doClick(self, event):
        self.canvas.after(300, self.doClickAction, event)

    def doClickAction(self, event):
        cell = self.findClickedCell(event)
        if self.doubleClick == True:
            if cell == self.highlightedCell or cell.agent == None:
                self.clearHighlight()
            else:
                self.highlightedCell = cell
                self.highlightedAgent = cell.agent
                self.highlightCell(cell)
            self.doubleClick = False
        else:
            if cell == self.highlightedCell and self.highlightedAgent == None:
                self.clearHighlight()
            else:
                self.highlightedCell = cell
                self.highlightedAgent = None
                self.highlightCell(cell)
        if self.lastSelectedEditingMode.get() != "None":
            self.doEditAction(cell)
        self.doTimestep()

    def doControlClick(self, event):
        self.doubleClick = False
        cell = self.findClickedCell(event)
        if cell == self.highlightedCell or cell.agent == None:
            self.clearHighlight()
        else:
            self.highlightedCell = cell
            self.highlightedAgent = cell.agent
            self.highlightCell(cell)
        self.doTimestep()

    def doCrossPlatformWindowSizing(self):
        self.window.update_idletasks()
        self.resizeInterface()
        self.window.update_idletasks()
        self.resizeInterface()

    def doDoubleClick(self, event):
        self.doubleClick = True

    def doEditAction(self, cell):
        mode = self.lastSelectedEditingMode.get()
        if mode == "Add Agent":
            self.trendemic.configureAgents(1, cell)
        elif mode == "Add Disease":
            self.trendemic.configureDiseases(1, [], cell)
        elif "Current" in mode:
            resourceMode = "currentSpice" if "Spice" in mode else "currentSugar"
            delta = 1 if "Add" in mode else -1
            self.trendemic.configureCell(cell, resourceMode, delta)
        elif "Maximum" in mode:
            resourceMode = "maximumSpice" if "Spice" in mode else "maximumSugar"
            delta = 1 if "Add" in mode else -1
            self.trendemic.configureCell(cell, resourceMode, delta)
        self.doTimestep()

    def doEditingMenu(self):
        self.doTimestep()

    def doEnvironmentColorMenu(self):
        self.activeColorOptions["environment"] = self.lastSelectedEnvironmentColor.get()
        self.doTimestep()

    def doGraphMenu(self):
        self.destroyCanvas()
        self.configureCanvas()
        if self.activeGraph.get() != "None":
            self.clearHighlight()
            self.configureGraph()
            self.widgets["networkButton"].configure(state="disabled")
            self.widgets["agentColorButton"].configure(state="disabled")
            self.widgets["environmentColorButton"].configure(state="disabled")
        else:
            self.configureGraph()
            self.widgets["networkButton"].configure(state="normal")
            self.widgets["agentColorButton"].configure(state="normal")
            self.widgets["environmentColorButton"].configure(state="normal")
        self.window.update()

    def doGraphTimestep(self):
        activeGraph = self.activeGraph.get()
        self.updateHistogram()

    def doNetworkMenu(self):
        if self.activeNetwork.get() != "None":
            self.widgets["graphButton"].configure(state="disabled")
            self.widgets["agentColorButton"].configure(state="disabled")
            self.widgets["environmentColorButton"].configure(state="disabled")
        else:
            self.widgets["graphButton"].configure(state="normal")
            self.widgets["agentColorButton"].configure(state="normal")
            self.widgets["environmentColorButton"].configure(state="normal")
        self.destroyCanvas()
        self.configureCanvas()
        self.configureGraph()
        self.window.update()

    def doPlayButton(self, *args):
        self.trendemic.toggleRun()
        self.widgets["playButton"].config(text="Play Simulation" if self.trendemic.run == False else "Pause Simulation")
        self.doTimestep()

    def doResize(self, event):
        # Do not resize if capturing a user input event but the event does not come from the GUI window
        if event != None and (event.widget != self.window or (self.screenHeight == event.height and self.screenWidth == event.width)):
            return

        if self.resizeID != None:
            self.window.after_cancel(self.resizeID)
        pollingInterval = 10
        self.resizeID = self.window.after(pollingInterval, self.resizeInterface)

    def doStepForwardButton(self, *args):
        if self.trendemic.end == True:
            self.trendemic.endSimulation()
        elif len(self.trendemic.agents) == 0 and self.trendemic.keepAlive == False:
            self.trendemic.toggleEnd()
        else:
            self.trendemic.doTimestep()

    def doTimestep(self):
        if self.stopSimulation == True:
            self.trendemic.toggleEnd()
            return
        if self.activeGraph.get() != "None" and self.widgets["graphButton"].cget("state") != "disabled":
            self.doGraphTimestep()
        else:
            for agent in self.graph:
                fillColor = self.lookupFillColor(agent["agent"])
                if self.activeNetwork.get() == "None" and agent["color"] != fillColor:
                    self.canvas.itemconfig(agent["object"], fill=fillColor, outline="#C0C0C0")
                elif agent["color"] != fillColor:
                    self.canvas.itemconfig(agent["object"], fill=fillColor)
                agent["color"] = fillColor

            if self.activeNetwork.get() != "None":
                self.deleteLines()
                self.drawLines()
            if self.highlightedAgent != None:
                if self.highlightedAgent.isAlive() == True:
                    self.highlightedCell = self.highlightedAgent.cell
                    self.highlightCell(self.highlightedCell)
                else:
                    self.clearHighlight()

        self.updateLabels()
        self.window.update()

    def doWindowClose(self, *args):
        self.stopSimulation = True
        self.window.destroy()
        self.trendemic.toggleEnd()

    def drawLines(self):
        lineCoordinates = set()
        if self.activeNetwork.get() == "Neighbors":
            for agent in self.trendemic.agents:
                for neighbor in agent.neighbors:
                    if neighbor != None and neighbor.isAlive() == True:
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (neighbor.cell.x, neighbor.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Family":
            for agent in self.trendemic.agents:
                family = [agent.socialNetwork["mother"], agent.socialNetwork["father"]] + agent.socialNetwork["children"]
                for familyMember in family:
                    if familyMember != None and familyMember.isAlive() == True:
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (familyMember.cell.x, familyMember.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Friends":
            for agent in self.trendemic.agents:
                for friendRecord in agent.socialNetwork["friends"]:
                    friend = friendRecord["friend"]
                    if friend.isAlive() == True:
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (friend.cell.x, friend.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Trade":
            for agent in self.trendemic.agents:
                for label in agent.socialNetwork:
                    if isinstance(label, str):
                        continue
                    trader = agent.socialNetwork[label]
                    if trader != None and trader["agent"].isAlive() == True and trader["lastSeen"] == self.trendemic.timestep and trader["timesTraded"] > 0:
                        trader = trader["agent"]
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (trader.cell.x, trader.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Loans":
            for agent in self.trendemic.agents:
                # Loan records are always kept on both sides, so only one side is needed
                for loanRecord in agent.socialNetwork["creditors"]:
                    creditor = agent.socialNetwork[loanRecord["creditor"]]["agent"]
                    if creditor.isAlive() == True:
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (creditor.cell.x, creditor.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Disease":
            for agent in self.trendemic.agents:
                if agent.isSick() == True:
                    for diseaseRecord in agent.diseases:
                        # Starting diseases without an infector are not considered
                        if "infector" not in diseaseRecord:
                            continue
                        infector = diseaseRecord["infector"]
                        if infector != None and infector.isAlive() == True:
                            lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (infector.cell.x, infector.cell.y)])
                            lineCoordinates.add(lineEndpointsPair)

        for lineEndpointsPair in lineCoordinates:
            coordList = list(lineEndpointsPair)
            (x1, y1), (x2, y2) = coordList[0], coordList[1]
            x1 = (x1 + 0.5) * self.siteWidth + self.borderEdge
            y1 = (y1 + 0.5) * self.siteHeight + self.borderEdge
            x2 = (x2 + 0.5) * self.siteWidth + self.borderEdge
            y2 = (y2 + 0.5) * self.siteHeight + self.borderEdge
            self.canvas.create_line(x1, y1, x2, y2, fill="black", width="2", tag="line")

    def findClickedCell(self, event):
        # Account for padding in GUI cells
        eventX = event.x - self.borderEdge
        eventY = event.y - self.borderEdge
        gridX = math.floor(eventX / self.siteWidth)
        gridY = math.floor(eventY / self.siteHeight)
        # Handle clicking just outside edge cells
        if gridX < 0:
            gridX = 0
        elif gridX > len(self.trendemic.agents) - 1:
            gridX = len(self.trendemic.agents) - 1
        if gridY < 0:
            gridY = 0
        elif gridY > len(self.trendemic.agents) - 1:
            gridY = len(self.trendemic.agents) - 1
        cell = self.trendemic.environment.findCell(gridX, gridY)
        return cell

    def findColorRange(self, startColor, endColor, minValue, maxValue):
        numColors = maxValue - minValue + 1
        if numColors < 2:
            return {minValue: endColor}

        startRGB = self.hexToInt(startColor)
        endRGB = self.hexToInt(endColor)
        colorRange = {}
        for i in range(numColors):
            factor = i / (numColors - 1)
            interpolatedRGB = self.interpolateColor(startRGB, endRGB, factor)
            colorRange[minValue + i] = self.intToHex(interpolatedRGB)

        return colorRange

    def findSugarAndSpiceColors(self, sugarColor, spiceColor):
        sugarRGB = self.hexToInt(sugarColor)
        spiceRGB = self.hexToInt(spiceColor)
        sugarAndSpiceRGB = self.interpolateColor(sugarRGB, spiceRGB, 0.5)
        whiteRGB = [255, 255, 255]

        maxSugar = self.trendemic.configuration["environmentMaxSugar"]
        maxSpice = self.trendemic.configuration["environmentMaxSpice"]
        colorRange = [[None for spice in range(maxSpice + 1)] for sugar in range(maxSugar + 1)]

        for sugar in range(maxSugar + 1):
            sugarFactor = sugar / maxSugar if maxSugar > 0 else 0
            for spice in range(maxSpice + 1):
                spiceFactor = spice / maxSpice if maxSpice > 0 else 0

                top = self.interpolateColor(whiteRGB, spiceRGB, spiceFactor)
                bottom = self.interpolateColor(sugarRGB, sugarAndSpiceRGB, spiceFactor)
                finalRGB = self.interpolateColor(top, bottom, sugarFactor)
                colorRange[sugar][spice] = self.intToHex(finalRGB)

        return colorRange

    def hexToInt(self, hexval):
        intvals = []
        hexval = hexval.lstrip('#')
        for i in range(0, len(hexval), 2):
            subval = hexval[i:i + 2]
            intvals.append(int(subval, 16))
        return intvals
    
    def highlightCell(self, cell):
        x = cell.x
        y = cell.y
        x1 = self.borderEdge + x * self.siteWidth
        y1 = self.borderEdge + y * self.siteHeight
        x2 = self.borderEdge + (x + 1) * self.siteWidth
        y2 = self.borderEdge + (y + 1) * self.siteHeight

        if self.highlightRectangle != None:
            self.canvas.delete(self.highlightRectangle)
        self.highlightRectangle = self.canvas.create_rectangle(x1, y1, x2, y2, fill="", activefill="#88cafc", outline="black", width=5)

    def interpolateColor(self, startRGB, endRGB, factor):
        return [int((1 - factor) * startValue + factor * endValue)
                for startValue, endValue in zip(startRGB, endRGB)]

    def intToHex(self, intvals):
        hexval = "#"
        for i in intvals:
            subhex = "%0.2X" % i
            hexval = hexval + subhex
        return hexval

    def lookupFillColor(self, agent):
        if self.activeNetwork.get() != "None":
            return self.lookupNetworkColor(cell)
        
        if agent == None:
            return self.palette[2]
        elif agent.influencer:
            return self.colors["influencer"]
        return self.colors["default"]

    def lookupNetworkColor(self, cell):
        agent = cell.agent
        if agent == None:
            return "white"
        elif self.activeNetwork.get() in ["Neighbors", "Friends", "Trade"]:
            return "black"
        elif self.activeNetwork.get() == "Family":
            isChild = agent.socialNetwork["father"] != None or agent.socialNetwork["mother"] != None
            isParent = len(agent.socialNetwork["children"]) > 0
            if isChild == False and isParent == False:
                return "black"
            elif isChild == False and isParent == True:
                return "red"
            elif isChild == True and isParent == False:
                return "green"
            else: # isChild == True and isParent == True
                return "yellow"
        elif self.activeNetwork.get() == "Loans":
            isLender = len(agent.socialNetwork["debtors"]) > 0
            isBorrower = len(agent.socialNetwork["creditors"]) > 0
            if isLender == True:
                return "yellow" if isBorrower == True else "green"
            elif isBorrower == True:
                return "red"
            else:
                return "black"
        elif self.activeNetwork.get() == "Disease":
            return self.colors["sick"] if agent.isSick() == True else self.colors["healthy"]
        return "black"

    def resizeInterface(self):
        self.updateScreenDimensions()
        self.updateSiteDimensions()
        self.destroyCanvas()
        self.configureCanvas()
        if self.activeGraph.get() != "None" and self.widgets["graphButton"].cget("state") != "disabled":
            self.configureGraph()
        else:
            self.configureGraph()

    def updateGraphAxes(self, maxX, maxY):
        xTicks = len(self.graphObjects["xTickLabels"])
        for i in range(1, xTicks + 1):
            self.canvas.itemconfigure(self.graphObjects["xTickLabels"][i / xTicks], text=round(i / xTicks * maxX))
        yTicks = len(self.graphObjects["yTickLabels"])
        for i in range(1, yTicks + 1):
            self.canvas.itemconfigure(self.graphObjects["yTickLabels"][i / yTicks], text=round(i / yTicks * maxY))

    def updateGraphDimensions(self):
        self.window.update_idletasks()
        canvasWidth = self.canvas.winfo_width()
        canvasHeight = self.canvas.winfo_height()
        self.graphStartX = self.graphBorder
        self.graphWidth = max(canvasWidth - 2 * self.graphBorder, 0)
        self.graphStartY = self.graphBorder
        self.graphHeight = max(canvasHeight - 2 * self.graphBorder, 0)

    def updateHighlightedCellStats(self):
        cell = self.highlightedCell
        if cell != None:
            cellSeason = cell.season if cell.season != None else '-'
            cellStats = f"Cell: ({cell.x},{cell.y}) | Sugar: {cell.sugar}/{cell.maxSugar} | Spice: {cell.spice}/{cell.maxSpice} | Pollution: {round(cell.pollution, 2)} | Season: {cellSeason}"
            agent = cell.agent
            if agent != None:
                agentStats = f"Agent: {str(agent)} | Age: {agent.age} | Vision: {round(agent.findVision(), 2)} | Movement: {round(agent.findMovement(), 2)} | "
                agentStats += f"Sugar: {round(agent.sugar, 2)} | Spice: {round(agent.spice, 2)} | "
                agentStats += f"Metabolism: {round(((agent.findSugarMetabolism() + agent.findSpiceMetabolism()) / 2), 2)} | Decision Model: {agent.decisionModel} | Tribe: {agent.tribe}"
            else:
                agentStats = self.defaultAgentString
            cellStats += f"\n{agentStats}"
        else:
            cellStats = f"{self.defaultCellString}\n{self.defaultAgentString}"

        label = self.widgets["cellLabel"]
        label.config(text=cellStats)

    def updateHistogram(self):
        bins = self.graphObjects["bins"]
        labels = self.graphObjects["binLabels"]
        graphStats = {
            "Tag Histogram": (self.trendemic.graphStats["meanTribeTags"], self.trendemic.configuration["agentTagStringLength"]),
            "Age Histogram": (self.trendemic.graphStats["ageBins"], self.trendemic.configuration["agentMaxAge"][1]),
            "Sugar Histogram": (self.trendemic.graphStats["sugarBins"], self.trendemic.graphStats["maxSugar"]),
            "Spice Histogram": (self.trendemic.graphStats["spiceBins"], self.trendemic.graphStats["maxSpice"]),
        }
        activeGraph = self.activeGraph.get()
        binValues = graphStats[activeGraph][0]
        maxX = graphStats[activeGraph][1]
        if len(binValues) == 0:
            maxBinHeight = 0
        elif activeGraph == "Tag Histogram":
            maxBinHeight = 100
        else:
            maxBinHeight = max(binValues)

        if maxBinHeight != 0:
            self.updateGraphAxes(maxX, maxBinHeight)
            for i in range(len(bins)):
                x0, y0, x1, y1 = self.canvas.coords(bins[i])
                y0 = y1 - (binValues[i] / maxBinHeight) * self.graphHeight
                self.canvas.coords(bins[i], x0, y0, x1, y1)
                x2, y2 = self.canvas.coords(labels[i])
                y2 = y0 - 10
                self.canvas.itemconfigure(labels[i], text=round(binValues[i]))
                self.canvas.coords(labels[i], x2, y2)

    def updateLabels(self):
        self.trendemic.updateRuntimeStats()
        stats = self.trendemic.runtimeStats
        statsString = f"Timestep: {self.trendemic.timestep} | Agents: {stats['population']}"
        label = self.widgets["statsLabel"]
        label.config(text=statsString)
        if self.highlightedCell != None:
            self.updateHighlightedCellStats()

    def updateScreenDimensions(self):
        self.window.update_idletasks()
        self.screenWidth = self.window.winfo_width()
        self.screenHeight = self.window.winfo_height()

    def updateSiteDimensions(self):
        self.siteWidth = (self.screenWidth - 2 * self.borderEdge) / len(self.trendemic.agents) / 2
        self.siteHeight = (self.canvas.winfo_height() - 2 * self.borderEdge) / len(self.trendemic.agents) / 2
