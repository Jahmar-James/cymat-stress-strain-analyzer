# app/data_layer/IO/repositories/specimen_repository.py

from typing import TYPE_CHECKING

from data_layer.IO.repositories import BaseRepository

if TYPE_CHECKING:
    from data_layer.models import SpecimenDB

class SpecimenRepository(BaseRepository):
    """Handle save and creation of specimen class from db"""
    def __init__(self, specimen_ORM):
        super().__init__model = specimen_ORM()
        
    
    # CRUD operations

    @staticmethod
    def save_to_db(specimen: 'SpecimenDB'):
        # Placeholder database save operation
        pass

    @staticmethod
    def fetch_from_db(db_id: int) -> 'SpecimenDB':
        # Placeholder database fetch operation
        return SpecimenDB()