class Behavior:
    def __init__(self, configuration, trendemic):
        self.configuration = configuration
        self.trendemic = trendemic

    def __str__(self):
        return f"{self.configuration}"
