# app/app_layer/managers/data_io_manager.py

from typing import List, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from data_layer.models.specimen import Specimen 
    from data_layer.models.sample_group import SampleGroup
    
    from data_layer.IO.specimen_data_manager import SpecimenDataManager
    from data_layer.IO.sample_group_data_manager import SampleGroupDataManager

class DataIOManager:
    """
    Manage data input and output
    """
    def __init__(self, specimen_data_manager: 'SpecimenDataManager', sample_group_data_manager: 'SampleGroupDataManager'):
        self.specimen_data_manager = specimen_data_manager
        self.sample_group_data_manager = sample_group_data_manager
        
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