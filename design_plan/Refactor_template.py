# Refactoring template specimen model
"""
This scrpit is a template for refactoring the specimen model.
As it will requrie a holtics approach to refactor the specimen model.
This scripit will contain a rough outline of the proposed architecture and design of the specimen model.

"""

from pydantic import BaseModel, validator
import numpy as np
from typing import List
import pandas as pd
import numpy as np
from pint import UnitRegistry

## Domain Layer ##

# ------- DTO Layer --------

ureg = UnitRegistry()

class SpecimenDTO(BaseModel):
    force: np.ndarray
    displacement: np.ndarray
    stress: np.ndarray = None
    strain: np.ndarray = None
    unit: str = "pascal"
    
    # Add validators if necessary
    @validator('force', pre=True, always=True)
    def validate_force(cls, v):
        # Placeholder validation
        return v

    # ... Additional validators

    @property
    def stress_with_unit(self):
        return self.stress * ureg(self.unit)

    @property
    def strain_with_unit(self):
        return self.strain * ureg(self.unit)
    
    @classmethod
    def from_raw_data(cls, raw_data, data_formater: SpecimenIO):
        # Logic to create DTO from raw database or storage data

class SpecimenFromDB(SpecimenDTO):
    db_id: int
    # Any other database-specific fields

    # Add validators if necessary

"""
    Data Access

    This layer deals with persistent storage, such as databases or files.

    - SpecimenIO Data Importer/Formatter: Import data from files or other sources
    - SpecimenCrossSection: Manage cross-section images of specimens.
    
    Optional:
        -  Repository Classes: Handle CRUD operations 
        -  ORM Models: Database models 
        -  DB Session Management: Handle database sessions 

"""
class SpecimenIO:
    

# ------- Database Layer (Optional) --------

class SpecimenRepository:

    @staticmethod
    def save_to_db(specimen: SpecimenFromDB()):
        # Placeholder database save operation
        pass

    @staticmethod
    def fetch_from_db(db_id: int) -> SpecimenFromDB():
        # Placeholder database fetch operation
        return SpecimenFromDB()()

"""
    Business Logic

    This layer contains the core logic and computations of your application.

    Speciemn logic: Analysis and computations for single sample

        - SpecimenOperations: Responsible for performing calculations on specimens.
        - SpecimenFactory: Factory to determine specimen creation based on analysis type or program model. Encapsulates the logic for specimen instantiation.
        - SpecimenGraphicsService: Responsible for managing graphics-related operations for specimens.

    Specimen Group (SKU): Analysis and computations for a group of specimens

        - SKUOperations: Operations to handle groups like merging datapoints and basic statistics.
        - Control Chart: Operations to handle control chart computations and plotting.
        - SKUGraphics. Graphical representation of specimen groups
        - SKUFormatter: For formatting specimen data into desired structures such as dataframes.

        - Excel Exporters: for SKU / Group of specimens
            -> ExcelSheet DTO: Represents a single sheet's data and structure.
            -> ExcelFormatter (operation): Class to handle formatting for Excel sheets.
            -> ExcelExportService: A service class responsible for generating and saving Excel sheets.

"""
# ------- Operations Layer --------


class SpecimenOperations:

    @staticmethod
    def calculate_stress(specimen: SpecimenDTO) -> np.ndarray:
        # Calculate stress from the specimen's force and other attributes
        # Placeholder operation
        return specimen.force

    @staticmethod
    def calculate_strain(specimen: SpecimenDTO) -> np.ndarray:
        # Calculate strain from the specimen's displacement and other attributes
        # Placeholder operation
        return specimen.displacement

    # ... Additional methods

"""
    Service Layer

    Serves as an interface to the DTO and Operations layers. It will guide the workflow, ensuring data integrity and proper sequence of operations.
    
    - PlotManager (renamed as GraphicsManager): Manage all graphics-related services and operations:  sub-services can be SpecimenGraphicsService and SKUGraphicsService
    - GraphicsControlInterface: Interface for controlling graphics.
    - SpecimenModifierInterface: Interface for modifying specimen details.
    - ButtonActions (or renamed as ActionHandlers) user-initiated actions are received and the appropriate business logic or service is called. However, the actual business logic should reside in the BLL.
    - DataHandler(or renamed as DataIOManager): Manage all data-related services and operations: sub-services can be SpecimenIO and SKUManager
"""

class SpecimenService:

    @staticmethod
    def add_stress_and_strain(specimen: SpecimenDTO):
        # Check and calculate if stress or strain are not present
        if not specimen.stress:
            specimen.stress = SpecimenOperations.calculate_stress(specimen)
        if not specimen.strain:
            specimen.strain = SpecimenOperations.calculate_strain(specimen)
        # ... Additional service methods

# ------- Controller Layer --------

class SpecimenController:
    pass


"""
    Application Backend

    - AppVariables (or renamed to AppState): Manage the state of the application.Keep track on specimen analysis type.
    - Facade claess :Simplify using business logic class and Service class

"""

class AppVariables:
    def __init__(self):
        self.specimens = []
        self.average_of_specimens = None
        self.average_of_specimens_hysteresis = pd.DataFrame()
        self.avg_pleatue_stress = None 
        self.selected_indices = None
        self.selected_specimen_names = []
        self.current_specimen = None
        self.current_slider_manager = None
        # Map tab identifiers to tuples (specimen, slider_manager)
        self.notebook_to_data = {}
        self.export_in_progress = False
        self.preliminary_sample = False
        self.prelim_mode = tk.BooleanVar(value=self.preliminary_sample)
        self.DIN_Mode = True
        self.ISO_Mode = False

    @classmethod
    def load_from_database(cls, id):
        specimen = SpecimenRepository().get(id)
        cls.current_specimens.append(specimen)

    @classmethod
    def save_to_database(cls, specimen_dto: SpecimenDTO):
        SpecimenRepository().save(specimen_dto)
    
    @classmethod
    def load_from_program_zip_file(cls, path):
        pass

    @classmethod
    def save_to_program_zip_file(cls, path):
        pass

# ------- Facade Layer --------
class SpecimenFacade:
    def __init__(self):
        self.repository = SpecimenRepository()
        self.service = SpecimenService(self.repository)
        self.controller = SpecimenController(self.service)

    def display_average_stress(self):
        return self.controller.get_average_stress()

    def load_specimen_from_db(self, id):
        AppVariables.load_from_database(id)

    def save_specimen_to_db(self, specimen_dto: SpecimenDTO):
        AppVariables.save_to_database(specimen_dto)


"""
    Application UI
    
    - Currenlty Tkiner with tkinterbootstrap theme  
    - WidgetManager: Manages all the widgets of the application.
    - AppConfiguration: Configuration for the UI.
"""


class StressStrainApp:
    pass

class UI:
    def __init__(self, controller):
        self.controller = controller
