# Playgound to Refactor plan of sample class
from abc import ABC, abstractmethod


class AnalyzableEntity(ABC):
    """
    Base class for Mechanical Testing sample objects that require data processing and plotting.
    Examples: A single Sample or a Collection of Samples.

    Responsibilities:
    1. **Hold Generic Operations**:
        - Provide methods such as unit conversion, calculating stress, strain, energy absorptivity, etc.
    2. **Define a Common Interface**:
        - Each subclass should define how key properties and methods are accessed and used.
        - For example, `SampleGeneric` must implement `_Strength` as part of the `AnalyzableEntity` interface.

    Abstract Methods:
    - Define methods that subclasses must implement, such as plotting or data extraction.
    """

    def __init__(self):
        raise NotImplementedError("This is an abstract base class and cannot be instantiated directly.")

    # Common Operations

    def plot_stress_strain(self) -> None:
        """
        Plot the stress-strain curve for a sample.
        Can be used to provide an automated view of the data, potentially overlayed with other samples.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def plot_force_displacement(self) -> None:
        """
        Plot the force-displacement curve for a sample.
        Can be used to provide an automated view of the data, potentially overlayed with other samples.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    # Interface - Abstract Methods

    @abstractmethod
    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        pass


class SampleGeneric(AnalyzableEntity):
    """
    Default implementation for a single mechanical testing sample.
    Variations of this class will be created based on the analysis standard.
    - This class can be returned from a factory method based on the standard.

    Responsibilities:
    - Handle validation to ensure the sample data meets the requirements for this class.
    - Calculate specific metrics relevant to the sample.
    - Manage persistent storage (e.g., saving data as files or in a database).
    """

    def __init__(self):
        self.standard = "Generic"  # to be Enum
        # Validator to ensure the data meets the requirements to create this sample.
        # The validator will have a base class, as each standard has its own requirements.
        self.validator = None

        # Operator to calculate sample-specific metrics.
        # The operator will also have a base class to share generic operations (e.g., stress, strain).
        self.operator = None

        # IOManager to manage persistent storage, saving data either as files or into a database.
        # This will not have a base class since varing metrics will be save in an object (e.g., JSON for custom metrics).
        self.io_manager = None

    def create_entity(self) -> bool:
        """
        Factory method to create an instance of the entity (sample) after validation.
        This method will use the validator and operator to prepare the sample.
        """
        pass


# VisualizationSample
# CymatISO133142011Sample


class SampleGenericGroup(AnalyzableEntity):
    """
    A collection of mechanical testing samples.
    This class handles operations and calculations that apply to groups of samples, such as averaging properties.

    Responsibilities:
    - Validate that all samples in the group have compatible properties (e.g., so that average properties can be calculated).
    """

    def __init__(self):
        # Validator to ensure that all samples have the necessary properties to form a group.
        # For example, checks might ensure that samples can be averaged together.
        self.validator = None
        self.io_manger = None

    def create_entity(self):
        """
        Method to create a group of samples after validation.
        Can perform calculations such as averaging key properties across the group.
        """
        pass


class PlotManager:
    """
    Manages plotting and visualization for the entities (samples or sample groups).
    This class provides more control and customization for users who need to go beyond the automated plots.

    Responsibilities:
    - Access the entity data directly for plotting.
    - Allow greater customization of plot styles and content compared to the automated plots provided by `AnalyzableEntity`.
    """

    def __init__(self):
        pass

    def plot_custom(self, entity: AnalyzableEntity):
        """
        Provide a customizable plot for a specific entity (either a single sample or a group of samples).
        This method will allow users to specify plot parameters and customize the visualization.
        """
        pass


# Folder Structure
"""
FRONTEND
main.py
/tkinter_frontend
    /core
    /top_level_create_sample
     - __init__.py
     -settings_top_level_create_sample.py
    /top_level_create_sample_group
    /top_level_plotting

BACKEND
/data_extraction -  Different formats of data fomart and styles
    - __init__.py
    - mechanical_test_data_preprocessor.py
    /Cleaners
        - __init__.py
        - default_data_cleaner.py
        - MTS_data_cleaner_2020.py
        - Element_data_cleaner.py
/stadards
    - __init__.py
    - sample_factory.py
    - sample_processor.py
    /bases
        - __init__.py
        - analyzable_entity.py
        - base_standard_validator.py
        - base_standard_operator.py
        - base_standard_io_manager.py 
        - base_standard_group_io_manager.py
    /default_sample
        - __init__.py
        - sample.py
        - sample_group.py
        - validator.py
        - operator.py
    /visualizations_sample
    /iso_13314_2011
        - __init__.py
        - sample.py
        - sample_group.py
        - validator.py
        - operator.py
/Visualization
    - plotting_manager.py         
    - plot_data_helpers.py  
/config
    - __init__.py
    /app_settings
    /workflow_settings
/tests
"""
