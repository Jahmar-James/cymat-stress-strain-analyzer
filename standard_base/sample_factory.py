from enum import Enum
from typing import Callable

from standard_base import MechanicalTestStandards
from standard_base.default_sample.sample import SampleGeneric

standard_registry = {MechanicalTestStandards.GENERAL_PRELIMINARY: SampleGeneric}


# Decorator for registering validators
def register_sample(standard) -> Callable:
    def decorator(cls):
        global standard_registry
        standard_registry[standard] = cls
        return cls

    return decorator


from standards.cymat_iso_13314_2011.sample_iso13314_cymat import SampleCymat
