import math
import tkinter

class GUI:
    def __init__(self, trendemic, screenHeight=1000, screenWidth=900):
        self.trendemic = trendemic
        self.screenHeight = screenHeight
        self.screenWidth = screenWidth
        self.canvas = None
        self.nodes = [None for i in range(len(self.trendemic.agents))]
        self.edges = []
        self.window = None
        self.doubleClick = False
        self.resizeID = None

        self.palette = ["#FA3232", "#3232FA", "#32FA32", "#32FAFA", "#FA32FA", "#AA3232", "#3232AA", "#32AA32", "#32AAAA", "#AA32AA", "#FA8800", "#00FA88", "#8800FA", "#FA8888", "#8888FA", "#88FA88", "#FA3288", "#3288FA", "#88FA32", "#AA66AA", "#66AAAA", "#3ED06E", "#6E3ED0", "#D06E3E", "#000000"]
        self.colors = {"default": self.palette[0], "influencer": self.palette[1], "influenced": self.palette[2]}

        # Set the default strings for interface at simulation start
        self.defaultSimulationString = "Timestep: - | Agents: -"

        self.widgets = {}
        self.borderEdge = 5
        self.graphBorder = 90
        self.menuTrayColumns = 3
        self.siteHeight = 0
        self.siteWidth = 0
        self.stopSimulation = False
        self.configureWindow()

    def configureButtons(self, window):
        playButton = tkinter.Button(window, text="Play Simulation", command=self.doPlayButton)
        playButton.grid(row=0, column=0, sticky="nsew")
        stepButton = tkinter.Button(window, text="Step Forward", command=self.doStepForwardButton, relief=tkinter.RAISED)
        stepButton.grid(row=0, column=1, sticky="nsew")

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
        editingButton.grid(row=0, column=2, sticky="nsew")

        statsLabel = tkinter.Label(window, text=self.defaultSimulationString, font="Roboto 10", justify=tkinter.CENTER)
        statsLabel.grid(row=1, column=0, columnspan=self.menuTrayColumns, sticky="nsew")
        self.widgets["playButton"] = playButton
        self.widgets["stepButton"] = stepButton
        self.widgets["editingButton"] = editingButton
        self.widgets["statsLabel"] = statsLabel

    def configureCanvas(self):
        canvas = tkinter.Canvas(self.window, background="white")
        canvas.grid(row=3, column=0, columnspan=self.menuTrayColumns, sticky="nsew")
        self.canvas = canvas

    def configureEditingModes(self):
        return ["Add Agent"]

    def configureGraph(self):
        i = 1
        j = 1
        # Setup initial radial dispersion of nodes for force-directed layout
        for agent in self.trendemic.agents:
            stepX = math.cos(((2 * math.pi) * (360 / i)) / len(self.trendemic.agents))
            stepY = math.sin(((2 * math.pi) * (360 / i)) / len(self.trendemic.agents))
            fillColor = self.lookupFillColor(agent)
            x1 = stepX * self.siteWidth + 100 + (self.screenWidth / 4)
            y1 = stepY * self.siteHeight + 100 + (self.screenHeight / 4)
            x2 = x1 + self.siteWidth
            y2 = y1 + self.siteHeight
            self.nodes[agent.ID] = {"object": self.canvas.create_oval(x1, y1, x2, y2, fill=fillColor, outline="#c0c0c0", activestipple="gray50"), "agent": agent, "color": fillColor}
            i += 1
            j += 1
        self.doRepulsion()
        self.doAttraction()
        self.drawEdges()

    def configureGraphNames(self):
        return ["TODO"]

    def configureNetworkNames(self):
        return ["TODO"]

    def configureWindow(self):
        window = tkinter.Tk()
        self.window = window
        window.title("Trendemic")
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

    def destroyCanvas(self):
        self.canvas.destroy()

    def doAttraction(self):
        traversed = []
        attractiveForce = 0.005
        for source in self.nodes:
            for sink in self.nodes:
                if source in traversed:
                    continue
                neighbors = source["agent"].neighbors
                sinkAgent = None
                for neighbor in neighbors:
                    if neighbor == sink["agent"]:
                        sinkAgent = sink["agent"]
                        break
                if sinkAgent == None:
                    continue
                a = self.findMidpoint(source["object"])
                b = self.findMidpoint(sink["object"])
                aX = a[0]
                aY = a[1]
                bX = b[0]
                bY = b[1]
                attraction = attractiveForce * (((bX - aX)**2) + ((bY - aY)**2))
                theta = math.atan((bY - aY) / (bX - aX)) if (bX - aX) > 0 else 0
                attractionA = ((attraction * math.cos(theta)), (attraction * math.sin(theta)))
                attractionB = (((-1 * attraction) * math.cos(theta)), ((-1 * attraction) * math.sin(theta)))
                source["deltaX"] = attractionA[0]
                source["deltaY"] = attractionA[1]
                sink["deltaX"] = attractionB[0]
                sink["deltaY"] = attractionB[1]
            traversed.append(source)
        self.drawGraph()

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

    def doPlayButton(self, *args):
        self.trendemic.toggleRun()
        self.widgets["playButton"].config(text="Play Simulation" if self.trendemic.run == False else "Pause Simulation")
        self.doTimestep()

    def doRepulsion(self):
        traversed = []
        repulsiveForce = 0.005
        for source in self.nodes:
            for sink in self.nodes:
                if source in traversed:
                    continue
                a = self.findMidpoint(source["object"])
                b = self.findMidpoint(sink["object"])
                aX = a[0]
                aY = a[1]
                bX = b[0]
                bY = b[1]
                repulsionDenominator = math.sqrt(((bX - aX)**2) + ((bY - aY)**2))
                repulsion = repulsiveForce / repulsionDenominator if repulsionDenominator > 0 else 0
                theta = math.atan((bY - aY) / (bX - aX)) if (bX - aX) > 0 else 0
                repulsionA = (((-1 * repulsion) * math.cos(theta)), ((-1 * repulsion) * math.sin(theta)))
                repulsionB = ((repulsion * math.cos(theta)), (repulsion * math.sin(theta)))
                source["deltaX"] = repulsionA[0]
                source["deltaY"] = repulsionA[1]
                sink["deltaX"] = repulsionB[0]
                sink["deltaY"] = repulsionB[1]
            traversed.append(source)
        self.drawGraph()

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
        for agent in self.nodes:
            fillColor = self.lookupFillColor(agent["agent"])
            if agent["color"] != fillColor:
                self.canvas.itemconfig(agent["object"], fill=fillColor)
            agent["color"] = fillColor
        self.updateLabels()
        self.doRepulsion()
        self.doAttraction()
        self.window.update()

    def doWindowClose(self, *args):
        self.stopSimulation = True
        self.window.destroy()
        self.trendemic.toggleEnd()

    def drawEdges(self):
        for edge in self.edges:
            self.canvas.delete(edge)
        for agent in self.trendemic.agents:
            agentNode = self.nodes[agent.ID]["object"]
            agentMidpoint = self.findMidpoint(agentNode)
            agentX = agentMidpoint[0]
            agentY = agentMidpoint[1]
            for n in range(len(agent.neighbors)):
                neighborNode = self.nodes[n]["object"]
                neighborMidpoint = self.findMidpoint(neighborNode)
                neighborX = neighborMidpoint[0]
                neighborY = neighborMidpoint[1]
                edge = self.canvas.create_line(agentX, agentY, neighborX, neighborY, fill="black", width="2")
                self.edges.append(edge)

    def drawGraph(self):
        for node in self.nodes:
            deltaX = node["deltaX"] if "deltaX" in node else 0
            deltaY = node["deltaY"] if "deltaY" in node else 0
            nodeObject = node["object"]
            nodeMidpoint = self.findMidpoint(nodeObject)
            nodeX = nodeMidpoint[0]
            nodeY = nodeMidpoint[1]
            stepX = nodeX + deltaX
            stepY = nodeY + deltaY
            fillColor = self.lookupFillColor(node["agent"])
            x1 = stepX
            y1 = stepY
            x2 = x1 + self.siteWidth
            y2 = y1 + self.siteHeight
            self.canvas.coords(nodeObject, x1, y1, x2, y2)
        self.drawEdges()

    def findMidpoint(self, canvasObject):
        coords = self.canvas.coords(canvasObject)
        height = coords[1] - coords[3]
        width = coords[2] - coords[0]
        x = coords[0]
        y = coords[1]
        midpointX = x + (width / 2)
        midpointY = y - (height / 2)
        return (midpointX, midpointY)

    def lookupFillColor(self, agent):
        if agent == None:
            return "black"
        elif agent.influencer:
            return self.colors["influencer"]
        elif agent.influenced:
            return self.colors["influenced"]
        return self.colors["default"]

    def resizeInterface(self):
        self.updateScreenDimensions()
        self.updateSiteDimensions()
        self.destroyCanvas()
        self.configureCanvas()
        self.configureGraph()

    def updateLabels(self):
        self.trendemic.updateRuntimeStats()
        stats = self.trendemic.runtimeStats
        statsString = f"Timestep: {self.trendemic.timestep} | Agents: {stats['population']}"
        label = self.widgets["statsLabel"]
        label.config(text=statsString)

    def updateScreenDimensions(self):
        self.window.update_idletasks()
        self.screenWidth = self.window.winfo_width()
        self.screenHeight = self.window.winfo_height()

    def updateSiteDimensions(self):
        self.siteWidth = (self.screenWidth - 2 * self.borderEdge) / len(self.trendemic.agents) / 2
        self.siteHeight = (self.canvas.winfo_height() - 2 * self.borderEdge) / len(self.trendemic.agents) / 2
