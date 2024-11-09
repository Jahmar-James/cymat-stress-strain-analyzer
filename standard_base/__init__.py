# Expose the factory and processor for external use
# from .sample_factory import MechanicalTestStandards, register_sample, standard_registry
from enum import Enum


class MechanicalTestStandards(Enum):
    GENERAL_PRELIMINARY = "(General (Preliminary)"
    CYMAT_ISO13314_2011 = "Cymat_ISO13314-2011"
    VISUALIZATION_SAMPLE = "Visualizations_sample"

    # Missing values check casefold of the str enum value
    @classmethod
    def _missing_(cls, value: str):
        value = value.casefold()
        for standard in cls:
            if value == standard.value.casefold():
                return standard
        return None
