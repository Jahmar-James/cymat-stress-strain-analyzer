# app/data_layer/metrics/__init__.py

from collections import namedtuple

Metric = namedtuple('Metric', ['value', 'default_unit'])

from data_layer.metrics.ISO13314_metrics import ISO_13314_SpecimenMetricsDTO
from data_layer.metrics.specimen_metrics import SpecimenMetricsDTO


# Must be imported lasst to avoid circular imports
from data_layer.metrics.metrics_factory import SpecimenMetricsFactory