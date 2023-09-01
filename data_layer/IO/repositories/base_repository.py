# app/data_layer/IO/repositories/base_repository.py

from abc import ABC

class BaseRepository(ABC):
    def __init__(self, model):
        self.model = model

    