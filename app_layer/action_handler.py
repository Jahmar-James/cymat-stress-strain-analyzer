# app/app_layer/action_handler.py


class ActionHandler:
    """
    Backend functions called from AppController, contains business logic.
    Contains the high-level methods that act upon user interactions to execute business logic.
    """
    def __init__(self, service_layer):
        self.service_layer = service_layer
    
    def perform_analysis(self, specimen):
        self.service_layer.specimen_analysis.analyze(specimen)

    def plot_specimen_graph(self, specimen):
        self.service_layer.specimen_graph_manager.plot(specimen)
