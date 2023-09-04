# app/service_layer/operations/sample_group_operations.py

from .data_processing_service import DataProcessingService

from data_layer.models.sample_group import SampleGroup

class SampleGroupOperations(DataProcessingService):
    """
    Methods for aggregate operations on the specimens, such as computing mean, median, standard deviation, etc. for various metrics.
    Helper methods to calculate general properties of the sample group, such as mean stress, mean strain, etc.
    """
    @staticmethod
    def get_mean_strength(sample_group: 'SampleGroup') -> float:
        strengths = [specimen.metrics.strength for specimen in sample_group.specimens]
        return sum(strengths) / len(strengths)
