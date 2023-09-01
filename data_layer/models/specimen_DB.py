# app/data_layer/models/specimen_DB.py

from data_layer.models.specimen import Specimen

class SpecimenDB(Specimen):
    def __init__(self, name, length, width, thickness, weight, data = None, data_formater = None):
        super().__init__(name, length, width, thickness, weight, data, data_formater)
        self.id = None

    @classmethod
    def from_db(cls, id, repository = None):
        repository = repository or SpecimenRepository()
        return repository.retrieve_specimen(id)

    