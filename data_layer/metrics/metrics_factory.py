# app/data_layer/metrics/metrics_factory.py

from data_layer.metrics import SpecimenMetricsDTO, ISO_1360_SpecimenMetricsDTO


class SpecimenMetricsFactory:
    """ 
    Factory to determine specimen creation based on analysis type or program model. 
    Encapsulates the logic for specimen instantiation.
    """
    _registry = {
            "base": SpecimenMetricsDTO,
            "ISO_1360": ISO_1360_SpecimenMetricsDTO
        }

    @staticmethod
    def create_specimen(criteria: str = 'base'):
        if criteria in SpecimenMetricsFactory._registry:
            return SpecimenMetricsFactory._registry[criteria]()
        else:
            raise ValueError(f"Unknown criteria: {criteria}")