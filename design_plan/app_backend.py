# top of server side app
# service layer

from abc import ABC, abstractmethod
from pydantic import BaseModel

class WidgetManager(ABC):
    """
    Ordering of tkinter widgets 
    """
    @abstractmethod
    def create_widgets(self):
        """main function to create widgets"""
        pass

class TkWidgetManager(WidgetManager):
    def create_widgets(self):
        pass

class StreamlitWidgetManager(WidgetManager):
    def create_widgets(self):
        pass

class DataIOManager:
    """
    Manage data input and output
    """
    def perform_analysis(self, specimens: List[Specimen]):
        sample_group = SampleGroup(specimens)
        # Perform analysis on specimens
        # ...
        return analysis_result
    
    def export_sample_group_to_excel(self, specimens: List[Specimen]):
        # Export specimens to Excel
        pass

    def import_sample_group_from_database():
        pass

    def import_sample_group_from_files():
        pass

    def perpare_data_for_export():
        pass

    def prepare_data_for_plotting():
        pass

class GraphicsManager:
    """
    Manage all graphics-related services and operations: 
    """
    def plot_current_specimen(self) -> None:
        # Plot the current specimen
        pass

    def plot_all_specimens(self) -> None:
        # overaly all specimen in the sample group from selected tab
        pass

    def plot_average(self) -> None:
        # average all specimen in the sample group from selected tab
        pass

    def _filter(self):
        # filter specimen based on selected criteria
        pass

    def _set_plotting_parameters(self):
        # set plotting parameters. Interanl vs external plot presentation
        pass


class AppState(BaseModel):
    """
    Contain app states
    """
    specimens: List[SampleGroup] = []
    current_specimen: Optional[Specimen] = None
    selected_specimen_indices: List[int] = []
    export_in_progress: bool = False
    analysis_type: Optional[str] = None  # ISO_1360 or DIN_5122
    analysis_parameters: Optional[dict] = None  # parameters for analysis
    analysis_result: Optional[dict] = None  # result of analysis

    def add_specimen(self, specimen: Specimen):
        self.specimens.append(specimen)

    def select_specimens(self, selected_specimen_indices: List[int]) -> List[SampleGroup]:
        self.selected_specimen_indices = selected_specimen_indices
        return [self.specimens[i] for i in selected_specimen_indices]  # Selecting multiple specimens based on indices

    @property
    def current_specimen(self):
        # Your logic here, for example, you might want to return the first selected specimen
        return self.specimens[self.selected_specimen_indices[0]] if self.selected_specimen_indices else None
    

# app_layer/backends/app_backend.py

class FrontendInterface:
    """Shared interface for all frontends."""
    def load_samples_from_database(self, sample_id: list[int]):
        # Load sample from database
        # ...
        self.app_state.add_specimen(sample)

    def load_samples_from_files(self, file_paths: list[str]):
        # Load sample from files
        # ...
        self.app_state.add_specimen(sample)

class AppBackend(FrontendInterface):
    """
    The main backend class responsible for coordinating the different managers and app state.
    """
    def __init__(self, 
                 widget_manager: Optional[WidgetManager] = None,
                 data_io_manager: Optional[DataIOManager] = None,
                 graphics_manager: Optional[GraphicsManager] = None,
                 app_state: Optional[AppState] = None):
        
        # Initialize managers and state
        self.widget_manager = widget_manager or WidgetManager()
        self.data_io_manager = data_io_manager or DataIOManager()
        self.graphics_manager = graphics_manager or GraphicsManager()
        self.app_state = app_state or AppState()

    @abstractmethod
    def init_ui(self):
        pass

class TkAppBackend(AppBackend):
    """
    The backend specifically tailored for Tkinter.
    """
    def init_ui(self):
        self.widget_manager.create_tkinter_widgets()

class StreamlitAppBackend(AppBackend):
    """
    The backend specifically tailored for Streamlit.
    """
    def init_ui(self):
        self.widget_manager.create_streamlit_widgets()


# app_layer/handlers/action_handler.py
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


# app_layer/controllers/app_controller.py

class AppContorller:
    """
    Orchestrates the flow of the application by coordinating between the frontend and the backend.
    This class takes user input, processes the data via the backend and updates the UI.
    """
    def __init__(self, app_backend: AppBackend, action_handler: ActionHandler):
        self.app_backend = app_backend
        self.action_handler = action_handler

        # initialize other services and state here

    def initialize_app(self):
        """
        Initialize the app. This could involve setting up the UI, loading initial data, etc.
        """
        self.app_backend.init_ui()

    def run(self):
        """
        Main loop for running the application. 
        In a GUI this might be your main event loop.
        """
        pass

    def load_specimen(self, specimen_id: int):
        """
        Load a specimen given its ID and update the frontend.
         High-level method to load a specimen.
        """
        self.app_backend.load_specimen(specimen_id)






"""
project_root/
│
├── data_layer/                            # Core data management and manipulation
│   ├── __init__.py
│   ├── models/                            # Data models and structures
│   │   ├── analyzable_entity.py           # Base class for all analyzable entities
│   │   ├── specimen.py                    # Individual specimen model
│   │   ├── specimen_DB.py                 # Database operations specific to specimen
│   │   └── sample_group.py                # Model for grouping specimens
│   ├── metrics/                           # Metrics computation related to specimens
│   |    └── specimen_metrics.py
│   └── IO/                               # Input/Output operations
|      ├── repositories/                  # Storage and retrieval of data
|      │   ├── base_repository.py         # Base class for database repository operations
|      │   └── specimen_repository.py     # Specimen-specific database operations
|      ├── specimenIO.py                  # IO operations specific to specimens
|      ├── cross_section_manager.py       # Manage cross-sectional data and operations
|      ├── word/                          # Word document-related operations
|      │   └── word_exporter.py
|      └── excel/                         # Excel operations
|            └── excel_exporter.py
│
├── service_layer/                         # Business logic and operations
│   ├── __init__.py
│   ├── service_layer.py                   # ServiceLayer class that aggregates all services
│   ├── analysis/                          # Data analysis methods and protocols
│   │   ├── specimen_analysis_protocol.py  # Analysis specific to specimens
│   │   └── sample_group_analysis_protocol.py # Analysis for groups of specimens
│   ├── plotting/                          # Graph plotting and visualization
│   │   ├── specimen_graph_manager.py      # Manage specimen-specific graphs
│   │   ├── sample_group_graph_manager.py  # Manage group-specific graphs
│   │   ├── control_chart.py               # Generate control charts for data
│   │   └── control_process_metrics.py     # Metrics for control process charts
│   ├── operations/                        # Aggregate operations
│   │   ├── specimen_operations.py         # Specimen-specific operations
│   │   └── sample_group_operations.py     # Group-specific operations
│   └── sample_group_facade.py             # A simplified interface for complex operations on SampleGroups
│
├── app_layer/                             # Application UI and event handling
│   ├── __init__.py
│   ├── frontends/                         # Different frontend interfaces
│   │   ├── tk_frontend.py                 # Tkinter frontend
│   │   └── web_frontend.py                # Web frontend (Streamlit or Flask)
│   ├── controllers/                       # Direct and manage app flow
│   │   └── app_controller.py
│   ├── handlers/                          # Respond to user interactions/events
│   │   └── action_handler.py
│   ├── managers/                          # Manage UI components and their interactions
│   │   ├── widget_manager.py              # Manage widget order and display
│   │   ├── data_io_manager.py             # Handle data inputs/outputs in the app
│   │   └── graphics_manager.py            # Manage graphical displays and visualizations
│   ├── app_state.py                       # Holds the current state of the application
│   └── app_backend.py                     # Backend logic for the application, and potential UI if using frameworks like Tkinter
│
├── utils/
│   ├── __init__.py
|
├── config/                                # Configuration files
│
├── tests/                                 # Test suites and test cases | mirror the structure of the main application
│
├── static/                                # Static files like CSS, JS, images, etc. (if needed)
│   
├── data/                                  # Raw data, database files, etc.
│   └── database/                          # Database files and related assets
│
└── docs/                                  # Documentation and related materials
    ├── design/                            # Design documents
    └── README.md                          # Project README

"""

# main.py 

import argparse

# Import your classes and services
from app_layer.controllers.app_controller import AppController
from app_layer.action_handler import ActionHandler
from app_layer.managers.tk_widget_manager import TkWidgetManager
from app_layer.managers.streamlit_widget_manager import StreamlitWidgetManager
from app_layer.app_state import AppState
from app_layer.app_backend import AppBackend, TkAppBackend, StreamlitAppBackend
from service_layer.your_service_layer import YourServiceLayer  # Replace with your actual service layer

def main():
    parser = argparse.ArgumentParser(description="Launch the app with a specific frontend.")
    parser.add_argument("--frontend", type=str, choices=["tkinter", "streamlit"], default="tkinter",
                        help="Choose the frontend to use for the app.")
    args = parser.parse_args()

    # Initialize service layer and handlers
    service_layer = YourServiceLayer()  # Replace with your actual service layer
    action_handler = ActionHandler(service_layer)

    # Initialize app state
    app_state = AppState()

    # Create the appropriate widget manager based on the frontend choice
    if args.frontend == "tkinter":
        widget_manager = TkWidgetManager()
        app_backend = TkAppBackend(widget_manager, ..., app_state)  # Fill in the ...
        app_controller = AppController(app_backend)
        app_controller.run()  # or however you start your Tkinter loop
    elif args.frontend == "streamlit":
        widget_manager = StreamlitWidgetManager()
        app_backend = StreamlitAppBackend(widget_manager, ..., app_state)  # Fill in the ...
        app_controller = AppController(app_backend)
        app_controller.run_streamlit()  # or however you start your Streamlit app

if __name__ == "__main__":
    main()
