# app/app_layer/action_handler.py


class ActionHandler:
    """
    Handler for managing user-triggered actions and communicating with the service layer.
    Facade of service layer that contains the high-level methods that act upon user interactions to execute business logic.
   
    Attributes:
        service_layer (ServiceLayer): The business logic or data manipulation layer.
        Services: GraphManager, DataIOManager, ExcelExporter
    """
    def __init__(self, service_layer):
        self.service_layer = service_layer

    def plot_specimen_graph(self, specimen):
        self.service_layer.specimen_graph_manager.plot(specimen)
