# service_layer/service_layer.py

from .analysis.specimen_analysis_protocol import SpecimenAnalysisProtocol
from .analysis.sample_group_analysis_protocol import SampleGroupAnalysisProtocol
from .plotting.specimen_graph_manager import SpecimenGraphManager
from .plotting.sample_group_graph_manager import SampleGroupGraphManager
from .operations.specimen_operations import SpecimenOperations
from .operations.sample_group_operations import SampleGroupOperations

class ServiceLayer:
    def __init__(self):
        self.specimen_analysis = SpecimenAnalysisProtocol()
        self.sample_group_analysis = SampleGroupAnalysisProtocol()
        self.specimen_graph_manager = SpecimenGraphManager()
        self.sample_group_graph_manager = SampleGroupGraphManager()
        self.specimen_operations = SpecimenOperations()
        self.sample_group_operations = SampleGroupOperations()
