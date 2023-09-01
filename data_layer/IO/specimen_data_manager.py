# app/data_layer/IO/specimen_data_manager.py

from typing import TYPE_CHECKING
from data_layer.IO import SpecimenIO
from data_layer.IO.repositories import SpecimenRepository

if TYPE_CHECKING:
    from data_layer.models import Specimen, SpecimenDB

class SpecimenDataManager:
    """Manage import and export of specimen class from different sources"""
    def __init__(self, data,  data_formater, repository):
        self.data = data
        self.data_formater = data_formater or SpecimenIO()
        self.repositorty  =  repository or SpecimenRepository() 

    @classmethod
    def from_database(cls, id,  repository_instance:SpecimenRepository) -> 'SpecimenDB': 
        specimen = repository_instance.get(id)
        return 
    
    @classmethod
    def from_program_zip_file(cls, path, data_formate:SpecimenIO()) -> 'Specimen':
        pass