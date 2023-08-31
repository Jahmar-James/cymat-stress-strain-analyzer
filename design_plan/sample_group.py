
from specimen_new import Specimen, SpecimenFromDB, SpecimenRepository, SpecimenIO, SpecimenDataManager, SpecimenPropertiesDTO, SpecimenMetricsDTO, SpecimenGraphManager, SpecimenAnalysisProtocol
from analyzable_entity import AnalyzableEntity
from pint import UnitRegistry
import numpy as np
from process_control import ControlChart, ControlProcessMetrics
from pydantic import BaseModel
from typing_extensions import Protocol
from bases import BaseRepository, ExcelExporter

class SampleGroupCharacteristics(BaseModel):
    """"""
    analysis_type: str
    strength: float

class SampleGroup(AnalyzableEntity):
    """The main class that holds a collection of Specimen objects. Methods might include adding/removing specimens, iterating over specimens, and so on."""
    def __init__(self, characteristics: SampleGroupCharacteristics = None, data_manager = None, graph_manager = None ):
        self.specimens = []
        self.type = None
        self.characteristics = characteristics
        self.data_manager = data_manager or  SampleGroupDataManager()
        self.graph_manager = graph_manager or SampleGroupGraphManager()
        self.stress = None
        self.strain = None

    def __iter__(self):
        for specimen in self.specimens:
            yield specimen

    def __repr__(self) -> str:
        pass

    def add_specimen(self, specimen: Specimen):
        if self.type:
            # Check if specimen adheres to the SampleGroupCharacteristics'
            if specimen.metrics.analysis_type == self.type:
                self.specimens.append(specimen)
            else:
                print("Please add a specimen of the same type as the sample group or remove all samples from bin and start over.")
        elif len(self.specimens) == 1:
            self.type = specimen.metrics.analysis_type
            self.specimens.append(specimen)
        else:
            raise ValueError("Specimen does not match the sample group type")
        
     
    def calculate_characteristics(self):
        """
        Calculate the characteristics of the sample group. 
        Same computation as in the SpecimenAnalysisProtocol, but for  average stress and strain of the entire sample group.
        
        """
        pass

class SampleGroupOperations:
    """
    Methods for aggregate operations on the specimens, such as computing mean, median, standard deviation, etc. for various metrics.
    Helper methods to calculate general properties of the sample group, such as mean stress, mean strain, etc.
    """
    @staticmethod
    def get_mean_strength(sample_group: SampleGroup) -> float:
        strengths = [specimen.metrics.strength for specimen in sample_group.specimens]
        return sum(strengths) / len(strengths)
    
    @staticmethod
    def calculate_group_stress(sample_group: SampleGroup) -> np.array:
        pass   
        return SampleGroup.stress

    @staticmethod
    def calculate_group_strain(sample_group: SampleGroup) -> np.array:
        pass 
        return SampleGroup.strain
    #... Other aggregate operations ...


class SampleGroupAnalysisProtocol:
    """A protocol for the analysis of a SampleGroup. It defines the steps of the analysis and the order in which they should be executed."""
    def __init__(self, sample_group: SampleGroup):
        self.sample_group = sample_group

    def execute(self):
        """Execute the analysis protocol to reutrn SampleGroupCharacteristics onto the SampleGroup.characteristics ."""
        pass

class SampleGroupGraphManager:
    """A service class for all graphical operations related to SampleGroups, including plotting aggregated data or overlaying individual specimen plots."""
    def __init__(self, sample_group: SampleGroup, plotter: SampleGroupPlotter = None, contol_chart: ControlChart = None):
        self.sample_group = sample_group 
        self.control_chart = contol_chart or ControlChart()
        self.plotter = plotter or  SampleGroupPlotter()

    def generate_sample_group_plot(self):
        """Generate a plot for the average stress-strain curve of the sample group."""
        pass

    def generate_control_charts(self):
        """Generate a control chart for the sample group."""
        pass

class SampleGroupPlotter:
    pass

class SampleGroupDataManager:
    """This class could handle bulk data operations for the entire SampleGroup, like saving all specimens to a database or loading them."""
    def __init__(self, repository=None, control_metrics_provider=None, excel_exporter=None):
            self.repository = repository or SampleGroupRepository()
            self.control_metrics = control_metrics_provider or ControlProcessMetrics()
            self.excel_exporter = excel_exporter or SampleGroupExcelExporter()


class SampleGroupTable(Base):
    """A SQLAlchemy table for storing SampleGroup data in a database."""
    __tablename__ = "sample_groups"
    id = Column(Integer, primary_key=True)
    analysis_type = Column(String)
    strength = Column(Float)
    # ... Other columns ...

class SampleGroupRepository(BaseRepository):
    """Offers methods to persist and retrieve SampleGroups from storage"""
    def __init__(self):
        super().__init__(model = SampleGroupTable)

class SampleGroupExcelExporter(ExcelExporter):
    """Exports a SampleGroup to an Excel file"""
    def __init__(self, sample_group: SampleGroup):
        self.sample_group = sample_group
        super().__init__(self.sample_group)

    def generate_excel_sheet(self):
        """Generate an Excel sheet for the sample group."""
        pass

""" 
- Excel Exporters: 
        -> ExcelSheet DTO: Represents a single sheet's data and structure.
        -> ExcelFormatter (operation): Class to handle formatting for Excel sheets.
        -> ExcelExportService: A service class responsible for generating and saving Excel sheets.
"""

class SampleGroupFacade:
    """ Provides a simplified interface for complex operations on SampleGroups"""
