# app/data_layer/IO/specimen_data_manager.py

from typing import TYPE_CHECKING
from data_layer.IO import SpecimenIO
from data_layer.IO.repositories import SpecimenRepository
from service_layer.operations.specimen_operations import SpecimenOperations


if TYPE_CHECKING:
    from data_layer.models import Specimen, SpecimenDB
    import pandas as pd

class SpecimenDataManager:
    """Manage import and export of specimen class from different sources"""
    def __init__(self, data=None, data_formatter=None, repository=None):
        self.data = data
        self.data_formatter = data_formatter or SpecimenIO()
        self.repositorty  =  repository or SpecimenRepository()
        self.points_of_interest = {} 
        
    def load_data(self, file_path: str):
        self.data = self.data_formatter.read_and_clean_data(file_path)
        return self.data
    
    def align_data(self, data: pd.DataFrame):
        instance = Points_of_interest
        start_idx_along_strain, end_idx_along_strain =  SpecimenOperations.determine_region_for_young_modulus( instance.start_pt_algoritm, instance.end_pt_algoritm)
        self.points_of_interest['start_idx_along_strain_youngs_modulus'] = start_idx_along_strain
        self.points_of_interest['end_idx_along_strain_youngs_modulus'] = end_idx_along_strain  
        data  = SpecimenOperations.zero_strain_data(start_idx_along_strain, data)
        self.shifted_data = data
        return data
        

    @classmethod
    def from_database(cls, id,  repository_instance:SpecimenRepository) -> 'SpecimenDB': 
        specimen = repository_instance.get(id)
        return 
    
    @classmethod
    def from_program_zip_file(cls, path, data_formate:SpecimenIO()) -> 'Specimen':
        pass
    

class Points_of_interest:
    pass