# app/data_layer/IO/specimen_data_manager.py

from data_layer.models import Specimen
from data_layer.IO import SpecimenIO
from data_layer.IO.repositories import SpecimenRepository

class SpecimenDataManager:
    """Manage import and export of specimen class from different sources"""
    def __init__(self, data, data_formater, repositorty):
        self.data = data
        self.data_formater = data_formater or SpecimenIO()
        self.repositorty  =  repositorty or SpecimenRepository() 

    @classmethod
    def from_database(cls, id,  repository_instance:SpecimenRepository) -> Specimen: 
        specimen = repository_instance.get(id)
        return 
    
    @classmethod
    def from_program_zip_file(cls, path, data_formate:SpecimenIO()) -> Specimen:
        pass