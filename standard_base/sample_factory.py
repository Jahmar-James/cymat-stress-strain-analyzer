from enum import Enum
from typing import Callable

standard_registry = {}


# Decorator for registering validators
def register_sample(standard) -> Callable:
    def decorator(cls):
        global standard_registry
        standard_registry[standard] = cls()
        return cls

    return decorator


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


from standards.cymat_iso_13314_2011.sample_iso13314_cymat import SampleCymat
from standards.default_sample.sample import SampleGeneric
