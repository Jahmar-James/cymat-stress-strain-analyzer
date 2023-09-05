# app/data_layer/IO/specimen_data_manager.py

from typing import TYPE_CHECKING, Optional

import pandas as pd

from service_layer.operations.specimen_operations import SpecimenOperations

from .specimenIO import Idataformatter, SpecimenIO
from ..IO.repositories.specimen_repository import SpecimenRepository
from .PoI import (PointsOfInterest, YoungModulusPointsOfInterest, ZeroPointsOfInterest)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_layer.models import Specimen, SpecimenDB, SpecimenDTO

class SpecimenDataManager():
    """Manage import and export of specimen class from different sources"""
    def __init__(self, data=None, data_formatter : Optional['Idataformatter'] = None, 
                 repository : Optional['SpecimenRepository'] = None,
                 specimen_operations: Optional['SpecimenOperations'] = None,
                 points_of_interest: Optional['PointsOfInterest'] = None):
        
        self.data = data
        self.data_formatter = data_formatter or SpecimenIO()
        self.repository  =  repository or SpecimenRepository()
        self.points_of_interest = points_of_interest or YoungModulusPointsOfInterest(data) 
        self.specimen_operations = specimen_operations or SpecimenOperations()
        
    def get(self, data_manager_attribute: str, default = None):
        """Get an attribute from the data manager"""   
        return getattr(self, data_manager_attribute, default)
        
    def set_points_of_interest(self, points_of_interest: 'PointsOfInterest'):
        self.points_of_interest = points_of_interest
        
    def load_data(self, file_path: str):
        self.data = self.data_formatter.read_and_clean_data(file_path)
        return self.data
    
    def get_modulus_region(self, data: pd.DataFrame, data_marker: 'PointsOfInterest'):
        young_modulus_marker = data_marker.find_points()
        self.points_of_interest.points.update(young_modulus_marker.get_all_points())
    
    def align_data_to_zero(self, data: pd.DataFrame, shift : Optional[float] = None, data_marker: Optional['PointsOfInterest'] = None):
        if shift:
            data = self.specimen_operations.shift_data(shift, data)
            self.shifted_data = data
            return data
        elif data_marker:
            zero_marker = data_marker.find_points()
            data = self.specimen_operations.shift_data(zero_marker['intercept'], data)
            self.shifted_data = data
            return data
        else:
            raise ValueError("Either shift or data_marker must be provided")
        
    def from_database( id, repository_instance:'SpecimenRepository') -> 'SpecimenDB': 
        pass
    
    def to_database(self, specimen:'Specimen', repository_instance:'SpecimenRepository'):
        pass

    def from_program_zip_file(self, path, data_formatter:'SpecimenIO') -> 'SpecimenDTO':
        return data_formatter.deserialize(path)

    def to_program_zip_file(self, SpecimenDTO :'SpecimenDTO', directory, data_formatter:'SpecimenIO'):
        return data_formatter.serialize(SpecimenDTO, directory)

    
    @property
    def points(self):
        return self.points_of_interest.points
