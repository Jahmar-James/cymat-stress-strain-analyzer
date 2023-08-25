# top of server side app
# service layer

class AppContorller:
    """
    Conduct the app 
    """

class ActionHandler:
    """
    Backend functions called from front end / user interactions
    """

class WidgetManager:
    """
    Ordering of tkinter widgets 
    """

class DataIOManager:
    """
    Manage data input and output
    """

class GraphicsManager:
    """
    Manage all graphics-related services and operations:  sub-services can be SpecimenGraphicsService and SKUGraphicsService
    """

class AppState:
    """
    Contain app states
    """

class AppBackend:
    """
    Currently tkinter so also UI
    """

"""
project_root/
│
├── data_layer/                            # Core data management and manipulation
│   ├── __init__.py
│   ├── models/                            # Data models and structures
│   │   ├── analyzable_entity.py            # Base class for all analyzable entities
│   │   ├── specimen.py                    # Individual specimen model
│   │   ├── specimen_DB.py                 # Database operations specific to specimen
│   │   └── sample_group.py                # Model for grouping specimens
│   ├── metrics/                           # Metrics computation related to specimens
│   |    └── specimen_metrics.py
│   └── IO/                                # Input/Output operations
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