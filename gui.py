import math
import tkinter

REPULSIVE_FORCE = 10
ATTRACTIVE_FORCE = 0.00003

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
        self.showLoadingScreen()
        i = 1
        j = 1
        # Setup initial radial dispersion of nodes for force-directed layout
        for agent in self.trendemic.agents:
            stepX = math.cos(((2 * math.pi) * (360 / i)) / len(self.trendemic.agents))
            stepY = math.sin(((2 * math.pi) * (360 / i)) / len(self.trendemic.agents))
            fillColor = self.lookupFillColor(agent)
            x = stepX * self.siteWidth * 5 + (self.screenWidth / 2)
            y = stepY * self.siteHeight * 5 + (self.screenHeight / 2)
            self.nodes[agent.ID] = { "agent": agent, "x": x, "y": y, "deltaX": 0, "deltaY": 0,"color": fillColor}
            i += 1
            j += 1
        
        self.doForceDirectedLayout()

        for node in self.nodes:
            x = node["x"]
            y = node["y"]
            x1 = x
            y1 = y
            x2 = x + self.siteWidth
            y2 = y + self.siteHeight
            node["object"] = self.canvas.create_oval(x1, y1, x2, y2, fill=node["color"], outline="#c0c0c0", activestipple="gray50")
        self.hideLoadingScreen()
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
        self.delayGraphSetup()

        self.window.protocol("WM_DELETE_WINDOW", self.doWindowClose)
        self.window.bind("<Escape>", self.doWindowClose)
        self.window.bind("<space>", self.doPlayButton)
        self.window.bind("<Right>", self.doStepForwardButton)
        self.window.bind("<Configure>", self.doResize)

        self.doCrossPlatformWindowSizing()

    def delayGraphSetup(self):
        self.window.after(20, self.configureGraph)  

    def destroyCanvas(self):
        self.canvas.destroy()

    def doAttraction(self):
        traversed = []
        attractiveForce = ATTRACTIVE_FORCE
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
                (aX, aY) = self.findMidpoint(source)
                (bX, bY) = self.findMidpoint(sink)
                dX = bX - aX
                dY = bY - aY
                attraction = attractiveForce * (math.sqrt((dX**2) + (dY**2)))
                theta = math.atan2((bY - aY), (bX - aX))
                attractionA = ((attraction * math.cos(theta)), (attraction * math.sin(theta)))
                attractionB = (((-1 * attraction) * math.cos(theta)), ((-1 * attraction) * math.sin(theta)))
                source["deltaX"] += attractionA[0]
                source["deltaY"] += attractionA[1]
                sink["deltaX"] += attractionB[0]
                sink["deltaY"] += attractionB[1]
            traversed.append(source)
        for node in self.nodes:
            damping = 0.88
            maxStep = 5
            node["x"] += max(min(node["deltaX"] * damping, maxStep), -maxStep)
            node["y"] += max(min(node["deltaY"] * damping, maxStep), -maxStep)

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
    
    def doForceDirectedLayout(self, steps=50):
        for i in range(steps):
            self.doRepulsion()
            self.doAttraction()

    def doPlayButton(self, *args):
        self.trendemic.toggleRun()
        self.widgets["playButton"].config(text="Play Simulation" if self.trendemic.run == False else "Pause Simulation")
        self.doTimestep()

    def doRepulsion(self):
        traversed = []
        repulsiveForce = REPULSIVE_FORCE

        # Set initial values for node's delta values
        for node in self.nodes:
            node["deltaX"] = 0
            node["deltaY"] = 0

        for source in self.nodes:
            for sink in self.nodes:
                if source in traversed:
                    continue
                (aX, aY) = self.findMidpoint(source)
                (bX, bY) = self.findMidpoint(sink)
                dX = bX - aX
                dY = bY - aY
                repulsionDenominator = math.sqrt(dX**2 + dY**2)
                # Prevent incredibly small denominators
                if repulsionDenominator < 0.01:
                    repulsionDenominator = 0.01
                repulsion = repulsiveForce / repulsionDenominator
                theta = math.atan2(dY, dX)
                repulsionA = (((-1 * repulsion) * math.cos(theta)), ((-1 * repulsion) * math.sin(theta)))
                repulsionB = ((repulsion * math.cos(theta)), (repulsion * math.sin(theta)))
                source["deltaX"] += repulsionA[0]
                source["deltaY"] += repulsionA[1]
                sink["deltaX"] += repulsionB[0]
                sink["deltaY"] += repulsionB[1]
            traversed.append(source)
        for node in self.nodes:
            damping = 0.88
            maxStep = 5
            node["x"] += max(min(node["deltaX"] * damping, maxStep), -maxStep)
            node["y"] += max(min(node["deltaY"] * damping, maxStep), -maxStep)

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
        self.window.update()

    def doWindowClose(self, *args):
        self.stopSimulation = True
        self.window.destroy()
        self.trendemic.toggleEnd()

    def drawEdges(self):
        for edge in self.edges:
            self.canvas.delete(edge)
        for agent in self.trendemic.agents:
            agentNode = self.nodes[agent.ID]
            agentMidpoint = self.findMidpoint(agentNode)
            agentX = agentMidpoint[0]
            agentY = agentMidpoint[1]
            for n in range(len(agent.neighbors)):
                neighborNode = self.nodes[n]
                neighborMidpoint = self.findMidpoint(neighborNode)
                neighborX = neighborMidpoint[0]
                neighborY = neighborMidpoint[1]
                edge = self.canvas.create_line(agentX, agentY, neighborX, neighborY, fill="black", width="2")
                self.edges.append(edge)

    def findMidpoint(self, node):
        x = node["x"]
        y = node["y"]
        width = self.siteWidth
        height = self.siteHeight
        midpointX = x + (width / 2)
        midpointY = y + (height / 2)
        return (midpointX, midpointY)

    def hideLoadingScreen(self):
        self.loadingLabel.destroy()
        self.canvas.grid()  
        self.window.update_idletasks()

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
    
    def showLoadingScreen(self):
        self.loadingLabel = tkinter.Label(self.window, text="Loading...", font=("Roboto", 14))
        self.loadingLabel.grid(row=3, column=0, columnspan=self.menuTrayColumns, sticky="nsew")
        self.canvas.grid_remove() 
        self.window.update_idletasks()

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
