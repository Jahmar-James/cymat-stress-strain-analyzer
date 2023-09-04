# app/data_layer/IO/repositories/specimen_repository.py

from typing import TYPE_CHECKING, Optional, Union

from .base_repository import BaseRepository
from .specimen_orm import Specimen_Table

if TYPE_CHECKING:
    from data_layer.models import SpecimenDB


class SpecimenRepository(BaseRepository):
    """Handle save and creation of specimen class from db"""
    def __init__(self,  specimen_ORM : Optional['Specimen_Table'] = Specimen_Table):
        super().__init__(model=specimen_ORM)
        
    def retrieve_specimen_by_id(self, id: int) -> 'Specimen_Table':
        return super().retrieve_entity_by_id(entity_id = id, current_session=None)
        
    @staticmethod
    def save_to_db(specimen: 'SpecimenDB'):
        repo_instance = SpecimenRepository(specimen_ORM=Specimen_Table)
        specimen_orm = specimen.convert_to_ORM()
        repo_instance.create_entity(entity=specimen_orm, current_session=None)

    @staticmethod
    def fetch_from_db(db_id: int , returning_class : Optional['SpecimenDB'] = None) -> Union['SpecimenDB', 'Specimen_Table']:
        """Fetch a specimen from the database by id. Default return is a Specimen ORM oobject add returning_class to get SpecimenDB."""
        repo_instance = SpecimenRepository(specimen_ORM=Specimen_Table)
        specimen_ORM = repo_instance.retrieve_entity_by_id(entity_id = db_id, current_session=None)
        return specimen_ORM if not returning_class else returning_class.convert_from_ORM(specimen_ORM)
    
    
