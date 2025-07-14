class Behavior:
    def __init__(self, configuration, trendemic):
        self.configuration = configuration
        self.trendemic = trendemic

        #k=6, p=0.1, m=3, local_weight=1.0, global_weight=0.0, heterogeneous_thresholds=False, threshold_distribution="uniform",
        #social_engineer_enabled=False, seeding_strategy=None, social_engineer_count=5

    def __str__(self):
        return f"{self.configuration}"
