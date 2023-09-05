# app/data_layer/models/specimen_DB.py

from typing import Optional

from .specimen import Specimen
from ..IO.repositories.specimen_repository import SpecimenRepository
from ..IO.repositories.specimen_orm import Specimen_Table


class SpecimenDB(Specimen):
    def __init__(self, name, length, width, thickness, weight, data = None, data_formater = None):
        super().__init__(name, length, width, thickness, weight, data, data_formater)
        self.id = None

    @classmethod
    def from_db(cls, id, repository: Optional['SpecimenRepository'] = None):
        repository = repository or SpecimenRepository()
        return repository.retrieve_specimen_by_id(id)
    

    def convert_to_ORM(self) -> 'Specimen_Table':
        """Convert a Specimen DB object to an ORM object."""
        db_object  = self
        return Specimen_Table(
            id=db_object.id,
            status=db_object.status,
            name=db_object.name,
            type=db_object.type,
            properties=db_object.properties,
            analysis_type=db_object.analysis_type,
            metrics=db_object.metrics,
            analysis_date=db_object.analysis_date,
            production_date=db_object.production_date,
            cross_sectional_image=db_object.cross_sectional_image,
            notes=db_object.notes
        )

    @classmethod
    def convert_from_ORM( cls, orm_object: 'Specimen_Table') -> 'SpecimenDB':
        """Convert a Specimen ORM object to a DB object."""
        pass



