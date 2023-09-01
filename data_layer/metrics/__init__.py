# app/data_layer/metrics/__init__.py

from collections import namedtuple

from data_layer.metrics.specimen_metrics import SpecimenMetricsDTO
from data_layer.metrics.ISO1346_metrics import ISO_1346_SpecimenMetricsDTO

from data_layer.metrics.metrics_factory import SpecimenMetricsFactory

Metric = namedtuple('Metric', ['value', 'default_unit'])
