# app/data_layer/metrics/__init__.py

"""
This Classes will contain the metrics for each analysis type and validation.
The Factory will create the correct DTO metric for the specimen analysis type.
"""

from collections import namedtuple
# add uncertainty to metric
# using the package uncertainties https://pythonhosted.org/uncertainties/ for the uncertainty

# units usinf the package pint https://pint.readthedocs.io/en/0.11.3/

Metric = namedtuple('Metric', ['value', 'default_unit'])

from data_layer.metrics.ISO13314_metrics import ISO_13314_SpecimenMetricsDTO
from data_layer.metrics.specimen_metrics import SpecimenMetricsDTO

# Must be imported lasst to avoid circular imports
from data_layer.metrics.metrics_factory import SpecimenMetricsFactory
