# app/data_layer/models/specimen_DB.py

from typing import Optional

from .specimen import Specimen
from ..IO.repositories.specimen_repository import SpecimenRepository


class SpecimenDB(Specimen):
    def __init__(self, name, length, width, thickness, weight, data = None, data_formater = None):
        super().__init__(name, length, width, thickness, weight, data, data_formater)
        self.id = None

    @classmethod
    def from_db(cls, id, repository: Optional['SpecimenRepository'] = None):
        repository = repository or SpecimenRepository()
        return repository.retrieve_specimen_by_id(id)

    